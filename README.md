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

The matching feature uses an AI-powered skill matcher (`app/matching.py`) that compares candidate skills to job-required skills by meaning rather than by exact text. It is built as layered AI, where each layer is tried in turn and the system degrades gracefully if a layer is unavailable, so the endpoint never fails.

1. Curated skill-synonym layer (knowledge-based): canonicalizes common abbreviations and variants, so "JS" is treated as "JavaScript", "Postgres" as "PostgreSQL", and "ML" as "Machine Learning".
2. Semantic embeddings (a real AI model, optional): a pretrained sentence-transformer (default `all-MiniLM-L6-v2`, in `app/embeddings.py`) turns each skill into a vector that encodes meaning, so skills that are written completely differently but mean related things still match, such as "PyTorch" with "Deep Learning" or "Scrum" with "Agile". A hosted embeddings API (OpenAI-compatible) can be used as a backup when the local model is not installed.
3. TF-IDF character n-gram vectors with cosine similarity (scikit-learn): the always-available fallback that catches closely related spellings and minor variants, such as "ReactJS" and "React" or a misspelled "Kubernete".

A similarity threshold keeps genuinely different skills apart. A job's match score is the percentage of its required skills the candidate has, where "has" allows semantic equivalence instead of only an exact string match. Jobs with no matched skills are excluded, the rest are ranked from highest to lowest score, and each result lists the matched skills as reasons, including how each was recognized (for example "AI recognized your 'JS' as JavaScript" or "AI semantic match: 'Deep Learning' ~ your 'PyTorch' (71% related)"). The matcher degrades gracefully: embeddings to TF-IDF to synonym-aware exact matching, so results stay clear and explainable in every configuration.

#### Enabling the embedding (AI-model) layer

The default install uses the synonym + TF-IDF layers, which need no extra setup and keep CI light. To turn on the semantic-embedding layer:

- Local model (recommended): `pip install -r requirements-embeddings.txt`. The first run downloads the model (~90 MB) and caches it; afterward it runs offline and private.
- Hosted API backup: set `OPENAI_API_KEY` (no extra packages needed). Optionally set `AJMS_EMBEDDING_API_BASE` / `AJMS_EMBEDDING_API_MODEL` for an OpenAI-compatible provider.

Selection is controlled by `AJMS_EMBEDDINGS` (`auto` by default; also `local`, `api`, or `off`). In `auto`, the matcher prefers the local model, then the API, then TF-IDF.

Tuning knobs (all optional environment variables), useful because a small model gives modest similarity to bare skill tokens:

- `AJMS_EMBEDDING_MODEL` — swap the local model (e.g. `all-mpnet-base-v2` is stronger but slower than the default `all-MiniLM-L6-v2`).
- `AJMS_EMBEDDING_TEMPLATE` — wraps each skill in context before embedding; defaults to `"a technology skill: {skill}"` because measurements showed it lifts related pairs substantially (e.g. PyTorch~Deep Learning 36%→60%). Must contain `{skill}`; set it to empty to embed bare tokens.
- `AJMS_EMBEDDING_THRESHOLD` — the semantic match cutoff (default `0.45`).

Distinct-skills guard: because a semantic model rates genuinely different skills like "Java"/"JavaScript" (~65%) as highly as real matches, `DISTINCT_GROUPS` in `app/matching.py` lists sets that must never cross-match (Java/JavaScript, C/C++/C#, React/React Native, ...). This keeps the precision of exact matching while embeddings add recall. `verify_embeddings.py` prints each pair's raw model similarity so you can tune against real numbers.

#### Future work (beta, not enabled)

`app/llm_matching.py` scaffolds an optional LLM post-step that could extract skills from a free-text resume or write a natural-language "why this is a good fit" explanation and re-rank the shortlist. It is deliberately not wired into the endpoint: it is non-deterministic, needs an API key, and would run only as an additive step on top of the deterministic result.
