"""AI-powered skill matching.

This module replaces exact string matching with a semantic matcher so that
equivalent skills written differently are recognized as the same. It combines
two NLP techniques:

1. A curated skill-synonym layer that canonicalizes common abbreviations and
   variants (for example "JS" and "JavaScript", "ML" and "Machine Learning").
2. TF-IDF character n-gram vectors with cosine similarity (scikit-learn), which
   catches morphological variants and minor differences the synonym map does
   not list (for example "Postgres" and "PostgreSQL", "ReactJS" and "React").

The result is an explainable score: the percentage of a job's required skills
the candidate has, where "having" a skill now allows semantic equivalence
rather than only an exact string match.

If scikit-learn is unavailable for any reason, the matcher degrades gracefully
to synonym-aware exact matching so the endpoint never fails.
"""

from __future__ import annotations

import os
import re
from typing import List, Optional, Tuple

try:  # scikit-learn is the TF-IDF engine; fall back cleanly if it is missing
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    _SKLEARN_AVAILABLE = True
except Exception:  # pragma: no cover - exercised only without scikit-learn
    _SKLEARN_AVAILABLE = False

try:  # numpy backs the embedding similarity math
    import numpy as _np

    _NUMPY_AVAILABLE = True
except Exception:  # pragma: no cover
    _NUMPY_AVAILABLE = False

# The embedding layer (local sentence-transformer model, or a hosted API) is
# optional. When present it upgrades similarity from character-spelling to real
# semantic meaning; when absent the matcher falls back to TF-IDF.
try:
    from app.embeddings import get_embedding_provider

    _EMBEDDINGS_IMPORTABLE = True
except Exception:  # pragma: no cover
    _EMBEDDINGS_IMPORTABLE = False

    def get_embedding_provider(mode=None):  # type: ignore
        return None


# Sentinel so callers can distinguish "use the configured default provider"
# from "explicitly no provider" (None) when constructing a SkillMatcher.
_DEFAULT = object()


# Canonical forms for common technology abbreviations and spellings. The keys
# are normalized (lowercase) variants; the values are the canonical skill.
SKILL_ALIASES = {
    "js": "javascript",
    "ecmascript": "javascript",
    "ts": "typescript",
    "py": "python",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "postgres": "postgresql",
    "psql": "postgresql",
    "pg": "postgresql",
    "k8s": "kubernetes",
    "k8": "kubernetes",
    "nodejs": "node.js",
    "node": "node.js",
    "reactjs": "react",
    "react.js": "react",
    "aws": "amazon web services",
    "gcp": "google cloud platform",
    "oop": "object oriented programming",
    "rest": "rest api",
    "restful": "rest api",
    "golang": "go",
    "tf": "tensorflow",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "db": "database",
    "ci/cd": "continuous integration",
    "cicd": "continuous integration",
}


def _normalize(skill: str) -> str:
    """Lowercase, trim, collapse internal whitespace, and apply the alias map."""
    s = re.sub(r"\s+", " ", skill.strip().lower())
    return SKILL_ALIASES.get(s, s)


# Groups of skills that are genuinely DISTINCT even though a semantic model may
# rate them as similar (measured: a model scores "Java" ~ "JavaScript" at ~65%,
# as high as real matches). Two DIFFERENT members of the same group are never
# allowed to count as a semantic match, so domain knowledge keeps precision
# while embeddings add recall. Members are normalized (lowercase) forms.
DISTINCT_GROUPS = [
    {"java", "javascript"},
    {"c", "c++", "c#", "objective-c"},
    {"react", "react native"},
    {"go", "rust"},          # unrelated systems languages the model may conflate
    {"php", "perl"},
]


def _are_distinct(a: str, b: str) -> bool:
    """True if a and b are different members of the same distinct-skills group."""
    if a == b:
        return False
    for group in DISTINCT_GROUPS:
        if a in group and b in group:
            return True
    return False


