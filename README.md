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

Base path for all endpoints: `/api/v1`. Interactive API documentation is also available through FastAPI at `/docs` while the backend is running.

All responses are JSON. Error responses don't follow one consistent shape: most lookup
failures (profile/job not found) return a plain string in `detail`, e.g.

```json
{
  "detail": "Candidate profile not found"
}
```

The matching endpoint's 422 is the one exception, returning a structured object:

```json
{
  "detail": {
    "code": "INSUFFICIENT_PROFILE_DATA",
    "missing_fields": ["experience", "education"]
  }
}
```

### Candidate Profile

#### Create or Update a Candidate Profile

```
PUT /api/v1/candidates/{candidate_id}/profile
```

Creates a new candidate profile or updates an existing one (upsert). Calling this again with
the same `candidate_id` replaces the stored profile rather than creating a duplicate.

**Request body**

```json
{
  "skills": ["Python", "SQL"],
  "experience": [
    {
      "title": "Backend Developer",
      "company": "Acme",
      "start_date": "2022-01-01",
      "end_date": null,
      "description": "Built internal tooling"
    }
  ],
  "education": [
    {
      "qualification": "BSc Computer Science",
      "institution": "State University",
      "field_of_study": "Computer Science"
    }
  ]
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| skills | array of strings | no | Defaults to `[]` if omitted |
| experience | array of objects | no | Defaults to `[]`; can be empty |
| experience[].title | string | yes | |
| experience[].company | string | yes | |
| experience[].start_date | date | yes | ISO format YYYY-MM-DD |
| experience[].end_date | date | no | Null if current |
| experience[].description | string | no | |
| education | array of objects | no | Defaults to `[]`; can be empty |
| education[].qualification | string | yes | |
| education[].institution | string | yes | |
| education[].field_of_study | string | no | |

**Response, 200 OK**

```json
{
  "candidate_id": "cand-1",
  "skills": ["Python", "SQL"],
  "experience": [...],
  "education": [...],
  "completeness": {
    "percentage": 100.0,
    "is_match_ready": true,
    "missing_fields": []
  }
}
```

`completeness` is calculated on every request, not stored. `is_match_ready` must be `true`
before this candidate can be scored against jobs.

#### Retrieve a Candidate Profile

```
GET /api/v1/candidates/{candidate_id}/profile
```

Returns the same shape as the PUT response.

**Response, 404 Not Found**, if no profile exists for the given `candidate_id`.

### Job Listings

#### List Jobs

```
GET /api/v1/jobs/
```

Returns all job listings stored in the `jobs` table.

**Response, 200 OK**

```json
[
  {
    "job_id": "job-101",
    "title": "Backend Engineer",
    "company": "Northwind Systems",
    "required_skills": ["Python", "FastAPI", "PostgreSQL"],
    "posting_date": "2026-08-12"
  }
]
```

#### Create or Update a Job

```
POST /api/v1/jobs/
```

Creates a new job listing, or updates the existing one if a job with the same `job_id`
already exists (upsert), matching the candidate profile pattern above.

**Request body**

```json
{
  "job_id": "job-101",
  "title": "Backend Engineer",
  "company": "Northwind Systems",
  "required_skills": ["Python", "FastAPI", "PostgreSQL"],
  "posting_date": "2026-08-12"
}
```

**Response, 201 Created**, returns the saved job.

#### Retrieve a Single Job

```
GET /api/v1/jobs/{job_id}
```

**Response, 404 Not Found**, if no job exists with that `job_id`.

### Matching

#### Generate Ranked Matches for a Candidate

```
POST /api/v1/matches
```

Scores a candidate's profile against every job listing stored in the `jobs` table (the same
data served by the Job Listings endpoints above) and returns a ranked list. Scoring uses an
AI skill matcher rather than plain exact-text overlap — a skill-synonym layer, semantic
embeddings, and TF-IDF similarity are tried in turn, so skills written differently (`"JS"` vs
`"JavaScript"`, `"PyTorch"` vs `"Deep Learning"`) can still match. See System Architecture and
Matching Approach below for how the matcher is layered and configured.

**Request body**

```json
{
  "candidate_id": "cand-1",
  "limit": 5
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| candidate_id | string | yes | Must reference an existing, complete profile |
| limit | integer | no | Default 5, min 1, max 50 |

**Response, 200 OK**

```json
{
  "candidate_id": "cand-1",
  "matches": [
    {
      "rank": 1,
      "job_id": "job-101",
      "score": 75.0,
      "reasons": ["Matches required skill: python", "AI recognized your 'JS' as JavaScript"],
      "posting_date": "2026-08-12"
    }
  ],
  "engine": "tfidf",
  "engine_label": "AI keyword matching (TF-IDF + synonyms)"
}
```

`engine` identifies which matching layer actually produced the results (`"embeddings"`,
`"tfidf"`, or `"synonym"`); `engine_label` is a human-readable version of the same, for
display in the UI. Scores are on a 0 to 100 scale, a higher score means a stronger match.
Jobs with no matched skills are excluded from the results rather than returned with a score
of zero.

**Response, 404 Not Found**, if `candidate_id` does not reference an existing profile.

**Response, 422 Unprocessable Entity**, if the candidate's profile exists but is not complete
enough to match reliably:

```json
{
  "detail": {
    "code": "INSUFFICIENT_PROFILE_DATA",
    "missing_fields": ["experience", "education"]
  }
}
```

### Data Model Summary

Candidate and job data are both persisted in the shared Postgres database (Supabase),
accessed through SQLAlchemy.

**candidates table**

| Column | Type |
|---|---|
| candidate_id | text, primary key |
| skills | jsonb |
| experience | jsonb |
| education | jsonb |
| updated_at | timestamptz |

**jobs table**

| Column | Type |
|---|---|
| job_id | text, primary key |
| title | text |
| company | text |
| required_skills | jsonb |
| posting_date | date |

Skills, experience, and education (on candidates) and required_skills (on jobs) are stored
as JSON rather than normalized into separate tables. This was a deliberate tradeoff for the
alpha release, it keeps the schema simple and flexible, at the cost of not being able to
efficiently query or filter by individual skill at the database level. This is documented as
known technical debt to revisit if the system needs to scale past its current scope.

Row Level Security is enabled on both the candidates and jobs tables in Supabase. Neither
table is reachable through Supabase's own client side API; the FastAPI backend is the only
consumer, connecting directly through SQLAlchemy.


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

The backend includes automated tests using Pytest: integration tests covering the matching workflow and error handling for incomplete and missing candidate profiles, plus dedicated tests for the AI matching logic and the embeddings layer.

To run the backend tests:

```bash
pytest
```

To run the tests with a coverage report:

```bash
pytest --cov=app --cov-report=term-missing
```

During final system validation, after the AI matching integration, all 15 automated backend tests passed. The backend achieved 87% total code coverage across 395 statements.

Coverage results for key modules and routes included:

- Candidate routes: 87%
- Job routes: 76%
- Matching routes: 100%
- Matching logic: 93%
- Embeddings module: 85%

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
