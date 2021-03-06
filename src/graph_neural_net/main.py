import argparse
import collections
import gn_utils
import graph_construction
import json
import math
import nn
import os
import pickle
import random
from tabulate import tabulate
from typing import Any, Counter, Dict, List, Optional, Tuple
import utils

GraphJson = Dict[str, Any]

def collect_jsons_in_directory(directory: str) -> List[str]:
    files = []
    for (root, _, fnames) in os.walk(directory):
        for fname in fnames:
            if fname.endswith('.json'):
                files.append(os.path.join(root, fname))
    return files

def collect_graph_jsons(files: List[str], dirs: List[str], projects: List[str]) -> Tuple[List[str], List[List[GraphJson]]]:
    project_names = []
    project_graph_files : List[List[str]] = []

    project_names.extend(files)
    project_graph_files.extend(map(lambda x: [x], files))

    for directory in dirs:
        project_names.append(directory)
        project_graph_files.append(collect_jsons_in_directory(directory))

    for project in projects:
        if not os.path.exists(project):
            raise ValueError('{} does not exist')
        for directory in os.listdir(project):
            path = os.path.join(project, directory)
            project_names.append(path)
            project_graph_files.append(collect_jsons_in_directory(path))

    project_graph_json : List[List[GraphJson]] = []
    for files in project_graph_files:
        jsons = []
        for fname in files:
            if not os.path.exists(fname):
                raise ValueError('{} does not exist')
            with open(fname) as f:
                jsons.append(json.load(f))
        project_graph_json.append(jsons)

    return project_names, project_graph_json

def describe_dataset(dataset, names, graphs, labels):
    utils.log('====={} set ({} nodes, {} edges, {} labels): =====\n{}\n'.format(
        dataset,
        sum(sum(g.n_node) for g in graphs),
        sum(sum(g.n_edge) for g in graphs),
        sum(map(len, labels)),
        '\n'.join(names)
    ))

def get_train_test_index_split(n: int, split_percent: float) -> Tuple[List[int], List[int]]:
    idxs = list(range(n))
    random.shuffle(idxs)
    n_train = math.floor(split_percent * len(idxs))
    train_idxs = idxs[:n_train]
    test_idxs = idxs[n_train:]
    return train_idxs, test_idxs

def load_index_maps(args: Any, graph_jsons: List[Dict[str, Any]]) -> graph_construction.IndexMaps:
    params = {}
    def add_arg_to_params(arg):
        value = getattr(args, arg)
        if value is not None:
            params[arg] = value

    for arg in ['ast_nonunk_percent', 'ast_nonunk_count',
                'edge_nonunk_percent', 'edge_nonunk_count',
                'label_nonunk_percent', 'label_nonunk_count',
                ]:
        add_arg_to_params(arg)

    if args.load_mappings:
        if params:
            raise ValueError('Cannot modify loaded index map!')

        with open(args.load_mappings, 'rb') as f:
            return pickle.load(f)
    else:
        return graph_construction.construct_index_maps(graph_jsons, not args.no_collapse_any_unk, **params)

def save_index_maps(index_maps: graph_construction.IndexMaps) -> None:
    path = os.path.join(utils.DIRNAME, 'index_maps')
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, utils.get_time_str()), 'wb') as f:
        pickle.dump(index_maps, f)

def describe_index_maps(index_maps: graph_construction.IndexMaps) -> None:
    utils.log('{} AST types, {} Edge types, {} labels'.format(
        len(index_maps.ast_type_index_map),
        len(index_maps.edge_type_index_map),
        len(index_maps.label_index_map),
    ))

def report_label_distribution(name: str, labels: List[Dict[int, int]], label_name_map: Dict[int, str], report_count: int) -> None:
    logname = os.path.join('reports', utils.get_time_str(), 'distr_{}'.format(name))
    report = '{} set label distribution:\n\ntotal: {}\n'.format(name, sum(map(len, labels)))

    counter = Counter[int](utils.flatten(l.values() for l in labels))
    most_common = counter.most_common(report_count)
    table_entries = [(count, label_name_map[key]) for (key, count) in most_common]
    report += tabulate(table_entries, headers=['Count', 'Label']) + '\n'

    utils.write(report, logname)

