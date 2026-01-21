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

*Generated: 2026-01-19*
