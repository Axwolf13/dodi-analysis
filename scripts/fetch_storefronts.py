"""
Fetch archived storefront pages for DODI v2.

For each platform, finds the first successful Wayback Machine capture of a
representative purchase page in the target window and saves the raw HTML
(the `id_` form, without the Wayback toolbar) to data/storefront/raw/.

    python scripts/fetch_storefronts.py            # April to September 2024
    python scripts/fetch_storefronts.py --year 2015

Cached pages are not fetched again. Pacing is slow on purpose: the Wayback
APIs rate-limit hard.
"""
import argparse
import gzip
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "storefront" / "raw"
UA = {"User-Agent": "Mozilla/5.0 (DODI storefront study)"}
PAUSE = 6

# One purchase page per platform, matched to the product its contract governs.
# Several candidates each: store URLs move and not every one was archived.
PAGES = {
    "adobe": ["www.adobe.com/creativecloud/plans.html"],
    "amazon": ["www.amazon.com/Atomic-Habits-Proven-Build-Break-ebook/dp/B07D23CFGR",
               "www.amazon.com/Oppenheimer-Cillian-Murphy/dp/B0CFGX8V66",
               "www.amazon.com/gp/video/detail/B0CFGX8V66",
               "www.amazon.com/Hobbit-J-R-R-Tolkien-ebook/dp/B007978NPG",
               "www.amazon.com/dp/B007978NPG"],
    "gog": ["www.gog.com/en/game/cyberpunk_2077", "www.gog.com/game/cyberpunk_2077",
            "www.gog.com/en/game/the_witcher_3_wild_hunt_game_of_the_year_edition",
            "www.gog.com/game/the_witcher_3_wild_hunt_game_of_the_year_edition"],
    "microsoft": ["www.xbox.com/en-US/games/store/cyberpunk-2077/bx3m8l83bbrw",
                  "www.microsoft.com/en-us/p/cyberpunk-2077/bx3m8l83bbrw",
                  "www.xbox.com/en-US/games/store/minecraft/9mvxmvt8zkwc"],
    "netflix": ["www.netflix.com/", "www.netflix.com/signup/planform"],
    "spotify": ["www.spotify.com/us/premium/", "www.spotify.com/premium/"],
    "steam": ["store.steampowered.com/app/1091500/Cyberpunk_2077/",
              "store.steampowered.com/app/292030/The_Witcher_3_Wild_Hunt/"],
    # x.com itself is a JavaScript shell with no text in the archive; the help page describes the offer
    "twitter": ["help.x.com/en/using-x/x-premium", "help.twitter.com/en/using-x/x-premium"],
    "ubisoft": ["store.ubisoft.com/us/assassins-creed-mirage/6214b6c3c7c7f1f36e8a3f1b.html",
                "store.ubisoft.com/us/home", "store.ubisoft.com/us/"],
    # facebook: sells no content to users, so there is no purchase page to fetch
}


def get(url, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        data = r.read()
    # the archive sometimes replays the original gzip body without decoding it
    return gzip.decompress(data) if data[:2] == b"\x1f\x8b" else data


def first_capture(page, start, end):
    q = "https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode({
        "url": page, "from": start, "to": end, "limit": 3, "output": "json",
        "filter": "statuscode:200", "fl": "timestamp,original",
    })
    rows = json.loads(get(q) or b"[]")
    return rows[1] if len(rows) > 1 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2024)
    args = ap.parse_args()
    start, end = f"{args.year}04", f"{args.year}09"
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    index_path = RAW_DIR / "index.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else {}

    for platform, candidates in PAGES.items():
        key = f"{platform}_{args.year}"
        if key in index and (RAW_DIR / f"{key}.html").exists():
            print(f"  {key}: cached ({index[key]['snapshot']})")
            continue
        for page in candidates:
            try:
                hit = first_capture(page, start, end)
            except Exception as e:
                print(f"  {key}: CDX failed for {page}: {e}")
                hit = None
            time.sleep(PAUSE)
            if not hit:
                continue
            ts, original = hit
            snapshot = f"https://web.archive.org/web/{ts}/{original}"
            try:
                html = get(f"https://web.archive.org/web/{ts}id_/{original}")
            except Exception as e:
                print(f"  {key}: fetch failed for {snapshot}: {e}")
                time.sleep(PAUSE)
                continue
            (RAW_DIR / f"{key}.html").write_bytes(html)
            index[key] = {"page": page, "snapshot": snapshot, "timestamp": ts, "bytes": len(html)}
            index_path.write_text(json.dumps(index, indent=2))
            print(f"  {key}: {snapshot} ({len(html) // 1024} KB)")
            time.sleep(PAUSE)
            break
        else:
            print(f"  {key}: no capture found")


if __name__ == "__main__":
    main()
