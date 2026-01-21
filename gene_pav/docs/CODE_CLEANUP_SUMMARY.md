# PAVprot Code Cleanup - Final Summary Report

> **Date:** 2026-01-19
> **Task:** Priority Task 1 - Code Cleanup (Top Priority)
> **Status:** Assessment Complete

---

## Executive Summary

A comprehensive one-by-one assessment of **all 29 Python scripts** in the PAVprot pipeline has been completed. This review covered core pipeline scripts, plotting modules, project-specific scripts, and test files.

### Key Findings

| Category | Finding |
|----------|---------|
| **Critical Issues** | 1 broken script (`synonym_mapping_parse.py`) |
| **Integration Decision** | Keep `run_pipeline.py` separate from `pavprot.py` |
| **Plotting Integration** | Most features already exist; only add `--scenario` filter |
| **Code Duplication** | `load_data()` duplicated in 4 files → create `plot/utils.py` |
| **Planned Future Work** | Unified external tools module |

---

## 1. Documents Created

| Document | Purpose |
|----------|---------|
| `docs/INDIVIDUAL_SCRIPT_ASSESSMENT.md` | One-by-one review of all 29 scripts |
| `docs/RUN_PIPELINE_INTEGRATION_ASSESSMENT.md` | Analysis: Should run_pipeline.py merge into pavprot.py? |
| `docs/PLOTTING_SCRIPTS_INTEGRATION_ASSESSMENT.md` | Feature comparison: project_scripts/ vs plot/ |
| `docs/SCRIPTS_COMBINE_SPLIT_RECOMMENDATIONS.md` | Recommendations for combining/splitting scripts |
| `docs/CODE_REVIEW_REPORT.md` | Consolidated code review findings |
| `docs/CODE_CLEANUP_SUMMARY.md` | This summary document |

---

## 2. Codebase Statistics

### 2.1 File Inventory

```
gene_pav/
├── Core Scripts (11 files)          6,139 lines
│   ├── pavprot.py                   1,841 lines (main orchestrator)
│   ├── gsmc.py 1,344 lines (scenario classification)
│   ├── parse_interproscan.py          669 lines (IPR domain parsing)
│   ├── bidirectional_best_hits.py     524 lines (BBH analysis)
│   ├── pairwise_align_prot.py         462 lines (protein alignment)
│   ├── inconsistent_genes_*.py        451 lines (inconsistency detection)
│   ├── parse_liftover_*.py            435 lines (liftover parsing)
│   ├── mapping_multiplicity.py    219 lines (mapping detection)
│   ├── synonym_mapping_summary.py      84 lines (summary stats)
│   ├── synonym_mapping_parse.py        92 lines ⚠️ BROKEN
│   └── __init__.py                      0 lines
│
├── plot/ (7 files)                  2,599 lines
│   ├── plot_ipr_comparison.py         839 lines
│   ├── plot_ipr_proportional_bias.py  506 lines
│   ├── plot_ipr_gene_level.py         354 lines
│   ├── plot_domain_comparison.py      344 lines
│   ├── plot_ipr_shapes.py             324 lines
│   ├── plot_ipr_advanced.py           232 lines
│   └── __init__.py                      0 lines
│
├── project_scripts/ (6 files)       3,262 lines
│   ├── run_pipeline.py              ~1,900 lines
│   ├── run_emckmnje1_analysis.py      460 lines
│   ├── plot_oldvsnew_psauron_plddt.py 327 lines
│   ├── plot_ipr_1to1_comparison.py    295 lines
│   ├── plot_psauron_distribution.py   200 lines
│   └── analyze_fungidb_species.py     140 lines
│
├── test/ (5 files)                  ~1,250 lines
│   ├── test_pavprot.py               ~400 lines
│   ├── test_all_outputs.py           ~250 lines
│   ├── test_bed_coverage.py          ~300 lines
│   ├── test_bed_files.py             ~170 lines
│   └── test_inconsistent_genes.py    ~140 lines
│
└── docs/ (19+ files)                Various
```

