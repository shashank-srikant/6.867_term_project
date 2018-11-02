import * as fs from 'fs';
import * as ts from 'typescript';
import * as util from 'util';
import { stringify } from 'querystring';

// Base class to convert ASTs to graphs
export abstract class Graph {
    private ast_path: string;
    constructor(ast_path:string){ 
        this.ast_path = ast_path;
    }

    abstract visit (node: ts.Node): void;

    public ast2graph(){
        console.log("in ast_parse")
        // Currently, this is the source file's path, not AST's.
        const source_code = fs.readFileSync(this.ast_path, 'utf-8')
        const source_obj = ts.createSourceFile(this.ast_path, source_code, ts.ScriptTarget.Latest, true);
        
        // util.inspect() allows to dump jsons with circular references in its objects
        // console.log(util.inspect(sourceFile,{compact:true, colors:true}));
        this.visit(source_obj);
        // overload visit for getting different types of edges 
        // the output of `visit` would be passed to to_graph() 
        // to_graph() converts a dict to a graph, and shapes it in the format required for training
        // the output of to_graph() will be pushed to write_graph() to store on disk
    }
}


/*
// Unit-test
const input_file_path = process.argv[2];
var graph_obj = new Graph(input_file_path);
graph_obj.ast2graph();
*/