# PAVprot Pipeline Architecture

> **Generated:** 2026-02-02
> **Purpose:** Comprehensive documentation of module connections, data flow, and pipeline structure

---

## Overview

**PAVprot** is a Presence/Absence Variation (PAV) protein analysis pipeline that analyzes gene mapping relationships between old and new genome annotations. It integrates GffCompare tracking data, DIAMOND BLASTP alignments, and InterProScan domain annotations.

---

## Module Summary

| Module | Purpose | Key Classes/Functions |
|--------|---------|----------------------|
| **pavprot.py** | Main pipeline orchestrator | PAVprot, DiamondRunner |
| **bidirectional_best_hits.py** | Reciprocal best hit analysis | BidirectionalBestHits |
| **pairwise_align_prot.py** | Local sequence alignment | local_alignment_similarity() |
| **mapping_multiplicity.py** | Multi-mapping detection | detect_multiple_mappings() |
| **parse_interproscan.py** | Domain annotation parsing | InterProParser |
| **gsmc.py** | Scenario classification | get_cdi_genes(), detect_*() |
| **tools_runner.py** | External tools interface | ToolsRunner |

---

## Core Modules

### 1. pavprot.py - Main Pipeline Orchestrator

**Purpose:** Central hub that coordinates all pipeline stages.

**Key Classes:**
- `PAVprot` - Main class with methods for:
  - `parse_tracking()` - Parse GffCompare tracking files
  - `compute_all_metrics()` - Single-pass metric computation
  - `load_interproscan_data()` - Load InterProScan TSV files
  - `load_gff()` - Parse GFF3 files

- `DiamondRunner` - Manages DIAMOND BLASTP execution
  - `diamond_blastp()` - Forward search (query→reference)
  - `diamond_blastp_reverse()` - Reverse search
  - `run_bidirectional()` - Run both for BBH

**Dependencies:**
- `parse_interproscan.py`
- `mapping_multiplicity.py`
- `bidirectional_best_hits.py`
- `pairwise_align_prot.py`
- `gsmc.py`

---

### 2. bidirectional_best_hits.py - Ortholog Identification

**Purpose:** Identifies reciprocal best hits (BBH) - strong ortholog candidates.

**Key Classes:**
- `BlastHit` - Dataclass for alignment hits
- `BidirectionalBestHits` - Main analyzer
  - `find_bbh()` - Find reciprocal best hits
  - `classify_relationships()` - bbh_ortholog, best_hit_only, multi_hit

**Input:** DIAMOND TSV.gz files (forward + reverse)
**Output:** `*_bbh_results.tsv`

---

### 3. pairwise_align_prot.py - Local Sequence Alignment

**Purpose:** Biopython local alignment for identity/coverage metrics.

**Key Functions:**
- `local_alignment_similarity()` - Perform alignment
- `calculate_alignment_stats()` - BLAST-style statistics
- `read_all_sequences()` - Load FASTA

**Dependencies:** Biopython (Bio.Align, SeqIO)

---

### 4. mapping_multiplicity.py - Multi-Gene Mapping Detection

**Purpose:** Detects 1-to-many and many-to-1 relationships.

**Output Files:**
1. `*_old_to_multiple_new.tsv` - 1-to-many summary
2. `*_old_to_multiple_new_detailed.tsv` - Detailed pairs
3. `*_new_to_multiple_old.tsv` - Many-to-1 summary
4. `*_new_to_multiple_old_detailed.tsv` - Detailed pairs
5. `*_multiple_mappings_summary.txt` - Statistics

---

### 5. parse_interproscan.py - Domain Annotation Parsing

**Purpose:** Parses InterProScan TSV and maps domains to genes.

**Key Class:** `InterProParser`
- `parse_tsv()` - Parse raw 15-column format
- `total_ipr_length()` - Calculate domain coverage
- `transcript_to_geneMap()` - Build transcript→gene mappings

**Handles:** NCBI and VEuPathDB GFF3 formats

---

### 6. gsmc.py - Gene Mapping Scenario Classification

**Purpose:** Exclusive scenario detection (E, A, B, J, CDI, G, H).

**Scenarios:**
| Code | Name | Definition |
|------|------|------------|
| E | 1:1 orthologs | old→1 new AND new→1 old |
| A | 1:2N | old→exactly 2 new, NOT CDI |
| J | 1:2N+ | old→3+ new, NOT CDI |
| B | N:1 | new→2+ old, NOT CDI |
| CDI | Complex | Both sides multi-mapping |
| G | Unmapped old | Old gene not mapped |
| H | Unmapped new | New gene not mapped |

**Key Functions:**
- `get_cdi_genes()` - Identify cross-mapping
- `detect_one_to_one_orthologs()` - Scenario E
- `detect_one_to_many()` - Scenario A
- `detect_many_to_one()` - Scenario B
- `detect_complex_one_to_many()` - Scenario J

---

## Data Flow Diagram

