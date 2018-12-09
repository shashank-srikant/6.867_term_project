#!/usr/bin/env python3

import argparse
import igraph
from igraph import *
import json
import plotly.graph_objs as go
import plotly.offline as po
import sys
from matplotlib import pyplot as plt

def colorize(arr, name='viridis'):
    cmap = plt.get_cmap(name)
    idxmap = {}
    for i in arr:
        idxmap[i] = len(idxmap)
    return [list(cmap(idxmap[i] / len(idxmap))) for i in arr]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file')
    parser.add_argument('--key-label', default=1, type=int)
    parser.add_argument('--layout', default='rt', help='for big graphs, try rt_circular')
    args = parser.parse_args()

    with open(args.file) as f:
        json_f = json.load(f)
        nodes = json_f['nodes']
        edges = json_f['edges']

    G = Graph()
    for n in nodes:
        G.add_vertex(str(n['id']))

    if all('token' in n for n in nodes):
        G.vs["label"] = [n['token'] for n in nodes]

    G.vs['color'] = colorize([n['ast_type'] for n in nodes], 'viridis')
    for c in G.vs['color']:
        c[-1] = 0.4

    def proc_edges(es):
        return [(str(e['src']), str(e['dst'])) for e in es]
    def edge_of_label(lab):
        return list(e for e in edges if e['edge_type'] == lab)

    key_label = args.key_label
    rest_labels = list(set(e['edge_type'] for e in edges) - {key_label})

    cs = [key_label] * len(edge_of_label(key_label))
    for rl in rest_labels:
        cs += [rl] * len(edge_of_label(rl))

    G.add_edges(proc_edges(edge_of_label(key_label)))
    lay = G.layout(args.layout)
    for rl in rest_labels:
        G.add_edges(proc_edges(edge_of_label(rl)))
    G.es['color'] = colorize(cs, 'viridis')
    plot(G, layout=lay, vertex_size=40, margin=40)

if __name__ == '__main__':
    main()
