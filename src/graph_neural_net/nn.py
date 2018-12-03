import graph_nets as gn
import gn_utils
import numpy as np
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
    placeholder_graph: gn.graphs.GraphsTuple
    placeholder_weights: tf.placeholder
    placeholder_labels: tf.placeholder

class BatchInput(NamedTuple):
    output_vec: tf.Tensor
    prediction_vec: tf.Tensor
    loss_vec: tf.Tensor
    weighted_correct: tf.Tensor
    weighted_loss: tf.Tensor

class BatchResult(NamedTuple):
    total_weight: float
    sum_loss: float
    sum_weighted_correct: float
    weighted_true_preds: np.array
    weighted_n_labs: np.array
    weighted_n_preds: np.array

class ReportParameters(NamedTuple):
    top_k: int
    label_name_map: Dict[int, str]

class Trainer:
    def __init__(self,
                 train_graphs: List[gn.graphs.GraphsTuple],
                 train_labels: List[Dict[int, int]],
                 test_graphs: List[gn.graphs.GraphsTuple],
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

        self.num_labels = 1 + max(l for lab_dict in train_labels for l in lab_dict.values())

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
            node_model_fn=lambda: snt.nets.MLP([NODE_LATENT_SIZE, self.num_labels]),
        )

        self.loss_placeholder, self.batch_input = self._construct_loss_placeholder_and_batch_input()
        self.batched_test_graphs, self.batched_test_labels = self._batch_graphs(test_graphs, test_labels)

        self.saver = tf.train.Saver(
            list(self.encoder_module.get_variables()) +
            list(self.latent_module.get_variables()) +
            list(self.decoder_module.get_variables())
        )

    def _construct_loss_placeholder_and_batch_input(self) -> Tuple[LossPlaceholder, BatchInput]:
        # construct placeholder from an arbitrary graph in the dataset to get correct shapes
        placeholder_graph = gn.utils_tf._placeholders_from_graphs_tuple(self.train_graphs[0], True)
        n_nodes_placeholder = placeholder_graph.nodes.shape[0]
        weights = tf.placeholder(tf.float32, shape=[n_nodes_placeholder])
        labels = tf.placeholder(tf.int64, shape=[n_nodes_placeholder])

        loss_placeholder = LossPlaceholder(
            placeholder_graph=placeholder_graph,
            placeholder_weights=weights,
            placeholder_labels=labels,
         )

        graph = self.encoder_module(placeholder_graph)
        for _ in range(self.niter):
            graph = self.latent_module(graph)
        graph = self.decoder_module(graph)

        pred = tf.argmax(graph.nodes, 1)

        loss_vec = tf.losses.sparse_softmax_cross_entropy(
            labels,
            graph.nodes,
            weights,
            reduction=tf.losses.Reduction.NONE,
        )
        loss = tf.reduce_sum(loss_vec)

        correct_vec = tf.equal(pred, labels)
        correct = tf.reduce_sum(weights * tf.cast(correct_vec, tf.float32))

        batch_input = BatchInput(
            output_vec=tf.nn.softmax(graph.nodes),
            prediction_vec=pred,
            loss_vec=loss_vec,
            weighted_correct=correct,
            weighted_loss=loss,
        )

        return loss_placeholder, batch_input

    def _batch_graphs(self, graphs: List[gn.graphs.GraphsTuple], labels: List[Dict[int, int]]) -> Tuple[List[gn.graphs.GraphsTuple], List[List[Dict[int, int]]]]:
        batched_graphs = []
        batched_labels = []
        for i in range(0, len(graphs), self.batch_size):
            batched_graphs.append(gn_utils.concat_np(graphs[i:i+self.batch_size]))
            batched_labels.append(labels[i:i+self.batch_size])

        return batched_graphs, batched_labels

    def _process_batches(self, sess: tf.Session,
                         batched_graphs: List[gn.graphs.GraphsTuple], batched_labels: List[List[Dict[int, int]]],
                         train_function: Optional[Any]=None) -> BatchResult:
        batch_result_acc = BatchResult(
            total_weight=0,
            sum_loss=0,
            sum_weighted_correct=0,
            weighted_true_preds=np.zeros(self.num_labels),
            weighted_n_labs=np.zeros(self.num_labels),
            weighted_n_preds=np.zeros(self.num_labels),
        )

        for graph, labels in tqdm(list(zip(batched_graphs, batched_labels)), desc='Batches'):
            weights_arr, labels_arr = gn_utils.weights_and_labels_arr(graph, labels)

            feed_dict = gn.utils_tf.get_feed_dict(self.loss_placeholder.placeholder_graph, graph)
            feed_dict[self.loss_placeholder.placeholder_weights] = weights_arr
            feed_dict[self.loss_placeholder.placeholder_labels] = labels_arr

            if train_function is None:
                batch_result = sess.run(self.batch_input, feed_dict)
            else:
                batch_result, _ = sess.run([self.batch_input, train_function], feed_dict)

            total_weight = batch_result_acc.total_weight + weights_arr.sum()
            sum_loss = batch_result_acc.sum_loss + batch_result.weighted_loss
            sum_weighted_correct = batch_result_acc.sum_weighted_correct + batch_result.weighted_correct
            weighted_true_preds = batch_result_acc.weighted_true_preds
            weighted_n_labs = batch_result_acc.weighted_n_labs
            weighted_n_preds = batch_result_acc.weighted_n_preds

            for (pred, weight, label) in zip(batch_result.prediction_vec, weights_arr, labels_arr):
                weighted_true_preds[label] += weight * (pred == label)
                weighted_n_labs[label] += weight
                weighted_n_preds[pred] += weight

            batch_result_acc = batch_result_acc._replace(
                total_weight=total_weight,
                sum_loss=sum_loss,
                sum_weighted_correct=sum_weighted_correct,
                weighted_true_preds=weighted_true_preds,
                weighted_n_labs=weighted_n_labs,

            )

        return batch_result_acc

    def report_rates_on_epoch(self, label: str, epno: int, batch_results: BatchResult, report_params: ReportParameters) -> None:
        with open(os.path.join(utils.DIRNAME, 'reports', utils.get_time_str(), 'epoch_{}_{}'.format(epno, label)), 'w') as f:
            f.write('Total #preds: {}\n'.format(batch_results.total_weight))

            true_pred = batch_results.weighted_true_preds
            false_miss = batch_results.weighted_n_labs - batch_results.weighted_true_preds
            false_pred = batch_results.weighted_n_preds - batch_results.weighted_true_preds
            true_miss = (batch_results.total_weight - batch_results.weighted_n_labs) - false_pred

            for i in range(report_params.top_k):
                f.write('{} -- True pred: {}, False miss: {}, False pred: {}, True Miss: {}\n'.format(
                    *map(lambda x: x[i], (report_params.label_name_map, true_pred, false_miss, false_pred, true_miss))
                ))

    def save(self, sess: tf.Session) -> None:
        tqdm.write('Saving model...')
        dname = 'graph_{}'.format(utils.get_time_str())
        dname = os.path.join(utils.DIRNAME, 'models', dname)
        os.makedirs(dname, exist_ok=True)
        self.saver.save(sess, os.path.join(dname, 'model'))
        tqdm.write('Saved model to {}'.format(dname))

    def _train(self,
               sess: tf.Session, train_function: Any,
               nepoch:int=1000,
               report_params:Optional[ReportParameters]=None,
    ) -> None:
        def fmt_report_str(name, batch_result):
            return '{}: loss: {:.2f}, Accuracy: {:.2f} ({}/{})'.format(
                name,
                batch_result.sum_loss,
                batch_result.sum_weighted_correct / batch_result.total_weight,
                batch_result.sum_weighted_correct, batch_result.total_weight,
            )

        def report_test_loss(epno: int) -> None:
            test_batch_result = self._process_batches(sess, self.batched_test_graphs, self.batched_test_labels)
            tqdm.write(fmt_report_str('Test', test_batch_result))
            if report_params:
                self.report_rates_on_epoch('Test', epno, test_batch_result, report_params)

        last_report_time: float = 0

        for epno in trange(nepoch, desc='Epochs'):
            graphs_and_labels = list(zip(self.train_graphs, self.train_labels))
            random.shuffle(graphs_and_labels)
            graphs, labels = zip(*graphs_and_labels)
            batched_train_graphs, batched_train_labels = self._batch_graphs(graphs, labels)

            train_batch_result = self._process_batches(sess, batched_train_graphs, batched_train_labels, train_function)
            if (time.time() - last_report_time) > REPORT_FREQ_SECS:
                tqdm.write(fmt_report_str('Train', train_batch_result))
                if report_params:
                    self.report_rates_on_epoch('Train', epno, train_batch_result, report_params)
                report_test_loss(epno)

                self.save(sess)
                last_report_time = time.time()

        report_test_loss(nepoch)

    def train(self,
              stepsize: float=5e-3, nepoch: int=1000,
              load_model: Optional[str]=None,
              report_params:Optional[ReportParameters]=None,
    ):
        optimizer = tf.train.AdamOptimizer(stepsize)
        train_function = optimizer.minimize(self.batch_input.weighted_loss)

        with tf.Session() as sess:
            sess.run(tf.global_variables_initializer())

            if load_model:
                self.saver.restore(sess, os.path.join(load_model, 'model'))

            try:
                self._train(
                    sess, train_function,
                    nepoch=nepoch,
                    report_params=report_params,
                )
            except KeyboardInterrupt:
                print('Caught SIGINT!')
            finally:
                self.save(sess)
