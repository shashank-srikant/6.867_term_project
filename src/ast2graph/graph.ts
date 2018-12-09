import * as ts from 'typescript';
import {GraphNode, Label, GraphEdge} from "./interfaces"
import { get_all_labels } from "./label"
import { Edge } from "./edge"
import { EdgeFeatures } from "./edge_features"

// Base class to convert ASTs to graphs
export class Graph {
    private ast_path: string;
    protected node_id_to_nodekind_list: GraphNode[]
    protected node_id_to_nodeobj_map: Map<ts.Node, number>;
    private max_node_count: number;
    private nodePrinter: ts.Printer;

    constructor(ast_path:string) {
        this.ast_path = ast_path;
        this.node_id_to_nodeobj_map = new Map();
        this.node_id_to_nodekind_list = [{'id': -1, 'ast_type':-1, "token": "root"}];
        this.max_node_count = 0;
	this.nodePrinter = ts.createPrinter();
    }

    public ast2graph(edge_obj_list:Edge[]):[GraphNode[], GraphEdge[], Label[], Map <string, number>]{
        // Currently, this is the source file's path, not AST's.
        const source_pgm = ts.createProgram({
            rootNames: [this.ast_path],
            options: {}
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

            // Populate label list for applicable node IDs
            let labels_dict = new Map();
            let labels_list:Label[] = [];
            get_all_labels(labels_list, labels_dict, source_file, checker, this.node_id_to_nodeobj_map);
            
            // Populate multiple edge lists, one for every edge type.
            let all_edges:GraphEdge[] = [];
            for(let i=0; i<edge_obj_list.length; i++) {
                let edge_list:GraphEdge[] = [];
                edge_list = edge_obj_list[i].visit_tree(source_file, edge_list, -1, checker, this.node_id_to_nodeobj_map);
                all_edges = all_edges.concat(edge_list);
            }

            return [this.node_id_to_nodekind_list, all_edges, labels_list, labels_dict];
        }
    }

    public ast2feature(edge_obj: EdgeFeatures):[Map<number, string[]>, Label[]] {
        // Currently, this is the source file's path, not AST's.
        const source_pgm = ts.createProgram({
            rootNames: [this.ast_path],
            options: {}
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

            // Populate label list for applicable node IDs
            let labels_dict = new Map();
            let labels_list:Label[] = [];
            get_all_labels(labels_list, labels_dict, source_file, checker, this.node_id_to_nodeobj_map);
            let feature_map = new Map<number, string[]>();
            // Get count features
            feature_map = edge_obj.visit_tree_and_parse_features(source_file, feature_map, -1, checker, this.node_id_to_nodeobj_map);

            console.log(labels_list);
            console.log(feature_map);

            return [feature_map, labels_list];
        }
    }

    public assign_node_counter(node: ts.Node) {
        this.max_node_count++;
        this.node_id_to_nodeobj_map.set(node, this.max_node_count);
        var tok = ts.SyntaxKind[node.kind];
        var nodeobj:GraphNode = {'id': this.max_node_count, 'ast_type':node.kind, 'token': tok};
        this.node_id_to_nodekind_list.push(nodeobj);
        for(let i = 0; i<node.getChildCount(); i++){
            this.assign_node_counter(node.getChildAt(i));
        }
    }
}
