import datetime

def generate_wayback_links():
    print("🕰️ TEMPORAL STUDY DATA COLLECTION LIST")
    print("="*60)
    print("Instructions:")
    print("1. Click the link.")
    print("2. Copy the text of the Terms of Service.")
    print("3. Save as: data/temporal/[Platform]_[Year].txt")
    print("   Example: data/temporal/Steam_2015.txt")
    print("="*60 + "\n")

    platforms = {
        "Steam": "https://store.steampowered.com/subscriber_agreement/",
        "Netflix": "https://help.netflix.com/legal/termsofuse",
        "Spotify": "https://www.spotify.com/legal/end-user-agreement/",
        "Ubisoft": "https://legal.ubi.com/termsofuse/",
        "GOG": "https://support.gog.com/hc/en-us/articles/212632089",
        "Adobe": "https://www.adobe.com/legal/terms.html",
        "Microsoft": "https://www.microsoft.com/en-us/servicesagreement/",
        "Amazon": "https://www.amazon.com/gp/help/customer/display.html?nodeId=508088",
        "Twitter": "https://twitter.com/tos",
        "Facebook": "https://www.facebook.com/legal/terms"
    }

    # We target mid-year (July 1st) to avoid holiday code freezes
    target_dates = ["20150701", "20180701", "20210701", "20240701"]

    for name, url in platforms.items():
        print(f"📂 PLATFORM: {name}")
        for date in target_dates:
            year = date[:4]
            # Wayback Machine API format
            wayback_url = f"https://web.archive.org/web/{date}/{url}"
            print(f"   - [ ] {year}: {wayback_url}")
        print("-" * 40)

if __name__ == "__main__":
    generate_wayback_links()