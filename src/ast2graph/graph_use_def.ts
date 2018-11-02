
import * as fs from 'fs';
import * as ts from 'typescript';
import { Graph } from "./graph";

class GraphUseDef extends Graph{
    visit(node: ts.Node): void{
        console.log(ts.SyntaxKind[node.kind])
        console.log('--')
        if (ts.isFunctionDeclaration(node)) {
            for (const param of node.parameters) {
            console.log(param.name.getText());
            }
        }
        node.forEachChild(this.visit);
    }
}

// Unit-test
const inputFile = process.argv[2];
var graph_obj = new GraphUseDef(inputFile);
graph_obj.ast2graph();