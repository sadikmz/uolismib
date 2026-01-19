# PAVprot Pipeline - Development Todo

> **Branch:** dev
> **Last Updated:** 2026-01-19

---

## Current Status

- [x] Set up dev branch on uolismib/gene_pav
- [x] Copy files from uolocal/fungidb/dev/gene_pav
- [x] Organize project scripts into `project_scripts/` subfolder
- [ ] Tidy up and review code
- [ ] Commit changes to dev branch
- [ ] Push dev branch to remote
- [ ] Review and merge to main

---

## Priority Tasks

### 1. Code Cleanup

- [ ] Remove hardcoded paths from core pipeline scripts
- [ ] Review and update docstrings
- [ ] Ensure all imports are correct after file reorganization
- [ ] Test pipeline with sample data

### 2. Documentation

- [ ] Update main README.md with usage examples
- [ ] Review docs/ folder for accuracy
- [ ] Add installation instructions
- [ ] Document dependencies (requirements.txt)

### 3. Testing

- [ ] Run existing tests in test/ folder
- [ ] Fix any failing tests
- [ ] Add tests for new modules if needed

### 4. project_scripts/ Folder

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
