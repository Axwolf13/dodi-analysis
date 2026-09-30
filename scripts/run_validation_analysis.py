# run_validation_analysis.py (FINAL WORKING VERSION)
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

# Import your DODIAnalyzer
import sys
sys.path.append('../')
from dodi_analyzer_clean import DODIAnalyzer

def run_validation():
    """
    Run DODI on validation dataset and correlate with ToS;DR grades
    """
    print("="*60)
    print("DODI VALIDATION STUDY")
    print("="*60 + "\n")
    
    # Load ToS;DR grades
    grades_df = pd.read_csv('tosdr_grades.csv')
    grades_df = grades_df[grades_df['Grade'] != 'N/A']
    
    results = []
    
    # Create analyzer instance once
    analyzer = DODIAnalyzer()
    
    # Analyze each ToS file
    validation_dir = Path('data/validation')
    
    for tos_file in validation_dir.glob('*.txt'):
        # Match filename to service
        service_slug = tos_file.stem.replace('_tos', '')
        
        # Find corresponding grade
        service_row = grades_df[
            grades_df['Service'].str.lower().str.replace(' ', '_') == service_slug
        ]
        
        if service_row.empty:
            continue
        
        service_name = service_row.iloc[0]['Service']
        tosdr_grade = service_row.iloc[0]['Grade']
        reviewed = str(service_row.iloc[0]['Reviewed']) == 'True'
        
        print(f"Analyzing {service_name}...")
        
        try:
            # Read the ToS text
            with open(tos_file, 'r', encoding='utf-8') as f:
                tos_text = f.read()
            
            # Analyze using your DODIAnalyzer
            analysis = analyzer.analyze(tos_text)
            
            results.append({
                'Service': service_name,
                'ToSDR_Grade': tosdr_grade,
                'Reviewed': reviewed,
                'DODI_Score': analysis['dodi_score'],
                'License_Ratio': analysis['ratio'],
                'Readability': analysis['grade_level'],
                'Red_Flags': analysis['red_flags'],
                'Ownership_Count': analysis['ownership_count'],
                'License_Count': analysis['license_count']
            })
            
            print(f"  ToS;DR: {tosdr_grade} | DODI: {analysis['dodi_score']:.1f}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    if df.empty:
        print("\n❌ No results - check file matching")
        return None, None, None
    
    df.to_csv('validation_results.csv', index=False)
    
    print(f"\n✅ Analyzed {len(results)} services")
    
    # STATISTICAL ANALYSIS
    print("\n" + "="*60)
    print("STATISTICAL VALIDATION")
    print("="*60 + "\n")
    
    # Convert grades to numeric
    grade_map = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5}
    df['Grade_Numeric'] = df['ToSDR_Grade'].map(grade_map)
    
    # Pearson correlation
    # Unreviewed ToS;DR grades are provisional, so the headline statistics use
    # reviewed grades only; including them is reported as a sensitivity check
    reviewed = df[df['Reviewed']]
    rho, rho_p = stats.spearmanr(reviewed['DODI_Score'], reviewed['Grade_Numeric'])
    r, p_value = stats.pearsonr(reviewed['DODI_Score'], reviewed['Grade_Numeric'])
    print(f"Reviewed grades only (n = {len(reviewed)})")
    print(f"Spearman correlation (rho): {rho:.3f}, p = {rho_p:.4f}")
    rho_all, p_all = stats.spearmanr(df['DODI_Score'], df['Grade_Numeric'])
    print(f"Sensitivity, including unreviewed grades (n = {len(df)}): "
          f"rho = {rho_all:.3f}, p = {p_all:.4f}")
    
    print(f"Pearson Correlation (r): {r:.3f}")
    print(f"P-value: {p_value:.6f}")
    print(f"R-squared: {r**2:.3f}")
    
    if p_value < 0.001:
        sig = "*** (p < 0.001)"
    elif p_value < 0.01:
        sig = "** (p < 0.01)"
    elif p_value < 0.05:
        sig = "* (p < 0.05)"
    else:
        sig = "ns"
    
    print(f"Significance: {sig}")
    
    if abs(r) > 0.7:
        strength = "STRONG"
    elif abs(r) > 0.4:
        strength = "MODERATE"
    else:
        strength = "WEAK"
    
    print(f"\nInterpretation: {strength} positive correlation")
    
    if abs(r) > 0.4 and p_value < 0.05:
        print("✅ VALIDATION SUCCESSFUL!")
        print("   DODI successfully predicts ToS;DR expert ratings")
    else:
        print("⚠️  Correlation is weak or not significant")
    
    # Summary by grade
    print("\n" + "="*60)
    print("GRADE COMPARISON")
    print("="*60 + "\n")
    
    summary = df.groupby('ToSDR_Grade')['DODI_Score'].agg([
        ('Count', 'count'),
        ('Mean', 'mean'),
        ('Std', 'std'),
        ('Min', 'min'),
        ('Max', 'max')
    ]).round(2)
    
    print(summary)
    
    # Detailed breakdown
    print("\n" + "="*60)
    print("DETAILED RESULTS")
    print("="*60 + "\n")
    
    for grade in sorted(df['ToSDR_Grade'].unique()):
        grade_df = df[df['ToSDR_Grade'] == grade]
        print(f"\nGrade {grade} ({len(grade_df)} services):")
        for _, row in grade_df.iterrows():
            print(f"  {row['Service']}: {row['DODI_Score']:.1f}")
    
    # Visualization
    create_validation_plots(reviewed, r, p_value, rho, rho_p)
    
    return df, r, p_value

