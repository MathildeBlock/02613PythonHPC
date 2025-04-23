import numpy as np
from os.path import join
import sys
from math import sqrt
from numba import njit, prange  # You can also experiment with parallel=True

@njit(cache=True)
def jacobi(u, interior_mask, max_iter, atol=1e-6):
    """
    Performs Jacobi iterations on a 2D grid using explicit loops.
    A double-buffering (ping–pong) approach is used to avoid extra copying.
    The interior of u (from u[1:-1,1:-1]) is updated only where interior_mask is True.
    
    Parameters:
      u           : 2D array of shape (SIZE+2, SIZE+2)
      interior_mask: 2D boolean array of shape (SIZE, SIZE) corresponding to u[1:-1,1:-1]
      max_iter    : maximum number of iterations
      atol        : absolute tolerance for convergence
      
    Returns:
      u           : updated 2D array after convergence
    """
    rows, cols = u.shape
    # Allocate a second buffer of the same shape as u for updates.
    u_new = u.copy()

    for it in range(max_iter):
        delta = 0.0
        # Iterate over the interior points
        for i in range(1, rows - 1):
            for j in range(1, cols - 1):
                if interior_mask[i-1, j-1]:
                    temp = 0.25 * (u[i, j-1] + u[i, j+1] + u[i-1, j] + u[i+1, j])
                    diff = abs(u[i, j] - temp)
                    if diff > delta:
                        delta = diff
                    u_new[i, j] = temp
        # Swap buffers: after the iteration, u_new becomes the current grid.
        u, u_new = u_new, u
        if delta < atol:
            break
    return u

def load_data(load_dir, bid):
    SIZE = 512
    u = np.zeros((SIZE + 2, SIZE + 2))
    # Load the interior domain into the interior of u.
    u[1:-1, 1:-1] = np.load(join(load_dir, f"{bid}_domain.npy"))
    interior_mask = np.load(join(load_dir, f"{bid}_interior.npy"))
    return u, interior_mask

def summary_stats(u, interior_mask):
    u_interior = u[1:-1, 1:-1][interior_mask]
    return {
        'mean_temp': u_interior.mean(),
        'std_temp': u_interior.std(),
        'pct_above_18': np.sum(u_interior > 18) / u_interior.size * 100,
        'pct_below_15': np.sum(u_interior < 15) / u_interior.size * 100,
    }

def process_building(args):
    """
    Loads the data for a floorplan, applies the Numba-accelerated Jacobi iterations,
    and returns summary statistics.
    """
    bid, load_dir, max_iter, abs_tol = args
    u, interior_mask = load_data(load_dir, bid)
    u_final = jacobi_numba(u, interior_mask, max_iter, abs_tol)
    stats = summary_stats(u_final, interior_mask)
    return (bid, stats)

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

    # Load floor plans
    all_u0 = np.empty((N, 514, 514))
    all_interior_mask = np.empty((N, 512, 512), dtype='bool')
    for i, bid in enumerate(building_ids):
        u0, interior_mask = load_data(LOAD_DIR, bid)
        all_u0[i] = u0
        all_interior_mask[i] = interior_mask

    # Run jacobi iterations for each floor plan
    MAX_ITER = 20_000
    ABS_TOL = 1e-4

    all_u = np.empty_like(all_u0)
    for i, (u0, interior_mask) in enumerate(zip(all_u0, all_interior_mask)):
        u = jacobi(u0, interior_mask, MAX_ITER, ABS_TOL)
        all_u[i] = u

    # Print summary statistics in CSV format
    stat_keys = ['mean_temp', 'std_temp', 'pct_above_18', 'pct_below_15']
    print('building_id, ' + ', '.join(stat_keys))  # CSV header
    for bid, u, interior_mask in zip(building_ids, all_u, all_interior_mask):
        stats = summary_stats(u, interior_mask)
        print(f"{bid},", ", ".join(str(stats[k]) for k in stat_keys))
