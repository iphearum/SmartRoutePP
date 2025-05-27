from fastapi import APIRouter, Request
from networkx.readwrite import json_graph
from shapely.geometry import LineString
from services.graph_helper import GraphHelper

router = APIRouter()

def serialize_linestring(obj):
    if isinstance(obj, LineString):
        return list(obj.coords)
    return obj


@router.get("/")
def read_root(request: Request):
    G = request.app.state.G
    data = json_graph.node_link_data(G, edges="links")  # ← Add this
    for edge in data.get("links", []):
        if "geometry" in edge:
            edge["geometry"] = serialize_linestring(edge["geometry"])
    return data


@router.get("/test_point")
def test_point_ops(request: Request, osmid: int):
    G = request.app.state.G
    data = json_graph.node_link_data(G, edges="links")  # ← Add this
    for edge in data.get("links", []):
        if "geometry" in edge:
            edge["geometry"] = serialize_linestring(edge["geometry"])
    helper = GraphHelper(data)
    
    latlon = helper.get_point_from_osmid(osmid)
    if not latlon:
        return {"error": "OSM ID not found"}
    
    point = helper.create_point(latlon)
    on_node = helper.is_point_on_node(point)

    for u, v, data in G.edges(data=True):
        if "geometry" in data:
            geom = data["geometry"]
            on_edge = helper.is_point_on_edge(point, geom)
            dist = helper.distance_to_edge(point, geom)
            return {
                "on_node": on_node,
                "on_edge": on_edge,
                "distance_to_edge": dist
            }

    return {"message": "No geometry found on edges"}
