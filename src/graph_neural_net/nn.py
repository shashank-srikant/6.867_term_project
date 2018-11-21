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
        tf.zeros([len(graphs), 0], dtype=np.float64),
        tf.constant(n_nodes, dtype=tf.int32),
        tf.constant(n_edges, dtype=tf.int32)
    )

    return gtuple, labels, index_maps

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

def train(train_graph, train_labels, test_graph, test_labels, num_labels,
          nepoch=1000, batch_size=16, report_ep=10):

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

    def placeheld_loss():
        g = gn.utils_tf._placeholders_from_graphs_tuple(train_graph, True)
        weights = tf.placeholder(tf.float32, shape=[g.nodes.shape[0]])
        labs = tf.placeholder(tf.int64, shape=[g.nodes.shape[0]])

        subgraph = encoder_module(g)
        for _ in range(N_ITER):
            subgraph = latent_module(subgraph)
        subgraph = decoder_module(subgraph)

        corr = tf.reduce_sum(tf.cast(tf.equal(tf.argmax(subgraph.nodes, 1), labs),
                                     tf.float32) * weights)

        return g, weights, labs, corr, tf.losses.sparse_softmax_cross_entropy(
            labs,
            subgraph.nodes,
            weights,
        )

    plh_g, plh_w, plh_l, corr, loss = placeheld_loss()
    optimizer = tf.train.AdamOptimizer(1e-4)
    train_fun = optimizer.minimize(loss)

    with tf.Session() as sess:
        try:
            sess.run(tf.global_variables_initializer())

            test_graph = gn.graphs.GraphsTuple(*map(sess.run, test_graph))

            for epno in tqdm.trange(nepoch):
                subgraphs_and_labels = [
                    (gn.utils_tf.get_graph(train_graph, i), train_labels[i])
                    for i in range(n_subgraphs)
                ]
                random.shuffle(subgraphs_and_labels)
                graphs, labels = zip(*subgraphs_and_labels)

                total_loss = 0
                total_correct = 0
                n_preds = 0

                subgraphs = [
                    gn.utils_tf.concat(graphs[i:i + batch_size], 0)
                    for i in range(0, n_subgraphs, batch_size)
                ]
                subgraphs = [
                    gn.graphs.GraphsTuple(*map(sess.run, subgraph))
                    for subgraph in subgraphs
                ]

                for i, subgraph in zip(tqdm.trange(0, n_subgraphs, batch_size), subgraphs):
                    sublabels = labels[i:i+batch_size]

                    weights_arr, labels_arr = weights_and_labels_arr(subgraph, sublabels)
                    feed_dict = gn.utils_tf.get_feed_dict(plh_g, subgraph)
                    feed_dict[plh_w] = weights_arr
                    feed_dict[plh_l] = labels_arr


                    if epno % report_ep == 0:
                        m_loss, m_correct, _ = sess.run([loss, corr, train_fun], feed_dict)
                        n_preds += int(weights_arr.sum())
                        total_loss += m_loss
                        total_correct += m_correct
                    else:
                        sess.run(train_fun, feed_dict)

                if epno % report_ep == 0:
                    tqdm.tqdm.write(
                        'Train: mean loss: {:.2f}, Accuracy: {:.2f} ({}/{})'.format(
                            total_loss / n_preds,
                            total_correct / n_preds,
                            int(total_correct), n_preds,
                        )
                    )

                    weights_arr, labels_arr = weights_and_labels_arr(test_graph, test_labels)
                    feed_dict = gn.utils_tf.get_feed_dict(plh_g, test_graph)
                    feed_dict[plh_w] = weights_arr
                    feed_dict[plh_l] = labels_arr

                    m_loss, m_correct = sess.run([loss, corr], feed_dict)
                    m_n_preds = int(weights_arr.sum())

                    tqdm.tqdm.write(
                        'Test: mean loss: {:.2f}, Accuracy: {:.2f} ({}/{})'.format(
                            m_loss / m_n_preds,
                            m_correct / m_n_preds,
                            int(m_correct), m_n_preds,
                        )
                    )


        except KeyboardInterrupt:
            print('Caught SIGINT!')
        finally:
            dname = 'graph_{}'.format(time.strftime('%Y-%m-%d-%H:%M:%S'))
            dname = os.path.join(_DIRNAME, 'models', dname)
            os.makedirs(dname, exist_ok=True)
            saver = tf.train.Saver(
                list(encoder_module.get_variables()) +
                list(latent_module.get_variables()) +
                list(decoder_module.get_variables())
            )
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
