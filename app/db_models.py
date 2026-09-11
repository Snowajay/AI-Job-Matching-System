from sqlalchemy import Column, Date, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    candidate_id = Column(String, primary_key=True)
    skills = Column(JSONB, nullable=False, default=list)
    experience = Column(JSONB, nullable=False, default=list)
    education = Column(JSONB, nullable=False, default=list)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    required_skills = Column(JSONB, nullable=False, default=list)
    posting_date = Column(Date, nullable=False)
