import * as ts from 'typescript';
import { GraphEdge } from "./interfaces";
import { Edge } from "./edge";
import { get_node, getNodes, get_block_identifiers, pass_null_check, is_assign_op} from "./utils"

export class EdgeUseDef extends Edge {
    protected var_last_use: Map<string, number>;
    protected var_last_define: Map<string, number>;
    //protected use_use: GraphEdge[];
    //protected use_def: GraphEdge[];
    private use_use_type: number;
    private use_def_type: number;

    constructor(){
        super([2, 3], "Connects an edge between usage and defines of all variables");
        this.use_use_type = 2;
        this.use_def_type = 3;
        this.var_last_define = new Map();
        this.var_last_use = new Map();
        //this.use_use = [];
        //this.use_def = [];
    }

    private draw_edge(parent: number, curr_node_id: number, edge_type: number, edge_list: GraphEdge[]){
        var edgeobj:GraphEdge = {'src': parent, 'dst': curr_node_id, 'edge_type': edge_type}
        edge_list.push(edgeobj);
    }

    private visit_block(node: ts.Node, node_map: Map<ts.Node, number>, 
                        use_use: GraphEdge[], use_def: GraphEdge[]){
        let visited_block = false;
        //console.log("***\n"+ts.SyntaxKind[node.kind]+"::"+(node).getText()+"\n***");
        let curr_node_id = node_map.get(node);
        switch(node.kind){
            case ts.SyntaxKind.VariableDeclaration: {
                this.var_last_define.set((<ts.Identifier>(<ts.VariableDeclaration>node).name).escapedText.toString(), curr_node_id);
                //console.log(this.var_last_define);
                visited_block = true;
                break;
            }
            case ts.SyntaxKind.Parameter:{
                this.var_last_define.set((<ts.Identifier>(<ts.ParameterDeclaration>node).name).escapedText.toString(), curr_node_id);
                //console.log(this.var_last_define);
                visited_block = true;
                break;
            }
            case ts.SyntaxKind.BinaryExpression: {
                let is_assign = is_assign_op((<ts.BinaryExpression> node).operatorToken.kind);

                let right_node = (<ts.BinaryExpression>node).right;
                let right_node_arr = getNodes(right_node);
                
                let left_node = (<ts.BinaryExpression> node).left;
                let left_node_arr = getNodes(left_node);
                
                // Variable use
                let var_names_use = Array.from(get_block_identifiers(right_node_arr));
                if(!is_assign){
                    var_names_use = var_names_use.concat(Array.from(get_block_identifiers(left_node_arr)))
                }
                for(let i = 0; i<var_names_use.length; i++){
                    // Should check if var_names_use[i] is in the list of vars defined in fn body?
                    let curr_node_id1 = get_node(left_node_arr, var_names_use[i]);
                    let curr_node_id2 = get_node(right_node_arr, var_names_use[i]);
                    let curr_node = curr_node_id1.concat(curr_node_id2);
                    curr_node_id = node_map.get(curr_node[0]);
                    // Use-Use edge
                    if(pass_null_check(this.var_last_use.get(var_names_use[i]))){
                        this.draw_edge(this.var_last_use.get(var_names_use[i]), curr_node_id, this.use_use_type, use_use);
                    }
                    
                    // Define-use edge
                    if(pass_null_check(this.var_last_define.get(var_names_use[i]))){
                        this.draw_edge(this.var_last_define.get(var_names_use[i]), curr_node_id, this.use_def_type, use_def);
                    }

                    this.var_last_use.set(var_names_use[i], curr_node_id);
                }
                // Variable defines
                if(is_assign){
                    let var_names_define = Array.from(get_block_identifiers(left_node_arr));
                    for(let i = 0; i<var_names_define.length; i++){
                        this.var_last_define.set(var_names_define[i], curr_node_id);
                    }
                }
                /*
                console.log("\nAfter\n");
                console.log(var_names_use);
                console.log(this.var_last_use);
                console.log(this.var_last_define);
                console.log(use_use);
                console.log(use_def);
                console.log("================");
                */
                visited_block = true;
                break;
            }
        }
        if(!visited_block){
            node.forEachChild(n => (this.visit_block(n, node_map, use_use, use_def)));
        }
    }

    public visit_tree(node: ts.Node, edges: GraphEdge[],
                        parent: number, checker: ts.TypeChecker,
                        node_map: Map<ts.Node, number>):GraphEdge[]{
        
        let edges_all: GraphEdge[] = [];
        switch(node.kind){
            case ts.SyntaxKind.SourceFile: {
                // All variables used in the program
                //let var_map = get_variable_names(node);
                
                // Variables used in every function
                for(let i = 0; i< (<ts.SourceFile>node).statements.length; i++){
                    if((<ts.SourceFile>node).statements[i].kind === ts.SyntaxKind.FunctionDeclaration){
                        let fn_name = (<ts.FunctionDeclaration>(<ts.SourceFile>node).statements[i]).name.escapedText.toString();
                        console.log("in "+fn_name+" ..");
                        //this.visit_block_variables((<ts.SourceFile>node).statements[i], edge_list, node_map, var_map.get(fn_name));
                        let use_use: GraphEdge[] = [];
                        let use_def: GraphEdge[] = [];
                        this.visit_block((<ts.SourceFile>node).statements[i], node_map, use_use, use_def);
                        edges = edges.concat(use_use);
                        edges = edges.concat(use_def);
                    }
                    else{
                        let use_use: GraphEdge[] = [];
                        let use_def: GraphEdge[] = [];
                        this.visit_block(node, node_map, use_use, use_def);
                        edges = edges.concat(use_use);
                        edges = edges.concat(use_def);
                        //console.log(edges);
                    }
                }
                break;
            }

            default: {
                console.log('in default')
                let use_use: GraphEdge[] = [];
                let use_def: GraphEdge[] = [];
                this.visit_block(node, node_map, use_use, use_def);
                edges = edges.concat(use_use);
                edges = edges.concat(use_def);
            }
        }
        return edges
    }
}