# AI-Job-Matching-System
CMSC 495 Team Project

## API Documentation

Base path for all endpoints: `/api/v1`

All responses are JSON. Error responses don't yet follow one consistent shape: most lookup
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

Returns all stored job listings.

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

#### Create a Job

```
POST /api/v1/jobs/
```

Adds a new job listing. This does not currently check for an existing `job_id` before
inserting, so posting the same `job_id` twice adds a duplicate entry rather than updating
the original.

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

Scores a candidate's profile against a fixed set of sample job listings using skill overlap,
and returns a ranked list. Note: this does not currently read from the Job Listings endpoints
above — see Data Model Summary.

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
      "reasons": ["Matches required skill: python", "Matches required skill: fastapi"],
      "posting_date": "2026-08-12"
    }
  ]
}
```

Scores are on a 0 to 100 scale, a higher score means a stronger match. Jobs with no skill
overlap are excluded from the results rather than returned with a score of zero.

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

Candidate data is persisted in a shared Postgres database (Supabase), accessed through
SQLAlchemy.

**candidates table**

| Column | Type |
|---|---|
| candidate_id | text, primary key |
| skills | jsonb |
| experience | jsonb |
| education | jsonb |
| updated_at | timestamptz |

Skills, experience, and education are stored as JSON rather than normalized into separate
tables. This was a deliberate tradeoff for the alpha release, it keeps the schema simple and
flexible, at the cost of not being able to efficiently query or filter candidates by individual
skill at the database level. This is documented as known technical debt to revisit if the
system needs to scale past its current scope.

Job listings are not persisted yet. `POST`/`GET` on the Job Listings endpoints read and write
an in-memory list inside the running process, which resets on every restart and isn't shared
across workers. The matching endpoint doesn't read that list either — it scores against a
fixed sample list defined directly in `app/routers/matches.py`. Backing jobs with a real table
(matching the `candidates` pattern) and wiring matching to read from it is outstanding work.

Row Level Security is enabled on both the candidates and jobs tables in Supabase. Neither
table is reachable through Supabase's own client side API; the FastAPI backend is the only
consumer, connecting directly through SQLAlchemy.
