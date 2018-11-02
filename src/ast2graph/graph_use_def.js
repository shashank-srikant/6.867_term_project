"use strict";
var __extends = (this && this.__extends) || (function () {
    var extendStatics = function (d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p]; };
        return extendStatics(d, b);
    }
    return function (d, b) {
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
exports.__esModule = true;
var ts = require("typescript");
var graph_1 = require("./graph");
var GraphUseDef = /** @class */ (function (_super) {
    __extends(GraphUseDef, _super);
    function GraphUseDef() {
        return _super !== null && _super.apply(this, arguments) || this;
    }
    GraphUseDef.prototype.visit = function (node) {
        console.log(ts.SyntaxKind[node.kind]);
        console.log('--');
        if (ts.isFunctionDeclaration(node)) {
            for (var _i = 0, _a = node.parameters; _i < _a.length; _i++) {
                var param = _a[_i];
                console.log(param.name.getText());
            }
        }
        node.forEachChild(this.visit);
    };
    return GraphUseDef;
}(graph_1.Graph));
// Unit-test
var inputFile = process.argv[2];
var graph_obj = new GraphUseDef(inputFile);
graph_obj.ast2graph();
