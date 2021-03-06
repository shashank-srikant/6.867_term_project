import * as ts from 'typescript';
import { GraphEdge } from "./interfaces";
import { Edge } from "./edge";

export class EdgeAST extends Edge {
    constructor(){
        super([1], "Forms edges between every existing edge of the input AST");
    }

    public visit_tree(
        node: ts.Node,
        edges: GraphEdge[],
        parent: number,
        checker: ts.TypeChecker,
        node_map: Map<ts.Node, number>
    ): GraphEdge[]{
        let curr_node_id = node_map.get(node);
        /*if(typeof curr_node_id == 'undefined'){
            console.log(ts.SyntaxKind[node.kind]);
        }
        */
        let edgeobj : GraphEdge = {'src': parent, 'dst': curr_node_id, 'edge_type': this.edge_type[0]};
        edges.push(edgeobj);
        //node.forEachChild(n => (this.visit_tree(n, edges, curr_node_id, checker, node_map)));
        for(let i = 0; i<node.getChildCount(); i++){
            edges = this.visit_tree(node.getChildAt(i), edges, curr_node_id, checker, node_map);
        }
        return edges;
    }
}
