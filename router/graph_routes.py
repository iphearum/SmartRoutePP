from fastapi import APIRouter, Request
from networkx.readwrite import json_graph
from shapely import Point
from shapely.geometry import LineString
from services.graph_helper import GraphHelper

router = APIRouter()

def serialize_linestring(obj):
    if isinstance(obj, LineString):
        return list(obj.coords)
    return obj

def get_data(G): 
    data = json_graph.node_link_data(G, edges="links")
    for edge in data.get("links", []): 
        if "geometry" in edge: 
            edge["geometry"] = serialize_linestring(edge["geometry"])
    return data

@router.get("/")
def read_root(request: Request):
    G = request.app.state.G
    return get_data(G)

@router.get("/adjlist")
def get_adj_list(request: Request): 
    G = request.app.state.G
    data = get_data(G)
    adj_list = {}

    for edge in data.get("links", []): 
        src = edge.get("source")
        tgt = edge.get("target")
        length = edge.get("length", 1)

        if src not in adj_list:
            adj_list[src] = []
        adj_list[src].append({"to": tgt, "length": length})

    return adj_list


@router.get('/getPoint')
def get_point_from_id(request: Request, id: int): 
    G = request.app.state.G 
    data =  get_data(G)
    graph = GraphHelper(data)
    getData = graph.get_point_from_node_id(id)
    return getData
   

@router.get("/on-edge")
def is_on_edge(request: Request,lon: float, lat: float): 
    G = request.app.state.G
    # Make sure this returns dict with 'nodes' and 'links'
    data = get_data(G) 
    graph = GraphHelper(data)  # or GraphHelper(G) if using raw graph
    p = Point(lon, lat)
    myresult = graph.is_point_on_edge(p) 
    return {"result": myresult}

