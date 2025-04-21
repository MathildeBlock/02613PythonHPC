#!/bin/bash
#BSUB -J all
#BSUB -q c02613
#BSUB -W 03:00
#BSUB -R "rusage[mem=2GB]"
#BSUB -n 4
#BSUB -R "span[hosts=1]"
#BSUB -gpu "num=1:mode=exclusive_process"
#BSUB -o %J.out
#BSUB -e %J.err
#BSUB -B 
#BSUB -N 
#BSUB -u s204201@dtu.dk

# Activate your virtual environment
source /dtu/projects/02613_2024/conda/conda_init.sh
conda activate 02613

# 12
time python 12_all_floorplans.py
