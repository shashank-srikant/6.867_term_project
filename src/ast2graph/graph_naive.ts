import * as fs from 'fs';
import * as ts from 'typescript';
import { Graph, GraphNode, GraphEdge, Label } from "./graph";


class GraphNaive extends Graph {
    private max_label_count: number;
    private edge_type: number;
    private output_file: string;

    constructor(ast_path: string, output_file: string){
        super(ast_path);
        this.max_label_count = 1;
        this.edge_type = 1;
	    this.output_file = output_file;
    }

    debug_info(...args: any[]){
        args.forEach(element => {
            console.log(element);
            console.log('--');
        });
    }

    has_label(node: ts.Node, checker: ts.TypeChecker): boolean {
        // Need to distinguish between user defined and inferred types
        try {
            let ty_loc = checker.getTypeAtLocation(node);
            console.log("node: " +  ts.SyntaxKind[node.kind] +
                        "; type: " + ts.TypeFlags[ty_loc.getFlags()] +
                        "; basetype: " + ty_loc.getBaseTypes()
                        );
            if(node.kind == ts.SyntaxKind.Identifier){
                console.log("----")
            }

        }
        catch(e) {
            console.log("oops. No type for " + ts.SyntaxKind[node.kind]);
        }
        return false;
    }

    visit_tree(node: ts.Node, edges: GraphEdge[], labels: Label[],
            parent: number, checker: ts.TypeChecker,
            node_map: Map<ts.Node, number>){
        
        var lbl = get_label(node, checker);
        
        var edgeobj:GraphEdge = {'src': parent, 'dst': curr_node_id, 'edge_type': this.edge_type}

        nodes.push(nodeobj);
        edges.push(edgeobj);

        node.forEachChild(n => (this.visit_tree(n, nodes, edges, labels, curr_node_id, checker, node_map)));
    }

    visit(node: ts.Node, pgm: ts.Program, checker: ts.TypeChecker, node_map: Map<ts.Node, number>): (void) {
        console.log('In GraphNaive.visit ..');

        var edge_list: GraphEdge[] = [];
        var labels_list: Label[] = [];
        this.visit_tree(node, edge_list, labels_list, -1, checker, node_map)

        this.debug_info(edge_list, labels_list,
                         this.label_dict, this.symbol_type_map);
    }
}

// Unit-test
const inputFile = process.argv[2];
const outputFile = process.argv[3] || 'example2.json';
var graph_obj = new GraphNaive(inputFile, outputFile);
graph_obj.ast2graph();
