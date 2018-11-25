import * as fs from 'fs';
import * as ts from 'typescript';
import * as util from 'util';
import { stringify } from 'querystring';

export function is_assign_op(op:ts.SyntaxKind){
    if(op === ts.SyntaxKind.EqualsToken || op === ts.SyntaxKind.PlusEqualsToken || op ===  ts.SyntaxKind.MinusEqualsToken || op ===  ts.SyntaxKind.AsteriskAsteriskEqualsToken || op ===  ts.SyntaxKind.AsteriskEqualsToken || op ===  ts.SyntaxKind.SlashEqualsToken || op ===  ts.SyntaxKind.PercentEqualsToken || op ===  ts.SyntaxKind.AmpersandEqualsToken || op ===  ts.SyntaxKind.BarEqualsToken || op ===  ts.SyntaxKind.CaretEqualsToken || op ===  ts.SyntaxKind.LessThanLessThanEqualsToken || op ===  ts.SyntaxKind.GreaterThanGreaterThanGreaterThanEqualsToken || op ===  ts.SyntaxKind.GreaterThanGreaterThanEqualsToken){
        return true;
    }
    else{
        return false;
    }
}

export function print_obj(obj: any, out_path:string, filename = "out.log"){
    fs.writeFile(out_path+filename , JSON.stringify(obj), function(err) {
        if (err) {
            console.log(err);
        }
    });
}

export function pass_null_check<T>(value: T | undefined | null): value is T {
    return <T>value !== undefined && <T>value !== null;
}

export function map2obj(aMap:Map<string, number>){
    const obj:{[key:string]: number} = {};
    aMap.forEach ((v,k) => { obj[k] = v });
    return obj;
}

export function get_block_identifiers(node: ts.Node[]): Set<string>{
    var id_nodes = node.filter(n => n.kind === ts.SyntaxKind.Identifier);
    var names = id_nodes.map(n => (<ts.Identifier>(n)).escapedText.toString());
    let names_set = new Set(names);
    return names_set;
}

export function get_block_variable_names_in_decl(node: ts.Node[]): Set<string>{
    var id_nodes = node.filter(n => (n.kind === ts.SyntaxKind.VariableDeclaration)).filter(
        n => (<ts.VariableDeclaration>n).name.kind === ts.SyntaxKind.Identifier
    );
    var names = id_nodes.map(n => <string>((<ts.Identifier>(<ts.VariableDeclaration>n).name).text));
    let names_set = new Set(names);
    return names_set;
}

export function getNodes(sf: ts.Node): ts.Node[] {
    var nodes: ts.Node[] = [];
    function allNodes(n: ts.Node) {
        ts.forEachChild(n, n => { nodes.push(n); allNodes(n); return false; })
    };
    if(sf.getChildCount() == 0){
        nodes.push(sf);
    }
    else{
        allNodes(sf);
    }
    return nodes;
}

export function get_variable_names(node: ts.Node): Map<string, string[]>{
    let all_names:Map<string, string[]> = new Map();
    // Get names of variables used in the script's body
    var body = (<ts.SourceFile>node).statements.filter(n => n.kind !== ts.SyntaxKind.FunctionDeclaration);
    let names1:string[] = [];
    for(let i = 0; i<body.length; i++){
        let all_nodes = getNodes(body[i]);
        let names_set = get_block_variable_names_in_decl(all_nodes);
        names1 = names1.concat(Array.from(names_set));
    }
    all_names.set("body", names1);
    
    // Get per-function variable names
    let all_nodes = getNodes(node);
    var fn_params = all_nodes.filter(n => (n.kind === ts.SyntaxKind.FunctionDeclaration))
    for(let i = 0; i<fn_params.length; i++){
        let names2 = [];
        let li_param = (<ts.FunctionExpression>fn_params[i]).parameters;
        for(let j = 0; j<li_param.length; j++){
            names2.push((<ts.Identifier>li_param[j].name).escapedText.toString());
        }
        let fn_nodes = getNodes(fn_params[i]);
        let names3 = get_block_variable_names_in_decl(fn_nodes);
        let names_fn = names2.concat(Array.from(names3));
        console.log((<ts.FunctionDeclaration>fn_params[i]).name.escapedText.toString());
        all_names.set((<ts.FunctionDeclaration>fn_params[i]).name.escapedText.toString(), names_fn);
    }    
    //let all_names = names1.concat(names2);
    console.log(all_names);
    return all_names;
}