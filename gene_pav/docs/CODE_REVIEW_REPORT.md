# PAVprot Pipeline - Consolidated Code Review Report

> **Date:** 2026-01-19
> **Branch:** dev
> **Scope:** Priority Task 1 - Code Cleanup (Top Priority)

---

## Executive Summary

This report provides a comprehensive critical review of the PAVprot pipeline codebase. The review covers all Python scripts, documentation, tests, and file organization.

### Codebase Statistics

| Category | Files | Lines of Code |
|----------|-------|---------------|
| Core Pipeline (root) | 11 | 6,139 |
| Plotting Modules (plot/) | 7 | 2,599 |
| Project Scripts (project_scripts/) | 6 | 3,262 |
| Test Files (test/) | 5 | ~3,500 |
| **Total** | **29** | **~15,500** |

### Critical Issues Found

| Severity | Count | Description |
|----------|-------|-------------|
| **CRITICAL** | 1 | `synonym_mapping_parse.py` - Syntax error, non-functional |
| **HIGH** | 2 | README directory mismatch, Test import path |
| **MEDIUM** | 3 | Code duplication, Filename typo, Hardcoded test path |
| **LOW** | 4 | Documentation gaps, Unused imports, Missing requirements.txt |

---

## 1. Core Pipeline Scripts Analysis

### 1.1 Script Inventory

| Script | Lines | Function | Status |
|--------|-------|----------|--------|
| `pavprot.py` | 1,841 | Main orchestrator | **OK** |
| `detect_advanced_scenarios.py` | 1,344 | Orthology classification | **OK** |
| `parse_interproscan.py` | 669 | IPR domain parsing | **OK** |
| `bidirectional_best_hits.py` | 524 | BBH analysis | **OK** |
| `pariwise_align_prot.py` | 462 | Protein alignment | **OK** (typo in name) |
| `inconsistent_genes_transcript_IPR_PAV.py` | 451 | IPR inconsistency | **OK** |
| `parse_liftover_extra_copy_number.py` | 435 | Liftover parsing | **OK** |
| `detect_one2many_mappings.py` | 219 | Mapping detection | **OK** |
| `synonym_mapping_summary.py` | 84 | Summary statistics | **OK** |
| `synonym_mapping_parse.py` | 92 | Synonym parsing | **BROKEN** |
| `__init__.py` | 0 | Package init | Empty |

### 1.2 Critical Issue: `synonym_mapping_parse.py`

**Status:** NON-FUNCTIONAL

**Error:**
```
IndentationError: unindent does not match any outer indentation level (line 59)
```

**Root Cause Analysis:**

The file contains **two separate scripts concatenated together**:

| Section | Lines | Content |
|---------|-------|---------|
| Script 1 | 1-57 | Incomplete parsing script with bugs |
| Script 2 | 59-93 | Different script with wrong indentation |

**Bugs in Script 1 (lines 1-57):**

1. **Line 3** - Unused import:
   ```python
   from curses import start_color  # Never used
   ```

2. **Line 27** - Syntax error (brackets vs parentheses):
   ```python
   df_grouped = df.groupby["GCF_013085055.1_gene"]  # WRONG
   # Should be: df.groupby("GCF_013085055.1_gene")
   ```

3. **Line 28** - References undefined column:
   ```python
   df_sorted = df.sort_values(by=["length"])
   # "length" column is never defined (line 26 is commented out)
   ```

4. **Lines 6-17** - Hardcoded project-specific column names

**Recommendation:** Delete and rewrite this script entirely.

### 1.3 Filename Typo

| Current | Should Be |
|---------|-----------|
| `pariwise_align_prot.py` | `pairwise_align_prot.py` |

### 1.4 Module Dependencies

```
pavprot.py
├── imports: detect_one2many_mappings
├── imports: bidirectional_best_hits
└── imports: pariwise_align_prot
```

All internal imports verified working.

---

## 2. Plotting Modules Analysis

### 2.1 Script Inventory

| Script | Lines | Purpose |
|--------|-------|---------|
| `plot_ipr_comparison.py` | 839 | Main IPR comparison plots |
| `plot_ipr_proportional_bias.py` | 506 | Bias analysis |
| `plot_ipr_gene_level.py` | 354 | Gene-level visualization |
| `plot_domain_comparison.py` | 344 | Before/after comparison |
| `plot_ipr_shapes.py` | 324 | Shape-encoded scatter |
| `plot_ipr_advanced.py` | 232 | Advanced visualizations |
| `__init__.py` | 0 | Empty |

