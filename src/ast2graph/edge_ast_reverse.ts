import * as ts from 'typescript';
import { GraphEdge } from "./interfaces";
import { Edge } from "./edge";

export class EdgeASTReverse extends Edge {
    constructor(){
        super([5], "Forms reverse edges between every existing edge of the input AST");
    }

    private reverse_list(edge_list:GraphEdge[]):GraphEdge[] {
        var rev_edge_list:GraphEdge[] = [];
        for(let i = 0; i<edge_list.length; i++){
            let edge: GraphEdge = {'src':edge_list[i]['dst'], 
                                'dst':edge_list[i]['src'],
                                'edge_type': edge_list[i]['edge_type']};
            rev_edge_list.push(edge);
        }
        return rev_edge_list;
    }

    private visit_tree_forward(node: ts.Node,
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

    public visit_tree(
        node: ts.Node,
        edges: GraphEdge[],
        parent: number,
        checker: ts.TypeChecker,
        node_map: Map<ts.Node, number>
    ): GraphEdge[]{
        var edges = this.visit_tree_forward(node, edges, parent, checker, node_map);
        return this.reverse_list(edges);
    }
}
