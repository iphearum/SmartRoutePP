from fastapi import APIRouter, Request
from networkx.readwrite import json_graph
from shapely.geometry import LineString
from services.graph_helper import GraphHelper
from services.route_finder import RouterEngine
import traceback
from fastapi.templating import Jinja2Templates



router = APIRouter()
templates = Jinja2Templates(directory="templates")  # Path to templates folder

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


@router.get('/getPoint')
def get_point_from_id(request: Request, id: int): 
    G = request.app.state.G 
    data = get_data(G)
    NodeData = data.get("nodes")
    graph = GraphHelper(NodeData)
    return graph.get_point_from_node_id(id)
  
@router.get("/adjlist")
def get_adj_list(request: Request): 
    G = request.app.state.G
    data = get_data(G)

    adj_list = {}

    for edge in data.get("links", []): 
        src = edge["source"]
        tgt = edge["target"]

        # Use geometry-based length if available
        if "geometry" in edge:
            coords = [(lon, lat) for lat, lon in edge["geometry"]]  # Flip to (x, y)
            line = LineString(coords)
            length = line.length
        else:
            length = edge.get("length", 1)

        adj_list.setdefault(src, []).append({"to": tgt, "length": length})

    return adj_list

@router.get("/getAdj")
def getAdjList(request: Request): 
    G = request.app.state.G 
    data = get_data(G)

    routeFinder = RouterEngine(data)
    return routeFinder.build_adjacency_list()


@router.get("/route")
def get_route(request: Request, start_id: int, end_id: int):
    print(f"ROUTE requested: start_id={start_id}, end_id={end_id}")
    G = request.app.state.G
    data = get_data(G)
    router = RouterEngine(data)

    try:
        result = router.route(start_id, end_id)
        return result
    except Exception as e:
        print("❌ Exception occurred:")
        traceback.print_exc()  # <--- ADD THIS LINE
        return {"error": f"{type(e).__name__}: {e}"}
    

@router.get("/map_route")
def map_route(request: Request, start_id: int, end_id: int):
    G = request.app.state.G

    # Use safe graph data with serialized geometry
    data = get_data(G)

    # Compute route using RouterEngine
    router = RouterEngine(data)
    result = router.route(start_id, end_id)  # contains "path" and "geometry"

    return templates.TemplateResponse("map_route.html", {
        "request": request,
        "geometry": result["geometry"],  # Pass to Jinja2 for Leaflet rendering
        "start": result["geometry"][0],
        "end": result["geometry"][-1],
        "path": result["path"]
    })


@router.get("/input-data")
def input_map(request: Request): 
    return templates.TemplateResponse("map_route.html", {
        "request": request
    })