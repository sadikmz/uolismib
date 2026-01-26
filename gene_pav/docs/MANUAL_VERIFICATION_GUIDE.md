# PAVprot Manual Verification Guide

> **Purpose:** Step-by-step manual testing of the entire pipeline
> **Time required:** ~30-45 minutes for full verification
> **Created:** 2026-01-26

---

## How to Use This Guide

1. Run each section in order
2. Check the "Expected" output after each command
3. Mark ✓ or ✗ in the checkbox
4. If something fails, check the Troubleshooting section

---

## PART 1: Environment Verification

### 1.1 Navigate to Project

```bash
cd /Users/sadik/projects/github_prj/uolismib/gene_pav
pwd
```

**Expected:** `/Users/sadik/projects/github_prj/uolismib/gene_pav`

- [ ] Correct directory

---

### 1.2 Check Python Version

```bash
python --version
```

**Expected:** Python 3.8 or higher

- [ ] Python version OK

---

### 1.3 Verify Dependencies

```bash
python -c "
import pandas as pd
import numpy as np
import matplotlib
import seaborn as sns
from Bio import SeqIO
print('pandas:', pd.__version__)
print('numpy:', np.__version__)
print('matplotlib:', matplotlib.__version__)
print('seaborn:', sns.__version__)
print('biopython: OK')
print('---')
print('All core dependencies installed ✓')
"
```

**Expected:** Version numbers printed, ending with "All core dependencies installed ✓"

- [ ] All dependencies OK

---

### 1.4 Verify Test Data Exists

```bash
echo "=== Test Data Files ===" && ls -la test/data/ && echo "" && echo "File count: $(ls test/data/ | wc -l)"
```

**Expected:** ~11 files including `.tracking`, `.gff3`, `.tsv`, `.faa` files

- [ ] Test data present

---

## PART 2: CLI Help Verification

### 2.1 Main Pipeline (pavprot.py)

```bash
python pavprot.py --help 2>&1 | head -20
```

**Expected:** Shows usage, description, and arguments starting with `--gff-comp`

- [ ] pavprot.py --help works

---

### 2.2 Scenario Classification (gsmc.py)

```bash
python gsmc.py --help 2>&1 | head -15
```

**Expected:** Shows "Gene Synteny Mapping Classifier" description

- [ ] gsmc.py --help works

---

### 2.3 Mapping Multiplicity

```bash
python mapping_multiplicity.py --help 2>&1 | head -15
```

**Expected:** Shows "Detect multiple mapping genes" description

- [ ] mapping_multiplicity.py --help works

---

### 2.4 BBH Analysis

```bash
python bidirectional_best_hits.py --help 2>&1 | head -15
```

**Expected:** Shows bidirectional best hits description

- [ ] bidirectional_best_hits.py --help works

---

### 2.5 Pairwise Alignment

```bash
python pairwise_align_prot.py --help 2>&1 | head -15
```

**Expected:** Shows pairwise alignment description

- [ ] pairwise_align_prot.py --help works

---

### 2.6 InterProScan Parser

```bash
python parse_interproscan.py --help 2>&1 | head -15
```

**Expected:** Shows InterProScan parsing description

- [ ] parse_interproscan.py --help works

---

### 2.7 Summary Statistics

```bash
python synonym_mapping_summary.py --help 2>&1 | head -15
```

**Expected:** Shows summary statistics description

- [ ] synonym_mapping_summary.py --help works

---

## PART 3: Unit Tests

### 3.1 Run All Tests

```bash
python -m pytest test/ -v --tb=short 2>&1 | tail -20
```

**Expected:** `47 passed, 2 skipped` (or similar)

- [ ] Tests pass

---

### 3.2 Check Test Summary

```bash
python -m pytest test/ -v 2>&1 | grep -E "(PASSED|FAILED|SKIPPED|ERROR)" | wc -l
```

**Expected:** 49 (47 passed + 2 skipped)

- [ ] Test count correct

---

## PART 4: Main Pipeline Testing

### 4.1 Create Test Output Directory

```bash
TEST_DIR="/tmp/pavprot_manual_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$TEST_DIR"
echo "Test output directory: $TEST_DIR"
```

**Expected:** Directory path printed

- [ ] Directory created

---

### 4.2 Run Minimal Pipeline (Tracking Only)

```bash
python pavprot.py \
  --gff-comp test/data/gffcompare.tracking \
  --output-dir "$TEST_DIR" \
  --output-prefix test1_minimal \
  2>&1

echo "---"
echo "Output files:"
ls -la "$TEST_DIR"/test1_minimal*
```

**Expected:**
- No errors
- At least 2 output files: `*_gffcomp.tsv` and `*_gene_level.tsv`

- [ ] Minimal pipeline runs
- [ ] Output files created

---

### 4.3 Verify Minimal Output Structure

