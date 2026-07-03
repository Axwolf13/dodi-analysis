"""
Batch ToS Analyzer
Processes multiple Terms of Service documents and generates comparison visualizations
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from dodi_analyzer_clean import DODIAnalyzer

def analyze_tos_documents(data_folder):
    """Analyze all .txt files in the data directory."""
    analyzer = DODIAnalyzer()
    results = []
    
    print("Analyzing Terms of Service documents...")
    print("-" * 60)
    
    for root, dirs, files in os.walk(data_folder):
        for file in files:
            if file.endswith(".txt"):
                platform = file.replace("_tos.txt", "").replace(".txt", "").replace("_", " ").title()
                category = os.path.basename(root).capitalize()
                
                try:
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                    
                    result = analyzer.analyze(text)
                    
                    print(f"\n{platform} ({category})")
                    print(f"  DODI Score: {result['dodi_score']}/100")
                    print(f"  Ownership terms: {result['ownership_count']}")
                    print(f"  License terms: {result['license_count']}")
                    print(f"  L/O Ratio: {result['ratio']}")
                    print(f"  Grade level: {result['grade_level']}")
                    print(f"  Red flags: {result['red_flags']}")
                    
                    results.append({
                        "Platform": platform,
                        "Category": category,
                        "DODI Score": result['dodi_score'],
                        "Ownership Words": result['ownership_count'],
                        "License Words": result['license_count'],
                        "Ratio": result['ratio'],
                        "Grade Level": result['grade_level'],
                        "Red Flags": result['red_flags']
                    })
                    
                except Exception as e:
                    print(f"Error processing {file}: {e}")
    
    return results

def save_results(results, output_dir):
    """Save analysis results to CSV and generate visualization."""
    if not results:
        print("No documents found to analyze.")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Create DataFrame and sort by score
    df = pd.DataFrame(results)
    df = df.sort_values('DODI Score', ascending=False)
    
    # Save to CSV
    csv_path = os.path.join(output_dir, "dodi_results.csv")
    df.to_csv(csv_path, index=False)
    print(f"\nResults saved to {csv_path}")
    
    # Generate visualization
    plt.figure(figsize=(10, 6))
    
    # Color mapping based on score ranges
    colors = []
    for score in df['DODI Score']:
        if score >= 75:
            colors.append('#d73027')
        elif score >= 50:
            colors.append('#fc8d59')
        elif score >= 25:
            colors.append('#fee090')
        else:
            colors.append('#91cf60')
    
    bars = plt.bar(df['Platform'], df['DODI Score'], color=colors)
    
    plt.title("Digital Ownership Deception Index (DODI)\nPreliminary Results", 
              fontsize=16, fontweight='bold')
    plt.xlabel("Platform", fontsize=12)
    plt.ylabel("Deception Score (0=Transparent, 100=Deceptive)", fontsize=12)
    plt.ylim(0, 105)
    
    # Reference lines
    plt.axhline(y=75, color='red', linestyle='--', alpha=0.3, label='Highly Deceptive')
    plt.axhline(y=50, color='orange', linestyle='--', alpha=0.3, label='Moderately Deceptive')
    plt.axhline(y=25, color='gray', linestyle='--', alpha=0.3, label='Somewhat Transparent')
    
    # Add score labels
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{height:.1f}', ha='center', va='bottom', fontweight='bold')
    
    plt.legend(loc='upper right')
    plt.tight_layout()
    
    chart_path = os.path.join(output_dir, "dodi_comparison.png")
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    print(f"Chart saved to {chart_path}")
    
    # Summary statistics
    print("\n" + "-" * 60)
    print("Analysis Summary")
    print("-" * 60)
    print(f"Most deceptive: {df.iloc[0]['Platform']} ({df.iloc[0]['DODI Score']:.1f})")
    print(f"Most transparent: {df.iloc[-1]['Platform']} ({df.iloc[-1]['DODI Score']:.1f})")
    print(f"Average score: {df['DODI Score'].mean():.1f}")
    print("-" * 60)

if __name__ == "__main__":
    data_folder = "../data"
    output_folder = "../output"
    
    results = analyze_tos_documents(data_folder)
    save_results(results, output_folder)