import * as ts from 'typescript';
import { GraphEdge } from "./interfaces";
import { Edge } from "./edge";
import { get_variable_names, getNodes, get_block_identifiers } from "./utils"

export class EdgeUseDef extends Edge {
    constructor(){
        super(2, "Connects an edge between usage and defines of all variables");
    } 

    private visit_block(node: ts.Node, edges: GraphEdge[], node_map: Map<ts.Node, number>, var_name: string){
        switch(node.kind){
            case ts.SyntaxKind.VariableDeclaration: {


            }
            case ts.SyntaxKind.ExpressionStatement: {
                if ((<ts.ExpressionStatement>node).expression
                    && (<ts.ExpressionStatement>node).expression.kind === ts.SyntaxKind.BinaryExpression
                    && 
                    (<ts.BinaryExpression> (<ts.ExpressionStatement>node).expression).operatorToken.kind == ts.SyntaxKind.EqualsToken)
                    {
                    let left_node = (<ts.BinaryExpression> (<ts.ExpressionStatement>node).expression).left;
                    let right_node = (<ts.BinaryExpression> (<ts.ExpressionStatement>node).expression).right;
                    let node_define = getNodes(left_node);
                    console.log(node_define);
                    let var_names_define = get_block_identifiers(node_define);
                    console.log(var_names_define);
                    process.exit(0)
                }
            }
        }
        node.forEachChild(n => (this.visit_block(n, edges, node_map, var_name)));
    }

    private visit_block_variables(node: ts.Node, edges: GraphEdge[], node_map: Map<ts.Node, number>, variables: string[]){
        for(let i = 0; i<variables.length; i++){
            let edge_list: GraphEdge[] = [];
            this.visit_block(node, edge_list, node_map, variables[i]);
            edges = edges.concat(edge_list)
        }
    }

    public visit_tree(node: ts.Node, edges: GraphEdge[],
                        parent: number, checker: ts.TypeChecker,
                        node_map: Map<ts.Node, number>){
        
        let var_map = get_variable_names(node);
        for(let i = 0; i< (<ts.SourceFile>node).statements.length; i++){
            if((<ts.SourceFile>node).statements[i].kind === ts.SyntaxKind.FunctionDeclaration){
                let fn_name = (<ts.FunctionDeclaration>(<ts.SourceFile>node).statements[i]).name.escapedText.toString();
                console.log("in "+fn_name+" ..");
                let edge_list:GraphEdge[] = [];
                this.visit_block_variables((<ts.SourceFile>node).statements[i], edge_list, node_map, var_map.get(fn_name));
            }
        }
        let curr_node_id = node_map.get(node);
        var edgeobj:GraphEdge = {'src': parent, 'dst': curr_node_id, 'edge_type': this.edge_type}
        edges.push(edgeobj);
        node.forEachChild(n => (this.visit_tree(n, edges, curr_node_id, checker, node_map)));
    }
}