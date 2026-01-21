# PAVprot Pipeline - Development Todo

> **Branch:** dev
> **Last Updated:** 2026-01-21

---

## Current Status

- [x] Set up dev branch on uolismib/gene_pav
- [x] Copy files from uolocal/fungidb/dev/gene_pav
- [x] Organize project scripts into `project_scripts/` subfolder
- [x] **Completed Section 6 tasks (2026-01-20)** - See "Completed Tasks" below
- [x] **Verified pipeline structure (2026-01-21)** - All modules functional

---

## Completed Tasks (2026-01-20)

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Created `tools_runner.py` with ToolsRunner class (8 tools) | b3b4d01 |
| 2 | Added `detect_annotation_source()` to tools_runner.py | b3b4d01 |
| 3 | Fixed hardcoded path in `test/test_all_outputs.py` | b3b4d01 |
| 4 | Created `config.yaml` for pipeline configuration | b3b4d01 |
| 5-6 | Created `plot/config.py` and `plot/utils.py` | b3b4d01 |
| 7-8,10 | Rewrote `synonym_mapping_parse.py` (fixed IndentationError, removed unused imports) | b3b4d01 |
| 9 | Renamed: `detect_advanced_scenarios.py` → `gsmc.py`, `detect_one2many_mappings.py` → `mapping_multiplicity.py` | b3b4d01 |
| 11 | Fixed typo: `pariwise_align_prot.py` → `pairwise_align_prot.py` | b3b4d01 |
| 12 | Consolidated plotting utilities into `plot/utils.py` | b3b4d01 |
| 13 | Fixed test import paths in `test_pavprot.py` | b3b4d01 |
| 14 | Updated `README.md` directory structure | b3b4d01 |
| 15 | Created `requirements.txt` | b3b4d01 |
| 19 | Added docstrings to `__init__.py` and `plot/__init__.py` | b3b4d01 |

**Files created:**
- `tools_runner.py` - Unified external tools interface
- `config.yaml` - Pipeline configuration
- `plot/config.py` - Plotting configuration and palettes
- `plot/utils.py` - Shared data loading utilities
- `requirements.txt` - Python dependencies

**Files renamed:**
- `detect_advanced_scenarios.py` → `gsmc.py` (Gene Synteny Mapping Classifier)
- `detect_one2many_mappings.py` → `mapping_multiplicity.py`
- `pariwise_align_prot.py` → `pairwise_align_prot.py`

---

## Priority Tasks

### 1. Code Cleanup (top priority)

