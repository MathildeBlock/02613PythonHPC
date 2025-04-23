import numpy as np
from os.path import join
from multiprocessing import Pool, cpu_count
import sys

def load_data(load_dir, bid):
    SIZE = 512
    u = np.zeros((SIZE + 2, SIZE + 2))
    u[1:-1, 1:-1] = np.load(join(load_dir, f"{bid}_domain.npy"))
    interior_mask = np.load(join(load_dir, f"{bid}_interior.npy"))
    return u, interior_mask

def jacobi(u, interior_mask, max_iter, atol=1e-6):
    u = np.copy(u)
    for _ in range(max_iter):
        # Compute average of neighbors (left, right, up, and down)
        u_new = 0.25 * (u[1:-1, :-2] + u[1:-1, 2:] +
                        u[:-2, 1:-1] + u[2:, 1:-1])
        u_new_interior = u_new[interior_mask]
        delta = np.abs(u[1:-1, 1:-1][interior_mask] - u_new_interior).max()
        u[1:-1, 1:-1][interior_mask] = u_new_interior
        if delta < atol:
            break
    return u

def summary_stats(u, interior_mask):
    u_interior = u[1:-1, 1:-1][interior_mask]
    return {
        'mean_temp': u_interior.mean(),
        'std_temp': u_interior.std(),
        'pct_above_18': np.sum(u_interior > 18) / u_interior.size * 100,
        'pct_below_15': np.sum(u_interior < 15) / u_interior.size * 100,
    }

def process_building(args):
    bid, load_dir, max_iter, abs_tol = args
    u0, interior_mask = load_data(load_dir, bid)
    u = jacobi(u0, interior_mask, max_iter, abs_tol)
    stats = summary_stats(u, interior_mask)
    return (bid, stats)

if __name__ == "__main__":
    # Directory with the data files.
    LOAD_DIR = '/dtu/projects/02613_2025/data/modified_swiss_dwellings/'
    with open(join(LOAD_DIR, 'building_ids.txt'), 'r') as f:
        building_ids = f.read().splitlines()

    # First argument: number of floorplans to process.
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    building_ids = building_ids[:N]

    # Second argument: number of workers to use (optional).
    requested_workers = int(sys.argv[2]) if len(sys.argv) > 2 else min(cpu_count(), N)
    num_workers = min(requested_workers, N)

    MAX_ITER = 20_000
    ABS_TOL = 1e-4

    # Prepare argument list for the pool
    args = [(bid, LOAD_DIR, MAX_ITER, ABS_TOL) for bid in building_ids]

    # Print header information with the used number of workers.
    print("NUM_WORKERS:", num_workers)
    stat_keys = ['mean_temp', 'std_temp', 'pct_above_18', 'pct_below_15']
    print("building_id," + ", ".join(stat_keys))

    # Dynamic scheduling: use imap_unordered with a chunksize of 1.
    with Pool(processes=num_workers) as pool:
        results = pool.imap_unordered(process_building, args, chunksize=1)
        results = list(results)  

    # Output results for each floorplan.
    for bid, stats in results:
        print(f"{bid},", ", ".join(str(stats[k]) for k in stat_keys))
