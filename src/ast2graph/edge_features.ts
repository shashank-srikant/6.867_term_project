import * as ts from 'typescript';
import { GraphEdge } from "./interfaces";
import { get_node, getNodes, get_block_identifiers, pass_null_check, is_assign_op, get_common_path} from "./utils"

export class EdgeFeatures{
    protected var_last_use: Map<string, string[]>;
    protected var_last_define: Map<string, string[]>;
    
    constructor(){
        this.var_last_define = new Map();
        this.var_last_use = new Map(); 
    }

    private visit_block(
        node: ts.Node,
        node_map: Map<ts.Node, number>,
        use_use: GraphEdge[], 
        use_def: GraphEdge[],
        feature_map: Map<number, string[]>,
        node_path: string[]
    ){
        let visited_block = false;
        // console.log("***\n"+ts.SyntaxKind[node.kind]+"::"+(node).getText()+"\n***");
        let curr_node_id = node_map.get(node);
        node_path = node_path.concat(node.kind.toString());

        let visitIdentifier = (name: ts.Node) => {
            if (name.kind === ts.SyntaxKind.Identifier) {
                this.var_last_define.set((<ts.Identifier> name).escapedText.toString(), node_path);
                visited_block = true;
            }
        };
        
        switch(node.kind){
            case ts.SyntaxKind.VariableDeclaration: {
                visitIdentifier((<ts.VariableDeclaration> node).name);
                break;
            }
            case ts.SyntaxKind.Parameter:{
                visitIdentifier((<ts.ParameterDeclaration> node).name);
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
                        // Currently not implemented
                        //process.exit(0);
                    }

                    // Define-use edge
                    if(pass_null_check(this.var_last_define.get(var_names_use[i]))){
                        let path = get_common_path(this.var_last_define.get(var_names_use[i]), node_path);
                        feature_map.set(curr_node_id, path);
                        //console.log("variable: "+var_names_use[i]);
                        //console.log(e1);
                        //console.log('--');
                        
                    }

                    this.var_last_use.set(var_names_use[i], node_path);
                }
                // Variable defines
                if(is_assign){
                    let var_names_define = Array.from(get_block_identifiers(left_node_arr));
                    for(let i = 0; i<var_names_define.length; i++){
                        this.var_last_define.set(var_names_define[i], node_path);
                    }
                }
                visited_block = true;
                break;
            }
        }
        if(!visited_block){
            var node_children = Array.from(node.getChildren());
            for(let i = 0; i<node_children.length; i++){
                this.visit_block(node_children[i], node_map, use_use, use_def, feature_map, node_path);
            }
            //node.forEachChild(n => (this.visit_block(n, node_map, use_use, use_def, feature_map, node_path)));
        }
    }

    public visit_tree_and_parse_features(
        node: ts.Node,
        feature_map: Map<number, string[]>,
        parent: number,
        checker: ts.TypeChecker,
        node_map: Map<ts.Node, number>
    ): Map<number, string[]>{
        switch(node.kind){
            case ts.SyntaxKind.SourceFile: {
                // All variables used in the program
                //let var_map = get_variable_names(node);

                // Variables used in every function
                for(let i = 0; i< (<ts.SourceFile>node).statements.length; i++){
                    if((<ts.SourceFile>node).statements[i].kind === ts.SyntaxKind.FunctionDeclaration){
                        let name = (<ts.FunctionDeclaration>(<ts.SourceFile>node).statements[i]).name;
                        if (name !== undefined && name.kind === ts.SyntaxKind.Identifier) {
                                        let fn_name = name.escapedText.toString();
                                        // console.log("in "+fn_name+" ..");
                                        //this.visit_block_variables((<ts.SourceFile>node).statements[i], edge_list, node_map, var_map.get(fn_name));
                                        let use_use: GraphEdge[] = [];
                                        let use_def: GraphEdge[] = [];
                                        let node_path: string[] = [];
                                        this.visit_block((<ts.SourceFile>node).statements[i], node_map, use_use, use_def, feature_map, node_path);
                                        //edges = edges.concat(use_use);
                                        //edges = edges.concat(use_def);
                        }
                    }
                    else{
                        let use_use: GraphEdge[] = [];
                        let use_def: GraphEdge[] = [];
                        let node_path: string[] = [];
                        this.visit_block(node, node_map, use_use, use_def, feature_map, node_path);
                        //edges = edges.concat(use_use);
                        //edges = edges.concat(use_def);
                        // console.log(edges);
                    }
                }
                break;
            }

            default: {
                // console.log('in default')
                let use_use: GraphEdge[] = [];
                let use_def: GraphEdge[] = [];
                let node_path: string[] = [];
                this.visit_block(node, node_map, use_use, use_def, feature_map, node_path);
                //edges = edges.concat(use_use);
                //edges = edges.concat(use_def);
            }
        }
        return feature_map;
    }
}
