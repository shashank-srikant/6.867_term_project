import * as ts from 'typescript';
import { GraphEdge } from "./interfaces";
import { Edge } from "./edge";
import { get_variable_names, getNodes, get_block_identifiers, pass_null_check, is_assign_op} from "./utils"

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

    private draw_use_use_edge(parent: number, curr_node_id: number, edge_type: number, use_use: GraphEdge[]){
        var edgeobj:GraphEdge = {'src': parent, 'dst': curr_node_id, 'edge_type': edge_type}
        use_use.push(edgeobj);
    }

    private draw_use_define_edge(parent: number, curr_node_id: number, edge_type: number, use_def: GraphEdge[]){
        var edgeobj:GraphEdge = {'src': parent, 'dst': curr_node_id, 'edge_type': edge_type}
        use_def.push(edgeobj);
    }

    private visit_block(node: ts.Node, node_map: Map<ts.Node, number>, 
                        use_use: GraphEdge[], use_def: GraphEdge[]){
        let visited_block = false;
        console.log("***\n"+ts.SyntaxKind[node.kind]+"::"+(node).getText()+"\n***");
        switch(node.kind){
            case ts.SyntaxKind.VariableDeclaration: {
                console.log('Declare');
                break;
            }
            case ts.SyntaxKind.BinaryExpression: {
                let is_assign = is_assign_op((<ts.BinaryExpression> node).operatorToken.kind);

                let curr_node_id = node_map.get(node);
                
                let right_node = (<ts.BinaryExpression>node).right;
                let right_node_arr = getNodes(right_node);
                
                let left_node = (<ts.BinaryExpression> node).left;
                let left_node_arr = getNodes(left_node);
                
                // Variable use
                let var_names_use = Array.from(get_block_identifiers(right_node_arr));
                if(!is_assign){
                    var_names_use.concat(Array.from(get_block_identifiers(left_node_arr)))
                }

                console.log("\nBefore\n");
                console.log(var_names_use);
                console.log(this.var_last_use);
                console.log(use_use);
                for(let i = 0; i<var_names_use.length; i++){
                    // Should check if var_names_use[i] is in the list of vars defined in fn body?
                    if(pass_null_check(this.var_last_use.get(var_names_use[i]))){
                        this.draw_use_use_edge(this.var_last_use.get(var_names_use[i]), curr_node_id, this.use_use_type, use_use);
                    }
                    this.var_last_use.set(var_names_use[i], curr_node_id);
                }
                console.log("\nAfter\n");
                console.log(var_names_use);
                console.log(this.var_last_use);
                console.log(use_use);
                console.log("================")
                
                // Variable defines
                if(is_assign){
                    
                }
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
                        node_map: Map<ts.Node, number>){
        
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
                }
                break;
            }

            default: {
                let use_use: GraphEdge[] = [];
                let use_def: GraphEdge[] = [];
                this.visit_block(node, node_map, use_use, use_def);
                edges = edges.concat(use_use);
                edges = edges.concat(use_def);
            }
        }
    }
}