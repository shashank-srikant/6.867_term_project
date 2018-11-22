import * as ts from 'typescript';
import { GraphEdge } from "./interfaces";
import { Edge } from "./edge";
import { get_variable_names } from "./utils"

export class EdgeUseDef extends Edge {
    constructor(){
        super(2, "Connects an edge between usage and defines of all variables");
    } 

        

    public visit_tree(node: ts.Node, edges: GraphEdge[],
                        parent: number, checker: ts.TypeChecker,
                        node_map: Map<ts.Node, number>){
        
        let n = get_variable_names(node);
        process.exit(0)
        let curr_node_id = node_map.get(node);
        var edgeobj:GraphEdge = {'src': parent, 'dst': curr_node_id, 'edge_type': this.edge_type}
        edges.push(edgeobj);
        node.forEachChild(n => (this.visit_tree(n, edges, curr_node_id, checker, node_map)));
    }
}