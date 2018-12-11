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

def histify(arr):
    arr = np.array(arr, dtype=np.float32)
    hist, bin_edges = np.histogram(arr)
    hist = hist.astype(np.float32)
    hist /= np.sum(hist)
    hist = np.array([0] + list(hist))
    hist = np.cumsum(hist)
    return hist, bin_edges

xlabel = 'Average Node Degree'
hist, bin_edges = histify(avg_deg)
fig = plt.figure()
ax = plt.gca()
ax.plot(bin_edges, hist)
ax.set_xlabel(xlabel)
ax.set_ylabel('Cumulative Density')
ax.set_title('CDF of {} Across Files'.format(xlabel))


fig = plt.figure()
ax = plt.gca()
apl_hist, apl_bin_edges = histify(avg_path_len)
d_hist, d_bin_edges = histify(diam)
ax.plot(d_bin_edges, d_hist, label='Max of All Paths')
ax.plot(list(apl_bin_edges) + [d_bin_edges[-1]], list(apl_hist) + [1], label='Average of All Paths')
ax.legend()
ax.set_xlabel('Path Length')
ax.set_ylabel('Cumulative Density')
ax.set_title('CDF of Diameter and Average Path Length Across Files'.format(xlabel))

plt.show()
