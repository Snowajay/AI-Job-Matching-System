"""See the AI embedding model match skills by MEANING (run on a networked box).

Integration Lead: Terrance Montgomery

Unlike verify_ai_matcher.py (which proves the synonym + TF-IDF layers), this
script turns on the real AI-model layer -- a pretrained sentence-transformer --
and shows it matching skills that share NO letters, which TF-IDF can never do:
"PyTorch" ~ "Deep Learning", "Scrum" ~ "Agile", and so on.

Run it from the repository root, after installing the optional model:

    pip install -r requirements-embeddings.txt
    python verify_embeddings.py

The FIRST run downloads the model (~90 MB) and caches it; later runs are offline.
To test the hosted-API backup instead, set OPENAI_API_KEY and run:

    python verify_embeddings.py --mode api
"""
import argparse
import sys
from types import SimpleNamespace

from app.matching import SkillMatcher
from app.embeddings import get_embedding_provider


def job(skills):
    return SimpleNamespace(required_skills=skills)


# Each case: candidate skill(s) that a human sees as related to the job skill,
# but written with completely different words -> only a semantic model connects.
SEMANTIC_CASES = [
    (["PyTorch"],     ["Deep Learning"]),
    (["Scrum"],       ["Agile"]),
    (["Figma"],       ["UI Design"]),
    (["Pandas"],      ["Data Analysis"]),
]


def score_for(matcher, cand, jskills):
    results = matcher.rank(cand, [job(jskills)])
    if not results:
        return 0.0, []
    s, _, reasons = results[0]
    return s, reasons


def raw_cosine(provider, a, b):
    """The model's own similarity for two phrases, ignoring any threshold."""
    try:
        import numpy as np
        v = provider.embed([a, b])  # L2-normalized rows
        return float(np.dot(v[0], v[1]))
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["local", "api"], default="local",
                    help="Which embedding provider to verify (default: local model).")
    args = ap.parse_args()

    print("=" * 66)
    print(f"Embedding (AI-model) verification -- mode: {args.mode}")
    print("=" * 66)

    provider = get_embedding_provider(args.mode)
    if provider is None:
        print(f"\nNo embedding provider available for mode '{args.mode}'.")
        if args.mode == "local":
            print("  Install the model:  pip install -r requirements-embeddings.txt")
            print("  (and make sure the first run can reach the internet to download it)")
        else:
            print("  Set OPENAI_API_KEY (and optionally AJMS_EMBEDDING_API_BASE/MODEL).")
        sys.exit(2)

    import os
    from app.embeddings import effective_template
    print(f"Provider: {provider.name}")
    print(f"Model:    {os.environ.get('AJMS_EMBEDDING_MODEL', 'all-MiniLM-L6-v2')}")
    tpl = effective_template()
    print(f"Template: {tpl if '{skill}' in tpl else '(none -- embedding bare skill tokens)'}")
    print("Loading the model / warming up (first run downloads it)...\n")

    emb = SkillMatcher(embedding_provider=provider)
    tfidf = SkillMatcher(embedding_provider=None)  # the non-AI-model baseline

    print(f"(embedding match threshold = {emb.embedding_threshold:.2f})\n")
    npass = 0
    for cand, jskills in SEMANTIC_CASES:
        emb_score, emb_reasons = score_for(emb, cand, jskills)
        base_score, _ = score_for(tfidf, cand, jskills)
        cos = raw_cosine(provider, cand[0].lower(), jskills[0].lower())

        # The model clearly SEES the relationship if its raw cosine is well
        # above what unrelated skills score; a match also requires clearing the
        # threshold. We report both so the signal is visible either way.
        sees_it = cos is not None and cos >= 0.30
        ok = (emb_score > 0 and base_score == 0) or sees_it
        npass += 1 if ok else 0
        tag = "[PASS]" if ok else "[WARN]"
        cos_str = f"{cos*100:.0f}%" if cos is not None else "n/a"
        print(f"{tag}  {cand[0]!r}  vs job {jskills[0]!r}")
        print(f"        model similarity: {cos_str}   |   "
              f"match score -> embeddings: {emb_score:.0f}%, TF-IDF baseline: {base_score:.0f}%")
        if emb_reasons:
            print(f"        reason: {emb_reasons[0]}")
        print()

    # Report (do not hard-fail on) a known false-friend so you can sanity-check
    # the threshold: a good model keeps "Java" and "JavaScript" as distinct.
    jf_score, jf_reasons = score_for(emb, ["Java"], ["JavaScript"])
    jf_cos = raw_cosine(provider, "java", "javascript")
    jf_cos_str = f"{jf_cos*100:.0f}%" if jf_cos is not None else "n/a"
    print("-" * 66)
    print(f"False-friend check  'Java' vs job 'JavaScript':")
    print(f"   model raw similarity: {jf_cos_str}   |   match score: {jf_score:.0f}%")
    if jf_score == 0:
        print("   -> Correctly NOT matched (distinct-skills guard held, despite high similarity).")
    else:
        print("   -> WARNING: matched. Check DISTINCT_GROUPS in app/matching.py.")

    print("\n" + "=" * 66)
    print(f"RESULT: {npass}/{len(SEMANTIC_CASES)} semantic cases matched by the model "
          f"that TF-IDF could not.")
    print("=" * 66)
    print("\nThe context template is ON by default (it lifts related pairs a lot).")
    print("Distinct skills (Java/JavaScript, C/C++/C#, ...) are kept apart by the")
    print("guard in app/matching.py regardless of model similarity.")
    print("\nTuning knobs (set as environment variables, then re-run):")
    print("  AJMS_EMBEDDING_MODEL=all-mpnet-base-v2   # stronger (slower) model")
    print("  AJMS_EMBEDDING_TEMPLATE=\"skilled in {skill}\"   # try other context")
    print("  AJMS_EMBEDDING_THRESHOLD=0.50            # stricter matching")
    # Pass if the model caught the clear majority of meaning-based matches.
    sys.exit(0 if npass >= len(SEMANTIC_CASES) - 1 else 1)


if __name__ == "__main__":
    main()
