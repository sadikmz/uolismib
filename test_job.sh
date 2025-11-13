#!/bin/bash
#SBATCH --job-name=test_job 
#SBATCH --partition=med
#SBATCH --time=24-00:00:00
#SBATCH --mem=40G
#SBATCH --ntasks=1          
#SBATCH --cpus-per-task=40   
#SBATCH --output=job.%J.%N.out
#SBATCH --error=job.%J.%N.err
#SBATCH --mail-user=sadikm@liverpool.ac.uk
#SBATCH --mail-type=END,FAIL

module load liftoff/1.6.3
# downlaod data
# "$APPSDIR"/datasets download genome accession "$genotype" --include protein,gff3,cds,rna,genome

## Load bash_profile to avail to tools appeneded in the $PATH. HOME set to "/home/sadikm/hc-storage"
source /home/sadikm/.bashrc

# for some reason (for new prog path in $HOME/apps), need to load bash_profile too
source /home/sadikm/.bash_profile


## When using conda installation 
# Load Miniconda3 module if exists in the HPC system
# module load Miniconda3/version.....

## conda base environment
HOME="/home/sadikm/hc-storage"
miniconda="$HOME/miniconda3"
source "$miniconda"/bin/activate

## activate the specific env to run
conda activate "$miniconda"/envs/busco

busco --help > busco_help.txt

gffcompare -h > gffcompare_help.txt

liftoff -h > liftoff_help.txt


