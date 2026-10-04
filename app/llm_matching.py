"""LLM-assisted matching -- BETA / NOT WIRED IN.

This is a future enhancement scaffold, deliberately NOT connected to the live
matching endpoint. Everything here is off by default and the rest of the system
never imports it at request time, so it cannot affect production behavior, CI,
or test determinism.

What it is for
--------------
The shipped matcher (synonym layer + embeddings/TF-IDF similarity) is fast and
fully deterministic. A large language model can add a different kind of value
that a similarity score cannot:

  1. Skill extraction / normalization: read a candidate's free-text resume or a
     messy job description and pull out a clean list of skills.
  2. Explanation / re-ranking: given a candidate and a shortlist of already-
     matched jobs, write a short natural-language "why this is a good fit" and
     optionally re-order the top N by a more holistic judgment (transferable
     skills, seniority, adjacent tech).

Why it is beta
--------------
  - Requires an API key (secret management) and network access.
  - Costs money per call and adds latency.
  - Non-deterministic output makes it hard to unit-test and risks hallucination,
    so it must never silently drive scores users rely on.

How it would plug in (when promoted out of beta)
------------------------------------------------
The intended design keeps the deterministic matcher as the source of truth and
uses the LLM only as an *optional post-step* on the already-ranked shortlist:

    from app.matching import default_matcher
    scored = default_matcher.rank(profile.skills, jobs)          # deterministic
    top = scored[: payload.limit]
    if LlmReranker.enabled():
        top = LlmReranker().explain(profile, top)                # optional, additive

so if the LLM is disabled or fails, the endpoint returns the deterministic
result unchanged.
"""

from __future__ import annotations

import os
from typing import List, Optional, Tuple


class LlmReranker:
    """Optional LLM post-processor. Disabled unless explicitly turned on.

    This is a stub: the methods describe the intended contract but intentionally
    do not call any model yet. Promote this to a real implementation in its own
    pull request, behind the AJMS_LLM_RERANK flag, once the team has signed off
    on cost, latency, and a way to test it (e.g. recorded/mocked responses).
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.environ.get("AJMS_LLM_API_KEY")
        self.model = model or os.environ.get("AJMS_LLM_MODEL", "")

    @staticmethod
    def enabled() -> bool:
        # Two guards must BOTH be set, so this can never switch on by accident.
        return os.environ.get("AJMS_LLM_RERANK", "").lower() in {"1", "true", "yes"} \
            and bool(os.environ.get("AJMS_LLM_API_KEY"))

    def explain(self, profile, ranked: List[Tuple[float, object, List[str]]]):
        """Return the shortlist with an added natural-language explanation.

        BETA: not implemented. Returns the input unchanged so any accidental use
        is a no-op rather than a failure.
        """
        raise NotImplementedError(
            "LlmReranker.explain is a beta stub and is not implemented yet."
        )

    def extract_skills(self, free_text: str) -> List[str]:
        """Parse skills out of free-text (resume / job description).

        BETA: not implemented.
        """
        raise NotImplementedError(
            "LlmReranker.extract_skills is a beta stub and is not implemented yet."
        )
