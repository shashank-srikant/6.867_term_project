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
        for directory in os.listdir(project):
            path = os.path.join(project, directory)
            project_names.append(path)
            project_graph_files.append(collect_jsons_in_directory(path))

    project_graph_json : List[List[GraphJson]] = []
    for files in project_graph_files:
        jsons = []
        for fname in files:
            with open(fname) as f:
                jsons.append(json.load(f))
        project_graph_json.append(jsons)

    return project_names, project_graph_json

def describe_dataset(dataset, names, graphs, labels):
    print('{} set ({} nodes, {} labels): =====\n{}\n====='.format(
        dataset,
        sum(sum(g.n_node) for g in graphs),
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


def save_index_maps(index_maps: graph_construction.IndexMaps) -> None:
    path = os.path.join(utils.DIRNAME, 'index_maps')
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, utils.get_time_str()), 'wb') as f:
        pickle.dump(index_maps, f)

def report_label_distribution(name: str, labels: List[Dict[int, int]], label_name_map: Dict[int, str], report_count: int) -> None:
    most_common = Counter[int](utils.flatten(l.values() for l in labels)).most_common(report_count)

    dirname = os.path.join(utils.DIRNAME, 'reports', utils.get_time_str())
    os.makedirs(dirname, exist_ok=True)
    with open(os.path.join(dirname, 'distr_{}'.format(name)), 'w') as f:
        print('total: {}'.format(sum(map(len, labels))), file=f)
        for (key, count) in most_common:
            print('{} {}'.format(count, label_name_map[key]), file=f)

def main() -> None:
    parser = argparse.ArgumentParser(description='Train and test using the Deepmind GNN framework.')
    parser.add_argument('--file', '-f', nargs='+', help='Individual graph files to process', default=[])
    parser.add_argument('--dir', '--directory', '-d', nargs='+', help='Individual project directories to process', default=[])
    parser.add_argument('--project', '-p', nargs='+', help='Directories containing a list of directories (equivalent to --dir PROJECT/*)', default=[])
    parser.add_argument('--report', help='Report data item frequencies', action='store_true', default=False)
    parser.add_argument('--report-count', nargs=1, type=int, help='Count of items to report. Default 10', default=10)
    parser.add_argument('--load-model', help='File to load model from')
    parser.add_argument('--load-mappings', nargs=1, help='File to load mappings from')
    parser.add_argument('--train-split-ratio', nargs=1, type=float, help='Train/test split ratio (default=0.8)', default=0.8)
    parser.add_argument('--random-seed', nargs=1, type=int, help='Random seed to use. Default=100, negative number = random', default=100)
    args = parser.parse_args()

    utils.set_random_seed(args.random_seed)

    project_names, project_graph_jsons = collect_graph_jsons(args.file, args.dir, args.project)
    train_idxs, test_idxs = get_train_test_index_split(len(project_names), args.train_split_ratio)

    def get_split(idxs):
        names = [project_names[i] for i in idxs]
        graph_jsons = [project_graph_jsons[i] for i in idxs]
        return names, graph_jsons

    train_names, train_graph_jsons = get_split(train_idxs)
    test_names, test_graph_jsons = get_split(test_idxs)

    if args.load_mappings:
        with open(args.load_mappings, 'rb') as f:
            index_maps = pickle.load(f)
    else:
        index_maps = graph_construction.construct_index_maps(utils.flatten(train_graph_jsons))
    save_index_maps(index_maps)

    train_graph_tuple, train_labels = graph_construction.graphs_json_to_graph_tuple_and_labels(utils.flatten(train_graph_jsons), index_maps)
    train_graphs = gn_utils.split_np(train_graph_tuple)
    test_graph_tuple, test_labels = graph_construction.graphs_json_to_graph_tuple_and_labels(utils.flatten(test_graph_jsons), index_maps)
    test_graphs = gn_utils.split_np(test_graph_tuple)

    describe_dataset('train', train_names, train_graphs, train_labels)
    describe_dataset('test', test_names, test_graphs, test_labels)

    report_params: Optional[nn.ReportParameters] = None

    if args.report:
        label_name_map = utils.invert_bijective_dict(index_maps.label_index_map)
        report_label_distribution('train', train_labels, label_name_map, args.report_count)
        report_label_distribution('test', test_labels, label_name_map, args.report_count)
        report_params = nn.ReportParameters(args.report_count, label_name_map)

    trainer = nn.Trainer(train_graphs, train_labels, test_graphs, test_labels)
    trainer.train(load_model=args.load_model, report_params=report_params)

if __name__ == '__main__':
    main()
