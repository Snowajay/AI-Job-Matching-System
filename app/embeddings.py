"""Embedding providers for semantic skill matching.

This module adds a real AI-model layer on top of the existing matcher. An
"embedding" turns a piece of text into a numeric vector whose geometry captures
*meaning*, so two skills that are written completely differently but mean
related things (for example "PyTorch" and "Deep Learning", or "Scrum" and
"Agile") end up close together -- something the character-based TF-IDF step
cannot do.

Two providers are supported, tried in priority order so the system degrades
gracefully and never breaks CI:

1. LocalEmbeddingProvider  -- a pretrained sentence-transformer model
   (default: all-MiniLM-L6-v2) that runs locally/offline after a one-time
   download. This is the primary "AI model".
2. ApiEmbeddingProvider    -- a hosted embeddings API (OpenAI-compatible) used
   as a backup when the local model is not installed but an API key is set.

If neither is available, callers fall back to the TF-IDF similarity already in
matching.py, and if even that is missing, to synonym-aware exact matching.

Selection is controlled by environment variables (all optional):

    AJMS_EMBEDDINGS         auto | local | api | off   (default: auto)
    AJMS_EMBEDDING_MODEL    local model name           (default: all-MiniLM-L6-v2)
    AJMS_EMBEDDING_API_BASE API base URL               (default: OpenAI)
    AJMS_EMBEDDING_API_MODEL API model name            (default: text-embedding-3-small)
    OPENAI_API_KEY          key for the API provider   (enables api mode)

Nothing here is imported at module load that would fail if the optional
dependencies are missing; everything is guarded.
"""

from __future__ import annotations

import os
from typing import List, Optional, Sequence

# numpy is already a transitive dependency of scikit-learn, so it is safe to use.
try:
    import numpy as np
    _NUMPY = True
except Exception:  # pragma: no cover
    _NUMPY = False


def _l2_normalize(mat):
    """Row-normalize a 2D array so cosine similarity is a plain dot product."""
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


# Embedding lone technical tokens ("PyTorch" vs "Deep Learning") gives weak
# similarities; wrapping each skill in a little context sentence lifts genuinely
# related pairs substantially (measured: PyTorch~Deep Learning 36% -> 60%). This
# default was chosen from those measurements; override with AJMS_EMBEDDING_TEMPLATE
# (must contain "{skill}"), or set it to empty to embed bare tokens.
DEFAULT_TEMPLATE = "a technology skill: {skill}"


def effective_template() -> str:
    tpl = os.environ.get("AJMS_EMBEDDING_TEMPLATE")
    return DEFAULT_TEMPLATE if tpl is None else tpl


def _apply_template(texts: Sequence[str]) -> List[str]:
    """Wrap each bare skill in the effective context template, if one is set."""
    tpl = effective_template()
    if "{skill}" in tpl:
        return [tpl.format(skill=t) for t in texts]
    return list(texts)


class EmbeddingProvider:
    """Interface: turn a list of skill strings into normalized vectors."""

    name = "base"

    def available(self) -> bool:
        raise NotImplementedError

    def embed(self, texts: Sequence[str]):
        """Return an (n, d) float32 numpy array of L2-normalized vectors."""
        raise NotImplementedError


class LocalEmbeddingProvider(EmbeddingProvider):
    """Pretrained sentence-transformer model running locally (the AI model)."""

    name = "local-sentence-transformer"

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or os.environ.get(
            "AJMS_EMBEDDING_MODEL", "all-MiniLM-L6-v2"
        )
        self._model = None
        self._tried = False

    def _load(self):
        if self._tried:
            return self._model
        self._tried = True
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        except Exception:
            # Library missing or model could not be downloaded/loaded.
            self._model = None
        return self._model

    def available(self) -> bool:
        return _NUMPY and self._load() is not None

    def embed(self, texts: Sequence[str]):
        model = self._load()
        vecs = model.encode(_apply_template(texts), convert_to_numpy=True, normalize_embeddings=True)
        return np.asarray(vecs, dtype="float32")


class ApiEmbeddingProvider(EmbeddingProvider):
    """Hosted embeddings via an OpenAI-compatible REST API (the backup)."""

    name = "hosted-api"

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None,
                 model: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = (base_url or os.environ.get(
            "AJMS_EMBEDDING_API_BASE", "https://api.openai.com/v1"
        )).rstrip("/")
        self.model = model or os.environ.get(
            "AJMS_EMBEDDING_API_MODEL", "text-embedding-3-small"
        )

    def available(self) -> bool:
        return _NUMPY and bool(self.api_key)

    def embed(self, texts: Sequence[str]):
        # Kept dependency-free on purpose: standard library only.
        import json
        import urllib.request

        payload = json.dumps({"model": self.model, "input": _apply_template(texts)}).encode()
        req = urllib.request.Request(
            f"{self.base_url}/embeddings",
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        # Preserve input order (OpenAI returns an "index" per item).
        rows = sorted(data["data"], key=lambda d: d["index"])
        mat = np.asarray([r["embedding"] for r in rows], dtype="float32")
        return _l2_normalize(mat)


def get_embedding_provider(mode: Optional[str] = None) -> Optional[EmbeddingProvider]:
    """Pick an embedding provider according to config, or None to use TF-IDF.

    mode (or AJMS_EMBEDDINGS): auto (default), local, api, off.
      - auto: prefer the local model, then the hosted API, else None.
      - local/api: force that provider (returns None if it is not available).
      - off: never use embeddings (always None -> TF-IDF fallback).
    """
    if not _NUMPY:
        return None
    mode = (mode or os.environ.get("AJMS_EMBEDDINGS", "auto")).strip().lower()

    if mode == "off":
        return None
    if mode == "local":
        p = LocalEmbeddingProvider()
        return p if p.available() else None
    if mode == "api":
        p = ApiEmbeddingProvider()
        return p if p.available() else None

    # auto: local first (free/offline/private), then API as a backup.
    local = LocalEmbeddingProvider()
    if local.available():
        return local
    api = ApiEmbeddingProvider()
    if api.available():
        return api
    return None
