# PAVprot Pipeline - Individual Script Assessment Report

> **Date:** 2026-01-19
> **Branch:** main
> **Scope:** Complete one-by-one assessment of all scripts per Priority Task 1

---

## Assessment Summary

| Category | Total Files | OK | Issues | Critical |
|----------|-------------|-----|--------|----------|
| Core Pipeline (root) | 11 | 9 | 1 | 1 |
| Plot Modules (plot/) | 7 | 7 | 0 | 0 |
| Project Scripts | 6 | 6 | 0 | 0 |
| Test Files | 5 | 2 | 2 | 1 |
| **Total** | **29** | **24** | **3** | **2** |

---

## 1. Core Pipeline Scripts (Root Level)

### 1.1 pavprot.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 1,841 |
| **Status** | OK |
| **Purpose** | Main pipeline orchestrator |

**Classes:**
- `PAVprot` - Core analysis class with static/class methods
- `DiamondRunner` - DIAMOND BLASTP execution wrapper

**Key Methods:**
- `fasta2dict()` - Parse FASTA files to dictionary
- `load_gff()` - Parse GFF3 for protein/gene mapping
- `parse_tracking()` - Parse gffcompare tracking files
- `filter_multi_transcripts()` - Consolidate multi-transcript data
- `load_interproscan_data()` - Load IPR domain data
- `enrich_interproscan_data()` - Add IPR lengths to data

**Internal Imports:**
```python
from parse_interproscan import InterProParser
from mapping_multiplicity import detect_multiple_mappings
from bidirectional_best_hits import identify_bbh
from pairwise_align_prot import align_proteins
from gsmc import classify_scenarios  # Renamed from detect_advanced_scenarios
```

**Note:** File names updated in v0.2.0 (see Section 1.5)

**Assessment:** Well-structured main module with proper CLI, docstrings, and error handling.

---

### 1.2 gsmc.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 1,344 |
| **Status** | OK |
| **Purpose** | Gene annotation mapping classification |

**Key Function:** `classify_scenarios(data_dict, ...)`

**Scenario Detection:**
| Code | Description | Detection Logic |
|------|-------------|-----------------|
| E | 1:1 orthologs | Single ref → single query |
| A | 1:N mapping | One ref → multiple queries |
| B | N:1 mapping | Multiple refs → one query |
| J | Complex 1:N | One ref → 3+ queries |
| CDI | Cross-mapping | Bidirectional many-to-many |
| F | Positional swaps | Same region, swapped genes |
| G | Unmapped ref | Reference with no query match |
| H | Unmapped query | Query with no reference match |

**Assessment:** Comprehensive biological scenario classification with detailed logging.

---

### 1.3 parse_interproscan.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 669 |
| **Status** | OK |
| **Purpose** | InterProScan TSV parsing |

**Class:** `InterProParser`

**Key Methods:**
- `parse_tsv()` - Parse InterProScan 14-column TSV
- `domain_distribution()` - Generate domain statistics DataFrame
- `total_ipr_length()` - Calculate merged IPR domain lengths
- `_calculate_interval_coverage()` - Merge overlapping intervals

**Output Files Generated:**
1. `*_domain_distribution.tsv`
2. `*_total_ipr_length.tsv`

**Assessment:** Well-implemented with overlap-aware coverage calculation (prevents double-counting).

---

### 1.4 bidirectional_best_hits.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 524 |
| **Status** | OK |
| **Purpose** | Bidirectional Best Hit (BBH) analysis |

**Key Function:** `identify_bbh(diamond_forward, diamond_reverse, ...)`

**Algorithm:**
1. Parse forward DIAMOND BLASTP results (query → ref)
2. Parse reverse DIAMOND BLASTP results (ref → query)
3. Identify pairs where A's best hit is B AND B's best hit is A

**Output Columns Added:**
- `is_bbh` (boolean)
- `bbh_pident` (percent identity)
- `bbh_evalue` (e-value)
- `bbh_bitscore` (bitscore)

**Assessment:** Standard BBH implementation with proper tie-breaking by bitscore.

---

