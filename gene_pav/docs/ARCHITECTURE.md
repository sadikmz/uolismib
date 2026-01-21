# PAVprot Module Architecture

## Directory Structure

```
gene_pav/
├── pavprot.py                          # Main orchestrator
├── parse_interproscan.py               # IPR domain parsing (imported by pavprot)
├── bidirectional_best_hits.py          # BBH analysis (imported by pavprot)
├── mapping_multiplicity.py         # 1:N mapping detection (imported by pavprot)
├── pairwise_align_prot.py              # Pairwise protein alignment
│
├── analysis/                           # Downstream analysis scripts
│   ├── gsmc.py    # Scenario classification (E,A,B,J,CDI,F,G,H)
│   ├── inconsistent_genes_transcript_IPR_PAV.py  # IPR consistency analysis
│   └── synonym_mapping_summary.py      # Statistics summary
│
├── utils/                              # Standalone utilities
│   ├── parse_liftover_extra_copy_number.py  # Liftoff pre-processing
│   └── synonym_mapping_parse.py        # Query gene counting utility
│
├── dev/                                # Development & legacy scripts
│   ├── check_plot_logic.py             # Plot debugging utility
│   ├── parse_interproscan_github_version.py  # Legacy IPR parser version
│   └── standalone_bed_coverage_test.py # BED coverage testing
│
├── plot/                               # Visualization scripts
│   ├── plot_ipr_comparison.py          # IPR scatter plots
│   ├── plot_ipr_gene_level.py          # Gene-level IPR analysis
│   ├── plot_ipr_advanced.py            # Advanced visualizations
│   ├── plot_ipr_shapes.py              # Domain shape plots
│   ├── plot_ipr_proportional_bias.py   # Bias analysis
│   └── plot_domain_comparison.py       # Domain comparison
│
└── test/                               # Test files
    ├── test_pavprot.py                 # PAVprot unit tests
    ├── test_bed_coverage.py            # BED coverage tests
    ├── test_bed_files.py               # BED file tests
    ├── test_inconsistent_genes.py      # Inconsistent genes tests
    └── test_all_outputs.py             # Output validation tests
```

---

## Complete Script Connectivity Diagram

