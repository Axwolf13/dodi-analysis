"""
DODI as an MCP server: lets any MCP client (Claude Code, Claude Desktop)
score Terms of Service documents with the deterministic DODI index.

Two transports:
  stdio (default), for local clients. Register with Claude Code:
      claude mcp add dodi -- python mcp_server.py
  Streamable HTTP, for remote clients such as Copilot Studio:
      python mcp_server.py --http          # serves http://0.0.0.0:8000/mcp
  HTTP mode also switches on when a PORT variable is set, which is how
  hosts like Render pass the port, so a deploy needs no extra flag.

The scorer itself is unchanged from scripts/dodi_analyzer_clean.py; this file
only exposes it over the protocol, plus read access to the study's results.
"""
import json
import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from dodi_analyzer_clean import DODIAnalyzer

HTTP_MODE = "--http" in sys.argv or "PORT" in os.environ

# Bound to 0.0.0.0 in HTTP mode so remote clients can connect. The SDK only
# enables its localhost-only DNS-rebinding check when bound to 127.0.0.1, which
# would reject requests arriving through a tunnel or a cloud host.
# Stateless: every request stands alone, so any server instance can answer it.
mcp = FastMCP(
    "dodi",
    host="0.0.0.0" if HTTP_MODE else "127.0.0.1",
    port=int(os.environ.get("PORT", 8000)),
    stateless_http=True,
)
analyzer = DODIAnalyzer()



# Plain HTTP endpoint outside the protocol, for uptime pings. Render's free tier
# sleeps after 15 idle minutes and a cold start can outlast an agent's tool-call
# timeout, so a pinger keeps it warm. Only served in HTTP mode.
@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "server": "dodi"})

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
    result["method"] = ("DODI v1.1, deterministic: 50% licence-vs-ownership term ratio, "
                        "25% Flesch-Kincaid readability penalty, 25% red-flag clauses, "
                        "counting whole words. Same document always scores the same.")
    return json.dumps(result, indent=2)


@mcp.tool()
def get_platform_rankings() -> str:
    """Get DODI scores for the 10 platforms in the 2015-2024 temporal study
    (Adobe, Amazon, Facebook, GOG, Microsoft, Netflix, Spotify, Steam,
    Twitter, Ubisoft), one score per ToS snapshot year. Higher = more deceptive."""
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
    ownership, licence, flags = analyzer.term_counts(text)
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
    mcp.run(transport="streamable-http" if HTTP_MODE else "stdio")
