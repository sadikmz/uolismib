# PAVprot Output Format Guide
## synonym_mapping_liftover_gffcomp.tsv

This document describes the complete output format of `pavprot.py`, including all optional columns.

## Output Filename

The output file is named based on:
- **Default prefix**: `synonym_mapping_liftover_gffcomp`
- **With class codes**: `synonym_mapping_liftover_gffcomp_em_j.tsv`
- **With DIAMOND**: `synonym_mapping_liftover_gffcomp_em_j_diamond_blastp.tsv`
- **Custom prefix**: Use `--output-prefix` to customize

## Column Descriptions

### Core Columns (Always Present)

| Column | Description | Example |
|--------|-------------|---------|
| `old_gene` | Reference gene ID | `gene-FOBCDRAFT_266382` |
| `old_transcript` | Reference transcript ID | `XM_031180388.3` |
| `new_gene` | Query gene ID | `FOZG_02279` |
| `new_transcript` | Query transcript ID | `FOZG_02279-t36_1` |
| `class_code` | Gffcompare class code | `em`, `j`, `n`, etc. |
| `exons` | Number of exons | `5` or `-` |
| `class_code_multi` | Multi-transcript class codes (semicolon-separated) | `em;j;n` |
| `class_type` | Classification type (0-5) | `0`, `1`, `2`, `3`, `4`, `5` |
| `emckmnj` | Flag: 1 if any code in [em,c,k,m,n,j], else 0 | `0` or `1` |
| `emckmnje` | Flag: 1 if any code in [em,c,k,m,n,j,e], else 0 | `0` or `1` |

### DIAMOND BLASTP Columns (when `--run-diamond` is used)

| Column | Description | Example |
|--------|-------------|---------|
| `identical_aa` | Number of identical amino acids | `458` |
| `mismatched_aa` | Number of mismatched amino acids | `12` |
| `indels_aa` | Number of insertions/deletions (gaps) | `3` |
| `aligned_aa` | Total aligned amino acid length | `473` |

### Liftoff Columns (when `--liftoff-gff` is provided)

| Column | Description | Example |
|--------|-------------|---------|
| `extra_copy_number` | Extra copy number from Liftoff GFF3 | `0`, `1`, `2`, etc. |

### InterProScan Columns (when `--interproscan-out` is provided)

| Column | Description | Example |
|--------|-------------|---------|
| `query_total_ipr_domain_length` | Total IPR domain length for query gene | `450` |
| `ref_total_ipr_domain_length` | Total IPR domain length for reference gene | `520` |

## Class Type Classification

| Type | Codes | Description |
|------|-------|-------------|
| `0` | em, c, k, m, n | High-quality matches |
| `1` | em, c, k, m, n, j | High-quality + partial matches |
| `2` | o, e | Generic exonic overlap |
| `3` | s, x | Single exon or opposite strand |
| `4` | i, y | Intronic |
| `5` | p, r, u | Other (polymerase, repeat, unknown) |

## Example Outputs

### Minimal Output (no optional features)

```tsv
old_gene	old_transcript	new_gene	new_transcript	class_code	exons	class_code_multi	class_type	emckmnj	emckmnje
gene-FOBCDRAFT_266382	XM_031180388.3	FOZG_02279	FOZG_02279-t36_1	j	4	j;m	1	1	1
gene-FOBCDRAFT_266382	XM_031180388.3	FOZG_02279	FOZG_02279-t36_2	m	3	j;m	1	1	1
gene-FOBCDRAFT_430	XM_031180643.3	FOZG_02018	FOZG_02018-t36_1	j	6	em;j;n	1	1	1
gene-FOBCDRAFT_430	XM_031180643.3	FOZG_02018	FOZG_02018-t36_2	n	5	em;j;n	1	1	1
gene-FOBCDRAFT_430	XM_031180643.3	FOZG_02018	FOZG_02018-t36_3	em	5	em;j;n	0	1	1
```

### Full Output (all features enabled)

