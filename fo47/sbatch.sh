#!/bin/bash
#SBATCH --job-name=fo47_lo 
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

