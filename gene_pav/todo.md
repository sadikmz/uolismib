# PAVprot Pipeline - Development Todo

> **Branch:** dev
> **Last Updated:** 2026-01-19

---

## Current Status

- [x] Set up dev branch on uolismib/gene_pav
- [x] Copy files from uolocal/fungidb/dev/gene_pav
- [x] Organize project scripts into `project_scripts/` subfolder

---

## Priority Tasks

### 1. Code Cleanup (top priority )

- [ ] Extensively and critically review the entire pipeline
- [ ] Revisit critically individual scripts, input/output files, and documentation
- [ ] Review plotting scripts and assess if any project_scripts/*.py should be integrated into main plotting scripts
- [ ] Assess integrating project_scripts/run_pipeline.py into the main script to allow running all or specific parts
- [ ] All of the codes of files have to assessed, examined, and review critically 
- [ ] Extensively and critically review file organization  
- [ ] Suggest scripts to be combined or split
- [ ] Do not copy or delet files
- [ ] Complete all review without user command prompts   
- [ ] Provide extensive report in markdown if possible for each files and show how each files are connected to the pipeline 

### 2. Initial tidy-up

- [ ] Remove hardcoded paths from all pipeline scripts
- [ ] Rename detect_advanced_scenarios.py gamc.py (Gene Annotation Mapping Classifier) 
- [ ] Review and update docstrings
- [ ] Ensure all imports are correct after file reorganization

### 3. Tidy up and review code

2. [ ] Commit changes to dev branch
3. [ ] Push dev branch to remote
4. [ ] Review and merge to main

### 4. Documentation

- [ ] Update main README.md with usage examples
- [ ] Review docs/ folder for accuracy
- [ ] Add installation instructions
- [ ] Document dependencies (requirements.txt)

### 4. Testing

- [ ] Test pipeline with sample data
- [ ] Run existing tests in test/ folder
- [ ] Fix any failing tests
- [ ] Add tests for new modules if needed

### 5. project_scripts/ Folder

- [ ] Update paths in project_scripts/ to be configurable
- [ ] Add example config file or CLI arguments
- [ ] Update project_scripts/README.md with usage

### 6. Codebase review note (Top priority 20/01/2026)

- [ ] Ref: doc/CODE_REVIEW_REPOR.md under "Critical Issues Found"
  - [ ] `synonym_mapping_parse.py` - Syntax error, non-functional
  - [ ] README directory mismatch, Test import path
  - [ ] Code duplication, Filename typo, Hardcoded test path
  - [ ] Documentation gaps, Unused imports, Missing requirements.txt
  - [ ] Ref: doc/CODE_REVIEW_REPOR.md under "Critical Issues Found"fajflajf


- [ ] Ref: doc/CODE_REVIEW_REPOR.md under "Core Pipeline Scripts Analysis"

  - [ ] Renaming scripts or resolving typos

    - [ ] `pariwise_align_prot.py` typo in name 
    - [ ] suggest new name for detect_one2many_mappings 
    - [ ] `1.3 Filename Typo` 

  - [ ] `synonym_mapping_parse.py` broken: 

    - [ ] `IndentationError: unindent does not match any outer indentation level (line 59)`
    - [ ] **Lines 6-17** - Hardcoded project-specific column names
      - [ ] Suggestion: 
        - [ ] parse/get the prefix "GCF_013085055.1" and "FungiDB-68_Fo47" from input. 
        - [ ] eg --prefix (note: comma prefix input file annotation or genome for old and new annotations, by detault old annotation as "old" and new annotation as "new")
        - [ ] when --prefix not provide input of old vs new annotation will be autodetected from `Tools running module`. See `8. Future: Unified External Tools Module`in RUN_PIPELINE_INTEGRATION_ASSESSMENT.md
          - [ ] First create a mock/dry module to `tools running` - pick appropriate naming for this module 
        - [ ] So any ref and query or qry prefix need to be updated to the associated prefix of the input files example in ref_gene, ref_transcript, query_gene, query_transcript etc...
        - [ ] eg. GCF_013085055.1 is new annotation and FungiDB-68_Fo47 is old annotation  
        - [ ] ​	 

  - [ ] Document any hardcoded lines

    - [ ] avoid hardcoding 
    - [ ] suggest a solution to avoid hardcoding including file path, prefix and full file names and other related aspects
    - [ ] Example in 3.2 Hardcoded Paths (Expected - These Are Examples)
    - [ ] Example in 4.3 Hardcoded Path in Tests

  - [ ] Code Duplication Issue eg below in plotting script but can also exist in other scripts

    - [ ] plotting 
      - [ ] See in 2.2 Code Duplication Issue plotting scripts
      - [ ] Assess the code and suggest a better implementation or if the existing way is the best way to handle
      - [ ] Assess different version in `plot_ipr_comparison.py` what is different from the other function where the functionality in this script adapted other scripts. Assess also the recommendation: Create `plot/utils.py` with shared functions. 
      - [ ] Common Boilerplate (plotting scripts repeat):
        - [ ] Assess the suggeison - Move to `plot/config.py`.

  - [ ] Integration Assessment

    - [ ] Create a single module for internally running tools - pick appropriate naming for this modul. See note in 4.3 Future Integration Note

    - [ ] Create a template / dry-code module that will used to write the full implementation. See note in 4.3 Future Integration Note 

      > **PLANNED:** External tool execution is planned to be consolidated into a single unified module. This will include:
      >
      > - **Psauron** - Protein structure quality scoring
      > - **ProteinX/AlphaFold** - pLDDT confidence scores
      > - **DIAMOND** - BLAST-based protein alignment
      > - **InterProScan** - Domain/motif detection
      > - **gffcompare** - GFF comparison and tracking
      > - **Liftoff** - Annotation liftover
      > - **Pairwise alignment** - Protein sequence alignment
      >
      > Once this unified external tools module is implemented, the Psauron and pLDDT visualization features can be reconsidered for integration into the main `plot/` modules.

  - [ ] Address issues in Test Suite Analysis. See section 4. Test Suite Analysis

  - [ ] Resolve 5. Documentation Analysis, 

  - [ ] Update 6. Recommended Actions and 8. Summary

  - [ ] `__init__.py` empty 

  - [ ] Run this without command prompt

---

## File Structure

```
gene_pav/
├── Core Pipeline (root level)
│   ├── pavprot.py                    # Main orchestrator
│   ├── parse_interproscan.py         # IPR domain parsing
│   ├── detect_advanced_scenarios.py  # Scenario classification
│   ├── bidirectional_best_hits.py    # BBH analysis
│   ├── detect_one2many_mappings.py   # Mapping detection
│   ├── pariwise_align_prot.py        # Protein alignment
│   └── ...
│
├── project_scripts/                  # Project-specific examples
│   ├── run_pipeline.py
│   ├── run_emckmnje1_analysis.py
│   ├── analyze_fungidb_species.py
│   └── plot_*.py
│
├── plot/                             # Generic plotting modules
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

## Codebase review note (Top priority 20/01/2026)

**Lines 64-137**

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
- "comma prefix input file annotation or genome for old and new annotations"
- "by detault old annotation as "old" and new annotation as "new""

---

##### Line 89-90:
```
- [ ] when --prefix not provide input of old vs new annotation will be autodetected from `Tools running module`. See `8. Future: Unified External Tools Module`in RUN_PIPELINE_INTEGRATION_ASSESSMENT.md
- [ ] First create a mock/dry module to `tools running` - pick appropriate naming for this module
```

**Task (Line 89):** When `--prefix` not provided, input of old vs new annotation will be autodetected from `Tools running module`

**Reference:** See `8. Future: Unified External Tools Module` in RUN_PIPELINE_INTEGRATION_ASSESSMENT.md

**Sub-task (Line 90):** First create a mock/dry module to `tools running` - pick appropriate naming for this module

---

##### Line 91:
```
- [ ] So any ref and query or qry prefix need to be updated to the associated prefix of the input files example in ref_gene, ref_transcript, query_gene, query_transcript etc...
```

**Task:** Any ref and query or qry prefix need to be updated to the associated prefix of the input files

**Examples given:** ref_gene, ref_transcript, query_gene, query_transcript etc...

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
        - [ ] Assess the suggeison - Move to `plot/config.py`.
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
    - [ ] Create a single module for internally running tools - pick appropriate naming for this modul. See note in 4.3 Future Integration Note
    - [ ] Create a template / dry-code module that will used to write the full implementation. See note in 4.3 Future Integration Note
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

| # | Task | Reference |
|---|------|-----------|
| 1 | `synonym_mapping_parse.py` - Syntax error, non-functional | Line 67 |
| 2 | README directory mismatch | Line 68 |
| 3 | Test import path | Line 68 |
| 4 | Code duplication | Line 69 |
| 5 | Filename typo | Line 69 |
| 6 | Hardcoded test path | Line 69 |
| 7 | Documentation gaps | Line 70 |
| 8 | Unused imports | Line 70 |
| 9 | Missing requirements.txt | Line 70 |
| 10 | `pariwise_align_prot.py` typo in name | Line 78 |
| 11 | Suggest new name for detect_one2many_mappings | Line 79 |
| 12 | Fix IndentationError in synonym_mapping_parse.py line 59 | Line 84 |
| 13 | Fix hardcoded column names (Lines 6-17) in synonym_mapping_parse.py | Line 85 |
| 14 | Parse/get prefix from input | Line 87 |
| 15 | Implement `--prefix` flag | Line 88 |
| 16 | Auto-detect old vs new annotation from Tools running module | Line 89 |
| 17 | Create mock/dry module for tools running | Line 90 |
| 18 | Update ref/query/qry prefix to associated prefix of input files | Line 91 |
| 19 | Avoid hardcoding | Line 97 |
| 20 | Suggest solution to avoid hardcoding (file path, prefix, full file names) | Line 98 |
| 21 | Assess code duplication in plotting scripts | Line 105-106 |
| 22 | Assess `plot_ipr_comparison.py` differences; assess `plot/utils.py` recommendation | Line 107 |
| 23 | Assess suggestion to move boilerplate to `plot/config.py` | Line 108-109 |
| 24 | Create single module for running tools | Line 113 |
| 25 | Create template/dry-code module for full implementation | Line 115 |
| 26 | Address Test Suite Analysis issues | Line 129 |
| 27 | Resolve Documentation Analysis | Line 131 |
| 28 | Update Recommended Actions and Summary | Line 133 |
| 29 | Fix empty `__init__.py` | Line 135 |
| 30 | Run without command prompt | Line 137 |

---

## Suggestions for Each Task (Renumbered by Priority)

> **Instruction:** Run without command prompt - execute tasks autonomously without asking for confirmation at each step.

---

### Task 1: Create ToolsRunner module

**Priority: 1**

**Includes:**
- Create mock/dry module for tools running
- Create single module for running tools
- Create template/dry-code module for full implementation

**Suggestions:**

- Create `tools_runner.py` with stub functions:

```python
class ToolsRunner:
    """Unified external tools module (template)"""

    def run_diamond(self): pass
    def run_interproscan(self): pass
    def run_gffcompare(self): pass
    def run_liftoff(self): pass
    def run_psauron(self): pass
    def run_pairwise_alignment(self): pass
    def detect_annotation_source(self): pass
    def run_BUSCO(self): pass
```

- Create `tools_runner.py` at root level with class-based design for all 8 tools listed in lines 117-127

* Create `tools_runner.py` with:

- Abstract base class `ExternalTool`
- Stub implementations for each tool
- Common interface: `run()`, `check_installed()`, `parse_output()`

---

### Task 2: Auto-detect old vs new annotation from Tools running module

**Priority: 2**

**Suggestion:** Defer until Task 1 (ToolsRunner module) is created. The tools module will provide annotation source detection.

---

### Task 3: Prefix handling and hardcoded fixes

**Priority: 3**

**Includes:**
- Update ref/query/qry prefix to associated prefix of input files
- Parse/get prefix from input
- Implement `--prefix` flag
- Fix hardcoded column names
- Fix hardcoded test path

**Suggestion:** When user provides `--prefix A,B` which corresponds to old, new annotations, respectively:

- Map `ref_*` columns to the associated prefix to new annotation
- Map `query_*` or `qry_*` columns to the associated prefix old annotation
- Example: `ref_gene` displays with prefix from new annotation, `query_gene` with prefix from old annotation

**Suggestions:**

- Add function to extract prefix from gene IDs:

```python
def detect_prefix(gene_id):
    # Extract prefix before _gene or _transcript
    pass
```

- Based on line 88 instructions:

```python
parser.add_argument('--prefix',
    help='Comma-separated prefix for input file annotation or genome for old and new annotations. Default: old,new')
```

- Replace hardcoded column names with generic names or make configurable via `--prefix`

**Current State:**

```python
NAMES = [
"GCF_013085055.1_gene",
"GCF_013085055.1_transcript",
...
]
```

- **Hard coded path current State:** `test/test_all_outputs.py:14` has `/Users/sadik/...`

- Change to hardcoded path to `sys.path.insert(0, '..')`

- Use CLI arguments for all paths
- Use config files (YAML/JSON) for defaults
- Use `Path` objects with relative paths

---

### Task 4: Suggest solution to avoid hardcoding

**Priority: 5**

**Suggestion:** Create `config.py` or `config.yaml`:

```yaml
defaults:
  output_dir: "./output"
  temp_dir: "./tmp"
prefixes:
  old: "old"
  new: "new"
```

---

### Task 5: Assess code duplication in plotting scripts

**Priority: 6**

**Suggestion:** Review `load_data()` in:

- `plot_ipr_advanced.py:23`
- `plot_ipr_shapes.py:19`
- `plot_ipr_gene_level.py:20`
- `plot_ipr_proportional_bias.py:20`

Consolidate into `plot/utils.py`

---

### Task 6: Assess plot_ipr_comparison.py and boilerplate

**Priority: 7**

**Includes:**
- Assess `plot_ipr_comparison.py` differences
- Assess suggestion to move boilerplate to `plot/config.py`

**Current State:** Uses `load_pavprot_data()` (different name, extra processing)

**Suggestion:**
- Keep `load_pavprot_data()` in `plot/utils.py` as the main function
- Have `load_data()` call it or alias it
- Document the difference

**Current boilerplate repeated in 6 files:**
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
```

**Suggestion:** Create `plot/config.py`:
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def setup_plotting():
    sns.set_style("whitegrid")
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['savefig.dpi'] = 300
```

---

### Task 7: Fix `synonym_mapping_parse.py` - Syntax error, non-functional

**Priority: 8**

**Current State:** Two scripts concatenated together, IndentationError at line 59

**Note:** This should come after:
  - Creating dry code for class `ToolsRunner`
  - Resolving file prefix which will be used for output files and associated variable naming

**Suggestion:**

- Delete lines 59-93 (the second concatenated script)
- Fix line 27: Change `df.groupby["GCF_013085055.1_gene"]` to `df.groupby("GCF_013085055.1_gene")`
- Remove unused import `from curses import start_color` (line 3)

---

### Task 8: Fix IndentationError in synonym_mapping_parse.py line 59

**Priority: 9**

**Suggestion:** Delete lines 59-93 (second concatenated script with wrong indentation)

---

### Task 9: Suggest new names for scripts

**Priority: 10**

- Critically assess the functionality of detect_advanced_scenarios.py and scripts detect_one2many_mappings, if there any duplication or unique aspects
- Suggest if can be combined, duplicated or unique
- Suggest new name for detect_advanced_scenarios.py (eg. GSMC.py - gene_synteny_mapping_classifier)
- Suggest new names for scripts detect_one2many_mappings
- Suggest a descriptive name for detect_one2many_mappings if it's unique and need to standalone

**Suggestions:**

- GSMC.py (gene synteny mapping classifier) for detect_advanced_scenarios.py

---

### Task 10: Unused imports

**Priority: 11**

**Current State:** `from curses import start_color` in synonym_mapping_parse.py

**Suggestion:** Remove unused imports from all files (run `flake8` or manual review)

---

### Task 11: Filename typo

**Priority: 12**

- `pariwise_align_prot.py`
- Check other scripts

**Suggestion:**

- Rename file: `pariwise_align_prot.py` → `pairwise_align_prot.py`, and update import in `pavprot.py`

---

### Task 12: Code duplication

**Priority: 13**

**Current State:** `load_data()` duplicated in 4 plotting files

**Suggestion:** Create `plot/utils.py` with shared function, update imports in all 4 files

---

### Task 13: Test import path

**Priority: 14**

**Current State:** Tests fail with `ModuleNotFoundError: No module named 'pavprot'`

**Suggestion:** Add to top of each test file:

```python
import sys
sys.path.insert(0, '..')
```

---

### Task 14: README directory mismatch

**Priority: 15**

**Current State:** README references `core/`, `analysis/`, `utils/`, `tests/` which don't exist

**Suggestion:** Update README.md to show actual structure:
```
gene_pav/
├── *.py                 # Core scripts at root
├── plot/
├── project_scripts/
├── test/                # Not tests/
└── docs/
```

---

### Task 15: Missing requirements.txt

**Priority: 16**

**Suggestion:** Create `requirements.txt`:

```
pandas>=1.3.0
biopython>=1.79
matplotlib>=3.4.0
seaborn>=0.11.0
numpy>=1.21.0
```

---

### Task 16: Address Test Suite Analysis issues

**Priority: 17**

**Suggestion:**

- Add `sys.path.insert(0, '..')` to all test files
- Fix hardcoded path in `test_all_outputs.py`
- Run `python -m pytest test/` to verify

---

### Task 17: Resolve Documentation Analysis and gaps

**Priority: 18**

**Suggestion:**

- Review docs/ folder, ensure each script has corresponding documentation

- Update README.md structure
- Ensure docs match actual file organization
- Add missing installation instructions

---

### Task 18: Update Recommended Actions and Summary

**Priority: 19**

**Suggestion:** Update CODE_REVIEW_REPORT.md sections 6 and 8 after completing fixes

---

### Task 19: Fix empty `__init__.py` files

**Priority: 20**

**Suggestion:** Add docstrings:

`gene_pav/__init__.py`:
```python
"""PAVprot Pipeline - Gene Annotation Presence/Absence Variation Analysis"""
```

`plot/__init__.py`:
```python
"""Plotting modules for PAVprot output visualization"""
```

---

