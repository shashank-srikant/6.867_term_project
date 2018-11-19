import * as fs from 'fs';
import * as ts from 'typescript';
import * as util from 'util';
import { stringify } from 'querystring';

export interface GraphNode {
    "id": number, 
    "ast_type": number
}

export interface GraphEdge {
    "src": GraphNode['id'],
    "dst": GraphNode['id'],
    "edge_type": number
}

export interface Label {
    "node": GraphNode['id'],
    "label": number
}

// Base class to convert ASTs to graphs
export abstract class Graph {
    private ast_path: string;
    constructor(ast_path:string){ 
        this.ast_path = ast_path;
    }

    abstract visit (node: ts.Node, pgm: ts.Program, checker: ts.TypeChecker): void;


    public get_variable_names(node: ts.Node, pgm: ts.Program, checker:ts.TypeChecker): void{
        var nodes: ts.Node[] = [];
        function getNodes(sf: ts.Node): ts.Node[] {
            var nodes: ts.Node[] = [];
            function allNodes(n: ts.Node) {
                ts.forEachChild(n, n => { nodes.push(n); allNodes(n); return false; })
            };
            allNodes(sf);
            return nodes;
        }
        var id_nodes = getNodes(node).filter(n => 
                                (n.kind === ts.SyntaxKind.Identifier
                                ));
        var names = id_nodes.map(n => <string>((<ts.Identifier>n).escapedText));
        function decl_flags(n:ts.Identifier){
            return checker.getSymbolAtLocation(n).getDeclarations();
        }
        console.log("**")
        console.log(util.inspect(id_nodes,{compact:true}));
        console.log("&&")
        console.log(names)
        //console.log(id_nodes_symbolobj)
        //var names = id_nodes.map(n =>  decl_flags((<ts.Identifier>n)));
        //var decls = names.map(n => n.getDeclarations());
        //console.log(names);
        //return names
        //return node.forEachChild(n => (this.get_variable_names(n)));
    }
    
    public ast2graph(){
        // Currently, this is the source file's path, not AST's.
        const source_pgm = ts.createProgram({
            rootNames: [this.ast_path],
            options: {
            }
        });
        const checker = source_pgm.getTypeChecker()
        let source_files = source_pgm.getSourceFiles();
        for (let source_file of source_files) {
            if (!source_file.fileName.endsWith(this.ast_path)) {
                continue;
            }
            const var_names = this.get_variable_names((<ts.Node>source_file), source_pgm, checker);
            //this.visit(source_file, source_pgm, checker);
            console.log('finished var names')
        }
    
        // util.inspect() allows to dump jsons with circular references in its objects
        // console.log(util.inspect(sourceFile,{compact:true, colors:true}));

        // overload visit for getting different types of edges
        // the output of `visit` would be passed to to_graph()
        // to_graph() converts a dict to a graph, and shapes it in the format required for training
        // the output of to_graph() will be pushed to write_graph() to store on disk
    }


    public print_obj(obj: any, filename = "out.log"){
        fs.writeFile(filename , JSON.stringify(obj), function(err) {
            if (err) {
                console.log(err);
            }
        });
    }
}


/*
// Unit-test
const input_file_path = process.argv[2];
var graph_obj = new Graph(input_file_path);
graph_obj.ast2graph();

const source_pgm = ts.createProgram(path)
let source_files = source_pgm.getSourceFiles();
for (let node of source_files){
    if (!node.fileName.endsWith(path)) {
        console.log(node.id)
    }
}
*/