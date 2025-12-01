# InterProScan Parser

A comprehensive Python tool for running InterProScan and parsing its TSV output files with pandas-based data processing.

## Features

- Run InterProScan directly from the script with automatic pipeline execution
- Parse existing InterProScan TSV output files
- Select longest domain when proteins match multiple domains
- Track both overall longest domain and longest InterPro-annotated domain
- Generate domain length distribution statistics
- Export parsed results to TSV format

## Requirements

- Python 3.6+
- pandas library (`pip install pandas`)
- InterProScan (only if using `--run` mode)

## Usage

### Mode 1: Parse Existing Output

Parse an existing InterProScan TSV output (with auto-generated output filename):

```bash
python parse_interproscan.py --parse results.tsv
# Creates: results_parsed.tsv (15 columns - standard InterProScan format)
```

Parse with explicit output filename:

```bash
python parse_interproscan.py --parse results.tsv --output-parsed-tsv parsed_results.tsv
```

### Mode 2: Run InterProScan and Parse

Run InterProScan and parse the output (uses input file basename by default):

```bash
python parse_interproscan.py \
    --run \
    --input proteins.fasta \
    --format TSV \
    --cpu 8
# Creates: proteins.tsv (InterProScan output)
# Automatically runs longest domain analysis
# InterProScan runs with --iprlookup and --goterms enabled by default
```

Run with custom output basename:

```bash
python parse_interproscan.py \
    --run \
    --input proteins.fasta \
    --output-base myanalysis \
    --format TSV \
    --cpu 8
# Creates: myanalysis.tsv (InterProScan output)
# Automatically runs complete analysis pipeline
```

Run with pathways (--iprlookup and --goterms are always included):

```bash
python parse_interproscan.py \
    --run \
    --input proteins.fasta \
    --output-base results \
    --format TSV \
    --cpu 8 \
    --pathways
# InterProScan runs with --iprlookup, --goterms, and --pathways
```

Run with specific databases:

```bash
python parse_interproscan.py \
    --run \
    --input proteins.fasta \
    --output-base results \
    --databases Pfam,PRINTS,Gene3D \
    --cpu 4
```

### Longest Domain Analysis

Select only the longest domain for each protein and generate statistics. Proteins are automatically split into two files based on whether their longest IPR domain matches their overall longest domain.

**Auto-generated filenames** (simplest approach):

```bash
python parse_interproscan.py --parse results.tsv --longest-domain
# Creates 3 files:
#   - results_longest_domains.tsv (proteins where longest IPR domain = overall longest, IPRorNot=yes)
#   - results_non_ipr.tsv (proteins where longest IPR domain != overall longest, IPRorNot=no)
#   - results_domain_distribution.tsv (statistics for all domains)
```

**Explicit filenames**:

```bash
python parse_interproscan.py \
    --parse results.tsv \
    --longest-domain \
    --domain-stats-tsv domain_distribution.tsv \
    --output-parsed-tsv longest_domains.tsv
```

## Command-Line Arguments

### General Options

- `--run`: Run InterProScan before parsing (automatically enables `--longest-domain`)
- `--parse FILE`: Parse existing InterProScan TSV output file

### InterProScan Run Options (used with `--run`)

- `-i, --input FILE`: Input protein FASTA file (required)
- `-b, --output-base NAME`: Output file basename (optional, default: basename of input file)
  - InterProScan will append the format extension (e.g., `.tsv`, `.gff3`)
  - Example: `-b myanalysis` with `-f TSV` creates `myanalysis.tsv`
- `-f, --format {TSV,XML,JSON,GFF3}`: Output format (default: TSV)
- `--cpu N`: Number of CPUs to use (default: 4)
- `--databases DB`: Databases to search (default: all, or comma-separated list)
- `--pathways`: Include pathway annotations (optional)

**Note**: `--iprlookup` and `--goterms` are **always included by default** when running InterProScan. This ensures GO term annotations and InterPro mappings are always available in the output.

### Analysis Options

- `--longest-domain`: Select only the longest domain for each protein
- `--domain-stats-tsv FILE`: Output file for domain length distribution (TSV)
  - Default (with `--longest-domain`): `<basename>_domain_distribution.tsv`
- `--output-parsed-tsv FILE`: Output file for parsed results (TSV)
  - Default (without `--longest-domain`): `<basename>_parsed.tsv`
  - Default (with `--longest-domain`): `<basename>_longest_domains.tsv`

**Note**:
- `<basename>` refers to the InterProScan output file's basename (determined by `-b` option or input file)
- When `--run` is used, `--longest-domain` is automatically enabled for complete pipeline execution
- When `--longest-domain` is used without any output arguments, all output files are automatically generated with descriptive names
- **All output files use the same basename** for consistent file organization

## TSV Format

### Input Format (InterProScan Standard - 15 columns)

InterProScan outputs a 15-column TSV format:

1. Protein accession (e.g., P51587)
2. Sequence MD5 digest (e.g., 14086411a2cdf1c4cba63020e1622579)
3. Sequence length (e.g., 3418)
4. Analysis/Database (e.g., Pfam, PRINTS, Gene3D)
5. Signature accession (e.g., PF09103, G3DSA:2.40.50.140)
6. Signature description (e.g., BRCA2 repeat profile)
7. Start location
8. Stop location
9. Score - e-value or score from database method (e.g., 3.1E-52)
10. Status - match status (T: true)
11. Date - run date
12. InterPro accession (e.g., IPR002093) - **may be "-" if no InterPro mapping**
13. InterPro description (e.g., BRCA2 repeat) - **may be "-"**
14. GO annotations (e.g., GO:0005515|GO:0006302) - **may be "-"**
15. Pathway annotations (e.g., REACT_71|MetaCyc:PWY-123) - **may be "-"**

**Note**: Missing values are represented as "-" (dash character).

### Output Format

#### Standard Parsing (15 columns)

When using `--parse` without `--longest-domain`, the output maintains the standard 15-column InterProScan format.

#### Longest Domain Analysis (18 columns, split into 2 files)

When using `--longest-domain`, proteins are split into two output files, each containing **18 columns**:

**Main output file** (`*_longest_domains.tsv`): Proteins where longest IPR domain IS the overall longest (IPRorNot="yes")
**Non-IPR output file** (`*_non_ipr.tsv`): Proteins where longest IPR domain is NOT the overall longest (IPRorNot="no")

**Column structure (both files)**:
- **Columns 1-15**: Standard InterProScan fields (same as input)
- **Column 16**: `longestDom` - name of the longest domain overall (any database)
- **Column 17**: `longestIPRdom` - name of the longest InterPro-annotated domain (IPR prefix)
- **Column 18**: `IPRorNot` - yes/no indicating if longestIPRdom matches longestDom

**Column Details**:
- `longestDom`: The domain name (or accession if no description) of the longest matching domain from any database
- `longestIPRdom`: The domain name of the longest domain with InterPro annotation (starts with "IPR"). Empty if no IPR domains found.
- `IPRorNot`: "yes" if the longest IPR domain matches the overall longest domain, "no" otherwise (determines which file the protein goes to)
