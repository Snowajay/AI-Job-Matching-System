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

import re
from typing import List, Tuple

try:  # scikit-learn is the ML engine; fall back cleanly if it is missing
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    _SKLEARN_AVAILABLE = True
except Exception:  # pragma: no cover - exercised only without scikit-learn
    _SKLEARN_AVAILABLE = False


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


class SkillMatcher:
    """Scores a candidate's skills against a job's required skills."""

    def __init__(self, threshold: float = 0.60):
        # Minimum cosine similarity for two non-identical skills to count as a
        # match. Tuned so clear variants match while unrelated skills do not.
        self.threshold = threshold

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

        # Build the TF-IDF space once over every skill involved in this request.
        sim_lookup = self._build_similarity_lookup(cand_norm, jobs)

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
                    reasons.append(f"Matches required skill: {original}")
                elif kind == "semantic" and best_sim >= self.threshold:
                    matched += 1
                    pct = int(round(best_sim * 100))
                    reasons.append(f"Matches '{original}' via your skill '{best_cand}' ({pct}% similar)")

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
            sim = sim_lookup.get((job_skill_norm, cnorm), 0.0)
            if sim > best_sim:
                best_sim = sim
                best_display = cand_original[i]
        return best_display, best_sim, "semantic"

    def _build_similarity_lookup(self, cand_norm, jobs):
        """Fit TF-IDF over all skills in the request and precompute cosine sims."""
        if not _SKLEARN_AVAILABLE:
            return None

        job_norms = []
        for job in jobs:
            job_norms.extend(_normalize(s) for s in (job.required_skills or []) if s and s.strip())

        vocab = list(dict.fromkeys(cand_norm + job_norms))  # unique, order-stable
        if len(vocab) < 2:
            return {}

        try:
            vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
            matrix = vectorizer.fit_transform(vocab)
            sims = cosine_similarity(matrix)
        except Exception:  # pragma: no cover - defensive
            return None

        index = {term: i for i, term in enumerate(vocab)}
        lookup = {}
        for job_term in set(job_norms):
            for cand_term in set(cand_norm):
                lookup[(job_term, cand_term)] = float(sims[index[job_term]][index[cand_term]])
        return lookup


# Module-level default instance used by the matching endpoint.
default_matcher = SkillMatcher()
