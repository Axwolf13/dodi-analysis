"""
DODI v2: the gap between what the store promises and what the contract grants.

v1.1 scores the contract alone, so an honest subscription whose terms are full of
licence language scores as highly deceptive. v2 weights the contract score by
what the storefront promises:

    v2 = v1.1 contract score x promise x (1 - 0.5 x licence disclosed at sale)

    promise 1.0  one-time purchase of a specific title ("Buy", "Add to cart" + price)
            0.5  subscription sold with "Buy" wording
            0.0  subscription or free service, or no store at all

The storefront coding, with quotes and Wayback snapshots, is in
data/storefront/coding.csv.

    python scripts/dodi_v2.py
"""
import json
from pathlib import Path

import pandas as pd
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parent.parent
CODING = REPO_ROOT / "data" / "storefront" / "coding.csv"
OUT = REPO_ROOT / "output"


def score_v2(contract, promise, disclosed):
    """Contract score weighted by the store promise, halved if the licence is stated at sale."""
    return contract * promise * (0.5 if disclosed else 1.0)


def main():
    coding = pd.read_csv(CODING)
    v11 = pd.read_csv(OUT / "temporal_results.csv")
    v11["platform"] = v11["Platform"].str.lower()
    rows = []
    for _, c in coding.iterrows():
        match = v11[(v11["platform"] == c["platform"]) & (v11["Year"] == c["year"])]
        if match.empty:
            continue
        contract = float(match["DODI_Score"].iloc[0])
        disclosed = str(c["licence_at_sale"]).lower() == "yes"
        v2 = score_v2(contract, float(c["promise"]), disclosed)
        rows.append({"platform": c["platform"], "year": int(c["year"]), "sale_type": c["sale_type"],
                     "promise": float(c["promise"]), "licence_at_sale": disclosed,
                     "dodi_v1_1": round(contract, 1), "dodi_v2": round(v2, 1)})
    res = pd.DataFrame(rows).sort_values(["year", "dodi_v2"], ascending=[True, False])
    res.to_csv(OUT / "dodi_v2_results.csv", index=False)

    report = {"results": res.to_dict(orient="records")}
    # Does weighting by the store promise bring the index closer to the LLM readers?
    judge_path = OUT / "judge_results.csv"
    if judge_path.exists():
        j = pd.read_csv(judge_path)
        j = j[(j["model"] == "claude-haiku-cli") & (j["run"] == 1)]
        j["platform"] = j["doc_id"].str.extract(r"temporal/(\w+)_(\d{4})")[0]
        j["year"] = pd.to_numeric(j["doc_id"].str.extract(r"_(\d{4})$")[0], errors="coerce")
        m = res.merge(j[["platform", "year", "judge_score"]], on=["platform", "year"])
        if len(m) >= 5:
            r1, p1 = stats.spearmanr(m["dodi_v1_1"], m["judge_score"])
            r2, p2 = stats.spearmanr(m["dodi_v2"], m["judge_score"])
            report["haiku_agreement"] = {"n": len(m), "v1_1_rho": round(r1, 3), "v1_1_p": round(p1, 3),
                                         "v2_rho": round(r2, 3), "v2_p": round(p2, 3)}
    (OUT / "dodi_v2.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(res.to_string(index=False))
    if "haiku_agreement" in report:
        print("\nAgreement with the Haiku judge on the same documents:", report["haiku_agreement"])


if __name__ == "__main__":
    main()
