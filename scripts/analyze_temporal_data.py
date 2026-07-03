# analyze_temporal_data.py
from pathlib import Path
from dodi_analyzer_clean import DODIAnalyzer
import csv

def analyze_temporal_dataset():
    """
    Run DODI analysis on all temporal ToS files
    """
    temporal_dir = Path('data/temporal')
    output_file = 'output/temporal_results.csv'
    
    print("="*60)
    print("TEMPORAL DODI ANALYSIS")
    print("="*60 + "\n")
    
    analyzer = DODIAnalyzer()
    results = []
    
    files = sorted(temporal_dir.glob('*.txt'))
    
    for i, tos_file in enumerate(files, 1):
        # Parse filename: platform_year.txt
        parts = tos_file.stem.split('_')
        platform = parts[0].title()
        year = parts[1] if len(parts) > 1 else 'Unknown'
        
        print(f"[{i}/{len(files)}] Analyzing {platform} {year}...", end=' ')
        
        try:
            with open(tos_file, 'r', encoding='utf-8') as f:
                text = f.read()
            
            analysis = analyzer.analyze(text)
            
            results.append({
                'Platform': platform,
                'Year': year,
                'DODI_Score': analysis['dodi_score'],
                'License_Ratio': analysis['ratio'],
                'Readability': analysis['grade_level'],
                'Red_Flags': analysis['red_flags'],
                'Ownership_Count': analysis['ownership_count'],
                'License_Count': analysis['license_count']
            })
            
            print(f"✅ DODI: {analysis['dodi_score']}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Save results
    if results:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        
        print(f"\n{'='*60}")
        print(f"✅ ANALYSIS COMPLETE!")
        print(f"{'='*60}")
        print(f"\nResults saved to: {output_file}")
        print(f"Total documents analyzed: {len(results)}")
        
        # Quick summary
        print(f"\n{'='*60}")
        print("QUICK SUMMARY")
        print(f"{'='*60}")
        
        platforms = {}
        for r in results:
            if r['Platform'] not in platforms:
                platforms[r['Platform']] = []
            platforms[r['Platform']].append(r)
        
        for platform, data in sorted(platforms.items()):
            scores = [d['DODI_Score'] for d in sorted(data, key=lambda x: x['Year'])]
            years = [d['Year'] for d in sorted(data, key=lambda x: x['Year'])]
            
            if len(scores) >= 2:
                change = scores[-1] - scores[0]
                change_pct = (change / scores[0] * 100) if scores[0] > 0 else 0
                trend = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                
                print(f"\n{platform}:")
                print(f"  Years: {years[0]} → {years[-1]}")
                print(f"  DODI:  {scores[0]:.1f} → {scores[-1]:.1f}")
                print(f"  Change: {change:+.1f} ({change_pct:+.1f}%) {trend}")
    
    return results

if __name__ == "__main__":
    analyze_temporal_dataset()