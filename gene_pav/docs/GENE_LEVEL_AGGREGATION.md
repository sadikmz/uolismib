# Gene-Level IPR Domain Aggregation

## Important: How ref_gene_total_iprdom_len is Calculated

The `ref_gene_total_iprdom_len` (and `query_gene_total_iprdom_len`) columns represent the **total sum of ALL IPR domain lengths across ALL transcripts of a gene**.

### What It IS

✓ **Sum of ALL IPR domains from ALL transcripts of the gene**

If a gene has multiple transcripts, each with their own IPR domains, we sum them ALL:

```
Gene: FOZG_00001
  Transcript 1: Domain A (100bp) + Domain B (50bp)  = 150 bp
  Transcript 2: Domain A (100bp) + Domain C (75bp)  = 175 bp

  → ref_gene_total_iprdom_len = 100 + 50 + 100 + 75 = 325 bp
```

**Note:** Even if the same domain (Domain A) appears in multiple transcripts, each occurrence is counted. This is biologically accurate because each transcript is a real molecular entity with its own domain structure.

### What It IS NOT

✗ **NOT** the IPR domain length of a single transcript
```
WRONG: Pick transcript 1 → 150 bp
```

✗ **NOT** the maximum IPR domain length among transcripts
```
WRONG: max(150, 175) → 175 bp
```

✗ **NOT** the length of a single domain
```
WRONG: Pick longest domain → 100 bp
```

## Implementation Details

### Code Location

**parse_interproscan.py** - `total_ipr_length()` method:

```python
def total_ipr_length(self) -> Dict[str, int]:
    # 1. Calculate domain length for each IPR domain entry
    df['domain_length'] = df['stop_location'] - df['start_location'] + 1

    # 2. Filter to only IPR domains (interpro_accession starts with 'IPR')
    ipr_df = df[df['interpro_accession'].str.startswith('IPR', na=False)]

    # 3. Map protein IDs to gene IDs using GFF
    ipr_df['gene_id'] = ipr_df['protein_accession'].map(self.transcript_to_gene_map)

    # 4. Group by gene_id and SUM all domain lengths
    total_lengths = ipr_df.groupby('gene_id')['domain_length'].sum()

    return total_lengths.to_dict()
```

### Step-by-Step Example

**Input: InterProScan TSV**
```
protein_accession  start  stop  interpro_accession
FOZG_00001-t1      10     110   IPR000001          # 101 bp
FOZG_00001-t1      200    250   IPR000002          #  51 bp
FOZG_00001-t2      10     110   IPR000001          # 101 bp (same domain, different transcript)
FOZG_00001-t2      300    375   IPR000003          #  76 bp
```

**Processing:**
1. Calculate domain lengths: 101, 51, 101, 76
2. Map to gene:
   - FOZG_00001-t1 → FOZG_00001
   - FOZG_00001-t2 → FOZG_00001
3. Group by gene_id (FOZG_00001) and sum: 101 + 51 + 101 + 76 = **329 bp**

**Output:**
```
gene_id      total_iprdom_len
FOZG_00001   329
```

## Real Data Example

From test data (foc67_v68.prot.test50.tsv):

### Gene: FOZG_03587
```
Number of transcripts: 1
  Transcript: FOZG_03587-t36_1
    11 IPR domains:
      - IPR037171: 215 bp
      - IPR004165: 228 bp
      - IPR004165: 198 bp
      - IPR012792: 236 bp
      - IPR014388: 483 bp
      - IPR037171: 311 bp
      - IPR004164: 9 bp
      - IPR004165: 484 bp
      - IPR004165: 199 bp
      - IPR004165: 231 bp
      - IPR012791: 208 bp

ref_gene_total_iprdom_len = 2802 bp
(Sum of ALL 11 domains)
```

### Gene: FOZG_06497
```
Number of transcripts: 1
  Transcript: FOZG_06497-t36_1
    3 IPR domains:
      - IPR029058: 342 bp
      - IPR029058: 295 bp
      - IPR000073: 277 bp

ref_gene_total_iprdom_len = 914 bp
(Sum of ALL 3 domains)
```

## Why This Approach?

1. **Biologically Accurate**: Each transcript is real and has its own domain architecture

2. **Gene-Level Analysis**: PAVprot focuses on gene-level comparisons, so aggregating all transcript data to the gene level is appropriate

3. **Captures Complexity**: Genes with multiple transcripts often have different domain combinations - this captures the full complexity

4. **Consistent with PAVprot**: Matches PAVprot's gene-centric approach

## PAVprot Output Format

```
ref_gene  ref_transcript  query_gene  query_transcript  ...  query_gene_total_iprdom_len  ref_gene_total_iprdom_len
FOZG_001  FOZG_001-t1     gene-XYZ    XP_123.1         ...  448                          329
FOZG_001  FOZG_001-t2     gene-XYZ    XP_123.1         ...  448                          329
```

**Note:** If a ref_gene has multiple transcripts (rows), all rows for that gene will have the **same** `ref_gene_total_iprdom_len` value because it's calculated at the gene level.

## Verification

Run the test script to verify behavior:

```bash
python test_gene_level_aggregation.py
```

This will show:
- How domains are aggregated across transcripts
- Detailed breakdown for sample genes
- Verification that the method works correctly

## Summary

✓ `ref_gene_total_iprdom_len` = **Sum of ALL IPR domain lengths from ALL transcripts of the ref_gene**

✓ `query_gene_total_iprdom_len` = **Sum of ALL IPR domain lengths from ALL transcripts of the query_gene**

This provides a comprehensive measure of IPR domain content at the gene level, which is appropriate for gene-level comparative analysis in PAVprot.
