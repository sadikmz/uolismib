# Dataset Summary: PRJNA662919

## Dataset Identification

- **BioProject ID:** PRJNA662919
- **Database:** FungiDB
- **Organism:** Fusarium oxysporum (plant pathogenic fungus)
- **Strain:** FocnCong:1-1
- **Study Focus:** Morphological differentiation and developmental responses
- **Lead Author:** Yu Ayukawa
- **Corresponding Authors:** Tsutomu Arie, Ken Shirasu
- **Affiliation:** Iwate Biotechnology Research Center (Arie), Riken Center for Sustainable Resource Science (Shirasu)
- **Publication:** Nature Communications 12, 4477 (2021)
- **PMID:** 34108627

## Experimental Overview

### Research Objective

Investigation of gene expression changes associated with morphological differentiation in Fusarium oxysporum strain FocnCong:1-1 under different culture conditions. The study examines three distinct morphological forms of the pathogen: filamentous mycelia, chlamydospore-like bud cells, and hyphal structures, providing insights into developmental regulation in this plant pathogenic fungus.

### Study Design

**Morphological Differentiation Study:**

- **Condition 1:** Pure culture mycelia on PDA (potato dextrose agar) medium - control condition
- **Condition 2:** Bud cell morphology on NO3 media (nitrate-containing minimal medium)
- **Condition 3:** Hyphal structures/filamentous growth on NO3 media
- **Biological Replicates per Condition:** 3
- **Total Samples:** 9 RNA-Seq runs

## Sample Groups and Details

### PDA Mycelia (3 biological replicates)

- **Sample Group Label:** PDA_mycelia
- **Description:** Fusarium oxysporum pure culture on PDA medium (control condition)
- **Culture Condition:** PDA at 25°C, standard fungal culture
- **Morphology:** Filamentous hyphal growth
- **Biological Replicates:** 3

#### PDA Mycelia Replicate 1

- **Run Accession:** SRR12623566
- **BioSample ID:** SAMN16100087
- **Sample Alias:** FoxyspPDA_mycelia_rep1
- **Read Count:** 6.98M reads
- **Base Count:** 580.6 Mb
- **Biological Replicate Number:** 1

#### PDA Mycelia Replicate 2

- **Run Accession:** SRR12623567
- **BioSample ID:** SAMN16100086
- **Sample Alias:** FoxyspPDA_mycelia_rep2
- **Read Count:** 4.37M reads
- **Base Count:** 362.7 Mb
- **Biological Replicate Number:** 2

#### PDA Mycelia Replicate 3

- **Run Accession:** SRR12623568
- **BioSample ID:** SAMN16100085
- **Sample Alias:** FoxyspPDA_mycelia_rep3
- **Read Count:** 7.97M reads
- **Base Count:** 662.1 Mb
- **Biological Replicate Number:** 3

**PDA Mycelia Group Summary:** 3 biological replicates, 19.3M total reads, 1.61 Gb total bases

### NO3 Media - Bud Cell Morphology (3 biological replicates)

- **Sample Group Label:** NO3_budcells
- **Description:** Fusarium oxysporum bud cell (chlamydospore-like) morphology on NO3 media
- **Culture Condition:** NO3 media (minimal medium with nitrate as nitrogen source), stress/differentiation condition
- **Morphology:** Specialized spore-like structures (bud cells)
- **Biological Replicates:** 3

#### Bud Cell Replicate 1

- **Run Accession:** SRR12623569
- **BioSample ID:** SAMN16100084
- **Sample Alias:** FoxyspNO3_budcell_rep1
- **Read Count:** 6.76M reads
- **Base Count:** 562.1 Mb
- **Biological Replicate Number:** 1

#### Bud Cell Replicate 2

- **Run Accession:** SRR12623570
- **BioSample ID:** SAMN16100083
- **Sample Alias:** FoxyspNO3_budcell_rep2
- **Read Count:** 6.61M reads
- **Base Count:** 548.4 Mb
- **Biological Replicate Number:** 2

