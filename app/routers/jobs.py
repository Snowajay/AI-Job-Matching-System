from typing import List

from fastapi import APIRouter, HTTPException

from app.models.job import JobListing


router = APIRouter(prefix="/jobs", tags=["jobs"])

jobs: List[JobListing] = []


@router.get("/", response_model=List[JobListing])
def get_jobs():
    return jobs


@router.post("/", response_model=JobListing, status_code=201)
def create_job(job: JobListing):
    jobs.append(job)
    return job


@router.get("/{job_id}", response_model=JobListing)
def get_job(job_id: str):
    for job in jobs:
        if job.job_id == job_id:
            return job
    raise HTTPException(status_code=404, detail="Job not found")
