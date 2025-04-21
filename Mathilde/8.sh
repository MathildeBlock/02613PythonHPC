#!/bin/bash
#BSUB -J numba
#BSUB -q c02613
#BSUB -W 00:15
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

# 2 Reference Implementation timing
# Run the simulation for a small subset (10 floorplans) and time it.
echo "reference"
time python simulate.py 10

# 8.2 Run and time the new solution for a small subset of floorplans
echo "cuda"
time python 8_numba.py 10
