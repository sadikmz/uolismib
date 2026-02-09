#!/usr/bin/env python3
"""
PAVprot Master Pipeline Script
==============================

This script orchestrates the complete PAVprot analysis workflow.
Designed for initial automated runs, with easy manual resumption.

USAGE:
------
    # Run everything:
    python run_pipeline.py --all

    # Run specific tasks:
    python run_pipeline.py --task plots
    python run_pipeline.py --task psauron
    python run_pipeline.py --task proteinx
    python run_pipeline.py --task fungidb

    # List available tasks:
    python run_pipeline.py --list

MANUAL RESUMPTION:
------------------
Each task is a standalone function. To run manually in Python:

    from run_pipeline import PipelineRunner
    runner = PipelineRunner(config)
    runner.task_1_ipr_scatter()      # Run specific task
    runner.task_4_scenario_barplot()  # Run another task

CONFIGURATION:
--------------
Edit the CONFIG dictionary below to set your input/output paths.

Author: PAVprot Pipeline
Date: 2026-01-09
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# =============================================================================
# CONFIGURATION - Edit these paths for your environment
# =============================================================================

CONFIG = {
    # Base directories
    "gene_pav_dir": Path(__file__).parent.parent,  # Updated to point to gene_pav/ directory
    "output_dir": Path(__file__).parent.parent / "plot_out" / "refactored",  # Output to refactored plots

    # Dataset input directory (can be overridden via constructor)
    "dataset_dir": Path(__file__).parent.parent / "pavprot_out_20260209_152204",  # Updated to latest output

    # PAVprot output files (will auto-detect from dataset_dir)
    "transcript_level_tsv": None,  # Will auto-detect from dataset_dir
    "gene_level_tsv": None,        # Will auto-detect from dataset_dir

    # External data files (optional - tasks will skip if not found)
    "psauron_ref": Path("/Users/sadik/Documents/projects/FungiDB/foc47/output/psauron/ref_all.csv"),
    "psauron_qry": Path("/Users/sadik/Documents/projects/FungiDB/foc47/output/psauron/qry_all.csv"),
    "proteinx_ref": Path("/Users/sadik/Documents/projects/FungiDB/foc47/output/proteinx/GCF_013085055.1_proteinx.tsv"),
    "proteinx_qry": Path("/Users/sadik/Documents/projects/FungiDB/foc47/output/proteinx/Foc47_013085055.1_proteinx.tsv"),
    "phytopathogen_list": Path("/Users/sadik/Documents/projects/data/disease_research_supported.csv"),
    "fungidb_gene_stats": Path("/Users/sadik/Documents/projects/data/fungidb_v68_gene_stats.tsv"),

    # Plot settings
    "figure_dpi": 150,
    "figure_format": "png",
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def find_latest_output(dataset_dir: Path) -> tuple:
    """
    Auto-detect PAVprot output files from a dataset directory.
    Prefers enriched files (*_with_psauron.tsv) if available.

    Args:
        dataset_dir: Path to dataset directory (e.g., pavprotOut/)

    Returns:
        Tuple of (transcript_level_path, gene_level_path)
    """
    transcript_file = None
    gene_file = None

    if dataset_dir.exists():
        # Look for enriched gene_level file first (with psauron scores)
        for f in dataset_dir.glob("*gene_level_with_psauron.tsv"):
            gene_file = f
            break

        # Fallback to raw gene_level file if enriched not found
        if not gene_file:
            for f in dataset_dir.glob("*_gene_level.tsv"):
                gene_file = f
                break

        # Look for enriched transcript-level file first
        for f in sorted(dataset_dir.glob("*transcript_level_with_psauron.tsv"), reverse=True):
            transcript_file = f
            break

        # Fallback to main gffcomp file without "_gene_level" in name
        if not transcript_file:
            for f in sorted(dataset_dir.glob("*gffcomp*mapping*.tsv"), reverse=True):
                if ("_gene_level" not in f.name and
                    "domain_distribution" not in f.name and
                    "ipr_length" not in f.name and
                    "multiple" not in f.name):
                    transcript_file = f
                    break

    return transcript_file, gene_file


def check_file_exists(filepath: Path, task_name: str) -> bool:
    """Check if file exists and print status."""
    if filepath is None or not filepath.exists():
        print(f"  [SKIP] {task_name}: Input file not found - {filepath}")
        return False
    return True


def mapping_type_to_colon(mapping_type: str) -> str:
    """
    Convert mapping_type from 'to' notation to ':' notation for legend.

    Examples:
        '1to1' -> '1:1'
        '1to2N' -> '1:2N'
        '1to2N+' -> '1:2N+'
        'Nto1' -> 'N:1'
    """
    return mapping_type.replace('to', ':')


# =============================================================================
# PIPELINE RUNNER CLASS
# =============================================================================

class PipelineRunner:
    """
    Master pipeline runner with modular task functions.

    Each task_* method is independent and can be called manually.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.gene_pav_dir = Path(config["gene_pav_dir"])
        self.output_dir = Path(config["output_dir"])
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Use specified dataset directory (or default from config)
        self.dataset_dir = Path(config.get("dataset_dir", config["gene_pav_dir"] / "pavprotOut"))

        # Auto-detect PAVprot output if not specified
        if config["transcript_level_tsv"] is None or config["gene_level_tsv"] is None:
            t_file, g_file = find_latest_output(self.dataset_dir)
            self.transcript_tsv = t_file or config["transcript_level_tsv"]
            self.gene_tsv = g_file or config["gene_level_tsv"]
        else:
            self.transcript_tsv = Path(config["transcript_level_tsv"])
            self.gene_tsv = Path(config["gene_level_tsv"])

        # Store loaded data for reuse
        self._transcript_df = None
        self._gene_df = None

        # Track failed plots for reporting
        self.failed_plots = []

    @property
    def transcript_df(self) -> pd.DataFrame:
        """Lazy-load transcript-level data."""
        if self._transcript_df is None and self.transcript_tsv and self.transcript_tsv.exists():
            print(f"  Loading transcript data: {self.transcript_tsv}")
            self._transcript_df = pd.read_csv(self.transcript_tsv, sep='\t')
        return self._transcript_df

    @property
    def gene_df(self) -> pd.DataFrame:
        """Lazy-load gene-level data."""
        if self._gene_df is None and self.gene_tsv and self.gene_tsv.exists():
            print(f"  Loading gene-level data: {self.gene_tsv}")
            self._gene_df = pd.read_csv(self.gene_tsv, sep='\t')
        return self._gene_df

    # =========================================================================
    # TASK 1: IPR Domain Length Scatter (by class_type)
    # =========================================================================
    def task_1_ipr_scatter(self) -> Optional[Path]:
        """
        Generate: test_summary_by_class_type.png

        Scatter plot of gene pair IPR domain lengths colored by class_type_gene.

        Returns:
            Path to output file, or None if skipped
        """
        print("\n[Task 1] IPR Domain Length Scatter Plot")

        if self.gene_df is None:
            print("  [SKIP] Gene-level data not available")
            return None

        df = self.gene_df.copy()

        # Check required columns
        x_col = 'ref_total_ipr_domain_length'
        y_col = 'query_total_ipr_domain_length'

        if x_col not in df.columns or y_col not in df.columns:
            print(f"  [SKIP] Required columns not found: {x_col}, {y_col}")
            return None

        # Filter out missing values
        plot_df = df[[x_col, y_col, 'class_type_gene']].dropna()

        # Create plot
        fig, ax = plt.subplots(figsize=(10, 8))

        # Color by class_type_gene
        class_types = plot_df['class_type_gene'].unique()
        colors = plt.cm.tab10(np.linspace(0, 1, len(class_types)))

        for ctype, color in zip(class_types, colors):
            mask = plot_df['class_type_gene'] == ctype
            ax.scatter(
                plot_df.loc[mask, x_col],
                plot_df.loc[mask, y_col],
                c=[color],
                label=ctype,
                alpha=0.6,
                s=20
            )

        ax.set_xlabel('Old predicted genes total IPR domain length (aa)')
        ax.set_ylabel('New predicted genes total IPR domain length (aa)')
        ax.set_title('Gene pair total IPR domain length')
        ax.legend(title='Class Type', bbox_to_anchor=(1.02, 1), loc='upper left')

        # Add diagonal line
        max_val = max(plot_df[x_col].max(), plot_df[y_col].max())
        ax.plot([0, max_val], [0, max_val], 'k--', alpha=0.3, label='y=x')

        plt.tight_layout()

        output_path = self.output_dir / "test_summary_by_class_type.png"
        fig.savefig(output_path, dpi=self.config["figure_dpi"], bbox_inches='tight')
        plt.close(fig)

        print(f"  [DONE] Saved: {output_path}")
        return output_path

    # =========================================================================
    # TASK 2: Log-Log Scale Plot with Shapes
    # =========================================================================
    def task_2_loglog_scale(self) -> Optional[Path]:
        """
        Generate: test_summary_loglog_scale.png

        Log-log scale scatter with different shapes by mapping_type.
        Legend uses ':' notation (1:1, 1:2N, etc.)

        Returns:
            Path to output file, or None if skipped
        """
        print("\n[Task 2] Log-Log Scale Plot with Mapping Type Shapes")

        if self.gene_df is None:
            print("  [SKIP] Gene-level data not available")
            return None

        df = self.gene_df.copy()

        x_col = 'ref_total_ipr_domain_length'
        y_col = 'query_total_ipr_domain_length'

        if x_col not in df.columns or y_col not in df.columns:
            print(f"  [SKIP] Required columns not found: {x_col}, {y_col}")
            return None

        # Filter and prepare data (add small value for log scale)
        plot_df = df[[x_col, y_col, 'mapping_type']].dropna()
        plot_df = plot_df[(plot_df[x_col] > 0) & (plot_df[y_col] > 0)]

        # Define marker shapes for mapping types
        markers = {
            '1to1': 'o',      # circle
            '1to2N': 's',     # square
            '1to2N+': '^',    # triangle up
            'Nto1': 'D',      # diamond
            'complex': 'X',   # X marker
        }

        fig, ax = plt.subplots(figsize=(10, 8))

        for mtype in plot_df['mapping_type'].unique():
            mask = plot_df['mapping_type'] == mtype
            marker = markers.get(mtype, 'o')
            label = mapping_type_to_colon(mtype)  # Convert to ':' notation

            ax.scatter(
                plot_df.loc[mask, x_col],
                plot_df.loc[mask, y_col],
                marker=marker,
                label=label,
                alpha=0.6,
                s=30
            )

        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_xlabel('Old predicted genes total IPR domain length (aa)')
        ax.set_ylabel('New predicted genes total IPR domain length (aa)')
        ax.set_title('Gene pair total IPR domain length (Log-Log scale plot)')
        ax.legend(title='Mapping Type', bbox_to_anchor=(1.02, 1), loc='upper left')

        # Add diagonal line
        min_val = min(plot_df[x_col].min(), plot_df[y_col].min())
        max_val = max(plot_df[x_col].max(), plot_df[y_col].max())
        ax.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.3)

        plt.tight_layout()

        output_path = self.output_dir / "test_summary_loglog_scale.png"
        fig.savefig(output_path, dpi=self.config["figure_dpi"], bbox_inches='tight')
        plt.close(fig)

        print(f"  [DONE] Saved: {output_path}")
        return output_path

    # =========================================================================
    # TASK 2b: Log-Log Scale Plot with Class Type Shapes
    # =========================================================================
    def task_2b_loglog_class_shapes(self) -> Optional[Path]:
        """
        Generate: test_summary_loglog_scale_class_shapes.png

        Log-log scale scatter with:
        - Shapes = class_type_gene
        - Colors = mapping_type

        Returns:
            Path to output file, or None if skipped
        """
        print("\n[Task 2b] Log-Log Scale Plot with Class Type Shapes")

        if self.gene_df is None:
            print("  [SKIP] Gene-level data not available")
            return None

        df = self.gene_df.copy()

        x_col = 'ref_total_ipr_domain_length'
        y_col = 'query_total_ipr_domain_length'

        if x_col not in df.columns or y_col not in df.columns:
            print(f"  [SKIP] Required columns not found: {x_col}, {y_col}")
            return None

        # Filter and prepare data
        required_cols = [x_col, y_col, 'mapping_type', 'class_type_gene']
        plot_df = df[required_cols].dropna()
        plot_df = plot_df[(plot_df[x_col] > 0) & (plot_df[y_col] > 0)]

        # Colors for mapping types (same as original test_summary_loglog_scale.png - tab10)
        mapping_colors = {
            '1to1': '#1f77b4',      # blue (tab10[0])
            '1to2N': '#ff7f0e',     # orange (tab10[1])
            '1to2N+': '#2ca02c',    # green (tab10[2])
            'Nto1': '#d62728',      # red (tab10[3])
            'complex': '#9467bd',   # purple (tab10[4])
        }

        # Shapes for class types (most common ones)
        class_markers = {
            'a': 'o',           # circle - exact match
            'ackmnj': 's',      # square
            'ackmnje': '^',     # triangle up
            'ckmnj': 'D',       # diamond
            'e': 'v',           # triangle down
            'iy': 'p',          # pentagon
            'o': 'h',           # hexagon
            'pru': '*',         # star
            'sx': 'X',          # X marker
        }

        fig, ax = plt.subplots(figsize=(12, 8))

        # Plot by mapping_type (color) and class_type_gene (shape)
        for mtype in ['1to1', '1to2N', '1to2N+', 'Nto1', 'complex']:
            m_mask = plot_df['mapping_type'] == mtype
            if not m_mask.any():
                continue

            color = mapping_colors.get(mtype, 'gray')

            for ctype in plot_df.loc[m_mask, 'class_type_gene'].unique():
                if pd.isna(ctype):
                    continue
                c_mask = m_mask & (plot_df['class_type_gene'] == ctype)
                marker = class_markers.get(ctype, 'o')
                # Larger size for 'pru' class type
                size = 80 if ctype == 'pru' else 30

                ax.scatter(
                    plot_df.loc[c_mask, x_col],
                    plot_df.loc[c_mask, y_col],
                    marker=marker,
                    c=color,
                    alpha=0.6,
                    s=size
                )

        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_xlabel('Old predicted genes total IPR domain length (aa)')
        ax.set_ylabel('New predicted genes total IPR domain length (aa)')
        ax.set_title('Gene pair total IPR domain length (Log-Log scale, Class Type Shapes)')

        # Add diagonal line
        min_val = min(plot_df[x_col].min(), plot_df[y_col].min())
        max_val = max(plot_df[x_col].max(), plot_df[y_col].max())
        ax.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.3)

        # Create separate legends
        from matplotlib.lines import Line2D

        # Legend 1: Colors (Mapping Type)
        color_handles = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor=color,
                   markersize=10, label=mapping_type_to_colon(mtype))
            for mtype, color in mapping_colors.items()
            if mtype in plot_df['mapping_type'].values
        ]

        # Legend 2: Shapes (Class Type) - only include those present in data
        shape_handles = [
            Line2D([0], [0], marker=marker, color='w', markerfacecolor='gray',
                   markersize=10, label=ctype)
            for ctype, marker in class_markers.items()
            if ctype in plot_df['class_type_gene'].values
        ]

        # Add first legend (colors = mapping type)
        legend1 = ax.legend(handles=color_handles, title='Mapping Type',
                           bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
        ax.add_artist(legend1)

        # Add second legend (shapes = class type)
        legend2 = ax.legend(handles=shape_handles, title='Class Type',
                           bbox_to_anchor=(1.02, 0.55), loc='upper left', fontsize=8)

        plt.tight_layout()

        output_path = self.output_dir / "test_summary_loglog_scale_class_shapes.png"
        fig.savefig(output_path, dpi=self.config["figure_dpi"], bbox_inches='tight')
        plt.close(fig)

        print(f"  [DONE] Saved: {output_path}")
        return output_path

    # =========================================================================
    # TASK 3: Quadrants Plot (Presence/Absence Patterns)
    # =========================================================================
    def task_3_quadrants(self) -> Optional[Path]:
        """
        Generate: test_summary_quadrants_gene_level.png

        Quadrant plot showing presence/absence patterns.
        Legend: Ref only -> New only, Query only -> Old only
        Separate legends for colors (quadrant) and shapes (mapping_type).

        Returns:
            Path to output file, or None if skipped
        """
        print("\n[Task 3] Quadrant Plot (Presence/Absence Patterns)")

        if self.gene_df is None:
            print("  [SKIP] Gene-level data not available")
            return None

        df = self.gene_df.copy()

        x_col = 'ref_total_ipr_domain_length'
        y_col = 'query_total_ipr_domain_length'

        if x_col not in df.columns or y_col not in df.columns:
            print(f"  [SKIP] Required columns not found: {x_col}, {y_col}")
            return None

        # Classify into quadrants
        # Fill NaN with 0 for classification
        df[x_col] = df[x_col].fillna(0)
        df[y_col] = df[y_col].fillna(0)

        def classify_quadrant(row):
            ref_has = row[x_col] > 0
            qry_has = row[y_col] > 0
            if ref_has and qry_has:
                return 'Both'
            elif ref_has and not qry_has:
                return 'New only'  # Renamed from 'Ref only'
            elif not ref_has and qry_has:
                return 'Old only'  # Renamed from 'Query only'
            else:
                return 'Neither'

        df['quadrant'] = df.apply(classify_quadrant, axis=1)

        # Define marker shapes for mapping types
        markers = {
            '1to1': 'o',
            '1to2N': 's',
            '1to2N+': '^',
            'Nto1': 'D',
            'complex': 'X',
        }

        # Colors for quadrants
        quadrant_colors = {
            'Both': 'green',
            'New only': 'blue',
            'Old only': 'orange',
            'Neither': 'red',
        }

        fig, ax = plt.subplots(figsize=(12, 8))

        # Plot by quadrant and mapping_type
        for quadrant in ['Both', 'New only', 'Old only', 'Neither']:
            q_mask = df['quadrant'] == quadrant
            if not q_mask.any():
                continue

            for mtype in df.loc[q_mask, 'mapping_type'].unique():
                if pd.isna(mtype):
                    continue
                m_mask = q_mask & (df['mapping_type'] == mtype)
                marker = markers.get(mtype, 'o')

                ax.scatter(
                    df.loc[m_mask, x_col],
                    df.loc[m_mask, y_col],
                    marker=marker,
                    c=quadrant_colors[quadrant],
                    alpha=0.6,
                    s=30
                )

        ax.set_xlabel('Old predicted genes total IPR domain length (aa)')
        ax.set_ylabel('New predicted genes total IPR domain length (aa)')
        ax.set_title('Gene-level IPR Domains Presence / Absence Patterns')

        # Create separate legends for colors and shapes
        from matplotlib.lines import Line2D

        # Legend 1: Colors (Quadrant/Presence-Absence)
        color_handles = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor=color,
                   markersize=10, label=quadrant)
            for quadrant, color in quadrant_colors.items()
            if quadrant in df['quadrant'].values
        ]

        # Legend 2: Shapes (Mapping Type)
        shape_handles = [
            Line2D([0], [0], marker=marker, color='w', markerfacecolor='gray',
                   markersize=10, label=mapping_type_to_colon(mtype))
            for mtype, marker in markers.items()
            if mtype in df['mapping_type'].values
        ]

        # Add first legend (colors) - positioned at top right
        legend1 = ax.legend(handles=color_handles, title='IPR Domain Pattern',
                           bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
        ax.add_artist(legend1)

        # Add second legend (shapes) - positioned below first
        legend2 = ax.legend(handles=shape_handles, title='Mapping Type',
                           bbox_to_anchor=(1.02, 0.6), loc='upper left', fontsize=9)

        plt.tight_layout()

        output_path = self.output_dir / "test_summary_quadrants_gene_level.png"
        fig.savefig(output_path, dpi=self.config["figure_dpi"], bbox_inches='tight')
        plt.close(fig)

        print(f"  [DONE] Saved: {output_path}")
        return output_path

    # =========================================================================
    # TASK 3b: Quadrants Plot (Swapped - Colors=MappingType, Shapes=Pattern)
    # =========================================================================
    def task_3b_quadrants_swapped(self) -> Optional[Path]:
        """
        Generate: test_summary_quadrants_gene_level_swapped.png

        Same as task_3 but with swapped visual encoding:
        - Colors = Mapping Type (1:1, 1:2N, etc.)
        - Shapes = IPR Domain Pattern (Both, New only, Old only, Neither)

        Returns:
            Path to output file, or None if skipped
        """
        print("\n[Task 3b] Quadrant Plot (Swapped: Colors=MappingType, Shapes=Pattern)")

        if self.gene_df is None:
            print("  [SKIP] Gene-level data not available")
            return None

        df = self.gene_df.copy()

        x_col = 'ref_total_ipr_domain_length'
        y_col = 'query_total_ipr_domain_length'

        if x_col not in df.columns or y_col not in df.columns:
            print(f"  [SKIP] Required columns not found: {x_col}, {y_col}")
            return None

        # Classify into quadrants
        df[x_col] = df[x_col].fillna(0)
        df[y_col] = df[y_col].fillna(0)

        def classify_quadrant(row):
            ref_has = row[x_col] > 0
            qry_has = row[y_col] > 0
            if ref_has and qry_has:
                return 'Both'
            elif ref_has and not qry_has:
                return 'New only'
            elif not ref_has and qry_has:
                return 'Old only'
            else:
                return 'Neither'

        df['quadrant'] = df.apply(classify_quadrant, axis=1)

        # SWAPPED: Shapes for quadrants (IPR Domain Pattern)
        quadrant_markers = {
            'Both': 'o',       # circle
            'New only': 's',   # square
            'Old only': '^',   # triangle
            'Neither': 'X',    # X marker
        }

        # SWAPPED: Colors for mapping types
        mapping_colors = {
            '1to1': 'green',
            '1to2N': 'blue',
            '1to2N+': 'purple',
            'Nto1': 'orange',
            'complex': 'red',
        }

        fig, ax = plt.subplots(figsize=(12, 8))

        # Plot by mapping_type and quadrant (swapped order)
        for mtype in ['1to1', '1to2N', '1to2N+', 'Nto1', 'complex']:
            m_mask = df['mapping_type'] == mtype
            if not m_mask.any():
                continue

            for quadrant in df.loc[m_mask, 'quadrant'].unique():
                if pd.isna(quadrant):
                    continue
                q_mask = m_mask & (df['quadrant'] == quadrant)
                marker = quadrant_markers.get(quadrant, 'o')
                color = mapping_colors.get(mtype, 'gray')

                ax.scatter(
                    df.loc[q_mask, x_col],
                    df.loc[q_mask, y_col],
                    marker=marker,
                    c=color,
                    alpha=0.6,
                    s=30
                )

        ax.set_xlabel('Old predicted genes total IPR domain length (aa)')
        ax.set_ylabel('New predicted genes total IPR domain length (aa)')
        ax.set_title('Gene-level IPR Domains Presence / Absence Patterns (Swapped Encoding)')

        # Create separate legends
        from matplotlib.lines import Line2D

        # Legend 1: Colors (Mapping Type)
        color_handles = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor=color,
                   markersize=10, label=mapping_type_to_colon(mtype))
            for mtype, color in mapping_colors.items()
            if mtype in df['mapping_type'].values
        ]

        # Legend 2: Shapes (IPR Domain Pattern)
        shape_handles = [
            Line2D([0], [0], marker=marker, color='w', markerfacecolor='gray',
                   markersize=10, label=quadrant)
            for quadrant, marker in quadrant_markers.items()
            if quadrant in df['quadrant'].values
        ]

        # Add first legend (colors = mapping type) - positioned at top right
        legend1 = ax.legend(handles=color_handles, title='Mapping Type',
                           bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
        ax.add_artist(legend1)

        # Add second legend (shapes = IPR pattern) - positioned below first
        legend2 = ax.legend(handles=shape_handles, title='IPR Domain Pattern',
                           bbox_to_anchor=(1.02, 0.55), loc='upper left', fontsize=9)

        plt.tight_layout()

        output_path = self.output_dir / "test_summary_quadrants_gene_level_swapped.png"
        fig.savefig(output_path, dpi=self.config["figure_dpi"], bbox_inches='tight')
        plt.close(fig)

        print(f"  [DONE] Saved: {output_path}")
        return output_path

    # =========================================================================
    # TASK 4: Mapping Scenario Bar Plot
    # =========================================================================
    def task_4_scenario_barplot(self) -> Optional[Path]:
        """
        Generate: scenario_barplot.png (New_plot_1)

        Horizontal stacked bar plot of gene pairs by mapping scenario.
        Color partitioned by class_type_gene.
        Also generates non-stacked version.

        Returns:
            Path to output file, or None if skipped
        """
        print("\n[Task 4] Mapping Scenario Bar Plot")

        if self.gene_df is None:
            print("  [SKIP] Gene-level data not available")
            return None

        df = self.gene_df.copy()

        if 'scenario' not in df.columns:
            print("  [SKIP] 'scenario' column not found")
            return None

        # Count gene pairs by scenario and class_type_gene
        counts = df.groupby(['scenario', 'class_type_gene']).size().unstack(fill_value=0)

        # Reorder scenarios
        scenario_order = ['E', 'A', 'J', 'B', 'CDI']
        counts = counts.reindex([s for s in scenario_order if s in counts.index])

        # Map scenario letters to 1:N notation for display
        scenario_to_notation = {
            'E': '1:1',
            'A': '1:2N',
            'J': '1:2N+',
            'B': 'N:1',
            'CDI': 'complex',
        }
        counts.index = counts.index.map(lambda x: scenario_to_notation.get(x, x))

        # ===== Stacked version =====
        fig1, ax1 = plt.subplots(figsize=(12, 6))

        counts.plot(kind='barh', stacked=True, ax=ax1, colormap='tab10')

        ax1.set_xlabel('Number of gene pairs')
        ax1.set_ylabel('Mapping Type')
        ax1.set_title('Gene Pairs by Mapping Type (Stacked by Class Type)')
        ax1.legend(title='Class Type', bbox_to_anchor=(1.02, 1), loc='upper left')

        plt.tight_layout()

        output_stacked = self.output_dir / "scenario_barplot_stacked.png"
        fig1.savefig(output_stacked, dpi=self.config["figure_dpi"], bbox_inches='tight')
        plt.close(fig1)

        print(f"  [DONE] Saved: {output_stacked}")

        # ===== Non-stacked version =====
        fig2, ax2 = plt.subplots(figsize=(10, 6))

        scenario_totals = counts.sum(axis=1)
        scenario_totals.plot(kind='barh', ax=ax2, color='steelblue')

        ax2.set_xlabel('Number of gene pairs')
        ax2.set_ylabel('Mapping Type')
        ax2.set_title('Gene Pairs by Mapping Type')

        # Add count labels
        for i, v in enumerate(scenario_totals):
            ax2.text(v + 50, i, str(int(v)), va='center')

        plt.tight_layout()

        output_simple = self.output_dir / "scenario_barplot_simple.png"
        fig2.savefig(output_simple, dpi=self.config["figure_dpi"], bbox_inches='tight')
        plt.close(fig2)

        print(f"  [DONE] Saved: {output_simple}")

        return output_stacked

    # =========================================================================
    # TASK 5: ProteinX Plot
    # =========================================================================
    def task_5_proteinx(self) -> Optional[Path]:
        """
        Generate: proteinx_comparison.png

        Compares ProteinX pLDDT scores between ref and query.
        Creates stacked bar plot comparing pLDDT distribution.

        Returns:
            Path to output file, or None if skipped
        """
        print("\n[Task 5] ProteinX Plot")

        ref_file = Path(self.config["proteinx_ref"])
        qry_file = Path(self.config["proteinx_qry"])

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

        output_path = self.output_dir / "proteinx_comparison.png"
        fig.savefig(output_path, dpi=self.config["figure_dpi"], bbox_inches='tight')
        plt.close(fig)

        # Print summary stats
        print(f"  New (NCBI) pLDDT: mean={ref_plddt.mean():.1f}, median={ref_plddt.median():.1f}")
        print(f"  Old (FungiDB) pLDDT: mean={qry_plddt.mean():.1f}, median={qry_plddt.median():.1f}")
        print(f"  [DONE] Saved: {output_path}")

        # ===== Additional plots: pLDDT by mapping_type and class_type =====
        # Requires merging with PAVprot transcript-level data
        if self.transcript_df is not None:
            print("  Generating pLDDT distribution by mapping/class type...")

            # Clean gene_name to get transcript ID (remove _sample_N suffix)
            ref_df['transcript_id'] = ref_df['gene_name'].str.replace(r'_sample_\d+$', '', regex=True)
            qry_df['transcript_id'] = qry_df['gene_name'].str.replace(r'_sample_\d+$', '', regex=True)

            # Detect column naming scheme
            if 'query_transcript' in self.transcript_df.columns:
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
            pavprot_df = self.transcript_df[[ref_trans_col, qry_trans_col,
                                             'class_type_gene', 'class_type_transcript']].copy()

            # Add mapping_type from gene_df if available
            if self.gene_df is not None and 'mapping_type' in self.gene_df.columns:
                gene_mapping = self.gene_df[[ref_gene_col, qry_gene_col, 'mapping_type']].drop_duplicates()
                # Get gene columns from transcript data
                if ref_gene_col in self.transcript_df.columns and qry_gene_col in self.transcript_df.columns:
                    pavprot_df[ref_gene_col] = self.transcript_df[ref_gene_col]
                    pavprot_df[qry_gene_col] = self.transcript_df[qry_gene_col]
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
                mt_path = self.output_dir / "proteinx_by_mapping_type.png"
                fig_mt.savefig(mt_path, dpi=self.config["figure_dpi"], bbox_inches='tight')
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
                ct_path = self.output_dir / "proteinx_by_class_type.png"
                fig_ct.savefig(ct_path, dpi=self.config["figure_dpi"], bbox_inches='tight')
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
                    comb_path = self.output_dir / "proteinx_by_mapping_and_class.png"
                    fig_comb.savefig(comb_path, dpi=self.config["figure_dpi"], bbox_inches='tight')
                    plt.close(fig_comb)
                    print(f"  [DONE] Saved: {comb_path}")

        return output_path

    # =========================================================================
    # TASK 6: Psauron Data Integration
    # =========================================================================
    def task_6_psauron_integration(self) -> Optional[Path]:
        """
        Integrate Psauron scores into PAVprot output files.

        Psauron predicts whether a sequence is a real protein using
        in-frame reading scores. Higher scores indicate better coding potential.

        - Appends psauron scores to transcript-level TSV
        - Calculates mean for gene-level TSV

        Returns:
            Path to integrated gene-level file, or None if skipped
        """
        print("\n[Task 6] Psauron Data Integration")

        ref_file = Path(self.config["psauron_ref"])
        qry_file = Path(self.config["psauron_qry"])

        if not check_file_exists(ref_file, "Psauron ref"):
            return None
        if not check_file_exists(qry_file, "Psauron qry"):
            return None

        if self.transcript_tsv is None or not self.transcript_tsv.exists():
            print("  [SKIP] Transcript-level TSV not found")
            return None

        # Load psauron data (skip first 2 lines which are command info)
        print(f"  Loading Psauron ref: {ref_file}")
        psauron_ref = pd.read_csv(ref_file, skiprows=2)
        print(f"    Loaded {len(psauron_ref)} entries")

        print(f"  Loading Psauron qry: {qry_file}")
        psauron_qry = pd.read_csv(qry_file, skiprows=2)
        print(f"    Loaded {len(psauron_qry)} entries")

        # Rename columns for clarity
        psauron_ref = psauron_ref.rename(columns={
            'description': 'ref_transcript',
            'psauron_is_protein': 'ref_psauron_is_protein',
            'in-frame_score': 'ref_psauron_score'
        })
        psauron_qry = psauron_qry.rename(columns={
            'description': 'query_transcript',
            'psauron_is_protein': 'qry_psauron_is_protein',
            'in-frame_score': 'qry_psauron_score'
        })

        # Load transcript-level data
        print(f"  Loading transcript data: {self.transcript_tsv}")
        transcript_df = pd.read_csv(self.transcript_tsv, sep='\t')
        print(f"    Loaded {len(transcript_df)} transcript pairs")

        # Detect column naming scheme in transcript data
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

        # Merge psauron scores with transcript-level data
        # Left join to keep all original records
        merged_df = transcript_df.merge(
            psauron_ref[['ref_transcript', 'ref_psauron_is_protein', 'ref_psauron_score']].rename(
                columns={'ref_transcript': ref_trans_col}),
            on=ref_trans_col,
            how='left'
        )
        merged_df = merged_df.merge(
            psauron_qry[['query_transcript', 'qry_psauron_is_protein', 'qry_psauron_score']].rename(
                columns={'query_transcript': qry_trans_col}),
            on=qry_trans_col,
            how='left'
        )

        # Save integrated transcript-level file
        transcript_out = self.output_dir / "transcript_level_with_psauron.tsv"
        merged_df.to_csv(transcript_out, sep='\t', index=False)
        print(f"  [DONE] Saved transcript-level: {transcript_out}")

        # Calculate gene-level aggregation (mean of transcript scores)
        gene_agg = merged_df.groupby([qry_gene_col, ref_gene_col]).agg({
            'ref_psauron_score': 'mean',
            'qry_psauron_score': 'mean',
            'ref_psauron_is_protein': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else None,
            'qry_psauron_is_protein': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else None,
        }).reset_index()

        gene_agg = gene_agg.rename(columns={
            'ref_psauron_score': 'ref_psauron_score_mean',
            'qry_psauron_score': 'qry_psauron_score_mean',
        })

        # Load and merge with existing gene-level data
        if self.gene_tsv and self.gene_tsv.exists():
            gene_df = pd.read_csv(self.gene_tsv, sep='\t')

            # Drop existing psauron columns if present to avoid _x/_y suffixes
            psauron_cols_to_drop = [c for c in gene_df.columns if 'psauron' in c.lower()]
            if psauron_cols_to_drop:
                gene_df = gene_df.drop(columns=psauron_cols_to_drop)

            gene_merged = gene_df.merge(
                gene_agg,
                on=[qry_gene_col, ref_gene_col],
                how='left'
            )

            gene_out = self.output_dir / "gene_level_with_psauron.tsv"
            gene_merged.to_csv(gene_out, sep='\t', index=False)
            print(f"  [DONE] Saved gene-level: {gene_out}")

            # Store for use by task_7
            self._psauron_gene_df = gene_merged

            # Print summary stats
            ref_matched = merged_df['ref_psauron_score'].notna().sum()
            qry_matched = merged_df['qry_psauron_score'].notna().sum()
            print(f"  Matched ref transcripts: {ref_matched}/{len(merged_df)} ({100*ref_matched/len(merged_df):.1f}%)")
            print(f"  Matched qry transcripts: {qry_matched}/{len(merged_df)} ({100*qry_matched/len(merged_df):.1f}%)")

            return gene_out

        return transcript_out

    # =========================================================================
    # TASK 7: Psauron Plots
    # =========================================================================
    def task_7_psauron_plots(self) -> Optional[Path]:
        """
        Generate Psauron comparison plots.

        Creates:
        - Scatter plot: ref vs query psauron scores
        - Distribution comparison (histogram)
        - Score comparison by mapping type

        Requires Task 6 (integration) to be completed first, or loads
        from saved file if available.

        Returns:
            Path to output file, or None if skipped
        """
        print("\n[Task 7] Psauron Plots")

        # Try to get integrated data from task_6, or load from file
        psauron_gene_file = self.output_dir / "gene_level_with_psauron.tsv"

        if hasattr(self, '_psauron_gene_df') and self._psauron_gene_df is not None:
            df = self._psauron_gene_df
            print("  Using data from Task 6")
        elif psauron_gene_file.exists():
            print(f"  Loading from: {psauron_gene_file}")
            df = pd.read_csv(psauron_gene_file, sep='\t')
        else:
            print("  [SKIP] Run Task 6 (Psauron integration) first")
            return None

        # Detect column naming scheme
        if 'query_gene' in df.columns:
            # NEW NAMING: ref_gene, query_gene
            ref_gene_col = 'ref_gene'
            qry_gene_col = 'query_gene'
            ref_trans_col = 'ref_transcript'
            qry_trans_col = 'query_transcript'
        else:
            # OLD NAMING: new_gene, old_gene
            ref_gene_col = 'new_gene'
            qry_gene_col = 'old_gene'
            ref_trans_col = 'new_transcript'
            qry_trans_col = 'old_transcript'

        # Check required columns
        ref_col = 'ref_psauron_score_mean'
        qry_col = 'qry_psauron_score_mean'

        if ref_col not in df.columns or qry_col not in df.columns:
            print(f"  [SKIP] Required columns not found: {ref_col}, {qry_col}")
            return None

        # Filter to records with both scores
        cols_to_select = [ref_col, qry_col, 'mapping_type']
        if 'class_type_gene' in df.columns:
            cols_to_select.append('class_type_gene')
        plot_df = df[cols_to_select].dropna()
        print(f"  Plotting {len(plot_df)} gene pairs with both scores")

        if len(plot_df) == 0:
            print("  [SKIP] No gene pairs with both psauron scores")
            return None

        # Create figure with 3 subplots
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))

        # ===== Plot 1: Scatter ref vs query =====
        ax1 = axes[0]
        ax1.scatter(plot_df[ref_col], plot_df[qry_col], alpha=0.5, s=15)
        ax1.plot([0, 1], [0, 1], 'k--', alpha=0.3, label='y=x')
        ax1.set_xlabel('New annotation (NCBI RefSeq) Psauron Score')
        ax1.set_ylabel('Old annotation (FungiDB v68) Psauron Score')
        ax1.set_title('Psauron Score: New vs Old')
        ax1.set_xlim(0, 1.05)
        ax1.set_ylim(0, 1.05)

        # Add correlation and R²
        corr = plot_df[ref_col].corr(plot_df[qry_col])
        r_squared = corr ** 2
        ax1.text(0.05, 0.95, f'r = {corr:.3f}\nR² = {r_squared:.3f}', transform=ax1.transAxes,
                fontsize=10, va='top')

        # ===== Plot 2: Distribution comparison =====
        ax2 = axes[1]
        ax2.hist(plot_df[ref_col], bins=30, alpha=0.5, label='New (NCBI)',
                color='steelblue', density=True)
        ax2.hist(plot_df[qry_col], bins=30, alpha=0.5, label='Old (FungiDB)',
                color='coral', density=True)
        ax2.axvline(x=0.5, color='red', linestyle='--', alpha=0.5, label='Threshold (0.5)')
        ax2.set_xlabel('Psauron Score')
        ax2.set_ylabel('Density')
        ax2.set_title('Psauron Score Distribution')
        ax2.legend()

        # ===== Plot 3: Box plot by mapping type =====
        ax3 = axes[2]

        # Prepare data for box plot
        mapping_types = ['1to1', '1to2N', '1to2N+', 'Nto1', 'complex']
        mapping_types_present = [m for m in mapping_types if m in plot_df['mapping_type'].values]

        ref_data = [plot_df[plot_df['mapping_type'] == m][ref_col].values
                   for m in mapping_types_present]
        qry_data = [plot_df[plot_df['mapping_type'] == m][qry_col].values
                   for m in mapping_types_present]

        # Position for grouped boxes
        positions_ref = np.arange(len(mapping_types_present)) * 2
        positions_qry = positions_ref + 0.6

        bp_ref = ax3.boxplot(ref_data, positions=positions_ref, widths=0.5,
                             patch_artist=True)
        bp_qry = ax3.boxplot(qry_data, positions=positions_qry, widths=0.5,
                             patch_artist=True)

        # Color the boxes
        for box in bp_ref['boxes']:
            box.set_facecolor('steelblue')
            box.set_alpha(0.7)
        for box in bp_qry['boxes']:
            box.set_facecolor('coral')
            box.set_alpha(0.7)

        ax3.set_xticks(positions_ref + 0.3)
        ax3.set_xticklabels([mapping_type_to_colon(m) for m in mapping_types_present])
        ax3.set_xlabel('Mapping Type')
        ax3.set_ylabel('Psauron Score')
        ax3.set_title('Psauron Score by Mapping Type')

        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor='steelblue', alpha=0.7, label='New (NCBI)'),
                         Patch(facecolor='coral', alpha=0.7, label='Old (FungiDB)')]
        ax3.legend(handles=legend_elements)

        plt.tight_layout()

        output_path = self.output_dir / "psauron_comparison.png"
        fig.savefig(output_path, dpi=self.config["figure_dpi"], bbox_inches='tight')
        plt.close(fig)

        # Print summary stats
        print(f"  New (NCBI) mean: {plot_df[ref_col].mean():.3f} (std: {plot_df[ref_col].std():.3f})")
        print(f"  Old (FungiDB) mean: {plot_df[qry_col].mean():.3f} (std: {plot_df[qry_col].std():.3f})")
        print(f"  [DONE] Saved: {output_path}")

        # ===== Psauron by Mapping Type =====
        if 'mapping_type' in df.columns and len(plot_df) > 0:
            fig_mt, axes_mt = plt.subplots(1, 2, figsize=(14, 5))
            mapping_types = ['1to1', '1to2N', '1to2N+', 'Nto1', 'complex']
            mapping_colors = {
                '1to1': '#1f77b4', '1to2N': '#ff7f0e', '1to2N+': '#2ca02c',
                'Nto1': '#d62728', 'complex': '#9467bd'
            }

            for ax, col, title in [(axes_mt[0], ref_col, 'New (NCBI)'),
                                    (axes_mt[1], qry_col, 'Old (FungiDB)')]:
                for mtype in mapping_types:
                    data = plot_df[plot_df['mapping_type'] == mtype][col].dropna()
                    if len(data) > 0:
                        ax.hist(data, bins=30, alpha=0.5, density=True,
                               label=f'{mapping_type_to_colon(mtype)} (n={len(data)})',
                               color=mapping_colors.get(mtype, 'gray'))
                ax.set_xlabel('Psauron Score')
                ax.set_ylabel('Density')
                ax.set_title(f'{title} - Psauron by Mapping Type')
                ax.legend(fontsize=8)

            plt.tight_layout()
            mt_path = self.output_dir / "psauron_by_mapping_type.png"
            fig_mt.savefig(mt_path, dpi=self.config["figure_dpi"], bbox_inches='tight')
            plt.close(fig_mt)
            print(f"  [DONE] Saved: {mt_path}")

        # ===== Psauron by Class Type =====
        if 'class_type_gene' in df.columns and len(plot_df) > 0:
            fig_ct, axes_ct = plt.subplots(1, 2, figsize=(14, 5))
            top_classes = plot_df['class_type_gene'].value_counts().head(8).index.tolist()
            class_colors = plt.cm.tab10(np.linspace(0, 1, len(top_classes)))

            for ax, col, title in [(axes_ct[0], ref_col, 'New (NCBI)'),
                                    (axes_ct[1], qry_col, 'Old (FungiDB)')]:
                for i, ctype in enumerate(top_classes):
                    data = plot_df[plot_df['class_type_gene'] == ctype][col].dropna()
                    if len(data) > 0:
                        ax.hist(data, bins=25, alpha=0.5, density=True,
                               label=f'{ctype} (n={len(data)})',
                               color=class_colors[i % len(class_colors)])
                ax.set_xlabel('Psauron Score')
                ax.set_ylabel('Density')
                ax.set_title(f'{title} - Psauron by Class Type')
                ax.legend(fontsize=7, loc='upper right')

            plt.tight_layout()
            ct_path = self.output_dir / "psauron_by_class_type.png"
            fig_ct.savefig(ct_path, dpi=self.config["figure_dpi"], bbox_inches='tight')
            plt.close(fig_ct)
            print(f"  [DONE] Saved: {ct_path}")

        # ===== Psauron by Mapping Type x Class Type =====
        if 'mapping_type' in df.columns and 'class_type_gene' in df.columns and len(plot_df) > 0:
            mapping_types_present = plot_df['mapping_type'].unique()
            top_classes = plot_df['class_type_gene'].value_counts().head(4).index.tolist()
            class_colors = plt.cm.tab10(np.linspace(0, 1, len(top_classes)))

            fig_comb, axes_comb = plt.subplots(len(mapping_types_present), 2,
                                              figsize=(12, 3*len(mapping_types_present)))
            if len(mapping_types_present) == 1:
                axes_comb = axes_comb.reshape(1, -1)

            for row_idx, (mtype, (ax_ref, ax_qry)) in enumerate(zip(
                sorted(mapping_types_present),
                zip(axes_comb[:, 0], axes_comb[:, 1]))):

                mtype_data = plot_df[plot_df['mapping_type'] == mtype]
                for i, ctype in enumerate(top_classes):
                    subset_ref = mtype_data[mtype_data['class_type_gene'] == ctype][ref_col].dropna()
                    subset_qry = mtype_data[mtype_data['class_type_gene'] == ctype][qry_col].dropna()

                    if len(subset_ref) > 0:
                        ax_ref.hist(subset_ref, bins=20, alpha=0.5,
                                   label=f'{ctype} (n={len(subset_ref)})',
                                   color=class_colors[i % len(class_colors)])
                    if len(subset_qry) > 0:
                        ax_qry.hist(subset_qry, bins=20, alpha=0.5,
                                   label=f'{ctype} (n={len(subset_qry)})',
                                   color=class_colors[i % len(class_colors)])

                ax_ref.set_title(f'New (NCBI) - {mapping_type_to_colon(mtype)}')
                ax_qry.set_title(f'Old (FungiDB) - {mapping_type_to_colon(mtype)}')
                if row_idx == len(mapping_types_present) - 1:
                    ax_ref.set_xlabel('Psauron Score')
                    ax_qry.set_xlabel('Psauron Score')
                ax_ref.legend(fontsize=6)

            plt.tight_layout()
            comb_path = self.output_dir / "psauron_by_mapping_and_class.png"
            fig_comb.savefig(comb_path, dpi=self.config["figure_dpi"], bbox_inches='tight')
            plt.close(fig_comb)
            print(f"  [DONE] Saved: {comb_path}")

        # ===== Psauron vs pLDDT plots (Gene-to-Gene comparison) =====
        # Aggregate to gene level and compare gene pairs
        ref_proteinx = Path(self.config["proteinx_ref"])
        qry_proteinx = Path(self.config["proteinx_qry"])

        if ref_proteinx.exists() and qry_proteinx.exists():
            print("  Generating Psauron vs pLDDT plots (gene-to-gene)...")

            # Load ProteinX data
            proteinx_ref = pd.read_csv(ref_proteinx, sep='\t')
            proteinx_qry = pd.read_csv(qry_proteinx, sep='\t')

            # Clean gene_name to get transcript ID
            proteinx_ref['transcript_id'] = proteinx_ref['gene_name'].str.replace(r'_sample_\d+$', '', regex=True)
            proteinx_qry['transcript_id'] = proteinx_qry['gene_name'].str.replace(r'_sample_\d+$', '', regex=True)

            # Load transcript-level data to map transcripts to gene pairs
            psauron_transcript_file = self.output_dir / "transcript_level_with_psauron.tsv"
            if psauron_transcript_file.exists():
                psauron_trans_df = pd.read_csv(psauron_transcript_file, sep='\t')

                # Merge ref pLDDT with transcript data to get gene mapping
                ref_trans_plddt = proteinx_ref[['transcript_id', 'residue_plddt_mean']].merge(
                    psauron_trans_df[[qry_trans_col, qry_gene_col, ref_gene_col]].rename(
                        columns={qry_trans_col: 'transcript_id'}),
                    on='transcript_id', how='inner'
                )

                # Merge query pLDDT with transcript data
                qry_trans_plddt = proteinx_qry[['transcript_id', 'residue_plddt_mean']].merge(
                    psauron_trans_df[[ref_trans_col, qry_gene_col, ref_gene_col]].rename(
                        columns={ref_trans_col: 'transcript_id'}),
                    on='transcript_id', how='inner'
                )

                # Aggregate pLDDT to gene level (mean of transcript pLDDT per gene pair)
                old_gene_plddt = ref_trans_plddt.groupby([qry_gene_col, ref_gene_col]).agg({
                    'residue_plddt_mean': 'mean'
                }).reset_index().rename(columns={'residue_plddt_mean': 'ref_plddt_mean'})

                qry_gene_plddt = qry_trans_plddt.groupby([qry_gene_col, ref_gene_col]).agg({
                    'residue_plddt_mean': 'mean'
                }).reset_index().rename(columns={'residue_plddt_mean': 'qry_plddt_mean'})

                # Start with gene-level Psauron data (already has mean scores)
                gene_combined = df[[qry_gene_col, ref_gene_col, ref_col, qry_col,
                                   'mapping_type', 'class_type_gene']].copy()

                # Merge pLDDT scores
                gene_combined = gene_combined.merge(old_gene_plddt, on=[qry_gene_col, ref_gene_col], how='left')
                gene_combined = gene_combined.merge(qry_gene_plddt, on=[qry_gene_col, ref_gene_col], how='left')

                # Filter to gene pairs with all scores
                valid_pairs = gene_combined.dropna(subset=[ref_col, qry_col, 'ref_plddt_mean', 'qry_plddt_mean'])
                print(f"    Gene pairs with all scores: {len(valid_pairs)}")

                if len(valid_pairs) > 0:
                    # ===== Plot 1: Gene-pair Psauron vs pLDDT scatter =====
                    fig_scatter, axes_scatter = plt.subplots(1, 2, figsize=(14, 6))

                    # Reference genes
                    ax1 = axes_scatter[0]
                    ax1.scatter(valid_pairs[ref_col], valid_pairs['ref_plddt_mean'],
                               alpha=0.3, s=15, c='steelblue')
                    ax1.set_xlabel('New (NCBI) Gene Psauron Score')
                    ax1.set_ylabel('New (NCBI) Gene pLDDT Score')
                    ax1.set_title(f'New annotation (NCBI RefSeq): Psauron vs pLDDT (n={len(valid_pairs)} gene pairs)')
                    ax1.set_xlim(0, 1.05)
                    corr_ref = valid_pairs[ref_col].corr(valid_pairs['ref_plddt_mean'])
                    r2_ref = corr_ref ** 2
                    ax1.text(0.05, 0.95, f'r = {corr_ref:.3f}\nR² = {r2_ref:.3f}', transform=ax1.transAxes, fontsize=10, va='top')

                    # Query genes
                    ax2 = axes_scatter[1]
                    ax2.scatter(valid_pairs[qry_col], valid_pairs['qry_plddt_mean'],
                               alpha=0.3, s=15, c='coral')
                    ax2.set_xlabel('Old (FungiDB) Gene Psauron Score')
                    ax2.set_ylabel('Old (FungiDB) Gene pLDDT Score')
                    ax2.set_title(f'Old annotation (FungiDB v68): Psauron vs pLDDT (n={len(valid_pairs)} gene pairs)')
                    ax2.set_xlim(0, 1.05)
                    corr_qry = valid_pairs[qry_col].corr(valid_pairs['qry_plddt_mean'])
                    r2_qry = corr_qry ** 2
                    ax2.text(0.05, 0.95, f'r = {corr_qry:.3f}\nR² = {r2_qry:.3f}', transform=ax2.transAxes, fontsize=10, va='top')

                    plt.tight_layout()
                    scatter_path = self.output_dir / "psauron_vs_plddt_gene_level.png"
                    fig_scatter.savefig(scatter_path, dpi=self.config["figure_dpi"], bbox_inches='tight')
                    plt.close(fig_scatter)
                    print(f"  [DONE] Saved: {scatter_path}")

                    # ===== Plot 2: Psauron vs pLDDT by Mapping Type (gene level) =====
                    mapping_types = ['1to1', '1to2N', '1to2N+', 'Nto1', 'complex']
                    mapping_colors = {
                        '1to1': '#1f77b4', '1to2N': '#ff7f0e', '1to2N+': '#2ca02c',
                        'Nto1': '#d62728', 'complex': '#9467bd'
                    }

                    fig_mt, axes_mt = plt.subplots(1, 2, figsize=(14, 6))

                    # Reference by mapping type
                    ax1 = axes_mt[0]
                    for mtype in mapping_types:
                        subset = valid_pairs[valid_pairs['mapping_type'] == mtype]
                        if len(subset) > 0:
                            ax1.scatter(subset[ref_col], subset['ref_plddt_mean'],
                                       alpha=0.4, s=20, c=mapping_colors.get(mtype, 'gray'),
                                       label=f'{mapping_type_to_colon(mtype)} (n={len(subset)})')
                    ax1.set_xlabel('New (NCBI) Psauron Score')
                    ax1.set_ylabel('New (NCBI) pLDDT Score')
                    ax1.set_title('New annotation (NCBI) by Mapping Type')
                    ax1.set_xlim(0, 1.05)
                    ax1.legend(fontsize=8)

                    # Query by mapping type
                    ax2 = axes_mt[1]
                    for mtype in mapping_types:
                        subset = valid_pairs[valid_pairs['mapping_type'] == mtype]
                        if len(subset) > 0:
                            ax2.scatter(subset[qry_col], subset['qry_plddt_mean'],
                                       alpha=0.4, s=20, c=mapping_colors.get(mtype, 'gray'),
                                       label=f'{mapping_type_to_colon(mtype)} (n={len(subset)})')
                    ax2.set_xlabel('Old (FungiDB) Psauron Score')
                    ax2.set_ylabel('Old (FungiDB) pLDDT Score')
                    ax2.set_title('Old annotation (FungiDB) by Mapping Type')
                    ax2.set_xlim(0, 1.05)
                    ax2.legend(fontsize=8)

                    plt.tight_layout()
                    mt_path = self.output_dir / "psauron_vs_plddt_by_mapping_gene_level.png"
                    fig_mt.savefig(mt_path, dpi=self.config["figure_dpi"], bbox_inches='tight')
                    plt.close(fig_mt)
                    print(f"  [DONE] Saved: {mt_path}")

                    # ===== Plot 3: Psauron vs pLDDT by Class Type (gene level) =====
                    top_classes = valid_pairs['class_type_gene'].value_counts().head(6).index.tolist()

                    fig_ct, axes_ct = plt.subplots(1, 2, figsize=(14, 6))

                    # Reference by class type
                    ax1 = axes_ct[0]
                    for i, ctype in enumerate(top_classes):
                        subset = valid_pairs[valid_pairs['class_type_gene'] == ctype]
                        if len(subset) > 0:
                            ax1.scatter(subset[ref_col], subset['ref_plddt_mean'],
                                       alpha=0.4, s=20, color=plt.cm.tab10(i/10),
                                       label=f'{ctype} (n={len(subset)})')
                    ax1.set_xlabel('New (NCBI) Psauron Score')
                    ax1.set_ylabel('New (NCBI) pLDDT Score')
                    ax1.set_title('New annotation (NCBI) by Class Type')
                    ax1.set_xlim(0, 1.05)
                    ax1.legend(fontsize=7, loc='lower right')

                    # Query by class type
                    ax2 = axes_ct[1]
                    for i, ctype in enumerate(top_classes):
                        subset = valid_pairs[valid_pairs['class_type_gene'] == ctype]
                        if len(subset) > 0:
                            ax2.scatter(subset[qry_col], subset['qry_plddt_mean'],
                                       alpha=0.4, s=20, color=plt.cm.tab10(i/10),
                                       label=f'{ctype} (n={len(subset)})')
                    ax2.set_xlabel('Old (FungiDB) Psauron Score')
                    ax2.set_ylabel('Old (FungiDB) pLDDT Score')
                    ax2.set_title('Old annotation (FungiDB) by Class Type')
                    ax2.set_xlim(0, 1.05)
                    ax2.legend(fontsize=7, loc='lower right')

                    plt.tight_layout()
                    ct_path = self.output_dir / "psauron_vs_plddt_by_class_gene_level.png"
                    fig_ct.savefig(ct_path, dpi=self.config["figure_dpi"], bbox_inches='tight')
                    plt.close(fig_ct)
                    print(f"  [DONE] Saved: {ct_path}")

                    # ===== Plot 4: Combined faceted - Mapping Type x Class Type (gene level) =====
                    mapping_types_present = [m for m in mapping_types if m in valid_pairs['mapping_type'].values]
                    top_3_classes = valid_pairs['class_type_gene'].value_counts().head(3).index.tolist()

                    if len(mapping_types_present) > 0 and len(top_3_classes) > 0:
                        fig_comb, axes_comb = plt.subplots(len(mapping_types_present), 2,
                                                          figsize=(12, 3 * len(mapping_types_present)))

                        if len(mapping_types_present) == 1:
                            axes_comb = axes_comb.reshape(1, -1)

                        for row_idx, mtype in enumerate(mapping_types_present):
                            mtype_data = valid_pairs[valid_pairs['mapping_type'] == mtype]

                            # Reference
                            ax_ref = axes_comb[row_idx, 0]
                            for i, ctype in enumerate(top_3_classes):
                                subset = mtype_data[mtype_data['class_type_gene'] == ctype]
                                if len(subset) > 0:
                                    ax_ref.scatter(subset[ref_col], subset['ref_plddt_mean'],
                                                  alpha=0.5, s=15, color=plt.cm.tab10(i/10), label=ctype)
                            ax_ref.set_xlim(0, 1.05)
                            ax_ref.set_ylabel('pLDDT')
                            ax_ref.set_title(f'New (NCBI) - {mapping_type_to_colon(mtype)}')
                            if row_idx == 0:
                                ax_ref.legend(fontsize=6, loc='lower right')
                            if row_idx == len(mapping_types_present) - 1:
                                ax_ref.set_xlabel('Psauron Score')

                            # Query
                            ax_qry = axes_comb[row_idx, 1]
                            for i, ctype in enumerate(top_3_classes):
                                subset = mtype_data[mtype_data['class_type_gene'] == ctype]
                                if len(subset) > 0:
                                    ax_qry.scatter(subset[qry_col], subset['qry_plddt_mean'],
                                                  alpha=0.5, s=15, color=plt.cm.tab10(i/10), label=ctype)
                            ax_qry.set_xlim(0, 1.05)
                            ax_qry.set_title(f'Old (FungiDB) - {mapping_type_to_colon(mtype)}')
                            if row_idx == len(mapping_types_present) - 1:
                                ax_qry.set_xlabel('Psauron Score')

                        plt.tight_layout()
                        comb_path = self.output_dir / "psauron_vs_plddt_by_mapping_and_class_gene_level.png"
                        fig_comb.savefig(comb_path, dpi=self.config["figure_dpi"], bbox_inches='tight')
                        plt.close(fig_comb)
                        print(f"  [DONE] Saved: {comb_path}")

        return output_path

    # =========================================================================
    # TASK 8: FungiDB Transcript Analysis
    # =========================================================================
    def task_8_fungidb_analysis(self) -> Optional[Path]:
        """
        Analyze transcript counts across FungiDB phytopathogens.

        Generates:
        - Summary tables at genus and order level
        - Visualization plots (transcripts per gene, exon distributions)

        Returns:
            Path to output directory, or None if skipped
        """
        print("\n[Task 8] FungiDB Transcript Analysis")

        phyto_file = Path(self.config["phytopathogen_list"])
        stats_file = Path(self.config["fungidb_gene_stats"])

        if not check_file_exists(phyto_file, "Phytopathogen list"):
            return None
        if not check_file_exists(stats_file, "FungiDB gene stats"):
            return None

        # Load data
        print(f"  Loading phytopathogen list: {phyto_file}")
        phyto_df = pd.read_csv(phyto_file)

        print(f"  Loading gene stats: {stats_file}")
        stats_df = pd.read_csv(stats_file, sep='\t', low_memory=False)
        print(f"    Loaded {len(stats_df)} gene records")

        # Handle comma-separated exon_counts (multi-transcript genes)
        # Take mean of exon counts for multi-transcript genes
        def parse_exon_counts(x):
            if pd.isna(x):
                return np.nan
            if isinstance(x, (int, float)):
                return float(x)
            # Handle comma-separated values
            try:
                vals = [float(v.strip()) for v in str(x).split(',')]
                return np.mean(vals)
            except:
                return np.nan

        stats_df['exon_counts_numeric'] = stats_df['exon_counts'].apply(parse_exon_counts)

        # Ensure transcripts_per_gene is numeric
        stats_df['transcripts_per_gene'] = pd.to_numeric(stats_df['transcripts_per_gene'], errors='coerce')

        # Extract genus from organism column in phytopathogen list
        # The format is <i>Genus</i> or <i>Genus species</i>
        def extract_genus(org_str):
            import re
            # Remove HTML tags and extract first word (genus)
            clean = re.sub(r'<[^>]+>', '', str(org_str)).strip()
            return clean.split()[0] if clean else None

        phyto_df['genus_extracted'] = phyto_df['Organism'].apply(extract_genus)

        # Filter to significant plant pathogens
        plant_pathogen_col = 'Significant Plant Pathogen'
        if plant_pathogen_col in phyto_df.columns:
            phyto_fungi = phyto_df[
                (phyto_df[plant_pathogen_col].fillna('').str.lower() == 'yes') &
                (phyto_df['VEuPathDB Database'].fillna('').str.lower() == 'fungidb')
            ]
            print(f"  Found {len(phyto_fungi)} significant plant pathogens in FungiDB")
        else:
            print(f"  [WARN] Column '{plant_pathogen_col}' not found")
            phyto_fungi = phyto_df

        if len(phyto_fungi) == 0:
            print("  [SKIP] No FungiDB plant pathogens found")
            return None

        # Get list of phytopathogen genera
        phyto_genera = set(phyto_fungi['genus_extracted'].dropna().unique())
        print(f"  Phytopathogen genera: {sorted(phyto_genera)}")

        # Filter gene stats to phytopathogen genera
        filtered_stats = stats_df[stats_df['genus'].isin(phyto_genera)]
        print(f"  Matched {len(filtered_stats)} genes from phytopathogen genera")

        if len(filtered_stats) == 0:
            print("  [SKIP] No matching genes found")
            return None

        # Create output subdirectory for Task 8
        task8_dir = self.output_dir / "fungidb_analysis"
        task8_dir.mkdir(exist_ok=True)

        # ===== Summary by Genus =====
        genus_summary = filtered_stats.groupby('genus').agg({
            'gene_id': 'count',
            'transcripts_per_gene': ['mean', 'median', 'std'],
            'exon_counts_numeric': ['mean','std'],
            'organism_abbreviation': 'nunique'
        }).round(3)
        genus_summary.columns = ['gene_count', 'mean_transcripts', 'median_transcripts',
                                 'std_transcripts', 'mean_exons', 'std_exons', 'num_organisms']
        genus_summary['mean_genes_per_organism'] = (genus_summary['gene_count'] / genus_summary['num_organisms']).round(0).astype(int)
        genus_summary = genus_summary.sort_values('gene_count', ascending=False)

        genus_file = task8_dir / "summary_by_genus.tsv"
        genus_summary.to_csv(genus_file, sep='\t')
        print(f"  [DONE] Saved: {genus_file}")

        # ===== Summary by Order =====
        order_summary = filtered_stats.groupby('order').agg({
            'gene_id': 'count',
            'transcripts_per_gene': ['mean', 'median', 'std'],
            'exon_counts_numeric': ['mean','std'],
            'genus': 'nunique',
            'organism_abbreviation': 'nunique'
        }).round(3)
        order_summary.columns = ['gene_count', 'mean_transcripts', 'median_transcripts',
                                'std_transcripts', 'mean_exons', 'std_exons', 'num_genera', 'num_organisms']
        order_summary = order_summary.sort_values('gene_count', ascending=False)

        order_file = task8_dir / "summary_by_order.tsv"
        order_summary.to_csv(order_file, sep='\t')
        print(f"  [DONE] Saved: {order_file}")

        # ===== Full filtered dataset =====
        filtered_file = task8_dir / "phytopathogen_gene_stats.tsv"
        filtered_stats.to_csv(filtered_file, sep='\t', index=False)
        print(f"  [DONE] Saved: {filtered_file}")

        # ===== Visualization Plots =====
        # Plot 1: Transcripts per gene by genus
        fig1, ax1 = plt.subplots(figsize=(14, 6))

        # Get top genera by gene count
        top_genera = genus_summary.head(15).index.tolist()
        plot_data = filtered_stats[filtered_stats['genus'].isin(top_genera)].copy()

        genus_order = [g for g in genus_summary.index if g in top_genera]
        plot_data['genus'] = pd.Categorical(plot_data['genus'], categories=genus_order, ordered=True)

        # Box plot
        plot_data.boxplot(column='transcripts_per_gene', by='genus', ax=ax1)
        ax1.set_xlabel('Genus')
        ax1.set_ylabel('Transcripts per Gene')
        ax1.set_title('Transcripts per Gene by Genus (Top 15 Phytopathogen Genera)')
        plt.suptitle('')  # Remove default title
        ax1.tick_params(axis='x', rotation=45)

        plt.tight_layout()
        plot1_path = task8_dir / "transcripts_by_genus.png"
        fig1.savefig(plot1_path, dpi=self.config["figure_dpi"], bbox_inches='tight')
        plt.close(fig1)
        print(f"  [DONE] Saved: {plot1_path}")

        # Plot 2a: Exon counts PER GENE by order (mean of transcript exon counts)
        fig2a, ax2a = plt.subplots(figsize=(12, 6))

        top_orders = order_summary.head(10).index.tolist()
        order_data = filtered_stats[filtered_stats['order'].isin(top_orders)].copy()

        order_order = [o for o in order_summary.index if o in top_orders]
        order_data['order'] = pd.Categorical(order_data['order'], categories=order_order, ordered=True)

        order_data.boxplot(column='exon_counts_numeric', by='order', ax=ax2a)
        ax2a.set_xlabel('Order')
        ax2a.set_ylabel('Mean Exon Count per Gene')
        ax2a.set_title('Exon Counts per Gene by Order (Top 10 Phytopathogen Orders)')
        plt.suptitle('')
        ax2a.tick_params(axis='x', rotation=45)

        plt.tight_layout()
        plot2a_path = task8_dir / "exons_per_gene_by_order.png"
        fig2a.savefig(plot2a_path, dpi=self.config["figure_dpi"], bbox_inches='tight')
        plt.close(fig2a)
        print(f"  [DONE] Saved: {plot2a_path}")

        # Plot 2b: Exon counts PER TRANSCRIPT by order (expand comma-separated values)
        # Expand comma-separated exon counts to get individual transcript values
        def expand_exon_counts(df):
            rows = []
            for _, row in df.iterrows():
                exon_str = row['exon_counts']
                order_val = row['order']
                if pd.isna(exon_str):
                    continue
                # Handle comma-separated values
                if isinstance(exon_str, str) and ',' in exon_str:
                    for val in exon_str.split(','):
                        try:
                            rows.append({'order': order_val, 'exon_count': float(val.strip())})
                        except:
                            pass
                else:
                    try:
                        rows.append({'order': order_val, 'exon_count': float(exon_str)})
                    except:
                        pass
            return pd.DataFrame(rows)

        # Only expand for top orders to avoid memory issues
        order_subset = filtered_stats[filtered_stats['order'].isin(top_orders)][['order', 'exon_counts']]
        expanded_exons = expand_exon_counts(order_subset)

        if len(expanded_exons) > 0:
            fig2b, ax2b = plt.subplots(figsize=(12, 6))

            expanded_exons['order'] = pd.Categorical(expanded_exons['order'], categories=order_order, ordered=True)
            expanded_exons.boxplot(column='exon_count', by='order', ax=ax2b)
            ax2b.set_xlabel('Order')
            ax2b.set_ylabel('Exon Count per Transcript')
            ax2b.set_title('Exon Counts per Transcript by Order (Top 10 Phytopathogen Orders)')
            plt.suptitle('')
            ax2b.tick_params(axis='x', rotation=45)

            plt.tight_layout()
            plot2b_path = task8_dir / "exons_per_transcript_by_order.png"
            fig2b.savefig(plot2b_path, dpi=self.config["figure_dpi"], bbox_inches='tight')
            plt.close(fig2b)
            print(f"  [DONE] Saved: {plot2b_path}")

        # Plot 3: Bar chart - gene counts by genus
        fig3, ax3 = plt.subplots(figsize=(12, 6))

        genus_counts = genus_summary['gene_count'].head(15)
        colors = plt.cm.viridis(np.linspace(0, 0.8, len(genus_counts)))
        bars = ax3.barh(genus_counts.index[::-1], genus_counts.values[::-1], color=colors[::-1])

        ax3.set_xlabel('Number of Genes')
        ax3.set_ylabel('Genus')
        ax3.set_title('Gene Counts by Phytopathogen Genus (Top 15)')

        # Add count labels
        for bar in bars:
            width = bar.get_width()
            ax3.text(width + max(genus_counts)*0.01, bar.get_y() + bar.get_height()/2,
                    f'{int(width):,}', va='center', fontsize=8)

        plt.tight_layout()
        plot3_path = task8_dir / "gene_counts_by_genus.png"
        fig3.savefig(plot3_path, dpi=self.config["figure_dpi"], bbox_inches='tight')
        plt.close(fig3)
        print(f"  [DONE] Saved: {plot3_path}")

        # Print summary
        print(f"\n  Summary:")
        print(f"    Total phytopathogen genera: {len(phyto_genera)}")
        print(f"    Matched genera in FungiDB: {filtered_stats['genus'].nunique()}")
        print(f"    Total genes analyzed: {len(filtered_stats):,}")
        print(f"    Output directory: {task8_dir}")

        return task8_dir

    # =========================================================================
    # RUN ALL TASKS
    # =========================================================================
    def run_all(self):
        """Run all tasks in sequence."""
        print("="*60)
        print("PAVprot Master Pipeline - Running All Tasks")
        print("="*60)

        results = {}

        # Core plots (Tasks 1-4 + variants)
        results['task_1'] = self.task_1_ipr_scatter()
        results['task_2'] = self.task_2_loglog_scale()
        results['task_2b'] = self.task_2b_loglog_class_shapes()
        results['task_3'] = self.task_3_quadrants()
        results['task_3b'] = self.task_3b_quadrants_swapped()
        results['task_4'] = self.task_4_scenario_barplot()

        # External data integration (Tasks 5-8)
        results['task_5'] = self.task_5_proteinx()
        results['task_6'] = self.task_6_psauron_integration()
        results['task_7'] = self.task_7_psauron_plots()
        results['task_8'] = self.task_8_fungidb_analysis()

        # Summary
        print("\n" + "="*60)
        print("PIPELINE SUMMARY")
        print("="*60)

        completed = sum(1 for v in results.values() if v is not None)
        total = len(results)

        print(f"Completed: {completed}/{total} tasks")
        print(f"Output directory: {self.output_dir}")

        for task, result in results.items():
            status = "DONE" if result else "SKIP/TODO"
            print(f"  {task}: {status}")

        return results

    def run_plots(self):
        """Run only plotting tasks (1-4 + variants)."""
        print("Running plot tasks only...")
        self.task_1_ipr_scatter()
        self.task_2_loglog_scale()
        self.task_2b_loglog_class_shapes()
        self.task_3_quadrants()
        self.task_3b_quadrants_swapped()
        self.task_4_scenario_barplot()


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="PAVprot Master Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pipeline.py --all           Run all tasks
  python run_pipeline.py --task plots    Run only plot tasks (1-4)
  python run_pipeline.py --task psauron  Run psauron integration
  python run_pipeline.py --list          List available tasks
        """
    )

    parser.add_argument('--all', action='store_true', help='Run all tasks')
    parser.add_argument('--task', choices=['plots', 'psauron', 'proteinx', 'fungidb'],
                        help='Run specific task group')
    parser.add_argument('--list', action='store_true', help='List available tasks')
    parser.add_argument('--output-dir', help='Override output directory')

    args = parser.parse_args()

    if args.list:
        print("Available tasks:")
        print("  1.  task_1_ipr_scatter        - IPR domain length scatter by class_type")
        print("  2.  task_2_loglog_scale       - Log-log scale plot with mapping type shapes")
        print("  2b. task_2b_loglog_class_shapes - Log-log with class type shapes, mapping colors")
        print("  3.  task_3_quadrants          - Presence/absence quadrants (colors=pattern)")
        print("  3b. task_3b_quadrants_swapped - Quadrants (colors=mapping, shapes=pattern)")
        print("  4.  task_4_scenario_barplot   - Mapping scenario bar plot (stacked + simple)")
        print("  5.  task_5_proteinx           - ProteinX pLDDT comparison")
        print("  6.  task_6_psauron_integration - Psauron data integration")
        print("  7.  task_7_psauron_plots      - Psauron comparison plots")
        print("  8.  task_8_fungidb_analysis   - FungiDB phytopathogen analysis")
        print("\nUsage:")
        print("  python run_pipeline.py --all            # Run all tasks")
        print("  python run_pipeline.py --task plots     # Run only plot tasks (1-4)")
        print("  python run_pipeline.py --task proteinx  # Run only ProteinX plot")
        return

    # Update config if output dir specified
    config = CONFIG.copy()
    if args.output_dir:
        config["output_dir"] = Path(args.output_dir)

    runner = PipelineRunner(config)

    if args.all:
        runner.run_all()
    elif args.task == 'plots':
        runner.run_plots()
    elif args.task == 'psauron':
        runner.task_6_psauron_integration()
        runner.task_7_psauron_plots()
    elif args.task == 'proteinx':
        runner.task_5_proteinx()
    elif args.task == 'fungidb':
        runner.task_8_fungidb_analysis()
    else:
        # Default: run all
        runner.run_all()


if __name__ == '__main__':
    main()
