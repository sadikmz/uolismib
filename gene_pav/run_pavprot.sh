#!/bin/bash

# This script runs the PAVPROT analysis pipeline.
# Usage: ./run_pavprot.sh

set -e

# Base directories
HOME_DIR="$HOME"
PROJECT_DIR="$HOME_DIR/projects/github_prj/uolismib/gene_pav"
DATA_DIR="$HOME_DIR/Documents/projects/FungiDB/foc47"

cd "$PROJECT_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

python pavprot.py \
  --gff-comp "$DATA_DIR/output/gffcompare_out/foc47_vs_GCF_013085055.1_gffcomp.tracking.tsv" \
  --gff "$DATA_DIR/data/v68/FungiDB-68_FoxysporumFo47.gff,$DATA_DIR/data/GCF_013085055.1/genomic.gff" \
  --liftoff-gff "$DATA_DIR/output/liftover_out/GCF_013085055.1_liftover_polished.gff3" \
  --class-code = c k m n j e \
  --prot "$DATA_DIR/output/pavprot_out/compareprot_out/input_seq_dir/qry_all.faa,$DATA_DIR/output/pavprot_out/compareprot_out/input_seq_dir/ref_all.faa" \
  --run-diamond \
  --run-bbh \
  --bbh-min-pident 30 \
  --bbh-min-coverage 50.0 \
  --output-prefix FocTst \
  --output-dir pavprot_out_${TIMESTAMP} \
  --interproscan-out "$DATA_DIR/output/inteproscan/foc67_v68.prot.faa.tsv,$DATA_DIR/output/inteproscan/GCF_013085055.1.prot.faa.tsv" \
  --plot
  # --run-pairwise  # Disabled: requires XM->XP ID mapping (see todo.md)
  # --filter-exact-match \
  # --filter-exclusive-1to1 \
  # --filter-class-type-gene "=,c,k,m,n,j,e"

