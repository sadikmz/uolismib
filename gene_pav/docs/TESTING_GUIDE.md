# PAVprot Pipeline Testing Guide

> **Purpose:** Manual verification of the entire pipeline before release
> **Created:** 2026-01-26

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Quick Verification](#2-quick-verification)
3. [Running the Main Pipeline](#3-running-the-main-pipeline)
4. [Testing Individual Modules](#4-testing-individual-modules)
5. [Running Unit Tests](#5-running-unit-tests)
6. [Integration Testing](#6-integration-testing)
7. [Testing Plot Modules](#7-testing-plot-modules)
8. [Verification Checklist](#8-verification-checklist)

---

## 1. Prerequisites

### 1.1 Environment Setup

```bash
# Navigate to project directory
cd /Users/sadik/projects/github_prj/uolismib/gene_pav

# Verify Python version (requires 3.8+)
python --version

# Install dependencies
pip install -r requirements.txt

# Verify key dependencies
python -c "import pandas; print(f'pandas: {pandas.__version__}')"
python -c "import numpy; print(f'numpy: {numpy.__version__}')"
python -c "import Bio; print(f'biopython: {Bio.__version__}')"
```

### 1.2 Test Data Location

```bash
# Verify test data exists
ls -la test/data/

# Expected files:
# - gffcompare.tracking
# - gff_feature_table.gff3
# - test_interproscan.tsv
# - mock_*.faa (FASTA files)
# - mock_*.gff3 (GFF files)
```

### 1.3 External Tools (Optional)

```bash
# Check if DIAMOND is installed (optional, for BLASTP)
which diamond && diamond version

# Check if InterProScan is available (optional)
which interproscan.sh
```

---

## 2. Quick Verification

### 2.1 Run Pre-Release Check Script

```bash
# Quick check (linter + tests + CLI)
./scripts/pre_release_check.sh

# Full check (includes clean venv test)
./scripts/pre_release_check.sh --full

# Individual checks
./scripts/pre_release_check.sh --lint   # Linting only
./scripts/pre_release_check.sh --test   # Tests only
./scripts/pre_release_check.sh --cli    # CLI help only
```

### 2.2 Verify All CLI Help Commands

```bash
# Core pipeline
python pavprot.py --help

# Scenario classification
python gsmc.py --help

# Mapping analysis
python mapping_multiplicity.py --help

# BBH analysis
python bidirectional_best_hits.py --help

# Alignment
python pairwise_align_prot.py --help

# InterProScan parsing
python parse_interproscan.py --help

# Summary statistics
python synonym_mapping_summary.py --help
```

---

## 3. Running the Main Pipeline

### 3.1 Minimal Run (Tracking File Only)

```bash
# Create output directory
mkdir -p /tmp/pavprot_manual_test

# Run with just tracking file
python pavprot.py \
  --gff-comp test/data/gffcompare.tracking \
  --output-dir /tmp/pavprot_manual_test \
  --output-prefix minimal_test

# Check outputs
ls -la /tmp/pavprot_manual_test/
```

**Expected outputs:**
- `minimal_test_gffcomp.tsv` - Main transcript-level results
- `minimal_test_gene_level.tsv` - Gene-level with scenarios

### 3.2 Run with GFF Files

```bash
python pavprot.py \
  --gff-comp test/data/gffcompare.tracking \
  --gff test/data/gff_feature_table.gff3 \
  --output-dir /tmp/pavprot_manual_test \
  --output-prefix with_gff
```

### 3.3 Run with InterProScan Data

```bash
python pavprot.py \
  --gff-comp test/data/gffcompare.tracking \
  --gff test/data/gff_feature_table.gff3 \
  --interproscan-out test/data/test_interproscan.tsv \
  --output-dir /tmp/pavprot_manual_test \
  --output-prefix with_ipr
```

### 3.4 Full Pipeline with DIAMOND (if installed)

```bash
# Only if you have DIAMOND and FASTA files
python pavprot.py \
  --gff-comp test/data/gffcompare.tracking \
  --gff test/data/gff_feature_table.gff3 \
  --run-diamond \
  --ref-faa test/data/mock_reference.faa \
  --qry-faa test/data/mock_query.faa \
  --run-bbh \
  --output-dir /tmp/pavprot_manual_test \
  --output-prefix full_test
```

### 3.5 Verify Output Contents

```bash
# Check main output columns
head -1 /tmp/pavprot_manual_test/minimal_test_gffcomp.tsv | tr '\t' '\n' | nl

# Check gene-level scenarios
cat /tmp/pavprot_manual_test/minimal_test_gene_level.tsv | cut -f1-5,$(head -1 /tmp/pavprot_manual_test/minimal_test_gene_level.tsv | tr '\t' '\n' | grep -n scenario | cut -d: -f1)

# Count scenarios
awk -F'\t' 'NR>1 {print $NF}' /tmp/pavprot_manual_test/minimal_test_gene_level.tsv | sort | uniq -c
```

---

## 4. Testing Individual Modules

### 4.1 gsmc.py - Scenario Classification

```bash
# Test scenario detection on existing output
python gsmc.py --help

# The module is typically called internally by pavprot.py
# To test functions directly:
python -c "
from gsmc import get_cdi_genes, detect_one_to_one_orthologs
import pandas as pd

# Load test data
df = pd.read_csv('/tmp/pavprot_manual_test/minimal_test_gffcomp.tsv', sep='\t')
print(f'Loaded {len(df)} records')
print(f'Columns: {list(df.columns)[:10]}...')
"
```

### 4.2 mapping_multiplicity.py - Multi-Mapping Detection

```bash
# Run on pavprot output
python mapping_multiplicity.py \
  /tmp/pavprot_manual_test/minimal_test_gffcomp.tsv \
  --output-prefix /tmp/pavprot_manual_test/mapping_test

# Check outputs
ls -la /tmp/pavprot_manual_test/mapping_test*
cat /tmp/pavprot_manual_test/mapping_test_multiple_mappings_summary.txt
```

### 4.3 parse_interproscan.py - Domain Parsing

```bash
# Parse InterProScan file
python parse_interproscan.py --help

# Test parsing
python -c "
from parse_interproscan import InterProParser

parser = InterProParser()
df = parser.parse_tsv('test/data/test_interproscan.tsv')
print(f'Parsed {len(df)} domain entries')
print(df.head())
"
```

### 4.4 bidirectional_best_hits.py - BBH Analysis

```bash
# Show help
python bidirectional_best_hits.py --help

# Test class import
python -c "
from bidirectional_best_hits import BidirectionalBestHits, BlastHit
print('BidirectionalBestHits class loaded successfully')
print(f'BlastHit fields: {BlastHit.__dataclass_fields__.keys()}')
"
```

### 4.5 pairwise_align_prot.py - Local Alignment

```bash
# Show help
python pairwise_align_prot.py --help

# Test alignment function
python -c "
from pairwise_align_prot import local_alignment_similarity

seq1 = 'MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSH'
seq2 = 'MVLSGEDKSNIKAAWGKIGGHGAEYGAEALERMFASFPTTKTYFPHFDVSH'

result = local_alignment_similarity(seq1, seq2, 'test1', 'test2')
print(f'Identity: {result[\"identity\"]:.1f}%')
print(f'Coverage (seq1): {result[\"coverage_seq1\"]:.1f}%')
print(f'Coverage (seq2): {result[\"coverage_seq2\"]:.1f}%')
"
```

### 4.6 synonym_mapping_summary.py - Statistics

```bash
# Generate summary statistics
python synonym_mapping_summary.py /tmp/pavprot_manual_test/minimal_test_gffcomp.tsv
```

---

## 5. Running Unit Tests

### 5.1 Run All Tests

```bash
# Verbose output
python -m pytest test/ -v

# With coverage report
python -m pytest test/ -v --cov=. --cov-report=term-missing

# Stop on first failure
python -m pytest test/ -v -x
```

### 5.2 Run Specific Test Files

```bash
# Test pavprot core
python -m pytest test/test_pavprot.py -v

# Test scenario classification
python -m pytest test/test_gsmc.py -v

# Test mapping multiplicity
python -m pytest test/test_mapping_multiplicity.py -v

# Test tools runner
python -m pytest test/test_tools_runner.py -v

# Test edge cases
python -m pytest test/test_edge_cases.py -v
```

### 5.3 Run Specific Test Classes/Functions

```bash
# Run specific test class
python -m pytest test/test_gsmc.py::TestScenarioE -v

# Run specific test function
python -m pytest test/test_gsmc.py::TestScenarioE::test_one_to_one_detection -v
```

### 5.4 Expected Test Results

```
Expected: 47 passed, 2 skipped
- 2 skipped tests require external data or longer runtime
- All core functionality should pass
```

---

## 6. Integration Testing

### 6.1 Run Integration Test Script

```bash
# Run the integration test wrapper
./test/run_integration_test.sh

# Check output directory (timestamped)
ls -la test/output_*/

# View test log
cat test/output_*/test_run.log
```

### 6.2 Manual Integration Test

```bash
# Create timestamped output directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="/tmp/pavprot_integration_${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"

# Run full pipeline
python pavprot.py \
  --gff-comp test/data/gffcompare.tracking \
  --gff test/data/gff_feature_table.gff3 \
  --interproscan-out test/data/test_interproscan.tsv \
  --output-dir "$OUTPUT_DIR" \
  --output-prefix integration_test \
  2>&1 | tee "$OUTPUT_DIR/run.log"

# Verify outputs
echo "=== Output Files ==="
ls -la "$OUTPUT_DIR"

echo "=== Record Counts ==="
wc -l "$OUTPUT_DIR"/*.tsv

echo "=== Scenarios ==="
tail -n +2 "$OUTPUT_DIR"/integration_test_gene_level.tsv | cut -f$(head -1 "$OUTPUT_DIR"/integration_test_gene_level.tsv | tr '\t' '\n' | grep -n scenario | cut -d: -f1) | sort | uniq -c
```

### 6.3 Validate Output Structure

```bash
# Check required columns exist
python -c "
import pandas as pd
import sys

required_cols = ['ref_gene', 'ref_transcript', 'query_gene', 'query_transcript',
                 'class_code', 'exons', 'class_type_transcript']

df = pd.read_csv('$OUTPUT_DIR/integration_test_gffcomp.tsv', sep='\t')
missing = [c for c in required_cols if c not in df.columns]

if missing:
    print(f'ERROR: Missing columns: {missing}')
    sys.exit(1)
else:
    print('✓ All required columns present')
    print(f'  Total columns: {len(df.columns)}')
    print(f'  Total records: {len(df)}')
"
```

---

## 7. Testing Plot Modules

### 7.1 Verify Plot Module Imports

```bash
python -c "
from plot.config import setup_plotting, CLASS_TYPE_PALETTE, SCENARIO_PALETTE
from plot.utils import load_data, load_pavprot_data, filter_by_class_type

print('✓ plot.config imported successfully')
print(f'  CLASS_TYPE_PALETTE: {len(CLASS_TYPE_PALETTE)} colors')
print(f'  SCENARIO_PALETTE: {len(SCENARIO_PALETTE)} colors')

print('✓ plot.utils imported successfully')
"
```

### 7.2 Test Plot Generation (if you have real data)

```bash
# Test IPR comparison plot
python plot/plot_ipr_comparison.py --help

# Generate test plot (requires pavprot output with IPR data)
# python plot/plot_ipr_comparison.py /tmp/pavprot_manual_test/with_ipr_gffcomp.tsv -o /tmp/test_plot

# Test advanced plots
python plot/plot_ipr_advanced.py --help
```

### 7.3 Verify New Plot Functions

```bash
python -c "
from plot.plot_ipr_advanced import (
    plot_bland_altman,
    plot_delta_distribution,
    plot_violin_comparison,
    plot_cdf_comparison,
    plot_contour_density
)
print('✓ All 5 new plotting functions imported successfully')
"
```

---

## 8. Verification Checklist

Use this checklist to verify the pipeline is working correctly:

### Core Functionality

- [ ] `python pavprot.py --help` shows help
- [ ] Pipeline runs with just tracking file
- [ ] Pipeline runs with GFF file
- [ ] Pipeline runs with InterProScan data
- [ ] Gene-level output includes scenarios
- [ ] Mapping multiplicity detection works

### Individual Modules

- [ ] `python gsmc.py --help` works
- [ ] `python mapping_multiplicity.py --help` works
- [ ] `python bidirectional_best_hits.py --help` works
- [ ] `python pairwise_align_prot.py --help` works
- [ ] `python parse_interproscan.py --help` works
- [ ] `python synonym_mapping_summary.py --help` works

### Tests

- [ ] `pytest test/ -v` passes (47 passed, 2 skipped)
- [ ] No import errors
- [ ] Edge cases handled correctly

### Plot Modules

- [ ] `plot.config` imports without error
- [ ] `plot.utils` imports without error
- [ ] New plot functions in `plot_ipr_advanced.py` exist

### Output Validation

- [ ] Output TSV has required columns
- [ ] Scenarios are assigned (E, A, B, J, CDI, G, H)
- [ ] No Python tracebacks/errors

### Pre-Release Script

- [ ] `./scripts/pre_release_check.sh` passes all checks
- [ ] `./scripts/pre_release_check.sh --full` passes clean venv test

---

## Quick Test Commands Summary

```bash
# 1. Quick health check
./scripts/pre_release_check.sh

# 2. Run all tests
python -m pytest test/ -v

# 3. Test main pipeline
python pavprot.py --gff-comp test/data/gffcompare.tracking --output-dir /tmp/test

# 4. Check outputs
ls -la /tmp/test/
head /tmp/test/*_gffcomp.tsv

# 5. Full verification
./scripts/pre_release_check.sh --full
```

---

## Troubleshooting

### Import Errors

```bash
# Check if module is importable
python -c "import pavprot; print('OK')"

# Check dependencies
pip check
```

### Missing Test Data

```bash
# Verify test data directory
ls -la test/data/

# If missing, check git status
git status test/data/
```

### DIAMOND Not Found

```bash
# DIAMOND is optional - pipeline works without it
# To install: conda install -c bioconda diamond
```

### Test Failures

```bash
# Run with more verbose output
python -m pytest test/ -v --tb=long

# Check specific failing test
python -m pytest test/test_file.py::test_name -v --tb=long
```

---

*Last updated: 2026-01-26*
