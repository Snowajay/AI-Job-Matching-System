from datetime import date

from fastapi import APIRouter, HTTPException

from app.models.candidate import compute_completeness
from app.models.match import JobListing, MatchRequest, MatchResponse, MatchResult
from app.routers.candidates import get_stored_profile

router = APIRouter(prefix="/matches", tags=["matches"])

# Sample job listings standing in for a real jobs data source.
SAMPLE_JOBS: list[JobListing] = [
    JobListing(
        job_id="job-101",
        title="Backend Engineer",
        company="Northwind Systems",
        required_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
        posting_date=date(2026, 8, 12),
    ),
    JobListing(
        job_id="job-102",
        title="Data Engineer",
        company="Lumen Analytics",
        required_skills=["Python", "SQL", "Airflow", "AWS"],
        posting_date=date(2026, 8, 20),
    ),
    JobListing(
        job_id="job-103",
        title="Frontend Engineer",
        company="Brightside Labs",
        required_skills=["JavaScript", "React", "TypeScript", "CSS"],
        posting_date=date(2026, 8, 25),
    ),
    JobListing(
        job_id="job-104",
        title="Full Stack Engineer",
        company="Northwind Systems",
        required_skills=["Python", "React", "FastAPI", "TypeScript"],
        posting_date=date(2026, 9, 1),
    ),
    JobListing(
        job_id="job-105",
        title="Machine Learning Engineer",
        company="Vector Health",
        required_skills=["Python", "PyTorch", "SQL", "AWS"],
        posting_date=date(2026, 9, 3),
    ),
]


@router.post("", response_model=MatchResponse)
def create_matches(payload: MatchRequest):
    profile = get_stored_profile(payload.candidate_id)
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

    scored = []
    for job in SAMPLE_JOBS:
        job_skills = {skill.lower() for skill in job.required_skills}
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