```
┌────────────────────────────────────────────────────────────────────────────────────────
│                                    INPUT FILES                                          
├────────────────────────────────────────────────────────────────────────────────────────
│  • GffCompare tracking file (.tracking)                                                 
│  • Reference GFF3 (.gff3)                                                               
│  • Query GFF3 (.gff3)                                                                   
│  • Reference protein FASTA (.faa)                                                       
│  • Query protein FASTA (.faa)                                                           
│  • InterProScan TSV (optional)                                                          
│  • Liftoff GFF3 (optional, for extra_copy_number)                                       
└───────────────────────────────────────┬────────────────────────────────────────────────
                                        │
                                        ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃                              pavprot.py (MAIN ORCHESTRATOR)                             
┃   IMPORTS:                                                                              
┃   ├── from parse_interproscan import InterProParser, run_interproscan                   
┃   ├── from detect_one2many_mappings import detect_multiple_mappings                     
┃   └── from bidirectional_best_hits import BidirectionalBestHits,enrich_pavprot_with_bbh┃
┃                                                                                         
┃   FUNCTIONS:                                                                            
┃   1. parse_tracking()      → Extract ref/query gene pairs + class codes                 
┃   2. compute_all_metrics() → ref_multi_query, qry_multi_ref, exact_match                
┃   3. DiamondRunner         → Run DIAMOND BLASTP (optional)                              
┃   4. BBH analysis          → Bidirectional best hits (optional)                         
┃   5. InterProScan          → Domain annotation enrichment (optional)                    
┃   6. write_results()       → Main output TSV                                            
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          ┌────────────────────┼────────────────────┬────────────────────┐
          ▼                    ▼                    ▼                    ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ parse_           │ │ bidirectional_   │ │ detect_one2many_ │ │ utils/           │
│ interproscan.py  │ │ best_hits.py     │ │ mappings.py      │ │ parse_liftover_  │
│                  │ │                  │ │                  │ │ extra_copy_      │
│ CALLED BY:       │ │ CALLED BY:       │ │ CALLED BY:       │ │ number.py        │
│ pavprot.py       │ │ pavprot.py       │ │ pavprot.py       │ │                  │
│ (import)         │ │ (import)         │ │ (import)         │ │ STANDALONE       │
│                  │ │                  │ │                  │ │ (pre-processing) │
│ WHEN:            │ │ WHEN:            │ │ WHEN:            │ │                  │
│ --interproscan   │ │ --run-bbh        │ │ Always (at end)  │ │ WHEN:            │
│ --run-interpro   │ │                  │ │                  │ │ Before pavprot   │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
                                        │
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────────
│                              PRIMARY OUTPUT (TSV)                                       
│                                                                                         
│   synonym_mapping_liftover_gffcomp.tsv                                                  
│   ├── ref_gene, query_gene, ref_transcript, query_transcript                            
│   ├── class_code, class_type_transcript, class_type_gene                                
│   ├── ref_multi_query, qry_multi_ref, exact_match                                       
│   ├── pident, qcovhsp, scovhsp (if --run-diamond)                                       
│   ├── is_bbh, bbh_avg_pident, bbh_avg_coverage (if --run-bbh)                           
│   └── query_total_ipr_domain_length, ref_total_ipr_domain_length (if --interproscan)   │
└───────────────────────────────────────┬────────────────────────────────────────────────
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
        ▼                               ▼                               ▼
┌───────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│ analysis/         │     │ analysis/               │     │ analysis/               │
│ detect_advanced_  │     │ synonym_mapping_        │     │ inconsistent_genes_     │
│ scenarios.py      │     │ summary.py              │     │ transcript_IPR_PAV.py   │
│                   │     │                         │     │                         │
│ DOWNSTREAM        │     │ STANDALONE              │     │ DOWNSTREAM              │
│ ANALYSIS          │     │ UTILITY                 │     │ ANALYSIS                │
│                   │     │                         │     │                         │
│ INPUT:            │     │ INPUT:                  │     │ INPUT:                  │
│ pavprot TSV       │     │ pavprot TSV             │     │ pavprot TSV             │
│                   │     │                         │     │ (with IPR columns)      │
│ OUTPUT:           │     │ OUTPUT:                 │     │                         │
│ scenario_*.tsv    │     │ stdout statistics       │     │ OUTPUT:                 │
│ (E,A,B,J,CDI,F,   │     │                         │     │ *_inconsistent_genes.tsv│
│  G,H)             │     │                         │     │ *_analysis.png          │
└───────────────────┘     └─────────────────────────┘     └─────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────────────────────────────────────
│                            SCENARIO OUTPUT FILES                                        
│   scenario_E_1to1_orthologs.tsv       → 1:1 exclusive ortholog pairs                    
│   scenario_A_1toN_mappings.tsv        → One ref → multiple queries                      
│   scenario_B_Nto1_mappings.tsv        → Multiple refs → one query                       
│   scenario_J_complex_1toN_mappings.tsv→ One ref → 3+ queries                            
│   scenario_CDI_cross_mappings.tsv     → Cross-mapping classification                    
│   scenario_F_positional_swaps.tsv     → Adjacent gene order inversions                  
│   scenario_G_unmapped_ref_genes.tsv   → Ref genes without query matches                 
│   scenario_H_unmapped_query_genes.tsv → Query genes without ref matches                 
└────────────────────────────────────────────────────────────────────────────────────────
                                        │
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────────
│                              VISUALIZATION SCRIPTS                                      
│                                 (plot/ directory)                                       
├────────────────────────────────────────────────────────────────────────────────────────
│   plot_ipr_comparison.py      → Query vs Ref IPR domain length scatter plots            
│   plot_ipr_gene_level.py      → Gene-level IPR domain analysis                          
│   plot_ipr_shapes.py          → Domain shape/distribution plots                         
│   plot_ipr_advanced.py        → Advanced IPR visualizations                             
│   plot_ipr_proportional_bias.py → Proportional bias analysis                            
│   plot_domain_comparison.py   → Domain comparison between ref/query                         ALL TAKE: pavprot TSV output (with IPR columns) as INPUT                              
│   ALL PRODUCE: PNG visualization files                                                  
└────────────────────────────────────────────────────────────────────────────────────────
```

