#!/usr/bin/env python3

import argparse
import igraph
from igraph import *
import json
import plotly.graph_objs as go
import plotly.offline as po
import sys
from matplotlib import pyplot as plt
from igraph.drawing.text import TextDrawer
from igraph.drawing.shapes import RectangleDrawer
import cairo

def colorize(arr, name='viridis'):
    cmap = plt.get_cmap(name)
    idxmap = {}
    for i in arr:
        idxmap[i] = len(idxmap)

    float_of = lambda i: (idxmap[i] / len(idxmap))
    return [list(cmap(float_of(i))) for i in arr]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file')
    parser.add_argument('--key-label', default='AstChild', type=str)
    parser.add_argument('--layout', default='rt', help='for big graphs, try rt_circular')
    parser.add_argument('--node-color', default='viridis')
    parser.add_argument('--edge-color', default='viridis')
    args = parser.parse_args()

    with open(args.file) as f:
        json_f = json.load(f)
        nodes = json_f['nodes']
        edges = json_f['edges']

    G = Graph()
    dG = Graph(directed=True)
    for n in nodes:
        G.add_vertex(str(n['id']))
        dG.add_vertex(str(n['id']))

    if all('token' in n for n in nodes):
        dG.vs["label"] = [n['token'] for n in nodes]

    dG.vs['color'] = colorize([n['ast_type'] for n in nodes], args.node_color)
    for c in dG.vs['color']:
        c[-1] = 0.4

    def proc_edges(es):
        return [(str(e['src']), str(e['dst'])) for e in es]
    def edge_of_label(lab):
        return list(e for e in edges if e['edge_type'] == lab)

    key_label = args.key_label
    rest_labels = list(set(e['edge_type'] for e in edges) - {key_label})

    cidxmap = {key_label: 0}
    cs = [key_label] * len(edge_of_label(key_label))
    for rl in rest_labels:
        cidxmap[rl] = len(cs)
        cs += [rl] * len(edge_of_label(rl))

    G.add_edges(proc_edges(edge_of_label(key_label)))
    dG.add_edges(proc_edges(edge_of_label(key_label)))
    lay = G.layout(args.layout)
    for rl in rest_labels:
        dG.add_edges(proc_edges(edge_of_label(rl)))

    dG.es['color'] = colorize(cs, args.edge_color)

    plot = Plot("plot.png", bbox=(800, 670), background="white")

    plot.add(dG, layout=lay, vertex_size=40, bbox=(40, 70, 580, 630))
    plot.redraw()

    # Grab the surface, construct a drawing context and a TextDrawer
    ctx = cairo.Context(plot.surface)
    ctx.set_font_size(20)

    drawer = TextDrawer(ctx, "Legend", halign=TextDrawer.CENTER)
    drawer.draw_at(680, 40, width=40)

    ctx.rectangle(620, 20, 160, 125)
    ctx.rectangle(620, 48, 160, 1)
    ctx.stroke()
    ctx.set_source_rgb(0., 0., 0.)

    ctx.set_font_size(18)
    y = 40 + 30
    for lab in [key_label] + rest_labels:
        ctx.set_source_rgb(*dG.es['color'][cidxmap[lab]][:3])
        ctx.rectangle(640, y - 8, 20, 1)
        ctx.stroke()
        ctx.set_source_rgb(0., 0., 0.)
        drawer = TextDrawer(ctx, str(lab), halign=TextDrawer.CENTER)
        drawer.draw_at(700, y, width=40)
        y += 15

    # Save the plot
    plot.save()

if __name__ == '__main__':
    main()
