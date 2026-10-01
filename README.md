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
```

### Database Configuration

The backend uses PostgreSQL for persistent storage of candidate profiles and job listings. Database connection information is configured through environment variables. The `.env.example` file provides the required format for the database configuration.

Before starting the backend, create a `.env` file based on `.env.example` and provide the appropriate PostgreSQL database connection information.

### Run the Backend

With the virtual environment activated, start the FastAPI application with:

```bash
uvicorn app.main:app --reload
```

The backend API will run locally at `http://127.0.0.1:8000`.

FastAPI also provides interactive API documentation at `http://127.0.0.1:8000/docs`.


### Frontend

Open a second terminal window and navigate to the frontend directory:

```bash
cd frontend
npm install
npm run dev
```

The React frontend will run locally through Vite. By default, it can be accessed at `http://localhost:5173`.

To create a production build of the frontend, run:

```bash
npm run build
```


## API Documentation

The FastAPI backend uses the `/api/v1` prefix for the candidate, job, and matching endpoints. Interactive API documentation is also available through FastAPI at `/docs` while the backend is running.

### Candidate Endpoints

- `PUT /api/v1/candidates/{candidate_id}/profile` - Creates or updates a candidate profile, including skills, experience, and education.
- `GET /api/v1/candidates/{candidate_id}/profile` - Retrieves an existing candidate profile. A profile that does not exist returns a 404 response.

### Job Endpoints

- `GET /api/v1/jobs/` - Retrieves all job listings stored in the database.
- `POST /api/v1/jobs/` - Creates a new job listing or updates an existing listing with the same job ID.
- `GET /api/v1/jobs/{job_id}` - Retrieves a specific job listing. A job that does not exist returns a 404 response.

### Matching Endpoint

- `POST /api/v1/matches` - Generates ranked job matches for a candidate.

The matching process compares the candidate's skills with the required skills for each job stored in the database. The match score represents the percentage of the job's required skills that are present in the candidate's profile. Results are ranked from the highest match score to the lowest.

A candidate must have skills, experience, and education information before matching can be performed. A missing candidate profile returns a 404 response, while an incomplete profile returns a 422 response.


## User Guide

The application provides a web interface for creating a candidate profile, viewing available jobs, and generating job matches.

### 1. Create or Update a Candidate Profile

Enter the candidate's information in the Candidate Profile section. The profile includes:

- Skills
- Work experience
- Education

Save the profile before requesting job matches. All three sections must contain information before the profile is considered ready for matching.

### 2. View Job Listings

The Job Listings section displays the jobs currently stored in the database. Each listing includes information such as the job title, company, required skills, and posting date.

### 3. Generate Job Matches

After completing the candidate profile, use the Job Matches section to request matches. The system compares the candidate's skills with the required skills for the available jobs.

Matching jobs are ranked by score, with the strongest skill match appearing first. The results also identify which required skills matched the candidate's profile.

### 4. Review Match Results

Review the ranked results to compare the candidate's skills with the available positions. A higher percentage indicates that the candidate possesses a greater percentage of the skills required by that job.


## Testing and Code Quality

The backend includes automated integration tests using Pytest. The test suite validates the matching workflow as well as error handling for incomplete and missing candidate profiles.

To run the backend tests:

```bash
pytest
```

To run the tests with a coverage report:

```bash
pytest --cov=app --cov-report=term-missing
```

During final system validation, all 4 automated backend tests passed. The backend achieved 92% total code coverage across 196 statements.

Coverage results for key API routes included:

- Candidate routes: 87%
- Job routes: 76%
- Matching routes: 94%

The frontend was also validated using a production Vite build. The production build completed successfully.

## Continuous Integration

The project uses GitHub Actions for continuous integration. The workflow is located at:

`.github/workflows/ci.yml`

The CI workflow automatically validates both the backend and frontend.

The pipeline performs the following tasks:

- Checks out the repository
- Configures the Python environment
- Installs backend dependencies
- Creates the test database tables
- Runs the automated backend tests
- Configures Node.js
- Installs frontend dependencies
- Builds the React frontend

During final validation, the GitHub Actions workflow completed successfully on the `main` branch. The complete workflow finished in 42 seconds. The backend test job completed successfully in 38 seconds, and the frontend build job completed successfully in 7 seconds.


## System Architecture and Matching Approach

The application follows a three-tier structure consisting of a React frontend, FastAPI backend, and PostgreSQL database.

The React frontend provides the user interface for candidate profiles, job listings, and match results. The frontend communicates with the FastAPI backend through REST API endpoints. The backend handles application logic and uses SQLAlchemy to communicate with the PostgreSQL database.

Candidate profiles and job listings are stored in the shared database so that the matching process uses the same data available throughout the application.

### Matching Approach

The current matching feature uses a skill-based ranking algorithm. Candidate skills and job-required skills are normalized to lowercase before comparison. The system identifies overlapping skills and calculates a match score using the percentage of required job skills found in the candidate's profile.

Jobs with no matching skills are excluded from the results. The remaining jobs are ranked from highest to lowest score, and the interface displays the matching skills as reasons for each result.

This approach provides a clear and explainable foundation for job matching. Future development could expand the system with machine learning or natural language processing to evaluate factors beyond direct skill overlap.
