#!/usr/bin/env python3
"""
AI Skill Matcher - verification script
Integration Lead: Terrance Montgomery

Proves the AI-powered semantic matcher works and shows the value it adds over
the old exact-string matcher. Runs offline - no database and no server needed:

    python test_ai_matcher.py

For each scenario it prints what the OLD exact matcher would have scored and
what the NEW AI matcher scores, then checks the result. Exit code is 0 if every
check passes, 1 otherwise.
"""

import sys
from types import SimpleNamespace

try:
    from app.matching import SkillMatcher
    from app.matching import _SKLEARN_AVAILABLE
except Exception as exc:  # pragma: no cover
    print("Could not import the matcher. Run this from the repo root")
    print("(the folder that contains the 'app' directory), after installing")
    print("dependencies with:  pip install -r requirements.txt")
    print("Error:", exc)
    sys.exit(2)


def job(skills):
    return SimpleNamespace(required_skills=skills)


def exact_score(candidate, job_skills):
    """What the OLD matcher scored: case-insensitive exact skill overlap."""
    cand = {s.lower() for s in candidate}
    req = {s.lower() for s in job_skills}
    if not req:
        return 0.0
    overlap = cand & req
    return round(len(overlap) / len(req) * 100, 2) if overlap else 0.0


matcher = SkillMatcher()


def ai_match(candidate, job_skills):
    """Returns (score, reasons) from the AI matcher for a single job."""
    results = matcher.rank(candidate, [job(job_skills)])
    if not results:
        return 0.0, []
    score, _, reasons = results[0]
    return score, reasons


PASSED = 0
FAILED = 0


def check(label, condition, detail=""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"    [PASS] {label}")
    else:
        FAILED += 1
        print(f"    [FAIL] {label}" + (f"  -> {detail}" if detail else ""))


def scenario(title, candidate, job_skills):
    old = exact_score(candidate, job_skills)
    new, reasons = ai_match(candidate, job_skills)
    print(f"\n--- {title} ---")
    print(f"    Candidate skills : {candidate}")
    print(f"    Job requires     : {job_skills}")
    print(f"    OLD exact match  : {old:.2f}%")
    print(f"    NEW AI match     : {new:.2f}%")
    for r in reasons:
        print(f"        - {r}")
    return old, new


def main():
    print("=" * 64)
    print("AI Skill Matcher - verification")
    print("scikit-learn available:", _SKLEARN_AVAILABLE,
          "(semantic similarity on)" if _SKLEARN_AVAILABLE else "(synonym-only fallback)")
    print("=" * 64)

    print("\n### 1. The headline case: abbreviations and variants ###")
    old, new = scenario(
        "Candidate uses short forms the old matcher would miss",
        ["JS", "Postgres", "ML"],
        ["JavaScript", "PostgreSQL", "Machine Learning"],
    )
    check("AI matches all three equivalent skills (100%)", new == 100.0, f"got {new}")
    check("Old exact matcher scored this 0% (shows the value added)", old == 0.0, f"got {old}")

    print("\n### 2. Backward compatibility: exact skills still score the same ###")
    old, new = scenario(
        "Exact skill names",
        ["Python", "FastAPI", "PostgreSQL"],
        ["Python", "FastAPI", "PostgreSQL"],
    )
    check("Exact full match is still 100%", new == 100.0, f"got {new}")
    check("AI score equals old score for exact skills", new == old, f"ai={new} old={old}")

    old, new = scenario(
        "Partial exact overlap (1 of 4)",
        ["Python", "FastAPI", "PostgreSQL"],
        ["Python", "Spark", "AWS", "Kafka"],
    )
    check("Partial overlap stays at 25%", new == 25.0, f"got {new}")

    print("\n### 3. Unrelated skills are excluded ###")
    old, new = scenario(
        "No real overlap",
        ["Python", "FastAPI", "PostgreSQL"],
        ["Photoshop", "Illustrator"],
    )
    check("Unrelated job scores 0% (excluded)", new == 0.0, f"got {new}")

    print("\n### 4. It does not over-match: false friends stay apart ###")
    old, new = scenario(
        "Java is NOT JavaScript",
        ["Java"],
        ["JavaScript"],
    )
    check("Java does not match JavaScript", new == 0.0, f"got {new}")

    print("\n### 5. It tolerates close variants and misspellings ###")
    old, new = scenario(
        "Variant spellings and a typo",
        ["ReactJS", "Postgres", "Kubernetes"],
        ["React", "PostgreSQL", "Kubernete"],
    )
    check("Variants and typo all match (100%)", new == 100.0, f"got {new}")

    total = PASSED + FAILED
    print("\n" + "=" * 64)
    print(f"RESULT: {PASSED}/{total} checks passed, {FAILED} failed")
    if FAILED == 0:
        print("The AI skill matcher is working.")
    print("=" * 64)
    sys.exit(0 if FAILED == 0 else 1)


if __name__ == "__main__":
    main()