### 2.2 Code Duplication Issue

**`load_data()` function duplicated identically in 4 files:**

```python
# Identical in all 4 files:
def load_data(input_file):
    """Load PAVprot output TSV file"""
    df = pd.read_csv(input_file, sep='\t')
    return df
```

| File | Line |
|------|------|
| `plot_ipr_advanced.py` | 23 |
| `plot_ipr_shapes.py` | 19 |
| `plot_ipr_gene_level.py` | 20 |
| `plot_ipr_proportional_bias.py` | 20 |

**Different version in `plot_ipr_comparison.py`:**
```python
def load_pavprot_data(input_file):  # Different name, extra processing
```

**Recommendation:** Create `plot/utils.py` with shared functions.

### 2.3 Common Boilerplate

All 6 plotting scripts repeat:
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import argparse
import sys
from pathlib import Path

sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
```

**Recommendation:** Move to `plot/config.py`.

---

## 3. Project Scripts Analysis

### 3.1 Script Inventory

| Script | Lines | Purpose | Hardcoded Paths |
|--------|-------|---------|-----------------|
| `run_pipeline.py` | 1,900 | Master orchestrator | 6 |
| `run_emckmnje1_analysis.py` | 460 | Filtered analysis | 6 |
| `plot_oldvsnew_psauron_plddt.py` | 327 | Psauron/pLDDT plots | 2 |
| `plot_ipr_1to1_comparison.py` | 295 | 1:1 ortholog plots | 0 |
| `plot_psauron_distribution.py` | 200 | Psauron distribution | 0 |
| `analyze_fungidb_species.py` | 140 | FungiDB analysis | 2 |

### 3.2 Hardcoded Paths (Expected - These Are Examples)

All hardcoded paths are in `project_scripts/` which is the correct location for project-specific examples:

```
project_scripts/run_pipeline.py:65-70
project_scripts/run_emckmnje1_analysis.py:60-63, 358-359
project_scripts/analyze_fungidb_species.py:18-19
project_scripts/plot_oldvsnew_psauron_plddt.py:47-48
```

**Status:** ACCEPTABLE - These serve as templates/examples.

### 3.3 Integration Assessment

**Question from todo.md:** Should `run_pipeline.py` be integrated into main script?

**Analysis:**

| Aspect | run_pipeline.py | pavprot.py |
|--------|-----------------|------------|
| Lines | 1,900 | 1,841 |
| Purpose | Downstream analysis orchestration | Core PAVprot analysis |
| Tasks | 15+ plotting/integration tasks | Gene mapping, IPR integration |
| Dependencies | External data (Psauron, ProteinX) | GFF, FASTA, gffcompare |

**Recommendation:** Keep separate. They serve different purposes:
- `pavprot.py` = Core pipeline (generic)
- `run_pipeline.py` = Downstream analysis template (project-specific)

Consider extracting reusable tasks into `tasks/` module.

---

## 4. Test Suite Analysis

### 4.1 Test Files

| File | Lines | Target |
|------|-------|--------|
| `test_pavprot.py` | ~400 | pavprot.py core functions |
| `test_inconsistent_genes.py` | ~200 | Inconsistency detection |
| `test_bed_coverage.py` | ~350 | BED coverage utilities |
| `test_bed_files.py` | ~160 | BED file parsing |
| `test_all_outputs.py` | ~350 | Integration tests |

### 4.2 Test Import Issue

**Problem:**
```bash
$ cd test && python3 test_pavprot.py
ModuleNotFoundError: No module named 'pavprot'
```

**Cause:** Tests use direct import without path setup:
```python
from pavprot import PAVprot, DiamondRunner  # Line 10
```

**Solution verified working:**
```python
import sys
sys.path.insert(0, '..')
from pavprot import PAVprot, DiamondRunner
```

**Recommendation:** Add `sys.path.insert(0, '..')` to all test files.

### 4.3 Hardcoded Path in Tests

```python
# test/test_all_outputs.py:14
sys.path.insert(0, '/Users/sadik/projects/github_prj/uolismib/uolocal/dev_workspace/gene_pav')
```

**Recommendation:** Change to relative path `sys.path.insert(0, '..')`.

### 4.4 Test Data

Test data exists in `test/data/`:
- `gff_feature_table.gff3`
- `gffcompare.tracking`
- `test_interproscan.tsv`
- Mock data files for unit tests

---

## 5. Documentation Analysis

### 5.1 Documentation Files (19 total)

| File | Size | Content |
|------|------|---------|
| `ARCHITECTURE.md` | 31KB | Module connectivity |
| `SCENARIOS.md` | 22KB | Biological scenarios |
| `multi-mapping_gene_scenarios.md` | 22KB | Multi-mapping details |
| `SETUP_COMMANDS.md` | 8KB | Setup history |
| `RESTRUCTURE_REPORT.md` | 21KB | Previous restructure |
| `PAVprot_Module_Architecture.md` | 27KB | Module details |
| Others | Various | Specific topics |

### 5.2 README.md Issue

**Problem:** README references directories that don't exist:

```markdown
gene_pav/
├── core/                         # DOES NOT EXIST
│   ├── parse_interproscan.py
│   ...
├── analysis/                     # DOES NOT EXIST
│   ├── detect_advanced_scenarios.py
│   ...
├── utils/                        # DOES NOT EXIST
├── tests/                        # Should be test/
```

**Actual structure:**
```
gene_pav/
├── *.py                          # All core scripts at root
├── plot/
├── project_scripts/
├── test/                         # Not tests/
└── docs/
```

**Recommendation:** Update README to match actual structure.

### 5.3 Missing Documentation

1. **requirements.txt** - Dependencies not documented in file
2. **Installation guide** - No step-by-step setup
3. **API documentation** - No function-level docs

---

## 6. Recommended Actions

### 6.1 Priority Matrix

| Priority | Issue | Effort | Action |
|----------|-------|--------|--------|
| **P0** | `synonym_mapping_parse.py` broken | 5 min | Delete or rewrite |
| **P0** | README directory mismatch | 15 min | Update README.md |
| **P1** | Test import paths | 10 min | Add sys.path to tests |
| **P1** | Hardcoded path in test | 2 min | Fix relative path |
| **P2** | Code duplication in plot/ | 30 min | Create plot/utils.py |
| **P2** | Filename typo | 5 min | Rename pariwise → pairwise |
| **P3** | Missing requirements.txt | 10 min | Create file |
| **P3** | Empty __init__.py files | 5 min | Add docstrings |

### 6.2 Scripts to Combine

| Current | Proposed |
|---------|----------|
| `synonym_mapping_parse.py` + `synonym_mapping_summary.py` | Single `synonym_mapping.py` (after fixing) |

### 6.3 Scripts to Rename

| Current | Proposed | Reason |
|---------|----------|--------|
| `detect_advanced_scenarios.py` | `gamc.py` | Per todo.md request |
| `pariwise_align_prot.py` | `pairwise_align_prot.py` | Fix typo |
| `inconsistent_genes_transcript_IPR_PAV.py` | `ipr_inconsistency.py` | Shorter |

### 6.4 New Files to Create

```
gene_pav/
├── requirements.txt              # NEW: Dependencies
├── plot/
│   └── utils.py                  # NEW: Shared plotting functions
└── test/
    └── conftest.py               # NEW: Pytest configuration (optional)
