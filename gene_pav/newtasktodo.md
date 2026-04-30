For F. oxysporum old vs new annotaitonn, can you help with the following?

A Venn diagram showing the similarities and differences between the protein-coding genes in the two genomes
InterPro summary statistics - total number of proteins and percentage of proteins with at least one InterPro domain

Use the output from pavprot for the ven diagram and generate python script for each task
Use the gff file to capture total gene counts.  

# Base directories
HOME_DIR="$HOME"
PROJECT_DIR="$HOME_DIR/projects/github_prj/uolismib/gene_pav"
DATA_DIR="$HOME_DIR/Documents/projects/FungiDB/foc
oldGff="$HOME_DIR/Documents/projects/FungiDB/foc47/data/plot/FungiDB-68_Fo47.gff
oldGff="$HOME_DIR/Documents/projects/FungiDB/foc47/data/plot/GCF_013085055.1.gff

1. Venn Diagram Script for Gene Comparison
- Option1: use diamond blastp output of pavpropt (for plotting provide a minimum and coverage and percent identity to consider similar propteins). Update foc_blastp_venn_pident50.0_cov50.0.png: Total proteins should total protein coding genes in the gff file, with similar counter part would be blastp similarity ouput ...  
- Option2: 
- Option3:
- Option3:
- Option4: Using OrthoFinder ouput
- 
-  
2. interproscan ouput
old="$DATA_DIR/output/inteproscan/foc67_v68.prot.faa.tsv,
new=$DATA_DIR/output/inteproscan/GCF_013085055.1.prot.faa.tsv"

3. gff files
4. 