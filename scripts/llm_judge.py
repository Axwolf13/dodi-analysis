"""
LLM-as-judge validation layer for DODI.

Sends every ToS document in the corpus to an LLM with a rubric mirroring
DODI's three components and collects structured scores. Responses are cached
to disk keyed by (judge, doc, run), so re-runs are free and the agreement
analysis never needs a live model.

Two judge backends, both free of API billing:
  claude-cli  Claude Haiku through the Claude Code CLI in headless mode
              (runs on the local Claude subscription; no API key)
  gemini      Gemini 3.5 Flash on the AI Studio free tier
              (needs GEMINI_API_KEY in the environment or repo-root .env)

Runs performed:
  1. claude-cli on all 52 documents (40 temporal + 12 validation)
  2. claude-cli twice more on a 10-document subset (self-consistency)
  3. gemini on the 12 validation documents (cross-vendor judge), if key present
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / "output" / "llm_judge"

CLAUDE_JUDGE = "claude-haiku-cli"
GEMINI_JUDGE = "gemini-3.5-flash"

# Fixed subset for the repeat runs: spread across score range and years so
# consistency isn't measured only on easy extremes.
CONSISTENCY_SUBSET = [
    "temporal/gog_2015", "temporal/gog_2024", "temporal/adobe_2024",
    "temporal/netflix_2024", "temporal/steam_2015", "temporal/twitter_2021",
    "validation/wikipedia", "validation/google",
    "validation/reddit", "validation/netflix",
]

RUBRIC = """You are an expert reviewer of consumer Terms of Service documents. You rate how hard a document works to keep an ordinary consumer from noticing that "buying" digital content only grants a revocable licence.

Score the document on these dimensions, each 0-100 where higher means worse for the consumer:

- ownership_opacity: how strongly the language frames transactions as licences rather than purchases, and how well it hides that the user owns nothing. A DRM-free store that says plainly "you own this" scores near 0. A document that says "buy" in marketing but grants only a revocable licence scores high.
- readability_burden: how much the document's length, sentence structure and legal vocabulary impede an ordinary reader.
- aggressive_clauses: presence and severity of unilateral termination, rights waivers (arbitration, class action), and broad data exploitation clauses.
- overall_deception: your overall judgment of ownership deception, 0-100. This is your holistic call, not an average of the subscores.

Also assign tosdr_style_grade: a letter A-E in the style of ToS;DR, where A is most consumer-friendly overall and E is worst.

Base every score only on the document text provided. Judge as a consumer advocate would, not as the platform's lawyer would.

Respond with ONLY a JSON object, no markdown fences, no commentary, exactly this shape:
{"ownership_opacity": <int>, "readability_burden": <int>, "aggressive_clauses": <int>, "overall_deception": <int>, "tosdr_style_grade": "<A-E>", "rationale": "<2-3 sentences>", "evidence_quotes": ["<short quote>", "<short quote>"]}"""

REQUIRED_KEYS = {
    "ownership_opacity", "readability_burden", "aggressive_clauses",
    "overall_deception", "tosdr_style_grade", "rationale", "evidence_quotes",
}


def load_env_key(name):
    if os.environ.get(name):
        return os.environ[name]
    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith(f"{name}="):
                return line.split("=", 1)[1].strip().strip('"')
    return None


def corpus_docs():
    """Yield (doc_id, path) for all 52 documents."""
    for f in sorted((REPO_ROOT / "data" / "temporal").glob("*.txt")):
        yield f"temporal/{f.stem}", f
    for f in sorted((REPO_ROOT / "data" / "validation").glob("*.txt")):
        yield f"validation/{f.stem.replace('_tos', '')}", f


def parse_judge_json(raw):
    # Models occasionally wrap JSON in fences or prose despite instructions;
    # extract the outermost object before giving up.
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"no JSON object in output: {raw[:200]}")
    result = json.loads(match.group(0))
    missing = REQUIRED_KEYS - result.keys()
    if missing:
        raise ValueError(f"missing keys: {missing}")
    return result


def judge_claude_cli(doc_text, model="haiku"):
    exe = shutil.which("claude")
    if not exe:
        sys.exit("claude CLI not found on PATH.")
    prompt = f"{RUBRIC}\n\nRate this Terms of Service document.\n\n<document>\n{doc_text}\n</document>"
    proc = subprocess.run(
        [exe, "-p", "--model", model],
        input=prompt, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=600,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI failed: {proc.stderr[:300]}")
    return parse_judge_json(proc.stdout)


def judge_gemini(doc_text, api_key):
    from google import genai
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=GEMINI_JUDGE,
        contents=f"{RUBRIC}\n\nRate this Terms of Service document.\n\n<document>\n{doc_text}\n</document>",
        config={"response_mime_type": "application/json"},
    )
    return parse_judge_json(response.text)


def judge_document(judge, doc_id, path, run, gemini_key=None):
    cache_path = CACHE_DIR / judge / f"{doc_id.replace('/', '__')}__run{run}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text()), True

    text = path.read_text(encoding="utf-8", errors="replace")
    if judge == CLAUDE_JUDGE:
        result = judge_claude_cli(text)
    else:
        result = judge_gemini(text, gemini_key)
    result["_meta"] = {"model": judge, "doc_id": doc_id, "run": run}

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(result, indent=2))
    return result, False


def run_batch(judge, docs, run, label, gemini_key=None, pace_seconds=0):
    print(f"\n{'=' * 60}\n{label}\n{'=' * 60}")
    for doc_id, path in docs:
        for attempt in range(3):
            try:
                result, cached = judge_document(judge, doc_id, path, run, gemini_key)
                break
            except Exception as e:
                if attempt == 2:
                    print(f"  ❌ {doc_id}: {type(e).__name__}: {str(e)[:150]}")
                    result = None
                    break
                wait = 20 * (attempt + 1)
                print(f"  retry {doc_id} in {wait}s ({type(e).__name__})")
                time.sleep(wait)
        if result is None:
            continue
        flag = "cached" if cached else "fresh"
        print(f"  {doc_id}: deception {result['overall_deception']:3d}, "
              f"grade {result['tosdr_style_grade']} ({flag})")
        # Free-tier rate limits: pace fresh Gemini calls, never cached ones
        if not cached and pace_seconds:
            time.sleep(pace_seconds)


def main():
    all_docs = list(corpus_docs())
    print(f"Corpus: {len(all_docs)} documents")

    subset = [(d, p) for d, p in all_docs if d in CONSISTENCY_SUBSET]
    validation = [(d, p) for d, p in all_docs if d.startswith("validation/")]

    run_batch(CLAUDE_JUDGE, all_docs, 1,
              f"Run 1: {CLAUDE_JUDGE} on all {len(all_docs)} documents")
    run_batch(CLAUDE_JUDGE, subset, 2,
              f"Run 2: {CLAUDE_JUDGE} consistency repeat on {len(subset)} documents")
    run_batch(CLAUDE_JUDGE, subset, 3,
              f"Run 3: {CLAUDE_JUDGE} consistency repeat on {len(subset)} documents")

    gemini_key = load_env_key("GEMINI_API_KEY")
    if gemini_key:
        run_batch(GEMINI_JUDGE, validation, 1,
                  f"Cross-vendor judge: {GEMINI_JUDGE} on {len(validation)} validation documents",
                  gemini_key=gemini_key, pace_seconds=7)
    else:
        print("\nNo GEMINI_API_KEY found, skipping the cross-vendor judge. "
              "Free key: https://aistudio.google.com/apikey")

    print("\n✅ Judge runs complete. Next: python scripts/analyze_judge_agreement.py")


if __name__ == "__main__":
    main()
