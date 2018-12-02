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
    senders = np.empty(sum(n_edges), dtype=np.int64)
    receivers = np.empty(sum(n_edges), dtype=np.int64)
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
        nodes,
        edges,
        receivers,
        senders,
        np.zeros([len(graphs), 0], dtype=np.float64),
        n_nodes,
        n_edges,
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


def train(train_graphs, train_labels, test_graphs, test_labels, num_labels,
          nepoch=1000, batch_size=16, report_ep=10):
    NODE_LATENT_SIZE = 128
    NODE_HIDDEN_SIZE = 256
    EDGE_LATENT_SIZE = 128
    EDGE_HIDDEN_SIZE = 256
    N_ITER = 10

    node_features_len = train_graphs[0].nodes.shape[1]
    edge_features_len = train_graphs[0].edges.shape[1]
    n_train_graphs = len(train_graphs)

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
        g = gn.utils_tf._placeholders_from_graphs_tuple(train_graphs[0], True)
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

            test_graphs_and_labels = [
                (
                    concat_np(test_graphs[i:i+batch_size]),
                    test_labels[i:i+batch_size],
                )
                for i in tqdm.trange(0, len(test_graphs), batch_size, desc='Batching test graphs')
            ]

            for epno in tqdm.trange(nepoch, desc='Epoch'):
                subgraphs_and_labels = list(zip(train_graphs, train_labels))
                random.shuffle(subgraphs_and_labels)
                graphs, labels = zip(*subgraphs_and_labels)

                total_loss = 0
                total_correct = 0
                n_preds = 0

                subgraphs = [
                    concat_np(graphs[i:i + batch_size])
                    for i in tqdm.trange(0, n_train_graphs, batch_size, desc='Batching train graphs')
                ]

                for i, subgraph in zip(tqdm.trange(0, n_train_graphs, batch_size, desc='Batch'), subgraphs):
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

                    test_sum_n_preds = 0
                    test_sum_loss = 0
                    test_sum_correct = 0
                    for (m_test_graph, m_test_labels) in test_graphs_and_labels:
                        weights_arr, labels_arr = weights_and_labels_arr(m_test_graph, m_test_labels)
                        feed_dict = gn.utils_tf.get_feed_dict(plh_g, m_test_graph)
                        feed_dict[plh_w] = weights_arr
                        feed_dict[plh_l] = labels_arr

                        m_loss, m_correct = sess.run([loss, corr], feed_dict)

                        test_sum_n_preds += int(weights_arr.sum())
                        test_sum_loss += m_loss
                        test_sum_correct += int(m_correct)

                    tqdm.tqdm.write(
                        'Test: mean loss: {:.2f}, Accuracy: {:.2f} ({}/{})'.format(
                            test_sum_loss / test_sum_n_preds,
                            test_sum_correct / test_sum_n_preds,
                            test_sum_correct, test_sum_n_preds,
                        )
                    )

        except KeyboardInterrupt:
            print('Caught SIGINT!')
        finally:
            print('Saving model...')
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
    parser.add_argument('--file', '-f', nargs='+', help='Individual graph files to process', default=[])
    parser.add_argument('--dir', '--directory', '-d', nargs='+', help='Individual project directories to process', default=[])
    parser.add_argument('--project', '-p', nargs='+', help='Directories containing a list of directories (equivalent to --dir PROJECT/*)', default=[])
    args = parser.parse_args()

    def collect_directory(directory):
        files = []
        for (root, _, fnames) in os.walk(directory):
            for fname in fnames:
                if fname.endswith('.json'):
                    files.append(os.path.join(root, fname))
        return (directory, files)

    # list of (dir name, [graph file]) tuples
    project_graph_files = []

    project_graph_files.extend(map(lambda x: (x, [x]), args.file))

    for directory in args.dir:
        project_graph_files.append(collect_directory(directory))

    for project in args.project:
        for directory in os.listdir(project):
            project_graph_files.append(collect_directory(os.path.join(project, directory)))

    project_graph_json = []
    split_index_map = [0]
    split_idx_cumsum = 0
    for (_, files) in project_graph_files:
        jsons = []
        for fname in files:
            with open(fname) as f:
                jsons.append(json.load(f))
        project_graph_json.append(jsons)
        split_idx_cumsum += len(files)
        split_index_map.append(split_idx_cumsum)

    all_graphs = [graph for graphs in project_graph_json for graph in graphs]

    graph_tuple, labels, index_maps = graphs_json_to_graph_tuple_and_labels(all_graphs)
    n_labels = len(index_maps.label_index_map)

    def graphs_labs_of_underlying_idxs(all_idxs):
        graphs = [gn.utils_np.get_graph(graph_tuple, i) for i in all_idxs]
        labs = [labels[i] for i in all_idxs]
        return concat_np(graphs), labs

    dir_graphs_labs = []
    for idx in range(len(split_index_map) - 1):
        dir_graphs_labs.append(graphs_labs_of_underlying_idxs(list(range(split_index_map[idx], split_index_map[idx + 1]))))

    split_perc = 0.8
    idxs = list(range(len(dir_graphs_labs)))
    random.shuffle(idxs)
    n_train = math.floor(split_perc * len(idxs))

    def graphs_labs_of_project_idxs(idxs):
        graphs = []
        labels = []
        for idx in idxs:
            graph, labs = dir_graphs_labs[idx]
            for j in range(len(labs)):
                graphs.append(gn.utils_np.get_graph(graph, j))
                labels.append(labs[j])

        return graphs, labels

    train_graphs, train_labels = graphs_labs_of_project_idxs(idxs[:n_train])
    test_graphs, test_labels = graphs_labs_of_project_idxs(idxs[n_train:])

    print('train set ({} nodes, {} labels): =====\n{}\n====='.format(
        sum(sum(g.n_node) for g in train_graphs),
        sum(map(len, train_labels)),
        '\n'.join(project_graph_files[i][0] for i in idxs[:n_train])
    ))

    print('test set ({} nodes, {} labels): =====\n{}\n====='.format(
        sum(sum(g.n_node) for g in train_graphs),
        sum(map(len, test_labels)),
        '\n'.join(project_graph_files[i][0] for i in idxs[n_train:])
    ))

    train(train_graphs, train_labels, test_graphs, test_labels, n_labels)


if __name__ == '__main__':
    main()
