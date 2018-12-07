"use strict";
exports.__esModule = true;
var ts = require("typescript");
var label_1 = require("./label");
// Base class to convert ASTs to graphs
var Graph = /** @class */ (function () {
    function Graph(ast_path) {
        this.ast_path = ast_path;
        this.node_id_to_nodeobj_map = new Map();
        this.node_id_to_nodekind_list = [{ 'id': -1, 'ast_type': -1 }];
        this.max_node_count = 0;
    }
    Graph.prototype.ast2graph = function (edge_obj_list) {
        // Currently, this is the source file's path, not AST's.
        var source_pgm = ts.createProgram({
            rootNames: [this.ast_path],
            options: {}
        });
        var checker = source_pgm.getTypeChecker();
        var source_files = source_pgm.getSourceFiles();
        // For each source file provided
        for (var _i = 0, source_files_1 = source_files; _i < source_files_1.length; _i++) {
            var source_file = source_files_1[_i];
            if (!source_file.fileName.endsWith(this.ast_path)) {
                continue;
            }
            // Populate node counters/IDs to every node in the AST
            this.assign_node_counter(source_file);
            // Populate label list for applicable node IDs
            var labels_dict = new Map();
            var labels_list = [];
            label_1.get_all_labels(labels_list, labels_dict, source_file, checker, this.node_id_to_nodeobj_map);
            // Populate multiple edge lists, one for every edge type.
            var all_edges = [];
            for (var i = 0; i < edge_obj_list.length; i++) {
                var edge_list = [];
                edge_list = edge_obj_list[i].visit_tree(source_file, edge_list, -1, checker, this.node_id_to_nodeobj_map);
                all_edges = all_edges.concat(edge_list);
            }
            return [this.node_id_to_nodekind_list, all_edges, labels_list, labels_dict];
        }
    };
    Graph.prototype.ast2feature = function (edge_obj) {
        // Currently, this is the source file's path, not AST's.
        var source_pgm = ts.createProgram({
            rootNames: [this.ast_path],
            options: {}
        });
        var checker = source_pgm.getTypeChecker();
        var source_files = source_pgm.getSourceFiles();
        // For each source file provided
        for (var _i = 0, source_files_2 = source_files; _i < source_files_2.length; _i++) {
            var source_file = source_files_2[_i];
            if (!source_file.fileName.endsWith(this.ast_path)) {
                continue;
            }
            // Populate node counters/IDs to every node in the AST
            this.assign_node_counter(source_file);
            var feature_map = new Map();
            // Get count features
            feature_map = edge_obj.visit_tree_and_parse_features(source_file, feature_map, -1, checker, this.node_id_to_nodeobj_map);
            console.log(feature_map);
            process.exit(0);
        }
    };
    Graph.prototype.assign_node_counter = function (node) {
        var _this = this;
        this.max_node_count++;
        this.node_id_to_nodeobj_map.set(node, this.max_node_count);
        var nodeobj = { 'id': this.max_node_count, 'ast_type': node.kind };
        this.node_id_to_nodekind_list.push(nodeobj);
        node.forEachChild(function (n) { return (_this.assign_node_counter(n)); });
    };
    return Graph;
}());
exports.Graph = Graph;
