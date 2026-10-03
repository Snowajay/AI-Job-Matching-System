#!/usr/bin/env python3
"""
AI Job Matching System - End-to-end smoke test
Integration Lead: Terrance Montgomery

Runs the whole user flow against a running API and prints PASS/FAIL for each
check. Uses only the Python standard library, so there is nothing to install:
if you can run the backend, you can run this.

USAGE (PowerShell or any terminal):
    python smoke_test.py
    python smoke_test.py http://localhost:8000
    $env:BASE_URL="http://localhost:8000"; python smoke_test.py

The script is safe to run over and over: it uses fixed "smoke-" ids and both
create routes upsert, so each run overwrites its own test data instead of
piling up duplicates. Exit code is 0 if every check passes, 1 otherwise.
"""

import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("BASE_URL", "http://localhost:8000")).rstrip("/")

# ---- tiny HTTP helper (stdlib only) -----------------------------------------

def request(method, path, body=None):
    """Return (status_code, parsed_json_or_text). Never raises on HTTP errors."""
    url = BASE_URL + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw
    except urllib.error.URLError as e:
        print(f"\n  Could not reach {url}")
        print(f"  Reason: {e.reason}")
        print("  Is the backend running? Start it with:  uvicorn app.main:app --reload")
        sys.exit(2)

# ---- result tracking ---------------------------------------------------------

PASSED = 0
FAILED = 0

