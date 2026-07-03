# verify_spotify_2015.py
from dodi_analyzer_clean import DODIAnalyzer
from pathlib import Path

file = Path('data/temporal/spotify_2015.txt')

print("="*60)
print("VERIFYING SPOTIFY 2015")
print("="*60)

# Check file size
size = file.stat().st_size
print(f"\nFile size: {size:,} bytes ({size/1024:.1f} KB)")

if size < 1000:
    print("⚠️  WARNING: File is very small!")

# Read content
with open(file, 'r', encoding='utf-8') as f:
    text = f.read()

print(f"\nText length: {len(text):,} characters")
print(f"First 500 characters:")
print("-"*60)
print(text[:500])
print("-"*60)

# Run analysis
analyzer = DODIAnalyzer()
result = analyzer.analyze(text)

print(f"\nDODI Analysis:")
print(f"  DODI Score: {result['dodi_score']}")
print(f"  Ownership count: {result['ownership_count']}")
print(f"  License count: {result['license_count']}")
print(f"  Ratio: {result['ratio']}")
print(f"  Red flags: {result['red_flags']}")
print(f"  Grade level: {result['grade_level']}")

# Diagnosis
print("\n" + "="*60)
if result['ownership_count'] == 0:
    print("❌ PROBLEM FOUND: Zero ownership words!")
    print("   This likely means:")
    print("   - File contains redirect/error page")
    print("   - File is incomplete")
    print("   - File is wrong document")
    print("\n   ACTION: Re-download Spotify 2015 ToS")
elif size < 5000:
    print("⚠️  SUSPICIOUS: File seems too short for full ToS")
    print("   ACTION: Verify this is complete document")
else:
    print("✅ File appears valid")
    print("   Score of 100.0 reflects genuinely terrible ToS")