```bash
echo "=== Columns in transcript-level output ==="
head -1 "$TEST_DIR"/test1_minimal_gffcomp.tsv | tr '\t' '\n' | nl

echo ""
echo "=== Record count ==="
wc -l "$TEST_DIR"/test1_minimal_gffcomp.tsv
```

**Expected:**
- Multiple columns including: ref_gene, ref_transcript, query_gene, query_transcript, class_code
- At least 2 lines (header + data)

- [ ] Columns present
- [ ] Data rows exist

---

### 4.4 Run Pipeline with GFF

```bash
python pavprot.py \
  --gff-comp test/data/gffcompare.tracking \
  --gff test/data/gff_feature_table.gff3 \
  --output-dir "$TEST_DIR" \
  --output-prefix test2_with_gff \
  2>&1

echo "---"
ls -la "$TEST_DIR"/test2_with_gff*
```

**Expected:** Output files created without errors

- [ ] Pipeline with GFF runs

---

### 4.5 Run Pipeline with InterProScan

```bash
python pavprot.py \
  --gff-comp test/data/gffcompare.tracking \
  --gff test/data/gff_feature_table.gff3 \
  --interproscan-out test/data/test_interproscan.tsv \
  --output-dir "$TEST_DIR" \
  --output-prefix test3_with_ipr \
  2>&1

echo "---"
ls -la "$TEST_DIR"/test3_with_ipr*
```

**Expected:** Output files created, may include IPR columns

- [ ] Pipeline with InterProScan runs

---

### 4.6 Check Gene-Level Output and Scenarios

```bash
echo "=== Gene-level output columns ==="
head -1 "$TEST_DIR"/test1_minimal_gene_level.tsv | tr '\t' '\n' | nl | tail -10

echo ""
echo "=== Scenario distribution ==="
if head -1 "$TEST_DIR"/test1_minimal_gene_level.tsv | grep -q "scenario"; then
  awk -F'\t' 'NR==1 {for(i=1;i<=NF;i++) if($i=="scenario") col=i} NR>1 {print $col}' "$TEST_DIR"/test1_minimal_gene_level.tsv | sort | uniq -c
else
  echo "No scenario column found (may be expected for minimal test data)"
fi
```

**Expected:** Shows scenario column (E, A, B, J, CDI, etc.) or message about no scenario column

- [ ] Gene-level output verified

---

## PART 5: Individual Module Testing

### 5.1 Test mapping_multiplicity.py

```bash
python mapping_multiplicity.py \
  "$TEST_DIR"/test1_minimal_gffcomp.tsv \
  --output-prefix "$TEST_DIR"/mapping_test \
  2>&1

echo "---"
echo "Output files:"
ls -la "$TEST_DIR"/mapping_test* 2>/dev/null || echo "No output files (may be expected if no multiple mappings)"
```

**Expected:** Either output files or "No multiple mappings found" message

- [ ] mapping_multiplicity runs

---

### 5.2 Test synonym_mapping_summary.py

```bash
python synonym_mapping_summary.py "$TEST_DIR"/test1_minimal_gffcomp.tsv 2>&1 | head -30
```

**Expected:** Summary statistics with counts for records, genes, transcripts

- [ ] Summary statistics generated

---

### 5.3 Test Pairwise Alignment Function

```bash
python -c "
from pairwise_align_prot import local_alignment_similarity

# Test sequences (hemoglobin-like)
seq1 = 'MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSH'
seq2 = 'MVLSGEDKSNIKAAWGKIGGHGAEYGAEALERMFASFPTTKTYFPHFDVSH'

result = local_alignment_similarity(seq1, seq2, 'human', 'chimp')

print('Pairwise Alignment Test')
print('=' * 40)
print(f'Sequence 1 length: {len(seq1)} aa')
print(f'Sequence 2 length: {len(seq2)} aa')
print(f'Identity: {result[\"identity\"]:.1f}%')
print(f'Coverage (seq1): {result[\"coverage_seq1\"]:.1f}%')
print(f'Coverage (seq2): {result[\"coverage_seq2\"]:.1f}%')
print(f'Aligned length: {result[\"aligned_length\"]} aa')
print('=' * 40)
print('✓ Pairwise alignment works')
"
```

**Expected:** Identity ~80-90%, coverage near 100%

- [ ] Pairwise alignment works

---

### 5.4 Test InterProScan Parser

```bash
python -c "
from parse_interproscan import InterProParser

parser = InterProParser()
df = parser.parse_tsv('test/data/test_interproscan.tsv')

print('InterProScan Parser Test')
print('=' * 40)
print(f'Records parsed: {len(df)}')
print(f'Columns: {list(df.columns)[:5]}...')
print(f'Unique proteins: {df.iloc[:, 0].nunique() if len(df) > 0 else 0}')
print('=' * 40)
print('✓ InterProScan parser works')
"
```

