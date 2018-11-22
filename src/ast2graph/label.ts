import * as ts from 'typescript';
import {Label} from "./interfaces"

function get_type(node: ts.Node, checker: ts.TypeChecker): string {
    let type: string;
    let symbol = checker.getSymbolAtLocation(node);
    if (!symbol) {
        type = "$any$";
    } 
    else {
        let mType = checker.typeToString(checker.getTypeOfSymbolAtLocation(symbol, node));
        if (checker.isUnknownSymbol(symbol) || mType.startsWith('typeof ')) {
            console.log('in here');
        } else if (mType.startsWith("\"") || mType.match('[0-9]+')) {
            type = "none";
        } else {
            type = '$' + mType + '$';
            //symbol_type_map.push([type, symbol.escapedName.toString()])
        }
    }
    return type;
}

function get_label(node: ts.Node, checker: ts.TypeChecker): [string, number] {
    let type: [string, number];
    if(node.kind == ts.SyntaxKind.VariableDeclaration){
        return [get_type((<ts.VariableDeclaration>node).name, checker), 1]
    }

    else if(!ts.isIdentifier(node)){
        type = ["none", 1]
        return type;
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
    if(lbl[0] != "none"){
        if(!label_dict.has(lbl[0])){
            let max_label_count = get_max_count(label_dict);
            label_dict.set(lbl[0], max_label_count+1);
        }
        var labelObj:Label = {'node': curr_node_id,
                                'label': label_dict.get(lbl[0]),
                                'label_type': lbl[1]
                            };
        labels.push(labelObj);
    }
    node.forEachChild(n => (get_all_labels(labels, label_dict, n, checker, node_map)));
}