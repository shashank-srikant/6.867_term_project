#!/usr/bin/env python3

from matplotlib import pyplot as plt
import numpy as np
import sys

avg_deg = []
avg_path_len = []
diam = []

with open(sys.argv[1], 'r') as f:
    for line in f.readlines():
        deg, p, di = line.split()
        avg_deg.append(float(deg))
        avg_path_len.append(float(p))
        diam.append(int(di))

def plot(arr, xlabel):
    arr = np.array(arr, dtype=np.float32)
    hist, bin_edges = np.histogram(arr)
    hist = hist.astype(np.float32)
    hist /= np.sum(hist)
    hist = np.array([0] + list(hist))
    hist = np.cumsum(hist)
    fig = plt.figure()
    ax = plt.gca()
    ax.plot(bin_edges, hist)
    ax.set_xlabel(xlabel)
    ax.set_ylabel('Cumulative Density')
    ax.set_title('CDF of {} Across Random Subset of Files'.format(xlabel))

plot(avg_deg, 'Average Node Degree')
plot(avg_path_len, 'Average Path Length')
plot(diam, 'Graph Diameter')

plt.show()
