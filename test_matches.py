"""Tests for the candidate profile and job matching endpoints.

Added by the Integration Lead to cover the seam between the candidate
profile and the matching endpoint: a complete profile returns ranked
matches, an incomplete profile is refused, and an unknown candidate 404s.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

FULL_PROFILE = {
    "skills": ["Python", "FastAPI", "PostgreSQL"],
    "experience": [{"title": "Backend Developer", "company": "Acme", "start_date": "2022-01-01"}],
    "education": [{"qualification": "B.S. Computer Science", "institution": "UMGC"}],
}


def test_upsert_profile_marks_ready():
    response = client.put("/api/v1/candidates/cand-1/profile", json=FULL_PROFILE)
    assert response.status_code == 200
    completeness = response.json()["completeness"]
    assert completeness["is_match_ready"] is True
    assert completeness["missing_fields"] == []


def test_match_returns_ranked_results():
    client.put("/api/v1/candidates/cand-2/profile", json=FULL_PROFILE)
    response = client.post("/api/v1/matches", json={"candidate_id": "cand-2", "limit": 5})
    assert response.status_code == 200
    matches = response.json()["matches"]
    assert len(matches) >= 1
    # ranks are sequential starting at 1
    assert [m["rank"] for m in matches] == list(range(1, len(matches) + 1))
    # scores are sorted from strongest to weakest
    scores = [m["score"] for m in matches]
    assert scores == sorted(scores, reverse=True)
    # the backend role shares the most skills, so it should rank first
    assert matches[0]["job_id"] == "job-101"


def test_match_incomplete_profile_returns_422():
    client.put(
        "/api/v1/candidates/cand-3/profile",
        json={"skills": ["Python"], "experience": [], "education": []},
    )
    response = client.post("/api/v1/matches", json={"candidate_id": "cand-3"})
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "INSUFFICIENT_PROFILE_DATA"
    assert "experience" in detail["missing_fields"]
    assert "education" in detail["missing_fields"]


def test_match_unknown_candidate_returns_404():
    response = client.post("/api/v1/matches", json={"candidate_id": "nope"})
    assert response.status_code == 404
