import * as fs from 'fs';
import * as ts from 'typescript';
import { Graph } from "./graph";

class GraphUseDef extends Graph {
    constructor(ast_path:string){
        super(ast_path);
    } 

    visit(node: ts.Node, var_names: string[]): (void) {
        //console.log('In visit..');
        // console.log(node);
        //console.log(ts.SyntaxKind[node.kind]);
        //console.log('--');

        // Stupid typescript and its handling of this
        node.forEachChild(n => (this.visit(n, var_names)));
    }
}

// Unit-test
const inputFile = process.argv[2];
var graph_obj = new GraphUseDef(inputFile);
graph_obj.ast2graph();