"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const ts = require("typescript");
const edge_1 = require("./edge");
const utils_1 = require("./utils");
class EdgeUseDef extends edge_1.Edge {
    constructor() {
        super([2, 3], "Connects an edge between usage and defines of all variables");
        this.use_use_type = 2;
        this.use_def_type = 3;
        this.var_last_define = new Map();
        this.var_last_use = new Map();
    }
    draw_edge(parent, curr_node_id, edge_type, edge_list) {
        var edgeobj = { 'src': parent, 'dst': curr_node_id, 'edge_type': edge_type };
        edge_list.push(edgeobj);
    }
    visit_block(node, node_map, use_use, use_def) {
        let visited_block = false;
        let curr_node_id = node_map.get(node);
        switch (node.kind) {
            case ts.SyntaxKind.VariableDeclaration: {
                this.var_last_define.set(node.name.escapedText.toString(), curr_node_id);
                visited_block = true;
                break;
            }
            case ts.SyntaxKind.Parameter: {
                this.var_last_define.set(node.name.escapedText.toString(), curr_node_id);
                visited_block = true;
                break;
            }
            case ts.SyntaxKind.BinaryExpression: {
                let is_assign = utils_1.is_assign_op(node.operatorToken.kind);
                let right_node = node.right;
                let right_node_arr = utils_1.getNodes(right_node);
                let left_node = node.left;
                let left_node_arr = utils_1.getNodes(left_node);
                let var_names_use = Array.from(utils_1.get_block_identifiers(right_node_arr));
                if (!is_assign) {
                    var_names_use = var_names_use.concat(Array.from(utils_1.get_block_identifiers(left_node_arr)));
                }
                for (let i = 0; i < var_names_use.length; i++) {
                    let curr_node_id1 = utils_1.get_node(left_node_arr, var_names_use[i]);
                    let curr_node_id2 = utils_1.get_node(right_node_arr, var_names_use[i]);
                    let curr_node = curr_node_id1.concat(curr_node_id2);
                    curr_node_id = node_map.get(curr_node[0]);
                    if (utils_1.pass_null_check(this.var_last_use.get(var_names_use[i]))) {
                        this.draw_edge(this.var_last_use.get(var_names_use[i]), curr_node_id, this.use_use_type, use_use);
                    }
                    if (utils_1.pass_null_check(this.var_last_define.get(var_names_use[i]))) {
                        this.draw_edge(this.var_last_define.get(var_names_use[i]), curr_node_id, this.use_def_type, use_def);
                    }
                    this.var_last_use.set(var_names_use[i], curr_node_id);
                }
                if (is_assign) {
                    let var_names_define = Array.from(utils_1.get_block_identifiers(left_node_arr));
                    for (let i = 0; i < var_names_define.length; i++) {
                        this.var_last_define.set(var_names_define[i], curr_node_id);
                    }
                }
                visited_block = true;
                break;
            }
        }
        if (!visited_block) {
            node.forEachChild(n => (this.visit_block(n, node_map, use_use, use_def)));
        }
    }
    visit_tree(node, edges, parent, checker, node_map) {
        let edges_all = [];
        switch (node.kind) {
            case ts.SyntaxKind.SourceFile: {
                for (let i = 0; i < node.statements.length; i++) {
                    if (node.statements[i].kind === ts.SyntaxKind.FunctionDeclaration) {
                        let fn_name = node.statements[i].name.escapedText.toString();
                        console.log("in " + fn_name + " ..");
                        let use_use = [];
                        let use_def = [];
                        this.visit_block(node.statements[i], node_map, use_use, use_def);
                        edges = edges.concat(use_use);
                        edges = edges.concat(use_def);
                    }
                    else {
                        let use_use = [];
                        let use_def = [];
                        this.visit_block(node, node_map, use_use, use_def);
                        edges = edges.concat(use_use);
                        edges = edges.concat(use_def);
                    }
                }
                break;
            }
            default: {
                console.log('in default');
                let use_use = [];
                let use_def = [];
                this.visit_block(node, node_map, use_use, use_def);
                edges = edges.concat(use_use);
                edges = edges.concat(use_def);
            }
        }
        return edges;
    }
}
exports.EdgeUseDef = EdgeUseDef;
//# sourceMappingURL=edge_use_def.js.map