# PAVprot Codebase Restructuring Report

**Generated:** 2026-01-09
**Updated:** 2026-01-09 (Post-Consolidation)
**Status:** COMPLETED

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Final Directory Structure](#final-directory-structure)
3. [Script Dependency Map](#script-dependency-map)
4. [Output File Traceability](#output-file-traceability)
5. [Redundancy Analysis](#redundancy-analysis)
6. [Migration Log](#migration-log)
7. [Files Archived](#files-archived)

---

## Executive Summary

### Restructuring Status: COMPLETED

| Category | Before | After | Action Taken |
|----------|--------|-------|--------------|
| Core Scripts | 5 (scattered) | 5 (in core/) | Copied to core/ module |
| Analysis Scripts | 3 | 3 | Unchanged |
| Plot Scripts | 9 (3 redundant) | 6 | Moved backups to archive/ |
| Test Scripts | 5 | 5 | Unchanged |
| Utility Scripts | 2 | 2 | Unchanged |
| Dev/Legacy Scripts | 3 | 0 | Moved to archive/legacy_scripts/ |
| Documentation Files | 18 (8 redundant) | 10 | Moved redundant to archive/old_docs/ |
| Output Directories | 6 (scattered) | 2 | Consolidated to output/ and archive/ |

### Final Disk Usage

| Directory | Content | Size |
|-----------|---------|------|
| `output/latest/` | Production outputs (IPR, mappings) | ~36 MB |
| `test/output/` | Test outputs (pavprot_out, bbh_test) | ~300 KB |
| `archive/old_outputs/` | All archived outputs | ~65 MB |
| `archive/legacy_scripts/` | Legacy/backup scripts | ~100 KB |
| `archive/old_docs/` | Redundant documentation | ~100 KB |

---

## Final Directory Structure

```
gene_pav/
├── pavprot.py                           # MAIN ORCHESTRATOR (70 KB)
├── parse_interproscan.py                # Core module - IPR parsing
├── bidirectional_best_hits.py           # Core module - BBH analysis
├── mapping_multiplicity.py          # Core module - 1:N detection
├── pairwise_align_prot.py               # Core module - protein alignment
├── README.md                            # Quick start guide
│
├── core/                                # CORE MODULES (packaged)
│   ├── __init__.py
│   ├── parse_interproscan.py
│   ├── bidirectional_best_hits.py
│   ├── mapping_multiplicity.py
│   └── pairwise_align_prot.py
│
├── analysis/                            # DOWNSTREAM ANALYSIS (3 scripts)
│   ├── gsmc.py     # Scenario classification
│   ├── inconsistent_genes_transcript_IPR_PAV.py
│   └── synonym_mapping_summary.py       # Statistics generator
│
├── plot/                                # VISUALIZATION (6 active scripts)
│   ├── plot_ipr_comparison.py
│   ├── plot_ipr_advanced.py
│   ├── plot_ipr_gene_level.py
│   ├── plot_ipr_shapes.py
│   ├── plot_ipr_proportional_bias.py
│   └── plot_domain_comparison.py
│
├── utils/                               # STANDALONE UTILITIES (2 scripts)
│   ├── parse_liftover_extra_copy_number.py
│   └── synonym_mapping_parse.py
│
├── test/                                # TEST SUITE
│   ├── test_*.py                        # Test scripts
│   ├── data/                            # Test fixtures
│   │   └── mock_fasta/
│   └── output/                          # Test outputs
│       ├── pavprot_out/                 # Main test outputs
│       └── bbh_test/                    # BBH test outputs
│
├── docs/                                # DOCUMENTATION (cleaned)
│   ├── ARCHITECTURE.md
│   ├── SCENARIOS.md
│   ├── IMPLEMENTATION_ROADMAP.md
│   ├── OUTPUT_FORMAT.md
│   ├── SCENARIO_IMPLEMENTATION.md
│   ├── GENE_LEVEL_AGGREGATION.md
│   └── RESTRUCTURE_REPORT.md            # This file
│
├── output/                              # PRODUCTION OUTPUT
│   └── latest/                          # Most recent run (36 MB)
│       ├── synonym_mapping_liftover_gffcomp.tsv
│       ├── *_total_ipr_length.tsv
│       └── *_domain_distribution.tsv
│
├── examples/                            # EXAMPLE DATA
│
└── archive/                             # ARCHIVED FILES
    ├── backup_before_overlap_fix/       # Old code versions
    ├── legacy_scripts/                  # Backup/legacy scripts
    │   ├── plot_ipr_comparison_bk.py
    │   ├── plot_ipr_comparison.00.py
    │   ├── plot_ipr_advanced_bk.py
    │   ├── check_plot_logic.py
    │   ├── standalone_bed_coverage_test.py
    │   └── parse_interproscan_github_version.py
    ├── old_docs/                        # Redundant documentation
    └── old_outputs/                     # Historical outputs
        ├── interproscan_test_dec18/
        ├── test_new_output_dec19/
        ├── misc_test_dec18/
        ├── pavprot_output_scenario12/
        ├── scenarios_A_B_CDI_E_F_G_H_J_output/
        └── test_plot_out/
```

---

## Script Dependency Map

### Core Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                         pavprot.py                               │
│                    (MAIN ORCHESTRATOR)                           │
├─────────────────────────────────────────────────────────────────┤
│  IMPORTS:                                                        │
│  ├── from parse_interproscan import InterProParser, run_interproscan
│  ├── from detect_one2many_mappings import detect_multiple_mappings
│  ├── from bidirectional_best_hits import BidirectionalBestHits, enrich_pavprot_with_bbh
│  └── from pariwise_align_prot import local_alignment_similarity, read_all_sequences
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ parse_          │  │ bidirectional_  │  │ detect_         │
│ interproscan.py │  │ best_hits.py    │  │ one2many_       │
│                 │  │                 │  │ mappings.py     │
│ STANDALONE: Yes │  │ STANDALONE: Yes │  │ STANDALONE: Yes │
│ DEPENDENCIES:   │  │ DEPENDENCIES:   │  │ DEPENDENCIES:   │
│ - pandas        │  │ - pandas        │  │ - pandas        │
│ - subprocess    │  │ - gzip          │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │
         ▼
┌─────────────────┐
│ pariwise_       │
│ align_prot.py   │
│                 │
│ STANDALONE: Yes │
│ DEPENDENCIES:   │
│ - Bio.Align     │
│ - Bio.SeqIO     │
└─────────────────┘
```

### Downstream Analysis

```
┌─────────────────────────────────────────────────────────────────┐
│                 synonym_mapping_liftover_gffcomp.tsv             │
│                        (PAVPROT OUTPUT)                          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ detect_advanced │   │ synonym_mapping │   │ inconsistent_   │
│ _scenarios.py   │   │ _summary.py     │   │ genes_*.py      │
│                 │   │                 │   │                 │
│ INPUT:          │   │ INPUT:          │   │ INPUT:          │
│ - pavprot TSV   │   │ - pavprot TSV   │   │ - pavprot TSV   │
│ - GFF files     │   │                 │   │   (with IPR)    │
│ - FASTA files   │   │ OUTPUT:         │   │                 │
│                 │   │ - stdout stats  │   │ OUTPUT:         │
│ OUTPUT:         │   │                 │   │ - *_inconsist-  │
│ - scenario_*.tsv│   │                 │   │   ent_genes.tsv │
│ - detection_    │   │                 │   │ - *.png plots   │
│   summary.txt   │   │                 │   │                 │
└─────────────────┘   └─────────────────┘   └─────────────────┘
```

### Visualization Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                 synonym_mapping_liftover_gffcomp.tsv             │
│                  (REQUIRES IPR COLUMNS)                          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
    ┌───────────────┬───────────┼───────────┬───────────────┐
    ▼               ▼           ▼           ▼               ▼
┌─────────┐   ┌─────────┐  ┌─────────┐  ┌─────────┐   ┌─────────┐
│plot_ipr_│   │plot_ipr_│  │plot_ipr_│  │plot_ipr_│   │plot_ipr_│
│comparis-│   │advanced │  │gene_    │  │shapes   │   │propor-  │
│on.py    │   │.py      │  │level.py │  │.py      │   │tional_  │
│         │   │         │  │         │  │         │   │bias.py  │
│ OUTPUT: │   │ OUTPUT: │  │ OUTPUT: │  │ OUTPUT: │   │ OUTPUT: │
│*_by_    │   │*_advanc-│  │*_gene_  │  │*_shapes │   │*_bias   │
│class_   │   │ed.png   │  │level.png│  │.png     │   │.png     │
│type.png │   │         │  │         │  │         │   │         │
│*_hexbin │   │         │  │         │  │         │   │         │
│*_quadr- │   │         │  │         │  │         │   │         │
│ants.png │   │         │  │         │  │         │   │         │
└─────────┘   └─────────┘  └─────────┘  └─────────┘   └─────────┘

┌─────────────────────────────────────────────────────────────────┐
│                 InterProScan TSV Files                           │
│             (ref_interproscan.tsv, query_interproscan.tsv)       │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
                        ┌─────────────┐
                        │ plot_domain_│
                        │ comparison  │
                        │ .py         │
                        │             │
                        │ OUTPUT:     │
                        │ *_domain_   │
                        │ comp.png    │
                        └─────────────┘
```

---

## Output File Traceability

### Primary Output Files

| Output File | Generated By | Input Required | Description |
|-------------|--------------|----------------|-------------|
| `synonym_mapping_liftover_gffcomp.tsv` | `pavprot.py` | tracking, GFF | Main gene mapping output |
| `*_total_ipr_length.tsv` | `pavprot.py` | InterProScan TSV | IPR domain lengths per gene |
| `*_domain_distribution.tsv` | `pavprot.py` | InterProScan TSV | Domain details per transcript |
| `*_ref_to_multiple_query.tsv` | `mapping_multiplicity.py` | pavprot output | 1:N mappings |
| `*_query_to_multiple_ref.tsv` | `mapping_multiplicity.py` | pavprot output | N:1 mappings |
| `*_multiple_mappings_summary.txt` | `mapping_multiplicity.py` | pavprot output | Statistics summary |

### Scenario Output Files

| Scenario File | Generated By | Description |
|---------------|--------------|-------------|
| `scenario_E_1to1_orthologs.tsv` | `gsmc.py` | True 1:1 orthologs |
| `scenario_A_1toN_mappings.tsv` | `gsmc.py` | One ref → multiple queries |
| `scenario_B_Nto1_mappings.tsv` | `gsmc.py` | Multiple refs → one query |
| `scenario_J_complex_1toN_mappings.tsv` | `gsmc.py` | One ref → 3+ queries |
| `scenario_CDI_cross_mappings.tsv` | `gsmc.py` | Cross-mapping groups |
| `scenario_F_positional_swaps.tsv` | `gsmc.py` | Adjacent gene order inversions |
| `scenario_G_unmapped_ref_genes.tsv` | `gsmc.py` | Ref genes without query matches |
| `scenario_H_unmapped_query_genes.tsv` | `gsmc.py` | Query genes without ref matches |
| `detection_summary.txt` | `gsmc.py` | Scenario counts summary |

### Plot Output Files

| Plot Pattern | Generated By | Input |
|--------------|--------------|-------|
| `*_by_class_type.png` | `plot_ipr_comparison.py` | pavprot TSV (with IPR) |
| `*_density_hexbin.png` | `plot_ipr_comparison.py` | pavprot TSV (with IPR) |
| `*_loglog_scale.png` | `plot_ipr_comparison.py` | pavprot TSV (with IPR) |
| `*_quadrants.png` | `plot_ipr_comparison.py` | pavprot TSV (with IPR) |
| `*_quadrants_gene_level.png` | `plot_ipr_comparison.py` | pavprot TSV (with IPR) |
| `*_inconsistent_genes_summary_plot.png` | `plot_ipr_comparison.py` | pavprot TSV (with IPR) |
| `*_gene_level.png` | `plot_ipr_gene_level.py` | pavprot TSV (with IPR) |
| `*_shapes.png` | `plot_ipr_shapes.py` | pavprot TSV (with IPR) |
| `*_bias.png` | `plot_ipr_proportional_bias.py` | pavprot TSV (with IPR) |
| `*_domain_comp.png` | `plot_domain_comparison.py` | InterProScan TSV |

---

## Redundancy Analysis

### Redundant Python Scripts

| File | Status | Reason | Recommendation |
|------|--------|--------|----------------|
| `plot/plot_ipr_comparison_bk.py` | REDUNDANT | Backup of active script | REMOVE |
| `plot/plot_ipr_comparison.00.py` | REDUNDANT | Old version | REMOVE |
| `plot/plot_ipr_advanced_bk.py` | REDUNDANT | Backup of active script | REMOVE |
| `dev/parse_interproscan_github_version.py` | LEGACY | Old version | ARCHIVE |
| `dev/check_plot_logic.py` | DEBUG | Development utility | ARCHIVE |
| `dev/standalone_bed_coverage_test.py` | LEGACY | Superseded by tests | ARCHIVE |
| `backup_before_overlap_fix/pavprot.py` | BACKUP | Old version | ARCHIVE |
| `backup_before_overlap_fix/parse_interproscan.py` | BACKUP | Old version | ARCHIVE |

### Redundant Documentation

| File | Status | Overlaps With | Recommendation |
|------|--------|---------------|----------------|
| `docs/INTERPROSCAN_INTEGRATION_COMPLETE.md` | REDUNDANT | COMPLETE_INTEGRATION_GUIDE.md | REMOVE |
| `docs/INTERPROSCAN_INTEGRATION_SUMMARY.md` | REDUNDANT | COMPLETE_INTEGRATION_GUIDE.md | REMOVE |
| `docs/INTERPROSCAN_UPDATE_SUMMARY.md` | REDUNDANT | COMPLETE_INTEGRATION_GUIDE.md | REMOVE |
| `docs/INTERPROSCAN_SIMPLIFICATION_SUMMARY.md` | REDUNDANT | IMPROVEMENT_NOTES.md | REMOVE |
| `docs/FINAL_INTEGRATION_CONFIRMATION.md` | REDUNDANT | Confirmation only | REMOVE |
| `tmp_docs/OUTPUT_FILES_UPDATED.md` | REDUNDANT | SYNONYM_MAPPING_OUTPUT_GUIDE.md | REMOVE |
| `tmp_docs/FINAL_SUMMARY.txt` | TEMP | Development notes | REMOVE |
| `tmp_docs/OUTPUT_FILES_SUMMARY.txt` | TEMP | Development notes | REMOVE |
| `tmp_docs/TEST_RESULTS_SUMMARY.txt` | TEMP | Test output | REMOVE |
| `test/uolocal/dev_workspace/gene_pav/COVERAGE_CALCULATION_README.md` | ORPHAN | Misplaced file | MOVE to docs/ |

### Redundant Output Directories

| Directory | Size | Reason | Recommendation |
|-----------|------|--------|----------------|
| `old_output_backup/` | 420 KB | Superseded by new_pavprot_output | REMOVE |
| `pavprot_output_scenario12/` | 35 MB | Old run output | ARCHIVE |
| `test/plot_out/` | 29 MB | Test artifacts (regenerable) | ARCHIVE |
| `new_pavprot_output/scenarios_CDI_F_G_H_output/` | ~1 MB | Superseded by A_B_CDI_E_F_G_H_J | REMOVE |
| `new_pavprot_output/scenarios_CDI_E_F_G_H_output/` | ~1 MB | Superseded by A_B_CDI_E_F_G_H_J | REMOVE |
| `new_pavprot_output/scenarios_A_B_CDI_E_F_G_H_output/` | ~1 MB | Superseded by A_B_CDI_E_F_G_H_J | REMOVE |

---

## Migration Log

### Actions Completed (2026-01-09)

| Action | Source | Destination | Status |
|--------|--------|-------------|--------|
| Created directories | - | core/, archive/, examples/, output/ | ✅ |
| Created core package | Core scripts | core/ | ✅ |
| Archived backup scripts | plot/*_bk.py, plot/*.00.py | archive/legacy_scripts/ | ✅ |
| Archived legacy scripts | dev/ | archive/legacy_scripts/ | ✅ |
| Archived old docs | docs/INTERPROSCAN_*.md | archive/old_docs/ | ✅ |
| Archived old outputs | pavprot_output_scenario12/ | archive/old_outputs/ | ✅ |
| Archived test plots | test/plot_out/ | archive/old_outputs/test_plot_out/ | ✅ |
| Moved test data | output/pavprot_out/ | archive/old_outputs/interproscan_test_dec18/ | ✅ |
| Moved redundant test | test/output/test_new_output/ | archive/old_outputs/test_new_output_dec19/ | ✅ |
| Moved misc test files | output/test_output_*.tsv, allvall.tsv | archive/old_outputs/misc_test_dec18/ | ✅ |
| Renamed production output | output/new_pavprot_output/ | output/latest/ | ✅ |
| Removed redundant dirs | old_output_backup/, tmp_docs/ | (deleted) | ✅ |

---

## Files Archived

### archive/old_outputs/

| Directory | Content | Original Location |
|-----------|---------|-------------------|
| `interproscan_test_dec18/` | InterProScan test outputs | output/pavprot_out/ |
| `test_new_output_dec19/` | Test run outputs | test/output/test_new_output/ |
| `misc_test_dec18/` | Misc test files (allvall.tsv, etc.) | output/ |
| `pavprot_output_scenario12/` | Old scenario run | root |
| `scenarios_A_B_CDI_E_F_G_H_J_output/` | Scenario outputs | new_pavprot_output/ |
| `test_plot_out/` | Test plot artifacts | test/ |

### archive/legacy_scripts/

| Script | Reason Archived |
|--------|-----------------|
| `plot_ipr_comparison_bk.py` | Backup of active script |
| `plot_ipr_comparison.00.py` | Old version |
| `plot_ipr_advanced_bk.py` | Backup of active script |
| `check_plot_logic.py` | Debug/development utility |
| `standalone_bed_coverage_test.py` | Legacy test script |
| `parse_interproscan_github_version.py` | Old version |

### archive/old_docs/

Redundant documentation files moved from docs/

---

## Summary

### Restructuring Complete

- **Directories reduced:** 32 → 27
- **Clear separation:** Production outputs in `output/latest/`, test outputs in `test/output/`, archives in `archive/`
- **No duplicate directory names:** Eliminated conflicting `pavprot_out` directories
- **Test data separated:** All test artifacts moved to appropriate locations

### Key Locations

| Purpose | Location |
|---------|----------|
| Production outputs | `output/latest/` |
| Test outputs | `test/output/pavprot_out/`, `test/output/bbh_test/` |
| Historical outputs | `archive/old_outputs/` |
| Legacy scripts | `archive/legacy_scripts/` |
| Active documentation | `docs/` |

---

*Report generated and updated by Claude Code*
