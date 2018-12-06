"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const ts = require("typescript");
const label_1 = require("./label");
class Graph {
    constructor(ast_path) {
        this.ast_path = ast_path;
        this.node_id_to_nodeobj_map = new Map();
        this.node_id_to_nodekind_list = [{ 'id': -1, 'ast_type': -1 }];
        this.max_node_count = 0;
    }
    ast2graph(edge_obj_list) {
        const source_pgm = ts.createProgram({
            rootNames: [this.ast_path],
            options: {}
        });
        const checker = source_pgm.getTypeChecker();
        let source_files = source_pgm.getSourceFiles();
        for (let source_file of source_files) {
            if (!source_file.fileName.endsWith(this.ast_path)) {
                continue;
            }
            this.assign_node_counter(source_file);
            let labels_dict = new Map();
            let labels_list = [];
            label_1.get_all_labels(labels_list, labels_dict, source_file, checker, this.node_id_to_nodeobj_map);
            let all_edges = [];
            for (let i = 0; i < edge_obj_list.length; i++) {
                let edge_list = [];
                edge_list = edge_obj_list[i].visit_tree(source_file, edge_list, -1, checker, this.node_id_to_nodeobj_map);
                console.log(edge_list);
                all_edges = all_edges.concat(edge_list);
            }
            console.log('done ast2graph');
            return [this.node_id_to_nodekind_list, all_edges, labels_list, labels_dict];
        }
    }
    assign_node_counter(node) {
        this.max_node_count++;
        this.node_id_to_nodeobj_map.set(node, this.max_node_count);
        var nodeobj = { 'id': this.max_node_count, 'ast_type': node.kind };
        this.node_id_to_nodekind_list.push(nodeobj);
        node.forEachChild(n => (this.assign_node_counter(n)));
    }
}
exports.Graph = Graph;
//# sourceMappingURL=graph.js.map