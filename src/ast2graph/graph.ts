import * as fs from 'fs';
import * as ts from 'typescript';
import * as util from 'util';
import { stringify } from 'querystring';
import {GraphNode, Label} from "./interfaces"
import { get_all_labels } from "./label"

// Base class to convert ASTs to graphs
export class Graph {
    private ast_path: string;
    private out_path: string;
    protected symbol_type_map:[string, string][];
    
    protected node_id_to_nodekind_map: GraphNode[]
    protected node_id_to_nodeobj_map: Map<ts.Node, number>;
    private max_node_count: number;

    constructor(ast_path:string, out_path="../data/"){
        this.ast_path = ast_path;
        this.out_path = out_path;
        this.symbol_type_map = [];
        this.node_id_to_nodeobj_map = new Map();
        this.node_id_to_nodekind_map = [{'id': -1, 'ast_type':-1}];
        this.max_node_count = 0;
    }

    // To be filled in by the inheriting class
    public visit (node: ts.Node, 
                    pgm: ts.Program,
                    checker: ts.TypeChecker,
                    node_map: Map<ts.Node, number>
                    ): void{

    }

    // ...args: (()=>GraphEdge[])[]
    public ast2graph(){
        // Currently, this is the source file's path, not AST's.
        const source_pgm = ts.createProgram({
            rootNames: [this.ast_path],
            options: {
            }
        });
        const checker = source_pgm.getTypeChecker()
        let source_files = source_pgm.getSourceFiles();
        
        // For each source file provided
        for (let source_file of source_files) {
            if (!source_file.fileName.endsWith(this.ast_path)) {
                continue;
            }
            // Populate node counters/IDs to every node in the AST            
            this.assign_node_counter(source_file);
            console.log(this.node_id_to_nodekind_map);

            // Populate label list for applicable node IDs
            let label_dict = new Map();
            let label_map:Label[] = []
            get_all_labels(label_map, label_dict, 
                            source_file, checker, this.node_id_to_nodeobj_map);
            console.log(label_map);
            console.log(label_dict);
            //this.visit(source_file, source_pgm, checker, this.node_id_to_nodeobj_map);
            
            
            /*
            this.print_obj({"nodes": this.node_id_to_nodekind_map,
                            "edges": edge_list,
                            "labels": labels_list,
                            "label_map": this.map2obj(this.label_dict)
                            }, this.output_file);
            */
            console.log('done ast2graph')
        }
    }

    public assign_node_counter(node: ts.Node){
        this.max_node_count++;
        this.node_id_to_nodeobj_map.set(node, this.max_node_count);
        var nodeobj:GraphNode = {'id': this.max_node_count, 'ast_type':node.kind};
        this.node_id_to_nodekind_map.push(nodeobj)
        node.forEachChild(n => (this.assign_node_counter(n)));
    }
}
