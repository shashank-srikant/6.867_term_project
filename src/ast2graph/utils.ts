import * as fs from 'fs';
import * as ts from 'typescript';

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

// Junk function. Will eventually be removed
export function get_variable_names(node: ts.Node, pgm: ts.Program, checker:ts.TypeChecker): void{
    var nodes: ts.Node[] = [];
    function getNodes(sf: ts.Node): ts.Node[] {
        var nodes: ts.Node[] = [];
        function allNodes(n: ts.Node) {
            ts.forEachChild(n, n => { nodes.push(n); allNodes(n); return false; })
        };
        allNodes(sf);
        return nodes;
    }
    var id_nodes = getNodes(node).filter(n =>
                            (n.kind === ts.SyntaxKind.VariableDeclaration)).filter(n =>
                    (<ts.VariableDeclaration>n).name.kind === ts.SyntaxKind.Identifier
                    );
    var names = id_nodes.map(n => <string>((<ts.Identifier>(<ts.VariableDeclaration>n).name).text));
    
    //console.log(id_nodes_symbolobj)
    //var names = id_nodes.map(n =>  decl_flags((<ts.Identifier>n)));
    //var decls = names.map(n => n.getDeclarations());
    console.log('BEGIN NAMES');
    console.log(names);
    console.log('END NAMES');
    //return names
    //return node.forEachChild(n => (this.get_variable_names(n)));
}