#!/bin/bash
#SBATCH --job-name=fo47_pavprot 
#SBATCH --partition=med
#SBATCH --time=24-00:00:00
#SBATCH --mem=40G
#SBATCH --ntasks=1          
#SBATCH --cpus-per-task=40   
#SBATCH --output=job.%J.%N.out
#SBATCH --error=job.%J.%N.err
#SBATCH --mail-user=sadikm@liverpool.ac.uk
#SBATCH --mail-type=END,FAIL

# module load liftoff/1.6.3
module load python/3.11.9

# cwd=$(pwd)
threads=31
tmp="/dev/shm"
genotype="GCF_013085055.1"
DATADIR="/home/sadikm/hc-storage/data"
ref_genome="$DATADIR/foc47/v68/FungiDB-68_FoxysporumFo47_Genome.fasta"
ref_gff="$DATADIR/foc47/v68/FungiDB-68_FoxysporumFo47.gff"
ref_prot="$DATADIR/foc47/v68/FungiDB-68_FoxysporumFo47_AnnotatedProteins.fasta"
target_genome=$DATADIR/foc47/$genotype/"$genotype"_ASM1308505v1_genomic.fna
target_prot=$DATADIR/foc47/$genotype/protein.faa
gffcompare_tracking=gffcompare_out/"fo47_vs_${genotype}_gffcomp.tracking"
targt_gff=$DATADIR/foc47/$genotype/genomic.gff

APPSDIR=/home/sadikm/hc-storage/apps

./pavprot.02.py \
--gff-comp "$gffcompare_tracking" \
--ref-gff "$targt_gff" \
--ref-faa "$target_prot" \
--qry-faa "$ref_prot" \
--run-diamond \
--diamond-threads $threads \
--output-prefix fo47_vs_"$genotype"