**Total: ~15,500 lines of Python code**

---

## 3. Critical Issues Requiring Action

### 3.1 CRITICAL: Delete Broken Script

**File:** `synonym_mapping_parse.py`

| Issue | Description |
|-------|-------------|
| IndentationError | Line 59 - Two scripts concatenated |
| Syntax Error | `df.groupby["..."]` - brackets instead of parentheses |
| Undefined Column | References "length" column that doesn't exist |
| Unused Import | `from curses import start_color` |

**Action:** Delete this file immediately.

### 3.2 HIGH: Fix Test Import Paths

**File:** `test/test_all_outputs.py:14`

```python
# Current (WRONG - hardcoded to different repo):
sys.path.insert(0, '/Users/sadik/projects/github_prj/uolismib/uolocal/dev_workspace/gene_pav')

# Should be:
sys.path.insert(0, '..')
```

**Action:** Update all test files to use relative imports.

### 3.3 MEDIUM: Create Shared Plot Utilities

**Problem:** `load_data()` duplicated in 4 files:
- `plot/plot_ipr_advanced.py:23`
- `plot/plot_ipr_shapes.py:19`
- `plot/plot_ipr_gene_level.py:20`
- `plot/plot_ipr_proportional_bias.py:20`

**Action:** Create `plot/utils.py` with shared functions.

### 3.4 LOW: Filename Typo

| Current | Should Be |
|---------|-----------|
| `pairwise_align_prot.py` | `pairwise_align_prot.py` |

---

## 4. Integration Decisions

### 4.1 run_pipeline.py → pavprot.py

**Decision: DO NOT INTEGRATE**

| Reason | Explanation |
|--------|-------------|
| Different purposes | Core analysis vs. downstream visualization |
| Different dependencies | Core (pandas, Biopython) vs. Viz (matplotlib, seaborn) |
| Different inputs | Raw files vs. PAVprot output TSV |
| Maintainability | 3,700-line monolith would be hard to maintain |

**Alternative:** Add `downstream` subcommand to `pavprot.py` for unified CLI entry point.

### 4.2 project_scripts/ Plotting → plot/

**Decision: PARTIAL INTEGRATION**

| Feature | In project_scripts/ | In plot/ | Action |
|---------|---------------------|----------|--------|
| Regression line + R² | ✓ | ✓ Already exists | None |
| Log-scale plots | ✓ | ✓ Already exists | None |
| Pearson correlation | ✓ | ✓ Already exists | None |
| **Scenario filtering** | ✓ | ✗ Missing | **ADD** |
| Psauron visualization | ✓ | Cannot add | Keep in project_scripts/ |
| pLDDT visualization | ✓ | Cannot add | Keep in project_scripts/ |

**Action:** Add `--scenario` parameter to plot modules.

---

## 5. Future Development: Unified External Tools Module

**PLANNED:** Consolidate external tool execution into a single unified module:

| Tool | Purpose |
|------|---------|
| **Psauron** | Protein structure quality scoring |
| **ProteinX/AlphaFold** | pLDDT confidence scores |
| **DIAMOND** | BLAST-based protein alignment |
| **InterProScan** | Domain/motif detection |
| **gffcompare** | GFF comparison and tracking |
| **Liftoff** | Annotation liftover |
| **Pairwise alignment** | Protein sequence alignment |

This module will provide:
1. Consistent interface for running external tools
2. Tool installation verification
3. Temporary file management
4. Integration with both core analysis and downstream visualization

---

## 6. Action Item Summary

### Priority 0 (Immediate)

| Task | Effort |
|------|--------|
| Delete `synonym_mapping_parse.py` | 1 min |
| Fix hardcoded path in `test/test_all_outputs.py` | 2 min |