**Expected:** Shows record count and columns

- [ ] InterProScan parser works

---

### 5.5 Test BBH Class

```bash
python -c "
from bidirectional_best_hits import BidirectionalBestHits, BlastHit

print('BBH Module Test')
print('=' * 40)
print(f'BidirectionalBestHits class: OK')
print(f'BlastHit dataclass fields: {list(BlastHit.__dataclass_fields__.keys())}')
print('=' * 40)
print('✓ BBH module loads correctly')
"
```

**Expected:** Shows class loaded and BlastHit fields

- [ ] BBH module works

---

### 5.6 Test GSMC Functions

```bash
python -c "
from gsmc import (
    get_cdi_genes,
    detect_one_to_one_orthologs,
    detect_one_to_many,
    detect_many_to_one,
    detect_complex_one_to_many
)

print('GSMC Module Test')
print('=' * 40)
print('Functions loaded:')
print('  - get_cdi_genes')
print('  - detect_one_to_one_orthologs (Scenario E)')
print('  - detect_one_to_many (Scenario A)')
print('  - detect_many_to_one (Scenario B)')
print('  - detect_complex_one_to_many (Scenario J)')
print('=' * 40)
print('✓ GSMC module loads correctly')
"
```

**Expected:** All functions listed as loaded

- [ ] GSMC module works

---

## PART 6: Plot Module Verification

### 6.1 Test Plot Config

```bash
python -c "
from plot.config import setup_plotting, CLASS_TYPE_PALETTE, SCENARIO_PALETTE, MARKER_STYLES

print('Plot Config Test')
print('=' * 40)
print(f'CLASS_TYPE_PALETTE colors: {len(CLASS_TYPE_PALETTE)}')
for k, v in list(CLASS_TYPE_PALETTE.items())[:3]:
    print(f'  {k}: {v}')
print(f'SCENARIO_PALETTE colors: {len(SCENARIO_PALETTE)}')
print(f'MARKER_STYLES: {len(MARKER_STYLES)}')
print('=' * 40)
print('✓ Plot config loads correctly')
"
```

**Expected:** Shows color palettes

- [ ] Plot config works

---

### 6.2 Test Plot Utils

```bash
python -c "
from plot.utils import load_data, load_pavprot_data, filter_by_class_type, add_ipr_status_column

print('Plot Utils Test')
print('=' * 40)
print('Functions available:')
print('  - load_data')
print('  - load_pavprot_data')
print('  - filter_by_class_type')
print('  - add_ipr_status_column')
print('=' * 40)
print('✓ Plot utils loads correctly')
"
```

**Expected:** Functions listed

- [ ] Plot utils works

---

### 6.3 Test New Plot Functions (plot_ipr_advanced.py)

```bash
python -c "
from plot.plot_ipr_advanced import (
    load_data,
    plot_log_scale,
    plot_regression_analysis,
    plot_faceted_by_emckmnj,
    plot_bland_altman,
    plot_delta_distribution,
    plot_violin_comparison,
    plot_cdf_comparison,
    plot_contour_density
)

print('Plot IPR Advanced Test')
print('=' * 40)
print('Functions available:')
funcs = ['load_data', 'plot_log_scale', 'plot_regression_analysis',
         'plot_faceted_by_emckmnj', 'plot_bland_altman', 'plot_delta_distribution',
         'plot_violin_comparison', 'plot_cdf_comparison', 'plot_contour_density']
for f in funcs:
    print(f'  ✓ {f}')
print('=' * 40)
print('✓ All 9 plot functions available')
"
```

**Expected:** All 9 functions listed with checkmarks

- [ ] Advanced plot functions work

---

## PART 7: Tools Runner Verification

### 7.1 Test Tools Runner

```bash
python -c "
from tools_runner import ToolsRunner

print('Tools Runner Test')
print('=' * 40)

# Create instance
runner = ToolsRunner(output_dir='/tmp/test', dry_run=True)
print(f'Output dir: {runner.output_dir}')
print(f'Dry run mode: {runner.dry_run}')

# Check methods exist
methods = ['run_psauron', 'run_alphafold_plddt', 'run_diamond',
           'run_interproscan', 'run_gffcompare', 'run_liftoff',
           'run_pairwise_alignment', 'run_busco', 'detect_annotation_source']
print(f'Methods available: {len(methods)}')
for m in methods:
    has_method = hasattr(runner, m)
    status = '✓' if has_method else '✗'
    print(f'  {status} {m}')

print('=' * 40)
print('✓ Tools runner loads correctly')
"
```

**Expected:** All 9 methods listed with checkmarks

- [ ] Tools runner works

---

## PART 8: Pre-Release Script Verification

### 8.1 Test Pre-Release Script Exists

