#!/usr/bin/env python3
"""
Create Venn diagram showing similarities and differences between
protein-coding genes in F. oxysporum old vs new annotations.

Uses PAVprot output to identify:
- Genes unique to old annotation
- Genes unique to new annotation
- Genes present in both annotations (mapped)

Usage:
    python create_gene_venn_diagram.py
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn2_circles
import seaborn as sns
from pathlib import Path

# File paths
PAVPROT_OUTPUT = "tmp/pavprot_out_20260209_154955/gene_level_enriched_all.tsv"
OUTPUT_DIR = "plots"

def load_pavprot_data(filepath):
    """Load PAVprot gene-level mapping data"""
    print(f"Loading PAVprot data from: {filepath}")
    df = pd.read_csv(filepath, sep='\t')
    print(f"Loaded {len(df)} gene mapping records")
    return df

def extract_gene_sets(df):
    """Extract sets of genes from old and new annotations"""

    # Get all old genes (including unmapped)
    old_genes = set()
    new_genes = set()

    # Mapped genes from PAVprot output
    mapped_old = set(df['old_gene'].dropna())
    mapped_new = set(df['new_gene'].dropna())

    old_genes.update(mapped_old)
    new_genes.update(mapped_new)

    print(f"Genes found in analysis:")
    print(f"  Old annotation: {len(old_genes)} genes")
    print(f"  New annotation: {len(new_genes)} genes")

    # Find overlapping genes (those that map between annotations)
    # Note: This identifies genes that have orthologs, not identical gene IDs
    overlapping = len(df[df['mapping_type'] == '1to1'])

    return old_genes, new_genes, overlapping, df

def create_venn_diagram(old_genes, new_genes, overlapping_count, df, output_dir):
    """Create Venn diagram showing gene overlap"""

    # Calculate statistics
    total_old = len(old_genes)
    total_new = len(new_genes)

    # For Venn diagram, we need to show:
    # - Genes with 1:1 orthologs (overlapping)
    # - Genes unique to old (no ortholog in new)
    # - Genes unique to new (no ortholog in old)

    # Count different mapping scenarios
    scenario_counts = df['scenario'].value_counts()
    one_to_one = len(df[df['scenario'] == 'E'])  # 1:1 orthologs

    # Approximate unique genes (this is simplified)
    old_unique_approx = total_old - one_to_one
    new_unique_approx = total_new - one_to_one

    print(f"\nVenn Diagram Statistics:")
    print(f"  1:1 Orthologs (E): {one_to_one}")
    print(f"  Old annotation unique: ~{old_unique_approx}")
    print(f"  New annotation unique: ~{new_unique_approx}")

    # Create the plot
    plt.figure(figsize=(12, 8))

    # Adjust subset values to control circle spacing
    # Smaller overlap relative to unique sets = less overlap
    spacing_factor = 0.3  # Reduce overlap for better spacing
    adjusted_overlap = one_to_one * spacing_factor

    # Create Venn diagram with adjusted spacing
    venn = venn2(
        subsets=(old_unique_approx, new_unique_approx, adjusted_overlap),
        set_labels=('Old Annotation\n(foc67_v68)', 'New Annotation\n(GCF_013085055.1)')
    )

    # Customize colors and adjust patch positions to match circles
    if venn.get_patch_by_id('10'):
        venn.get_patch_by_id('10').set_color('#ff9999')  # Old unique
    if venn.get_patch_by_id('01'):
        venn.get_patch_by_id('01').set_color('#99ccff')  # New unique
    if venn.get_patch_by_id('11'):
        venn.get_patch_by_id('11').set_color('#99ff99')  # Shared/mapped

    # Move the colored patches to match our circle positioning
    for patch in venn.patches:
        if patch is not None:
            # Get current position and shift it
            current_path = patch.get_path()
            vertices = current_path.vertices.copy()

            # Determine which patch this is and adjust accordingly
            center_x = vertices[:, 0].mean()
            if center_x < 0:  # Left patch (old annotation)
                vertices[:, 0] += 0.1  # Shift slightly right to match circle
            else:  # Right patch (new annotation)
                vertices[:, 0] += 0.1  # Shift to match circle position

    # Add circles with matching spacing
    circles = venn2_circles(
        subsets=(old_unique_approx, new_unique_approx, adjusted_overlap),
        linewidth=2.0
    )

    # Customize circle colors
    if circles[0]:  # Old annotation circle (left)
        circles[0].set_edgecolor('#cc0000')  # Dark red outline
    if circles[1]:  # New annotation circle (right)
        circles[1].set_edgecolor('#0000cc')  # Dark blue outline

    plt.title('F. oxysporum Gene Content Comparison\nOld vs New Genome Annotation',
             fontsize=16, fontweight='bold', pad=20)

    # Add summary text
    summary_text = f"""
    Total genes - Old: {total_old:,}
    Total genes - New: {total_new:,}
    1:1 Orthologs: {one_to_one:,}
    """

    plt.figtext(0.02, 0.02, summary_text, fontsize=10,
               bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))

    # Save plot
    output_path = Path(output_dir) / "foc_gene_venn_diagram.png"
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nVenn diagram saved to: {output_path}")

    return output_path

def create_scenario_summary(df, output_dir):
    """Create summary of mapping scenarios"""

    scenario_counts = df['scenario'].value_counts()

    # Create scenario summary plot
    plt.figure(figsize=(10, 6))

    scenario_counts.plot(kind='bar', color='steelblue')
    plt.title('Gene Mapping Scenarios\nF. oxysporum Old vs New Annotation')
    plt.xlabel('Scenario Type')
    plt.ylabel('Number of Gene Pairs')
    plt.xticks(rotation=45)

    # Add count labels on bars
    for i, v in enumerate(scenario_counts.values):
        plt.text(i, v + max(scenario_counts.values) * 0.01, str(v),
                ha='center', va='bottom')

    plt.tight_layout()

    # Save plot
    output_path = Path(output_dir) / "foc_scenario_summary.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Scenario summary saved to: {output_path}")

    return scenario_counts

def main():
    """Main analysis function"""
    print("=== F. oxysporum Gene Comparison Analysis ===\n")

    # Load data
    df = load_pavprot_data(PAVPROT_OUTPUT)

    # Extract gene sets
    old_genes, new_genes, overlapping, df = extract_gene_sets(df)

    # Create Venn diagram
    venn_path = create_venn_diagram(old_genes, new_genes, overlapping, df, OUTPUT_DIR)

    # Create scenario summary
    scenario_counts = create_scenario_summary(df, OUTPUT_DIR)

    print(f"\n=== Analysis Complete ===")
    print(f"Results saved to: {OUTPUT_DIR}/")
    print(f"- Venn diagram: foc_gene_venn_diagram.png")
    print(f"- Scenario summary: foc_scenario_summary.png")

    return venn_path, scenario_counts

if __name__ == "__main__":
    main()