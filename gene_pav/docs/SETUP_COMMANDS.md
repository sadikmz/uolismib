# gene_pav GitHub Setup Commands

Commands used to set up the dev branch and organize the repository.

---

## 1. Git Branch Setup

```bash
# Navigate to uolismib/gene_pav
cd /Users/sadik/projects/github_prj/uolismib/gene_pav

# Create and switch to new dev branch
git checkout -b dev
```

---

## 2. Copy Files from uolocal

```bash
# Copy analysis scripts
cp /Users/sadik/projects/github_prj/uolismib/uolocal/fungidb/dev/gene_pav/analysis/*.py /Users/sadik/projects/github_prj/uolismib/gene_pav/

# Copy utils
cp /Users/sadik/projects/github_prj/uolismib/uolocal/fungidb/dev/gene_pav/utils/*.py /Users/sadik/projects/github_prj/uolismib/gene_pav/

# Copy root level scripts
cp /Users/sadik/projects/github_prj/uolismib/uolocal/fungidb/dev/gene_pav/*.py /Users/sadik/projects/github_prj/uolismib/gene_pav/
cp /Users/sadik/projects/github_prj/uolismib/uolocal/fungidb/dev/gene_pav/*.sh /Users/sadik/projects/github_prj/uolismib/gene_pav/
cp /Users/sadik/projects/github_prj/uolismib/uolocal/fungidb/dev/gene_pav/*.md /Users/sadik/projects/github_prj/uolismib/gene_pav/

# Copy directories
cp -r /Users/sadik/projects/github_prj/uolismib/uolocal/fungidb/dev/gene_pav/plot /Users/sadik/projects/github_prj/uolismib/gene_pav/
cp -r /Users/sadik/projects/github_prj/uolismib/uolocal/fungidb/dev/gene_pav/test /Users/sadik/projects/github_prj/uolismib/gene_pav/
cp -r /Users/sadik/projects/github_prj/uolismib/uolocal/fungidb/dev/gene_pav/docs /Users/sadik/projects/github_prj/uolismib/gene_pav/

# Copy .gitignore
cp /Users/sadik/projects/github_prj/uolismib/uolocal/fungidb/dev/gene_pav/.gitignore /Users/sadik/projects/github_prj/uolismib/gene_pav/
```

---

## 3. Organize Project Scripts

```bash
# Create project_scripts folder
mkdir -p project_scripts

# Move project-specific scripts to subfolder
mv run_pipeline.py project_scripts/
mv run_emckmnje1_analysis.py project_scripts/
mv analyze_fungidb_species.py project_scripts/
mv plot_oldvsnew_psauron_plddt.py project_scripts/
mv plot_ipr_1to1_comparison.py project_scripts/
mv plot_psauron_distribution.py project_scripts/
mv project_scripts_README.md project_scripts/README.md
```

---

## 4. Commit and Push

```bash
# Stage all changes
git add -A

# Commit
git commit -m "Add enhanced PAVprot pipeline with scenario detection

- Enhanced pavprot.py with scenario detection and quality metrics
- Added gsmc.py for orthology classification
- Added bidirectional_best_hits.py for BBH analysis
- Added comprehensive documentation in docs/
- Added plotting modules in plot/
- Added test suite
- Moved project-specific scripts to project_scripts/

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

# Push to remote dev branch
git push origin dev
```

---

## 5. Merge to Main (when ready)

```bash
# Switch to main branch
git checkout main

# Merge dev into main
git merge dev

# Push main to remote
git push origin main
```

---

## Directory Structure After Setup

```
gene_pav/
├── pavprot.py                    # Main pipeline
├── parse_interproscan.py         # IPR parsing
├── gsmc.py  # Scenario classification
├── bidirectional_best_hits.py    # BBH analysis
├── mapping_multiplicity.py   # Mapping detection
├── pairwise_align_prot.py        # Protein alignment
├── ...
│
├── project_scripts/              # Project-specific (Fo47)
│   ├── README.md
│   ├── run_pipeline.py
│   ├── run_emckmnje1_analysis.py
│   ├── analyze_fungidb_species.py
│   └── plot_*.py
│
├── plot/                         # Generic plotting modules
├── docs/                         # Documentation
├── test/                         # Unit tests
└── README.md
```

