import {Graph} from "./graph"
import {EdgeAST} from "./edge_ast"
import {EdgeUseDef} from "./edge_use_def"
import {map2obj, print_obj} from "./utils"

const input_file = process.argv[2];
const output_path = "../data/"
const output_file = process.argv[3] || 'example2.json';
var graph_obj = new Graph(input_file);

let edge_obj_list = []
edge_obj_list.push(new EdgeAST());
edge_obj_list.push(new EdgeUseDef());
let [node_id_to_nodekind_map, edge_list, labels_list, label_dict] = graph_obj.ast2graph(edge_obj_list);

print_obj({
    "nodes": node_id_to_nodekind_map,
    "edges": edge_list,
    "labels": labels_list,
    "label_map": map2obj(label_dict)
}, output_path, output_file);
