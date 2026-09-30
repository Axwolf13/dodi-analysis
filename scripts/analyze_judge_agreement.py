"""
Agreement analysis between DODI, the LLM judge, and ToS;DR expert grades.

Reads the cached judge outputs written by llm_judge.py plus the existing
DODI results (temporal_results.csv, validation_results.csv) and reports:

  1. Judge vs DODI over all 52 documents (does the judge agree with the index?)
  2. Judge vs ToS;DR over the 12 validation documents (n=12, same caveat as DODI)
  3. DODI vs ToS;DR (the original validation, recomputed for reference)
  4. Judge self-consistency across 3 runs on a 10-document subset
  5. Judge vs judge: Gemini 2.5 Flash against Claude Haiku on validation docs
  6. Largest rank disagreements between judge and DODI, with rationales

Writes output/judge_results.csv and output/judge_agreement.md. No API calls.
"""
import json
from pathlib import Path

import pandas as pd
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / "output" / "llm_judge"
JUDGE_MODEL = "claude-haiku-cli"
SECOND_JUDGE_MODEL = "gemini-3.5-flash"

GRADE_MAP = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}


def load_judge_results():
    rows = []
    for f in CACHE_DIR.rglob("*.json"):
        r = json.loads(f.read_text())
        meta = r["_meta"]
        rows.append({
            "doc_id": meta["doc_id"],
            "model": meta["model"],
            "run": meta["run"],
            "judge_score": r["overall_deception"],
            "ownership_opacity": r["ownership_opacity"],
            "readability_burden": r["readability_burden"],
            "aggressive_clauses": r["aggressive_clauses"],
            "judge_grade": r["tosdr_style_grade"],
            "rationale": r["rationale"],
        })
    return pd.DataFrame(rows)


def load_dodi_scores():
    """DODI score per doc_id, matching the judge's doc_id scheme."""
    temporal = pd.read_csv(REPO_ROOT / "output" / "temporal_results.csv")
    temporal["doc_id"] = ("temporal/" + temporal["Platform"].str.lower()
                          + "_" + temporal["Year"].astype(str))
    validation = pd.read_csv(REPO_ROOT / "validation_results.csv")
    validation["doc_id"] = ("validation/" + validation["Service"].str.lower()
                            .str.replace(" ", "_"))
    dodi = pd.concat([
        temporal[["doc_id", "DODI_Score"]],
        validation[["doc_id", "DODI_Score"]],
    ])
    # Unreviewed ToS;DR grades are provisional; compare against reviewed ones only
    tosdr = validation[validation["Reviewed"]].set_index("doc_id")["ToSDR_Grade"]
    return dodi.set_index("doc_id")["DODI_Score"], tosdr


def spearman_line(label, a, b):
    rho, p = stats.spearmanr(a, b)
    line = f"{label}: Spearman rho = {rho:.3f} (p = {p:.4f}, n = {len(a)})"
    print(line)
    return line


def main():
    judge = load_judge_results()
    if judge.empty:
        raise SystemExit("No judge outputs found. Run scripts/llm_judge.py first.")
    dodi, tosdr = load_dodi_scores()

    judge.to_csv(REPO_ROOT / "output" / "judge_results.csv", index=False)
    report = ["# LLM-judge agreement analysis", ""]

    # Primary judge, run 1: the full-corpus pass
    primary = (judge[(judge["model"] == JUDGE_MODEL) & (judge["run"] == 1)]
               .set_index("doc_id"))
    merged = primary.join(dodi, how="inner")
    print(f"Matched {len(merged)} of {len(primary)} judged docs to DODI scores\n")

    report.append("## Correlations")
    report.append(spearman_line("Judge vs DODI (all docs)",
                                merged["judge_score"], merged["DODI_Score"]))

    val = merged.join(tosdr, how="inner").dropna(subset=["ToSDR_Grade"])
    val = val[val["ToSDR_Grade"].isin(GRADE_MAP)]
    val["tosdr_num"] = val["ToSDR_Grade"].map(GRADE_MAP)
    val["judge_grade_num"] = val["judge_grade"].map(GRADE_MAP)
    report.append(spearman_line("Judge score vs ToS;DR grade",
                                val["judge_score"], val["tosdr_num"]))
    report.append(spearman_line("Judge letter grade vs ToS;DR grade",
                                val["judge_grade_num"], val["tosdr_num"]))
    report.append(spearman_line("DODI vs ToS;DR grade (reference)",
                                val["DODI_Score"], val["tosdr_num"]))

    # Self-consistency: per-doc std of judge_score across the 3 runs
    repeats = judge[judge["model"] == JUDGE_MODEL].groupby("doc_id").filter(
        lambda g: g["run"].nunique() >= 3)
    if not repeats.empty:
        per_doc = repeats.groupby("doc_id")["judge_score"].agg(["mean", "std", "min", "max"])
        line = (f"Self-consistency ({per_doc.shape[0]} docs x 3 runs): "
                f"mean per-doc std = {per_doc['std'].mean():.1f} points, "
                f"max spread = {(per_doc['max'] - per_doc['min']).max():.0f} points")
        print("\n" + line)
        report += ["", "## Self-consistency", line, "", per_doc.round(1).to_markdown()]

    # Judge vs judge on the validation docs
    second = (judge[(judge["model"] == SECOND_JUDGE_MODEL) & (judge["run"] == 1)]
              .set_index("doc_id"))
    both = primary.join(second, how="inner", lsuffix="_claude", rsuffix="_gemini")
    if not both.empty:
        report += ["", "## Judge vs judge"]
        report.append(spearman_line(
            f"{SECOND_JUDGE_MODEL} vs {JUDGE_MODEL} ({len(both)} validation docs)",
            both["judge_score_claude"], both["judge_score_gemini"]))
        mad = (both["judge_score_claude"] - both["judge_score_gemini"]).abs().mean()
        line = f"Mean absolute score difference between judges: {mad:.1f} points"
        print(line)
        report.append(line)

    # Disagreements: rank each doc under both scorers, surface the largest gaps
    merged["dodi_rank"] = merged["DODI_Score"].rank()
    merged["judge_rank"] = merged["judge_score"].rank()
    merged["rank_gap"] = (merged["dodi_rank"] - merged["judge_rank"]).abs()
    top = merged.nlargest(5, "rank_gap")
    report += ["", "## Largest rank disagreements (judge vs DODI)", ""]
    print("\nLargest rank disagreements:")
    for doc_id, row in top.iterrows():
        entry = (f"- **{doc_id}**: DODI {row['DODI_Score']:.1f} "
                 f"(rank {row['dodi_rank']:.0f}) vs judge {row['judge_score']} "
                 f"(rank {row['judge_rank']:.0f}). Judge rationale: {row['rationale']}")
        print(f"  {doc_id}: DODI {row['DODI_Score']:.1f} vs judge {row['judge_score']}")
        report.append(entry)

    out = REPO_ROOT / "output" / "judge_agreement.md"
    out.write_text("\n".join(report), encoding="utf-8")
    print(f"\n✅ Wrote output/judge_results.csv and output/judge_agreement.md")


if __name__ == "__main__":
    main()
