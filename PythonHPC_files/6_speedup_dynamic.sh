#!/bin/bash
#BSUB -J jacobi_parallel_dynamic
#BSUB -q hpc
#BSUB -W 20:00
#BSUB -R "rusage[mem=2GB]"
#BSUB -o jacobi_parallel_20_dynamic_%J.out
#BSUB -e jacobi_parallel_20_dynamic_%J.err
#BSUB -B 
#BSUB -N 
#BSUB -u s203788@student.dtu.dk
#BSUB -R "select[model == XeonGold6126]"
#BSUB -n 16 
#BSUB -R "span[hosts=1]"

# Activate your virtual environment
source /dtu/projects/02613_2024/conda/conda_init.sh
conda activate 02613

# Run the simulation for a small subset (10 floorplans) and time it.
#time python simulate.py 10


# Time the parallel simulation
# Number of floorplans to process.
NUM_FLOORPLANS=100

# Output results file: the script will append results from each run.
RESULTS_FILE="speedup_results_20_dynamic.txt"
echo "Speedup Experiment Results" > ${RESULTS_FILE}

# Array of worker counts to test.
for workers in 1 2 4 8 16; do
    echo "Running experiment with ${workers} worker(s) ..." | tee -a ${RESULTS_FILE}
    # Time the run and append output to results file.
    # Note: 'time' outputs to stderr, so redirect accordingly.
    { time python 6_simulate_parallel_dynamic.py ${NUM_FLOORPLANS} ${workers}; } 2>&1 | tee -a ${RESULTS_FILE}
    echo "----------------------------------------" >> ${RESULTS_FILE}
done

