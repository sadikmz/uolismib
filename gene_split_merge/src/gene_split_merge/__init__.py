"""
Gene Split/Merge Detection Tool
=================================

A high-performance tool for detecting gene split and merge events between
two genome annotations using DIAMOND BLASTP with optional clustering analysis.

Main Components:
    - analyzer: Gene structure analysis and BBH detection
    - clustering: DIAMOND clustering functionality
    - utils: DIAMOND utility functions
    - core: Main workflow orchestration
    - cli_clustering: Standalone clustering CLI

Example Usage:
    >>> from gene_split_merge import DetectGeneSplitMerge
    >>> workflow = DetectGeneSplitMerge(
    ...     ref_gff="reference.gff3",
    ...     ref_proteins="reference_proteins.fasta",
    ...     upd_gff="updated.gff3",
    ...     upd_proteins="updated_proteins.fasta",
    ...     output_dir="results/"
    ... )
    >>> splits, merges = workflow.run_complete_workflow()
"""

__version__ = "1.5.0"
__author__ = "ISMIB"
__license__ = "MIT"

# Import main classes and functions
from .analyzer import (
    Gene,
    BlastHit,
    GFFParser,
    BlastAnalyzer,
    GeneStructureAnalyzer,
    ResultsExporter
)

from .clustering import (
    ClusterParser,
    DiamondClusterer
)

from .utils import (
    DiamondDatabaseManager,
    DiamondOutputParser,
    DiamondAlignmentAnalyzer,
    DiamondWorkflowHelper
)

from .core import DetectGeneSplitMerge

# Define public API
__all__ = [
    # Main workflow
    'DetectGeneSplitMerge',

    # Core analysis classes
    'Gene',
    'BlastHit',
    'GFFParser',
    'BlastAnalyzer',
    'GeneStructureAnalyzer',
    'ResultsExporter',

    # Clustering classes
    'ClusterParser',
    'DiamondClusterer',

    # Utility classes
    'DiamondDatabaseManager',
    'DiamondOutputParser',
    'DiamondAlignmentAnalyzer',
    'DiamondWorkflowHelper',
]
