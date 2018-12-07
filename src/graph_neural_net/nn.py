import graph_construction
import graph_nets as gn
import gn_utils
import numpy as np
import os
import random
import sonnet as snt
from tabulate import tabulate
import tensorflow as tf
import time
from tqdm import tqdm, trange
from typing import Any, Dict, List, NamedTuple, Optional, Sequence, Tuple
import utils

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
    unkless_weighted_correct: tf.Tensor
    weighted_loss: tf.Tensor

class BatchResult(NamedTuple):
    total_weight: float
    sum_loss: float
    sum_weighted_correct: np.array
    sum_unkless_weighted_correct: np.array
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
                 label_index_map: Dict[str, int],
                 *,
                 niter: int=10, iteration_ensemble: bool = False, batch_size: int=16,
                 top_k_report: Sequence[int]=[1],
                 node_latent_size:int=128, node_hidden_size:int=256,
                 edge_latent_size:int=128, edge_hidden_size:int=256,
    ) -> None:
        self.train_graphs = train_graphs
        self.train_labels = train_labels
        self.test_graphs = test_graphs
        self.test_labels = test_labels
        self.label_index_map = label_index_map

        self.niter = niter
        self.batch_size = batch_size
        self.top_k_report = top_k_report

        # grab a random representative graph of the node/edge feature lengths
        rep_graph = train_graphs[0]
        node_features_len = rep_graph.nodes.shape[1]
        edge_features_len = rep_graph.edges.shape[1]

        self.num_labels = 1 + max(l for lab_dict in train_labels for l in lab_dict.values())

        self.encoder_module = gn.modules.InteractionNetwork(
            edge_model_fn=lambda: snt.nets.MLP([edge_features_len, edge_latent_size]),
            node_model_fn=lambda: snt.nets.MLP([node_features_len, node_latent_size]),
        )
        self.latent_module = gn.modules.InteractionNetwork(
            edge_model_fn=lambda: snt.nets.MLP([edge_latent_size, edge_hidden_size, edge_latent_size]),
            node_model_fn=lambda: snt.nets.MLP([node_latent_size, node_hidden_size, node_latent_size]),
        )
        self.decoder_module = gn.modules.InteractionNetwork(
            edge_model_fn=lambda: snt.nets.MLP([edge_latent_size, edge_latent_size]),
            node_model_fn=lambda: snt.nets.MLP([node_latent_size, self.num_labels]),
        )
        self.using_iteration_ensemble = iteration_ensemble
        self.iteration_ensemble_weights = tf.get_variable('iteration_ensemble_weights', [niter + 1], trainable=True, dtype=tf.float64)

        self.loss_placeholder, self.batch_input = self._construct_loss_placeholder_and_batch_input()
        self.batched_test_graphs, self.batched_test_labels = self._batch_graphs(test_graphs, test_labels)

        self.saver = tf.train.Saver(
            list(self.encoder_module.get_variables()) +
            list(self.latent_module.get_variables()) +
            list(self.decoder_module.get_variables()) +
            [self.iteration_ensemble_weights]
        )

        self.hyperparams = (
            list(self.encoder_module.get_variables()) +
            list(self.latent_module.get_variables()) +
            list(self.decoder_module.get_variables()) +
            [self.iteration_ensemble_weights]
        )

        self.n_hyperparams = 0
        for v in self.hyperparams:
            self.n_hyperparams += np.prod(v.get_shape().as_list())
        print("{} parameters initialized in this graph network..".format(self.n_hyperparams))

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

        init_graph = self.encoder_module(placeholder_graph)
        iter_graphs = [init_graph]
        for _ in range(self.niter):
            iter_graphs.append(self.latent_module(iter_graphs[-1]))
        decoded_graphs = list(map(self.decoder_module, iter_graphs))

        if self.using_iteration_ensemble:
            ensemble_probs = tf.nn.softmax(self.iteration_ensemble_weights)
            nodes = ensemble_probs[0] * decoded_graphs[0].nodes
            for i in range(1, self.niter + 1):
                nodes += ensemble_probs[i] * decoded_graphs[i].nodes
        else:
            nodes = decoded_graphs[-1].nodes

        pred = tf.argmax(nodes, 1)

        loss_vec = tf.losses.sparse_softmax_cross_entropy(
            labels,
            nodes,
            weights,
            reduction=tf.losses.Reduction.NONE,
        )
        loss = tf.reduce_sum(loss_vec)

        top_k_corr = []
        unkless_top_k_corr = []
        for k in self.top_k_report:
            in_top_k = tf.nn.in_top_k(tf.cast(nodes, tf.float32), labels, k)
            sum_in_top_k = tf.reduce_sum(weights * tf.cast(in_top_k, tf.float32))
            top_k_corr.append(sum_in_top_k)

            unkless_in_top_k = tf.nn.in_top_k(tf.cast(nodes, tf.float32), labels, k)
            unkless_sum_in_top_k = tf.reduce_sum(weights * tf.cast((~tf.equal(labels, self.label_index_map[graph_construction.UNK])) & unkless_in_top_k, tf.float32))
            unkless_top_k_corr.append(unkless_sum_in_top_k)

        top_k_corr = tf.stack(top_k_corr, axis=0)
        unkless_top_k_corr = tf.stack(unkless_top_k_corr, axis=0)

        batch_input = BatchInput(
            output_vec=tf.nn.softmax(nodes),
            prediction_vec=pred,
            loss_vec=loss_vec,
            weighted_correct=top_k_corr,
            unkless_weighted_correct=unkless_top_k_corr,
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
            sum_weighted_correct=np.zeros(len(self.top_k_report)),
            sum_unkless_weighted_correct=np.zeros(len(self.top_k_report)),
            weighted_true_preds=np.zeros(self.num_labels),
            weighted_n_labs=np.zeros(self.num_labels),
            weighted_n_preds=np.zeros(self.num_labels),
        )

        for graph, labels in tqdm(list(zip(batched_graphs, batched_labels)), desc='Batches', leave=False):
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
            sum_unkless_weighted_correct = batch_result_acc.sum_unkless_weighted_correct + batch_result.unkless_weighted_correct
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
                sum_unkless_weighted_correct=sum_unkless_weighted_correct,
                weighted_true_preds=weighted_true_preds,
                weighted_n_labs=weighted_n_labs,

            )

        return batch_result_acc

    def report_rates_on_epoch(self, label: str, epno: int, batch_results: BatchResult, report_params: ReportParameters) -> None:
        report_str = 'Total #preds: {}\n'.format(batch_results.total_weight)

        true_pred = batch_results.weighted_true_preds
        false_miss = batch_results.weighted_n_labs - batch_results.weighted_true_preds
        false_pred = batch_results.weighted_n_preds - batch_results.weighted_true_preds
        # true_miss = (batch_results.total_weight - batch_results.weighted_n_labs) - false_pred

        report_for_i = lambda i: list(map(lambda x: x[i], (report_params.label_name_map, true_pred, false_miss, false_pred)))
        report_str += tabulate(list(map(report_for_i, range(report_params.top_k))), headers=['Label', '#Correct', '#Missed', '#Falsely Predicted'])
        report_str += '\n'

        utils.write(report_str, os.path.join('reports', utils.get_time_str(), 'epoch_{}_{}'.format(epno, label)))

    def save(self, sess: tf.Session) -> None:
        dname = 'graph_{}'.format(utils.get_time_str())
        dname = os.path.join(utils.DIRNAME, 'models', dname)
        os.makedirs(dname, exist_ok=True)
        self.saver.save(sess, os.path.join(dname, 'model'))
        utils.log('Saved model to {}'.format(dname))

    def _train(self,
               sess: tf.Session, train_function: Any,
               nepoch:int=1000,
               report_params:Optional[ReportParameters]=None,
    ) -> None:
        def fmt_report_str(name, batch_result):
            report = '{}: {} Predictions\n'.format(name, batch_result.total_weight)
            report += 'Loss: {:.2f}\n'.format(batch_result.sum_loss / batch_result.total_weight)

            unkless_weight = batch_result.total_weight - batch_result.weighted_n_labs[self.label_index_map[graph_construction.UNK]]

            for (k, corr, unkless_corr) in zip(self.top_k_report, batch_result.sum_weighted_correct, batch_result.sum_unkless_weighted_correct):
                report += 'Top {} accuracy: {:.2f} ({:.2f} w/out UNK)\n'.format(
                    k,
                    corr / batch_result.total_weight,
                    unkless_corr / unkless_weight,
                )
            return report

        def report_test_loss(epno: int) -> None:
            test_batch_result = self._process_batches(sess, self.batched_test_graphs, self.batched_test_labels)
            utils.log(fmt_report_str('Test', test_batch_result))
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
                ensemble_weights = sess.run(tf.nn.softmax(self.iteration_ensemble_weights))
                utils.log('Iteration ensemble weights:\n{}\n'.format(' '.join(map('{:.2f}'.format, ensemble_weights))))
                utils.log(fmt_report_str('Train', train_batch_result))
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
                utils.log('Caught SIGINT!')
            finally:
                self.save(sess)
