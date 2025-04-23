from os.path import join
import sys

import numpy as np
import cupy as cp  # Added for GPU acceleration

def load_data(load_dir, bid):
    SIZE = 512
    u = np.zeros((SIZE + 2, SIZE + 2))
    u[1:-1, 1:-1] = np.load(join(load_dir, f"{bid}_domain.npy"))
    interior_mask = np.load(join(load_dir, f"{bid}_interior.npy"))
    return u, interior_mask

def jacobi(u, interior_mask, max_iter, atol=1e-6):
    # Move arrays to GPU
    u = cp.array(u)
    interior_mask = cp.array(interior_mask)

    for i in range(max_iter):
        u_new = 0.25 * (u[1:-1, :-2] + u[1:-1, 2:] + u[:-2, 1:-1] + u[2:, 1:-1])
        u_new_interior = u_new[interior_mask]
        delta = cp.abs(u[1:-1, 1:-1][interior_mask] - u_new_interior).max()
        u[1:-1, 1:-1][interior_mask] = u_new_interior

        if delta < atol:
            break
    # Return the GPU array directly
    return u

def summary_stats(u, interior_mask):
    # Assume u and interior_mask are already CuPy arrays on the GPU
    u_interior = u[1:-1, 1:-1][interior_mask]
    mean_temp = float(cp.mean(u_interior).get())
    std_temp = float(cp.std(u_interior).get())
    pct_above_18 = float((cp.sum(u_interior > 18) / u_interior.size * 100).get())
    pct_below_15 = float((cp.sum(u_interior < 15) / u_interior.size * 100).get())
    return {
        'mean_temp': mean_temp,
        'std_temp': std_temp,
        'pct_above_18': pct_above_18,
        'pct_below_15': pct_below_15,
    }

if __name__ == '__main__':
    # Load data
    LOAD_DIR = '/dtu/projects/02613_2025/data/modified_swiss_dwellings/'
    with open(join(LOAD_DIR, 'building_ids.txt'), 'r') as f:
        building_ids = f.read().splitlines()

    if len(sys.argv) < 2:
        N = 1
    else:
        N = int(sys.argv[1])
    building_ids = building_ids[:N]

    # Load floor plans (remains NumPy for initial loading)
    all_u0 = np.empty((N, 514, 514))
    all_interior_mask = np.empty((N, 512, 512), dtype='bool')
    for i, bid in enumerate(building_ids):
        u0, interior_mask = load_data(LOAD_DIR, bid)
        all_u0[i] = u0
        all_interior_mask[i] = interior_mask

    # Run jacobi iterations for each floor plan
    MAX_ITER = 20_000
    ABS_TOL = 1e-4

    # Store results as a list of CuPy arrays
    all_u_cp = []
    for i, (u0, interior_mask) in enumerate(zip(all_u0, all_interior_mask)):
        # jacobi now returns a CuPy array
        u_cp = jacobi(u0, interior_mask, MAX_ITER, ABS_TOL)
        all_u_cp.append(u_cp)

    # Convert masks to CuPy once before the stats loop
    all_interior_mask_cp = [cp.array(mask) for mask in all_interior_mask]

    # Print summary statistics in CSV format
    stat_keys = ['mean_temp', 'std_temp', 'pct_above_18', 'pct_below_15']
    print('building_id, ' + ', '.join(stat_keys))  # CSV header
    # Iterate through CuPy arrays for stats calculation
    for bid, u_cp, interior_mask_cp in zip(building_ids, all_u_cp, all_interior_mask_cp):
        # Pass CuPy arrays directly to summary_stats
        stats = summary_stats(u_cp, interior_mask_cp)
        print(f"{bid},", ", ".join(str(stats[k]) for k in stat_keys))