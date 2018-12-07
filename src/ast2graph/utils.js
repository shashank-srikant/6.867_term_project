"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const fs = require("fs");
const ts = require("typescript");
function is_assign_op(op) {
    if (op === ts.SyntaxKind.EqualsToken || op === ts.SyntaxKind.PlusEqualsToken || op === ts.SyntaxKind.MinusEqualsToken || op === ts.SyntaxKind.AsteriskAsteriskEqualsToken || op === ts.SyntaxKind.AsteriskEqualsToken || op === ts.SyntaxKind.SlashEqualsToken || op === ts.SyntaxKind.PercentEqualsToken || op === ts.SyntaxKind.AmpersandEqualsToken || op === ts.SyntaxKind.BarEqualsToken || op === ts.SyntaxKind.CaretEqualsToken || op === ts.SyntaxKind.LessThanLessThanEqualsToken || op === ts.SyntaxKind.GreaterThanGreaterThanGreaterThanEqualsToken || op === ts.SyntaxKind.GreaterThanGreaterThanEqualsToken) {
        return true;
    }
    else {
        return false;
    }
}
exports.is_assign_op = is_assign_op;
function get_node(node, varname) {
    let node_list = [];
    var id_nodes = node.filter(n => n.kind === ts.SyntaxKind.Identifier);
    for (let i = 0; i < id_nodes.length; i++) {
        if (id_nodes[i].escapedText.toString() == varname) {
            node_list.push(id_nodes[i]);
        }
    }
    return node_list;
}
exports.get_node = get_node;
function print_obj(obj, out_path, filename = "out.log") {
    fs.writeFile(out_path + filename, JSON.stringify(obj), function (err) {
        if (err) {
            console.log(err);
        }
    });
}
exports.print_obj = print_obj;
function pass_null_check(value) {
    return value !== undefined && value !== null;
}
exports.pass_null_check = pass_null_check;
function map2obj(aMap) {
    const obj = {};
    aMap.forEach((v, k) => { obj[k] = v; });
    return obj;
}
exports.map2obj = map2obj;
function get_block_identifiers(node) {
    var id_nodes = node.filter(n => n.kind === ts.SyntaxKind.Identifier);
    var names = id_nodes.map(n => (n).escapedText.toString());
    let names_set = new Set(names);
    return names_set;
}
exports.get_block_identifiers = get_block_identifiers;
function get_block_variable_names_in_decl(node) {
    var id_nodes = node.filter(n => (n.kind === ts.SyntaxKind.VariableDeclaration)).filter(n => n.name.kind === ts.SyntaxKind.Identifier);
    var names = id_nodes.map(n => (n.name.text));
    let names_set = new Set(names);
    return names_set;
}
exports.get_block_variable_names_in_decl = get_block_variable_names_in_decl;
function get_block_variable_names_in_fn(node) {
    let names_fn = [];
    console.log(node);
    process.exit(0);
    let all_nodes = getNodes(node);
    var fn_params = all_nodes.filter(n => (n.kind === ts.SyntaxKind.FunctionDeclaration));
    for (let i = 0; i < fn_params.length; i++) {
        let names2 = [];
        let li_param = fn_params[i].parameters;
        for (let j = 0; j < li_param.length; j++) {
            names2.push(li_param[j].name.escapedText.toString());
        }
        let fn_nodes = getNodes(fn_params[i]);
        let names3 = get_block_variable_names_in_decl(fn_nodes);
        names2 = names2.concat(Array.from(names3));
        names_fn = names_fn.concat(names2);
    }
    let names_fn_set = new Set(names_fn);
    return names_fn_set;
}
exports.get_block_variable_names_in_fn = get_block_variable_names_in_fn;
function getNodes(sf) {
    var nodes = [];
    function allNodes(n) {
        ts.forEachChild(n, n => { nodes.push(n); allNodes(n); return false; });
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
function get_variable_names(node) {
    let all_names = new Map();
    var body = node.statements.filter(n => n.kind !== ts.SyntaxKind.FunctionDeclaration);
    let names1 = [];
    for (let i = 0; i < body.length; i++) {
        let all_nodes = getNodes(body[i]);
        let names_set = get_block_variable_names_in_decl(all_nodes);
        names1 = names1.concat(Array.from(names_set));
    }
    all_names.set("body", names1);
    let all_nodes = getNodes(node);
    var fn_params = all_nodes.filter(n => (n.kind === ts.SyntaxKind.FunctionDeclaration));
    for (let i = 0; i < fn_params.length; i++) {
        let names2 = [];
        let li_param = fn_params[i].parameters;
        for (let j = 0; j < li_param.length; j++) {
            names2.push(li_param[j].name.escapedText.toString());
        }
        let fn_nodes = getNodes(fn_params[i]);
        let names3 = get_block_variable_names_in_decl(fn_nodes);
        let names_fn = names2.concat(Array.from(names3));
        console.log(fn_params[i].name.escapedText.toString());
        all_names.set(fn_params[i].name.escapedText.toString(), names_fn);
    }
    console.log(all_names);
    return all_names;
}
exports.get_variable_names = get_variable_names;
//# sourceMappingURL=utils.js.map