"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const ts = require("typescript");
function get_type(node, checker) {
    let type;
    let symbol = checker.getSymbolAtLocation(node);
    if (!symbol) {
        type = "$any$";
    }
    else {
        let mType = checker.typeToString(checker.getTypeOfSymbolAtLocation(symbol, node));
        if (checker.isUnknownSymbol(symbol) || mType.startsWith('typeof ')) {
            console.log('in here');
        }
        else if (mType.startsWith("\"") || mType.match('[0-9]+')) {
            type = "none";
        }
        else {
            type = '$' + mType + '$';
        }
    }
    return type;
}
function get_label(node, checker) {
    let type;
    if (node.kind == ts.SyntaxKind.VariableDeclaration) {
        return [get_type(node.name, checker), 1];
    }
    else if (!ts.isIdentifier(node)) {
        type = ["none", 1];
        return type;
    }
    else {
        return [get_type(node, checker), 1];
    }
}
function get_max_count(label_dict) {
    if (label_dict.size == 0) {
        return 0;
    }
    return Math.max(...label_dict.values());
}
function get_all_labels(labels, label_dict, node, checker, node_map) {
    let lbl = get_label(node, checker);
    let curr_node_id = node_map.get(node);
    if (lbl[0] != "none") {
        if (!label_dict.has(lbl[0])) {
            let max_label_count = get_max_count(label_dict);
            label_dict.set(lbl[0], max_label_count + 1);
        }
        var labelObj = { 'node': curr_node_id,
            'label': label_dict.get(lbl[0]),
            'label_type': lbl[1]
        };
        labels.push(labelObj);
    }
    node.forEachChild(n => (get_all_labels(labels, label_dict, n, checker, node_map)));
}
exports.get_all_labels = get_all_labels;
//# sourceMappingURL=label.js.map