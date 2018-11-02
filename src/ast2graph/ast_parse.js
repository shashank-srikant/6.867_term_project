"use strict";
exports.__esModule = true;
var fs = require("fs");
var ts = require("typescript");
var util = require("util");
function visit(node) {
    console.log(ts.SyntaxKind[node.kind]);
    console.log('--');
    if (ts.isFunctionDeclaration(node)) {
        for (var _i = 0, _a = node.parameters; _i < _a.length; _i++) {
            var param = _a[_i];
            console.log(param.name.getText());
        }
    }
    node.forEachChild(visit);
}
function instrument(source_obj) {
    console.log("in instrument");
    visit(source_obj);
}
function instrument1(fileName, sourceCode) {
    console.log("in instrument1");
    var sourceFile = ts.createSourceFile(fileName, sourceCode, ts.ScriptTarget.Latest, true);
    console.log(util.inspect(sourceFile, { compact: true, colors: true }));
    //visit(sourceFile);
}
/*
const inputFile = process.argv[2];
const ast_json = fs.readFileSync(inputFile);
console.log("hey there");
const ast_obj = <ts.Node> JSON.parse(ast_json.toString());
instrument(ast_obj);
*/
var inputFile = process.argv[2];
instrument1(inputFile, fs.readFileSync(inputFile, 'utf-8'));
//console.log(ast_obj.constructor.name);
//console.log(Object.getOwnPropertyNames(ast_obj.children));