### 1.5 pairwise_align_prot.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 462 |
| **Status** | OK (filename typo) |
| **Purpose** | Protein sequence alignment |

**ISSUE:** Filename has typo
| Current | Should Be |
|---------|-----------|
| `pairwise_align_prot.py` | `pairwise_align_prot.py` |

**Key Function:** `align_proteins(ref_fasta, query_fasta, ...)`

**Features:**
- Uses Biopython's `pairwise2` module
- Calculates identity, similarity, gaps
- Supports BLOSUM62 matrix

**Assessment:** Functional but should rename file to fix typo.

---

### 1.6 inconsistent_genes_transcript_IPR_PAV.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 451 |
| **Status** | OK |
| **Purpose** | Detect IPR domain inconsistencies |

**Key Function:** `analyze_inconsistent_genes(df, ...)`

**Detection Logic:**
Identifies genes where different transcripts fall into different IPR presence/absence quadrants:
- Q1: Present in both (query + ref have IPR)
- Q2: Ref only (ref has IPR, query missing)
- Q3: Query only (query has IPR, ref missing)
- Q4: Absent in both

**Output:** Filtered DataFrame with inconsistency flags

**Assessment:** Useful for identifying problematic gene annotations.

---

### 1.7 parse_liftover_extra_copy_number.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 435 |
| **Status** | OK |
| **Purpose** | Parse Liftoff GFF for extra copies |

**Key Function:** `parse_extra_copy_numbers(liftoff_gff)`

**Extracts:**
- `extra_copy_number` attribute from Liftoff GFF
- Maps transcript IDs to copy numbers

**Assessment:** Properly handles Liftoff-specific GFF attributes.

---

### 1.8 mapping_multiplicity.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 219 |
| **Status** | OK |
| **Purpose** | Detect 1:N and N:1 mappings |

**Key Function:** `mapping_multiplicity(data_dict)`

**Output Columns Added:**
- `ref_to_query_count` - Number of queries per reference
- `query_to_ref_count` - Number of references per query
- `mapping_type` - "1:1", "1:N", "N:1", or "N:M"

**Assessment:** Simple but effective mapping type classification.

---

### 1.9 synonym_mapping_summary.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 84 |
| **Status** | OK |
| **Purpose** | Generate summary statistics |

**Key Function:** `generate_summary(input_tsv, output_prefix)`

**Statistics Generated:**
- Class code distribution
- Class type distribution
- Mapping type counts
- IPR domain statistics

**Assessment:** Utility script for quick data summaries.

---

### 1.10 synonym_mapping_parse.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 92 |
| **Status** | **CRITICAL - BROKEN** |
| **Purpose** | Unknown (corrupted file) |

**CRITICAL ERRORS:**

1. **IndentationError at line 59:**
   ```
   IndentationError: unindent does not match any outer indentation level
   ```

2. **Two scripts concatenated together:**
   | Section | Lines | Content |
   |---------|-------|---------|
   | Script 1 | 1-57 | Incomplete parsing script |
   | Script 2 | 59-93 | Different script with wrong indentation |

3. **Bugs in Script 1:**
   - Line 3: Unused import `from curses import start_color`
   - Line 27: Syntax error `df.groupby["GCF_013085055.1_gene"]` (brackets not parentheses)
   - Line 28: References undefined "length" column

**RECOMMENDATION:** Delete this file entirely or rewrite from scratch.

---

### 1.11 __init__.py (root)

| Attribute | Value |
|-----------|-------|
| **Lines** | 0 (empty) |
| **Status** | OK |
| **Purpose** | Package marker |

**Assessment:** Empty is acceptable. Could add docstring and `__all__` exports.

---

## 2. Plot Modules (plot/)

### 2.1 plot_ipr_comparison.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 839 |
| **Status** | OK |
| **Purpose** | Main IPR comparison visualizations |

**Functions:**
- `load_pavprot_data()` - Load and preprocess data (different from other plots)
- `plot_scatter_comparison()` - Query vs reference scatter
- `plot_density_heatmap()` - 2D density visualization
- `plot_class_code_breakdown()` - Per-class distribution
- `plot_emckmnj_comparison()` - emckmnj flag analysis