---

## Earlier Commands (uolocal Setup)

### Rename dev_workspace to dev

```bash
cd /Users/sadik/projects/github_prj/uolismib/uolocal/fungidb

# Rename directory
mv dev_workspace dev
```

### Remove core/ Duplicates

The `core/` directory contained identical copies of files in `analysis/`. Removed to avoid duplication.

```bash
cd /Users/sadik/projects/github_prj/uolismib/uolocal/fungidb/dev/gene_pav

# Remove duplicate core/ directory
rm -rf core/
```

### Commit and Push to uolocal

```bash
cd /Users/sadik/projects/github_prj/uolismib/uolocal/fungidb/dev/gene_pav

# Stage and commit
git add -A
git commit -m "Removed core/ duplicates (files were identical to analysis/) Added sync_to_github.sh script Added project_scripts_README.md"

# Commit rename
cd /Users/sadik/projects/github_prj/uolismib/uolocal/fungidb
git add -A
git commit -m "Rename dev_workspace to dev for cleaner directory structure"

# Push to uolocal GitHub
git push origin main
```

---

## Delete and Recreate dev Branch (uolismib)

```bash
cd /Users/sadik/projects/github_prj/uolismib/gene_pav

# Switch to main
git checkout main

# Delete local dev branch
git branch -D dev

# Delete remote dev branch
git push origin --delete dev

# Create fresh dev branch
git checkout -b dev
```

---

## Repository URLs

| Repo | URL | Purpose |
|------|-----|---------|
| uolocal | `git@github.com:sadikmz/uolocal.git` | Testing/working repo |
| uolismib | `git@github.com:sadikmz/uolismib.git` | Main public repo |

---

## Git Branch Management

### List Branches

```bash
# List local branches (* = current, + = checked out in worktree)
git branch

# List all branches (local and remote)
git branch -a
```

### Switch Branches

```bash
# Switch to existing branch
git checkout branch_name

# Or (newer syntax)
git switch branch_name

# Create and switch to new branch
git checkout -b new_branch_name
```

### Delete Branches

```bash
# Delete local branch (safe - won't delete if unmerged)
git branch -d branch_name

# Force delete local branch (even if unmerged)
git branch -D branch_name

# Delete remote branch
git push origin --delete branch_name
```

### Compare Branches

```bash
# Show commits on branch_a not in branch_b
git log branch_b..branch_a --oneline

# Show file differences between branches
git diff branch_a..branch_b --stat

# Show detailed diff
git diff branch_a..branch_b
```

### Assess a Branch

```bash
# View last N commits on a branch
git log branch_name --oneline -10

# Compare branch to main
git diff main..branch_name --stat

# Compare branch to dev
git diff dev..branch_name --stat

# List worktrees (shows where branches are checked out)
git worktree list
```

---

## Git Worktrees Explained

A **worktree** lets you have multiple branches checked out at the same time in different directories.

### Normal Git (without worktrees)

```
/my-repo/           ← only ONE branch at a time
├── .git/
├── file1.py
└── file2.py

# To switch: git checkout other-branch
# Problem: ALL files change, can't work on both simultaneously
```

### With Worktrees

```
/my-repo/                          ← main branch
├── .git/
├── file1.py
└── file2.py

/another-folder/worktree-dev/      ← dev branch (separate folder)
├── file1.py
└── file2.py

# Both branches exist simultaneously!
# Edit main in one folder, dev in another
```

### Your Current Setup

```
/Users/sadik/projects/github_prj/uolismib                    ← dev branch
/Users/sadik/.claude-worktrees/uolismib/focused-lumiere      ← focused-lumiere branch
```

### Why Use Worktrees?

| Use Case | Benefit |
|----------|---------|
| Compare branches side-by-side | Open both in different editor windows |
| Run tests on one branch while coding another | No need to stash/switch |
| Long-running builds | Build on main while developing on feature branch |
| Quick hotfix | Fix main without losing work in progress |

### Common Commands

