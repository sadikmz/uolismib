#!/usr/bin/env python3
"""
Plot domain distribution comparison before and after liftover.

Usage:
    python plot_domain_comparison.py --before domain_dist_before.tsv --after domain_dist_after.tsv
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (16, 12)
plt.rcParams['font.size'] = 10


def load_and_filter_longest_ipr(filepath):
    """
    Load domain distribution file and filter for longest IPR domains.

    Args:
        filepath: Path to domain_distribution.tsv file

    Returns:
        DataFrame with only longest IPR domains
    """
    df = pd.read_csv(filepath, sep='\t')

    # Filter for rows where is_longest_ipr == 'T'
    longest_ipr = df[df['is_longest_ipr'] == 'T'].copy()

    return longest_ipr


def plot_comparison(before_df, after_df, output_prefix='domain_comparison'):
    """
    Create comprehensive comparison plots.

    Args:
        before_df: DataFrame with before liftover data
        after_df: DataFrame with after liftover data
        output_prefix: Prefix for output files
    """
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Domain Distribution Comparison: Before vs After Liftover',
                 fontsize=16, fontweight='bold', y=0.995)

    # 1. Domain length distribution (histogram)
    ax = axes[0, 0]
    ax.hist(before_df['domain_length'], bins=50, alpha=0.6, label='Before',
            color='#3498db', edgecolor='black')
    ax.hist(after_df['domain_length'], bins=50, alpha=0.6, label='After',
            color='#e74c3c', edgecolor='black')
    ax.set_xlabel('Domain Length (aa)', fontweight='bold')
    ax.set_ylabel('Frequency', fontweight='bold')
    ax.set_title('Longest IPR Domain Length Distribution', fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3)

    # 2. Domain length distribution (box plot)
    ax = axes[0, 1]
    box_data = [before_df['domain_length'], after_df['domain_length']]
    bp = ax.boxplot(box_data, labels=['Before', 'After'], patch_artist=True,
                    showfliers=False, widths=0.6)
    bp['boxes'][0].set_facecolor('#3498db')
    bp['boxes'][1].set_facecolor('#e74c3c')
    for element in ['whiskers', 'fliers', 'means', 'medians', 'caps']:
        plt.setp(bp[element], color='black', linewidth=1.5)
    ax.set_ylabel('Domain Length (aa)', fontweight='bold')
    ax.set_title('Domain Length Distribution (Box Plot)', fontweight='bold')
    ax.grid(axis='y', alpha=0.3)

    # Add statistics
    before_median = before_df['domain_length'].median()
    after_median = after_df['domain_length'].median()
    ax.text(0.02, 0.98, f'Before median: {before_median:.0f} aa\nAfter median: {after_median:.0f} aa',
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # 3. Database distribution
    ax = axes[0, 2]
    before_db = before_df['analysis'].value_counts().head(10)
    after_db = after_df['analysis'].value_counts().head(10)

    # Combine and sort
    all_dbs = sorted(set(before_db.index) | set(after_db.index))
    before_counts = [before_db.get(db, 0) for db in all_dbs]
    after_counts = [after_db.get(db, 0) for db in all_dbs]

    x = np.arange(len(all_dbs))
    width = 0.35
    ax.bar(x - width/2, before_counts, width, label='Before', color='#3498db', alpha=0.8)
    ax.bar(x + width/2, after_counts, width, label='After', color='#e74c3c', alpha=0.8)
    ax.set_xlabel('Database', fontweight='bold')
    ax.set_ylabel('Count', fontweight='bold')
    ax.set_title('Database Distribution (Top 10)', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(all_dbs, rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # 4. Protein count comparison
    ax = axes[1, 0]
    before_proteins = len(before_df['protein_accession'].unique())
    after_proteins = len(after_df['protein_accession'].unique())

    bars = ax.bar(['Before', 'After'], [before_proteins, after_proteins],
                  color=['#3498db', '#e74c3c'], alpha=0.8, edgecolor='black', linewidth=2)
    ax.set_ylabel('Number of Proteins', fontweight='bold')
    ax.set_title('Protein Count with Longest IPR Domains', fontweight='bold')
    ax.grid(axis='y', alpha=0.3)

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}',
                ha='center', va='bottom', fontweight='bold')

    # 5. Multiple longest IPR domains
    ax = axes[1, 1]
    before_multiple = (before_df['multiple_longest'] == 'yes').sum()
    after_multiple = (after_df['multiple_longest'] == 'yes').sum()
    before_single = (before_df['multiple_longest'] == 'no').sum()
    after_single = (after_df['multiple_longest'] == 'no').sum()

    x = np.arange(2)
    width = 0.35
    ax.bar(x - width/2, [before_single, before_multiple], width,
           label='Before', color='#3498db', alpha=0.8)
    ax.bar(x + width/2, [after_single, after_multiple], width,
           label='After', color='#e74c3c', alpha=0.8)
    ax.set_ylabel('Count', fontweight='bold')
    ax.set_title('Proteins with Single vs Multiple Longest IPR', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(['Single Longest', 'Multiple Longest'])
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # 6. Summary statistics table
    ax = axes[1, 2]
    ax.axis('tight')
    ax.axis('off')

    stats_data = [
        ['Metric', 'Before', 'After', 'Change'],
        ['Total Proteins',
         f'{before_proteins:,}',
         f'{after_proteins:,}',
         f'{after_proteins - before_proteins:+,}'],
        ['Mean Length (aa)',
         f'{before_df["domain_length"].mean():.1f}',
         f'{after_df["domain_length"].mean():.1f}',
         f'{after_df["domain_length"].mean() - before_df["domain_length"].mean():+.1f}'],
        ['Median Length (aa)',
         f'{before_median:.0f}',
         f'{after_median:.0f}',
         f'{after_median - before_median:+.0f}'],
        ['Min Length (aa)',
         f'{before_df["domain_length"].min():.0f}',
         f'{after_df["domain_length"].min():.0f}',
         f'{after_df["domain_length"].min() - before_df["domain_length"].min():.0f}'],
        ['Max Length (aa)',
         f'{before_df["domain_length"].max():.0f}',
         f'{after_df["domain_length"].max():.0f}',
         f'{after_df["domain_length"].max() - before_df["domain_length"].max():.0f}'],
        ['# Databases',
         f'{before_df["analysis"].nunique()}',
         f'{after_df["analysis"].nunique()}',
         f'{after_df["analysis"].nunique() - before_df["analysis"].nunique():+}'],
        ['Multiple Longest',
         f'{before_multiple:,}',
         f'{after_multiple:,}',
         f'{after_multiple - before_multiple:+,}'],
    ]

    table = ax.table(cellText=stats_data, cellLoc='center', loc='center',
                     bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)

    # Style header row
    for i in range(4):
        table[(0, i)].set_facecolor('#34495e')
        table[(0, i)].set_text_props(weight='bold', color='white')

    # Alternate row colors
    for i in range(1, len(stats_data)):
        for j in range(4):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#ecf0f1')

    ax.set_title('Summary Statistics', fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig(f'{output_prefix}_overview.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {output_prefix}_overview.png")
    plt.close()

    # Create additional detailed plots
    plot_length_comparison_scatter(before_df, after_df, output_prefix)
    plot_cumulative_distribution(before_df, after_df, output_prefix)


def plot_length_comparison_scatter(before_df, after_df, output_prefix):
    """
    Create scatter plot comparing domain lengths for same proteins.
    """
    # Merge on protein_accession to compare same proteins
    merged = before_df[['protein_accession', 'domain_length']].merge(
        after_df[['protein_accession', 'domain_length']],
        on='protein_accession',
        suffixes=('_before', '_after'),
        how='inner'
    )

    if len(merged) > 0:
        fig, ax = plt.subplots(figsize=(10, 10))

        # Scatter plot
        ax.scatter(merged['domain_length_before'], merged['domain_length_after'],
                  alpha=0.5, s=30, color='#3498db', edgecolors='black', linewidth=0.5)

        # Add diagonal line (y=x)
        max_val = max(merged['domain_length_before'].max(), merged['domain_length_after'].max())
        ax.plot([0, max_val], [0, max_val], 'r--', linewidth=2, label='No change (y=x)')

        ax.set_xlabel('Domain Length Before (aa)', fontweight='bold', fontsize=12)
        ax.set_ylabel('Domain Length After (aa)', fontweight='bold', fontsize=12)
        ax.set_title('Domain Length Comparison for Same Proteins\n(Longest IPR Domain)',
                    fontweight='bold', fontsize=14)
        ax.legend()
        ax.grid(alpha=0.3)
        ax.set_aspect('equal')

        # Add statistics
        correlation = merged['domain_length_before'].corr(merged['domain_length_after'])
        unchanged = (merged['domain_length_before'] == merged['domain_length_after']).sum()
        increased = (merged['domain_length_after'] > merged['domain_length_before']).sum()
        decreased = (merged['domain_length_after'] < merged['domain_length_before']).sum()

        stats_text = f'n = {len(merged):,} proteins\n'
        stats_text += f'Correlation: {correlation:.3f}\n'
        stats_text += f'Unchanged: {unchanged:,} ({100*unchanged/len(merged):.1f}%)\n'
        stats_text += f'Increased: {increased:,} ({100*increased/len(merged):.1f}%)\n'
        stats_text += f'Decreased: {decreased:,} ({100*decreased/len(merged):.1f}%)'

        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
               fontsize=10)

        plt.tight_layout()
        plt.savefig(f'{output_prefix}_scatter.png', dpi=300, bbox_inches='tight')
        print(f"Saved: {output_prefix}_scatter.png")
        plt.close()


def plot_cumulative_distribution(before_df, after_df, output_prefix):
    """
    Create cumulative distribution plot.
    """
    fig, ax = plt.subplots(figsize=(12, 8))

    # Sort data
    before_sorted = np.sort(before_df['domain_length'])
    after_sorted = np.sort(after_df['domain_length'])

    # Calculate cumulative
    before_cum = np.arange(1, len(before_sorted) + 1) / len(before_sorted) * 100
    after_cum = np.arange(1, len(after_sorted) + 1) / len(after_sorted) * 100

    # Plot
    ax.plot(before_sorted, before_cum, linewidth=2, label='Before', color='#3498db')
    ax.plot(after_sorted, after_cum, linewidth=2, label='After', color='#e74c3c')

    ax.set_xlabel('Domain Length (aa)', fontweight='bold', fontsize=12)
    ax.set_ylabel('Cumulative Percentage (%)', fontweight='bold', fontsize=12)
    ax.set_title('Cumulative Distribution of Longest IPR Domain Lengths',
                fontweight='bold', fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(alpha=0.3)

    # Add percentile lines
    for percentile in [25, 50, 75]:
        before_val = np.percentile(before_df['domain_length'], percentile)
        after_val = np.percentile(after_df['domain_length'], percentile)
        ax.axhline(y=percentile, color='gray', linestyle=':', alpha=0.5)
        ax.text(ax.get_xlim()[1] * 0.02, percentile + 2, f'{percentile}th',
               fontsize=9, color='gray')

    plt.tight_layout()
    plt.savefig(f'{output_prefix}_cumulative.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {output_prefix}_cumulative.png")
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description='Compare domain distributions before and after liftover'
    )
    parser.add_argument(
        '--before',
        required=True,
        help='Domain distribution file before liftover (TSV)'
    )
    parser.add_argument(
        '--after',
        required=True,
        help='Domain distribution file after liftover (TSV)'
    )
    parser.add_argument(
        '--output',
        default='domain_comparison',
        help='Output prefix for plots (default: domain_comparison)'
    )

    args = parser.parse_args()

    print(f"Loading before data from: {args.before}")
    before_df = load_and_filter_longest_ipr(args.before)
    print(f"  - Found {len(before_df):,} longest IPR domains from {before_df['protein_accession'].nunique():,} proteins")

    print(f"Loading after data from: {args.after}")
    after_df = load_and_filter_longest_ipr(args.after)
    print(f"  - Found {len(after_df):,} longest IPR domains from {after_df['protein_accession'].nunique():,} proteins")

    print(f"\nCreating comparison plots...")
    plot_comparison(before_df, after_df, args.output)

    print(f"\n✓ Done! Generated plots:")
    print(f"  - {args.output}_overview.png (main comparison)")
    print(f"  - {args.output}_scatter.png (length comparison)")
    print(f"  - {args.output}_cumulative.png (cumulative distribution)")


if __name__ == '__main__':
    main()