---

## Detailed Script Relationships

### CORE MODULES (Main Directory - Imported by pavprot.py)

| Script | Import Statement | Purpose | When Activated |
|--------|-----------------|---------|----------------|
| `parse_interproscan.py` | `from parse_interproscan import InterProParser, run_interproscan` | Parse InterProScan TSV, calculate IPR domain lengths with overlap merging | `--interproscan-out` or `--run-interproscan` |
| `bidirectional_best_hits.py` | `from bidirectional_best_hits import BidirectionalBestHits, enrich_pavprot_with_bbh` | Find reciprocal best DIAMOND hits for ortholog confidence | `--run-diamond --run-bbh` |
| `mapping_multiplicity.py` | `from detect_one2many_mappings import detect_multiple_mappings` | Generate 1:N and N:1 mapping summary reports | Always (called at end of pavprot) |

---

### analysis/ - Downstream Analysis Scripts (Consume pavprot output)

| Script | Input | Output | Purpose |
|--------|-------|--------|---------|
| `gsmc.py` | `synonym_mapping_liftover_gffcomp.tsv` | `scenario_*.tsv` files | Classify gene pairs into biological scenarios (E, A, B, J, CDI, F, G, H) |
| `synonym_mapping_summary.py` | `synonym_mapping_liftover_gffcomp.tsv` | stdout statistics | Generate summary statistics (counts, distributions) |
| `inconsistent_genes_transcript_IPR_PAV.py` | `synonym_mapping_liftover_gffcomp.tsv` (with IPR) | `*_inconsistent_genes.tsv`, `*.png` | Find genes with transcripts in different IPR presence/absence quadrants |

---

### utils/ - Pre-processing / Standalone Utilities

| Script | Input | Output | Purpose |
|--------|-------|--------|---------|
| `parse_liftover_extra_copy_number.py` | Liftoff GFF3, (optional) tracking file | `extra_copies.tsv`, `*_liftover.faa` | Extract duplicated genes from Liftoff output for pavprot `--liftoff-gff` |
| `synonym_mapping_parse.py` | pavprot TSV | stdout | Count unique query genes per reference gene (utility) |

---

### plot/ - Visualization Scripts

| Script | Input | Output | Purpose |
|--------|-------|--------|---------|
| `plot_ipr_comparison.py` | pavprot TSV (with IPR) | `*_scatter.png` | Query vs Ref IPR domain length scatter plots by class_type |
| `plot_ipr_gene_level.py` | pavprot TSV (with IPR) | `*_gene_level.png` | Gene-level IPR domain distribution |
| `plot_ipr_shapes.py` | pavprot TSV (with IPR) | `*_shapes.png` | Domain shape/distribution visualization |
| `plot_ipr_advanced.py` | pavprot TSV (with IPR) | `*_advanced.png` | Advanced multi-panel IPR visualizations |
| `plot_ipr_proportional_bias.py` | pavprot TSV (with IPR) | `*_bias.png` | Proportional bias analysis between genomes |
| `plot_domain_comparison.py` | InterProScan outputs | `*_domain_comp.png` | Direct domain comparison between ref/query |

---

## Output Files by Script

### pavprot.py (Main Orchestrator)

**Location:** `analysis/pavprot.py`

