# ISMIB GitHub Projects Repository

Bioinformatics tools and scripts for genomic analysis.

## Projects

### Gene Split/Merge Detection Tool

A Python implementation for detecting gene split and merge events between two genome annotations using DIAMOND BLASTP.

**Key Features:**
- Fast protein alignment with DIAMOND BLASTP (10-20,000x faster than BLAST+)
- Bidirectional best hits (BBH) for ortholog identification
- Gene structure analysis to detect splits and merges
- Optional protein clustering with multiple algorithms

**Documentation:**
- [Main README](gene_split_merge/README.md)
- [GFF3 File Format Guide](gene_split_merge/tmp/GFF3_FORMAT.md)

**Location:** `gene_split_merge/`

---

### Parse InterProScan

Tools for parsing and analyzing InterProScan results.

**Location:** `parse_interproscan/`

---

### Gene PAV (Presence/Absence Variation)

Tools for analyzing gene presence/absence variation across genomes.

**Location:** `gene_pav/`

---

## Additional Resources

- Scripts and utilities: `uolocal/`
- Temporary files: `tmp_compare/`

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

**Note:** Some codes are experimental and not fully tested. Please validate with your datasets before production use.
