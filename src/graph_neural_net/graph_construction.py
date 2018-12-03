import collections
import graph_nets as gn
import numpy as np
import utils
from typing import Any, Counter, Dict, List, NamedTuple, Tuple

class IndexMaps(NamedTuple):
    ast_type_index_map: Dict[str, int]
    edge_type_index_map: Dict[str, int]
    label_index_map: Dict[str, int]

def construct_index_maps(graph_jsons: List[Dict[str, Any]], ast_type_unk_percent:float=0.1, edge_type_unk_percent:float=0, label_unk_percent:float=0.5):
    ast_type_counter = Counter[str]()
    edge_type_counter = Counter[str]()
    label_counter = Counter[str]()

    for g in graph_jsons:
        ast_type_counter.update(n['ast_type'] for n in g['nodes'])
        edge_type_counter.update(n['edge_type'] for n in g['edges'])
        label_counter.update(l['label'] for l in g['labels'])

    def unked_index_map(counter, percent):
        # default to 0
        m = utils.defaultdict_nowrite(int)
        m['__UNK__'] = 0
        k = int(len(counter) * (1 - percent))
        m.update({n: i + 1 for (i, (n, _)) in enumerate(counter.most_common(k))})
        return m

    ast_type_index_map = unked_index_map(ast_type_counter, ast_type_unk_percent)
    edge_type_index_map = unked_index_map(edge_type_counter, edge_type_unk_percent)
    label_index_map = unked_index_map(label_counter, label_unk_percent)

    return IndexMaps(ast_type_index_map, edge_type_index_map, label_index_map)

def graphs_json_to_graph_tuple_and_labels(graphs: List[Dict[str, Any]], index_maps: IndexMaps) -> Tuple[gn.graphs.GraphsTuple, List[Dict[int, int]]]:
    ast_type_index_map, edge_type_index_map, label_index_map = index_maps

    node_index_map: Dict[Tuple[int, int], int] = {}

    n_nodes = np.array(list(len(g['nodes']) for g in graphs))
    nodes = np.zeros((sum(n_nodes), 1 + max(ast_type_index_map.values())))

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
    edges = np.zeros((sum(n_edges), 1 + max(edge_type_index_map.values())))

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

    return gtuple, labels
