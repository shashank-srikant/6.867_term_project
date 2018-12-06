import sys
sys.path.append('../graph_neural_net/')
import graph_construction, utils
from typing import Dict, Tuple
print(graph_construction.UNK)

[_, graphs_train, _, graphs_test, index_maps] = utils.load_train_test_data('train_test')
graphs_train, graphs_test = utils.flatten(graphs_train), utils.flatten(graphs_test)
ast_type_index_map, edge_type_index_map, label_index_map = index_maps
node_index_map: Dict[Tuple[int, int], int] = {}
labels = []
offset = 0
for g_idx, g in enumerate(graphs_train):
    print(g['nodes'])
    for n in g['nodes']:
        nid = n['id']
        if (g_idx, nid) in node_index_map:
            raise ValueError('Duplicate node in graph {}: id {}'.format(g_idx + 1, nid))
        nidx = len(node_index_map)
        node_index_map[(g_idx, nid)] = nidx

for g_idx, g in enumerate(graphs_train):
    g_labels = {}
    for l in g['labels']:
        g_labels[node_index_map[(g_idx, l['node'])] - offset] = label_index_map[l['label']]
    offset += n_nodes[g_idx]
    labels.append(g_labels)