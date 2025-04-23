from os.path import join
import sys
import numpy as np
from numba import njit
from numba import cuda

if cuda.is_available():
    print("CUDA is available. Using GPU.")
else:
    print("CUDA is not available. Using CPU.")

@cuda.jit
def jacobi_kernel(u, u_new, interior_mask):
    i, j = cuda.grid(2)
    rows, cols = u.shape
    # Only update interior points (not boundary)
    if 1 <= i < rows - 1 and 1 <= j < cols - 1:
        if interior_mask[i-1, j-1]:
            u_new[i, j] = 0.25 * (u[i, j-1] + u[i, j+1] + u[i-1, j] + u[i+1, j])
        else:
            u_new[i, j] = u[i, j]
    elif i < rows and j < cols:
        # Copy boundary points unchanged
        u_new[i, j] = u[i, j]

def jacobi_cuda(u, interior_mask, max_iter):
    """
    Jacobi solver using a custom CUDA kernel.
    Args:
        u: (np.ndarray) Initial grid, shape (N+2, N+2)
        interior_mask: (np.ndarray) Boolean mask, shape (N, N)
        max_iter: (int) Number of iterations
    Returns:
        np.ndarray: Solution grid after max_iter Jacobi iterations
    """
    u_d = cuda.to_device(u)
    u_new_d = cuda.device_array_like(u)
    mask_d = cuda.to_device(interior_mask)

    rows, cols = u.shape
    threadsperblock = (16, 16)
    blockspergrid_x = (rows + threadsperblock[0] - 1) // threadsperblock[0]
    blockspergrid_y = (cols + threadsperblock[1] - 1) // threadsperblock[1]
    blockspergrid = (blockspergrid_x, blockspergrid_y)

    for _ in range(max_iter):
        jacobi_kernel[blockspergrid, threadsperblock](u_d, u_new_d, mask_d)
        # Swap device arrays for next iteration
        u_d, u_new_d = u_new_d, u_d

    # After even number of iterations, u_d has the latest result
    # After odd, u_new_d has the latest result
    if max_iter % 2 == 0:
        result = u_d.copy_to_host()
    else:
        result = u_new_d.copy_to_host()
    return result


def load_data(load_dir, bid):
    SIZE = 512
    u = np.zeros((SIZE + 2, SIZE + 2))
    u[1:-1, 1:-1] = np.load(join(load_dir, f"{bid}_domain.npy"))
    interior_mask = np.load(join(load_dir, f"{bid}_interior.npy"))
    return u, interior_mask

def summary_stats(u, interior_mask):
    u_interior = u[1:-1, 1:-1][interior_mask]
    mean_temp = u_interior.mean()
    std_temp = u_interior.std()
    pct_above_18 = np.sum(u_interior > 18) / u_interior.size * 100
    pct_below_15 = np.sum(u_interior < 15) / u_interior.size * 100
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
        u = jacobi_cuda(u0, interior_mask, MAX_ITER)
        all_u[i] = u

    # Print summary statistics in CSV format
    stat_keys = ['mean_temp', 'std_temp', 'pct_above_18', 'pct_below_15']
    print('building_id, ' + ', '.join(stat_keys))  # CSV header
    for bid, u, interior_mask in zip(building_ids, all_u, all_interior_mask):
        stats = summary_stats(u, interior_mask)
        print(f"{bid},", ", ".join(str(stats[k]) for k in stat_keys))