#!/usr/bin/env python3
"""
Create DIAMOND BLASTP-based Venn diagram showing protein similarities
between F. oxysporum old vs new annotations.

Uses DIAMOND BLASTP output from PAVprot with configurable similarity thresholds:
- Minimum percent identity
- Minimum coverage (query and subject)

Usage:
    python create_blastp_venn_diagram.py [--min-pident 50] [--min-coverage 70]
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn2_circles
import seaborn as sns
import argparse
from pathlib import Path
import numpy as np

# Default parameters
DEFAULT_MIN_PIDENT = 50.0    # Minimum percent identity
DEFAULT_MIN_COVERAGE = 70.0  # Minimum coverage (both query and subject)
PAVPROT_OUTPUT = "tmp/pavprot_out_20260209_154955/gene_level_enriched_all.tsv"
OUTPUT_DIR = "plots"

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Create BLASTP-based Venn diagram for F. oxysporum proteins'
    )
    parser.add_argument('--min-pident', type=float, default=DEFAULT_MIN_PIDENT,
                       help=f'Minimum percent identity threshold (default: {DEFAULT_MIN_PIDENT})')
    parser.add_argument('--min-coverage', type=float, default=DEFAULT_MIN_COVERAGE,
                       help=f'Minimum coverage threshold (default: {DEFAULT_MIN_COVERAGE})')
    parser.add_argument('--output-dir', type=str, default=OUTPUT_DIR,
                       help=f'Output directory (default: {OUTPUT_DIR})')
    parser.add_argument('--input-file', type=str, default=PAVPROT_OUTPUT,
                       help=f'PAVprot output file (default: {PAVPROT_OUTPUT})')

    return parser.parse_args()

def load_pavprot_data(filepath):
    """Load PAVprot data with DIAMOND BLASTP results"""
    print(f"Loading PAVprot data from: {filepath}")
    df = pd.read_csv(filepath, sep='\t')
    print(f"Loaded {len(df)} gene mapping records")

    # Show available BLASTP columns
    blastp_cols = ['pident', 'qcovhsp', 'scovhsp', 'is_bbh', 'bbh_avg_pident', 'bbh_avg_coverage']
    available_cols = [col for col in blastp_cols if col in df.columns]
    print(f"Available BLASTP columns: {available_cols}")

    return df

def apply_similarity_filters(df, min_pident, min_coverage):
    """Apply BLASTP similarity filters"""

    print(f"\nApplying similarity filters:")
    print(f"  Minimum percent identity: {min_pident}%")
    print(f"  Minimum coverage: {min_coverage}%")

    initial_count = len(df)

    # Filter by percent identity
    df_filtered = df[df['pident'] >= min_pident].copy()
    after_pident = len(df_filtered)

    # Filter by coverage (both query and subject)
    df_filtered = df_filtered[
        (df_filtered['qcovhsp'] >= min_coverage) &
        (df_filtered['scovhsp'] >= min_coverage)
    ].copy()
    after_coverage = len(df_filtered)

    print(f"  Initial records: {initial_count:,}")
    print(f"  After pident filter: {after_pident:,}")
    print(f"  After coverage filter: {after_coverage:,}")
    print(f"  Filtered out: {initial_count - after_coverage:,} ({((initial_count - after_coverage) / initial_count * 100):.1f}%)")

    return df_filtered

def analyze_protein_sets(df, df_filtered, min_pident, min_coverage):
    """Analyze protein sets with and without similarity filters"""

    # All proteins (regardless of similarity)
    all_old_proteins = set(df['old_gene'].dropna())
    all_new_proteins = set(df['new_gene'].dropna())

    # Similar proteins (meeting thresholds)
    similar_old_proteins = set(df_filtered['old_gene'].dropna())
    similar_new_proteins = set(df_filtered['new_gene'].dropna())

    # Calculate sets for Venn diagram
    # Old proteins with similar matches in new
    old_with_similar = similar_old_proteins
    # New proteins with similar matches in old
    new_with_similar = similar_new_proteins
    # Proteins unique to old (no similar match in new)
    old_unique = all_old_proteins - old_with_similar
    # Proteins unique to new (no similar match in old)
    new_unique = all_new_proteins - new_with_similar

    # For Venn diagram: we want to show overlap of similar proteins
    # The overlap represents proteins that have similar counterparts in both annotations
    similar_pairs = len(df_filtered)

    stats = {
        'total_old': len(all_old_proteins),
        'total_new': len(all_new_proteins),
        'old_with_similar': len(old_with_similar),
        'new_with_similar': len(new_with_similar),
        'old_unique': len(old_unique),
        'new_unique': len(new_unique),
        'similar_pairs': similar_pairs,
        'parameters': {
            'min_pident': min_pident,
            'min_coverage': min_coverage
        }
    }

    return stats

def create_blastp_venn_diagram(stats, output_dir):
    """Create Venn diagram based on BLASTP similarity"""

    # Extract values for Venn diagram
    old_unique = stats['old_unique']
    new_unique = stats['new_unique']
    overlap = min(stats['old_with_similar'], stats['new_with_similar'])  # Conservative overlap estimate

    print(f"\nVenn Diagram Statistics:")
    print(f"  Old unique (no similar match): {old_unique}")
    print(f"  New unique (no similar match): {new_unique}")
    print(f"  Proteins with similar counterparts: {overlap}")
    print(f"  Similar protein pairs found: {stats['similar_pairs']}")

    # Create the plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # Main Venn diagram
    venn = venn2(
        subsets=(old_unique, new_unique, overlap),
        set_labels=(f'Old Annotation\n(foc67_v68)', f'New Annotation\n(GCF_013085055.1)'),
        ax=ax1
    )

    # Customize colors
    if venn.get_patch_by_id('10'):
        venn.get_patch_by_id('10').set_color('#ff9999')  # Old unique
    if venn.get_patch_by_id('01'):
        venn.get_patch_by_id('01').set_color('#99ccff')  # New unique
    if venn.get_patch_by_id('11'):
        venn.get_patch_by_id('11').set_color('#99ff99')  # Similar

    # Add circles with Method 3: Proportional to Data
    # Calculate sizes based on actual protein counts
    old_ratio = stats['total_old'] / max(stats['total_old'], stats['total_new'])
    new_ratio = stats['total_new'] / max(stats['total_old'], stats['total_new'])

    # Scale to desired size range
    base_size = 0.4  # Adjust this to control overall circle size
    old_radius = base_size * old_ratio
    new_radius = base_size * new_ratio

    circles = venn2_circles(subsets=(old_unique, new_unique, overlap),
                           linewidth=3.0,  # Thick outlines
                           ax=ax1)

    # Apply proportional sizes and colors
    if circles[0]:  # Old annotation circle
        circles[0].set_radius(old_radius)
        circles[0].set_edgecolor('#cc0000')  # Dark red
    if circles[1]:  # New annotation circle
        circles[1].set_radius(new_radius)
        circles[1].set_edgecolor('#0000cc')  # Dark blue

    print(f"  Proportional circle sizes - Old: {old_radius:.3f} (ratio: {old_ratio:.3f}), New: {new_radius:.3f} (ratio: {new_ratio:.3f})")

    ax1.set_title(f'Protein Similarity between Old and New Annotations\n(≥{stats["parameters"]["min_pident"]}% identity, ≥{stats["parameters"]["min_coverage"]}% coverage)',
                 fontsize=14, fontweight='bold')

    # Summary statistics plot
    categories = ['Total\nProteins', 'With Similar\nCounterpart', 'Unique\n(No Match)']
    old_values = [stats['total_old'], stats['old_with_similar'], stats['old_unique']]
    new_values = [stats['total_new'], stats['new_with_similar'], stats['new_unique']]

    # x = np.arange(len(categories))
    # width = 0.35

    # bars1 = ax2.bar(x - width/2, old_values, width, label='Old Annotation', color='#ff9999')
    # bars2 = ax2.bar(x + width/2, new_values, width, label='New Annotation', color='#99ccff')

    # ax2.set_xlabel('Protein Categories')
    # ax2.set_ylabel('Number of Proteins')
    # ax2.set_title('Protein Count Comparison')
    # ax2.set_xticks(x)
    # ax2.set_xticklabels(categories)
    # ax2.legend()

    # # Add value labels on bars
    # for bars in [bars1, bars2]:
    #     for bar in bars:
    #         height = bar.get_height()
    #         ax2.annotate(f'{height:,}',
    #                     xy=(bar.get_x() + bar.get_width() / 2, height),
    #                     xytext=(0, 3),  # 3 points vertical offset
    #                     textcoords="offset points",
    #                     ha='center', va='bottom', fontsize=9)

    # Add summary text with CORRECT statistics
    summary_text = f"""
    Similarity Parameters:
    • Min. Identity: {stats['parameters']['min_pident']}%
    • Min. Coverage: {stats['parameters']['min_coverage']}%

    Results:
    • Similar pairs found: {stats['similar_pairs']:,}
    • Old proteins with matches: {stats['old_with_similar']:,}
    • New proteins with matches: {stats['new_with_similar']:,}
    • Old unique (no match): {stats['old_unique']:,}
    • New unique (no match): {stats['new_unique']:,}
    """

    plt.figtext(0.02, 0.02, summary_text, fontsize=10,
               bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))

    # plt.suptitle('F. oxysporum Protein Similarity Analysis\nBased on DIAMOND BLASTP Results',
    #             fontsize=16, fontweight='bold', y=0.98)

    plt.tight_layout()

    # Save plot
    filename = f"foc_blastp_venn_pident{stats['parameters']['min_pident']}_cov{stats['parameters']['min_coverage']}.png"
    output_path = Path(output_dir) / filename
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nBLASTP Venn diagram saved to: {output_path}")

    return output_path

# def create_similarity_distribution_plot(df, df_filtered, min_pident, min_coverage, output_dir):
#     """Create plots showing similarity distribution"""

#     fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

#     # 1. Percent identity distribution
#     ax1.hist(df['pident'].dropna(), bins=50, alpha=0.7, color='steelblue', edgecolor='black')
#     ax1.axvline(min_pident, color='red', linestyle='--', linewidth=2, label=f'Threshold ({min_pident}%)')
#     ax1.set_xlabel('Percent Identity (%)')
#     ax1.set_ylabel('Frequency')
#     ax1.set_title('Distribution of Percent Identity')
#     ax1.legend()
#     ax1.grid(True, alpha=0.3)

#     # 2. Coverage distribution
#     ax2.hist(df['qcovhsp'].dropna(), bins=50, alpha=0.7, color='green', edgecolor='black', label='Query Coverage')
#     ax2.hist(df['scovhsp'].dropna(), bins=50, alpha=0.5, color='orange', edgecolor='black', label='Subject Coverage')
#     ax2.axvline(min_coverage, color='red', linestyle='--', linewidth=2, label=f'Threshold ({min_coverage}%)')
#     ax2.set_xlabel('Coverage (%)')
#     ax2.set_ylabel('Frequency')
#     ax2.set_title('Distribution of Query/Subject Coverage')
#     ax2.legend()
#     ax2.grid(True, alpha=0.3)

#     # 3. Identity vs Coverage scatter
#     scatter = ax3.scatter(df['qcovhsp'], df['pident'], alpha=0.6, c=df['scovhsp'],
#                          cmap='viridis', s=10)
#     ax3.axhline(min_pident, color='red', linestyle='--', alpha=0.7)
#     ax3.axvline(min_coverage, color='red', linestyle='--', alpha=0.7)
#     ax3.set_xlabel('Query Coverage (%)')
#     ax3.set_ylabel('Percent Identity (%)')
#     ax3.set_title('Identity vs Coverage Relationship')
#     plt.colorbar(scatter, ax=ax3, label='Subject Coverage (%)')
#     ax3.grid(True, alpha=0.3)

#     # 4. Bidirectional Best Hit analysis
#     bbh_counts = df['is_bbh'].value_counts().sort_index()

#     # Create bar chart instead of pie chart (more robust)
#     categories = []
#     values = []
#     colors = []

#     for val in [0.0, 1.0]:  # Check for both BBH categories
#         if val in bbh_counts.index:
#             categories.append('BBH' if val == 1.0 else 'Not BBH')
#             values.append(bbh_counts[val])
#             colors.append('lightblue' if val == 1.0 else 'lightcoral')

#     bars = ax4.bar(categories, values, color=colors)
#     ax4.set_title('Bidirectional Best Hits (BBH)')
#     ax4.set_ylabel('Number of Protein Pairs')

    # Add value labels on bars
    # for bar, value in zip(bars, values):
    #     ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01,
    #             f'{value:,}', ha='center', va='bottom')

    # plt.suptitle('DIAMOND BLASTP Similarity Analysis Details', fontsize=16, fontweight='bold')
    # plt.tight_layout()

    # Save plot
    # filename = f"foc_blastp_similarity_distribution_pident{min_pident}_cov{min_coverage}.png"
    # output_path = Path(output_dir) / filename
    # plt.savefig(output_path, dpi=300, bbox_inches='tight')
    # print(f"Similarity distribution plot saved to: {output_path}")

    return output_path

def main():
    """Main analysis function"""
    args = parse_arguments()

    print("=== F. oxysporum BLASTP-Based Protein Similarity Analysis ===\n")
    print(f"Parameters:")
    print(f"  Minimum percent identity: {args.min_pident}%")
    print(f"  Minimum coverage: {args.min_coverage}%")
    print(f"  Input file: {args.input_file}")
    print(f"  Output directory: {args.output_dir}")

    # Load data
    df = load_pavprot_data(args.input_file)

    # Apply similarity filters
    df_filtered = apply_similarity_filters(df, args.min_pident, args.min_coverage)

    # Analyze protein sets
    stats = analyze_protein_sets(df, df_filtered, args.min_pident, args.min_coverage)

    # Create Venn diagram
    venn_path = create_blastp_venn_diagram(stats, args.output_dir)

    # Create similarity distribution plots
    # dist_path = create_similarity_distribution_plot(df, df_filtered, args.min_pident,
    #                                                args.min_coverage, args.output_dir)

    print(f"\n=== Analysis Complete ===")
    print(f"Generated files:")
    # print(f"  • Venn diagram: {venn_path.name}")
    # print(f"  • Distribution plots: {dist_path.name}")

    # Print summary statistics with CONSISTENT SCOPE
    print(f"\n=== Summary Statistics (BLASTP Analysis Scope) ===")
    print(f"  Total protein pairs analyzed: {len(df):,}")
    print(f"  Similar pairs (≥{args.min_pident}% ID, ≥{args.min_coverage}% cov): {stats['similar_pairs']:,}")
    print(f"\n  BLASTP-analyzable proteins:")
    print(f"    Old annotation: {stats['total_old']:,} proteins")
    print(f"    New annotation: {stats['total_new']:,} proteins")
    print(f"\n  Proteins with BLASTP similarity matches:")
    print(f"    Old proteins with matches: {stats['old_with_similar']:,} ({(stats['old_with_similar']/stats['total_old']*100):.1f}%)")
    print(f"    New proteins with matches: {stats['new_with_similar']:,} ({(stats['new_with_similar']/stats['total_new']*100):.1f}%)")
    print(f"\n  Proteins without BLASTP matches:")
    print(f"    Old unique: {stats['old_unique']:,}")
    print(f"    New unique: {stats['new_unique']:,}")

if __name__ == "__main__":
    main()