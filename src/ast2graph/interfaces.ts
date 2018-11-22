export interface GraphNode {
    "id": number,
    "ast_type": number
}

export interface GraphEdge {
    "src": GraphNode['id'],
    "dst": GraphNode['id'],
    "edge_type": number
}

export interface Label {
    "node": GraphNode['id'],
    "label": number,
    "label_type": number 
    //to signify whether identifier is under a declaration stmnt type (0),
    // or any other node (1)
}