**Output Files:** Multiple PNG plots with `_comparison` suffix

**Assessment:** Comprehensive plotting module with good visualization variety.

---

### 2.2 plot_ipr_proportional_bias.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 506 |
| **Status** | OK |
| **Purpose** | Proportional bias analysis |

**Functions:**
- `load_data()` - **DUPLICATED** (see note below)
- `plot_proportional_bias()` - Bias scatter plots
- `plot_ratio_distributions()` - Query/ref ratio histograms

**DUPLICATION:** Contains identical `load_data()` function as 3 other files.

---

### 2.3 plot_ipr_gene_level.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 354 |
| **Status** | OK |
| **Purpose** | Gene-level visualizations |

**Functions:**
- `load_data()` - **DUPLICATED**
- `plot_gene_level_scatter()` - Per-gene comparisons
- `plot_gene_distribution()` - Gene count histograms

**DUPLICATION:** Contains identical `load_data()` function.

---

### 2.4 plot_domain_comparison.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 344 |
| **Status** | OK |
| **Purpose** | Before/after liftover comparison |

**Functions:**
- `load_and_filter_longest_ipr()` - Filter for longest IPR domains
- `plot_comparison()` - Multi-panel comparison figure
- `plot_length_comparison_scatter()` - Same-protein scatter
- `plot_cumulative_distribution()` - CDF comparison

**Output Files:** `*_overview.png`, `*_scatter.png`, `*_cumulative.png`

**Assessment:** Well-structured before/after analysis module.

---

### 2.5 plot_ipr_shapes.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 324 |
| **Status** | OK |
| **Purpose** | Shape-encoded scatter plots |

**Functions:**
- `load_data()` - **DUPLICATED**
- `plot_scatter_with_shapes()` - Shape markers for query/ref
- `plot_separate_distributions()` - Side-by-side distributions

**Features:**
- Different markers for query (circles) vs reference (triangles)
- Color coding by class_code and class_type

**DUPLICATION:** Contains identical `load_data()` function.

---

### 2.6 plot_ipr_advanced.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 232 |
| **Status** | OK |
| **Purpose** | Advanced visualization techniques |

**Functions:**
- `load_data()` - **DUPLICATED**
- `plot_hexbin()` - Hexagonal binning
- `plot_contour()` - Contour density plots

**DUPLICATION:** Contains identical `load_data()` function.

---

### 2.7 __init__.py (plot/)

| Attribute | Value |
|-----------|-------|
| **Lines** | 0 (empty) |
| **Status** | OK |
| **Purpose** | Package marker |

---

### Plot Module Code Duplication Summary

**Duplicated Function:** `load_data(input_file)`
```python
def load_data(input_file):
    """Load PAVprot output TSV file"""
    df = pd.read_csv(input_file, sep='\t')
    return df
```

**Files with identical function:**
| File | Line |
|------|------|
| `plot_ipr_advanced.py` | 23 |
| `plot_ipr_shapes.py` | 19 |
| `plot_ipr_gene_level.py` | 20 |
| `plot_ipr_proportional_bias.py` | 20 |

**RECOMMENDATION:** Create `plot/utils.py` with shared functions.

---

## 3. Project Scripts (project_scripts/)

### 3.1 run_pipeline.py

| Attribute | Value |
|-----------|-------|
| **Lines** | ~1,900 |
| **Status** | OK (example script) |
| **Purpose** | Master downstream analysis orchestrator |

**Class:** `PipelineRunner`

**Task Methods (15+):**
- `run_psauron_analysis()`
- `run_plddt_analysis()`
- `run_plotting_suite()`
- `integrate_external_data()`
- etc.

**Hardcoded Paths (expected for examples):**
```python
CONFIG = {
    "psauron_ref": Path("/Users/sadik/Documents/projects/FungiDB/..."),
    "psauron_qry": Path("/Users/sadik/Documents/projects/FungiDB/..."),
    ...
}
```

**Assessment:** Comprehensive downstream analysis template. Keep separate from `pavprot.py` - serves different purpose.

---

### 3.2 run_emckmnje1_analysis.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 460 |
| **Status** | OK (example script) |
| **Purpose** | Filtered emckmnj=1 analysis |

