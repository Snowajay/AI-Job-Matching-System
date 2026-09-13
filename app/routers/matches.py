from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models import Job
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

    candidate_skills = {skill.lower() for skill in profile.skills}

    # Read job listings from the shared database (the jobs table London
    # connected in PR #5) instead of a hardcoded in-memory list, so matching
    # runs against the same data everyone else on the team is using.
    jobs = db.query(Job).all()

    scored = []
    for job in jobs:
        job_skills = {skill.lower() for skill in job.required_skills}
        if not job_skills:
            continue
        overlap = candidate_skills & job_skills
        if not overlap:
            continue
        score = round(len(overlap) / len(job_skills) * 100, 2)
        reasons = [f"Matches required skill: {skill}" for skill in sorted(overlap)]
        scored.append((score, job, reasons))

    scored.sort(key=lambda item: item[0], reverse=True)
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

    return MatchResponse(candidate_id=payload.candidate_id, matches=matches)
