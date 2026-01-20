"""
PAVprot Pipeline - Gene Annotation Presence/Absence Variation Analysis

A comprehensive pipeline for analyzing gene mapping relationships between
reference and query genome annotations, integrating GffCompare tracking data,
DIAMOND BLASTP alignments, and InterProScan domain annotations.

Modules:
    - pavprot: Main pipeline orchestration
    - parse_interproscan: InterProScan output parsing
    - gsmc: Gene Synteny Mapping Classifier (scenario classification)
    - mapping_multiplicity: 1:N and N:1 mapping detection
    - bidirectional_best_hits: BBH analysis
    - pairwise_align_prot: Protein sequence alignment
    - tools_runner: External tools integration
"""

__version__ = "1.0.0"
__author__ = "PAVprot Development Team"
