import graph_nets as gn
import gn_utils
import os
import random
import sonnet as snt
import tensorflow as tf
import time
from tqdm import tqdm, trange
import utils

NODE_LATENT_SIZE = 128
NODE_HIDDEN_SIZE = 256
EDGE_LATENT_SIZE = 128
EDGE_HIDDEN_SIZE = 256

REPORT_FREQ_SECS = 600

class Trainer:
    def __init__(self, train_graphs, train_labels, test_graphs, test_labels,
                 *,
                 niter=10, batch_size=16,
    ):
        self.train_graphs = train_graphs
        self.train_labels = train_labels
        self.test_graphs = test_graphs
        self.test_labels = test_labels

        self.niter = niter
        self.batch_size = batch_size

        # grab a random representative graph of the node/edge feature lengths
        rep_graph = train_graphs[0]
        node_features_len = rep_graph.nodes.shape[1]
        edge_features_len = rep_graph.edges.shape[1]

        num_labels = 1 + max(l for lab_dict in train_labels for l in lab_dict.values())

        self.encoder_module = gn.modules.InteractionNetwork(
            edge_model_fn=lambda: snt.nets.MLP([edge_features_len, EDGE_LATENT_SIZE]),
            node_model_fn=lambda: snt.nets.MLP([node_features_len, NODE_LATENT_SIZE]),
        )
        self.latent_module = gn.modules.InteractionNetwork(
            edge_model_fn=lambda: snt.nets.MLP([EDGE_LATENT_SIZE, EDGE_HIDDEN_SIZE, EDGE_LATENT_SIZE]),
            node_model_fn=lambda: snt.nets.MLP([NODE_LATENT_SIZE, NODE_HIDDEN_SIZE, NODE_LATENT_SIZE]),
        )
        self.decoder_module = gn.modules.InteractionNetwork(
            edge_model_fn=lambda: snt.nets.MLP([EDGE_LATENT_SIZE, EDGE_LATENT_SIZE]),
            node_model_fn=lambda: snt.nets.MLP([NODE_LATENT_SIZE, num_labels]),
        )

        self.placeholder_graph, self.placeholder_weights, self.placeholder_labels, self.weighted_correct, self.weighted_loss = self._loss_placeholder()
        self.batched_test_graphs, self.batched_test_labels = self._batch_graphs(test_graphs, test_labels)

        self.saver = tf.train.Saver(
            list(self.encoder_module.get_variables()) +
            list(self.latent_module.get_variables()) +
            list(self.decoder_module.get_variables())
        )

    def _loss_placeholder(self):
        # construct placeholder from an arbitrary graph in the dataset to get correct shapes
        placeholder_graph = gn.utils_tf._placeholders_from_graphs_tuple(self.train_graphs[0], True)
        n_nodes_placeholder = placeholder_graph.nodes.shape[0]
        weights = tf.placeholder(tf.float32, shape=[n_nodes_placeholder])
        labels = tf.placeholder(tf.int64, shape=[n_nodes_placeholder])

        graph = self.encoder_module(placeholder_graph)
        for _ in range(self.niter):
            graph = self.latent_module(graph)
        graph = self.decoder_module(graph)

        pred = tf.argmax(graph.nodes, 1)
        pred_correct = tf.equal(pred, labels)
        corr = tf.reduce_sum(weights * tf.cast(pred_correct, tf.float32))

        return placeholder_graph, weights, labels, corr, tf.losses.sparse_softmax_cross_entropy(
            labels,
            graph.nodes,
            weights,
        )

    def _batch_graphs(self, graphs, labels):
        batched_graphs = []
        batched_labels = []
        for i in range(0, len(graphs), self.batch_size):
            batched_graphs.append(gn_utils.concat_np(graphs[i:i+self.batch_size]))
            batched_labels.append(labels[i:i+self.batch_size])

        return batched_graphs, batched_labels

    def _process_batches(self, sess, batched_graphs, batched_labels, train_function=None):
        total_weight = 0
        total_loss = 0
        total_correct = 0

        to_run = [self.weighted_correct, self.weighted_loss]
        if train_function:
            to_run.append(train_function)

        for graph, labels in zip(batched_graphs, batched_labels):
            weights_arr, labels_arr = gn_utils.weights_and_labels_arr(graph, labels)
            feed_dict = gn.utils_tf.get_feed_dict(self.placeholder_graph, graph)
            feed_dict[self.placeholder_weights] = weights_arr
            feed_dict[self.placeholder_labels] = labels_arr

            correct, loss = sess.run(to_run, feed_dict)[:2]

            total_weight += int(weights_arr.sum())
            total_loss += loss
            total_correct += correct

        return total_weight, total_loss, total_correct

    def save(self, sess):
        tqdm.write('Saving model...')
        dname = 'graph_{}'.format(utils.get_time_str())
        dname = os.path.join(utils.DIRNAME, 'models', dname)
        os.makedirs(dname, exist_ok=True)
        self.saver.save(sess, os.path.join(dname, 'model'))
        tqdm.write('Saved model to {}'.format(dname))

    def _train(self,
               sess, train_function,
               nepoch=1000,
               report_distr=False, label_name_map=None
    ):

        def fmt_report_str(name, weight, loss, correct):
            return '{}: loss: {:.2f}, Accuracy: {:.2f} ({}/{})'.format(
                name,
                loss,
                correct / weight,
                correct, weight,
            )

        last_report_time = 0

        test_weight, test_loss, test_correct = self._process_batches(sess, self.batched_test_graphs, self.batched_test_labels)
        tqdm.write(fmt_report_str('Test', test_weight, test_loss, test_correct))

        for epno in trange(nepoch, desc='Epoch'):
            graphs_and_labels = list(zip(self.train_graphs, self.train_labels))
            random.shuffle(graphs_and_labels)
            graphs, labels = zip(*graphs_and_labels)
            batched_train_graphs, batched_train_labels = self._batch_graphs(graphs, labels)

            train_weight, train_loss, train_correct = self._process_batches(sess, batched_train_graphs, batched_train_labels, train_function)
            if (time.time() - last_report_time) > REPORT_FREQ_SECS == 0:
                last_report_time = time.time()

                tqdm.write(fmt_report_str('Train', train_weight, train_loss, train_correct))

                test_weight, test_loss, test_correct = self._process_batches(sess, self.batched_test_graphs, self.batched_test_labels)
                tqdm.write(fmt_report_str('Test', test_weight, test_loss, test_correct))

                self.save(sess)
        test_weight, test_loss, test_correct = self._process_batches(sess, self.batched_test_graphs, self.batched_test_labels)
        tqdm.write(fmt_report_str('Test', test_weight, test_loss, test_correct))

    def train(self,
              stepsize=1e-6, nepoch=1000,
              load_model=None,
              report_distr=False, label_name_map=None
    ):
        optimizer = tf.train.AdamOptimizer(stepsize)
        train_function = optimizer.minimize(self.weighted_loss)

        with tf.Session() as sess:
            sess.run(tf.global_variables_initializer())

            if load_model:
                self.saver.restore(sess, os.path.join(load_model, 'model'))

            try:
                self._train(
                    sess, train_function,
                    nepoch=nepoch,
                    report_distr=report_distr, label_name_map=label_name_map
                )
            except KeyboardInterrupt:
                print('Caught SIGINT!')
            finally:
                self.save(sess)