```

---

## 7. Verification Commands

```bash
# Check syntax errors
cd /Users/sadik/projects/github_prj/uolismib/gene_pav
for f in *.py plot/*.py project_scripts/*.py; do
  python3 -m py_compile "$f" 2>&1 || echo "ERROR: $f"
done

# Find hardcoded paths
grep -rn "/Users/sadik" --include="*.py" .

# Check test imports
cd test && python3 -c "import sys; sys.path.insert(0,'..'); from pavprot import PAVprot; print('OK')"

# Run tests (after fixing imports)
cd test && python3 -m unittest discover -v
```

---

## 8. Summary

### What's Working Well

1. **Core pipeline (`pavprot.py`)** - 1,841 lines, imports correctly, main functionality solid
2. **Scenario detection** - Comprehensive classification system
3. **Plotting modules** - Good variety of visualizations
4. **Test data** - Exists and is organized
5. **Documentation** - Extensive (19 docs), covers key topics
6. **Hardcoded paths** - Correctly isolated in `project_scripts/`

### What Needs Attention

1. **`synonym_mapping_parse.py`** - Delete or completely rewrite
2. **README.md** - Update to match actual directory structure
3. **Test imports** - Add path configuration
4. **Code duplication** - Create shared utilities module
5. **Filename typo** - `pariwise` → `pairwise`

### Metrics

| Metric | Value |
|--------|-------|
| Files with syntax errors | 1 |
| Files with hardcoded user paths | 5 (all in project_scripts + 1 test) |
| Duplicated functions | 1 (`load_data` in 4 files) |
| Core scripts importable | 10/11 (91%) |
| Documentation coverage | Good |

---

*Report generated: 2026-01-19*
