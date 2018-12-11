#!/usr/bin/env python3

import argparse
from matplotlib import pyplot as plt
import numpy as np

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file')
    parser.add_argument('--title', default='')
    parser.add_argument('--xlabel', default='')
    parser.add_argument('--ylabel', default='')
    parser.add_argument('--horiz', type=float, nargs='+', default=[])
    parser.add_argument('--vert', type=float, nargs='+', default=[])
    args = parser.parse_args()

    with open(args.file, 'r') as f:
        hist = np.array(list(map(int, f.readlines()[0].strip().split())), dtype=np.float64)

    density = hist / np.sum(hist)
    cden = np.cumsum(density)
    plt.plot([0] + list(np.arange(1, len(density) + 1)), [0] + list(cden))
    plt.title(args.title)
    plt.xlabel(args.xlabel)
    plt.ylabel(args.ylabel)

    xlim = plt.xlim()
    ylim = plt.ylim()

    for vert in args.vert:
        plt.plot([vert, vert], ylim)

    for horiz in args.horiz:
        plt.plot(xlim, [horiz, horiz])

    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.show()

if __name__ == '__main__':
    main()
