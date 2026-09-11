from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.database import get_db
from app.db_models import Candidate
from app.models.candidate import (
    CandidateProfile,
    CandidateProfileUpdate,
    compute_completeness,
)

router = APIRouter(prefix="/candidates", tags=["candidates"])


def get_stored_profile(candidate_id: str, db: Session) -> CandidateProfileUpdate | None:
    record = db.get(Candidate, candidate_id)
    if record is None:
        return None
    return CandidateProfileUpdate(
        skills=record.skills,
        experience=record.experience,
        education=record.education,
    )


def _to_response(candidate_id: str, data: CandidateProfileUpdate) -> CandidateProfile:
    completeness = compute_completeness(data.skills, data.experience, data.education)
    return CandidateProfile(
        candidate_id=candidate_id,
        skills=data.skills,
        experience=data.experience,
        education=data.education,
        completeness=completeness,
    )


@router.put("/{candidate_id}/profile", response_model=CandidateProfile)
def upsert_candidate_profile(
    candidate_id: str, payload: CandidateProfileUpdate, db: Session = Depends(get_db)
):
    data = payload.model_dump(mode="json")
    stmt = pg_insert(Candidate).values(
        candidate_id=candidate_id,
        skills=data["skills"],
        experience=data["experience"],
        education=data["education"],
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[Candidate.candidate_id],
        set_={
            "skills": stmt.excluded.skills,
            "experience": stmt.excluded.experience,
            "education": stmt.excluded.education,
            "updated_at": func.now(),
        },
    )
    db.execute(stmt)
    db.commit()
    return _to_response(candidate_id, payload)


@router.get("/{candidate_id}/profile", response_model=CandidateProfile)
def get_candidate_profile(candidate_id: str, db: Session = Depends(get_db)):
    profile = get_stored_profile(candidate_id, db)
    if profile is None:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    return _to_response(candidate_id, profile)