```bash
ls -la scripts/pre_release_check.sh
file scripts/pre_release_check.sh
```

**Expected:** File exists, is executable shell script

- [ ] Script exists

---

### 8.2 Test Pre-Release Script Help

```bash
./scripts/pre_release_check.sh --help
```

**Expected:** Shows usage with --full, --lint, --test, --cli options

- [ ] Script help works

---

### 8.3 Run Quick Pre-Release Check

```bash
./scripts/pre_release_check.sh 2>&1 | tail -20
```

**Expected:** "All checks passed!" at the end

- [ ] Quick pre-release check passes

---

## PART 9: Output Validation

### 9.1 Validate Output TSV Structure

```bash
python -c "
import pandas as pd
import sys

print('Output Validation Test')
print('=' * 40)

# Load output
df = pd.read_csv('$TEST_DIR/test1_minimal_gffcomp.tsv', sep='\t')

# Required columns
required = ['ref_gene', 'ref_transcript', 'query_gene', 'query_transcript', 'class_code']
missing = [c for c in required if c not in df.columns]

if missing:
    print(f'✗ Missing required columns: {missing}')
    sys.exit(1)
else:
    print('✓ All required columns present')

print(f'Total columns: {len(df.columns)}')
print(f'Total records: {len(df)}')
print(f'Unique ref genes: {df[\"ref_gene\"].nunique()}')
print(f'Unique query genes: {df[\"query_gene\"].nunique()}')

# Check for NaN in key columns
nan_counts = df[required].isna().sum()
if nan_counts.any():
    print(f'Warning: NaN values in key columns: {nan_counts[nan_counts > 0].to_dict()}')
else:
    print('✓ No NaN values in key columns')

print('=' * 40)
print('✓ Output validation passed')
"
```

**Expected:** All checks pass

- [ ] Output validation passes

---

## PART 10: Cleanup

### 10.1 View Test Summary

```bash
echo "=== Test Output Summary ==="
echo "Directory: $TEST_DIR"
echo ""
echo "Files created:"
ls -la "$TEST_DIR"/ | awk '{print "  " $9 " (" $5 " bytes)"}' | grep -v "^  ("
echo ""
echo "Total size:"
du -sh "$TEST_DIR"
```

- [ ] Summary reviewed

---

### 10.2 Optional: Clean Up Test Files

```bash
# Uncomment to delete test files:
# rm -rf "$TEST_DIR"
# echo "Test files cleaned up"

echo "To clean up later, run:"
echo "  rm -rf $TEST_DIR"
```

- [ ] Cleanup noted

---

## Verification Summary

### Checklist

Copy this checklist and mark completed items:

```
PART 1: Environment
[ ] 1.1 Correct directory
[ ] 1.2 Python version OK
[ ] 1.3 Dependencies OK
[ ] 1.4 Test data present

PART 2: CLI Help
[ ] 2.1 pavprot.py
[ ] 2.2 gsmc.py
[ ] 2.3 mapping_multiplicity.py
[ ] 2.4 bidirectional_best_hits.py
[ ] 2.5 pairwise_align_prot.py
[ ] 2.6 parse_interproscan.py
[ ] 2.7 synonym_mapping_summary.py

PART 3: Unit Tests
[ ] 3.1 All tests pass
[ ] 3.2 Test count correct

PART 4: Main Pipeline
[ ] 4.1 Directory created
[ ] 4.2 Minimal pipeline runs
[ ] 4.3 Output structure OK
[ ] 4.4 Pipeline with GFF runs
[ ] 4.5 Pipeline with InterProScan runs
[ ] 4.6 Gene-level output OK

PART 5: Individual Modules
[ ] 5.1 mapping_multiplicity
[ ] 5.2 synonym_mapping_summary
[ ] 5.3 pairwise_align_prot
[ ] 5.4 parse_interproscan
[ ] 5.5 bidirectional_best_hits
[ ] 5.6 gsmc

PART 6: Plot Modules
[ ] 6.1 plot.config
[ ] 6.2 plot.utils
[ ] 6.3 plot_ipr_advanced (9 functions)

PART 7: Tools Runner
[ ] 7.1 All 9 methods available

PART 8: Pre-Release Script
[ ] 8.1 Script exists
[ ] 8.2 Help works
[ ] 8.3 Quick check passes

PART 9: Output Validation
[ ] 9.1 Structure valid

TOTAL: ___/31 checks passed
```

---

## Troubleshooting

### Import Error

```bash
# Check module is importable
python -c "import <module_name>"

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### Test Data Missing

```bash
# Check if files exist
ls -la test/data/

# Check git status
git status test/data/
```

### Permission Denied on Script

```bash
chmod +x scripts/pre_release_check.sh
```

### Module Not Found

```bash
# Reinstall dependencies
pip install -r requirements.txt
```

---

*Guide created: 2026-01-26*
