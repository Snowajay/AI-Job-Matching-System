# AI Job Matching System

## Overview

The AI Job Matching System is a CMSC 495 team project that helps match candidates with job opportunities based on their profile information and skills.

The system uses a React frontend, a FastAPI backend, and a PostgreSQL database. Candidates can create and update a profile, view available job listings, and receive ranked job matches based on their skills.

## Main Features

- Create and update candidate profiles
- Store candidate skills, experience, and education
- View available job listings
- Match candidates with jobs
- Rank job matches by match score
- Store candidate and job data in PostgreSQL
- Connect the React frontend to the FastAPI backend
- Run automated backend tests and frontend builds through CI

## Technologies Used

- React
- Vite
- FastAPI
- Python
- PostgreSQL
- Supabase
- SQLAlchemy
- GitHub Actions
- Pytest

## Project Structure

- `app/` - FastAPI backend, API routes, database models, and matching logic
- `frontend/` - React user interface
- `test_matches.py` - Backend integration tests
- `.github/workflows/ci.yml` - CI workflow for automated testing and frontend builds
- `.env.example` - Instructions for database environment configuration

## Setup

### Backend

Create and activate a Python virtual environment, then install the required packages:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt