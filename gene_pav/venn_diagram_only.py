#!/usr/bin/env python3
"""
Extract ONLY the Venn diagram generation from create_blastp_venn_diagram.py

Usage:
    python venn_diagram_only.py [--min-pident 50] [--min-coverage 70]
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
    parser = argparse.ArgumentParser(description='Generate ONLY Venn diagram from BLASTP data')
    parser.add_argument('--min-pident', type=float, default=DEFAULT_MIN_PIDENT,
                       help=f'Minimum percent identity threshold (default: {DEFAULT_MIN_PIDENT})')
    parser.add_argument('--min-coverage', type=float, default=DEFAULT_MIN_COVERAGE,
                       help=f'Minimum coverage threshold (default: {DEFAULT_MIN_COVERAGE})')
    parser.add_argument('--input-file', type=str, default=PAVPROT_OUTPUT,
                       help=f'PAVprot output file (default: {PAVPROT_OUTPUT})')
    parser.add_argument('--output-dir', type=str, default=OUTPUT_DIR,
                       help=f'Output directory (default: {OUTPUT_DIR})')
    return parser.parse_args()

def load_pavprot_data(filepath):
    """Load PAVprot data with DIAMOND BLASTP results"""
    print(f"Loading PAVprot data from: {filepath}")
    df = pd.read_csv(filepath, sep='\t')
    print(f"Loaded {len(df)} gene mapping records")
    return df

def apply_similarity_filters(df, min_pident, min_coverage):
    """Apply BLASTP similarity filters"""
    print(f"Applying similarity filters:")
    print(f"  Minimum percent identity: {min_pident}%")
    print(f"  Minimum coverage: {min_coverage}%")

    initial_count = len(df)

    # Filter by percent identity and coverage
    df_filtered = df[
        (df['pident'] >= min_pident) &
        (df['qcovhsp'] >= min_coverage) &
        (df['scovhsp'] >= min_coverage)
    ].copy()

    after_coverage = len(df_filtered)

    print(f"  Initial records: {initial_count:,}")
    print(f"  After filters: {after_coverage:,}")
    print(f"  Filtered out: {initial_count - after_coverage:,}")

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
    old_with_similar = similar_old_proteins
    new_with_similar = similar_new_proteins
    old_unique = all_old_proteins - old_with_similar
    new_unique = all_new_proteins - new_with_similar

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

def create_venn_diagram_only(stats, output_dir):
    """Create ONLY the Venn diagram - extracted from create_blastp_venn_diagram.py"""

    # Extract values for Venn diagram
    old_unique = stats['old_unique']
    new_unique = stats['new_unique']
    overlap = min(stats['old_with_similar'], stats['new_with_similar'])  # Conservative overlap estimate

    print(f"\nVenn Diagram Statistics:")
    print(f"  Old unique (no similar match): {old_unique}")
    print(f"  New unique (no similar match): {new_unique}")
    print(f"  Proteins with similar counterparts: {overlap}")
    print(f"  Similar protein pairs found: {stats['similar_pairs']}")

    # Create SINGLE plot (not subplots)
    plt.figure(figsize=(10, 8))

    # Main Venn diagram
    venn = venn2(
        subsets=(old_unique, new_unique, overlap),
        set_labels=(f'Old Annotation\n(foc67_v68)', f'New Annotation\n(GCF_013085055.1)')
    )

    # Customize colors
    if venn.get_patch_by_id('10'):
        venn.get_patch_by_id('10').set_color('#ff9999')  # Old unique
    if venn.get_patch_by_id('01'):
        venn.get_patch_by_id('01').set_color('#99ccff')  # New unique
    if venn.get_patch_by_id('11'):
        venn.get_patch_by_id('11').set_color('#99ff99')  # Similar

    # Add circles that match the colored patches exactly
    circles = venn2_circles(subsets=(old_unique, new_unique, overlap),
                           linewidth=3.0)  # Thick outlines

    # Apply colors to match the patches (no radius modification to keep alignment)
    if circles[0]:  # Old annotation circle
        circles[0].set_edgecolor('#cc0000')  # Dark red
    if circles[1]:  # New annotation circle
        circles[1].set_edgecolor('#0000cc')  # Dark blue

    print(f"  Circles aligned with colored patches")

    plt.title(f'Protein Similarity between Old and New Annotations\n(≥{stats["parameters"]["min_pident"]}% identity, ≥{stats["parameters"]["min_coverage"]}% coverage)',
             fontsize=14, fontweight='bold')

    # Add summary text
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

    plt.tight_layout()

    # Save plot
    filename = f"venn_only_pident{stats['parameters']['min_pident']}_cov{stats['parameters']['min_coverage']}.png"
    output_path = Path(output_dir) / filename
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nVenn diagram saved to: {output_path}")

    return output_path

def main():
    """Main analysis function - ONLY Venn diagram generation"""
    args = parse_arguments()

    print("=== ONLY VENN DIAGRAM GENERATION ===")
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

    # Create ONLY Venn diagram
    venn_path = create_venn_diagram_only(stats, args.output_dir)

    print(f"\n=== DONE ===")
    print(f"Generated: {venn_path.name}")

if __name__ == "__main__":
    main()