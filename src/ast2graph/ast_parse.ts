import * as fs from 'fs';
import * as ts from 'typescript';
import * as util from 'util';


function visit(node: ts.Node) {
    console.log(ts.SyntaxKind[node.kind])
    console.log('--')
    if (ts.isFunctionDeclaration(node)) {
        for (const param of node.parameters) {
          console.log(param.name.getText());
        }
    }
    node.forEachChild(visit);
}

function instrument(source_obj: ts.Node) {
  console.log("in instrument")
  visit(source_obj);
}


function instrument1(fileName: string, sourceCode: string) {
  console.log("in instrument1")
  const sourceFile = ts.createSourceFile(fileName, sourceCode, ts.ScriptTarget.Latest, true);
  console.log(util.inspect(sourceFile,{compact:true, colors:true}));
  //visit(sourceFile);
}

/*
const inputFile = process.argv[2];
const ast_json = fs.readFileSync(inputFile);
console.log("hey there");
const ast_obj = <ts.Node> JSON.parse(ast_json.toString());
instrument(ast_obj);
*/

const inputFile = process.argv[2];
instrument1(inputFile, fs.readFileSync(inputFile, 'utf-8'));
//console.log(ast_obj.constructor.name);
//console.log(Object.getOwnPropertyNames(ast_obj.children));
