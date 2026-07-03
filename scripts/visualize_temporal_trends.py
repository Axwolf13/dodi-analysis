# visualize_temporal_trends.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load results
df = pd.read_csv('output/temporal_results.csv')

# Setup
sns.set_style("whitegrid")
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Plot 1: All platforms over time
ax1 = axes[0, 0]
for platform in df['Platform'].unique():
    platform_data = df[df['Platform'] == platform].sort_values('Year')
    ax1.plot(platform_data['Year'], platform_data['DODI_Score'], 
             marker='o', label=platform, linewidth=2)

ax1.set_title('DODI Scores Over Time (All Platforms)', fontsize=14, fontweight='bold')
ax1.set_xlabel('Year')
ax1.set_ylabel('DODI Score (Higher = More Deceptive)')
ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
ax1.grid(True, alpha=0.3)

# Plot 2: By industry
ax2 = axes[0, 1]
industries = {
    'Gaming': ['Steam', 'Ubisoft', 'Gog'],
    'Streaming': ['Netflix', 'Spotify'],
    'Software': ['Adobe', 'Microsoft'],
    'Social': ['Facebook', 'Twitter'],
    'E-commerce': ['Amazon']
}

for industry, platforms in industries.items():
    industry_data = df[df['Platform'].isin(platforms)]
    industry_avg = industry_data.groupby('Year')['DODI_Score'].mean()
    ax2.plot(industry_avg.index, industry_avg.values,
             marker='o', label=industry, linewidth=2)

ax2.set_title('Average DODI by Industry', fontsize=14, fontweight='bold')
ax2.set_xlabel('Year')
ax2.set_ylabel('Average DODI Score')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Plot 3: Change from 2015 to 2024
ax3 = axes[1, 0]
changes = []
for platform in df['Platform'].unique():
    platform_data = df[df['Platform'] == platform].sort_values('Year')
    if len(platform_data) >= 2:
        start = platform_data.iloc[0]['DODI_Score']
        end = platform_data.iloc[-1]['DODI_Score']
        change_pct = ((end - start) / start) * 100
        changes.append({'Platform': platform, 'Change': change_pct})

changes_df = pd.DataFrame(changes).sort_values('Change')
colors = ['green' if x < 0 else 'red' for x in changes_df['Change']]

ax3.barh(changes_df['Platform'], changes_df['Change'], color=colors)
ax3.set_title('Percentage Change 2015→2024', fontsize=14, fontweight='bold')
ax3.set_xlabel('Change (%)')
ax3.axvline(x=0, color='black', linestyle='--', linewidth=1)
ax3.grid(True, alpha=0.3, axis='x')

# Plot 4: Distribution by year
ax4 = axes[1, 1]
df.boxplot(column='DODI_Score', by='Year', ax=ax4)
ax4.set_title('DODI Score Distribution by Year', fontsize=14, fontweight='bold')
ax4.set_xlabel('Year')
ax4.set_ylabel('DODI Score')
plt.suptitle('')  # Remove automatic title

plt.tight_layout()
plt.savefig('output/temporal_analysis.png', dpi=300, bbox_inches='tight')
print("✅ Saved: output/temporal_analysis.png")
plt.show()

# Highlight Spotify trajectory
spotify_data = df[df['Platform'] == 'Spotify'].sort_values('Year')
plt.plot(spotify_data['Year'], spotify_data['DODI_Score'], 
         'o-', linewidth=4, markersize=12, color='purple', 
         label='Spotify (GDPR Impact)', zorder=10)

# Add annotation
plt.annotate('GDPR Enforcement\n(May 2018)', 
             xy=(2018, 97.5), xytext=(2016, 105),
             arrowprops=dict(arrowstyle='->', lw=2, color='red'),
             fontsize=11, fontweight='bold', color='red')

# Add box showing improvement
plt.annotate('16% Improvement\n(p=0.045*)', 
             xy=(2024, 83.8), xytext=(2022, 75),
             bbox=dict(boxstyle='round', facecolor='green', alpha=0.3),
             fontsize=10, fontweight='bold')