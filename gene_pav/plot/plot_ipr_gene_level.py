#!/usr/bin/env python3
"""
Gene-level aggregation and conservation analysis
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import argparse
import sys
from pathlib import Path
from matplotlib.gridspec import GridSpec

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300

def load_data(input_file):
    """Load PAVprot output TSV file"""
    df = pd.read_csv(input_file, sep='\t')
    return df

def aggregate_by_gene(df):
    """Aggregate transcript-level data to gene-level"""

    df_both = df[(df['query_total_ipr_domain_length'] > 0) &
                 (df['ref_total_ipr_domain_length'] > 0)].copy()

    # Group by query gene
    gene_stats = []

    for qgene in df_both['new_gene'].unique():
        gene_data = df_both[df_both['new_gene'] == qgene]

        # Take the longest transcript for each gene
        max_idx = gene_data['query_total_ipr_domain_length'].idxmax()
        longest = gene_data.loc[max_idx]

        stats = {
            'new_gene': qgene,
            'old_gene': longest['old_gene'],
            'num_transcripts': len(gene_data),
            'class_codes': ';'.join(sorted(gene_data['class_code'].unique())),
            'class_type': longest['class_type'],
            'query_max_ipr': gene_data['query_total_ipr_domain_length'].max(),
            'query_mean_ipr': gene_data['query_total_ipr_domain_length'].mean(),
            'ref_max_ipr': gene_data['ref_total_ipr_domain_length'].max(),
            'ref_mean_ipr': gene_data['ref_total_ipr_domain_length'].mean(),
            'diff_max': gene_data['query_total_ipr_domain_length'].max() -
                       gene_data['ref_total_ipr_domain_length'].max(),
            'diff_mean': gene_data['query_total_ipr_domain_length'].mean() -
                        gene_data['ref_total_ipr_domain_length'].mean(),
        }

        # Calculate conservation score (0-100, higher = better agreement)
        # Based on: similarity of lengths, low variance
        if stats['ref_max_ipr'] > 0:
            ratio = min(stats['query_max_ipr'], stats['ref_max_ipr']) / max(stats['query_max_ipr'], stats['ref_max_ipr'])
            stats['conservation_score'] = int(ratio * 100)
        else:
            stats['conservation_score'] = 0

        gene_stats.append(stats)

    df_genes = pd.DataFrame(gene_stats)

    # Add categories
    df_genes['agreement_category'] = pd.cut(
        df_genes['conservation_score'],
        bins=[0, 50, 70, 85, 95, 100],
        labels=['Poor (<50%)', 'Fair (50-70%)', 'Good (70-85%)', 'Very Good (85-95%)', 'Excellent (>95%)']
    )

    return df_genes

def plot_gene_level_analysis(df_genes, output_prefix):
    """Plot gene-level aggregated analysis"""

    fig = plt.figure(figsize=(20, 14))
    gs = GridSpec(3, 3, figure=fig, hspace=0.35, wspace=0.35)

    # Plot 1: Conservation score distribution
    ax1 = fig.add_subplot(gs[0, 0])

    ax1.hist(df_genes['conservation_score'], bins=50, color='steelblue',
            alpha=0.7, edgecolor='black', linewidth=1.5)
    ax1.axvline(df_genes['conservation_score'].median(), color='red',
               linestyle='--', linewidth=2, label=f'Median = {df_genes["conservation_score"].median():.1f}%')
    ax1.set_xlabel('Conservation Score (%)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Number of Genes', fontsize=12, fontweight='bold')
    ax1.set_title('Gene-Level IPR Domain Conservation', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)

    # Plot 2: Agreement categories
    ax2 = fig.add_subplot(gs[0, 1])

    cat_counts = df_genes['agreement_category'].value_counts().sort_index()
    colors_cat = ['darkred', 'red', 'orange', 'lightgreen', 'darkgreen']

    bars = ax2.barh(range(len(cat_counts)), cat_counts.values,
                    color=colors_cat, alpha=0.8, edgecolor='black', linewidth=1.5)

    # Add percentages
    total = len(df_genes)
    for i, (bar, count) in enumerate(zip(bars, cat_counts.values)):
        pct = 100 * count / total
        ax2.text(bar.get_width(), bar.get_y() + bar.get_height()/2,
                f'{count} ({pct:.1f}%)', ha='left', va='center',
                fontsize=10, fontweight='bold')

    ax2.set_yticks(range(len(cat_counts)))
    ax2.set_yticklabels(cat_counts.index)
    ax2.set_xlabel('Number of Genes', fontsize=12, fontweight='bold')
    ax2.set_title('Agreement Quality Distribution', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='x')

    # Plot 3: Multi-transcript genes
    ax3 = fig.add_subplot(gs[0, 2])

    transcript_counts = df_genes['num_transcripts'].value_counts().sort_index().head(10)

    ax3.bar(transcript_counts.index.astype(str), transcript_counts.values,
           color='purple', alpha=0.7, edgecolor='black', linewidth=1.5)
    ax3.set_xlabel('Number of Transcripts per Gene', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Number of Genes', fontsize=12, fontweight='bold')
    ax3.set_title('Multi-Transcript Gene Distribution', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')

    # Plot 4: Conservation vs gene complexity (num transcripts)
    ax4 = fig.add_subplot(gs[1, 0])

    # Cap at 10 transcripts for visualization
    df_plot = df_genes[df_genes['num_transcripts'] <= 10].copy()

    data_box = [df_plot[df_plot['num_transcripts'] == i]['conservation_score'].values
                for i in range(1, 11) if len(df_plot[df_plot['num_transcripts'] == i]) > 0]
    labels_box = [str(i) for i in range(1, 11)
                  if len(df_plot[df_plot['num_transcripts'] == i]) > 0]

    bp = ax4.boxplot(data_box, labels=labels_box, patch_artist=True, showfliers=False)
    for patch in bp['boxes']:
        patch.set_facecolor('lightblue')
        patch.set_alpha(0.7)

    ax4.set_xlabel('Number of Transcripts', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Conservation Score (%)', fontsize=12, fontweight='bold')
    ax4.set_title('Conservation vs Gene Complexity', fontsize=14, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')
    ax4.axhline(70, color='orange', linestyle='--', linewidth=1, alpha=0.5, label='Good threshold')
    ax4.legend(fontsize=9)

    # Plot 5: Query vs Ref (gene-level)
    ax5 = fig.add_subplot(gs[1, 1])

    # Sample if too many
    df_sample = df_genes.sample(n=min(5000, len(df_genes)), random_state=42)

    scatter = ax5.scatter(df_sample['query_max_ipr'], df_sample['ref_max_ipr'],
                         c=df_sample['conservation_score'], cmap='RdYlGn',
                         s=30, alpha=0.6, edgecolors='black', linewidth=0.3,
                         vmin=0, vmax=100)

    max_val = max(df_genes['query_max_ipr'].max(), df_genes['ref_max_ipr'].max())
    ax5.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, linewidth=2)

    ax5.set_xlabel('Query Max IPR Length (aa)', fontsize=12, fontweight='bold')
    ax5.set_ylabel('Reference Max IPR Length (aa)', fontsize=12, fontweight='bold')
    ax5.set_title('Gene-Level Comparison\n(colored by conservation)', fontsize=14, fontweight='bold')

    cbar = plt.colorbar(scatter, ax=ax5)
    cbar.set_label('Conservation Score (%)', fontsize=11, fontweight='bold')
    ax5.grid(True, alpha=0.3)

    # Plot 6: Top poorly conserved genes
    ax6 = fig.add_subplot(gs[1, 2])

    df_poor = df_genes.nsmallest(15, 'conservation_score')

    y_pos = np.arange(len(df_poor))
    ax6.barh(y_pos, df_poor['conservation_score'], color='red',
            alpha=0.7, edgecolor='black', linewidth=1.5)
    ax6.set_yticks(y_pos)
    ax6.set_yticklabels([g[:15] for g in df_poor['new_gene']], fontsize=8)
    ax6.set_xlabel('Conservation Score (%)', fontsize=11, fontweight='bold')
    ax6.set_ylabel('Query Gene', fontsize=11, fontweight='bold')
    ax6.set_title('15 Poorest Conserved Genes', fontsize=13, fontweight='bold')
    ax6.grid(True, alpha=0.3, axis='x')
    ax6.invert_yaxis()

    # Plot 7: Difference distribution (gene-level)
    ax7 = fig.add_subplot(gs[2, 0])

    ax7.hist(df_genes['diff_max'], bins=50, color='coral',
            alpha=0.7, edgecolor='black', linewidth=1.5)
    ax7.axvline(0, color='red', linestyle='--', linewidth=2, label='Zero diff')
    ax7.axvline(df_genes['diff_max'].median(), color='green', linestyle='--',
               linewidth=2, label=f'Median = {df_genes["diff_max"].median():.0f} aa')
    ax7.set_xlabel('Difference (Query - Ref) (aa)', fontsize=12, fontweight='bold')
    ax7.set_ylabel('Number of Genes', fontsize=12, fontweight='bold')
    ax7.set_title('Gene-Level Difference Distribution', fontsize=14, fontweight='bold')
    ax7.legend(fontsize=10)
    ax7.grid(True, alpha=0.3)

    # Plot 8: Class code diversity
    ax8 = fig.add_subplot(gs[2, 1])

    # Count number of unique class codes per gene
    df_genes['num_class_codes'] = df_genes['class_codes'].str.split(';').str.len()

    cc_counts = df_genes['num_class_codes'].value_counts().sort_index()

    ax8.bar(cc_counts.index.astype(str), cc_counts.values,
           color='teal', alpha=0.7, edgecolor='black', linewidth=1.5)
    ax8.set_xlabel('Number of Different Class Codes per Gene', fontsize=11, fontweight='bold')
    ax8.set_ylabel('Number of Genes', fontsize=11, fontweight='bold')
    ax8.set_title('Class Code Diversity per Gene', fontsize=13, fontweight='bold')
    ax8.grid(True, alpha=0.3, axis='y')

    # Plot 9: Conservation heatmap by class type and transcript count
    ax9 = fig.add_subplot(gs[2, 2])

    # Create pivot table
    df_heatmap = df_genes[df_genes['num_transcripts'] <= 5].copy()
    pivot = df_heatmap.pivot_table(
        values='conservation_score',
        index='class_type',
        columns='num_transcripts',
        aggfunc='mean'
    )

    sns.heatmap(pivot, annot=True, fmt='.1f', cmap='RdYlGn', vmin=0, vmax=100,
               ax=ax9, cbar_kws={'label': 'Avg Conservation (%)'})
    ax9.set_xlabel('Number of Transcripts', fontsize=11, fontweight='bold')
    ax9.set_ylabel('Class Type', fontsize=11, fontweight='bold')
    ax9.set_title('Conservation by Type & Complexity', fontsize=13, fontweight='bold')

    plt.savefig(f"{output_prefix}_gene_level.png", bbox_inches='tight')
    print(f"Saved: {output_prefix}_gene_level.png", file=sys.stderr)
    plt.close()

def create_gene_summary_table(df_genes, output_prefix):
    """Create comprehensive gene-level summary table"""

    # Sort by conservation score
    df_sorted = df_genes.sort_values('conservation_score').copy()

    # Add rank
    df_sorted['conservation_rank'] = range(1, len(df_sorted) + 1)

    # Select columns for output
    output_cols = [
        'conservation_rank', 'new_gene', 'old_gene', 'conservation_score',
        'agreement_category', 'num_transcripts', 'class_codes', 'class_type',
        'query_max_ipr', 'ref_max_ipr', 'diff_max', 'query_mean_ipr', 'ref_mean_ipr', 'diff_mean'
    ]

    df_output = df_sorted[output_cols].copy()

    # Save full table
    full_file = f"{output_prefix}_gene_summary_full.tsv"
    df_output.to_csv(full_file, sep='\t', index=False, float_format='%.2f')
    print(f"Saved full summary: {full_file}", file=sys.stderr)

    # Save poorly conserved genes (bottom 5%)
    threshold_5 = df_genes['conservation_score'].quantile(0.05)
    df_poor = df_output[df_output['conservation_score'] <= threshold_5].copy()

    poor_file = f"{output_prefix}_poorly_conserved_genes.tsv"
    df_poor.to_csv(poor_file, sep='\t', index=False, float_format='%.2f')
    print(f"Saved poorly conserved genes: {poor_file} (n={len(df_poor)})", file=sys.stderr)

    # Save highly conserved genes (top 5%)
    threshold_95 = df_genes['conservation_score'].quantile(0.95)
    df_good = df_output[df_output['conservation_score'] >= threshold_95].sort_values(
        'conservation_score', ascending=False).copy()

    good_file = f"{output_prefix}_highly_conserved_genes.tsv"
    df_good.to_csv(good_file, sep='\t', index=False, float_format='%.2f')
    print(f"Saved highly conserved genes: {good_file} (n={len(df_good)})", file=sys.stderr)

    return df_output

def print_gene_stats(df_genes):
    """Print gene-level statistics"""

    print("\n" + "="*80, file=sys.stderr)
    print("GENE-LEVEL ANALYSIS SUMMARY", file=sys.stderr)
    print("="*80, file=sys.stderr)

    print(f"\nTotal unique query genes analyzed: {len(df_genes):,}", file=sys.stderr)

    print(f"\nConservation Score Statistics:", file=sys.stderr)
    print(f"  Mean: {df_genes['conservation_score'].mean():.1f}%", file=sys.stderr)
    print(f"  Median: {df_genes['conservation_score'].median():.1f}%", file=sys.stderr)
    print(f"  Std Dev: {df_genes['conservation_score'].std():.1f}%", file=sys.stderr)

    print(f"\nAgreement Category Breakdown:", file=sys.stderr)
    for cat, count in df_genes['agreement_category'].value_counts().sort_index().items():
        pct = 100 * count / len(df_genes)
        print(f"  {cat:20s}: {count:5,} ({pct:5.1f}%)", file=sys.stderr)

    print(f"\nTranscript Complexity:", file=sys.stderr)
    print(f"  Single-transcript genes: {len(df_genes[df_genes['num_transcripts']==1]):,} "
          f"({100*len(df_genes[df_genes['num_transcripts']==1])/len(df_genes):.1f}%)", file=sys.stderr)
    print(f"  Multi-transcript genes:  {len(df_genes[df_genes['num_transcripts']>1]):,} "
          f"({100*len(df_genes[df_genes['num_transcripts']>1])/len(df_genes):.1f}%)", file=sys.stderr)
    print(f"  Max transcripts per gene: {df_genes['num_transcripts'].max()}", file=sys.stderr)

    print(f"\nLength Differences (gene-level):", file=sys.stderr)
    print(f"  Mean difference: {df_genes['diff_max'].mean():+,.0f} aa", file=sys.stderr)
    print(f"  Median difference: {df_genes['diff_max'].median():+,.0f} aa", file=sys.stderr)
    print(f"  Genes with Query > Ref: {len(df_genes[df_genes['diff_max']>0]):,} "
          f"({100*len(df_genes[df_genes['diff_max']>0])/len(df_genes):.1f}%)", file=sys.stderr)
    print(f"  Genes with Ref > Query: {len(df_genes[df_genes['diff_max']<0]):,} "
          f"({100*len(df_genes[df_genes['diff_max']<0])/len(df_genes):.1f}%)", file=sys.stderr)

    print("="*80 + "\n", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(
        description="Gene-level aggregation and conservation analysis"
    )
    parser.add_argument('input', help="PAVprot output TSV file")
    parser.add_argument('--output-prefix', '-o', default='ipr_gene_analysis',
                       help="Output prefix for files")

    args = parser.parse_args()

    print(f"\nLoading data from: {args.input}", file=sys.stderr)
    df = load_data(args.input)
    print(f"Loaded {len(df)} transcript pairs", file=sys.stderr)

    # Create output directory
    output_path = Path(args.output_prefix)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("\nAggregating to gene level...", file=sys.stderr)
    df_genes = aggregate_by_gene(df)

    print_gene_stats(df_genes)

    print("Generating gene-level plots...", file=sys.stderr)
    plot_gene_level_analysis(df_genes, args.output_prefix)

    print("Creating gene summary tables...", file=sys.stderr)
    create_gene_summary_table(df_genes, args.output_prefix)

    print("\n✓ Gene-level analysis complete!", file=sys.stderr)

if __name__ == '__main__':
    main()