```tsv
old_gene	old_transcript	new_gene	new_transcript	class_code	exons	class_code_multi	class_type	emckmnj	emckmnje	identical_aa	mismatched_aa	indels_aa	aligned_aa	extra_copy_number	query_total_ipr_domain_length	ref_total_ipr_domain_length
gene-FOBCDRAFT_266382	XM_031180388.3	FOZG_02279	FOZG_02279-t36_1	j	4	j;m	1	1	1	432	8	2	442	0	450	520
gene-FOBCDRAFT_266382	XM_031180388.3	FOZG_02279	FOZG_02279-t36_2	m	3	j;m	1	1	1	428	10	3	441	1	450	520
gene-FOBCDRAFT_430	XM_031180643.3	FOZG_02018	FOZG_02018-t36_1	j	6	em;j;n	1	1	1	958	15	5	978	0	680	720
gene-FOBCDRAFT_430	XM_031180643.3	FOZG_02018	FOZG_02018-t36_2	n	5	em;j;n	1	1	1	975	8	2	985	0	680	720
gene-FOBCDRAFT_430	XM_031180643.3	FOZG_02018	FOZG_02018-t36_3	em	5	em;j;n	0	1	1	982	3	1	986	0	680	720
```

## Usage Examples

### 1. Basic PAVprot (no optional features)
```bash
python gene_pav/pavprot.py \
  --gff-comp gffcompare.tracking \
  --gff reference.gff3 \
  --class-code em,j \
  --output-prefix my_analysis
```

Output: `pavprot_out/my_analysis_em_j.tsv`

### 2. With DIAMOND BLASTP
```bash
python gene_pav/pavprot.py \
  --gff-comp gffcompare.tracking \
  --gff reference.gff3 \
  --class-code em,j \
  --prot reference.faa \
  --prot query.faa \
  --run-diamond \
  --diamond-threads 40 \
  --output-prefix my_analysis
```

Output: `pavprot_out/my_analysis_em_j_diamond_blastp.tsv`
Adds: `identical_aa`, `mismatched_aa`, `indels_aa`, `aligned_aa`

### 3. With Liftoff extra copy numbers
```bash
python gene_pav/pavprot.py \
  --gff-comp gffcompare.tracking \
  --gff reference.gff3 \
  --liftoff-gff liftoff_output.gff3 \
  --class-code em,j \
  --output-prefix my_analysis
```

Output: `pavprot_out/my_analysis_em_j.tsv`
Adds: `extra_copy_number`

### 4. With InterProScan (Single GFF)
```bash
python gene_pav/pavprot.py \
  --gff-comp gffcompare.tracking \
  --gff reference.gff3 \
  --interproscan-out reference_interproscan.tsv \
  --class-code em,j \
  --output-prefix my_analysis
```

Output: `pavprot_out/my_analysis_em_j.tsv`
Adds: `query_total_ipr_domain_length`, `ref_total_ipr_domain_length`

### 5. With InterProScan (Dual GFF - Query + Reference)
```bash
python gene_pav/pavprot.py \
  --gff-comp gffcompare.tracking \
  --gff reference.gff3,query.gff3 \
  --interproscan-out reference_interproscan.tsv,query_interproscan.tsv \
  --class-code em,j \
  --output-prefix my_analysis
```

Output: `pavprot_out/my_analysis_em_j.tsv`
Adds: `query_total_ipr_domain_length` (from query InterProScan), `ref_total_ipr_domain_length` (from reference InterProScan)

### 6. Complete Analysis (All Features)
```bash
python gene_pav/pavprot.py \
  --gff-comp gffcompare.tracking \
  --gff reference.gff3,query.gff3 \
  --liftoff-gff liftoff_output.gff3 \
  --interproscan-out reference_interproscan.tsv,query_interproscan.tsv \
  --class-code em,j \
  --prot reference.faa \
  --prot query.faa \
  --run-diamond \
  --diamond-threads 40 \
  --output-prefix synonym_mapping_liftover_gffcomp
```

Output: `pavprot_out/synonym_mapping_liftover_gffcomp_em_j_diamond_blastp.tsv`

Includes ALL columns:
- Core: 10 columns
- DIAMOND: 4 columns
- Liftoff: 1 column
- InterProScan: 2 columns
**Total: 17 columns**

## Notes

1. **Gene-level aggregation for InterProScan**: IPR domain lengths are summed per gene, not per transcript. Multiple transcripts from the same gene will show the same total IPR domain length.

2. **Extra copy number**: Extracted from Liftoff GFF3 `extra_copy_number` attribute in mRNA features.

3. **DIAMOND output**: Uses ultra-sensitive mode with E-value cutoff of 1e-6.

4. **Class codes**: Standard gffcompare class codes (=, c, j, e, i, o, p, r, u, x, s, ., y)

5. **Output directory**: All outputs are written to `pavprot_out/` directory (created automatically).
