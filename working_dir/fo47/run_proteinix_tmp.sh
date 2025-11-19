#!/bin/bash -l
#SBATCH -J protenix_predict
#SBATCH -o protenix_predict_%A.out
#SBATCH -p gpu
#SBATCH --ntasks=1
#SBATCH -c 8
#SBATCH --gres=gpu:1
#SBATCH -t 2-00:00:00
#SBATCH --mail-type=ALL

# ========================= # Run Protenix # ========================= start_time=$(date +%s) 

conda create -n protenix python=3.11 
conda activate protenix 
pip install protenix
gitclone and pip install ~/Protenix-main

export DS_BUILD_OPS=0

protenix predict \
--input ./test.json \ 
--out_dir ./test3_protenix \
--seeds 101 \
--model_name "protenix_mini_esm_v0.5.0" \
--use_msa false \
--sample 1 

end_time=$(date +%s) 
runtime=$((end_time - start_time)) 
hours=$((runtime / 3600)) 
minutes=$(((runtime % 3600) / 60)) 
seconds=$((runtime % 60)) 
echo "Total runtime: ${hours}h ${minutes}m ${seconds}s"
