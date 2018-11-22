import {Graph} from "./graph"

const inputFile = process.argv[2];
const outputFile = process.argv[3] || 'example2.json';
var graph_obj = new Graph(inputFile, outputFile);
graph_obj.ast2graph();