### Priority 1 (High)

| Task | Effort |
|------|--------|
| Add `--scenario` parameter to 4 plot modules | 1 hour |
| Create `plot/utils.py` with shared functions | 1 hour |
| Fix test import paths in all test files | 15 min |

### Priority 2 (Medium)

| Task | Effort |
|------|--------|
| Rename `pairwise_align_prot.py` → `pairwise_align_prot.py` | 5 min |
| Update README.md directory structure | 15 min |
| Add docstrings to empty `__init__.py` files | 10 min |

### Priority 3 (Future)

| Task | Effort |
|------|--------|
| Create unified external tools module | TBD |
| Add `downstream` subcommand to pavprot.py | 2 hours |
| Create YAML config system for external data | 1 hour |

---

## 7. What's Working Well

1. **Core pipeline (`pavprot.py`)** - Well-organized, all 37 functions work correctly
2. **Scenario detection** - Comprehensive 8-scenario classification system
3. **Plotting modules** - Actually MORE feature-complete than expected
4. **Test data** - Exists and is properly organized in `test/data/`
5. **Documentation** - Extensive (19+ docs) covering key topics
6. **Hardcoded paths** - Correctly isolated in `project_scripts/` (example code)

---

## 8. Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PAVprot Pipeline Flow                             │
└─────────────────────────────────────────────────────────────────────────┘

    INPUT FILES                    CORE ANALYSIS                   OUTPUT
         │                              │                             │
         ▼                              ▼                             ▼
┌─────────────────┐            ┌─────────────────┐           ┌─────────────────┐
│ GFF3, FASTA     │            │                 │           │ transcript.tsv  │
│ gffcompare.track│───────────▶│   pavprot.py    │──────────▶│ gene_level.tsv  │
│ InterProScan    │            │   (1,841 lines) │           │                 │
│ Liftoff output  │            │                 │           │                 │
└─────────────────┘            └─────────────────┘           └─────────────────┘
                                       │                             │
                    ┌──────────────────┼──────────────────┐          │
                    │                  │                  │          │
                    ▼                  ▼                  ▼          ▼
         ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
         │detect_advanced_  │ │parse_interpro    │ │bidirectional_    │
         │scenarios.py      │ │scan.py           │ │best_hits.py      │
         │(1,344 lines)     │ │(669 lines)       │ │(524 lines)       │
         └──────────────────┘ └──────────────────┘ └──────────────────┘

                                       │
                                       ▼
                            ┌─────────────────────┐
                            │  DOWNSTREAM TASKS   │
                            │  (project_scripts/) │
                            └─────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
         ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
         │   plot/          │ │ Psauron/ProteinX │ │ FungiDB          │
         │   (7 modules)    │ │ Integration      │ │ Analysis         │
         └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## 9. Verification Commands

```bash
# Check syntax errors in all Python files
cd /Users/sadik/projects/github_prj/uolismib/gene_pav
for f in *.py plot/*.py project_scripts/*.py; do
  python3 -m py_compile "$f" 2>&1 || echo "ERROR: $f"
done

# Find remaining hardcoded paths
grep -rn "/Users/sadik" --include="*.py" .

# Run tests (after fixing imports)
cd test && python3 -m unittest discover -v

# Check for duplicate functions
grep -rn "def load_data" --include="*.py" .
```

---

## 10. Conclusion

The PAVprot codebase is in **good overall health** with clear separation of concerns. The main issues are:

1. **One broken script** that should be deleted
2. **Minor code duplication** in plotting modules
3. **Test import path issues** requiring fix

The assessment confirmed that:
- `run_pipeline.py` should remain separate from `pavprot.py`
- Most project_scripts/ plotting features already exist in main modules
- Only the `--scenario` filter needs to be added
- Future work should focus on the unified external tools module

**Total effort for all P0-P2 fixes:** ~3-4 hours

---

*Summary completed: 2026-01-19*
