import * as fs from 'fs';
import * as ts from 'typescript';
import { Graph, GraphNode, GraphEdge } from "./graph";

class GraphNaive extends Graph {
    private max_node_count: number;
    private edge_type: number;
    constructor(ast_path:string){
        super(ast_path);
        this.max_node_count = 0;
        this.edge_type = 1;
    } 
    
    visit_tree(node: ts.Node, nodes: GraphNode[], edges: GraphEdge[], parent: number){
        var curr_node_id = this.max_node_count+1;
        var nodeobj:GraphNode = {'id': curr_node_id, 'ast_type':node.kind};
        var edgeobj:GraphEdge = {'src': parent, 'dst': curr_node_id, 'edge_type': this.edge_type}
        nodes.push(nodeobj)
        edges.push(edgeobj)
        node.forEachChild(n => (this.visit_tree(n, nodes, edges, curr_node_id)));
    }

    visit(node: ts.Node): (void) {
        console.log('In GraphNaive.visit ..');
        // console.log(node);
        //console.log(ts.SyntaxKind[node.kind]);
        //console.log('--');
        
        // Stupid typescript and its handling of this   
        var node_list: GraphNode[] = [];
        var edge_list: GraphEdge[] = [];
        this.visit_tree(node, node_list, edge_list, -1)
        console.log(node_list);
        //node.forEachChild(n => (this.visit(n, adj_list)));
    }
}

// Unit-test
const inputFile = process.argv[2];
var graph_obj = new GraphNaive(inputFile);
graph_obj.ast2graph();