```bash
# Add worktree
git worktree add ../feature-branch feature-branch

# List worktrees
git worktree list

# Remove worktree
git worktree remove ../feature-branch

# Prune stale worktree entries
git worktree prune
```

**Note:** A `+` sign in `git branch` output indicates the branch is checked out in another worktree.

---

## Section 4: Running a Test Job (2026-01-21)

### CLI Fix: mapping_multiplicity.py

Added argparse support to `mapping_multiplicity.py` for proper `--help` handling:

```python
# Added import
import argparse

# Replaced sys.argv-based main() with:
def main():
    parser = argparse.ArgumentParser(
        description='Detect multiple mapping genes (1-to-many and many-to-1 relationships)')
    parser.add_argument('input_file',
                        help='Path to synonym_mapping_liftover_gffcomp.tsv')
    parser.add_argument('--output-prefix', '-o',
                        help='Prefix for output files (default: input filename)')
    args = parser.parse_args()
    detect_multiple_mappings(args.input_file, args.output_prefix)
```

### Integration Test Wrapper Script

Created `test/run_integration_test.sh` for automated testing with timestamped output:

```bash
#!/bin/bash
# Run integration test with timestamped output directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="test/output_${TIMESTAMP}"

python pavprot.py \
  --gff-comp test/data/gffcompare.tracking \
  --gff test/data/gff_feature_table.gff3 \
  --interproscan-out test/data/test_interproscan.tsv \
  --output-dir "${OUTPUT_DIR}" \
  --output-prefix integration_test \
  2>&1 | tee "${OUTPUT_DIR}/test_run.log"
```

### Test Results

```
# Run unit tests
python -m pytest test/ -v
# Result: 47 passed, 2 skipped

# Run integration test
./test/run_integration_test.sh
# Result: 3 gene pairs detected, all E (1:1 orthologs)
```

### Git Commands

```bash
# Commit CLI fix and test wrapper
git add mapping_multiplicity.py test/run_integration_test.sh
git commit -m "Add argparse to mapping_multiplicity.py and create integration test wrapper

- Fix mapping_multiplicity.py CLI to support --help
- Add test/run_integration_test.sh with timestamped output
- All 47 tests pass, 2 skipped

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

---

## Section 5: Pre-Release Automation (2026-01-26)

### Created Automation Script

```bash
# Create scripts directory
mkdir -p scripts

# Create pre-release check script (see scripts/pre_release_check.sh)
# Make executable
chmod +x scripts/pre_release_check.sh
```

### Pre-Release Script Usage

```bash
# Quick check (linter + tests + CLI)
./scripts/pre_release_check.sh

# Full check (includes clean venv test)
./scripts/pre_release_check.sh --full

# Individual checks
./scripts/pre_release_check.sh --lint   # Linting only
./scripts/pre_release_check.sh --test   # Tests only
./scripts/pre_release_check.sh --cli    # CLI help checks only

