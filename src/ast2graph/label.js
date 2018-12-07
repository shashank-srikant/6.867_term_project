"use strict";
exports.__esModule = true;
var ts = require("typescript");
function customTypeToString(checker, typ) {
    var node = checker.typeToTypeNode(typ);
    if (node !== undefined && ts.isFunctionOrConstructorTypeNode(node)) {
        var n = node;
        if (n.typeParameters) {
            n.typeParameters.forEach(function (p) { p.name = ts.createIdentifier("_"); });
        }
        if (n.parameters) {
            n.parameters.forEach(function (p) { p.name = ts.createIdentifier("_"); });
        }
        var options = { removeComments: true };
        var printer = ts.createPrinter(options);
        var res = printer.printNode(ts.EmitHint.Unspecified, n, undefined);
        return res;
    }
    else {
        return checker.typeToString(typ, undefined, ts.TypeFormatFlags.NoTruncation);
    }
}
function get_type(node, checker) {
    var symbol = checker.getSymbolAtLocation(node);
    if (!symbol) {
        return "$any$";
    }
    else {
        var mType = customTypeToString(checker, checker.getTypeOfSymbolAtLocation(symbol, node));
        if (checker.isUnknownSymbol(symbol) || mType.startsWith('typeof ')) {
            // console.log('in here');
            return "none";
        }
        else if (mType.startsWith("\"")) {
            return "$string$";
        }
        else if (mType.match('[0-9]+')) {
            return "$number$";
        }
        else {
            return '$' + mType + '$';
            //symbol_type_map.push([type, symbol.escapedName.toString()])
        }
    }
}
function get_label(node, checker) {
    var type;
    if (node.kind === ts.SyntaxKind.VariableDeclaration) {
        return [get_type(node.name, checker), 1];
    }
    else if (!ts.isIdentifier(node)) {
        return ["none", 1];
    }
    else {
        return [get_type(node, checker), 1];
    }
}
function get_max_count(label_dict) {
    if (label_dict.size == 0) {
        return 0;
    }
    return Math.max.apply(Math, label_dict.values());
}
function get_all_labels(labels, label_dict, node, checker, node_map) {
    var lbl = get_label(node, checker);
    var curr_node_id = node_map.get(node);
    if (lbl[0] !== "none") {
        if (!label_dict.has(lbl[0])) {
            var max_label_count = get_max_count(label_dict);
            label_dict.set(lbl[0], max_label_count + 1);
        }
        if (lbl[0] === undefined) {
            throw new Error('this is real bad');
        }
        var labelObj = {
            'node': curr_node_id,
            'label': lbl[0],
            'label_type': lbl[1]
        };
        labels.push(labelObj);
    }
    node.forEachChild(function (n) { return (get_all_labels(labels, label_dict, n, checker, node_map)); });
}
exports.get_all_labels = get_all_labels;
