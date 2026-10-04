"""Tests for the embedding (AI-model) layer.

These do NOT download or call any real model. The semantic behavior is proven
with a deterministic stub provider (hand-built vectors), the hosted-API provider
is proven against a mocked HTTP response, and the factory's selection/fallback
logic is checked directly. The real sentence-transformer model is exercised
separately by verify_embeddings.py on a machine with network access.
"""

from types import SimpleNamespace

import numpy as np
import pytest

from app import embeddings
from app.embeddings import ApiEmbeddingProvider, get_embedding_provider
from app.matching import SkillMatcher


def job(skills):
    return SimpleNamespace(required_skills=skills)


# --- a deterministic "AI model": hand-placed vectors in a tiny semantic space -
# Skills that mean related things are placed close together. Strings are the
# NORMALIZED forms the matcher produces (lowercased, aliases applied).
_SEMANTIC_SPACE = {
    "deep learning":    [1.00, 0.00, 0.00, 0.00],
    "pytorch":          [0.95, 0.31, 0.00, 0.00],   # ~0.95 cosine with deep learning
    "machine learning": [0.90, 0.44, 0.00, 0.00],   # "ML" normalizes to this
    "python":           [0.70, 0.70, 0.10, 0.00],
    "agile":            [0.00, 1.00, 0.00, 0.00],
    "scrum":            [0.10, 0.99, 0.00, 0.00],    # ~0.99 cosine with agile
    "photoshop":        [0.00, 0.00, 1.00, 0.00],    # unrelated to everything above
    # Java and JavaScript look similar to the model (high cosine) but must NOT
    # match -- the distinct-skills guard has to override this.
    "java":             [0.00, 0.00, 0.00, 1.00],
    "javascript":       [0.10, 0.00, 0.00, 0.99],    # ~0.99 cosine with java
}


class StubProvider:
    """Returns the hand-built vectors above, L2-normalized, in input order."""

    name = "stub"

    def embed(self, texts):
        rows = []
        for t in texts:
            v = np.asarray(_SEMANTIC_SPACE.get(t, [0.0, 0.0, 0.0]), dtype="float32")
            n = np.linalg.norm(v)
            rows.append(v / n if n else v)
        return np.vstack(rows).astype("float32")


def test_embedding_matcher_matches_by_meaning_not_spelling():
    # "PyTorch" shares no characters with "Deep Learning", so TF-IDF/synonyms
    # would never connect them -- only a semantic model can.
    matcher = SkillMatcher(embedding_provider=StubProvider())
    results = matcher.rank(["PyTorch"], [job(["Deep Learning"]), job(["Photoshop"])])

    assert matcher.engine == "embeddings"
    matched = {tuple(j.required_skills): (s, r) for s, j, r in results}

    assert ("Deep Learning",) in matched
    score, reasons = matched[("Deep Learning",)]
    assert score == 100.0
    assert "AI semantic match" in reasons[0]
    assert "related" in reasons[0]

    # Unrelated skill is correctly excluded.
    assert ("Photoshop",) not in matched


def test_embedding_matcher_handles_alias_plus_meaning():
    # "Scrum" ~ "Agile" (meaning) and "ML" -> "machine learning" ~ "Deep
    # Learning" (alias + meaning), both via the model.
    matcher = SkillMatcher(embedding_provider=StubProvider())
    results = matcher.rank(["Scrum", "ML"], [job(["Agile", "Deep Learning"])])

    assert matcher.engine == "embeddings"
    assert len(results) == 1
    score, _, reasons = results[0]
    assert score == 100.0
    assert len(reasons) == 2


def test_distinct_skills_guard_blocks_false_friends():
    # The model thinks Java ~ JavaScript (0.99 in the stub space), but the guard
    # must keep them from matching, while real semantic matches still work.
    matcher = SkillMatcher(embedding_provider=StubProvider())
    results = matcher.rank(["Java"], [job(["JavaScript"]), job(["Deep Learning"])])
    matched = {tuple(j.required_skills) for _, j, _ in results}
    assert ("JavaScript",) not in matched   # guarded, despite high similarity

    # Sanity: a candidate who really has JavaScript still matches a JS job.
    results2 = matcher.rank(["JavaScript"], [job(["JavaScript"])])
    assert len(results2) == 1


def test_api_provider_parses_and_orders_mocked_response(monkeypatch):
    # Mock the HTTP call so no network/key is needed. Return rows out of order
    # to prove the provider restores input order via each row's "index".
    import json
    monkeypatch.setenv("AJMS_EMBEDDING_TEMPLATE", "")  # pin template off for exact assert

    class FakeResp:
        def __init__(self, payload):
            self._p = payload.encode()

        def read(self):
            return self._p

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=0):
        body = json.loads(req.data.decode())
        assert body["input"] == ["alpha", "beta"]
        payload = json.dumps({"data": [
            {"index": 1, "embedding": [0.0, 3.0]},   # beta (deliberately first)
            {"index": 0, "embedding": [4.0, 0.0]},   # alpha
        ]})
        return FakeResp(payload)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    provider = ApiEmbeddingProvider(api_key="test-key")
    vecs = provider.embed(["alpha", "beta"])

    assert vecs.shape == (2, 2)
    # Order restored: row 0 is alpha ([1,0]), row 1 is beta ([0,1]); normalized.
    np.testing.assert_allclose(vecs[0], [1.0, 0.0], atol=1e-6)
    np.testing.assert_allclose(vecs[1], [0.0, 1.0], atol=1e-6)


def test_factory_off_returns_none():
    assert get_embedding_provider("off") is None


def test_factory_api_needs_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert get_embedding_provider("api") is None
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    provider = get_embedding_provider("api")
    assert provider is not None and provider.name == "hosted-api"


def test_matcher_without_provider_falls_back_to_tfidf():
    # No embeddings -> engine must fall back so nothing breaks.
    matcher = SkillMatcher(embedding_provider=None)
    results = matcher.rank(["Kubernetes"], [job(["Kubernete"])])
    assert matcher.engine in ("tfidf", None)
    assert len(results) == 1
