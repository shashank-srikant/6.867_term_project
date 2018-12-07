"use strict";
exports.__esModule = true;
var ts = require("typescript");
var utils_1 = require("./utils");
var EdgeFeatures = /** @class */ (function () {
    function EdgeFeatures() {
        this.var_last_define = new Map();
        this.var_last_use = new Map();
    }
    EdgeFeatures.prototype.visit_block = function (node, node_map, use_use, use_def, feature_map) {
        var _this = this;
        var visited_block = false;
        // console.log("***\n"+ts.SyntaxKind[node.kind]+"::"+(node).getText()+"\n***");
        var curr_node_id = node_map.get(node);
        var visitIdentifier = function (name) {
            if (name.kind === ts.SyntaxKind.Identifier) {
                _this.var_last_define.set(name.escapedText.toString(), curr_node_id);
                visited_block = true;
            }
        };
        switch (node.kind) {
            case ts.SyntaxKind.VariableDeclaration: {
                visitIdentifier(node.name);
                break;
            }
            case ts.SyntaxKind.Parameter: {
                visitIdentifier(node.name);
                break;
            }
            case ts.SyntaxKind.BinaryExpression: {
                var is_assign = utils_1.is_assign_op(node.operatorToken.kind);
                var right_node = node.right;
                var right_node_arr = utils_1.getNodes(right_node);
                var left_node = node.left;
                var left_node_arr = utils_1.getNodes(left_node);
                // Variable use
                var var_names_use = Array.from(utils_1.get_block_identifiers(right_node_arr));
                if (!is_assign) {
                    var_names_use = var_names_use.concat(Array.from(utils_1.get_block_identifiers(left_node_arr)));
                }
                for (var i = 0; i < var_names_use.length; i++) {
                    // Should check if var_names_use[i] is in the list of vars defined in fn body?
                    var curr_node_id1 = utils_1.get_node(left_node_arr, var_names_use[i]);
                    var curr_node_id2 = utils_1.get_node(right_node_arr, var_names_use[i]);
                    var curr_node = curr_node_id1.concat(curr_node_id2);
                    curr_node_id = node_map.get(curr_node[0]);
                    // Use-Use edge
                    if (utils_1.pass_null_check(this.var_last_use.get(var_names_use[i]))) {
                        var e1 = utils_1.get_by_value(node_map, this.var_last_use.get(var_names_use[i]));
                        var e2 = utils_1.get_by_value(node_map, curr_node_id);
                        console.log("heyasd there");
                        console.log(this.var_last_use.get(var_names_use[i]));
                        console.log(e1);
                        console.log(e2);
                        process.exit(0);
                    }
                    // Define-use edge
                    if (utils_1.pass_null_check(this.var_last_define.get(var_names_use[i]))) {
                        //this.draw_edge(this.var_last_define.get(var_names_use[i]), curr_node_id, this.use_def_type, use_def);
                    }
                    this.var_last_use.set(var_names_use[i], curr_node_id);
                }
                // Variable defines
                if (is_assign) {
                    var var_names_define = Array.from(utils_1.get_block_identifiers(left_node_arr));
                    for (var i = 0; i < var_names_define.length; i++) {
                        this.var_last_define.set(var_names_define[i], curr_node_id);
                    }
                }
                visited_block = true;
                break;
            }
        }
        if (!visited_block) {
            node.forEachChild(function (n) { return (_this.visit_block(n, node_map, use_use, use_def, feature_map)); });
        }
    };
    EdgeFeatures.prototype.visit_tree_and_parse_features = function (node, feature_map, parent, checker, node_map) {
        switch (node.kind) {
            case ts.SyntaxKind.SourceFile: {
                // All variables used in the program
                //let var_map = get_variable_names(node);
                // Variables used in every function
                for (var i = 0; i < node.statements.length; i++) {
                    if (node.statements[i].kind === ts.SyntaxKind.FunctionDeclaration) {
                        var name_1 = node.statements[i].name;
                        if (name_1 !== undefined && name_1.kind === ts.SyntaxKind.Identifier) {
                            var fn_name = name_1.escapedText.toString();
                            // console.log("in "+fn_name+" ..");
                            //this.visit_block_variables((<ts.SourceFile>node).statements[i], edge_list, node_map, var_map.get(fn_name));
                            var use_use = [];
                            var use_def = [];
                            this.visit_block(node.statements[i], node_map, use_use, use_def, feature_map);
                            //edges = edges.concat(use_use);
                            //edges = edges.concat(use_def);
                        }
                    }
                    else {
                        var use_use = [];
                        var use_def = [];
                        this.visit_block(node, node_map, use_use, use_def, feature_map);
                        //edges = edges.concat(use_use);
                        //edges = edges.concat(use_def);
                        // console.log(edges);
                    }
                }
                break;
            }
            default: {
                // console.log('in default')
                var use_use = [];
                var use_def = [];
                this.visit_block(node, node_map, use_use, use_def, feature_map);
                //edges = edges.concat(use_use);
                //edges = edges.concat(use_def);
            }
        }
        return feature_map;
    };
    return EdgeFeatures;
}());
exports.EdgeFeatures = EdgeFeatures;
