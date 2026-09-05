from fastapi import APIRouter, HTTPException

from app.models.candidate import (
    CandidateProfile,
    CandidateProfileUpdate,
    compute_completeness,
)

router = APIRouter(prefix="/candidates", tags=["candidates"])

# In-memory store until a real database is wired up.
_profiles: dict[str, CandidateProfileUpdate] = {}


def get_stored_profile(candidate_id: str) -> CandidateProfileUpdate | None:
    """Used by other routers (e.g. matches) to read a candidate's saved profile."""
    return _profiles.get(candidate_id)


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
def upsert_candidate_profile(candidate_id: str, payload: CandidateProfileUpdate):
    _profiles[candidate_id] = payload
    return _to_response(candidate_id, payload)


@router.get("/{candidate_id}/profile", response_model=CandidateProfile)
def get_candidate_profile(candidate_id: str):
    profile = _profiles.get(candidate_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    return _to_response(candidate_id, profile)
