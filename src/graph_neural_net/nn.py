import argparse
import collections
import graph_nets as gn
import json
import math
import numpy as np
import os
import pickle
import random
import sonnet as snt
import tensorflow as tf
import time
import tqdm

_DIRNAME = os.path.abspath(os.path.dirname(__file__))

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

    labels = []
    offset = 0
    for g_idx, g in enumerate(graphs):
        g_labels = {}
        for l in g['labels']:
            g_labels[node_index_map[(g_idx, l['node'])] - offset] = label_index_map[l['label']]
        offset += n_nodes[g_idx]
        labels.append(g_labels)

    gtuple = gn.graphs.GraphsTuple(
        tf.constant(nodes, dtype=tf.float64),
        tf.constant(edges, dtype=tf.float64),
        tf.constant(receivers, dtype=tf.int32),
        tf.constant(senders, dtype=tf.int32),
        None,
        tf.constant(n_nodes, dtype=tf.int32),
        tf.constant(n_edges, dtype=tf.int32)
    )
    print(nodes)
    print(edges)
    print(receivers)
    print(senders)   
    print(labels)
    sys.exit(0)

    return gtuple, labels, index_maps

def train(train_graph, train_labels, test_graph, test_labels, num_labels,
          nepoch=10, batch_size=16):

    NODE_LATENT_SIZE = 128
    NODE_HIDDEN_SIZE = 256
    EDGE_LATENT_SIZE = 128
    EDGE_HIDDEN_SIZE = 256
    N_ITER = 10

    (n_nodes, node_features_len) = train_graph.nodes.shape
    (n_edges, edge_features_len) = train_graph.edges.shape
    n_subgraphs = train_graph.n_node.shape[0]

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
        node_model_fn=lambda: snt.nets.MLP([NODE_LATENT_SIZE, num_labels]),
    )

    test_graph = gn.utils_tf.make_runnable_in_session(test_graph)

    optimizer = tf.train.AdamOptimizer(1e-5)

    with tf.Session() as sess:
        try:
            sess.run(tf.global_variables_initializer())

            for epno in tqdm.trange(nepoch):
                subgraphs_and_labels = [
                    (gn.utils_tf.get_graph(train_graph, i), train_labels[i])
                    for i in range(n_subgraphs)
                ]
                random.shuffle(subgraphs_and_labels)
                graphs, labels = zip(*subgraphs_and_labels)

                total_loss = 0
                total_corr = 0
                n_preds = 0

                for i in tqdm.trange(0, n_subgraphs, batch_size):
                    subgraph = gn.utils_tf.concat(graphs[i:i + batch_size], 0)
                    subgraph = gn.utils_tf.make_runnable_in_session(subgraph)

                    sublabels = labels[i:i+batch_size]
                    loss_idxs = []
                    labels_arr = []

                    offset = 0
                    for j, sublab in enumerate(sublabels):
                        for node_idx, label in enumerate(sublab.items()):
                            loss_idxs.append(node_idx + offset)
                            labels_arr.append(1)

                        offset += subgraph.n_node[j]

                    subgraph = encoder_module(subgraph)
                    for _ in range(N_ITER):
                        subgraph = latent_module(subgraph)
                    subgraph = decoder_module(subgraph)

                    preds = tf.gather(subgraph.nodes, loss_idxs)
                    loss = tf.losses.sparse_softmax_cross_entropy(
                        labels_arr,
                        preds,
                    )

                    sess.run(optimizer.minimize(loss))

                    total_loss += sess.run(loss)
                    total_corr += sess.run(tf.reduce_sum(tf.equal(tf.argmax(preds, 1), labels_arr)))
                    n_pred += len(loss_idxs)

                tqdm.tqdm.twrite('Train: mean loss: {:.2f}, Mean accuracy: {:.2f}'.format(
                    total_loss / n_preds,
                    total_corr / n_preds,
                ))

        except KeyboardInterrupt:
            print('Caught SIGINT!')
            dname = 'graph_{}'.format(time.strftime('%Y-%m-%d-%H:%M:%S'))
            dname = os.path.join(_DIRNAME, 'models', dname)
            os.makedirs(dname, exist_ok=True)
            saver = tf.train.Saver([
                encoder_module.trainable_variables,
                latent_module.trainable_variables,
                decoder_module.trainable_variables,
            ])
            saver.save(sess, os.path.join(dname, 'model'))
            print('Saved model to {}'.format(dname))


def main():
    parser = argparse.ArgumentParser(description='Train and test using the Deepmind GNN framework.')
    parser.add_argument('graphs', nargs='+', help='A graph file to process')
    args = parser.parse_args()

    graphs = []
    for graph_f in args.graphs:
        with open(graph_f) as f:
            graphs.append(json.load(f))

    graph_tuple, labels, index_maps = graphs_json_to_graph_tuple_and_labels(graphs)
    n_labels = len(index_maps.label_index_map)
    train(graph_tuple, labels, graph_tuple, labels, n_labels)


if __name__ == '__main__':
    main()
