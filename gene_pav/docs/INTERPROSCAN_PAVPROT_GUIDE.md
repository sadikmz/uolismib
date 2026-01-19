# PAVprot InterProScan Integration Guide

## Overview

PAVprot now integrates with InterProScan output to add domain annotation information. The integration uses GFF files to properly map protein IDs to gene IDs.

## Key Concepts

### GFF File Logic

- **Single GFF**: `--ref-gff reference.gff` → No InterProScan data needed
- **Comma-separated GFFs**: `--ref-gff reference.gff,query.gff` → Requires `--interproscan-out` with 2 TSV files

### File Mapping

When using comma-separated inputs:
```
--ref-gff ref.gff,query.gff
--interproscan-out ref_interpro.tsv,query_interpro.tsv

Mapping:
  ref.gff         → ref_interpro.tsv      (reference genome)
  query.gff       → query_interpro.tsv    (query genome)
```

## Usage Examples

### Example 1: Without InterProScan (single GFF)

```bash
python gene_pav/pavprot.py \
  --gff-comp gffcompare.tracking \
  --ref-gff reference.gff3 \
  --liftoff-gff liftoff_output.gff3 \
  --class-code em,j \
  --output-prefix my_analysis
```

**Result**: Standard PAVprot output without domain annotations

### Example 2: With InterProScan (two GFFs)

```bash
python gene_pav/pavprot.py \
  --gff-comp gffcompare.tracking \
  --ref-gff reference.gff3,query.gff3 \
  --interproscan-out ref_interproscan.tsv,query_interproscan.tsv \
  --liftoff-gff liftoff_output.gff3 \
  --class-code em,j \
  --output-prefix my_analysis
```

**Result**: PAVprot output with 6 additional domain annotation columns

### Example 3: Full Pipeline with DIAMOND and InterProScan

```bash
python gene_pav/pavprot.py \
  --gff-comp gffcompare.tracking \
  --ref-gff GCF_013085055.1.gff3,foc67_v68.gff3 \
  --interproscan-out GCF_013085055.1_interpro.tsv,foc67_v68_interpro.tsv \
  --liftoff-gff liftoff_foc67.gff3 \
  --class-code em,j \
  --ref-faa GCF_013085055.1.prot.faa \
  --qry-faa foc67_v68.prot.faa \
  --run-diamond \
  --diamond-threads 40 \
  --output-prefix foc67_vs_GCF013085055
```

## Output Columns

### Standard Output (no InterProScan)
```
ref_gene
ref_transcript
query_gene
query_transcript
class_code
exons
class_code_multi
class_type
emckmnj
emckmnje
[diamond columns if --run-diamond]
[extra_copy_number if --liftoff-gff]
```

### With InterProScan
```
ref_gene
ref_transcript
query_gene
query_transcript
class_code
exons
class_code_multi
class_type
emckmnj
emckmnje
[diamond columns if --run-diamond]
[extra_copy_number if --liftoff-gff]
query_analysis                    ← NEW
query_signature_accession         ← NEW
query_total_IPR_domain_length     ← NEW
ref_analysis                      ← NEW
ref_signature_accession           ← NEW
ref_total_IPR_domain_length       ← NEW
```

## InterProScan Column Descriptions

| Column | Description | Example |
|--------|-------------|---------|
| `query_analysis` | Database/analysis used for longest IPR domain | PANTHER, Pfam, Gene3D |
| `query_signature_accession` | Signature/domain accession ID | PTHR13266, PF06985 |
| `query_total_IPR_domain_length` | Sum of all IPR domain lengths for the protein | 280 |
| `ref_analysis` | Same as query_analysis but for reference | SUPERFAMILY |
| `ref_signature_accession` | Same as query_signature_accession but for reference | SSF51735 |
| `ref_total_IPR_domain_length` | Same as query_total_IPR_domain_length but for reference | 341 |

## Preparing InterProScan Input

### Step 1: Run InterProScan on both genomes

```bash
# Reference genome
interproscan.sh -i reference.prot.faa -b reference_interpro -f TSV --iprlookup --goterms

# Query genome
interproscan.sh -i query.prot.faa -b query_interpro -f TSV --iprlookup --goterms
```

### Step 2: Use the raw TSV output directly

The raw InterProScan output (`*.tsv` files) can be used directly with PAVprot:

```bash
python gene_pav/pavprot.py \
  --gff-comp gffcompare.tracking \
  --ref-gff reference.gff3,query.gff3 \
  --interproscan-out reference_interpro.tsv,query_interpro.tsv \
  --output-prefix analysis
```

### Alternative: Pre-process with parse_interproscan (optional)

