import * as ts from 'typescript';
import { GraphEdge } from "./interfaces";
import { Edge } from "./edge";
import { get_variable_names, getNodes, get_block_identifiers } from "./utils"

export class EdgeUseDef extends Edge {
    protected var_last_use: Map<string, number>;
    protected var_last_define: Map<string, number>;
    protected use_use: GraphEdge[];
    protected use_def: GraphEdge[];
    private use_use_type: number;
    private use_def_type: number;

    constructor(){
        super([2, 3], "Connects an edge between usage and defines of all variables");
        this.use_use_type = 2;
        this.use_def_type = 3;
        this.var_last_define = new Map();
        this.var_last_use = new Map();
        this.use_use = [];
        this.use_def = [];
    } 

    private draw_use_use_edge(parent: number, curr_node_id: number, edge_type: number){
        var edgeobj:GraphEdge = {'src': parent, 'dst': curr_node_id, 'edge_type': edge_type}
        this.use_use.push(edgeobj);
    }

    private draw_use_define_edge(parent: number, curr_node_id: number, edge_type: number){
        var edgeobj:GraphEdge = {'src': parent, 'dst': curr_node_id, 'edge_type': edge_type}
        this.use_def.push(edgeobj);
    }

    private visit_block(node: ts.Node, node_map: Map<ts.Node, number>){
        switch(node.kind){
            case ts.SyntaxKind.VariableDeclaration: {


            }
            case ts.SyntaxKind.BinaryExpression: {
                if  ((<ts.BinaryExpression> (<ts.ExpressionStatement>node).expression).operatorToken.kind == ts.SyntaxKind.EqualsToken)
                    {
                    // Variable uses
                    let curr_node_id = node_map.get(node);
                    let right_node = (<ts.BinaryExpression> (<ts.ExpressionStatement>node).expression).right;
                    let node_use = getNodes(right_node);
                    let var_names_use = Array.from(get_block_identifiers(node_use));
                    for(let i = 0; i<var_names_use.length; i++){
                        // Should check if var_names_use[i] is in the list of vars defined in fn body?
                        this.draw_use_use_edge(this.var_last_use.get(var_names_use[i]), curr_node_id, this.use_use_type);
                        this.var_last_use.set(var_names_use[i], curr_node_id);
                    }
                    
                    process.exit(0)
                    // Variable defines
                    let left_node = (<ts.BinaryExpression> (<ts.ExpressionStatement>node).expression).left;
                    let node_define = getNodes(left_node);
                    let var_names_define = get_block_identifiers(node_define);
                    console.log(node_define);
                    console.log(var_names_define);
                }
                else{

                }
            }
        }
        node.forEachChild(n => (this.visit_block(n, node_map)));
    }

    private visit_block_variables(node: ts.Node, edges: GraphEdge[], node_map: Map<ts.Node, number>, variables: string[]){
        for(let i = 0; i<variables.length; i++){
            this.visit_block(node, node_map);
            edges = edges.concat(this.use_use);
            edges = edges.concat(this.use_def);
        }
    }

    public visit_tree(node: ts.Node, edges: GraphEdge[],
                        parent: number, checker: ts.TypeChecker,
                        node_map: Map<ts.Node, number>){
        
        // All variables used in the program
        let var_map = get_variable_names(node);
        
        // Variables used in every function
        for(let i = 0; i< (<ts.SourceFile>node).statements.length; i++){
            if((<ts.SourceFile>node).statements[i].kind === ts.SyntaxKind.FunctionDeclaration){
                let fn_name = (<ts.FunctionDeclaration>(<ts.SourceFile>node).statements[i]).name.escapedText.toString();
                console.log("in "+fn_name+" ..");
                let edge_list:GraphEdge[] = [];
                this.visit_block_variables((<ts.SourceFile>node).statements[i], edge_list, node_map, var_map.get(fn_name));
                edges = edges.concat(edge_list);
            }
        }
        node.forEachChild(n => (this.visit_tree(n, edges, parent, checker, node_map)));
    }
}