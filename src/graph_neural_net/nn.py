import argparse
import collections
import graph_nets as gn
import json
import numpy as np
import tensorflow as tf
import sonnet as snt
import pprint as pp

IndexMaps = collections.namedtuple('IndexMaps', (
    'ast_type_index_map',
    'edge_type_index_map',
    'label_index_map',
))

def construct_index_maps(graphs):
    ast_type_index_map = {}
    edge_type_index_map = {}
    label_index_map = {}

    for g in graphs:
        for n in g['nodes']:
            if n['ast_type'] not in ast_type_index_map:
                ast_type_index_map[n['ast_type']] = len(ast_type_index_map)
        for e in g['edges']:
            if e['edge_type'] not in edge_type_index_map:
                edge_type_index_map[e['edge_type']] = len(edge_type_index_map)
        for l in g['labels']:
            if l['label'] not in label_index_map:
                label_index_map[l['label']] = len(label_index_map)

    return IndexMaps(ast_type_index_map, edge_type_index_map, label_index_map)

def graphs_json_to_graph_tuple_and_labels(graphs, index_maps=None):
    # TODO unks
    if index_maps is None:
        index_maps = construct_index_maps(graphs)

    ast_type_index_map, edge_type_index_map, label_index_map = index_maps

    node_index_map = {}

    n_nodes = np.array(list(len(g['nodes']) for g in graphs))
    nodes = np.zeros((sum(n_nodes), len(ast_type_index_map)))

    for g_idx, g in enumerate(graphs):
        for n in g['nodes']:
            nid = n['id']
            if (g_idx, nid) in node_index_map:
                raise ValueError('Duplicate node in graph {}: id {}'.format(g_idx + 1, nid))
            nidx = len(node_index_map)
            node_index_map[(g_idx, nid)] = nidx
            nodes[nidx, ast_type_index_map[n['ast_type']]] = 1

    n_edges = np.array(list(len(g['edges']) for g in graphs))
    senders = np.empty(sum(n_edges))
    receivers = np.empty(sum(n_edges))
    edges = np.zeros((sum(n_edges), len(edge_type_index_map)))

    i = 0
    for g_idx, g in enumerate(graphs):
        for e in g['edges']:
            edges[i, edge_type_index_map[e['edge_type']]] = 1
            senders[i] = node_index_map[(g_idx, e['src'])]
            receivers[i] = node_index_map[(g_idx, e['dst'])]

            i += 1

    labels = {}
    for g_idx, g in enumerate(graphs):
        for l in g['labels']:
            labels[node_index_map[(g_idx, l['node'])]] = label_index_map[l['label']]

    gtuple = gn.graphs.GraphsTuple(
        tf.constant(nodes, dtype=tf.float64),
        tf.constant(edges, dtype=tf.float64),
        tf.constant(receivers, dtype=tf.int64),
        tf.constant(senders, dtype=tf.int64),
        None,
        tf.constant(n_nodes, dtype=tf.int64),
        tf.constant(n_edges, dtype=tf.int64)
    )
    print(nodes)
    print(edges)
    print(receivers)
    print(senders)   
    print(labels)
    sys.exit(0)

    return gtuple, labels, index_maps

def train(graph, labels, label_index_map, niter=10):
    NODE_LATENT_SIZE = 128
    NODE_HIDDEN_SIZE = 256
    EDGE_LATENT_SIZE = 128
    EDGE_HIDDEN_SIZE = 256
    (n_nodes, node_features_len) = graph.nodes.shape
    (n_edges, edge_features_len) = graph.edges.shape

    encoder_module = gn.modules.InteractionNetwork(
        edge_model_fn=lambda: snt.nets.MLP([edge_features_len, EDGE_LATENT_SIZE]),
        node_model_fn=lambda: snt.nets.MLP([node_features_len, NODE_LATENT_SIZE]),
    )
    latent_module = gn.modules.InteractionNetwork(
        edge_model_fn=lambda: snt.nets.MLP([EDGE_LATENT_SIZE, EDGE_HIDDEN_SIZE, EDGE_LATENT_SIZE]),
        node_model_fn=lambda: snt.nets.MLP([NODE_LATENT_SIZE, NODE_HIDDEN_SIZE, NODE_LATENT_SIZE]),
    )
    decoder_module = gn.modules.InteractionNetwork(
        edge_model_fn=lambda: snt.nets.MLP([EDGE_LATENT_SIZE, EDGE_LATENT_SIZE]),
        node_model_fn=lambda: snt.nets.MLP([NODE_LATENT_SIZE, len(label_index_map)]),
    )


    graph = gn.utils_tf.make_runnable_in_session(graph)
    graph = encoder_module(graph)
    for _ in range(niter):
        graph = latent_module(graph)
    graph = decoder_module(graph)

    loss_idxs = []
    labels_arr = np.zeros((len(labels), len(label_index_map)))
    for i, (node_idx, label) in enumerate(labels.items()):
        loss_idxs.append(node_idx)
        labels_arr[i, label_index_map[label]] = 1

    pred_nodes = tf.nn.softmax(graph.nodes)
    loss = tf.reduce_sum(tf.nn.softmax_cross_entropy_with_logits_v2(
        logits=tf.gather(graph.nodes, loss_idxs),
        labels=labels_arr,
    ))

    optimizer = tf.train.AdamOptimizer()
    train_func = optimizer.minimize(loss)

    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        for i in range(100):
            sess.run(train_func)
            print('step: {}, loss: {}'.format(i, sess.run(loss)))


        pred_nodes = sess.run(pred_nodes)

        for (node_idx, label) in labels.items():
            pred = pred_nodes[node_idx]
            print('pred: {}, actual: {}'.format(pred, label))

def main():
    parser = argparse.ArgumentParser(description='Train and test using the Deepmind GNN framework.')
    parser.add_argument('graphs', nargs='+', help='A graph file to process')
    args = parser.parse_args()

    graphs = []
    for graph_f in args.graphs:
        with open(graph_f) as f:
            graphs.append(json.load(f))

    graph_tuple, labels, index_maps = graphs_json_to_graph_tuple_and_labels(graphs)
    train(graph_tuple, labels, index_maps.label_index_map)


if __name__ == '__main__':
    main()
