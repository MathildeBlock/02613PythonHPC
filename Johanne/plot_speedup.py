import matplotlib.pyplot as plt

# Hypothetical measured times in seconds (replace these with your actual timings)
workers = [1, 2, 4, 8, 16]
times_static = [23.0705,12.3719, 7.4679, 5.2282, 3.6264]  # example values
times_dynamic = [17.0767,9.4069,5.0393, 3.3183, 2.8086] 
speedup = [times_static[0] / t for t in times_static]

plt.figure(figsize=(8,6))
plt.plot(workers, speedup, marker='o', linestyle='-')
plt.xlabel("Number of Workers")
plt.ylabel("Speed-Up")
plt.title("Speed-Up vs. Number of Workers")
plt.grid(True)

# Save the plot as an image (PNG format)
plt.savefig("speedup_plot_dynamic.png", dpi=300, bbox_inches='tight')

plt.show()
