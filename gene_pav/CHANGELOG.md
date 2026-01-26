# Changelog

All notable changes to the PAVprot pipeline will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Pre-release automation script** (`scripts/pre_release_check.sh`)
  - Runs linter, tests, CLI checks automatically
  - Supports `--full` flag for clean venv testing
  - Color-coded output with detailed logging

- **Configuration templates**
  - `project_scripts/config.yaml.template` for configurable paths
  - Updated `project_scripts/README.md` with configuration guide

- **Missing plotting functions** in `plot/plot_ipr_advanced.py`
  - `plot_bland_altman()` - Method agreement analysis
  - `plot_delta_distribution()` - Distribution of differences
  - `plot_violin_comparison()` - Violin plots for query vs reference
  - `plot_cdf_comparison()` - CDF with Kolmogorov-Smirnov test
  - `plot_contour_density()` - 2D density contour plots

### Fixed
- `synonym_mapping_summary.py` - Added argparse for proper `--help` support
- Resolved F821 linting errors (undefined function names)

---

## [0.2.0] - 2026-01-21

### Added
- **New modules**
  - `tools_runner.py` - Unified external tools interface with 8 tool methods
  - `gsmc.py` - Gene Synteny Mapping Classifier (renamed from `detect_advanced_scenarios.py`)
  - `mapping_multiplicity.py` - Mapping detection (renamed from `detect_one2many_mappings.py`)

- **Infrastructure files**
  - `config.yaml` - Pipeline configuration
  - `requirements.txt` - Python dependencies with pinned versions
  - `plot/config.py` - Shared plotting configuration and palettes
  - `plot/utils.py` - Shared data loading utilities

- **Testing infrastructure**
  - `test/data/` - Sample test data files
  - `test/run_integration_test.sh` - Integration test wrapper
  - `test/test_gsmc.py` - Tests for scenario classification
  - `test/test_mapping_multiplicity.py` - Tests for mapping detection
  - `test/test_tools_runner.py` - Tests for tools runner
  - `test/test_edge_cases.py` - Edge case handling tests
  - `pytest.ini` - Pytest configuration

- **Documentation**
  - `docs/CODE_REVIEW_REPORT.md` - Comprehensive code review
  - `docs/SETUP_COMMANDS.md` - Git/bash command reference
  - `docs/RUN_PIPELINE_INTEGRATION_ASSESSMENT.md` - Pipeline integration notes

### Changed
- **Renamed modules for clarity**
  - `detect_advanced_scenarios.py` → `gsmc.py`
  - `detect_one2many_mappings.py` → `mapping_multiplicity.py`
  - `pariwise_align_prot.py` → `pairwise_align_prot.py` (typo fix)

- **Consolidated plotting utilities**
  - Moved shared code to `plot/utils.py` and `plot/config.py`
  - Reduced code duplication across plotting scripts

- **Improved module organization**
  - Project-specific scripts moved to `project_scripts/`
  - Generic plotting modules in `plot/`
  - Tests organized in `test/`

### Fixed
- `synonym_mapping_parse.py` - Fixed IndentationError, removed unused imports
- `test/test_all_outputs.py` - Removed hardcoded test path
- `test/test_pavprot.py` - Fixed import paths after reorganization
- `README.md` - Updated directory structure to match actual layout
- `mapping_multiplicity.py` - Added argparse for CLI support

### Removed
- Duplicate code across plotting scripts (consolidated to utils)
- Unused imports in various modules

---

## [0.1.0] - 2026-01-09

### Added
- Initial PAVprot pipeline with scenario detection
- Core modules:
  - `pavprot.py` - Main pipeline orchestrator
  - `parse_interproscan.py` - InterProScan output parsing
  - `bidirectional_best_hits.py` - BBH analysis
  - `pairwise_align_prot.py` - Protein sequence alignment
  - `synonym_mapping_summary.py` - Summary statistics
  - `inconsistent_genes_transcript_IPR_PAV.py` - IPR inconsistency detection
- Plotting modules in `plot/`
- Basic documentation

### Scenarios Detected
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

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| 0.2.0 | 2026-01-21 | Module reorganization, testing infrastructure, tools_runner |
| 0.1.0 | 2026-01-09 | Initial release with scenario detection |

---

*For detailed commit history, run: `git log --oneline`*
