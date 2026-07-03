# statistical_analysis.py
import pandas as pd
from scipy import stats
import numpy as np

df = pd.read_csv('output/temporal_results.csv')

print("="*60)
print("STATISTICAL ANALYSIS")
print("="*60)

# Overall trend test
print("\n1. OVERALL TEMPORAL TREND:")
correlation, p_value = stats.pearsonr(df['Year'].astype(int), df['DODI_Score'])
print(f"   Correlation: r={correlation:.3f}, p={p_value:.4f}")
if p_value < 0.05:
    print(f"   ✅ Significant {'positive' if correlation > 0 else 'negative'} trend")
else:
    print(f"   ⚠️  No significant overall trend")

# Industry comparisons
print("\n2. INDUSTRY TRENDS:")
industries = {
    'Gaming': ['Steam', 'Ubisoft', 'Gog'],
    'Streaming': ['Netflix', 'Spotify'],
    'Software': ['Adobe', 'Microsoft'],
}

for industry, platforms in industries.items():
    industry_df = df[df['Platform'].isin(platforms)]
    r, p = stats.pearsonr(industry_df['Year'].astype(int), industry_df['DODI_Score'])
    print(f"   {industry}: r={r:.3f}, p={p:.4f}")

# Platform-by-platform significance
print("\n3. INDIVIDUAL PLATFORM TRENDS:")
for platform in df['Platform'].unique():
    platform_df = df[df['Platform'] == platform].sort_values('Year')
    if len(platform_df) >= 3:
        r, p = stats.pearsonr(platform_df['Year'].astype(int), platform_df['DODI_Score'])
        sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
        print(f"   {platform:<12} r={r:+.3f}, p={p:.4f} {sig}")