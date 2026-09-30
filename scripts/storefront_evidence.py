"""
Pull purchase language out of the archived storefront pages for DODI v2.

For every page fetched by fetch_storefronts.py, strips markup, then counts and
quotes the phrases that decide how a store frames an acquisition: buy and
purchase wording, subscription wording, and any licence disclosure. The quotes
are what data/storefront/coding.csv cites as evidence.

    python scripts/storefront_evidence.py            # summary table
    python scripts/storefront_evidence.py steam      # every quote for one platform
"""
import html
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "storefront" / "raw"

PATTERNS = {
    "buy": r"\bbuy(?:\s+now)?\b",
    "purchase": r"\bpurchas(?:e|es|ed|ing)\b",
    "add to cart": r"\badd to (?:cart|basket)\b",
    "own": r"\b(?:own it|yours to keep|keep forever|you own)\b",
    "subscribe": r"\bsubscri(?:be|ption)\b",
    "free trial": r"\b(?:free trial|try (?:it )?free|start free)\b",
    "per month": r"(?:/mo\b|per month|/month|monthly)",
    "licence": r"\blicen[cs](?:e|es|ed|ing)\b",
    "drm-free": r"\bdrm[- ]free\b",
}


def visible_text(path):
    raw = path.read_text(encoding="utf-8", errors="replace")
    raw = re.sub(r"<(script|style|noscript)[\s\S]*?</\1>", " ", raw, flags=re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw))).strip()


def main():
    index = json.loads((RAW_DIR / "index.json").read_text())
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for key, meta in sorted(index.items()):
        platform = key.rsplit("_", 1)[0]
        if only and platform != only:
            continue
        text = visible_text(RAW_DIR / f"{key}.html")
        counts = {k: len(re.findall(p, text, re.I)) for k, p in PATTERNS.items()}
        print(f"{key:16} {len(text):7,} chars  " + "  ".join(f"{k}={v}" for k, v in counts.items() if v))
        if only:
            print(f"  {meta['snapshot']}")
            for k, p in PATTERNS.items():
                for m in list(re.finditer(p, text, re.I))[:6]:
                    print(f"  [{k}] ...{text[max(0, m.start() - 90):m.end() + 70]}...")


if __name__ == "__main__":
    main()
