# p values to histogram

import matplotlib.pyplot as plt

def plot_histogram(pvalues):
    plt.figure(figsize=(10, 5))
    plt.hist(pvalues, bins=[i * 0.001+0.000000000001 for i in range(51)], edgecolor='black')
    plt.title("P Value Distribution (Bin width = 0.001)")
    plt.xlabel("P Value")
    plt.ylabel("No. of P Values")
    plt.tight_layout()
    plt.show()
    