def _display(skill: str) -> str:
    """Lowercase + collapse whitespace WITHOUT applying the alias map.

    Used to tell whether a match only lined up because the AI synonym layer
    treated two differently written skills as equivalent (e.g. "JS" and
    "JavaScript"), so the UI can say so instead of hiding it as a plain match.
    """
    return re.sub(r"\s+", " ", skill.strip().lower())


class SkillMatcher:
    """Scores a candidate's skills against a job's required skills.

    Similarity between two non-identical skills is computed by the best engine
    available, in this order:
      1. embeddings  -- a real AI model (local sentence-transformer, or a hosted
         API). Captures *meaning*, so "PyTorch" matches "Deep Learning".
      2. tfidf       -- character n-gram cosine. Captures *spelling*, so
         "Kubernete" matches "Kubernetes".
      3. none        -- synonym-aware exact matching only.
    The engine actually used for a given ``rank`` call is recorded on
    ``self.engine`` after the call, and surfaced in each match's reasons.
    """

    def __init__(
        self,
        threshold: float = 0.60,
        embedding_threshold: Optional[float] = None,
        embedding_provider=_DEFAULT,
    ):
        # Minimum TF-IDF cosine for two non-identical skills to count as a
        # spelling match. Tuned so clear variants match while unrelated do not.
        self.threshold = threshold
        # Minimum cosine for an EMBEDDING (semantic) match. Semantic cosines sit
        # on a different scale than character TF-IDF, so this has its own value.
        # Tunable at runtime via AJMS_EMBEDDING_THRESHOLD so the team can dial it
        # in against real model scores without editing code.
        if embedding_threshold is None:
            try:
                embedding_threshold = float(os.environ.get("AJMS_EMBEDDING_THRESHOLD", "0.45"))
            except ValueError:
                embedding_threshold = 0.45
        self.embedding_threshold = embedding_threshold
        # _DEFAULT -> resolve from config/env lazily on first use; None -> never
        # use embeddings; an explicit provider -> use it (handy for tests).
        self._embedding_provider = embedding_provider
        self.engine = None

    def _provider(self):
        if self._embedding_provider is _DEFAULT:
            self._embedding_provider = get_embedding_provider()
        return self._embedding_provider

    def rank(self, candidate_skills: List[str], jobs: List) -> List[Tuple[float, object, List[str]]]:
        """Rank jobs for a candidate.

        Returns a list of (score, job, reasons) for every job that has at least
        one matched skill, sorted from strongest to weakest. Each job in ``jobs``
        must expose a ``required_skills`` list.
        """
        cand_norm = [_normalize(s) for s in candidate_skills if s and s.strip()]
        cand_set = set(cand_norm)
        if not cand_norm:
            return []

        # Build the similarity space once (embeddings if available, else TF-IDF).
        # This also sets self.engine to "embeddings", "tfidf", or None.
        sim_lookup = self._build_similarity_lookup(cand_norm, jobs)
        sim_threshold = (
            self.embedding_threshold if self.engine == "embeddings" else self.threshold
        )

        results: List[Tuple[float, object, List[str]]] = []
        for job in jobs:
            job_norm = [_normalize(s) for s in (job.required_skills or []) if s and s.strip()]
            if not job_norm:
                continue

            matched = 0
            reasons: List[str] = []
            for original, norm in zip(job.required_skills, job_norm):
                best_cand, best_sim, kind = self._best_match(norm, cand_set, cand_norm, candidate_skills, sim_lookup)
                if kind == "exact":
                    matched += 1
                    # If the candidate wrote the skill differently from the job
                    # (e.g. "JS" for "JavaScript", "Postgres" for "PostgreSQL"),
                    # the match only happened because the AI synonym layer
                    # recognized them as the same skill. Surface that in the
                    # reason so the semantic matching is visible to the user,
                    # instead of looking like plain string equality.
                    if _display(best_cand) == _display(original):
                        reasons.append(f"Matches required skill: {original}")
                    else:
                        reasons.append(f"AI recognized your '{best_cand}' as {original}")
                elif kind == "semantic" and best_sim >= sim_threshold:
                    matched += 1
                    pct = int(round(best_sim * 100))
                    if self.engine == "embeddings":
                        # Real AI-model match: related by meaning, not spelling.
                        reasons.append(
                            f"AI semantic match: '{original}' ~ your '{best_cand}' ({pct}% related)"
                        )
                    else:
                        reasons.append(
                            f"AI matched '{original}' to your '{best_cand}' ({pct}% similar)"
                        )

            if matched == 0:
                continue
            score = round(matched / len(job_norm) * 100, 2)
            results.append((score, job, reasons))

        results.sort(key=lambda item: item[0], reverse=True)
        return results

    # ---- internals ----------------------------------------------------------

    def _best_match(self, job_skill_norm, cand_set, cand_norm, cand_original, sim_lookup):
        """Return (candidate_skill_display, similarity, kind) for one job skill."""
        # Exact (after synonym normalization) wins immediately.
        if job_skill_norm in cand_set:
            idx = cand_norm.index(job_skill_norm)
            return cand_original[idx], 1.0, "exact"

        # Otherwise use the TF-IDF cosine similarities, if available.
        if sim_lookup is None:
            return None, 0.0, "none"
        best_sim = 0.0
        best_display = None
        for i, cnorm in enumerate(cand_norm):
            # Distinct-skills guard: never let a semantic score connect two
            # skills we know are different (Java vs JavaScript, C vs C++, ...),
            # no matter how similar the model thinks they are.
            if _are_distinct(job_skill_norm, cnorm):
                continue
            sim = sim_lookup.get((job_skill_norm, cnorm), 0.0)
            if sim > best_sim:
                best_sim = sim
                best_display = cand_original[i]
        return best_display, best_sim, "semantic"

    def _build_similarity_lookup(self, cand_norm, jobs):
        """Precompute pairwise skill similarities with the best engine available.

        Sets ``self.engine`` to the engine used and returns a
        ``{(job_term, cand_term): cosine}`` lookup, or None when no similarity
        engine is available (callers then rely on synonym-aware exact matching).
        """
        self.engine = None

        job_norms = []
        for job in jobs:
            job_norms.extend(_normalize(s) for s in (job.required_skills or []) if s and s.strip())

        vocab = list(dict.fromkeys(cand_norm + job_norms))  # unique, order-stable
        if len(vocab) < 2:
            return {}

        # 1. Embeddings (real AI model) first, if a provider is configured.
        lookup = self._embedding_lookup(vocab, job_norms, cand_norm)
        if lookup is not None:
            self.engine = "embeddings"
            return lookup

        # 2. TF-IDF character n-grams (spelling similarity) as the fallback.
        if _SKLEARN_AVAILABLE:
            try:
                vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
                matrix = vectorizer.fit_transform(vocab)
                sims = cosine_similarity(matrix)
            except Exception:  # pragma: no cover - defensive
                return None
            self.engine = "tfidf"
            return self._lookup_from_matrix(sims, vocab, job_norms, cand_norm)

        # 3. Nothing available -> synonym-aware exact matching only.
        return None

    def _embedding_lookup(self, vocab, job_norms, cand_norm):
        """Embed every skill once and build the cosine lookup, or None."""
        if not _NUMPY_AVAILABLE:
            return None
        provider = self._provider()
        if provider is None:
            return None
        try:
            vecs = provider.embed(vocab)  # already L2-normalized
            sims = vecs @ vecs.T          # cosine, since rows are unit vectors
        except Exception:
            # Any runtime failure (model load, network, API error) -> fall back.
            return None
        return self._lookup_from_matrix(sims, vocab, job_norms, cand_norm)

    @staticmethod
    def _lookup_from_matrix(sims, vocab, job_norms, cand_norm):
        index = {term: i for i, term in enumerate(vocab)}
        lookup = {}
        for job_term in set(job_norms):
            for cand_term in set(cand_norm):
                lookup[(job_term, cand_term)] = float(sims[index[job_term]][index[cand_term]])
        return lookup


# Module-level default instance used by the matching endpoint.
default_matcher = SkillMatcher()
