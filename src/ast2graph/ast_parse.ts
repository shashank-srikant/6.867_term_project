import * as fs from 'fs';
import * as ts from 'typescript';
import * as util from 'util';

// Base class to convert ASTs to graphs
class Graph(){
    constructor(ast_path:string){ 
        this.ast_path = ast_path;
    }

    function visit(node: ts.Node) {
        console.log(ts.SyntaxKind[node.kind])
        console.log('--')
        if (ts.isFunctionDeclaration(node)) {
            for (const param of node.parameters) {
              console.log(param.name.getText());
            }
        }
        node.forEachChild(visit);
    }

    function ast_parse(fileName: string, sourceCode: string) {
        console.log("in ast_parse")
        const sourceFile = ts.createSourceFile(fileName, sourceCode, ts.ScriptTarget.Latest, true);
        //console.log(util.inspect(sourceFile,{compact:true, colors:true}));
        visit(sourceFile);
        // overload visit for getting different types of edges 
        // the output of `visit` would be passed to to_graph() 
        // to_graph() converts a dict to a graph, and shapes it in the format required for training
        // the output of to_graph() will be pushed to write_graph() to store on disk
    }
          
    function ast2graph(){
        ast_parse(this.ast_path, fs.readFileSync(this.ast_path, 'utf-8'));
    }
}


// Unit-test
const inputFile = process.argv[2];
var graph_obj = new Graph(inputFile);
graph_obj.ast2graph();