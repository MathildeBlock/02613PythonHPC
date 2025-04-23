from os.path import join
import numpy as np
import matplotlib.pyplot as plt

# Set the directory containing the data
LOAD_DIR = '/dtu/projects/02613_2025/data/modified_swiss_dwellings/'

# Load building IDs
with open(join(LOAD_DIR, 'building_ids.txt'), 'r') as f:
    building_ids = f.read().splitlines()

# Select a few floorplans to visualize (e.g., the first 3)
selected_ids = building_ids[:3]

def load_data(load_dir, bid):
    """
    Load the initial temperature domain and the interior mask for a given building ID.
    """
    SIZE = 512
    u = np.zeros((SIZE + 2, SIZE + 2))
    u[1:-1, 1:-1] = np.load(join(load_dir, f"{bid}_domain.npy"))
    interior_mask = np.load(join(load_dir, f"{bid}_interior.npy"))
    return u, interior_mask

def jacobi(u, interior_mask, max_iter, atol=1e-6):
    """
    Perform Jacobi iterations to compute the steady-state temperature distribution.
    """
    u = np.copy(u)
    for i in range(max_iter):
        # Compute the average of the four neighboring points
        u_new = 0.25 * (u[1:-1, :-2] + u[1:-1, 2:] +
                        u[:-2, 1:-1] + u[2:, 1:-1])
        # Update only the interior points using the provided mask
        u_new_interior = u_new[interior_mask]
        delta = np.abs(u[1:-1, 1:-1][interior_mask] - u_new_interior).max()
        u[1:-1, 1:-1][interior_mask] = u_new_interior
        if delta < atol:
            break
    return u

# Simulation parameters
MAX_ITER = 20_000
ABS_TOL = 1e-4

# Prepare a figure to display the simulation results
fig, axes = plt.subplots(1, len(selected_ids), figsize=(5 * len(selected_ids), 5))

for idx, bid in enumerate(selected_ids):
    # Load the initial domain and interior mask
    u, interior_mask = load_data(LOAD_DIR, bid)
    # Run the simulation
    u_sim = jacobi(u, interior_mask, MAX_ITER, ABS_TOL)
    
    # Plot the resulting temperature distribution
    ax = axes[idx] if len(selected_ids) > 1 else axes
    im = ax.imshow(u_sim, cmap='hot')
    ax.set_title(f"Building {bid}")
    ax.axis('off')
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

plt.tight_layout()
plt.show()
plt.savefig("simulation_floorplans_visualization.png", dpi=300)