"""
Stronger-judge robustness check: run Claude Sonnet (a larger model than the
Haiku primary judge) over the 12 validation documents, to test whether the
judge-vs-DODI disagreement is a small-model artifact or holds up.

Resumable and limit-safe by design:
  - every document is cached to output/llm_judge/claude-sonnet-cli/ on success
  - a re-run skips whatever is already cached and finishes the rest
  - if the Claude CLI fails (e.g. the daily session limit is reached), the run
    stops immediately instead of burning budget on retries, and prints exactly
    where it stopped so you can re-run this same command in the morning

    python scripts/judge_sonnet_validation.py

When all 12 are done it prints Sonnet-vs-DODI and Sonnet-vs-Haiku correlations.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import llm_judge

JUDGE = "claude-sonnet-cli"
VALIDATION = [d for d, _ in llm_judge.corpus_docs() if d.startswith("validation/")]


def cache_path(doc_id):
    return llm_judge.CACHE_DIR / JUDGE / f"{doc_id.replace('/', '__')}__run1.json"


def report_if_complete():
    """Once all 12 Sonnet docs exist, print the correlations that answer the
    question. Imports the analysis helpers so the DODI/Haiku scores line up."""
    if not all(cache_path(d).exists() for d in VALIDATION):
        return
    import pandas as pd
    from scipy import stats
    import analyze_judge_agreement as aa

    dodi, _ = aa.load_dodi_scores()
    sonnet, haiku = {}, {}
    for d in VALIDATION:
        sonnet[d] = json.loads(cache_path(d).read_text())["overall_deception"]
        hp = llm_judge.CACHE_DIR / "claude-haiku-cli" / f"{d.replace('/', '__')}__run1.json"
        if hp.exists():
            haiku[d] = json.loads(hp.read_text())["overall_deception"]

    ids = list(sonnet)
    s = [sonnet[d] for d in ids]
    dv = [dodi[d] for d in ids]
    print("\n" + "=" * 60)
    rho, p = stats.spearmanr(s, dv)
    print(f"Sonnet vs DODI (n={len(ids)}): rho = {rho:.3f} (p = {p:.4f})")
    common = [d for d in ids if d in haiku]
    if common:
        rho2, p2 = stats.spearmanr([sonnet[d] for d in common], [haiku[d] for d in common])
        print(f"Sonnet vs Haiku (n={len(common)}): rho = {rho2:.3f} (p = {p2:.4f})")
        print(f"Sonnet score range: {min(s)}-{max(s)}  |  "
              f"Haiku range: {min(haiku[d] for d in common)}-{max(haiku[d] for d in common)}")
    print("Reference from the full run: Haiku vs DODI rho = 0.11, DODI vs ToS;DR rho = 0.54")
    print("=" * 60)


def main():
    docs = dict(llm_judge.corpus_docs())
    done = sum(cache_path(d).exists() for d in VALIDATION)
    print(f"Sonnet validation judge: {done}/{len(VALIDATION)} already cached\n")

    for doc_id in VALIDATION:
        cp = cache_path(doc_id)
        if cp.exists():
            print(f"  {doc_id}: cached")
            continue

        text = docs[doc_id].read_text(encoding="utf-8", errors="replace")
        try:
            result = llm_judge.judge_claude_cli(text, model="sonnet")
        except Exception as e:
            # No retries: a CLI failure here is almost always the session limit.
            # Stop clean so the remaining budget survives to the morning.
            print(f"\n⏸  Stopped at {doc_id}: {type(e).__name__} {str(e)[:120]}")
            print(f"   {done}/{len(VALIDATION)} done and cached. "
                  f"Re-run this script after the limit resets to finish.")
            return

        result["_meta"] = {"model": JUDGE, "doc_id": doc_id, "run": 1}
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text(json.dumps(result, indent=2))
        done += 1
        print(f"  {doc_id}: deception {result['overall_deception']:3d}, "
              f"grade {result['tosdr_style_grade']} (fresh, {done}/{len(VALIDATION)})")

    print(f"\n✅ All {len(VALIDATION)} Sonnet validation docs done.")
    report_if_complete()


if __name__ == "__main__":
    main()
