"""
How much do DODI's results depend on how terms are counted?

v1.0 counted terms with str.count, so "own" also fired inside "download" and
"known", and "rent" inside "different" and "parent". v1.1 counts whole words
and their genuine forms (British "licence" included). This script scores the
whole corpus both ways and re-checks every result the study reports:

  1. term-level hit counts
  2. per-document score changes
  3. the face-validity check: is GOG still the least deceptive platform?
  4. the temporal trend, 2015 to 2024
  5. agreement with reviewed ToS;DR expert grades
  6. agreement with the two LLM judges
  7. how many documents saturate the capped components

Both columns use the documented 25/50/25 weights; only the counting differs.
Reads only files already in the repository; no network, no models.
Writes output/matching_audit.md.

    python scripts/matching_audit.py
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

from scipy import stats

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from dodi_analyzer_clean import DODIAnalyzer

GRADE_MAP = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}
JUDGES = {"Haiku": "claude-haiku-cli", "Sonnet": "claude-sonnet-cli"}
MODES = {"substring": "v1.0 substring", "word": "v1.1 word"}


def corpus():
    """(doc_id, platform, year, text) for every document in the study."""
    docs = []
    for f in sorted((REPO_ROOT / "data" / "temporal").glob("*.txt")):
        platform, year = f.stem.rsplit("_", 1)
        docs.append((f"temporal/{f.stem}", platform, int(year), f.read_text(encoding="utf-8", errors="replace")))
    for f in sorted((REPO_ROOT / "data" / "validation").glob("*.txt")):
        name = f.stem.replace("_tos", "")
        docs.append((f"validation/{name}", name, None, f.read_text(encoding="utf-8", errors="replace")))
    return docs


def term_hits(docs, analyzer):
    hits = defaultdict(int)
    for _, _, _, text in docs:
        for group in analyzer.term_counts(text):
            for term, n in group.items():
                hits[term] += n
    return hits


def reviewed_grades():
    """Reviewed ToS;DR grades only, as in run_validation_analysis.py."""
    grades = {}
    with open(REPO_ROOT / "tosdr_grades.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["Grade"] in GRADE_MAP and r["Reviewed"] == "True":
                grades["validation/" + r["Service"].lower()] = GRADE_MAP[r["Grade"]]
    return grades


def judge_scores(judge_dir):
    scores = {}
    for f in (REPO_ROOT / "output" / "llm_judge" / judge_dir).glob("*__run1.json"):
        doc_id = f.stem.replace("__run1", "").replace("__", "/")
        scores[doc_id] = json.loads(f.read_text())["overall_deception"]
    return scores


def spearman(a, b):
    rho, p = stats.spearmanr(a, b)
    return f"{rho:+.3f} (p = {p:.3f})"


def main():
    docs = corpus()
    n = len(docs)
    scorers = {mode: DODIAnalyzer(matching=mode) for mode in MODES}
    res = {mode: {d: a.analyze(text) for d, _, _, text in docs} for mode, a in scorers.items()}

    out = ["# Matching audit: substring (v1.0) vs whole-word counting (v1.1)", "",
           "Both columns use the documented 25/50/25 weights; only the counting differs.", ""]

    # 1. terms
    h_old, h_new = term_hits(docs, scorers["substring"]), term_hits(docs, scorers["word"])
    a = scorers["word"]
    out += [f"## 1. Term hits across all {n} documents", "",
            "| Term | v1.0 substring | v1.1 word | Change |", "|---|---:|---:|---:|"]
    for t in a.ownership_words + a.license_words:
        out.append(f"| {t} | {h_old[t]} | {h_new[t]} | {h_new[t] - h_old[t]:+d} |")
    out += ["", f"Red-flag phrases combined: {sum(h_old[t] for t in a.red_flags)} substring hits, "
                f"{sum(h_new[t] for t in a.red_flags)} whole-word hits.", ""]

    # 2. per-document scores
    deltas = sorted(((res["word"][d]["dodi_score"] - res["substring"][d]["dodi_score"], d) for d in res["word"]),
                    reverse=True)
    mean_abs = sum(abs(x) for x, _ in deltas) / len(deltas)
    out += ["## 2. Score changes", "",
            f"Mean absolute change: {mean_abs:.1f} points. Largest rises and falls:", "",
            "| Document | v1.0 | v1.1 | Change |", "|---|---:|---:|---:|"]
    for x, d in deltas[:5] + deltas[-5:]:
        out.append(f"| {d} | {res['substring'][d]['dodi_score']} | {res['word'][d]['dodi_score']} | {x:+.1f} |")
    out.append("")

    # 3 + 4. face validity and trend, temporal documents only
    temporal = [(d, p, y) for d, p, y, _ in docs if y is not None]
    years = sorted({y for _, _, y in temporal})
    out += ["## 3. Face validity: GOG's rank among the 10 platforms (1 = least deceptive)", "",
            "| Year | v1.0 rank | v1.1 rank | Least deceptive under v1.1 |", "|---|---:|---:|---|"]
    for y in years:
        order = {m: [p for _, p in sorted((res[m][d]["dodi_score"], p) for d, p, yy in temporal if yy == y)]
                 for m in MODES}
        out.append(f"| {y} | {order['substring'].index('gog') + 1} | {order['word'].index('gog') + 1} "
                   f"| {order['word'][0]} |")
    out += ["", "## 4. Temporal trend (mean score across the 10 platforms)", "",
            "| Year | v1.0 | v1.1 |", "|---|---:|---:|"]
    for y in years:
        cells = []
        for m in MODES:
            vals = [res[m][d]["dodi_score"] for d, _, yy in temporal if yy == y]
            cells.append(f"{sum(vals) / len(vals):.1f}")
        out.append(f"| {y} | {cells[0]} | {cells[1]} |")
    rising = {}
    for m in MODES:
        by_platform = defaultdict(dict)
        for d, p, y in temporal:
            by_platform[p][y] = res[m][d]["dodi_score"]
        rising[m] = sum(v[years[-1]] > v[years[0]] for v in by_platform.values())
    out += ["", f"Platforms scoring higher in {years[-1]} than {years[0]}: "
                f"v1.0 {rising['substring']} of 10, v1.1 {rising['word']} of 10.", ""]

    # 5. ToS;DR validation
    grades = reviewed_grades()
    val = sorted(grades)
    g = [grades[d] for d in val]
    out += ["## 5. Agreement with reviewed ToS;DR expert grades", "",
            f"| Scorer | Spearman vs ToS;DR (n = {len(val)}) |", "|---|---|"]
    for m, label in MODES.items():
        out.append(f"| DODI {label} | {spearman([res[m][d]['dodi_score'] for d in val], g)} |")
    out.append("")

    # 6. judges
    out += ["## 6. Agreement with the LLM judges", "", "| Judge | n | v1.0 | v1.1 |", "|---|---:|---|---|"]
    for name, folder in JUDGES.items():
        js = judge_scores(folder)
        ids = sorted(d for d in js if d in res["word"])
        j = [js[d] for d in ids]
        out.append(f"| {name} | {len(ids)} | "
                   f"{spearman([res['substring'][d]['dodi_score'] for d in ids], j)} | "
                   f"{spearman([res['word'][d]['dodi_score'] for d in ids], j)} |")
    out.append("")

    # 7. saturation
    out += ["## 7. Saturated components", "", "| | v1.0 | v1.1 |", "|---|---:|---:|"]
    checks = (("Ratio component capped (ratio >= 10 or no ownership words)",
               lambda r: r["ownership_count"] == 0 or r["ratio"] >= 10),
              ("Red-flag component capped (>= 50 hits)", lambda r: r["red_flags"] >= 50))
    for label, test in checks:
        out.append(f"| {label} | {sum(test(r) for r in res['substring'].values())} of {n} "
                   f"| {sum(test(r) for r in res['word'].values())} of {n} |")
    out.append("")

    report = "\n".join(out)
    (REPO_ROOT / "output" / "matching_audit.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
