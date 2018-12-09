import * as ts from 'typescript';
import { GraphEdge } from "./interfaces";
import { Edge } from "./edge";

export class EdgeTokens extends Edge {
    private prev_token:number;

    constructor(){
        super([4], "An edge between every token");
        this.prev_token = -1;
    }

    public visit_tree(
        node: ts.Node,
        edges: GraphEdge[],
        parent: number,
        checker: ts.TypeChecker,
        node_map: Map<ts.Node, number>
    ): GraphEdge[]{
        let curr_node_id = node_map.get(node);
        
        if(node.getChildCount() == 0){
            let edgeobj : GraphEdge = {'src': parent, 'dst': curr_node_id, 'edge_type': this.edge_type[0]};
            edges.push(edgeobj);
            this.prev_token = curr_node_id;
        }

        //node.forEachChild(n => (this.visit_tree(n, edges, curr_node_id, checker, node_map)));
        for(let i = 0; i<node.getChildCount(); i++){
            edges = this.visit_tree(node.getChildAt(i), edges, this.prev_token, checker, node_map);
        }
        // console.log(edges);
        // console.log(this.edge_name_list(edges, node_map));
        return edges;
    }
}
