"""
End-to-end test of the DODI MCP server: spawns mcp_server.py over stdio,
lists its tools and calls each one with real corpus documents.

Run from the repo root: python tests/test_mcp_server.py
"""
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO_ROOT = Path(__file__).resolve().parent.parent


async def main():
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(REPO_ROOT / "mcp_server.py")],
        cwd=str(REPO_ROOT),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            print("tools:", names)
            assert set(names) == {"score_tos", "get_platform_rankings", "explain_score"}

            gog = (REPO_ROOT / "data" / "temporal" / "gog_2015.txt").read_text(encoding="utf-8")
            netflix = (REPO_ROOT / "data" / "temporal" / "netflix_2024.txt").read_text(encoding="utf-8")

            r = await session.call_tool("score_tos", {"text": gog})
            gog_score = json.loads(r.content[0].text)["dodi_score"]
            r = await session.call_tool("score_tos", {"text": netflix})
            netflix_score = json.loads(r.content[0].text)["dodi_score"]
            print(f"score_tos: GOG 2015 = {gog_score}, Netflix 2024 = {netflix_score}")
            # Face-validity invariant from the study: GOG scores far below Netflix
            assert gog_score < netflix_score, "GOG should score less deceptive than Netflix"

            r = await session.call_tool("explain_score", {"text": netflix})
            detail = json.loads(r.content[0].text)
            print(f"explain_score: Netflix ratio = {detail['licence_to_ownership_ratio']}, "
                  f"top red flag = {next(iter(detail['red_flags_found']), 'none')}")
            assert detail["dodi_score"] == netflix_score, "explain and score must agree"

            r = await session.call_tool("get_platform_rankings", {})
            lines = r.content[0].text.strip().splitlines()
            print(f"get_platform_rankings: {len(lines) - 1} rows")
            assert len(lines) == 41, "expected 40 snapshots plus header"

            r = await session.call_tool("score_tos", {"text": "too short"})
            assert "error" in json.loads(r.content[0].text)
            print("short-input guard: ok")

    print("\nall MCP server tests passed")


if __name__ == "__main__":
    asyncio.run(main())
