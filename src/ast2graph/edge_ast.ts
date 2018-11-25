import * as ts from 'typescript';
import { GraphEdge } from "./interfaces";
import { Edge } from "./edge";

export class EdgeAST extends Edge {
    constructor(){
        super([1], "Forms edges between every existing edge of the input AST");
    }
    
    public visit_tree(node: ts.Node, edges: GraphEdge[],
            parent: number, checker: ts.TypeChecker,
            node_map: Map<ts.Node, number>){
        
        let curr_node_id = node_map.get(node);
        var edgeobj:GraphEdge = {'src': parent, 'dst': curr_node_id, 'edge_type': this.edge_type[0]}
        edges.push(edgeobj);
        node.forEachChild(n => (this.visit_tree(n, edges, curr_node_id, checker, node_map)));
    }
}