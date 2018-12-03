import graph_nets as gn
import numpy as np

def weights_and_labels_arr(graph, labels):
    weights_arr = np.zeros(graph.nodes.shape[0], dtype=np.float32)
    labels_arr = np.zeros(graph.nodes.shape[0], dtype=np.int64)

    offset = 0
    for j, sublab in enumerate(labels):
        for node_idx, label in sublab.items():
            weights_arr[node_idx + offset] = 1
            labels_arr[node_idx + offset] = label

        offset += graph.n_node[j]

    return weights_arr, labels_arr

def concat_np(graphs):
    n_node = np.concatenate([g.n_node for g in graphs])
    n_edge = np.concatenate([g.n_edge for g in graphs])
    nodes = np.concatenate([g.nodes for g in graphs])
    edges = np.concatenate([g.edges for g in graphs])
    globals = np.concatenate([g.globals for g in graphs])

    receivers = []
    senders = []

    goffset = 0
    for graph in graphs:
        receivers.append(graph.receivers + goffset)
        senders.append(graph.senders + goffset)
        goffset += graph.nodes.shape[0]

    receivers = np.concatenate(receivers)
    senders = np.concatenate(senders)

    return gn.graphs.GraphsTuple(nodes, edges, receivers, senders, globals, n_node, n_edge)

def split_np(graphs):
    n_graphs = graphs.n_node.shape[0]
    return [gn.utils_np.get_graph(graphs, i) for i in range(n_graphs)]
