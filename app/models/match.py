from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

from app.models.job import JobListing


class MatchRequest(BaseModel):
    candidate_id: str
    limit: Optional[int] = Field(default=5, ge=1, le=50)


class MatchResult(BaseModel):
    rank: int
    job_id: str
    score: float
    reasons: List[str]
    posting_date: date


class MatchResponse(BaseModel):
    candidate_id: str
    matches: List[MatchResult]
    # Which AI engine actually produced these matches, so the UI can show it.
    engine: Optional[str] = None          # "embeddings" | "tfidf" | "synonym"
    engine_label: Optional[str] = None    # human-friendly label for the UI
