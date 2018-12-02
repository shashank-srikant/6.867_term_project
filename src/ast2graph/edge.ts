import * as ts from 'typescript';
import { GraphEdge } from "./interfaces";

export abstract class Edge {
    protected edge_type: number[];
    protected edge_description: string;

    constructor(edge_type:number[], edge_descrip:string) {
        this.edge_type = edge_type;
        this.edge_description = edge_descrip;
    }

    abstract visit_tree(
	node: ts.Node,
	edges: GraphEdge[],
	parent: number,
	checker: ts.TypeChecker,
	node_map: Map<ts.Node, number>
    ) : GraphEdge[];
}
