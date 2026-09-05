from typing import List

from fastapi import APIRouter

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
