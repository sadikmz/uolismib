# PAVprot Quick Test Reference

> Copy-paste commands for manual testing

---

## 1. Setup

```bash
cd /Users/sadik/projects/github_prj/uolismib/gene_pav
```

---

## 2. Quick Health Check

```bash
./scripts/pre_release_check.sh
```

---

## 3. Run All Unit Tests

```bash
python -m pytest test/ -v
```

---

## 4. Test Main Pipeline

```bash
# Minimal test
python pavprot.py \
  --gff-comp test/data/gffcompare.tracking \
  --output-dir /tmp/pavprot_test \
  --output-prefix test1

# With InterProScan
python pavprot.py \
  --gff-comp test/data/gffcompare.tracking \
  --gff test/data/gff_feature_table.gff3 \
  --interproscan-out test/data/test_interproscan.tsv \
  --output-dir /tmp/pavprot_test \
  --output-prefix test2
```

---

## 5. Check Outputs

```bash
# List outputs
ls -la /tmp/pavprot_test/

# View columns
head -1 /tmp/pavprot_test/test1_gffcomp.tsv | tr '\t' '\n' | nl

# Count scenarios
awk -F'\t' 'NR>1 {print $NF}' /tmp/pavprot_test/test1_gene_level.tsv | sort | uniq -c

# View first few records
head -5 /tmp/pavprot_test/test1_gffcomp.tsv | column -t -s$'\t'
```

---

## 6. Test Individual Modules

```bash
# Mapping multiplicity
python mapping_multiplicity.py /tmp/pavprot_test/test1_gffcomp.tsv -o /tmp/mapping_test

# Summary statistics
python synonym_mapping_summary.py /tmp/pavprot_test/test1_gffcomp.tsv

# Pairwise alignment (test function)
python -c "
from pairwise_align_prot import local_alignment_similarity
result = local_alignment_similarity('MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSH',
                                    'MVLSGEDKSNIKAAWGKIGGHGAEYGAEALERMFASFPTTKTYFPHFDVSH',
                                    'seq1', 'seq2')
print(f'Identity: {result[\"identity\"]:.1f}%')
"
```

---

## 7. Test CLI Help

```bash
for module in pavprot gsmc mapping_multiplicity bidirectional_best_hits pairwise_align_prot parse_interproscan synonym_mapping_summary; do
  echo "=== $module ===" && python ${module}.py --help | head -5
done
```

---

## 8. Full Verification

```bash
./scripts/pre_release_check.sh --full
```

---

## Expected Results

| Check | Expected |
|-------|----------|
| Unit tests | 47 passed, 2 skipped |
| CLI help | All 7 modules pass |
| Linting | No critical errors |
| Clean venv | Tests pass |

---

## Cleanup

```bash
rm -rf /tmp/pavprot_test /tmp/mapping_test
```
