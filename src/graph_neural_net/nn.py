import graph_nets as gn
import gn_utils
import os
import random
import sonnet as snt
import tensorflow as tf
import time
from tqdm import tqdm, trange
from typing import Any, Dict, List, NamedTuple, Optional, Tuple
import utils

NODE_LATENT_SIZE = 128
NODE_HIDDEN_SIZE = 256
EDGE_LATENT_SIZE = 128
EDGE_HIDDEN_SIZE = 256

REPORT_FREQ_SECS = 600

class LossPlaceholder(NamedTuple):
    placeholder_graph: gn.graphs.GraphTuple
    placeholder_weights: tf.placeholder
    placeholder_labels: tf.placeholder
    correct_vec: tf.Tensor
    weighted_correct: tf.Tensor
    weighted_loss: tf.Tensor

class Trainer:
    def __init__(self,
                 train_graphs: List[gn.graphs.GraphTuple],
                 train_labels: List[Dict[int, int]],
                 test_graphs: List[gn.graphs.GraphTuple],
                 test_labels: List[Dict[int, int]],
                 *,
                 niter: int=10, batch_size: int=16,
    ) -> None:
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

        self.loss_placeholder = self._construct_loss_placeholder()
        self.batched_test_graphs, self.batched_test_labels = self._batch_graphs(test_graphs, test_labels)

        self.saver = tf.train.Saver(
            list(self.encoder_module.get_variables()) +
            list(self.latent_module.get_variables()) +
            list(self.decoder_module.get_variables())
        )

    def _construct_loss_placeholder(self) -> LossPlaceholder:
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
        loss = tf.losses.sparse_softmax_cross_entropy(
            labels,
            graph.nodes,
            weights,
        )

        return LossPlaceholder(
            placeholder_graph=placeholder_graph,
            placeholder_weights=weights,
            placeholder_labels=labels,
            correct_vec=pred_correct,
            weighted_correct=corr,
            weighted_loss=loss,
        )

    def _batch_graphs(self, graphs: List[gn.graphs.GraphTuple], labels: List[Dict[int, int]]) -> Tuple[List[gn.graphs.GraphTuple], List[List[Dict[int, int]]]]:
        batched_graphs = []
        batched_labels = []
        for i in range(0, len(graphs), self.batch_size):
            batched_graphs.append(gn_utils.concat_np(graphs[i:i+self.batch_size]))
            batched_labels.append(labels[i:i+self.batch_size])

        return batched_graphs, batched_labels

    def _process_batches(self, sess: tf.Session,
                         batched_graphs: List[gn.graphs.GraphTuple], batched_labels: List[List[Dict[int, int]]],
                         train_function: Optional[Any]=None) -> Tuple[float, float, float]:
        total_weight = 0
        total_loss = 0
        total_correct = 0

        to_run = [self.loss_placeholder.weighted_correct, self.loss_placeholder.weighted_loss]
        if train_function:
            to_run.append(train_function)

        for graph, labels in zip(batched_graphs, batched_labels):
            weights_arr, labels_arr = gn_utils.weights_and_labels_arr(graph, labels)
            feed_dict = gn.utils_tf.get_feed_dict(self.loss_placeholder.placeholder_graph, graph)
            feed_dict[self.loss_placeholder.placeholder_weights] = weights_arr
            feed_dict[self.loss_placeholder.placeholder_labels] = labels_arr

            correct, loss = sess.run(to_run, feed_dict)[:2]

            total_weight += int(weights_arr.sum())
            total_loss += loss
            total_correct += correct

        return total_weight, total_loss, total_correct

    def save(self, sess: tf.Session) -> None:
        tqdm.write('Saving model...')
        dname = 'graph_{}'.format(utils.get_time_str())
        dname = os.path.join(utils.DIRNAME, 'models', dname)
        os.makedirs(dname, exist_ok=True)
        self.saver.save(sess, os.path.join(dname, 'model'))
        tqdm.write('Saved model to {}'.format(dname))

    def _train(self,
               sess: tf.Session, train_function: Any,
               nepoch: int=1000,
               report_distr: bool=False, label_name_map: Optional[Dict[int, str]]=None
    ) -> None:

        def fmt_report_str(name, weight, loss, correct):
            return '{}: loss: {:.2f}, Accuracy: {:.2f} ({}/{})'.format(
                name,
                loss,
                correct / weight,
                correct, weight,
            )

        def report_test_loss():
            test_weight, test_loss, test_correct = self._process_batches(sess, self.batched_test_graphs, self.batched_test_labels)
            tqdm.write(fmt_report_str('Test', test_weight, test_loss, test_correct))

        last_report_time: float = 0

        for epno in trange(nepoch, desc='Epoch'):
            graphs_and_labels = list(zip(self.train_graphs, self.train_labels))
            random.shuffle(graphs_and_labels)
            graphs, labels = zip(*graphs_and_labels)
            batched_train_graphs, batched_train_labels = self._batch_graphs(graphs, labels)

            train_weight, train_loss, train_correct = self._process_batches(sess, batched_train_graphs, batched_train_labels, train_function)
            if (time.time() - last_report_time) > REPORT_FREQ_SECS:
                tqdm.write(fmt_report_str('Train', train_weight, train_loss, train_correct))
                report_test_loss()

                self.save(sess)
                last_report_time = time.time()

        report_test_loss()

    def train(self,
              stepsize: float=1e-5, nepoch: int=1000,
              load_model: Optional[str]=None,
              report_distr: bool=False, label_name_map: Optional[Dict[int, str]]=None
    ):
        optimizer = tf.train.AdamOptimizer(stepsize)
        train_function = optimizer.minimize(self.loss_placeholder.weighted_loss)

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