**Imports:**
```python
from run_pipeline import PipelineRunner, CONFIG, find_latest_output
```

**Features:**
- Filters data for `emckmnj == 1` genes only
- Runs subset of pipeline tasks

**Assessment:** Good example of task filtering pattern.

---

### 3.3 analyze_fungidb_species.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 140 |
| **Status** | OK (example script) |
| **Purpose** | FungiDB species statistics |

**Hardcoded Paths:**
```python
PHYTO_LIST = Path("/Users/sadik/Documents/projects/data/disease_research_supported.csv")
GENE_STATS = Path("/Users/sadik/Documents/projects/data/fungidb_v68_gene_stats.tsv")
```

**Assessment:** Project-specific analysis script with expected hardcoded paths.

---

### 3.4 plot_ipr_1to1_comparison.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 295 |
| **Status** | OK |
| **Purpose** | 1:1 ortholog IPR comparison plots |

**Key Features:**
- Filters for scenario "E" (1:1 orthologs)
- Creates specialized comparison plots

**Assessment:** Focused visualization for 1:1 mapping analysis.

---

### 3.5 plot_oldvsnew_psauron_plddt.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 327 |
| **Status** | OK (example script) |
| **Purpose** | Psauron/pLDDT quality score comparison |

**Hardcoded Paths (lines 46-50):**
```python
PSAURON_REF = Path("/Users/sadik/Documents/projects/...")
PSAURON_QRY = Path("/Users/sadik/Documents/projects/...")
```

**Features:**
- Compares protein quality metrics
- Visualizes Psauron vs pLDDT correlation

---

### 3.6 plot_psauron_distribution.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 200 |
| **Status** | OK |
| **Purpose** | Psauron score distributions |

**Features:**
- Histogram and KDE plots
- Per-class_code breakdown

**Assessment:** Clean distribution visualization script.

---

## 4. Test Files (test/)

### 4.1 test_pavprot.py

| Attribute | Value |
|-----------|-------|
| **Lines** | ~400 |
| **Status** | **ISSUE - Import path** |
| **Purpose** | Core unit tests |

**ISSUE (Line 10):**
```python
from pavprot import PAVprot, DiamondRunner  # Will fail without path setup
```

**Test Classes:**
- `TestPAVprot` - Tests for PAVprot class methods
- `TestDiamondRunner` - Tests for DIAMOND execution
- `TestMainExecution` - Integration tests

**Test Methods:**
- `test_fasta2dict()`
- `test_load_gff()`
- `test_parse_tracking()`
- `test_filter_multi_transcripts()`
- `test_load_extra_copy_numbers()`
- `test_diamond_blastp()` (mocked)
- `test_enrich_blastp()`

**FIX NEEDED:**
```python
import sys
sys.path.insert(0, '..')  # Add this before imports
from pavprot import PAVprot, DiamondRunner
```

---

### 4.2 test_inconsistent_genes.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 143 |
| **Status** | OK |
| **Purpose** | Mock data generator |

**Note:** This is NOT a traditional test file - it generates mock data for testing the inconsistent genes analysis functionality.

**Output:** Creates `mock_data_inconsistent_genes.tsv` with:
- 4 gene pairs with inconsistent transcripts
- 5 gene pairs with consistent transcripts

**Assessment:** Useful test data generator, but filename suggests it's a test file.

---

### 4.3 test_bed_coverage.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 296 |
| **Status** | OK |
| **Purpose** | BED coverage calculation tests |

**Functions:**
- `calculate_total_coverage()` - Merge overlapping intervals
- `calculate_bed_coverage_from_file()` - File-based calculation
- `calculate_ipr_coverage_from_dataframe()` - DataFrame calculation
- `run_tests()` - 10 comprehensive tests

**Test Coverage:**
1. No overlaps
2. Complete overlap
3. Partial overlap
4. Multiple overlaps
5. Adjacent intervals
6. Empty list
7. Single interval
8. Unsorted intervals
9. All intervals merge
10. DataFrame-based calculation

**Assessment:** Well-written test suite with comprehensive edge cases.

