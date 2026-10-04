from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models import Job
from app.matching import default_matcher
from app.models.candidate import compute_completeness
from app.models.match import MatchRequest, MatchResponse, MatchResult
from app.routers.candidates import get_stored_profile

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("", response_model=MatchResponse)
def create_matches(payload: MatchRequest, db: Session = Depends(get_db)):
    profile = get_stored_profile(payload.candidate_id, db)
    if profile is None:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

    completeness = compute_completeness(
        profile.skills, profile.experience, profile.education
    )
    if not completeness.is_match_ready:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INSUFFICIENT_PROFILE_DATA",
                "missing_fields": completeness.missing_fields,
            },
        )

    # Read job listings from the shared database (the jobs table connected in
    # PR #5) instead of a hardcoded in-memory list, so matching runs against the
    # same data everyone else on the team is using.
    jobs = db.query(Job).all()

    # Score with the AI skill matcher (semantic synonym + TF-IDF similarity)
    # rather than exact string overlap, so equivalent skills written
    # differently ("JS"/"JavaScript", "Postgres"/"PostgreSQL") still match.
    scored = default_matcher.rank(profile.skills, jobs)
    top_matches = scored[: payload.limit]

    matches = [
        MatchResult(
            rank=index + 1,
            job_id=job.job_id,
            score=score,
            reasons=reasons,
            posting_date=job.posting_date,
        )
        for index, (score, job, reasons) in enumerate(top_matches)
    ]

    engine = default_matcher.engine or "synonym"
    engine_label = {
        "embeddings": "AI semantic model (neural embeddings)",
        "tfidf": "AI keyword matching (TF-IDF + synonyms)",
        "synonym": "synonym matching",
    }.get(engine, engine)

    return MatchResponse(
        candidate_id=payload.candidate_id,
        matches=matches,
        engine=engine,
        engine_label=engine_label,
    )
