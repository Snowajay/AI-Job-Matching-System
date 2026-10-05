from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models import Job
from app.models.job import JobListing

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _to_response(job: Job) -> JobListing:
    return JobListing(
        job_id=job.job_id,
        title=job.title,
        company=job.company,
        required_skills=job.required_skills,
        posting_date=job.posting_date,
    )


@router.get("/", response_model=List[JobListing])
def get_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).all()
    return [_to_response(job) for job in jobs]


@router.post("/", response_model=JobListing, status_code=201)
def create_job(job: JobListing, db: Session = Depends(get_db)):
    existing = db.get(Job, job.job_id)

    if existing:
        existing.title = job.title
        existing.company = job.company
        existing.required_skills = job.required_skills
        existing.posting_date = job.posting_date
        record = existing
    else:
        record = Job(
            job_id=job.job_id,
            title=job.title,
            company=job.company,
            required_skills=job.required_skills,
            posting_date=job.posting_date,
        )
        db.add(record)

    db.commit()
    db.refresh(record)
    return _to_response(record)


@router.get("/{job_id}", response_model=JobListing)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return _to_response(job)