If you want to analyze InterProScan results separately first:

```bash
# Process reference InterProScan
python parse_interproscan/parse_interproscan.py \
  --parse reference_interpro.tsv \
  --gff reference.gff3

# Process query InterProScan
python parse_interproscan/parse_interproscan.py \
  --parse query_interpro.tsv \
  --gff query.gff3
```

## How GFF Mapping Works

The integration uses `parse_interproscan.py`'s GFF mapping functionality:

1. **Reads GFF file** to extract gene-to-transcript relationships
2. **Parses InterProScan TSV** to get protein domain annotations
3. **Maps protein IDs** to gene IDs using GFF relationships
4. **Extracts longest IPR domain** for each protein
5. **Calculates total IPR domain length** (sum of all IPR domains)

### NCBI GFF Format Support
```
mRNA: ID=rna-XM_059609290.1;Parent=gene-FOBCDRAFT_209856;Name=XM_059609290.1
CDS:  ID=cds-XP_059464304.1;Parent=rna-XM_059608890.1;Name=XP_059464304.1

Maps: XP_059464304.1 (protein) → gene-FOBCDRAFT_209856
```

### VEuPathDB GFF Format Support
```
mRNA: ID=FOZG_00001-t36_1;Parent=FOZG_00001

Maps: FOZG_00001-t36_1 (transcript) → FOZG_00001 (gene)
```

## Validation and Error Handling

### Validation Checks

1. **GFF count validation**: If `--ref-gff` has 2 GFFs, `--interproscan-out` must also have exactly 2 files
2. **File existence**: All InterProScan files must exist
3. **Warning**: If `--interproscan-out` is provided but `--ref-gff` has only 1 GFF, a warning is issued and InterProScan data is ignored

### Example Error Messages

```bash
# Error: Missing interproscan-out
$ python gene_pav/pavprot.py --gff-comp track.txt --ref-gff ref.gff,qry.gff
error: --interproscan-out is required when --ref-gff has 2 comma-separated GFFs

# Error: Wrong number of files
$ python gene_pav/pavprot.py --gff-comp track.txt --ref-gff ref.gff,qry.gff --interproscan-out single.tsv
error: --interproscan-out must have exactly 2 comma-separated files when --ref-gff has 2 GFFs. Got 1 files.

# Error: File not found
$ python gene_pav/pavprot.py --gff-comp track.txt --ref-gff ref.gff,qry.gff --interproscan-out ref.tsv,missing.tsv
error: InterProScan file not found: missing.tsv
```

## Example Workflow

### Complete Analysis Pipeline

```bash
#!/bin/bash

# 1. Run gffcompare
gffcompare -r reference.gff3 -o gffcompare query.gff3

# 2. Run InterProScan on both genomes (if not done already)
interproscan.sh -i reference.prot.faa -b ref_interpro -f TSV --iprlookup --goterms -cpu 40
interproscan.sh -i query.prot.faa -b qry_interpro -f TSV --iprlookup --goterms -cpu 40

# 3. Run PAVprot with full integration
python gene_pav/pavprot.py \
  --gff-comp gffcompare.tracking \
  --ref-gff reference.gff3,query.gff3 \
  --interproscan-out ref_interpro.tsv,qry_interpro.tsv \
  --liftoff-gff liftoff_output.gff3 \
  --class-code em,j \
  --ref-faa reference.prot.faa \
  --qry-faa query.prot.faa \
  --run-diamond \
  --diamond-threads 40 \
  --output-prefix my_comparison

# 4. Output will be in:
# pavprot_out/my_comparison_em_j_diamond_blastp.tsv
```

## Standalone parse_interproscan Usage

The `parse_interproscan.py` script remains fully functional as a standalone tool:

```bash
# Analyze InterProScan output with GFF mapping
python parse_interproscan/parse_interproscan.py \
  --parse interproscan_output.tsv \
  --gff genome.gff3

# Outputs:
# - interproscan_output_longest_ipr_domains.tsv
# - interproscan_output_domain_distribution.tsv

# Run InterProScan and parse results
python parse_interproscan/parse_interproscan.py \
  --run \
  --input proteins.faa \
  --gff genome.gff3 \
  --cpu 40
```

## Notes

- InterProScan integration is **optional** - PAVprot works perfectly fine without it
- Only IPR domains (accessions starting with "IPR") are considered
- If a protein is not found in InterProScan data, values default to `-` or `0`
- Domain length = `stop_location - start_location + 1`
- Total IPR domain length = sum of all IPR domains for that protein
- The GFF files enable proper gene ID mapping for both NCBI and non-NCBI formats
