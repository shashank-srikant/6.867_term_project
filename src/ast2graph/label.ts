import * as ts from 'typescript';
import {Label} from "./interfaces"

function customTypeToString(checker: ts.TypeChecker, typ: ts.Type): string {
    let node = checker.typeToTypeNode(typ);
    if (node !== undefined && ts.isFunctionOrConstructorTypeNode(node)) {
	let n = node as (ts.FunctionTypeNode | ts.ConstructorTypeNode);

	if (n.typeParameters) {
	    n.typeParameters.forEach((p: ts.NamedDeclaration) => {p.name = ts.createIdentifier("_")});
	}

	if (n.parameters) {
	    n.parameters.forEach((p: ts.NamedDeclaration) => {p.name = ts.createIdentifier("_")});
	}

	let options = { removeComments: true };
        let printer = ts.createPrinter(options);
        let res = printer.printNode(ts.EmitHint.Unspecified, n, undefined);

	return res;
    } else {
	return checker.typeToString(
	    typ,
	    undefined,
	    ts.TypeFormatFlags.NoTruncation
	);
    }
}

function get_type(node: ts.Node, checker: ts.TypeChecker): string {
    let symbol = checker.getSymbolAtLocation(node);
    if (!symbol) {
        return "$any$";
    } else {
	let mType = customTypeToString(checker, checker.getTypeOfSymbolAtLocation(symbol, node));

        if (checker.isUnknownSymbol(symbol) || mType.startsWith('typeof ')) {
            // console.log('in here');
	    return "none";
        } else if (mType.startsWith("\"")) {
            return "string";
        } else if (mType.match('[0-9]+')) {
	    return "number";
	} else {
            return '$' + mType + '$';
            //symbol_type_map.push([type, symbol.escapedName.toString()])
        }
    }
}

function get_label(node: ts.Node, checker: ts.TypeChecker): [string, number] {
    let type: [string, number];
    if(node.kind === ts.SyntaxKind.VariableDeclaration){
        return [get_type((<ts.VariableDeclaration>node).name, checker), 1]
    }

    else if(!ts.isIdentifier(node)){
        return ["none", 1];
    }

    else {
        return [get_type(node, checker), 1]
    }
}

function get_max_count(label_dict: Map<string, number>):number{
    if(label_dict.size == 0){
        return 0;
    }
    return Math.max(...label_dict.values());
}

export function get_all_labels(labels:Label[], label_dict:Map <string, number>,
                                node: ts.Node, checker: ts.TypeChecker,
                                node_map: Map<ts.Node, number>){

    let lbl = get_label(node, checker);
    let curr_node_id = node_map.get(node);
    if(lbl[0] !== "none"){
        if(!label_dict.has(lbl[0])){
            let max_label_count = get_max_count(label_dict);
            label_dict.set(lbl[0], max_label_count+1);
        }
	if (lbl[0] === undefined) {
	    throw new Error('this is real bad');
	}
        var labelObj:Label = {
	    'node': curr_node_id,
            'label': lbl[0],
            'label_type': lbl[1]
        };
        labels.push(labelObj);
    }
    node.forEachChild(n => (get_all_labels(labels, label_dict, n, checker, node_map)));
}
