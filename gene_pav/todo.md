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