def print_top_k_accuracies(train_labels: List[Dict[int, int]], test_labels: List[Dict[int, int]], top_k_accuracy: List[int], label: str) -> None:
    pred_freq_counter = Counter[int](utils.flatten(l.values() for l in train_labels))
    pred_vec = [lab for (lab, count) in pred_freq_counter.most_common()]

    total_labs = sum(map(len, test_labels))
    unk_labs = sum(1 for labs in test_labels for lab in labs.values() if lab == 0)

    for k in top_k_accuracy:
        k_preds = set(pred_vec[:k])
        corr = sum(1 for labs in test_labels for lab in labs.values() if lab in k_preds)
        utils.log('{}: top {} accuracy: {:.2f} ({:.2f} w/out UNK)'.format(
            label,
            k,
            corr / total_labs,
            corr / (total_labs - unk_labs),
        ))


def main() -> None:
    parser = argparse.ArgumentParser(description='Train and test using the Deepmind GNN framework.')
    parser.add_argument('--file', '-f', nargs='+', help='Individual graph files to process', default=[])
    parser.add_argument('--dir', '--directory', '-d', nargs='+', help='Individual project directories to process', default=[])
    parser.add_argument('--project', '-p', nargs='+', help='Directories containing a list of directories (equivalent to --dir PROJECT/*)', default=[])
    parser.add_argument('--report-count', type=int, help='Count of items to report. Default 10', default=10)
    parser.add_argument('--load-model', help='File to load model from')
    parser.add_argument('--load-mappings', help='File to load mappings from')
    parser.add_argument('--train-split-ratio', type=float, help='Train/test split ratio (default=0.8)', default=0.8)
    parser.add_argument('--step-size', type=float, help='Step size (default=1e-3)', default=1e-3)
    parser.add_argument('--random-seed', type=int, help='Random seed to use. Default=100, negative number = random', default=100)
    parser.add_argument('--niter', type=int, help='Number of iterations to run the GNN for.', default=10)
    parser.add_argument('--ignore-edge-type', nargs='+', type=int, help='Whether to completely ignore the given edge type', default=[])
    parser.add_argument('--no-collapse-any-unk', help='Don\'t collapse the $any$ and UNK tokens.', default=False, action='store_true')
    parser.add_argument('--batch-size', type=int, help='File batch size for training and testing', default=16)
    parser.add_argument('--iteration-ensemble', help='Whether to run the "iteration ensemble" experiment.', default=False, action='store_true')
    parser.add_argument('--top-k-accuracy', nargs='+', type=int, help='How many accuracies to report. Default 1.', default=[1,2,3,4,5])
    parser.add_argument('--node-latent-size', type=int, help='Latent state vector size for nodes', default=32)
    parser.add_argument('--node-hidden-size', type=int, help='Hidden state vector size for nodes (in 1-layer net)', default=64)
    parser.add_argument('--edge-latent-size', type=int, help='Latent state vector size for edges', default=32)
    parser.add_argument('--edge-hidden-size', type=int, help='Hidden state vector size for edges (in 1-layer net)', default=64)
    parser.add_argument('--train-without-unk', help='Whether to remove all UNK from the training data.', default=True, action='store_true')
    parser.add_argument('--load-train-test', help='Use train-test data from a file. Calculate split otherwise.', default=False, action='store_true')
    parser.add_argument('--train-loss-after-ep', help='FOR BO USE ONLY.', default=None, type=int)

    ast_type_unk_group = parser.add_mutually_exclusive_group()
    ast_type_unk_group.add_argument('--ast-nonunk-percent', type=float, help='The percentage of AST types to explicitly encode (i.e. not UNK)')
    ast_type_unk_group.add_argument('--ast-nonunk-count', type=int, help='The number of AST types to explicitly encode (i.e. not UNK)')

    edge_type_unk_group = parser.add_mutually_exclusive_group()
    edge_type_unk_group.add_argument('--edge-nonunk-percent', type=float, help='The percentage of edge types to explicitly encode (i.e. not UNK)')
    edge_type_unk_group.add_argument('--edge-nonunk-count', type=int, help='The number of edge types to explicitly encode (i.e. not UNK)')

    label_unk_group = parser.add_mutually_exclusive_group()
    label_unk_group.add_argument('--label-nonunk-percent', type=float, help='The percentage of labels to explicitly encode (i.e. not UNK)')
    label_unk_group.add_argument('--label-nonunk-count', type=int, default=20, help='The number of labels to explicitly encode (i.e. not UNK)')

    args = parser.parse_args()
    utils.log('Args: {}'.format(args))

    utils.set_random_seed(args.random_seed)

    if not args.load_train_test:
        project_names, project_graph_jsons = collect_graph_jsons(args.file, args.dir, args.project)
        train_idxs, test_idxs = get_train_test_index_split(len(project_names), args.train_split_ratio)

        def get_split(idxs):
            names = [project_names[i] for i in idxs]
            graph_jsons = [project_graph_jsons[i] for i in idxs]
            return names, graph_jsons

        train_names, train_graph_jsons = get_split(train_idxs)
        test_names, test_graph_jsons = get_split(test_idxs)

        index_maps = load_index_maps(args, utils.flatten(train_graph_jsons))
        # save_index_maps(index_maps)
        describe_index_maps(index_maps)
        utils.save_data('train_test',
                    train_names = train_names,
                    train_graph_jsons = train_graph_jsons,
                    test_names = test_names,
                    test_graph_jsons = test_graph_jsons,
                    index_maps = index_maps
                    )
    else:
        [train_names, train_graph_jsons, test_names, test_graph_jsons, index_maps] = utils.load_train_test_data('train_test_full')

    train_graph_tuple, train_labels = graph_construction.graphs_json_to_graph_tuple_and_labels(
        utils.flatten(train_graph_jsons),
        index_maps,
        ignore_edge_types=args.ignore_edge_type,
    )

    if args.train_without_unk:
        for labels in train_labels:
            for (k, v) in list(labels.items()):
                if v == 0:
                    del labels[k]

    train_graphs = gn_utils.split_np(train_graph_tuple)
    test_graph_tuple, test_labels = graph_construction.graphs_json_to_graph_tuple_and_labels(
        utils.flatten(test_graph_jsons),
        index_maps,
        ignore_edge_types=args.ignore_edge_type,
    )
    test_graphs = gn_utils.split_np(test_graph_tuple)

    describe_dataset('train', train_names, train_graphs, train_labels)
    describe_dataset('test', test_names, test_graphs, test_labels)

    print_top_k_accuracies(train_labels, train_labels, args.top_k_accuracy, 'Train')
    print_top_k_accuracies(train_labels, test_labels, args.top_k_accuracy, 'Test')

    label_name_map = utils.invert_bijective_dict(index_maps.label_index_map)
    report_label_distribution('train', train_labels, label_name_map, args.report_count)
    report_label_distribution('test', test_labels, label_name_map, args.report_count)
    report_params = nn.ReportParameters(args.report_count, label_name_map)

    trainer = nn.Trainer(train_graphs, train_labels, test_graphs, test_labels, index_maps.label_index_map,
                         niter=args.niter, iteration_ensemble=args.iteration_ensemble,
                         batch_size=args.batch_size, top_k_report=args.top_k_accuracy,
                         node_latent_size=args.node_latent_size, node_hidden_size=args.node_hidden_size,
                         edge_latent_size=args.edge_latent_size, edge_hidden_size=args.edge_hidden_size,
                         train_loss_after_epno=args.train_loss_after_ep
    )
    trainer.train(stepsize=args.step_size, load_model=args.load_model, report_params=report_params)

if __name__ == '__main__':
    main()