| Output File | Description | When Generated |
|-------------|-------------|----------------|
| `synonym_mapping_liftover_gffcomp.tsv` | Main output - gene/transcript mappings with all metrics | Always |
| `*_ref_to_multiple_query.tsv` | 1:N mapping summary (ref genes mapping to multiple queries) | Always |
| `*_ref_to_multiple_query_detailed.tsv` | 1:N mapping details with transcript info | Always |
| `*_query_to_multiple_ref.tsv` | N:1 mapping summary (query genes mapping to multiple refs) | Always |
| `*_query_to_multiple_ref_detailed.tsv` | N:1 mapping details with transcript info | Always |
| `*_multiple_mappings_summary.txt` | Statistics summary of all mapping types | Always |
| `*_total_ipr_length.tsv` | IPR domain length per gene | `--interproscan-out` |
| `*_domain_distribution.tsv` | Domain details per transcript | `--interproscan-out` |

**Main Output Columns:**
```
ref_gene | ref_transcript | query_gene | query_transcript | class_code | exons |
class_code_multi_query | class_code_multi_ref | class_type_transcript | class_type_gene |
emckmnj | emckmnje | ref_multi_transcript | qry_multi_transcript | exact_match |
class_code_pair | ref_multi_query | qry_multi_ref | ref_query_count | qry_ref_count |
[query_total_ipr_domain_length] | [ref_total_ipr_domain_length] |
[pident | qcovhsp | scovhsp | identical_aa | mismatched_aa | indels_aa | aligned_aa] |
[is_bbh | bbh_avg_pident | bbh_avg_coverage]
```
*Bracketed columns are optional based on flags*

---

### gsmc.py (Scenario Classification)

**Location:** `analysis/gsmc.py`

#### Exclusive Scenario Definitions (Updated 2026-01-09)

All scenarios are **mutually exclusive** - a gene pair belongs to exactly one scenario.

| Scenario | `scenario` | `mapping_type` | Criteria | Status |
|----------|------------|----------------|----------|--------|
| E | `E` | `1to1` | ref→1 query AND query→1 ref | ✅ Active |
| A | `A` | `1to2N` | ref→exactly 2 queries, NOT in CDI | ✅ Active |
| J | `J` | `1to2N+` | ref→3+ queries, NOT in CDI | ✅ Active |
| B | `B` | `Nto1` | query→2+ refs, NOT in CDI | ✅ Active |
| CDI | `CDI` | `complex` | Cross-mapping (both sides multi) | ✅ Active |
| G | `G` | `unmapped_ref` | Ref gene with no query match | ✅ Active |
| H | `H` | `unmapped_query` | Query gene with no ref match | ✅ Active |
| F | `F` | `swap` | Positional swaps | ⏸️ **DISABLED** |

#### Output Files

| Output File | Description | Status |
|-------------|-------------|--------|
| `scenario_E_1to1_orthologs.tsv` | Exclusive 1:1 ortholog pairs | Active |
| `scenario_A_1toN_mappings.tsv` | One ref → exactly 2 queries | Active |
| `scenario_B_Nto1_mappings.tsv` | Multiple refs → one query | Active |
| `scenario_J_complex_1toN_mappings.tsv` | One ref → 3+ queries | Active |
| `scenario_CDI_cross_mappings.tsv` | Cross-mapping classification | Active |
| `scenario_G_unmapped_ref_genes.tsv` | Ref genes without query matches | Active |
| `scenario_H_unmapped_query_genes.tsv` | Query genes without ref matches | Active |
| `scenario_F_positional_swaps.tsv` | Adjacent gene order inversions | **DISABLED** |
| `detection_summary.txt` | Summary counts for all scenarios | Active |

**Output Columns (scenario files):**
```
ref_gene | ref_transcripts | ref_transcript_count | query_gene | query_transcripts |
query_transcript_count | scenario | mapping_type
```

---

### mapping_multiplicity.py (1:N Detection)

**Location:** `analysis/mapping_multiplicity.py` (imported by pavprot.py)

