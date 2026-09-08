from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class Experience(BaseModel):
    title: str
    company: str
    start_date: date
    end_date: Optional[date] = None
    description: Optional[str] = None


class Education(BaseModel):
    qualification: str
    institution: str
    field_of_study: Optional[str] = None


class CandidateProfileUpdate(BaseModel):
    skills: List[str] = []
    experience: List[Experience] = []
    education: List[Education] = []


class Completeness(BaseModel):
    percentage: float
    is_match_ready: bool
    missing_fields: List[str]


class CandidateProfile(BaseModel):
    candidate_id: str
    skills: List[str]
    experience: List[Experience]
    education: List[Education]
    completeness: Completeness


def compute_completeness(
    skills: List[str], experience: List[Experience], education: List[Education]
) -> Completeness:
    sections = {
        "skills": bool(skills),
        "experience": bool(experience),
        "education": bool(education),
    }
    missing_fields = [name for name, present in sections.items() if not present]
    percentage = round((len(sections) - len(missing_fields)) / len(sections) * 100, 2)

    return Completeness(
        percentage=percentage,
        is_match_ready=not missing_fields,
        missing_fields=missing_fields,
    )
