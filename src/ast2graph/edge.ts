import * as ts from 'typescript';
import { GraphEdge, GraphEdgeDebug } from "./interfaces";
import { get_by_value} from "./utils"

export abstract class Edge {
    protected edge_type: number[];
    public edge_description: string;

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

    protected reverse_edge(edge_list:GraphEdge[], node_map:Map<ts.Node, number>): GraphEdgeDebug[]{
        function node_name(ed: number): string{
            if(ed == -1){
                return "ROOT";
            }
            else{
                let st = ts.SyntaxKind[get_by_value(node_map, ed).kind];
                return st;
            }
        }
        var rev_edge_list: GraphEdgeDebug[] = [];
        for(let i = 0; i<edge_list.length; i++) {
            let rev_edge:GraphEdgeDebug = {
                'src': node_name(edge_list[i]['src']),
                'dst': node_name(edge_list[i]['dst']),
                'edge_type': edge_list[i]['edge_type']
            }
            rev_edge_list.push(rev_edge);
        }
        return rev_edge_list;
    }
}