#### Bud Cell Replicate 3

- **Run Accession:** SRR12623571
- **BioSample ID:** SAMN16100082
- **Sample Alias:** FoxyspNO3_budcell_rep3
- **Read Count:** 8.20M reads
- **Base Count:** 680.6 Mb
- **Biological Replicate Number:** 3

**Bud Cell Group Summary:** 3 biological replicates, 21.6M total reads, 1.79 Gb total bases

### NO3 Media - Hyphal Growth (3 biological replicates)

- **Sample Group Label:** NO3_hypha
- **Description:** Fusarium oxysporum hyphal structures on NO3 media
- **Culture Condition:** NO3 media (minimal medium with nitrate), differentiation condition promoting hyphal elongation
- **Morphology:** Filamentous hyphal structures (thin, elongated hyphae)
- **Biological Replicates:** 3

#### Hypha Replicate 1

- **Run Accession:** SRR12623572
- **BioSample ID:** SAMN16100106
- **Sample Alias:** FoxyspNO3_hypha_rep1
- **Read Count:** 4.66M reads
- **Base Count:** 387.4 Mb
- **Biological Replicate Number:** 1

#### Hypha Replicate 2

- **Run Accession:** SRR12623574
- **BioSample ID:** SAMN16100105
- **Sample Alias:** FoxyspNO3_hypha_rep2
- **Read Count:** 2.97M reads
- **Base Count:** 245.3 Mb
- **Biological Replicate Number:** 2

#### Hypha Replicate 3

- **Run Accession:** SRR12623575
- **BioSample ID:** SAMN16100104
- **Sample Alias:** FoxyspNO3_hypha_rep3
- **Read Count:** 5.85M reads
- **Base Count:** 486.2 Mb
- **Biological Replicate Number:** 3

**Hypha Group Summary:** 3 biological replicates, 13.5M total reads, 1.12 Gb total bases

## Dataset Summary Statistics

### Overall Summary

- **Total Samples:** 9 RNA-Seq runs
- **Total Read Count:** 54.4M reads
- **Total Base Count:** 4.51 Gb
- **Sequencing Platform:** Illumina NextSeq 500
- **Library Layout:** Single-end reads (75 bp)
- **Strand Specificity:** Strand-specific (using cDNA directional library prep)
- **Library Selection:** cDNA
- **Data Type:** Organism-specific (pathogen only)

### Sample Distribution

| Condition     | Biological Replicates | Total Reads | Total Bases | Average Reads per Rep | Purpose                          |
| ------------- | --------------------- | ----------- | ----------- | --------------------- | -------------------------------- |
| PDA (Control) | 3                     | 19.3M       | 1.61 Gb     | 6.4M                  | Baseline mycelial development    |
| NO3 Bud Cells | 3                     | 21.6M       | 1.79 Gb     | 7.2M                  | Specialized spore morphogenesis  |
| NO3 Hypha     | 3                     | 13.5M       | 1.12 Gb     | 4.5M                  | Stress-induced hyphal elongation |

## Data Type Characterization

- **RNA-Seq Type:** Whole transcriptome (bulk RNA-Seq)
- **Organism Type:** Single organism (pathogenic fungus only)
- **Study Type:** NOT Dual RNA-Seq (excludes host plant transcriptome despite original dataset including host-pathogen co-infection samples)
- **Read Type:** Single-end only (not mixed with paired-end)
- **Strandedness:** Strand-specific (library prepared using directional cDNA synthesis)

## Data Quality Notes

- Consistent library preparation and sequencing protocol across all samples
- 3 biological replicates per condition enable robust statistical analysis
- Strand-specific sequencing allows accurate assessment of directional gene expression
- Single-end 75bp reads sufficient for genome-guided transcriptome mapping given reference genome availability
- Relatively consistent read depth across samples within groups (range 2.97M-8.20M reads)


---

# 