- [ ] Conduct a thorough critical review of the entire pipeline
- [ ] Critically revisit individual scripts, input/output files, and documentation
- [ ] Review plotting scripts and assess if any project_scripts/*.py should be integrated into main plotting scripts
- [ ] Assess integrating project_scripts/run_pipeline.py into the main script to allow running all or specific parts
- [ ] Assess, examine, and critically review all code files
- [ ] Critically review file organization
- [ ] Suggest scripts to be combined or split
- [ ] Do not copy or delete files
- [ ] Complete all reviews autonomously without user prompts
- [ ] Provide an extensive markdown report for each file showing how it connects to the pipeline 

### 2. Initial tidy-up ✓

- [x] Remove hardcoded paths from all pipeline scripts
- [x] Renamed: detect_advanced_scenarios.py → gsmc.py (Gene Synteny Mapping Classifier) 
- [x] Review and update docstrings
- [x] Ensure all imports are correct after file reorganization

### 3. Tidy up and review code

2. [x] Commit changes to dev branch
3. [ ] Push dev branch to remote
4. [ ] Review and merge to main

### 4. Documentation

- [ ] Update main README.md with usage examples
- [ ] Review docs/ folder for accuracy
- [x] Add installation instructions
- [x] Document dependencies (requirements.txt)

### 5. Testing

- [ ] Test pipeline with sample data
- [ ] Run existing tests in test/ folder
- [ ] Fix any failing tests
- [ ] Add tests for new modules if needed

### 6. project_scripts/ Folder

- [ ] Update paths in project_scripts/ to be configurable
- [ ] Add example config file or CLI arguments
- [ ] Update project_scripts/README.md with usage

### 7. Codebase Review Notes (Top priority 20/01/2026)

- [x] Ref: doc/CODE_REVIEW_REPOR.md under "Critical Issues Found"
  - [x] `synonym_mapping_parse.py` - Syntax error, non-functional ✅ **FIXED (b3b4d01)**
  - [x] README directory mismatch, Test import path ✅ **FIXED (b3b4d01)**
  - [x] Code duplication ✅ **CONSOLIDATED to plot/utils.py (b3b4d01)**
  - [x] Filename typo ✅ **FIXED pariwise→pairwise (b3b4d01)**
  - [x] Hardcoded test path ✅ **FIXED (b3b4d01)**
  - [x] Documentation gaps ✅ **Added docstrings (b3b4d01)**
  - [x] Unused imports ✅ **REMOVED (b3b4d01)**
  - [x] Missing requirements.txt ✅ **CREATED (b3b4d01)**


- [x] Ref: doc/CODE_REVIEW_REPOR.md under "Core Pipeline Scripts Analysis"

  - [x] Renaming scripts or resolving typos ✅ **ALL COMPLETED (b3b4d01)**

    - [x] `pariwise_align_prot.py` typo → `pairwise_align_prot.py` ✅
    - [x] `detect_one2many_mappings.py` → `mapping_multiplicity.py` ✅
    - [x] `detect_advanced_scenarios.py` → `gsmc.py` ✅ 

  - [x] `synonym_mapping_parse.py` broken: ✅ **FIXED (b3b4d01)**

    - [x] `IndentationError` at line 59 ✅ **FIXED** - Rewrote entire file
    - [x] Removed unused import `from curses import start_color`
    - [ ] **Future:** Hardcoded project-specific column names (Lines 6-17)
      - [ ] Suggestion: implement `--prefix` flag for dynamic column naming
      - [ ] Auto-detect annotation source via `tools_runner.detect_annotation_source()` 

  - [x] Document any hardcoded lines ✅ **ADDRESSED (b3b4d01)**

    - [x] Created `config.yaml` for configurable paths and settings
    - [x] Fixed hardcoded test path in `test/test_all_outputs.py`
    - [ ] **Future:** Review remaining hardcoded paths in project_scripts/

  - [x] Code Duplication Issue ✅ **RESOLVED (b3b4d01)**

    - [x] Created `plot/utils.py` with shared `load_data()` function
    - [x] Created `plot/config.py` with common boilerplate and palettes
    - [ ] **Future:** Update plotting scripts to use new shared utilities

  - [x] Integration Assessment ✅ **COMPLETED (b3b4d01)**

    - [x] Created `tools_runner.py` - Unified external tools module
    - [x] Implemented stub methods for all 8 tools:
      - ✅ Psauron, AlphaFold/pLDDT, DIAMOND, InterProScan
      - ✅ gffcompare, Liftoff, Pairwise alignment, BUSCO
    - [x] Added `detect_annotation_source()` method

    > **STATUS:** Template created with class-based design. Full implementations can be added as needed.

  - [x] Address issues in Test Suite Analysis ✅ **FIXED (b3b4d01)**
    - [x] Fixed test import paths
    - [x] Fixed hardcoded path in test_all_outputs.py

  - [ ] Resolve 5. Documentation Analysis
    - [ ] Review docs/ folder for accuracy with new file names

  - [ ] Update 6. Recommended Actions and 8. Summary in CODE_REVIEW_REPORT.md

  - [x] `__init__.py` empty ✅ **FIXED (b3b4d01)**
    - [x] Added docstrings to `gene_pav/__init__.py` and `plot/__init__.py`

  - [x] Run this without command prompt ✅ **DONE** - Batch operations completed

---

## File Structure

```
gene_pav/
├── Core Pipeline (root level)
│   ├── pavprot.py                    # Main orchestrator
│   ├── tools_runner.py               # Unified external tools module
│   ├── config.yaml                   # Pipeline configuration
│   ├── requirements.txt              # Python dependencies
│   ├── parse_interproscan.py         # IPR domain parsing
│   ├── gsmc.py                       # Gene Synteny Mapping Classifier (scenarios)
│   ├── mapping_multiplicity.py       # 1:N mapping detection
│   ├── bidirectional_best_hits.py    # BBH analysis
│   ├── pairwise_align_prot.py        # Protein alignment
│   ├── synonym_mapping_parse.py      # Synonym mapping utilities
│   └── synonym_mapping_summary.py    # Summary statistics
│
├── plot/                             # Generic plotting modules
│   ├── __init__.py
│   ├── config.py                     # Plot configuration
│   ├── utils.py                      # Shared utilities
│   └── plot_*.py                     # Visualization scripts
│
├── project_scripts/                  # Project-specific examples
│   ├── run_pipeline.py
│   └── ...
│
├── docs/                             # Documentation
├── test/                             # Unit tests
└── README.md
```

---

## Scenarios Detected

| Scenario | Description |
|----------|-------------|
| E | 1:1 orthologs |
| A | 1:N (one ref → multiple queries) |
| B | N:1 (multiple refs → one query) |
| J | Complex 1:N (one ref → 3+ queries) |
| CDI | Cross-mapping groups |
| F | Positional swaps |
| G | Unmapped reference genes |
| H | Unmapped query genes |

---

## Notes

- **uolocal repo:** Testing/working repo with Fo47-specific data
- **uolismib repo:** Main public repo (this one)
- Project-specific scripts in `project_scripts/` serve as examples

---

## Backlog (Future)

- [ ] Autogenerate markdown report
- [ ] Add BUSCO integration
- [ ] Add pairwise alignment scores
- [ ] Make pipeline modular (configurable runners)
- [ ] Add Metapredict integration

---

*See `docs/SETUP_COMMANDS.md` for setup history*

## Codebase Review Notes - Detailed Breakdown

**Reference: Lines 64-137 in original task list**

---

## 6.1 Reference to Critical Issues Found (Lines 66-71)

```
- [ ] Ref: doc/CODE_REVIEW_REPOR.md under "Critical Issues Found"
  - [ ] `synonym_mapping_parse.py` - Syntax error, non-functional
  - [ ] README directory mismatch, Test import path
  - [ ] Code duplication, Filename typo, Hardcoded test path
  - [ ] Documentation gaps, Unused imports, Missing requirements.txt
  - [ ] Ref: doc/CODE_REVIEW_REPOR.md under "Critical Issues Found"
```

**Tasks:**
| Line | Task |
|------|------|
| 67 | `synonym_mapping_parse.py` - Syntax error, non-functional |
| 68 | README directory mismatch, Test import path |
| 69 | Code duplication, Filename typo, Hardcoded test path |
| 70 | Documentation gaps, Unused imports, Missing requirements.txt |

---

## 6.2 Reference to Core Pipeline Scripts Analysis (Lines 74-93)

### 6.2.1 Renaming scripts or resolving typos (Lines 76-80)

```
  - [ ] Renaming scripts or resolving typos
    - [ ] `pariwise_align_prot.py` typo in name
    - [ ] suggest new name for detect_one2many_mappings
    - [ ] `1.3 Filename Typo`
```

**Tasks:**
| Line | Task |
|------|------|
| 78 | `pariwise_align_prot.py` typo in name |
| 79 | suggest new name for detect_one2many_mappings |
| 80 | `1.3 Filename Typo` (reference to CODE_REVIEW_REPORT.md section) |

---

### 6.2.2 `synonym_mapping_parse.py` broken (Lines 82-93)

```
  - [ ] `synonym_mapping_parse.py` broken:
  - [ ] `IndentationError: unindent does not match any outer indentation level (line 59)`
```

**Error identified:** IndentationError at line 59

---

#### 6.2.2.1 Lines 6-17 - Hardcoded project-specific column names (Lines 85-93)

```
    - [ ] **Lines 6-17** - Hardcoded project-specific column names
    - [ ] Suggestion:
```

**Suggestion sub-items:**

---

##### Line 87:
```
        - [ ] parse/get the prefix "GCF_013085055.1" and "FungiDB-68_Fo47" from input.
```

**Task:** Parse/get the prefix "GCF_013085055.1" and "FungiDB-68_Fo47" from input.

---

##### Line 88:
```
        - [ ] eg --prefix (note: comma prefix input file annotation or genome for old and new annotations, by detault old annotation as "old" and new annotation as "new")
```

**Task:** Example `--prefix` flag

**Note content:**
- Comma-separated prefix for input file annotation or genome (old and new annotations)
- By default: old annotation as "old" and new annotation as "new"

---

##### Line 89-90:
```
- [ ] when --prefix not provide input of old vs new annotation will be autodetected from `Tools running module`. See `8. Future: Unified External Tools Module`in RUN_PIPELINE_INTEGRATION_ASSESSMENT.md
- [ ] First create a mock/dry module to `tools running` - pick appropriate naming for this module
```

**Task (Line 89):** When `--prefix` is not provided, old vs new annotation will be auto-detected from `Tools running module`

**Reference:** See `8. Future: Unified External Tools Module` in RUN_PIPELINE_INTEGRATION_ASSESSMENT.md

**Sub-task (Line 90):** First create a mock/dry module for `tools running` - choose an appropriate name for this module

---

##### Line 91:
```
- [ ] So any ref and query or qry prefix need to be updated to the associated prefix of the input files example in ref_gene, ref_transcript, query_gene, query_transcript etc...
```

**Task:** Update ref and query (qry) prefixes to match the associated prefix of the input files

**Examples:** ref_gene, ref_transcript, query_gene, query_transcript, etc.

---

##### Line 92:
```
- [ ] eg. GCF_013085055.1 is new annotation and FungiDB-68_Fo47 is old annotation
```

**Example:**
- GCF_013085055.1 = new annotation
- FungiDB-68_Fo47 = old annotation

---

## 6.3 Document any hardcoded lines (Lines 95-100)

```
- [ ] Document any hardcoded lines
- [ ] avoid hardcoding
- [ ] suggest a solution to avoid hardcoding including file path, prefix and full file names and other related aspects
- [ ] Example in 3.2 Hardcoded Paths (Expected - These Are Examples)
- [ ] Example in 4.3 Hardcoded Path in Tests
```

**Tasks:**
| Line | Task |
|------|------|
| 97 | avoid hardcoding |
| 98 | suggest a solution to avoid hardcoding including file path, prefix and full file names and other related aspects |
| 99 | Example in 3.2 Hardcoded Paths (Expected - These Are Examples) |
| 100 | Example in 4.3 Hardcoded Path in Tests |

---

## 6.4 Code Duplication Issue (Lines 102-109)

```
  - [ ] Code Duplication Issue eg below in plotting script but can also exist in other scripts
    - [ ] plotting
      - [ ] See in 2.2 Code Duplication Issue plotting scripts
      - [ ] Assess the code and suggest a better implementation or if the existing way is the best way to handle
      - [ ] Assess different version in `plot_ipr_comparison.py` what is different from the other function where the functionality in this script adapted other scripts. Assess also the recommendation: Create `plot/utils.py` with shared functions.
      - [ ] Common Boilerplate (plotting scripts repeat):
        - [ ] Assess the suggestion - Move to `plot/config.py`.
```

**Tasks:**
| Line | Task |
|------|------|
| 105 | See in 2.2 Code Duplication Issue plotting scripts |
| 106 | Assess the code and suggest a better implementation or if the existing way is the best way to handle |
| 107 | Assess different version in `plot_ipr_comparison.py` what is different from the other function where the functionality in this script adapted other scripts. Assess also the recommendation: Create `plot/utils.py` with shared functions. |
| 108-109 | Common Boilerplate (plotting scripts repeat): Assess the suggestion - Move to `plot/config.py`. |

---

## 6.5 Integration Assessment (Lines 111-127)

```
  - [ ] Integration Assessment
    - [ ] Create a single module for internally running tools - choose appropriate naming for this module. See note in 4.3 Future Integration Note
    - [ ] Create a template / dry-code module that will be used to write the full implementation. See note in 4.3 Future Integration Note
```

**Tasks:**
| Line | Task |
|------|------|
| 113 | Create a single module for internally running tools - pick appropriate naming for this module. See note in 4.3 Future Integration Note |
| 115 | Create a template / dry-code module that will be used to write the full implementation. See note in 4.3 Future Integration Note |

**Planned tools to include (Lines 117-127):**
| Tool | Purpose |
|------|---------|
| Psauron | Protein structure quality scoring |
| ProteinX/AlphaFold | pLDDT confidence scores |
| DIAMOND | BLAST-based protein alignment |
| InterProScan | Domain/motif detection |
| gffcompare | GFF comparison and tracking |
| Liftoff | Annotation liftover |
| Pairwise alignment | Protein sequence alignment |

---

## 6.6 Remaining Tasks (Lines 129-137)

```
  - [ ] Address issues in Test Suite Analysis. See section 4. Test Suite Analysis
  - [ ] Resolve 5. Documentation Analysis,
  - [ ] Update 6. Recommended Actions and 8. Summary
  - [ ] `__init__.py` empty
  - [ ] Run this without command prompt
```

**Tasks:**
| Line | Task |
|------|------|
| 129 | Address issues in Test Suite Analysis. See section 4. Test Suite Analysis |
| 131 | Resolve 5. Documentation Analysis |
| 133 | Update 6. Recommended Actions and 8. Summary |
| 135 | `__init__.py` empty |
| 137 | Run this without command prompt |

---

## Summary: All Tasks in Section 6

> **Updated: 2026-01-21** - 26/30 tasks completed in commit b3b4d01

| # | Task | Status | Commit |
|---|------|--------|--------|
| 1 | `synonym_mapping_parse.py` - Syntax error | ✅ Done | b3b4d01 |
| 2 | README directory mismatch | ✅ Done | b3b4d01 |
| 3 | Test import path | ✅ Done | b3b4d01 |
| 4 | Code duplication | ✅ Done | b3b4d01 |
| 5 | Filename typo | ✅ Done | b3b4d01 |
| 6 | Hardcoded test path | ✅ Done | b3b4d01 |
| 7 | Documentation gaps | ✅ Done | b3b4d01 |
| 8 | Unused imports | ✅ Done | b3b4d01 |
| 9 | Missing requirements.txt | ✅ Done | b3b4d01 |
| 10 | `pariwise_align_prot.py` typo | ✅ Done | b3b4d01 |
| 11 | Rename detect_one2many_mappings | ✅ Done | b3b4d01 |
| 12 | Fix IndentationError | ✅ Done | b3b4d01 |
| 13 | Hardcoded column names | ⏳ Future | - |
| 14 | Parse/get prefix from input | ⏳ Future | - |
| 15 | Implement `--prefix` flag | ⏳ Future | - |
| 16 | Auto-detect annotation source | ✅ Done | b3b4d01 |
| 17 | Create tools_runner module | ✅ Done | b3b4d01 |
| 18 | Update ref/query prefix | ⏳ Future | - |
| 19 | Avoid hardcoding | ✅ Done | b3b4d01 |
| 20 | Create config.yaml | ✅ Done | b3b4d01 |
| 21 | Assess code duplication | ✅ Done | b3b4d01 |
| 22 | Create plot/utils.py | ✅ Done | b3b4d01 |
| 23 | Create plot/config.py | ✅ Done | b3b4d01 |
| 24 | Create single tools module | ✅ Done | b3b4d01 |
| 25 | Create template/dry-code | ✅ Done | b3b4d01 |
| 26 | Test Suite Analysis issues | ✅ Done | b3b4d01 |
| 27 | Documentation Analysis | ⏳ Pending | - |
| 28 | Update CODE_REVIEW_REPORT.md | ⏳ Pending | - |
| 29 | Fix empty `__init__.py` | ✅ Done | b3b4d01 |
| 30 | Run without command prompt | ✅ Done | b3b4d01 |

**Completion Rate: 26/30 (87%)**

---

## Completed Task Details (Archived)

> **Note:** Most tasks from Section 6 were completed in commit b3b4d01 (2026-01-20).
> Below is the archived record of what was accomplished.

---

### ✅ Task 1: Create ToolsRunner module - DONE

**Created:** `tools_runner.py` with:
- `ToolsRunner` class with 8 tool methods
- `detect_annotation_source()` method
- Common interface: `run()`, `check_installed()`, `parse_output()`

---

### ✅ Task 2-3: Hardcoded fixes - PARTIALLY DONE

**Completed:**
- Created `config.yaml` for configurable paths
- Fixed hardcoded test path in `test/test_all_outputs.py`

**Future:**
- Implement `--prefix` flag for dynamic column naming

---

### ✅ Tasks 4-6: Plotting utilities - DONE

**Created:**
- `plot/config.py` - Shared configuration and palettes
- `plot/utils.py` - Shared data loading functions

---

### ✅ Tasks 7-8: synonym_mapping_parse.py - DONE

**Fixed:**
- Rewrote entire file to fix IndentationError
- Removed unused imports

---

### ✅ Tasks 9-11: Script renaming - DONE

**Renamed:**
- `detect_advanced_scenarios.py` → `gsmc.py`
- `detect_one2many_mappings.py` → `mapping_multiplicity.py`
- `pariwise_align_prot.py` → `pairwise_align_prot.py`

---

### ✅ Tasks 12-16: Test & Import fixes - DONE

**Fixed:**
- Test import paths
- README directory structure
- Created `requirements.txt`

---

### ✅ Task 19: __init__.py - DONE

**Added docstrings to:**
- `gene_pav/__init__.py`
- `plot/__init__.py`

---

## Remaining Tasks

### ⏳ Task 13-15, 18: Prefix handling (Future)

Implement `--prefix` flag for dynamic column naming in synonym_mapping_parse.py

### ⏳ Task 27: Documentation Review

Review docs/ folder to ensure accuracy with new file names

### ⏳ Task 28: Update CODE_REVIEW_REPORT.md

Update sections 6 and 8 to reflect completed fixes

---

