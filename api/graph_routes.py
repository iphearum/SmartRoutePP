from typing import Optional
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse
from networkx.readwrite import json_graph
from shapely.geometry import LineString
from services.graph_helper import GraphHelper
from services.route_finder import RouterEngine
import traceback
from fastapi.templating import Jinja2Templates



router = APIRouter()
templates = Jinja2Templates(directory="templates")  # Path to templates folder


def normalize_geometry(geometry):
    fixed = []
    for coord in geometry:
        lat, lon = coord
        # Flip if lat is > 90 or < -90 (impossible lat value)
        if lat > 90 or lat < -90:
            lat, lon = lon, lat
        fixed.append([lat, lon])
    return fixed
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

def get_geometry_from_ids(app: FastAPI, start_id: int, end_id: int):
    G = app.state.G
    data = get_data(G)
    router = RouterEngine(data)
    result = router.route(start_id, end_id)
    return result["geometry"]


@router.get("/")
def read_root(request: Request):
    G = request.app.state.G
    return get_data(G)


@router.get('/getPoint')
def get_point_from_id(request: Request, id: int): 
    G = request.app.state.G 
    data = get_data(G)
    NodeData = data.get("nodes")
    graph = GraphHelper(NodeData)
    return graph.get_point_from_node_id(id)

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
    

@router.get("/map", response_class=HTMLResponse)
def render_map(request: Request, start_id: Optional[int] = None, end_id: Optional[int] = None):
    return templates.TemplateResponse("map.html", {
        "request": request,
        "start_id": start_id,
        "end_id": end_id
    })

@router.get("/request-route" ,response_class=HTMLResponse, name="request-route")
def request_route(request: Request): 
    return templates.TemplateResponse("route_form.html", {"request": request})

@router.get("/base")
def request_route(request: Request): 
    return templates.TemplateResponse("base.html", {"request": request})

@router.get("/visual", response_class=HTMLResponse)
def visual_map(request: Request, start_id: int , end_id: int ): 
    print(f"ROUTE requested: start_id={start_id}, end_id={end_id}")
    G = request.app.state.G
    data = get_data(G)
    router = RouterEngine(data)

    try:
        result = router.route(start_id, end_id)
        geometry = normalize_geometry(result["geometry"])
        return templates.TemplateResponse("map_view.html", {
        "request": request,
        "start_id": start_id,
        "end_id": end_id,
        "geometry": geometry
    })
    except Exception as e:
        print("❌ Exception occurred:")
        traceback.print_exc()  # <--- ADD THIS LINE
        return {"error": f"{type(e).__name__}: {e}"}
