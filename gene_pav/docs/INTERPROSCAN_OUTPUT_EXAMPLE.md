# InterProScan Integration in PAVprot - Output Example

## Summary

The InterProScan functionality has been **fully integrated** into `pavprot.py`. When you provide InterProScan TSV files, the output automatically includes total IPR domain lengths for query and reference genes.

## Output Columns

### Standard PAVprot Columns (always present):
- `old_gene` - Reference gene ID
- `old_transcript` - Reference transcript ID
- `new_gene` - Query gene ID
- `new_transcript` - Query transcript ID
- `class_code` - Gffcompare class code
- `exons` - Number of exons
- `class_code_multi` - Multi-transcript class codes
- `class_type` - Classification type (0-5)
- `emckmnj` - Flag for em,c,k,m,n,j codes
- `emckmnje` - Flag for em,c,k,m,n,j,e codes

### InterProScan Columns (when `--interproscan-out` is provided):
- **`query_total_ipr_domain_length`** - Total IPR domain length for query gene
- **`ref_total_ipr_domain_length`** - Total IPR domain length for reference gene

## Example Output (with InterProScan data):

```
old_gene	old_transcript	new_gene	new_transcript	class_code	exons	class_code_multi	class_type	emckmnj	emckmnje	query_total_ipr_domain_length	ref_total_ipr_domain_length
gene-FOBCDRAFT_266382	XM_031180388.3	FOZG_02279	FOZG_02279-t36_1	j	4	j;m	1	1	1	450	520
gene-FOBCDRAFT_266382	XM_031180388.3	FOZG_02279	FOZG_02279-t36_2	m	3	j;m	1	1	1	450	520
gene-FOBCDRAFT_430	XM_031180643.3	FOZG_02018	FOZG_02018-t36_1	j	6	em;j;n	1	1	1	680	720
gene-FOBCDRAFT_430	XM_031180643.3	FOZG_02018	FOZG_02018-t36_2	n	5	em;j;n	1	1	1	680	720
gene-FOBCDRAFT_430	XM_031180643.3	FOZG_02018	FOZG_02018-t36_3	em	5	em;j;n	0	1	1	680	720
```

## How It Works

1. **Parse InterProScan TSV**: `InterProParser` parses the InterProScan output (15-column format)
2. **Map transcripts to genes**: Uses GFF3 file to map protein/transcript IDs to gene IDs
3. **Calculate total IPR domain lengths**: Sums all IPR domain lengths per gene
4. **Enrich PAVprot data**: Adds `query_total_ipr_domain_length` and `ref_total_ipr_domain_length` columns

## Usage

### Single GFF + Single InterProScan (Reference only):
```bash
python gene_pav/pavprot.py \
  --gff-comp gffcompare.tracking \
  --gff reference.gff3 \
  --interproscan-out reference_interproscan.tsv \
  --class-code em,j \
  --output-prefix my_output
```

### Dual GFF + Dual InterProScan (Reference + Query):
```bash
python gene_pav/pavprot.py \
  --gff-comp gffcompare.tracking \
  --gff reference.gff3,query.gff3 \
  --interproscan-out reference_interproscan.tsv,query_interproscan.tsv \
  --class-code em,j \
  --output-prefix my_output
```

## Key Points

✓ **Automatic integration** - No manual pre-processing needed
✓ **Gene-level aggregation** - IPR domains are summed per gene (not per transcript)
✓ **Clean column names** - `query_total_ipr_domain_length` and `ref_total_ipr_domain_length`
✓ **Dual mode support** - Works with both single and dual GFF/InterProScan inputs
