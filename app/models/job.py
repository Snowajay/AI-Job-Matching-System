from typing import List, Optional

from pydantic import BaseModel


class JobListing(BaseModel):
    title: str
    required_skills: List[str]
    posting_date: Optional[str] = None

