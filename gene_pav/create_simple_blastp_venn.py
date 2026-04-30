#!/usr/bin/env python3
"""
Simple BLASTP-based Venn diagram for F. oxysporum protein similarities.

Uses only BLASTP coverage and identity thresholds - no scenario filtering.
Focuses solely on visualization.

Usage:
    python create_simple_blastp_venn.py [--min-pident 50] [--min-coverage 70]
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn2_circles
import argparse
from pathlib import Path

# Default parameters
DEFAULT_MIN_PIDENT = 50.0
DEFAULT_MIN_COVERAGE = 70.0
PAVPROT_OUTPUT = "tmp/pavprot_out_20260209_154955/gene_level_enriched_all.tsv"
OUTPUT_DIR = "plots"

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Create simple BLASTP-based Venn diagram'
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

def load_and_filter_data(filepath, min_pident, min_coverage):
    """Load PAVprot data and apply BLASTP filters"""
    print(f"Loading data from: {filepath}")
    df = pd.read_csv(filepath, sep='\t')
    print(f"Loaded {len(df)} total records")

    # Apply BLASTP similarity filters
    filtered = df[
        (df['pident'] >= min_pident) &
        (df['qcovhsp'] >= min_coverage) &
        (df['scovhsp'] >= min_coverage)
    ].copy()

    print(f"After BLASTP filters (≥{min_pident}% identity, ≥{min_coverage}% coverage): {len(filtered)} records")

    return df, filtered

def calculate_venn_sets(df_all, df_similar):
    """Calculate gene sets for Venn diagram"""
    # All genes from PAVprot analysis
    all_old_genes = set(df_all['old_gene'].dropna())
    all_new_genes = set(df_all['new_gene'].dropna())

    # Genes with BLASTP similarity above thresholds
    similar_old_genes = set(df_similar['old_gene'].dropna())
    similar_new_genes = set(df_similar['new_gene'].dropna())

    # Calculate sets for Venn diagram
    old_with_similar = similar_old_genes
    new_with_similar = similar_new_genes
    old_unique = all_old_genes - old_with_similar
    new_unique = all_new_genes - new_with_similar

    # Conservative overlap estimate (genes with similar counterparts)
    overlap = min(len(old_with_similar), len(new_with_similar))

    return {
        'total_old': len(all_old_genes),
        'total_new': len(all_new_genes),
        'old_unique': len(old_unique),
        'new_unique': len(new_unique),
        'overlap': overlap,
        'similar_pairs': len(df_similar)
    }

def create_simple_venn_diagram(stats, min_pident, min_coverage, output_dir):
    """Create simple Venn diagram"""

    plt.figure(figsize=(10, 8))

    # Extract values
    old_unique = stats['old_unique']
    new_unique = stats['new_unique']
    overlap = stats['overlap']

    print(f"\nVenn diagram values:")
    print(f"  Old unique: {old_unique}")
    print(f"  New unique: {new_unique}")
    print(f"  Overlap (similar): {overlap}")

    # Create Venn diagram
    venn = venn2(
        subsets=(old_unique, new_unique, overlap),
        set_labels=(
            f'Old Annotation\n({stats["total_old"]:,} genes)',
            f'New Annotation\n({stats["total_new"]:,} genes)'
        )
    )

    # Customize colors
    if venn.get_patch_by_id('10'):
        venn.get_patch_by_id('10').set_color('#ff9999')  # Old unique
    if venn.get_patch_by_id('01'):
        venn.get_patch_by_id('01').set_color('#99ccff')  # New unique
    if venn.get_patch_by_id('11'):
        venn.get_patch_by_id('11').set_color('#99ff99')  # Similar

    # Add circles
    circles = venn2_circles(
        subsets=(old_unique, new_unique, overlap),
        linewidth=2.0
    )

    if circles[0]:
        circles[0].set_edgecolor('#cc0000')
    if circles[1]:
        circles[1].set_edgecolor('#0000cc')

    plt.title(
        f'Protein Similarities (BLASTP-based)\n'
        f'≥{min_pident}% identity, ≥{min_coverage}% coverage',
        fontsize=14, fontweight='bold'
    )

    # Add summary
    summary_text = f"""
    BLASTP Parameters:
    • Min. Identity: {min_pident}%
    • Min. Coverage: {min_coverage}%
    • Similar pairs: {stats['similar_pairs']:,}
    """

    plt.figtext(0.02, 0.02, summary_text, fontsize=10,
               bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))

    plt.tight_layout()

    # Save plot
    filename = f"simple_blastp_venn_pident{min_pident}_cov{min_coverage}.png"
    output_path = Path(output_dir) / filename
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')

    print(f"\nVenn diagram saved: {output_path}")
    return output_path

def main():
    """Main function"""
    args = parse_arguments()

    print("=== Simple BLASTP Venn Diagram ===")
    print(f"Parameters: {args.min_pident}% identity, {args.min_coverage}% coverage")

    # Load and filter data
    df_all, df_similar = load_and_filter_data(
        args.input_file, args.min_pident, args.min_coverage
    )

    # Calculate gene sets
    stats = calculate_venn_sets(df_all, df_similar)

    # Create Venn diagram
    create_simple_venn_diagram(
        stats, args.min_pident, args.min_coverage, args.output_dir
    )

    print(f"\nDone! Generated simple BLASTP-based Venn diagram.")

if __name__ == "__main__":
    main()