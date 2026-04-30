#!/usr/bin/env python3
"""
Corrected Venn diagram using actual GFF gene counts + BLASTP similarity.

Uses actual gene counts from GFF files, not just PAVprot subset.

Usage:
    python venn_diagram_corrected.py [--min-pident 50] [--min-coverage 70]
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn2_circles
import argparse
from pathlib import Path

# Default parameters and file paths
DEFAULT_MIN_PIDENT = 50.0
DEFAULT_MIN_COVERAGE = 70.0
PAVPROT_OUTPUT = "tmp/pavprot_out_20260209_154955/gene_level_enriched_all.tsv"
OLD_GFF = "/Users/sadik/Documents/projects/FungiDB/foc47/data/plot/FungiDB-68_Fo47.gff"
NEW_GFF = "/Users/sadik/Documents/projects/FungiDB/foc47/data/plot/GCF_013085055.1.gff"
OUTPUT_DIR = "plots"

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Generate corrected Venn diagram with actual GFF gene counts')
    parser.add_argument('--min-pident', type=float, default=DEFAULT_MIN_PIDENT,
                       help=f'Minimum percent identity threshold (default: {DEFAULT_MIN_PIDENT})')
    parser.add_argument('--min-coverage', type=float, default=DEFAULT_MIN_COVERAGE,
                       help=f'Minimum coverage threshold (default: {DEFAULT_MIN_COVERAGE})')
    parser.add_argument('--input-file', type=str, default=PAVPROT_OUTPUT,
                       help=f'PAVprot output file (default: {PAVPROT_OUTPUT})')
    parser.add_argument('--old-gff', type=str, default=OLD_GFF,
                       help=f'Old annotation GFF file (default: {OLD_GFF})')
    parser.add_argument('--new-gff', type=str, default=NEW_GFF,
                       help=f'New annotation GFF file (default: {NEW_GFF})')
    parser.add_argument('--output-dir', type=str, default=OUTPUT_DIR,
                       help=f'Output directory (default: {OUTPUT_DIR})')
    return parser.parse_args()

def parse_gff_simple(gff_file):
    """Simple GFF parser to extract gene IDs from protein-coding genes"""
    print(f"Parsing GFF file: {gff_file}")

    genes = set()
    try:
        with open(gff_file, 'r') as f:
            for line_num, line in enumerate(f):
                if line.startswith('#'):
                    continue

                parts = line.strip().split('\t')
                if len(parts) < 9:
                    continue

                feature_type = parts[2]
                attributes = parts[8]

                # Handle different annotation formats
                if feature_type == 'protein_coding_gene':
                    # Old annotation format (FungiDB)
                    if 'ID=' in attributes:
                        for attr in attributes.split(';'):
                            if attr.startswith('ID='):
                                gene_id = attr.replace('ID=', '').strip()
                                genes.add(gene_id)
                                break

                elif feature_type == 'gene':
                    # New annotation format (NCBI RefSeq)
                    is_protein_coding = True
                    gene_id = None

                    for attr in attributes.split(';'):
                        if attr.startswith('ID='):
                            gene_id = attr.replace('ID=', '').strip()
                        elif attr.startswith('gbkey='):
                            gbkey = attr.replace('gbkey=', '').strip()
                            if gbkey != 'Gene':
                                is_protein_coding = False
                        elif 'pseudogene' in attr:
                            is_protein_coding = False

                    if gene_id and is_protein_coding:
                        genes.add(gene_id)

                if line_num % 10000 == 0 and line_num > 0:
                    print(f"  Processed {line_num:,} lines...")

    except Exception as e:
        print(f"Error parsing GFF: {e}")
        return set()

    print(f"  Found {len(genes):,} unique protein-coding genes")
    return genes

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

    filtered_count = len(df_filtered)

    print(f"  Initial records: {initial_count:,}")
    print(f"  After filters: {filtered_count:,}")
    print(f"  Filtered out: {initial_count - filtered_count:,}")

    return df_filtered

def analyze_with_gff_counts(old_genes_gff, new_genes_gff, df_filtered, min_pident, min_coverage):
    """Analyze using actual GFF gene counts + BLASTP similarity"""

    print(f"\n=== Using Actual GFF Gene Counts ===")
    print(f"GFF gene counts:")
    print(f"  Old annotation: {len(old_genes_gff):,} genes")
    print(f"  New annotation: {len(new_genes_gff):,} genes")

    # Get genes with BLASTP similarity from PAVprot
    old_genes_with_similarity = set(df_filtered['old_gene'].dropna())
    new_genes_with_similarity = set(df_filtered['new_gene'].dropna())

    print(f"BLASTP similarity matches:")
    print(f"  Old genes with matches: {len(old_genes_with_similarity):,}")
    print(f"  New genes with matches: {len(new_genes_with_similarity):,}")
    print(f"  Similar pairs: {len(df_filtered):,}")

    # Calculate sets for Venn diagram using ACTUAL GFF totals
    total_old_genes = len(old_genes_gff)
    total_new_genes = len(new_genes_gff)

    # Genes without BLASTP matches (using actual totals minus those with matches)
    old_unique = total_old_genes - len(old_genes_with_similarity)
    new_unique = total_new_genes - len(new_genes_with_similarity)

    # Overlap: conservative estimate of genes with similar counterparts
    overlap = min(len(old_genes_with_similarity), len(new_genes_with_similarity))

    stats = {
        'total_old_genes': total_old_genes,
        'total_new_genes': total_new_genes,
        'old_with_similarity': len(old_genes_with_similarity),
        'new_with_similarity': len(new_genes_with_similarity),
        'old_unique': old_unique,
        'new_unique': new_unique,
        'overlap': overlap,
        'similar_pairs': len(df_filtered),
        'parameters': {
            'min_pident': min_pident,
            'min_coverage': min_coverage
        }
    }

    return stats

def create_corrected_venn_diagram(stats, output_dir):
    """Create corrected Venn diagram using actual GFF gene counts"""

    # Extract values for Venn diagram
    old_unique = stats['old_unique']
    new_unique = stats['new_unique']
    overlap = stats['overlap']

    print(f"\n=== Corrected Venn Diagram Statistics ===")
    print(f"  Total old genes (GFF): {stats['total_old_genes']:,}")
    print(f"  Total new genes (GFF): {stats['total_new_genes']:,}")
    print(f"  Old unique (no similar match): {old_unique:,}")
    print(f"  New unique (no similar match): {new_unique:,}")
    print(f"  Genes with similar counterparts: {overlap:,}")
    print(f"  Similar protein pairs found: {stats['similar_pairs']:,}")

    # Create plot
    plt.figure(figsize=(10, 8))

    # Main Venn diagram
    venn = venn2(
        subsets=(old_unique, new_unique, overlap),
        set_labels=(f'Old Annotation\n({stats["total_old_genes"]:,} genes)',
                   f'New Annotation\n({stats["total_new_genes"]:,} genes)')
    )

    # Customize colors
    if venn.get_patch_by_id('10'):
        venn.get_patch_by_id('10').set_color('#ff9999')  # Old unique
    if venn.get_patch_by_id('01'):
        venn.get_patch_by_id('01').set_color('#99ccff')  # New unique
    if venn.get_patch_by_id('11'):
        venn.get_patch_by_id('11').set_color('#99ff99')  # Similar

    # Increase font size of the numbers inside circles
    number_font_size = 16  # Adjust this value to make numbers bigger/smaller
    if venn.get_label_by_id('10'):
        venn.get_label_by_id('10').set_fontsize(number_font_size)
    if venn.get_label_by_id('01'):
        venn.get_label_by_id('01').set_fontsize(number_font_size)
    if venn.get_label_by_id('11'):
        venn.get_label_by_id('11').set_fontsize(number_font_size)

    # Increase font size of set labels (annotation names below circles)
    label_font_size = 14  # Adjust this value for set labels
    # Access set labels through the subplot text objects
    for text in plt.gca().texts:
        if 'Annotation' in text.get_text():
            text.set_fontsize(label_font_size)

    # Add circles that align with patches
    circles = venn2_circles(subsets=(old_unique, new_unique, overlap),
                           linewidth=3.0)

    # Apply colors to match the patches
    if circles[0]:  # Old annotation circle
        circles[0].set_edgecolor('#cc0000')  # Dark red
    if circles[1]:  # New annotation circle
        circles[1].set_edgecolor('#0000cc')  # Dark blue

    plt.title(f'Similarity between Old and New Annotations of Foc47 Protein \n(≥{stats["parameters"]["min_pident"]}% identity, ≥{stats["parameters"]["min_coverage"]}% coverage)',
             fontsize=14, fontweight='bold')

    # Add summary text
    # old_coverage = (stats['old_with_similarity'] / stats['total_old_genes']) * 100
    # new_coverage = (stats['new_with_similarity'] / stats['total_new_genes']) * 100

    # summary_text = f"""
    # Similarity Parameters:
    # • Min. Identity: {stats['parameters']['min_pident']}%
    # • Min. Coverage: {stats['parameters']['min_coverage']}%

    # Results (using actual GFF counts):
    # • Old: {old_coverage:.1f}% genes with similarity
    # • New: {new_coverage:.1f}% genes with similarity
    # • Similar pairs found: {stats['similar_pairs']:,}
    # """

    # plt.figtext(0.02, 0.02,
                # bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))

    plt.tight_layout()

    # Save plot
    filename = f"corrected_venn_pident{stats['parameters']['min_pident']}_cov{stats['parameters']['min_coverage']}.png"
    output_path = Path(output_dir) / filename
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')

    print(f"Venn diagram saved to: {output_path}")
    return output_path

def main():
    """Main function using actual GFF gene counts"""
    args = parse_arguments()

    print("=== VENN DIAGRAM (Actual GFF Gene Counts) ===")
    print(f"Parameters: {args.min_pident}% identity, {args.min_coverage}% coverage")

    # Parse GFF files to get actual gene counts
    old_genes = parse_gff_simple(args.old_gff)
    new_genes = parse_gff_simple(args.new_gff)

    if len(old_genes) == 0 or len(new_genes) == 0:
        print("ERROR: Could not parse genes from GFF files")
        return

    # Load and filter PAVprot BLASTP data
    df = load_pavprot_data(args.input_file)
    df_filtered = apply_similarity_filters(df, args.min_pident, args.min_coverage)

    # Analyze using actual GFF counts + BLASTP similarity
    stats = analyze_with_gff_counts(old_genes, new_genes, df_filtered,
                                   args.min_pident, args.min_coverage)

    # Create corrected Venn diagram
    create_corrected_venn_diagram(stats, args.output_dir)

    print(f"\n=== CORRECTED ANALYSIS COMPLETE ===")

if __name__ == "__main__":
    main()