# Show help
./scripts/pre_release_check.sh --help
```

### What the Script Checks

| Phase | Check | Command Used |
|-------|-------|--------------|
| 1.1 | Critical lint errors | `flake8 *.py plot/*.py --select=E9,F63,F7,F82` |
| 1.1 | Style warnings | `flake8 *.py plot/*.py --max-line-length=120` |
| 1.1 | Unit tests | `python -m pytest test/ -v --tb=short` |
| 3 | CLI help | `python <module>.py --help` for each module |
| 3 | Integration test | `./test/run_integration_test.sh` |
| 3 | Clean venv | Creates temp venv, installs deps, runs tests |

### Linting Commands Explained

```bash
# Install flake8 (if not installed)
pip install flake8

# Check for critical errors only (syntax errors, undefined names)
flake8 *.py --select=E9,F63,F7,F82 --show-source

# Full check with style warnings
flake8 *.py --max-line-length=120 --statistics

# Check specific directories
flake8 *.py plot/*.py project_scripts/*.py
```

**Error codes:**
- `E9xx`: Runtime/syntax errors (critical)
- `F63`: Invalid `__future__` imports
- `F7`: Syntax errors in type comments
- `F82`: Undefined names (critical)
- `E501`: Line too long (style)
- `W503`: Line break before binary operator (style)

---

---

## Section 6: Linting Fixes (2026-01-26)

### Issue 1: Undefined Functions in `plot/plot_ipr_advanced.py`

**Problem:** 5 functions were called but never defined (F821 errors)

```bash
# Identify the issue with flake8
flake8 plot/plot_ipr_advanced.py --select=F821
```

**Output:**
```
plot/plot_ipr_advanced.py:220:5: F821 undefined name 'plot_bland_altman'
plot/plot_ipr_advanced.py:222:5: F821 undefined name 'plot_delta_distribution'
plot/plot_ipr_advanced.py:223:5: F821 undefined name 'plot_violin_comparison'
plot/plot_ipr_advanced.py:224:5: F821 undefined name 'plot_cdf_comparison'
plot/plot_ipr_advanced.py:227:5: F821 undefined name 'plot_contour_density'
```

**Fix:** Added 5 missing function implementations:

| Function | Purpose | Lines Added |
|----------|---------|-------------|
| `plot_bland_altman()` | Method agreement analysis | ~35 |
| `plot_delta_distribution()` | Histogram + boxplot of differences | ~45 |
| `plot_violin_comparison()` | Violin plots query vs reference | ~50 |
| `plot_cdf_comparison()` | CDF with KS test | ~40 |
| `plot_contour_density()` | 2D density contour using KDE | ~50 |

### Issue 2: CLI --help Not Working in `synonym_mapping_summary.py`

**Problem:** Script used `sys.argv` directly instead of argparse

```bash
# Test CLI help
python synonym_mapping_summary.py --help
# Failed: showed usage error instead of help
```

**Fix:** Converted to argparse:

```python
# Before (sys.argv approach)
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: ...")
        sys.exit(1)
    generate_summary_statistics(sys.argv[1])

# After (argparse approach)
def main():
    parser = argparse.ArgumentParser(
        description='Generate summary statistics...')
    parser.add_argument('input_file', help='Path to TSV file')
    args = parser.parse_args()
    generate_summary_statistics(args.input_file)

if __name__ == '__main__':
    main()
```

### Verify Fixes

```bash
# Re-run pre-release check
./scripts/pre_release_check.sh

# Expected output:
# ✓ No critical linting errors
# ✓ All tests passed
# ✓ All CLI modules pass --help check
# ✓ All checks passed!
```

### Flake8 Error Codes Reference

| Code | Severity | Description |
|------|----------|-------------|
| E9xx | Critical | Runtime/syntax errors |
| F821 | Critical | Undefined name |
| F401 | Warning | Imported but unused |
| F841 | Warning | Variable assigned but never used |
| E501 | Style | Line too long |
| E731 | Style | Lambda assignment (use def instead) |
| C901 | Style | Function too complex |

---

---

## Section 7: Phases 1.2-3 Completion (2026-01-26)

### Phase 1.2: Documentation Tasks

```bash
# Created config template for project_scripts
# File: project_scripts/config.yaml.template

# Updated project_scripts/README.md with configuration guide

# Created CHANGELOG.md
# File: CHANGELOG.md
```

### Phase 2: Code Review

```bash
# Generated comprehensive pipeline architecture documentation
# File: docs/PIPELINE_ARCHITECTURE.md

# Contents:
# - Module summary table
# - Data flow diagram
# - Module dependency graph
# - CLI options reference
# - Output columns documentation
```

### Phase 3: Full Pre-Release Check

```bash
# Run full pre-release verification (including clean venv test)
./scripts/pre_release_check.sh --full

# Results:
# ✓ No critical linting errors
# ✓ 47 tests passed, 2 skipped
# ✓ All 7 CLI modules pass --help
# ✓ Tests pass in clean virtual environment
# ✓ All checks passed!
```

### Files Created This Session

| File | Purpose |
|------|---------|
| `scripts/pre_release_check.sh` | Automated pre-release verification |
| `project_scripts/config.yaml.template` | Configuration template |
| `CHANGELOG.md` | Version history |
| `docs/PIPELINE_ARCHITECTURE.md` | Module documentation |

---

*Updated: 2026-01-26*