| Output File | Description |
|-------------|-------------|
| `*_ref_to_multiple_query.tsv` | Summary of ref genes mapping to multiple queries |
| `*_ref_to_multiple_query_detailed.tsv` | Detailed transcript-level info for 1:N |
| `*_query_to_multiple_ref.tsv` | Summary of query genes mapping to multiple refs |
| `*_query_to_multiple_ref_detailed.tsv` | Detailed transcript-level info for N:1 |
| `*_multiple_mappings_summary.txt` | Text summary with counts |

---

### parse_interproscan.py (IPR Domain Parsing)

**Location:** `analysis/parse_interproscan.py` (imported by pavprot.py)

| Output File | Description |
|-------------|-------------|
| `*_total_ipr_length.tsv` | Total IPR domain length per gene (merged overlaps) |
| `*_domain_distribution.tsv` | All domain annotations per transcript |

**Columns in *_total_ipr_length.tsv:**
```
gene_id | total_ipr_domain_length
```

**Columns in *_domain_distribution.tsv:**
```
transcript_id | gene_id | ipr_accession | ipr_description | start | end | length
```

---

### inconsistent_genes_transcript_IPR_PAV.py (IPR Consistency Analysis)

**Location:** `analysis/inconsistent_genes_transcript_IPR_PAV.py`

| Output File | Description |
|-------------|-------------|
| `*_inconsistent_genes.tsv` | Genes with transcripts in different IPR quadrants |
| `*_inconsistent_genes_summary.png` | Visualization of inconsistent genes |

---

### plot/ Scripts (Visualization)

**Location:** `plot/`

| Script | Output Files |
|--------|-------------|
| `plot_ipr_comparison.py` | `*_scatter.png`, `*_hexbin.png`, `*_quadrants.png`, `*_by_class_type.png` |
| `plot_ipr_gene_level.py` | `*_gene_level.png` |
| `plot_ipr_advanced.py` | `*_advanced.png`, `*_loglog.png`, `*_regression.png` |
| `plot_ipr_shapes.py` | `*_shapes.png` |
| `plot_ipr_proportional_bias.py` | `*_bias.png`, `*_bland_altman.png` |
| `plot_domain_comparison.py` | `*_domain_comp.png` |

---

### utils/ Scripts (Utilities)

**Location:** `utils/`

| Script | Output Files | Description |
|--------|-------------|-------------|
| `parse_liftover_extra_copy_number.py` | `extra_copies.tsv`, `*_liftover.faa` | Pre-processing for Liftoff GFF3 |
| `synonym_mapping_parse.py` | stdout | Query gene counting utility |

---

## Data Flow Summary

```
                    ┌──────────────────────────────────────────────┐
                    │           RAW INPUT FILES                    │
                    │  GffCompare, GFF3, FASTA, InterProScan       │
                    └──────────────────────┬───────────────────────┘
                                           │
                    ┌──────────────────────▼───────────────────────┐
                    │    OPTIONAL PRE-PROCESSING                   │
                    │  utils/parse_liftover_extra_copy_number.py   │
                    └──────────────────────┬───────────────────────┘
                                           │
┌──────────────────────────────────────────▼───────────────────────────────────────────── 
│                               pavprot.py                                                 
│                          (CENTRAL PIPELINE)                                             
│    ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐                  
│    │ parse_interproscan │ │ bidirectional_     │ │ detect_one2many_   │                  
│    │ .py                │ │ best_hits.py       │ │ mappings.py        │                  
│    │ InterProParser     │ │ BidirectionalBest  │ │ detect_multiple_   │                  
│    │ run_interproscan   │ │ Hits               │ │ mappings()         │                  
│    │ total_ipr_length   │ │ enrich_pavprot_    │ │                    │                  
│    │                    │ │ with_bbh           │ │                    │                  
│    └────────────────────┘ └────────────────────┘ └────────────────────┘                  │
└──────────────────────────────────────────┬─────────────────────────────────────────────
                                           │
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │      synonym_mapping_liftover_gffcomp.tsv    │
                    │              (PRIMARY OUTPUT)                │
                    └──────────────────────┬───────────────────────┘
                                           │
          ┌────────────────────────────────┼────────────────────────────────┐
          │                                │                                │
          ▼                                ▼                                ▼
┌─────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│ SCENARIO DETECTION  │     │ STATISTICS & SUMMARIES  │     │ VISUALIZATION           │
│ analysis/           │     │ analysis/               │     │ plot/                   │
│                     │     │                         │     │                         │
│ detect_advanced_    │     │ synonym_mapping_        │     │ plot_ipr_comparison.py  │
│ scenarios.py        │     │ summary.py              │     │ plot_ipr_gene_level.py  │
│                     │     │                         │     │ plot_ipr_advanced.py    │
│ ↓                   │     │ inconsistent_genes_     │     │ plot_ipr_shapes.py      │
│                     │     │ transcript_IPR_PAV.py   │     │ ...                     │
│ scenario_E.tsv      │     │                         │     │                         │
│ scenario_A.tsv      │     │                         │     │ ↓                       │
│ scenario_B.tsv      │     │                         │     │                         │
│ scenario_J.tsv      │     │                         │     │ *.png visualizations    │
│ scenario_CDI.tsv    │     │                         │     │                         │
│ scenario_F.tsv      │     │                         │     │                         │
│ scenario_G.tsv      │     │                         │     │                         │
│ scenario_H.tsv      │     │                         │     │                         │
└─────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
```

