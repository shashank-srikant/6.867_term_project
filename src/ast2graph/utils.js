"use strict";
exports.__esModule = true;
var fs = require("fs");
var ts = require("typescript");
var path = require("path");
function is_assign_op(op) {
    if (op === ts.SyntaxKind.EqualsToken || op === ts.SyntaxKind.PlusEqualsToken || op === ts.SyntaxKind.MinusEqualsToken || op === ts.SyntaxKind.AsteriskAsteriskEqualsToken || op === ts.SyntaxKind.AsteriskEqualsToken || op === ts.SyntaxKind.SlashEqualsToken || op === ts.SyntaxKind.PercentEqualsToken || op === ts.SyntaxKind.AmpersandEqualsToken || op === ts.SyntaxKind.BarEqualsToken || op === ts.SyntaxKind.CaretEqualsToken || op === ts.SyntaxKind.LessThanLessThanEqualsToken || op === ts.SyntaxKind.GreaterThanGreaterThanGreaterThanEqualsToken || op === ts.SyntaxKind.GreaterThanGreaterThanEqualsToken) {
        return true;
    }
    else {
        return false;
    }
}
exports.is_assign_op = is_assign_op;
function nodekind2str(path) {
    return path.map(function (val) { return ts.SyntaxKind[parseInt(val)]; });
}
exports.nodekind2str = nodekind2str;
function get_node(node, varname) {
    var node_list = [];
    var id_nodes = node.filter(function (n) { return n.kind === ts.SyntaxKind.Identifier; });
    for (var i = 0; i < id_nodes.length; i++) {
        if (id_nodes[i].escapedText.toString() == varname) {
            node_list.push(id_nodes[i]);
        }
    }
    return node_list;
}
exports.get_node = get_node;
function get_common_path(path1, path2) {
    // Assuming defines happen before usages
    console.log(nodekind2str(path1));
    console.log(nodekind2str(path2));
    for (var i = 0; i < Math.min(path1.length, path2.length); i++) {
        if (path1[i] !== path2[i]) {
            return nodekind2str(path1.slice(i - 1, path1.length).reverse().concat(path2.slice(i, path2.length)));
        }
    }
    return ["UNK"];
}
exports.get_common_path = get_common_path;
function get_by_value(map, searchValue) {
    console.log(searchValue);
    for (var _i = 0, _a = Array.from(map.entries()); _i < _a.length; _i++) {
        var entry = _a[_i];
        console.log(entry[1]);
        if (entry[1] === searchValue)
            return entry[0];
    }
}
exports.get_by_value = get_by_value;
function print_obj(obj, out_path, filename) {
    if (filename === void 0) { filename = "out.log"; }
    fs.writeFileSync(path.join(out_path, filename), JSON.stringify(obj));
}
exports.print_obj = print_obj;
function pass_null_check(value) {
    return value !== undefined && value !== null;
}
exports.pass_null_check = pass_null_check;
function map2obj(aMap) {
    var obj = {};
    aMap.forEach(function (v, k) { obj[k] = v; });
    return obj;
}
exports.map2obj = map2obj;
function get_block_identifiers(node) {
    var id_nodes = node.filter(function (n) { return n.kind === ts.SyntaxKind.Identifier; });
    var names = id_nodes.map(function (n) { return (n).escapedText.toString(); });
    var names_set = new Set(names);
    return names_set;
}
exports.get_block_identifiers = get_block_identifiers;
function get_block_variable_names_in_decl(node) {
    var id_nodes = node.filter(function (n) { return (n.kind === ts.SyntaxKind.VariableDeclaration); }).filter(function (n) { return n.name.kind === ts.SyntaxKind.Identifier; });
    var names = id_nodes.map(function (n) { return (n.name.text); });
    var names_set = new Set(names);
    return names_set;
}
exports.get_block_variable_names_in_decl = get_block_variable_names_in_decl;
function get_block_variable_names_in_fn(node) {
    var names_fn = [];
    // console.log(node);
    process.exit(0);
    var all_nodes = getNodes(node);
    var fn_params = all_nodes.filter(function (n) { return (n.kind === ts.SyntaxKind.FunctionDeclaration); });
    for (var i = 0; i < fn_params.length; i++) {
        var names2 = [];
        var li_param = fn_params[i].parameters;
        for (var j = 0; j < li_param.length; j++) {
            names2.push(li_param[j].name.escapedText.toString());
        }
        var fn_nodes = getNodes(fn_params[i]);
        var names3 = get_block_variable_names_in_decl(fn_nodes);
        names2 = names2.concat(Array.from(names3));
        names_fn = names_fn.concat(names2);
    }
    var names_fn_set = new Set(names_fn);
    return names_fn_set;
}
exports.get_block_variable_names_in_fn = get_block_variable_names_in_fn;
function getNodes(sf) {
    var nodes = [];
    function allNodes(n) {
        ts.forEachChild(n, function (n) { nodes.push(n); allNodes(n); return false; });
    }
    ;
    if (sf.getChildCount() == 0) {
        nodes.push(sf);
    }
    else {
        allNodes(sf);
    }
    return nodes;
}
exports.getNodes = getNodes;
// Junk function. Here to test out AST structure.
function get_variable_names(node) {
    var all_names = new Map();
    // Get names of variables used in the script's body
    var body = node.statements.filter(function (n) { return n.kind !== ts.SyntaxKind.FunctionDeclaration; });
    var names1 = [];
    for (var i = 0; i < body.length; i++) {
        var all_nodes_1 = getNodes(body[i]);
        var names_set = get_block_variable_names_in_decl(all_nodes_1);
        names1 = names1.concat(Array.from(names_set));
    }
    all_names.set("body", names1);
    // Get per-function variable names
    var all_nodes = getNodes(node);
    var fn_params = all_nodes.filter(function (n) { return (n.kind === ts.SyntaxKind.FunctionDeclaration); });
    for (var i = 0; i < fn_params.length; i++) {
        var names2 = [];
        var li_param = fn_params[i].parameters;
        for (var j = 0; j < li_param.length; j++) {
            names2.push(li_param[j].name.escapedText.toString());
        }
        var fn_nodes = getNodes(fn_params[i]);
        var names3 = get_block_variable_names_in_decl(fn_nodes);
        var names_fn = names2.concat(Array.from(names3));
        // console.log((<ts.FunctionDeclaration>fn_params[i]).name.escapedText.toString());
        all_names.set(fn_params[i].name.escapedText.toString(), names_fn);
    }
    //let all_names = names1.concat(names2);
    // console.log(all_names);
    return all_names;
}
exports.get_variable_names = get_variable_names;
