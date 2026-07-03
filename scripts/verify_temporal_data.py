# verify_temporal_data.py
import os
from pathlib import Path

temporal_dir = Path('data/temporal')

print("🔍 TEMPORAL DATA VERIFICATION")
print("="*60)

files = sorted(temporal_dir.glob('*.txt'))

print(f"\nTotal files: {len(files)}")
print(f"\nFiles by platform:")

# Group by platform
platforms = {}
for f in files:
    platform = f.stem.split('_')[0]
    if platform not in platforms:
        platforms[platform] = []
    platforms[platform].append(f.stem)

for platform, file_list in sorted(platforms.items()):
    print(f"\n{platform.upper()}: {len(file_list)} files")
    for fname in sorted(file_list):
        file_path = temporal_dir / f"{fname}.txt"
        size_kb = file_path.stat().st_size / 1024
        status = "✅" if size_kb > 1 else "⚠️ TOO SMALL"
        print(f"  {fname:<25} {size_kb:>6.1f} KB  {status}")

print("\n" + "="*60)
print("VERIFICATION COMPLETE")
print("="*60)

# Check for issues
issues = []
for f in files:
    if f.stat().st_size < 1024:  # Less than 1 KB
        issues.append(f"{f.name} is suspiciously small")

if issues:
    print("\n⚠️ ISSUES FOUND:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("\n✅ ALL FILES LOOK GOOD!")
    print("\nREADY FOR ANALYSIS! 🚀")