```
Input Files
├── GffCompare Tracking (.tracking)  ──→ pavprot.parse_tracking()
├── Old GFF3                         ──→ pavprot.load_gff()
├── New GFF3                         ──┘
├── Old FASTA (.faa)                 ──→ DiamondRunner
├── New FASTA (.faa)                 ──→ DiamondRunner
├── Liftoff GFF3                     ──→ pavprot.load_extra_copy_numbers()
└── InterProScan TSV(s)              ──→ InterProParser.parse_tsv()

                            ↓
                    pavprot.py Main()
                            ↓
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
    Tracking Data      DIAMOND/BBH         InterProScan
    (core mapping)      (similarity)         (domains)
        ↓                   ↓                   ↓
        └───────────────────┼───────────────────┘
                            ↓
            PAVprot.compute_all_metrics()
                            ↓
            write_results() → TSV (transcript-level)
                            ↓
            ┌───────────────┬───────────────┐
            ↓               ↓               ↓
        Multi-mapping  Gene-level      Excel Export
        detection      aggregation      (11 sheets)
            ↓               ↓               ↓
        Summary        Gene-level TSV  .xlsx workbook
        files          + scenarios

Output Files (pavprot_out/)
├── *_diamond_blastp.tsv              # Transcript-level
├── *_diamond_blastp.xlsx             # Excel workbook (11 sheets)
├── *_gene_level.tsv
├── *_old_to_multiple_new*.tsv
├── *_new_to_multiple_old*.tsv
├── *_multiple_mappings_summary.txt
├── *_domain_distribution.tsv
├── *_total_ipr_length.tsv
└── compareprot_out/
    ├── *_diamond_blastp_*.tsv.gz
    └── *_bbh_results.tsv
```

---

## Module Dependency Graph

```
pavprot.py (main orchestrator)
├── parse_interproscan.py
├── mapping_multiplicity.py
├── bidirectional_best_hits.py
├── pairwise_align_prot.py
└── gsmc.py

plot/ (visualization)
├── config.py (shared configuration)
├── utils.py (shared utilities)
├── plot_ipr_comparison.py
├── plot_ipr_advanced.py
├── plot_ipr_gene_level.py
├── plot_ipr_proportional_bias.py
├── plot_ipr_shapes.py
└── plot_domain_comparison.py

Standalone:
├── parse_liftover_extra_copy_number.py
├── inconsistent_genes_transcript_IPR_PAV.py
├── synonym_mapping_parse.py
└── synonym_mapping_summary.py
```

---

## Plot Modules

### Infrastructure
- **plot/config.py** - Matplotlib/seaborn setup, color palettes
- **plot/utils.py** - Data loading, filtering, validation

### Visualization
| Module | Purpose |
|--------|---------|
| `plot_ipr_comparison.py` | Scatter plots: query vs reference IPR lengths |
| `plot_ipr_advanced.py` | Log-log scale, Bland-Altman, CDF, contour density |
| `plot_ipr_gene_level.py` | Gene-level aggregated visualization |
| `plot_ipr_proportional_bias.py` | Bias detection, fold-change analysis |
| `plot_ipr_shapes.py` | Violin plots, density distributions |
| `plot_domain_comparison.py` | Before/after liftover comparison |

---

## CLI Options (pavprot.py)

### Core
```bash
--gff-comp FILE      # GffCompare tracking file (required)
--gff FILE           # GFF3 files: "old.gff,new.gff"
--output-dir DIR     # Output directory (default: pavprot_out)
--output-prefix STR  # Output filename prefix
```

### Alignment
```bash
--run-diamond        # Run DIAMOND BLASTP
--prot FILE          # Protein FASTA files: "old.faa,new.faa"
--run-bbh            # Enable bidirectional best hit
--run-pairwise       # Enable Biopython local alignment
```

### InterProScan
```bash
--run-interproscan   # Run InterProScan
--interproscan-out   # Existing InterProScan results: "old.tsv,new.tsv"
```

### Filtering
```bash
--class-code CODES   # Filter by class codes, space-separated (e.g., = c k m n j e)
--filter-exact-match # Only exact matches
--filter-exclusive-1to1  # Only 1:1 orthologs
```

### Output
```bash
--output-excel       # Export to Excel workbook (default: True)
--no-output-excel    # Disable Excel export
```

---

## Output Columns

### Main Output (transcript-level)
- `old_gene`, `old_transcript`, `new_gene`, `new_transcript`
- `class_code`, `exons`, `class_type_transcript`, `class_type_gene`
- `emckmnj`, `emckmnje` - Binary class code flags
- `old_multi_new`, `new_multi_old` - Mapping multiplicity

### Optional (DIAMOND)
- `pident`, `qcovhsp`, `scovhsp`
- `identical_aa`, `mismatched_aa`, `indels_aa`

### Optional (BBH)
- `is_bbh`, `bbh_avg_pident`, `bbh_avg_coverage`

### Optional (Pairwise)
- `pairwise_identity`, `pairwise_coverage_old`, `pairwise_coverage_new`

### Optional (InterProScan)
- `query_total_ipr_domain_length`, `ref_total_ipr_domain_length`

### Gene-Level Output
- All above plus: `scenario`, `mapping_type`
- `old_transcripts`, `new_transcripts` (comma-separated)

---

## File Structure

```
gene_pav/
├── Core Pipeline
│   ├── pavprot.py                    # Main orchestrator
│   ├── tools_runner.py               # External tools interface
│   ├── gsmc.py                       # Scenario classification
│   ├── mapping_multiplicity.py       # Multi-mapping detection
│   ├── bidirectional_best_hits.py    # BBH analysis
│   ├── pairwise_align_prot.py        # Local alignment
│   ├── parse_interproscan.py         # Domain parsing
│   └── synonym_mapping_summary.py    # Statistics
│
├── plot/                             # Visualization
│   ├── config.py, utils.py           # Infrastructure
│   └── plot_*.py                     # Plotting modules
│
├── project_scripts/                  # Examples
│   ├── config.yaml.template          # Configuration template
│   └── run_pipeline.py               # Workflow orchestrator
│
├── test/                             # Tests
├── docs/                             # Documentation
├── scripts/                          # Automation
│   └── pre_release_check.sh
└── config.yaml                       # Pipeline config
```

---

*See also: `docs/CODE_REVIEW_REPORT.md` for detailed code analysis*