def check(label, condition, detail=""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  [PASS] {label}")
    else:
        FAILED += 1
        print(f"  [FAIL] {label}")
        if detail:
            print(f"         {detail}")

def section(title):
    print(f"\n=== {title} ===")

# ---- test data ---------------------------------------------------------------

FULL_PROFILE = {
    "skills": ["Python", "FastAPI", "PostgreSQL"],
    "experience": [
        {"title": "Backend Developer", "company": "Acme", "start_date": "2022-01-01"}
    ],
    "education": [
        {"qualification": "B.S. Computer Science", "institution": "UMGC"}
    ],
}

PERFECT_JOB = {
    "job_id": "smoke-job-perfect",
    "title": "Backend Engineer",
    "company": "Test Co",
    "required_skills": ["Python", "FastAPI", "PostgreSQL"],
    "posting_date": "2026-09-01",
}

PARTIAL_JOB = {
    "job_id": "smoke-job-partial",
    "title": "Data Engineer",
    "company": "Other Co",
    "required_skills": ["Python", "Spark", "AWS", "Kafka"],
    "posting_date": "2026-09-02",
}

UNRELATED_JOB = {
    "job_id": "smoke-job-unrelated",
    "title": "Graphic Designer",
    "company": "Studio",
    "required_skills": ["Photoshop", "Illustrator"],
    "posting_date": "2026-09-03",
}

# ---- the flow ----------------------------------------------------------------

def main():
    print(f"Testing AI Job Matching System at: {BASE_URL}")

    section("1. API is up (health check)")
    status, body = request("GET", "/")
    check("GET / returns 200", status == 200, f"got {status}")
    check("root message present", isinstance(body, dict) and "message" in body, f"got {body}")

    section("2. Seed jobs (POST /api/v1/jobs/)")
    for job in (PERFECT_JOB, PARTIAL_JOB, UNRELATED_JOB):
        status, body = request("POST", "/api/v1/jobs/", job)
        check(f"create job '{job['job_id']}' returns 201", status == 201, f"got {status}: {body}")

    status, body = request("GET", "/api/v1/jobs/")
    ids = [j["job_id"] for j in body] if isinstance(body, list) else []
    check("GET /api/v1/jobs/ lists all three seeded jobs",
          all(j["job_id"] in ids for j in (PERFECT_JOB, PARTIAL_JOB, UNRELATED_JOB)),
          f"ids seen: {ids}")

    status, body = request("GET", f"/api/v1/jobs/{PERFECT_JOB['job_id']}")
    check("GET single job by id returns 200", status == 200, f"got {status}")

    section("3. Create a complete candidate profile (PUT /api/v1/candidates/{id}/profile)")
    status, body = request("PUT", "/api/v1/candidates/smoke-cand-full/profile", FULL_PROFILE)
    check("upsert full profile returns 200", status == 200, f"got {status}: {body}")
    comp = body.get("completeness", {}) if isinstance(body, dict) else {}
    check("full profile is match-ready", comp.get("is_match_ready") is True, f"completeness={comp}")
    check("no missing fields on full profile", comp.get("missing_fields") == [], f"missing={comp.get('missing_fields')}")

    status, body = request("GET", "/api/v1/candidates/smoke-cand-full/profile")
    check("GET profile round-trips the skills we stored",
          isinstance(body, dict) and body.get("skills") == FULL_PROFILE["skills"],
          f"got {body.get('skills') if isinstance(body, dict) else body}")

    section("4. Run a match (POST /api/v1/matches)")
    status, body = request("POST", "/api/v1/matches", {"candidate_id": "smoke-cand-full", "limit": 5})
    check("match returns 200", status == 200, f"got {status}: {body}")
    matches = body.get("matches", []) if isinstance(body, dict) else []
    check("at least one match returned", len(matches) >= 1, f"count={len(matches)}")

    if matches:
        ranks = [m["rank"] for m in matches]
        scores = [m["score"] for m in matches]
        check("ranks are sequential starting at 1", ranks == list(range(1, len(matches) + 1)), f"ranks={ranks}")
        check("scores sorted strongest to weakest", scores == sorted(scores, reverse=True), f"scores={scores}")
        perfect = next((m for m in matches if m["job_id"] == PERFECT_JOB["job_id"]), None)
        check("perfect-match job is in the results", perfect is not None, f"ids={[m['job_id'] for m in matches]}")
        if perfect is not None:
            # A job that matches every required skill must score 100 and sit at
            # the top score. (It shares rank 1 only if other 100% jobs exist.)
            check("perfect-match job scores 100.0", perfect["score"] == 100.0, f"score={perfect['score']}")
            check("perfect-match job is tied for the top score",
                  perfect["score"] == matches[0]["score"], f"top score={matches[0]['score']}")
        matched_ids = [m["job_id"] for m in matches]
        check("unrelated job (no skill overlap) is excluded",
              UNRELATED_JOB["job_id"] not in matched_ids, f"matched={matched_ids}")
        check("each match carries at least one reason",
              all(len(m.get("reasons", [])) >= 1 for m in matches),
              "a match had no reasons")

    section("5. Error paths behave correctly")
    incomplete = {"skills": ["Python"], "experience": [], "education": []}
    request("PUT", "/api/v1/candidates/smoke-cand-incomplete/profile", incomplete)
    status, body = request("POST", "/api/v1/matches", {"candidate_id": "smoke-cand-incomplete"})
    check("incomplete profile is refused with 422", status == 422, f"got {status}")
    detail = body.get("detail", {}) if isinstance(body, dict) else {}
    check("422 names the INSUFFICIENT_PROFILE_DATA code",
          isinstance(detail, dict) and detail.get("code") == "INSUFFICIENT_PROFILE_DATA", f"detail={detail}")
    check("422 lists experience and education as missing",
          isinstance(detail, dict) and {"experience", "education"} <= set(detail.get("missing_fields", [])),
          f"missing={detail.get('missing_fields') if isinstance(detail, dict) else detail}")

    status, body = request("POST", "/api/v1/matches", {"candidate_id": "does-not-exist"})
    check("unknown candidate returns 404", status == 404, f"got {status}")

    status, body = request("GET", "/api/v1/jobs/no-such-job")
    check("unknown job returns 404", status == 404, f"got {status}")

    # ---- summary -------------------------------------------------------------
    total = PASSED + FAILED
    print("\n" + "=" * 60)
    print(f"RESULT: {PASSED}/{total} checks passed, {FAILED} failed")
    print("=" * 60)
    sys.exit(0 if FAILED == 0 else 1)


if __name__ == "__main__":
    main()