def create_validation_plots(df, r, p_value, rho, rho_p):
    """Create validation visualizations"""
    sns.set_style("whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Box plot
    ax1 = axes[0]
    grade_order = ['A', 'B', 'C', 'D', 'E']
    present_grades = [g for g in grade_order if g in df['ToSDR_Grade'].values]
    
    sns.boxplot(data=df, x='ToSDR_Grade', y='DODI_Score',
                order=present_grades, ax=ax1, palette='RdYlGn_r')
    ax1.set_title('DODI Validation: Score vs ToS;DR Grade', 
                  fontsize=14, fontweight='bold')
    ax1.set_xlabel('ToS;DR Grade (Human Expert)', fontsize=12)
    ax1.set_ylabel('DODI Score (Automated)', fontsize=12)
    ax1.grid(axis='y', alpha=0.3)
    
    # Add sample size to x-axis labels
    labels = [f"{g}\n(n={len(df[df['ToSDR_Grade']==g])})" for g in present_grades]
    ax1.set_xticklabels(labels)
    
    # Scatter plot with regression
    ax2 = axes[1]
    grade_map = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5}
    df['Grade_Num'] = df['ToSDR_Grade'].map(grade_map)
    
    sns.scatterplot(data=df, x='Grade_Num', y='DODI_Score',
                    hue='ToSDR_Grade', s=150, ax=ax2, palette='RdYlGn_r')
    
    # Regression line
    z = np.polyfit(df['Grade_Num'], df['DODI_Score'], 1)
    p = np.poly1d(z)
    x_line = np.linspace(df['Grade_Num'].min(), df['Grade_Num'].max(), 100)
    ax2.plot(x_line, p(x_line), "r--", linewidth=2, label='Regression')
    
    ax2.set_title(f'Spearman ρ = {rho:.2f} (p = {rho_p:.2f}), Pearson r = {r:.2f}, n = {len(df)}',
                  fontsize=14, fontweight='bold')
    ax2.set_xlabel('ToS;DR Grade (1=A, 5=E)', fontsize=12)
    ax2.set_ylabel('DODI Score', fontsize=12)
    ax2.set_xticks([1, 2, 3, 4, 5])
    ax2.set_xticklabels(['A', 'B', 'C', 'D', 'E'])
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig('validation_analysis.png', dpi=300, bbox_inches='tight')
    print(f"\n✅ Saved visualization: validation_analysis.png")
    plt.show()

if __name__ == "__main__":
    df, r, p = run_validation()
    
    if df is not None:
        print("\n" + "="*60)
        print("VALIDATION STUDY COMPLETE")
        print("="*60)
        print(f"\nResults saved to:")
        print(f"  - validation_results.csv")
        print(f"  - validation_analysis.png")
        print(f"\nKey finding: r={r:.3f}, p={p:.4f}")