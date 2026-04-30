#!/usr/bin/env python3
"""
Correct InterPro summary using bash-verified counts
"""
import matplotlib.pyplot as plt
from pathlib import Path

# Correct statistics from bash analysis
old_total = 21911
old_with_domains = 18557
old_percentage = (old_with_domains / old_total) * 100

new_total = 14741  
new_with_domains = 12605
new_percentage = (new_with_domains / new_total) * 100

# Create summary plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Bar chart comparison
categories = ['Total\nProteins', 'With InterPro\nDomains', 'Without InterPro\nDomains']

old_values = [old_total, old_with_domains, old_total - old_with_domains]
new_values = [new_total, new_with_domains, new_total - new_with_domains]

x = range(len(categories))
width = 0.35

bars1 = ax1.bar([i - width/2 for i in x], old_values, width, 
                label='Old (foc67_v68)', color='#ff9999')
bars2 = ax1.bar([i + width/2 for i in x], new_values, width,
                label='New (GCF_013085055.1)', color='#99ccff')

ax1.set_ylabel('Number of Proteins')
ax1.set_title('InterPro Domain Coverage\nF. oxysporum Old vs New Annotation')
ax1.set_xticks(x)
ax1.set_xticklabels(categories)
ax1.legend()

# Add value labels
for i, (old_val, new_val) in enumerate(zip(old_values, new_values)):
    ax1.text(i - width/2, old_val + max(old_values)*0.01, f'{old_val:,}', 
            ha='center', va='bottom', fontsize=10)
    ax1.text(i + width/2, new_val + max(new_values)*0.01, f'{new_val:,}',
            ha='center', va='bottom', fontsize=10)

# Percentage comparison  
annotations = ['Old\n(foc67_v68)', 'New\n(GCF_013085055.1)']
percentages = [old_percentage, new_percentage]
colors = ['#ff9999', '#99ccff']

bars = ax2.bar(annotations, percentages, color=colors)
ax2.set_ylabel('Percentage (%)')
ax2.set_title('Percentage of Proteins\nwith InterPro Domains')
ax2.set_ylim(0, 100)

# Add percentage labels
for bar, pct in zip(bars, percentages):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f'{pct:.1f}%', ha='center', va='bottom', fontsize=14, fontweight='bold')

plt.tight_layout()

# Save plot
output_path = Path("plots") / "interpro_corrected_summary.png"
output_path.parent.mkdir(exist_ok=True)
plt.savefig(output_path, dpi=300, bbox_inches='tight')

# Print summary
print("="*70)
print("F. OXYSPORUM INTERPRO DOMAIN SUMMARY (CORRECTED)")
print("="*70)
print(f"{'Metric':<35} {'Old (foc67_v68)':<15} {'New (GCF_013085055.1)':<15}")
print("-"*70)
print(f"{'Total proteins':<35} {old_total:,<15} {new_total:,<15}")
print(f"{'With InterPro domains':<35} {old_with_domains:,<15} {new_with_domains:,<15}")
print(f"{'Without InterPro domains':<35} {old_total-old_with_domains:,<15} {new_total-new_with_domains:,<15}")
print(f"{'Percentage with domains':<35} {old_percentage:.1f}%{'':<11} {new_percentage:.1f}%{'':<11}")
print("="*70)
print(f"\nPlot saved to: {output_path}")
