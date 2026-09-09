from typing import List

from datetime import date

from pydantic import BaseModel


class JobListing(BaseModel):
    job_id: str
    title: str
    company: str
    required_skills: List[str]
    posting_date: date
