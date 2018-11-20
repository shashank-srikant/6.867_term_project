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
    "label": number,
    "label_type": number 
    //to signify whether a declaration stmnt type (0), or other (1)
}

// Base class to convert ASTs to graphs
export abstract class Graph {
    private ast_path: string;
    private out_path: string;
    protected label_dict: Map <string, number>;
    protected symbol_type_map:[string, string][];

    constructor(ast_path:string, out_path="../data/"){
        this.ast_path = ast_path;
        this.out_path = out_path;
        this.label_dict = new Map();
        this.symbol_type_map = [];
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
                                (n.kind === ts.SyntaxKind.VariableDeclaration)).filter(n =>
					  (<ts.VariableDeclaration>n).name.kind === ts.SyntaxKind.Identifier
					 );
        var names = id_nodes.map(n => <string>((<ts.Identifier>(<ts.VariableDeclaration>n).name).text));
       
        //console.log(id_nodes_symbolobj)
        //var names = id_nodes.map(n =>  decl_flags((<ts.Identifier>n)));
        //var decls = names.map(n => n.getDeclarations());
        console.log('BEGIN NAMES');
        console.log(names);
        console.log('END NAMES');
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
            this.visit(source_file, source_pgm, checker);
            console.log('finished var names')
        }

        // util.inspect() allows to dump jsons with circular references in its objects
        // console.log(util.inspect(sourceFile,{compact:true, colors:true}));

        // overload visit for getting different types of edges
        // the output of `visit` would be passed to to_graph()
        // to_graph() converts a dict to a graph, and shapes it in the format required for training
        // the output of to_graph() will be pushed to write_graph() to store on disk
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
                console.log('in here');
            } else if (mType.startsWith("\"") || mType.match('[0-9]+')) {
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
    
    public print_obj(obj: any, filename = "out.log"){
        fs.writeFile(this.out_path+filename , JSON.stringify(obj), function(err) {
            if (err) {
                console.log(err);
            }
        });
    }

    public map2obj(aMap:Map<string, number>){
        const obj:{[key:string]: number} = {};
        aMap.forEach ((v,k) => { obj[k] = v });
        return obj;
    }
}
