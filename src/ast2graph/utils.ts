import * as fs from 'fs';
import * as ts from 'typescript';
import * as util from 'util';
import { stringify } from 'querystring';

export function print_obj(obj: any, out_path:string, filename = "out.log"){
    fs.writeFile(out_path+filename , JSON.stringify(obj), function(err) {
        if (err) {
            console.log(err);
        }
    });
}

export function map2obj(aMap:Map<string, number>){
    const obj:{[key:string]: number} = {};
    aMap.forEach ((v,k) => { obj[k] = v });
    return obj;
}

export function get_variable_names(node: ts.Node): string[]{
    function getNodes(sf: ts.Node): ts.Node[] {
        var nodes: ts.Node[] = [];
        function allNodes(n: ts.Node) {
            ts.forEachChild(n, n => { nodes.push(n); allNodes(n); return false; })
        };
        allNodes(sf);
        return nodes;
    }
    let all_nodes = getNodes(node);
    var id_nodes = all_nodes.filter(n =>
                            (n.kind === ts.SyntaxKind.VariableDeclaration)).filter(n =>
                    (<ts.VariableDeclaration>n).name.kind === ts.SyntaxKind.Identifier
                    );
    var names1 = id_nodes.map(n => <string>((<ts.Identifier>(<ts.VariableDeclaration>n).name).text));
                                        
    var fn_params = all_nodes.filter(n => (n.kind === ts.SyntaxKind.FunctionDeclaration))
    let names2 = [];
    for(let i = 0; i<fn_params.length; i++){
        let li_param = (<ts.FunctionExpression>fn_params[i]).parameters;
        for(let j = 0; j<li_param.length; j++){
            names2.push((<ts.Identifier>li_param[j].name).escapedText.toString());
        }
    }    
    let all_names = names1.concat(names2);
    console.log(all_names);
    return all_names;
}