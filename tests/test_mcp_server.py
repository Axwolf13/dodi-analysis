"""
End-to-end test of the DODI MCP server over both transports: spawns
mcp_server.py over stdio, then again as a Streamable HTTP server, and runs the
same checks through each, listing the tools and calling every one with real
corpus documents.

Run from the repo root: python tests/test_mcp_server.py
"""
import asyncio
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

REPO_ROOT = Path(__file__).resolve().parent.parent
HTTP_PORT = 8765


async def run_checks(session):
    await session.initialize()

    tools = await session.list_tools()
    names = [t.name for t in tools.tools]
    print("  tools:", names)
    assert set(names) == {"score_tos", "get_platform_rankings", "explain_score"}

    gog = (REPO_ROOT / "data" / "temporal" / "gog_2015.txt").read_text(encoding="utf-8")
    netflix = (REPO_ROOT / "data" / "temporal" / "netflix_2024.txt").read_text(encoding="utf-8")

    r = await session.call_tool("score_tos", {"text": gog})
    gog_score = json.loads(r.content[0].text)["dodi_score"]
    r = await session.call_tool("score_tos", {"text": netflix})
    netflix_score = json.loads(r.content[0].text)["dodi_score"]
    print(f"  score_tos: GOG 2015 = {gog_score}, Netflix 2024 = {netflix_score}")
    # Face-validity invariant from the study: GOG scores far below Netflix
    assert gog_score < netflix_score, "GOG should score less deceptive than Netflix"

    r = await session.call_tool("explain_score", {"text": netflix})
    detail = json.loads(r.content[0].text)
    print(f"  explain_score: Netflix ratio = {detail['licence_to_ownership_ratio']}, "
          f"top red flag = {next(iter(detail['red_flags_found']), 'none')}")
    assert detail["dodi_score"] == netflix_score, "explain and score must agree"
    r = await session.call_tool("score_tos", {"text": netflix})
    scored = json.loads(r.content[0].text)
    assert sum(detail["ownership_terms_found"].values()) == scored["ownership_count"], \
        "explained ownership hits must add up to the scored count"
    assert sum(detail["licence_terms_found"].values()) == scored["license_count"], \
        "explained licence hits must add up to the scored count"
    assert sum(detail["red_flags_found"].values()) == scored["red_flags"], \
        "explained red flags must add up to the scored count"

    r = await session.call_tool("get_platform_rankings", {})
    lines = r.content[0].text.strip().splitlines()
    print(f"  get_platform_rankings: {len(lines) - 1} rows")
    assert len(lines) == 41, "expected 40 snapshots plus header"

    r = await session.call_tool("score_tos", {"text": "too short"})
    assert "error" in json.loads(r.content[0].text)
    print("  short-input guard: ok")


async def test_stdio():
    print("stdio:")
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(REPO_ROOT / "mcp_server.py")],
        cwd=str(REPO_ROOT),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await run_checks(session)


def wait_for_port(port, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.3)
    raise TimeoutError(f"server never listened on port {port}")


async def test_http():
    print("streamable HTTP:")
    server = subprocess.Popen(
        [sys.executable, str(REPO_ROOT / "mcp_server.py"), "--http"],
        cwd=str(REPO_ROOT),
        env={**os.environ, "PORT": str(HTTP_PORT)},
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        wait_for_port(HTTP_PORT)
        url = f"http://127.0.0.1:{HTTP_PORT}/mcp"
        async with streamablehttp_client(url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await run_checks(session)
    finally:
        server.terminate()
        server.wait(timeout=10)


async def main():
    await test_stdio()
    await test_http()
    print("\nall MCP server tests passed (stdio and streamable HTTP)")


if __name__ == "__main__":
    asyncio.run(main())
