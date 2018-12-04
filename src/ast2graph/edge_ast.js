"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const edge_1 = require("./edge");
class EdgeAST extends edge_1.Edge {
    constructor() {
        super([1], "Forms edges between every existing edge of the input AST");
    }
    visit_tree(node, edges, parent, checker, node_map) {
        let curr_node_id = node_map.get(node);
        var edgeobj = { 'src': parent, 'dst': curr_node_id, 'edge_type': this.edge_type[0] };
        edges.push(edgeobj);
        node.forEachChild(n => (this.visit_tree(n, edges, curr_node_id, checker, node_map)));
        return edges;
    }
}
exports.EdgeAST = EdgeAST;
//# sourceMappingURL=edge_ast.js.map