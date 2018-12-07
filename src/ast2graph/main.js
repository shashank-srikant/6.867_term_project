"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const graph_1 = require("./graph");
const edge_ast_1 = require("./edge_ast");
const edge_use_def_1 = require("./edge_use_def");
const utils_1 = require("./utils");
const input_file = process.argv[2];
const output_path = "../data/";
const output_file = process.argv[3] || 'example2.json';
var graph_obj = new graph_1.Graph(input_file);
let edge_obj_list = [];
edge_obj_list.push(new edge_ast_1.EdgeAST());
edge_obj_list.push(new edge_use_def_1.EdgeUseDef());
let [node_id_to_nodekind_map, edge_list, labels_list, label_dict] = graph_obj.ast2graph(edge_obj_list);
utils_1.print_obj({ "nodes": node_id_to_nodekind_map,
    "edges": edge_list,
    "labels": labels_list,
    "label_map": utils_1.map2obj(label_dict)
}, output_path, output_file);
//# sourceMappingURL=main.js.map