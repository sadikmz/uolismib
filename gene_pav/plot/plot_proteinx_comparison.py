#!/usr/bin/env python3
"""
Task 5 Proteinx

Extracted from: task_5_proteinx
Moved to plot module for production use.
"""

from pathlib import Path
from typing import Optional
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def mapping_type_to_colon(mapping_type: str) -> str:
    """Convert mapping_type to colon notation (e.g., '1to1' -> '1:1')."""
    return mapping_type.replace('to', ':')


def generate_proteinx_comparison(gene_df: pd.DataFrame = None, transcript_df: pd.DataFrame = None, output_dir: Path = None, config: dict = None, figure_dpi: int = 150) -> Optional[Path]:
    """
    Generate: proteinx_comparison.png

    Compares ProteinX pLDDT scores between ref and query.
    Creates stacked bar plot comparing pLDDT distribution.

    Returns:
        Path to output file, or None if skipped
    """
    print("\n[Task 5] ProteinX Plot")

    ref_file = Path(config["proteinx_ref"])
    qry_file = Path(config["proteinx_qry"])

    if not check_file_exists(ref_file, "ProteinX ref"):
        return None
    if not check_file_exists(qry_file, "ProteinX qry"):
        return None

    # Load ProteinX data
    print(f"  Loading ProteinX ref: {ref_file}")
    ref_df = pd.read_csv(ref_file, sep='\t')
    print(f"    Loaded {len(ref_df)} entries")

    print(f"  Loading ProteinX qry: {qry_file}")
    qry_df = pd.read_csv(qry_file, sep='\t')
    print(f"    Loaded {len(qry_df)} entries")

    # Extract pLDDT statistics
    ref_plddt = ref_df['residue_plddt_mean'].dropna()
    qry_plddt = qry_df['residue_plddt_mean'].dropna()

    # Define pLDDT bins (AlphaFold confidence levels)
    bins = [0, 50, 70, 90, 100]
    labels = ['Very Low\n(<50)', 'Low\n(50-70)', 'Confident\n(70-90)', 'Very High\n(>90)']
    colors = ['#FF6B6B', '#FFE66D', '#4ECDC4', '#45B7D1']

    # Bin the data
    ref_binned = pd.cut(ref_plddt, bins=bins, labels=labels)
    qry_binned = pd.cut(qry_plddt, bins=bins, labels=labels)

    ref_counts = ref_binned.value_counts().reindex(labels, fill_value=0)
    qry_counts = qry_binned.value_counts().reindex(labels, fill_value=0)

    # Calculate percentages
    ref_pct = ref_counts / ref_counts.sum() * 100
    qry_pct = qry_counts / qry_counts.sum() * 100

    # Create stacked bar plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Plot 1: Side-by-side bar chart
    x = np.arange(len(labels))
    width = 0.35

    ax1 = axes[0]
    bars1 = ax1.bar(x - width/2, ref_pct, width, label='New (NCBI)', color='steelblue')
    bars2 = ax1.bar(x + width/2, qry_pct, width, label='Old (FungiDB)', color='coral')

    ax1.set_xlabel('pLDDT Confidence Level')
    ax1.set_ylabel('Percentage of Proteins (%)')
    ax1.set_title('ProteinX pLDDT Distribution Comparison')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.legend()
    ax1.set_ylim(0, max(ref_pct.max(), qry_pct.max()) * 1.1)

    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.annotate(f'{height:.1f}%', xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)
    for bar in bars2:
        height = bar.get_height()
        ax1.annotate(f'{height:.1f}%', xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)

    # Plot 2: Histogram overlay
    ax2 = axes[1]
    ax2.hist(ref_plddt, bins=50, alpha=0.5, label=f'New (NCBI) (n={len(ref_plddt)})', color='steelblue', density=True)
    ax2.hist(qry_plddt, bins=50, alpha=0.5, label=f'Old (FungiDB) (n={len(qry_plddt)})', color='coral', density=True)
    ax2.axvline(x=50, color='red', linestyle='--', alpha=0.5, label='Low confidence threshold')
    ax2.axvline(x=70, color='orange', linestyle='--', alpha=0.5, label='Confident threshold')
    ax2.axvline(x=90, color='green', linestyle='--', alpha=0.5, label='Very high threshold')
    ax2.set_xlabel('Mean pLDDT Score')
    ax2.set_ylabel('Density')
    ax2.set_title('pLDDT Score Distribution')
    ax2.legend(fontsize=8)

    plt.tight_layout()

    output_path = output_dir / "proteinx_comparison.png"
    fig.savefig(output_path, dpi=figure_dpi, bbox_inches='tight')
    plt.close(fig)

    # Print summary stats
    print(f"  New (NCBI) pLDDT: mean={ref_plddt.mean():.1f}, median={ref_plddt.median():.1f}")
    print(f"  Old (FungiDB) pLDDT: mean={qry_plddt.mean():.1f}, median={qry_plddt.median():.1f}")
    print(f"  [DONE] Saved: {output_path}")

    # ===== Additional plots: pLDDT by mapping_type and class_type =====
    # Requires merging with PAVprot transcript-level data
    if transcript_df is not None:
        print("  Generating pLDDT distribution by mapping/class type...")

        # Clean gene_name to get transcript ID (remove _sample_N suffix)
        ref_df['transcript_id'] = ref_df['gene_name'].str.replace(r'_sample_\d+$', '', regex=True)
        qry_df['transcript_id'] = qry_df['gene_name'].str.replace(r'_sample_\d+$', '', regex=True)

        # Detect column naming scheme
        if 'query_transcript' in transcript_df.columns:
            # NEW NAMING: ref_transcript, query_transcript, ref_gene, query_gene
            ref_trans_col = 'ref_transcript'
            qry_trans_col = 'query_transcript'
            ref_gene_col = 'ref_gene'
            qry_gene_col = 'query_gene'
        else:
            # OLD NAMING: new_transcript, old_transcript, new_gene, old_gene
            ref_trans_col = 'new_transcript'
            qry_trans_col = 'old_transcript'
            ref_gene_col = 'new_gene'
            qry_gene_col = 'old_gene'

        # Get PAVprot data with mapping and class info
        pavprot_df = transcript_df[[ref_trans_col, qry_trans_col,
                                         'class_type_gene', 'class_type_transcript']].copy()

        # Add mapping_type from gene_df if available
        if gene_df is not None and 'mapping_type' in gene_df.columns:
            gene_mapping = gene_df[[ref_gene_col, qry_gene_col, 'mapping_type']].drop_duplicates()
            # Get gene columns from transcript data
            if ref_gene_col in transcript_df.columns and qry_gene_col in transcript_df.columns:
                pavprot_df[ref_gene_col] = transcript_df[ref_gene_col]
                pavprot_df[qry_gene_col] = transcript_df[qry_gene_col]
                pavprot_df = pavprot_df.merge(gene_mapping, on=[ref_gene_col, qry_gene_col], how='left')

        # Merge ref pLDDT with PAVprot data
        # ProteinX ref = new/NCBI annotation = ref_transcript in PAVprot
        ref_merged = ref_df[['transcript_id', 'residue_plddt_mean']].merge(
            pavprot_df.rename(columns={ref_trans_col: 'transcript_id'}),
            on='transcript_id', how='inner'
        )

        # Merge query pLDDT with PAVprot data
        # ProteinX qry = old/FungiDB annotation = query_transcript in PAVprot
        qry_merged = qry_df[['transcript_id', 'residue_plddt_mean']].merge(
            pavprot_df.rename(columns={qry_trans_col: 'transcript_id'}),
            on='transcript_id', how='inner'
        )

        print(f"    Matched ref: {len(ref_merged)}, query: {len(qry_merged)}")

        # Define mapping types and colors (used in multiple plots)
        mapping_types = ['1to1', '1to2N', '1to2N+', 'Nto1', 'complex']
        mapping_colors = {
            '1to1': '#1f77b4', '1to2N': '#ff7f0e', '1to2N+': '#2ca02c',
            'Nto1': '#d62728', 'complex': '#9467bd'
        }

        # ===== Plot: pLDDT by Mapping Type =====
        if 'mapping_type' in ref_merged.columns and len(ref_merged) > 0:
            fig_mt, axes_mt = plt.subplots(1, 2, figsize=(14, 5))

            # Reference by mapping type
            ax_ref = axes_mt[0]
            for mtype in mapping_types:
                data = ref_merged[ref_merged['mapping_type'] == mtype]['residue_plddt_mean'].dropna()
                if len(data) > 0:
                    ax_ref.hist(data, bins=30, alpha=0.5, density=True,
                               label=f'{mapping_type_to_colon(mtype)} (n={len(data)})',
                               color=mapping_colors.get(mtype, 'gray'))
            ax_ref.set_xlabel('Mean pLDDT Score')
            ax_ref.set_ylabel('Density')
            ax_ref.set_title('New (NCBI) pLDDT by Mapping Type')
            ax_ref.legend(fontsize=8)

            # Query by mapping type
            ax_qry = axes_mt[1]
            for mtype in mapping_types:
                data = qry_merged[qry_merged['mapping_type'] == mtype]['residue_plddt_mean'].dropna()
                if len(data) > 0:
                    ax_qry.hist(data, bins=30, alpha=0.5, density=True,
                               label=f'{mapping_type_to_colon(mtype)} (n={len(data)})',
                               color=mapping_colors.get(mtype, 'gray'))
            ax_qry.set_xlabel('Mean pLDDT Score')
            ax_qry.set_ylabel('Density')
            ax_qry.set_title('Old (FungiDB) pLDDT by Mapping Type')
            ax_qry.legend(fontsize=8)

            plt.tight_layout()
            mt_path = output_dir / "proteinx_by_mapping_type.png"
            fig_mt.savefig(mt_path, dpi=figure_dpi, bbox_inches='tight')
            plt.close(fig_mt)
            print(f"  [DONE] Saved: {mt_path}")

        # ===== Plot: pLDDT by Class Type =====
        if 'class_type_gene' in ref_merged.columns and len(ref_merged) > 0:
            fig_ct, axes_ct = plt.subplots(1, 2, figsize=(14, 5))

            # Get top class types
            top_classes = ref_merged['class_type_gene'].value_counts().head(8).index.tolist()
            class_colors = plt.cm.tab10(np.linspace(0, 1, len(top_classes)))

            # Reference by class type
            ax_ref = axes_ct[0]
            for i, ctype in enumerate(top_classes):
                data = ref_merged[ref_merged['class_type_gene'] == ctype]['residue_plddt_mean'].dropna()
                if len(data) > 0:
                    ax_ref.hist(data, bins=30, alpha=0.5, density=True,
                               label=f'{ctype} (n={len(data)})', color=class_colors[i])
            ax_ref.set_xlabel('Mean pLDDT Score')
            ax_ref.set_ylabel('Density')
            ax_ref.set_title('New (NCBI) pLDDT by Class Type')
            ax_ref.legend(fontsize=7, loc='upper left')

            # Query by class type
            ax_qry = axes_ct[1]
            for i, ctype in enumerate(top_classes):
                data = qry_merged[qry_merged['class_type_gene'] == ctype]['residue_plddt_mean'].dropna()
                if len(data) > 0:
                    ax_qry.hist(data, bins=30, alpha=0.5, density=True,
                               label=f'{ctype} (n={len(data)})', color=class_colors[i])
            ax_qry.set_xlabel('Mean pLDDT Score')
            ax_qry.set_ylabel('Density')
            ax_qry.set_title('Old (FungiDB) pLDDT by Class Type')
            ax_qry.legend(fontsize=7, loc='upper left')

            plt.tight_layout()
            ct_path = output_dir / "proteinx_by_class_type.png"
            fig_ct.savefig(ct_path, dpi=figure_dpi, bbox_inches='tight')
            plt.close(fig_ct)
            print(f"  [DONE] Saved: {ct_path}")

        # ===== Plot: Combined - pLDDT by Mapping Type AND Class Type =====
        if 'mapping_type' in ref_merged.columns and 'class_type_gene' in ref_merged.columns:
            # Create a faceted plot: rows=mapping_type, cols=ref/query
            mapping_types_present = [m for m in mapping_types if m in ref_merged['mapping_type'].values]

            if len(mapping_types_present) > 0:
                fig_comb, axes_comb = plt.subplots(len(mapping_types_present), 2,
                                                   figsize=(14, 3 * len(mapping_types_present)))

                # Ensure axes is 2D
                if len(mapping_types_present) == 1:
                    axes_comb = axes_comb.reshape(1, -1)

                top_classes_short = ref_merged['class_type_gene'].value_counts().head(5).index.tolist()

                for row_idx, mtype in enumerate(mapping_types_present):
                    # Reference
                    ax_ref = axes_comb[row_idx, 0]
                    ref_subset = ref_merged[ref_merged['mapping_type'] == mtype]
                    for i, ctype in enumerate(top_classes_short):
                        data = ref_subset[ref_subset['class_type_gene'] == ctype]['residue_plddt_mean'].dropna()
                        if len(data) > 0:
                            ax_ref.hist(data, bins=25, alpha=0.5, density=True,
                                       label=ctype, color=plt.cm.tab10(i/10))
                    ax_ref.set_ylabel('Density')
                    ax_ref.set_title(f'New (NCBI) - {mapping_type_to_colon(mtype)}')
                    if row_idx == 0:
                        ax_ref.legend(fontsize=6, loc='upper left')
                    if row_idx == len(mapping_types_present) - 1:
                        ax_ref.set_xlabel('Mean pLDDT Score')

                    # Query
                    ax_qry = axes_comb[row_idx, 1]
                    qry_subset = qry_merged[qry_merged['mapping_type'] == mtype]
                    for i, ctype in enumerate(top_classes_short):
                        data = qry_subset[qry_subset['class_type_gene'] == ctype]['residue_plddt_mean'].dropna()
                        if len(data) > 0:
                            ax_qry.hist(data, bins=25, alpha=0.5, density=True,
                                       label=ctype, color=plt.cm.tab10(i/10))
                    ax_qry.set_title(f'Old (FungiDB) - {mapping_type_to_colon(mtype)}')
                    if row_idx == len(mapping_types_present) - 1:
                        ax_qry.set_xlabel('Mean pLDDT Score')

                plt.tight_layout()
                comb_path = output_dir / "proteinx_by_mapping_and_class.png"
                fig_comb.savefig(comb_path, dpi=figure_dpi, bbox_inches='tight')
                plt.close(fig_comb)
                print(f"  [DONE] Saved: {comb_path}")

    return output_path

# =========================================================================
# TASK 6: Psauron Data Integration
# =========================================================================


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        gene_file = sys.argv[1]
        out_dir = sys.argv[2] if len(sys.argv) > 2 else Path.cwd()
        gene_df = pd.read_csv(gene_file, sep='\t')
        print(f"Generating plot from {gene_file}")
        print(f"Output to {out_dir}")