---

## Command-Line Flag → Module Activation

| pavprot.py Flag | Module Activated | Columns Added to Output |
|-----------------|-----------------|------------------------|
| (none) | Core parsing only | ref_gene, query_gene, class_code, ref_multi_query, qry_multi_ref, exact_match |
| `--run-diamond` | DiamondRunner | pident, qcovhsp, scovhsp, identical_aa, mismatched_aa, indels_aa |
| `--run-diamond --run-bbh` | BidirectionalBestHits | is_bbh, bbh_avg_pident, bbh_avg_coverage |
| `--interproscan-out` | InterProParser | query_total_ipr_domain_length, ref_total_ipr_domain_length |
| `--run-interproscan` | run_interproscan() + InterProParser | (runs InterProScan first, then parses) |
| `--liftoff-gff` | PAVprot.filter_extra_copy_transcripts | extra_copy_number |

---

## Typical Workflow Sequences

### Workflow 1: Basic Analysis
```bash
python pavprot.py --gff-comp tracking.txt --gff ref.gff,query.gff
python analysis/synonym_mapping_summary.py pavprot_out/synonym_mapping_liftover_gffcomp.tsv
```

### Workflow 2: Full Analysis with DIAMOND + BBH
```bash
python pavprot.py --gff-comp tracking.txt --gff ref.gff,query.gff \
    --ref-faa ref.faa --qry-faa query.faa \
    --run-diamond --run-bbh

python analysis/gsmc.py \
    --pavprot-output pavprot_out/synonym_mapping_liftover_gffcomp.tsv \
    --gff ref.gff,query.gff --scenarios E,A,B,J,CDI,F,G,H
```

### Workflow 3: Full Analysis with InterProScan
```bash
python pavprot.py --gff-comp tracking.txt --gff ref.gff,query.gff \
    --ref-faa ref.faa --qry-faa query.faa \
    --run-diamond --run-bbh \
    --interproscan-out ref_interpro.tsv,query_interpro.tsv

python plot/plot_ipr_comparison.py pavprot_out/synonym_mapping_liftover_gffcomp.tsv
python analysis/inconsistent_genes_transcript_IPR_PAV.py pavprot_out/synonym_mapping_liftover_gffcomp.tsv
```

### Workflow 4: Pre-processing Liftoff Extra Copies
```bash
# Step 1: Extract extra copy information
python utils/parse_liftover_extra_copy_number.py --gff liftoff.gff3 --output extra_copies.tsv

# Step 2: Run pavprot with liftoff info
python pavprot.py --gff-comp tracking.txt --gff ref.gff,query.gff \
    --liftoff-gff liftoff.gff3
```
