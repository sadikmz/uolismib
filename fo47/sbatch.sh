#!/bin/bash
#SBATCH --job-name=fo47_lo 
#SBATCH --partition=med
#SBATCH --time=24-00:00:00
#SBATCH --mem=20G
#SBATCH --ntasks=1          
#SBATCH --cpus-per-task=40   
#SBATCH --output=job.%J.out
#SBATCH --error=job.%J.err
#SBATCH --mail-user=sadikm@liverpool.ac.uk
#SBATCH --mail-type=END,FAIL

# load miniconda
# load miniconda
module load Miniconda3/23.9.0-0
#module load Trim_Galore/0.6.10-GCCcore-11.3.0

#Activate base environment
source ~/.bashrc

# Load bash_profile to avail to tools appeneded in the $PATH.
# Check the compatibilty of tools in bash_profile $PATH with those to be used in conda env before loading
source ~/.bash_profile

# activate the specific env to run
conda activate /home/data/salixomics/sadik/miniconda3/envs/liftoff
