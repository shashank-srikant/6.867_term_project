"use strict";
exports.__esModule = true;
var fs = require("fs");
var ts = require("typescript");
// Base class to convert ASTs to graphs
var Graph = /** @class */ (function () {
    function Graph(ast_path) {
        this.ast_path = ast_path;
    }
    Graph.prototype.ast2graph = function () {
        console.log("in ast_parse");
        var source_code = fs.readFileSync(this.ast_path, 'utf-8');
        var sourceFile = ts.createSourceFile(this.ast_path, source_code, ts.ScriptTarget.Latest, true);
        //console.log(util.inspect(sourceFile,{compact:true, colors:true}));
        this.visit(sourceFile);
        // overload visit for getting different types of edges 
        // the output of `visit` would be passed to to_graph() 
        // to_graph() converts a dict to a graph, and shapes it in the format required for training
        // the output of to_graph() will be pushed to write_graph() to store on disk
    };
    return Graph;
}());
exports.Graph = Graph;