---

### 4.4 test_bed_files.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 171 |
| **Status** | OK |
| **Purpose** | BED file-based tests |

**Import (Line 11):**
```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

**Tests:**
- `test_bed_file_1()` - No overlaps
- `test_bed_file_2()` - With overlaps
- `test_bed_file_3()` - Complex overlaps
- `test_total_coverage()` - Total without grouping

**Assessment:** Good integration tests using actual BED files.

---

### 4.5 test_all_outputs.py

| Attribute | Value |
|-----------|-------|
| **Lines** | 247 |
| **Status** | **CRITICAL - Hardcoded path** |
| **Purpose** | Integration output tests |

**CRITICAL ISSUE (Line 14):**
```python
sys.path.insert(0, '/Users/sadik/projects/github_prj/uolismib/uolocal/dev_workspace/gene_pav')
```

This hardcoded absolute path:
1. Will fail for any other user
2. Points to a different repository (`uolocal` instead of current repo)
3. Uses old directory name (`dev_workspace`)

**FIX:**
```python
sys.path.insert(0, '..')  # Relative path to parent directory
```

**Features:**
- Tests `parse_interproscan.py` integration
- Tests PAVprot output generation
- Validates overlap-aware IPR calculation

---

### 4.6 Test Data Files

| File | Purpose |
|------|---------|
| `test_data_1_no_overlap.bed` | Non-overlapping intervals |
| `test_data_2_with_overlap.bed` | Overlapping intervals |
| `test_data_3_complex.bed` | Complex overlap patterns |

| Directory | Contents |
|-----------|----------|
| `test/data/` | GFF, tracking, InterProScan test files |
| `test/output/` | Expected output files |

---

## 5. Recommendations by Priority

### P0 - Critical (Fix Immediately)

| File | Issue | Action |
|------|-------|--------|
| `synonym_mapping_parse.py` | Non-functional, syntax errors | Delete or completely rewrite |
| `test/test_all_outputs.py:14` | Hardcoded absolute path | Change to `sys.path.insert(0, '..')` |

### P1 - High Priority

| File | Issue | Action |
|------|-------|--------|
| `test/test_pavprot.py:10` | Import without path setup | Add `sys.path.insert(0, '..')` |
| `pairwise_align_prot.py` | Filename typo | Rename to `pairwise_align_prot.py` |
| `pavprot.py` | Import uses typo | Update import after rename |

### P2 - Medium Priority

| File | Issue | Action |
|------|-------|--------|
| `plot/*.py` (4 files) | Duplicated `load_data()` | Create `plot/utils.py` |

### P3 - Low Priority

| File | Issue | Action |
|------|-------|--------|
| `__init__.py` (root) | Empty | Add docstring and exports |
| `plot/__init__.py` | Empty | Add docstring and exports |

---

## 6. Pipeline Connectivity Map

```
                                    USER INPUT
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            pavprot.py (Main)                             │
│  - CLI argument parsing                                                  │
│  - Orchestrates all components                                           │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
           ┌─────────────────────┼─────────────────────┐
           │                     │                     │
           ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│parse_interproscan│  │detect_one2many   │  │bidirectional     │
│    .py           │  │  _mappings.py    │  │ _best_hits.py    │
│                  │  │                  │  │                  │
│ • Parse IPR TSV  │  │ • 1:N detection  │  │ • BBH analysis   │
│ • Merge overlaps │  │ • N:1 detection  │  │ • Best hit pairs │
│ • Domain stats   │  │ • Mapping types  │  │                  │
└────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    gsmc.py                          │
│  - Scenario classification (E, A, B, J, CDI, F, G, H)                    │
│  - Multi-transcript consolidation                                        │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
           ┌─────────────────────┼─────────────────────┐
           │                     │                     │
           ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│pairwise_align    │  │parse_liftover    │  │inconsistent_genes│
│   _prot.py       │  │ _extra_copy.py   │  │ _transcript_IPR  │
│                  │  │                  │  │   _PAV.py        │
│ • Seq alignment  │  │ • Liftoff GFF    │  │ • IPR quadrant   │
│ • Identity calc  │  │ • Copy numbers   │  │   inconsistency  │
└────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
                               ▼
                     ┌──────────────────┐
                     │  OUTPUT TSV FILE │
                     │synonym_mapping_*.│
                     │      tsv         │
                     └────────┬─────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│     plot/        │  │synonym_mapping   │  │ project_scripts/ │
│                  │  │  _summary.py     │  │                  │
│ • Visualizations │  │ • Statistics     │  │ • run_pipeline   │
│ • Comparisons    │  │ • Summaries      │  │ • Custom analysis│
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

---

## 7. File Organization Assessment

### Current Structure (Actual)
```
gene_pav/
├── pavprot.py                              # Main orchestrator
├── parse_interproscan.py                   # IPR parsing
├── gsmc.py            # Scenario classification
├── bidirectional_best_hits.py              # BBH analysis
├── mapping_multiplicity.py             # Mapping detection
├── pairwise_align_prot.py                  # TYPO - Protein alignment
├── inconsistent_genes_transcript_IPR_PAV.py # IPR inconsistency
├── parse_liftover_extra_copy_number.py     # Liftoff parsing
├── synonym_mapping_summary.py              # Summary statistics
├── synonym_mapping_parse.py                # BROKEN - Delete
├── __init__.py                             # Empty
│
├── plot/
│   ├── plot_ipr_comparison.py              # Main comparison plots
│   ├── plot_ipr_advanced.py                # Advanced visualization
│   ├── plot_ipr_shapes.py                  # Shape-encoded plots
│   ├── plot_ipr_gene_level.py              # Gene-level plots
│   ├── plot_ipr_proportional_bias.py       # Bias analysis
│   ├── plot_domain_comparison.py           # Before/after comparison
│   └── __init__.py                         # Empty
│
├── project_scripts/
│   ├── run_pipeline.py                     # Master orchestrator
│   ├── run_emckmnje1_analysis.py           # Filtered analysis
│   ├── analyze_fungidb_species.py          # FungiDB stats
│   ├── plot_ipr_1to1_comparison.py         # 1:1 ortholog plots
│   ├── plot_oldvsnew_psauron_plddt.py      # Psauron/pLDDT plots
│   └── plot_psauron_distribution.py        # Psauron distribution
│
├── test/
│   ├── test_pavprot.py                     # Core tests (import issue)
│   ├── test_inconsistent_genes.py          # Mock data generator
│   ├── test_bed_coverage.py                # Coverage tests
│   ├── test_bed_files.py                   # BED file tests
│   ├── test_all_outputs.py                 # Integration (hardcoded path)
│   ├── data/                               # Test input files
│   └── output/                             # Expected outputs
│
└── docs/
    ├── ARCHITECTURE.md
    ├── SCENARIOS.md
    ├── CODE_REVIEW_REPORT.md
    └── ... (19 files total)
```

### Recommended Changes

1. **Delete:** `synonym_mapping_parse.py`
2. **Rename:** `pairwise_align_prot.py` → `pairwise_align_prot.py`
3. **Create:** `plot/utils.py` with shared functions
4. **Fix:** Test import paths (3 files)

---

## 8. Scripts to Combine or Split

### Combine

| Current Files | Proposed | Reason |
|---------------|----------|--------|
| `synonym_mapping_parse.py` + `synonym_mapping_summary.py` | Single `synonym_mapping.py` | After fixing/rewriting parse |

### Keep Separate

| File | Reason |
|------|--------|
| `pavprot.py` vs `run_pipeline.py` | Different purposes (core vs downstream) |
| Individual plot scripts | Each serves specific visualization need |

---

## 9. Metrics Summary

| Metric | Value |
|--------|-------|
| Total Python files | 29 |
| Total lines of code | ~15,500 |
| Files with syntax errors | 1 |
| Files with import issues | 2 |
| Duplicated functions | 1 (in 4 files) |
| Hardcoded user paths (project_scripts) | 5 (acceptable) |
| Hardcoded user paths (tests) | 1 (needs fix) |
| Empty `__init__.py` files | 2 |

---

*Report generated: 2026-01-19*
*All 29 scripts individually read and assessed*
