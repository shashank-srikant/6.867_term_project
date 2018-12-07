import sys
import collections
sys.path.append('../graph_neural_net/')
import graph_construction, utils
from typing import Dict, Tuple, Counter
import numpy as np

[a, graphs_train, b, graphs_test, index_maps] = utils.load_train_test_data('train_test_full')
graphs_train, graphs_test = utils.flatten(graphs_train), utils.flatten(graphs_test)
ast_type_index_map, edge_type_index_map, label_index_map = index_maps

print(len(a))
print(a[0])
print(len(graphs_train))
#print(graphs_train[0])
print("--")
print(len(b))
print(b[0])
print(len(graphs_test))
#print(graphs_test[0])
print('--')
print(len(ast_type_index_map))
print(len(edge_type_index_map))
print('--')
def get_edges(graph):
    ed = 0
    for g in graph:
        ed += len(g['edges'])
    return ed
print(get_edges(graphs_train))
print(get_edges(graphs_test))

# This code is a clone of
# a part of graph_construction.graphs_json_to_graph_tuple_and_labels
def get_labels(graph):
    node_index_map: Dict[Tuple[int, int], int] = {}
    n_nodes = np.array(list(len(g['nodes']) for g in graph))

    for g_idx, g in enumerate(graph):
        for n in g['nodes']:
            nid = n['id']
            if (g_idx, nid) in node_index_map:
                raise ValueError('Duplicate node in graph {}: id {}'.format(g_idx + 1, nid))
            nidx = len(node_index_map)
            node_index_map[(g_idx, nid)] = nidx
    labels = []
    offset = 0
    for g_idx, g in enumerate(graph):
        g_labels = {}
        for l in g['labels']:
            g_labels[node_index_map[(g_idx, l['node'])] - offset] = label_index_map[l['label']]
        offset += n_nodes[g_idx]
        labels.append(g_labels)
    
    print("n_nodes: {}".format(len(n_nodes)))
    sum_n = 0
    for n in n_nodes:
        sum_n += n
    print("# nodes: {}".format(sum_n))
    return labels

labels_train = get_labels(graphs_train)
labels_test = get_labels(graphs_test)

def get_label_counter(labels):
    label_counter = Counter[int]()    
    for g in labels:
        label_counter.update(list(g.values()))
    return label_counter

label_counter_train = get_label_counter(labels_train)
label_counter_test = get_label_counter(labels_test)

majority_vote = label_counter_train.most_common(3)

def get_accuracy(counter_obj, majority_vote):
    correct = counter_obj[majority_vote]
    total = sum(counter_obj.values())
    print("total : {}".format(total))
    return correct, total, "{0:.0%}".format(correct/total)

for i in range(len(majority_vote)):
    c_train, t_train, acc_train = get_accuracy(label_counter_train, majority_vote[i][0])
    c_test, t_test, acc_test = get_accuracy(label_counter_test, majority_vote[i][0])
    lbl_name = "-"
    for k, v in label_index_map.items():
        if v == majority_vote[i][0]:
            lbl_name = k
    print("Label {} when set as the prediction across labels -- ".format(lbl_name))
    print((c_train, t_train, acc_train))
    print((c_test, t_test, acc_test))
    print('==')