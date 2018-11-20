import * as fs from 'fs';
import * as ts from 'typescript';
import { Graph, GraphNode, GraphEdge, Label } from "./graph";

class GraphNaive extends Graph {
    private max_node_count: number;
    private max_label_count: number;
    private edge_type: number;
    private label_dict: Map <string, number>;
    private symbol_type_map:[string, string][];
    
    constructor(ast_path: string){
        super(ast_path);
        this.max_node_count = 0;
        this.max_label_count = 1;
        this.edge_type = 1;
        this.label_dict = new Map();
        this.symbol_type_map = [];
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

    get_type(node: ts.Node, checker: ts.TypeChecker): string {
        let type: string;
        let symbol = checker.getSymbolAtLocation(node);
        if (!symbol) {
            type = "$any$";
        } 
        else {
            let mType = checker.typeToString(checker.getTypeOfSymbolAtLocation(symbol, node));
            if (checker.isUnknownSymbol(symbol) || mType.startsWith('typeof ')) {
                type = '$any$';
            } else if (mType.startsWith('"') || mType.match('[0-9]+')) {
                type = "none";
            } else {
                type = '$' + mType + '$';
                this.symbol_type_map.push([type, symbol.escapedName.toString()])
            }
        }
        return type;
    }

    get_label(node: ts.Node, checker: ts.TypeChecker): [string, number] {
        let type: [string, number];
        if(node.kind == ts.SyntaxKind.VariableDeclaration){
            return [this.get_type((<ts.VariableDeclaration>node).name, checker), 1]
        }

        else if(!ts.isIdentifier(node)){
            type = ["none", 1]
            return type;
        }

        else {
            return [this.get_type(node, checker), 1]
        }
    }

    visit_tree(node: ts.Node, nodes: GraphNode[], edges: GraphEdge[], labels: Label[], parent: number, checker: ts.TypeChecker){
        this.max_node_count++;
        var curr_node_id = this.max_node_count;
        var lbl = this.get_label(node, checker);

        if(lbl[0] != "none"){
            if(!this.label_dict.has(lbl[0])){
                this.label_dict.set(lbl[0], this.max_label_count);
                this.max_label_count++;
            }
            var labelObj:Label = {'node': curr_node_id, 
                                  'label': this.label_dict.get(lbl[0]),
                                  'label_type': lbl[1]
                                };
            labels.push(labelObj);
        }

        var nodeobj:GraphNode = {'id': curr_node_id, 'ast_type':node.kind};
        var edgeobj:GraphEdge = {'src': parent, 'dst': curr_node_id, 'edge_type': this.edge_type}
            
        nodes.push(nodeobj);
        edges.push(edgeobj);

        node.forEachChild(n => (this.visit_tree(n, nodes, edges, labels, curr_node_id, checker)));
    }

    visit(node: ts.Node, pgm: ts.Program, checker: ts.TypeChecker): (void) {
        console.log('In GraphNaive.visit ..');
        
        var node_list: GraphNode[] = [];
        var edge_list: GraphEdge[] = [];
        var labels_list: Label[] = [];
        this.visit_tree(node, node_list, edge_list, labels_list, -1, checker)
        console.log(node_list);
        console.log(edge_list);
        console.log(labels_list);
        console.log(this.label_dict);
        console.log(this.symbol_type_map);
        this.print_obj({"nodes": node_list, 
                        "edge_list": edge_list,
                        "labels": labels_list,
                        "label_map": this.map2obj(this.label_dict)
                       },
                        "example2.json");
    }
}

// Unit-test
const inputFile = process.argv[2];
var graph_obj = new GraphNaive(inputFile);
graph_obj.ast2graph();