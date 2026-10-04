"""Unit tests for the AI skill matcher.

These test the semantic matching logic directly (no database needed): that
synonyms and abbreviations match, that exact matching still scores the same as
before, that unrelated skills are excluded, and that close variants match via
similarity while false friends (JavaScript vs Java) do not.
"""

from types import SimpleNamespace

from app.matching import SkillMatcher


def job(skills):
    return SimpleNamespace(required_skills=skills)


def test_synonyms_and_abbreviations_match():
    matcher = SkillMatcher()
    results = matcher.rank(
        ["JS", "Postgres", "ML"],
        [job(["JavaScript", "PostgreSQL", "Machine Learning"])],
    )
    assert len(results) == 1
    score, _, reasons = results[0]
    # All three equivalent skills should be recognized, so it is a full match.
    assert score == 100.0
    assert len(reasons) == 3


def test_exact_matching_is_backward_compatible():
    matcher = SkillMatcher()
    results = matcher.rank(
        ["Python", "FastAPI", "PostgreSQL"],
        [
            job(["Python", "FastAPI", "PostgreSQL"]),  # exact full match
            job(["Python", "Spark", "AWS", "Kafka"]),  # 1 of 4
            job(["Photoshop", "Illustrator"]),         # no overlap
        ],
    )
    scores = {tuple(j.required_skills): s for s, j, _ in results}
    assert scores[("Python", "FastAPI", "PostgreSQL")] == 100.0
    assert scores[("Python", "Spark", "AWS", "Kafka")] == 25.0
    # The unrelated job has no matched skills and must be excluded.
    assert ("Photoshop", "Illustrator") not in scores


def test_unrelated_skills_are_excluded():
    matcher = SkillMatcher()
    results = matcher.rank(["Python"], [job(["Photoshop", "Illustrator"])])
    assert results == []


def test_close_variant_matches_but_false_friend_does_not():
    matcher = SkillMatcher()
    # "Kubernete" is a near-spelling of "Kubernetes" and should match by
    # similarity; "Java" is not "JavaScript" and should not.
    results = matcher.rank(
        ["Kubernetes", "JavaScript"],
        [job(["Kubernete"]), job(["Java"])],
    )
    matched_skill_sets = {tuple(j.required_skills) for _, j, _ in results}
    assert ("Kubernete",) in matched_skill_sets
    assert ("Java",) not in matched_skill_sets
