"""
DODI as an MCP server: lets any MCP client (Claude Code, Claude Desktop)
score Terms of Service documents with the deterministic DODI index.

Register with Claude Code from the repo root:
    claude mcp add dodi -- python mcp_server.py

The scorer itself is unchanged from scripts/dodi_analyzer_clean.py; this file
only exposes it over the protocol, plus read access to the study's results.
"""
import json
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from dodi_analyzer_clean import DODIAnalyzer

mcp = FastMCP("dodi")
analyzer = DODIAnalyzer()


def interpret(score):
    if score < 30:
        return "low deception: ownership language is comparatively honest"
    if score < 60:
        return "moderate deception: licence framing dominates but is not extreme"
    return "high deception: the document works hard to obscure that you own nothing"


@mcp.tool()
def score_tos(text: str) -> str:
    """Score a Terms of Service document with DODI (Digital Ownership
    Deception Index). Returns a 0-100 deception score (higher = more
    deceptive about ownership), component metrics and an interpretation.
    Pass the full plain text of the ToS document."""
    if len(text) < 500:
        return json.dumps({"error": "Text too short to score meaningfully; pass the full ToS document."})
    result = analyzer.analyze(text)
    result["interpretation"] = interpret(result["dodi_score"])
    result["method"] = ("Deterministic: 50% licence-vs-ownership term ratio, "
                        "25% Flesch-Kincaid readability penalty, 25% red-flag clauses. "
                        "Same document always scores the same.")
    return json.dumps(result, indent=2)


@mcp.tool()
def get_platform_rankings() -> str:
    """Get DODI scores for the 10 platforms in the 2015-2024 temporal study
    (Adobe, Amazon, Apple, Facebook, GOG, Microsoft, Netflix, Sony, Steam,
    Twitter), one score per ToS snapshot year. Higher = more deceptive."""
    csv_path = REPO_ROOT / "output" / "temporal_results.csv"
    if not csv_path.exists():
        return json.dumps({"error": "temporal_results.csv not found; run scripts/analyze_temporal_data.py"})
    return csv_path.read_text(encoding="utf-8")


@mcp.tool()
def explain_score(text: str) -> str:
    """Break down WHY a Terms of Service document gets its DODI score:
    which ownership and licence words were counted, which red-flag clauses
    matched and how often, and the readability grade level. Use after
    score_tos when the user wants the evidence behind the number."""
    if len(text) < 500:
        return json.dumps({"error": "Text too short to analyze."})
    lower = text.lower()
    ownership = {w: lower.count(w) for w in analyzer.ownership_words if lower.count(w)}
    licence = {w: lower.count(w) for w in analyzer.license_words if lower.count(w)}
    flags = {p: lower.count(p) for p in analyzer.red_flags if lower.count(p)}
    result = analyzer.analyze(text)
    return json.dumps({
        "dodi_score": result["dodi_score"],
        "ownership_terms_found": ownership,
        "licence_terms_found": licence,
        "red_flags_found": dict(sorted(flags.items(), key=lambda kv: -kv[1])),
        "flesch_kincaid_grade": result["grade_level"],
        "licence_to_ownership_ratio": result["ratio"],
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
