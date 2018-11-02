
import * as fs from 'fs';
import * as ts from 'typescript';
import { Graph } from "./graph";

class GraphUseDef extends Graph {
    constructor(ast_path:string){
        super(ast_path);
    } 

    visit(node: ts.Node): (void) {
        console.log('In visit..');
        // console.log(node);
        console.log(ts.SyntaxKind[node.kind]);
        console.log('--');
        if (ts.isFunctionDeclaration(node)) {
            for (const param of node.parameters) {
                console.log(param.name.getText());
            }
        }
        node.forEachChild(n => (this.visit(n)));
    }
}

// Unit-test
const inputFile = process.argv[2];
var graph_obj = new GraphUseDef(inputFile);
graph_obj.ast2graph();