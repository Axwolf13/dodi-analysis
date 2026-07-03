# test_weights_face_validity.py (CORRECTED PATHS)
"""
Test different weight schemes against preliminary results
Goal: Ensure face validity is preserved (Ubisoft high, GOG low)
"""

from dodi_analyzer_clean import DODIAnalyzer
import os

# Your preliminary platforms (CORRECTED PATHS)
test_files = {
    'Ubisoft': 'data/gaming/ubisoft_tos.txt',
    'Steam': 'data/gaming/steam_tos.txt',
    'Netflix': 'data/streaming/netflix_tos.txt',
    'GOG': 'data/gaming/gog_tos.txt'
}

# First, let's find the actual files
print("Looking for files...")
for platform, path in test_files.items():
    if os.path.exists(path):
        print(f"✅ Found: {path}")
    else:
        print(f"❌ Missing: {path}")

def test_weight_scheme(readability_w, ratio_w, red_flag_w, scheme_name):
    """Test a specific weight scheme"""
    
    print(f"\n{'='*60}")
    print(f"{scheme_name}")
    print(f"Weights: Readability {readability_w*100:.0f}%, License {ratio_w*100:.0f}%, Red Flags {red_flag_w*100:.0f}%")
    print(f"{'='*60}")
    
    import textstat
    
    results = {}
    
    for platform, filepath in test_files.items():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Manual calculation with custom weights
            analyzer = DODIAnalyzer()
            text_lower = text.lower()
            
            # Get base metrics
            ownership_count = sum(text_lower.count(w) for w in analyzer.ownership_words)
            license_count = sum(text_lower.count(w) for w in analyzer.license_words)
            
            if ownership_count == 0:
                ratio_score = 100
            else:
                ratio = license_count / ownership_count
                ratio_score = min((ratio / 10) * 100, 100)
            
            try:
                grade_level = textstat.flesch_kincaid_grade(text)
            except:
                grade_level = 12
            
            if grade_level <= 8:
                readability_penalty = 0
            elif grade_level >= 16:
                readability_penalty = 100
            else:
                readability_penalty = ((grade_level - 8) / 8) * 100
            
            red_flag_count = sum(text_lower.count(phrase) for phrase in analyzer.red_flags)
            red_flag_score = min((red_flag_count / 50) * 100, 100)
            
            # Apply custom weights
            dodi_score = (readability_penalty * readability_w) + (ratio_score * ratio_w) + (red_flag_score * red_flag_w)
            
            results[platform] = round(dodi_score, 1)
            print(f"{platform:12} {dodi_score:5.1f}")
            
        except Exception as e:
            print(f"{platform:12} ERROR: {e}")
    
    # Check face validity
    print(f"\nFace Validity Check:")
    if 'Ubisoft' in results and 'GOG' in results:
        separation = results['Ubisoft'] - results['GOG']
        if results['Ubisoft'] > 70 and results['GOG'] < 40:
            print(f"  ✅ PASS: Ubisoft ({results['Ubisoft']}) >> GOG ({results['GOG']}) | Gap: {separation:.1f}")
        else:
            print(f"  ❌ FAIL: Ubisoft ({results.get('Ubisoft', 'N/A')}) vs GOG ({results.get('GOG', 'N/A')})")
    
    return results

if __name__ == "__main__":
    
    print("\nTESTING WEIGHT SCHEMES FOR FACE VALIDITY")
    print("="*60)
    print("Target: Ubisoft ~75, Steam ~74, Netflix ~73, GOG ~32")
    print("="*60)
    
    # Test all three schemes
    
    # Original (preliminary results)
    original = test_weight_scheme(0.25, 0.50, 0.25, "ORIGINAL (Preliminary)")
    
    # Round 2 (first tuning)
    round2 = test_weight_scheme(0.15, 0.60, 0.25, "ROUND 2 (First Tuning)")
    
    # Round 3 (second tuning)  
    round3 = test_weight_scheme(0.10, 0.50, 0.40, "ROUND 3 (Second Tuning)")
    
    # Comparison
    print("\n" + "="*60)
    print("COMPARISON")
    print("="*60)
    print(f"{'Platform':<12} {'Original':<10} {'Round 2':<10} {'Round 3':<10}")
    print("-"*60)
    
    for platform in test_files.keys():
        if platform in original:
            print(f"{platform:<12} {original[platform]:<10.1f} {round2.get(platform, 0):<10.1f} {round3.get(platform, 0):<10.1f}")
    
    print("\n" + "="*60)
    print("FINAL RECOMMENDATION")
    print("="*60)
    
    # Determine which scheme is best
    all_pass = []
    
    for name, results in [("ORIGINAL", original), ("ROUND 2", round2), ("ROUND 3", round3)]:
        if 'Ubisoft' in results and 'GOG' in results:
            if results['Ubisoft'] > 70 and results['GOG'] < 40:
                all_pass.append(name)
    
    if all_pass:
        print(f"Schemes that pass face validity: {', '.join(all_pass)}")
        if "ORIGINAL" in all_pass:
            print("\n✅ RECOMMENDATION: Use ORIGINAL (25/50/25)")
            print("   Reason: Conservative, theoretically grounded, already validated")
        else:
            print(f"\n✅ RECOMMENDATION: Use {all_pass[0]}")
    else:
        print("⚠️  None passed - need to debug")
    
    print("\nFor temporal study: Use ONE scheme consistently.")