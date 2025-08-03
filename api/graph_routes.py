from typing import Optional
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from networkx.readwrite import json_graph
from shapely.geometry import LineString
from services.graph_helper import GraphHelper
from services.route_finder import RouterEngine
import traceback
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Utility functions
def normalize_geometry(geometry):
    """Ensure coordinates are in correct (lat, lon) order."""
    return [[lon, lat] if lat > 90 or lat < -90 else [lat, lon] 
            for lat, lon in geometry]

def serialize_linestring(obj):
    #Convert LineString to coordinate list.
    return list(obj.coords) if isinstance(obj, LineString) else obj

def get_graph_data(G):
    data = json_graph.node_link_data(G, edges="links")
    for edge in data.get("links", []):
        if "geometry" in edge:
            edge["geometry"] = serialize_linestring(edge["geometry"])
    return data

def get_router_engine(request: Request) -> RouterEngine:
    return RouterEngine(get_graph_data(request.app.state.G))

def get_graph_helper(request: Request) -> GraphHelper:
    data = get_graph_data(request.app.state.G)
    return GraphHelper(data)  

# Route handlers
@router.get("/readroot")
def read_root(request: Request):
    return get_graph_data(request.app.state.G)

@router.get("/")
def homepage(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})

@router.get('/getPoint')
def get_point_from_id(request: Request, id: int):
    return get_graph_helper(request).get_point_from_node_id(id)

@router.get("/getAdj")
def get_adjacency_list(request: Request):
    return get_router_engine(request).build_adjacency_list()

@router.get("/route")
def get_route(request: Request, start_id: int, end_id: int):
    print(f"ROUTE requested: start_id={start_id}, end_id={end_id}")
    try:
        return get_router_engine(request).route(start_id, end_id)
    except Exception as e:
        print("Exception occurred:")
        traceback.print_exc()
        return {"error": f"{type(e).__name__}: {e}"}

@router.get("/map", response_class=HTMLResponse)
def render_map(
    request: Request, 
    start_id: Optional[int] = None, 
    end_id: Optional[int] = None
):
    """Render map view."""
    return templates.TemplateResponse("map.html", {
        "request": request,
        "start_id": start_id,
        "end_id": end_id
    })

@router.get("/request-route-id", response_class=HTMLResponse, name="request-route-id")
def request_route(request: Request):
    return templates.TemplateResponse("route_form.html", {"request": request})

@router.get("/request-route-latlon", response_class=HTMLResponse, name="request-route-latlon")
def request_route(request: Request):
    return templates.TemplateResponse("route-request.html", {"request": request})

@router.get("/base")
def base_page(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})

@router.get("/visual", response_class=HTMLResponse)
def visual_map(request: Request, start_id: int, end_id: int):
    """Visual route map view."""
    print(f"ROUTE requested: start_id={start_id}, end_id={end_id}")
    try:
        result = get_router_engine(request).route(start_id, end_id)
        geometry = normalize_geometry(result["geometry"])
        return templates.TemplateResponse("map_view.html", {
            "request": request,
            "start_id": start_id,
            "end_id": end_id,
            "geometry": geometry
        })
    except Exception as e:
        print("Exception occurred:")
        traceback.print_exc()
        return {"error": f"{type(e).__name__}: {e}"}

@router.get("/point_on_edge")
def is_on_edge(request: Request, lat: float, lon: float):
    return get_graph_helper(request).is_point_on_edge(lat, lon)

@router.get("/distance")
def distance_to_point(request: Request, lat: float, lon: float):
    return get_graph_helper(request).distance_to_the_point(lat, lon)


#testing new route 
@router.get("/temp_route")
def route_from_temp_point(
    request: Request,
    lat: float,
    lon: float,
    dest_id: int
):
    try:
        graph_helper = get_graph_helper(request)
        source_id = graph_helper.add_temp_point(lat, lon)
        router_engine = RouterEngine(graph_helper.get_graph()) 
       
        print(source_id)


        updated_graph = graph_helper.get_graph()
        router_engine = RouterEngine(updated_graph)

        result = router_engine.route(source_id, dest_id)

        result["geometry"] = normalize_geometry(result["geometry"])

        # return {
        #     "start_temp_id": source_id,
        #     "end_id": dest_id,
        #     "geometry": result["geometry"],
        #     "path": result.get("path"),
        #     "length": result.get("length")
        # }
        return templates.TemplateResponse("map_view.html", {
            "request": request,
            "start_id": source_id,
            "end_id": dest_id,
            "geometry": result["geometry"]
        })

    except Exception as e:
        traceback.print_exc()
        return {"error": f"{type(e).__name__}: {e}"}
    

#testing new route - test 
@router.get("/closest-node")
def route_from_temp_point(
    request: Request,
    lat: float,
    lon: float):
    graph_helper = get_graph_helper(request)
    id = graph_helper.closest_node(lat, lon)
    return id


# have to work on this and do testing 
@router.post("/full_temp_route")
async def full_route_from_temp_point(
    request: Request,
    s_lat: float = Form(...),
    s_lon: float = Form(...),
    d_lat: float = Form(...),
    d_lon: float = Form(...)
):
    try:
        graph_helper = get_graph_helper(request)
        source_id = graph_helper.add_temp_point(s_lat, s_lon)
        dest_id = graph_helper.add_temp_point(d_lat, d_lon)
        router_engine = RouterEngine(graph_helper.get_graph(include_temp=True)) 
        

        updated_graph = graph_helper.get_graph(include_temp=True)
        router_engine = RouterEngine(updated_graph)

        result = router_engine.route(source_id, dest_id)

        result["geometry"] = normalize_geometry(result["geometry"])

        # return {
        #     "start_temp_id": source_id,
        #     "end_id": dest_id,
        #     "geometry": result["geometry"],
        #     "path": result.get("path"),
        #     "length": result.get("length")
        # }
        return templates.TemplateResponse("map_view.html", {
            "request": request,
            "start_id": source_id,
            "end_id": dest_id,
            "geometry": result["geometry"]
        })

    except Exception as e:
        traceback.print_exc()
        return {"error": f"{type(e).__name__}: {e}"}
    
@router.get("/selecting-route")
def test_templates(request: Request): 
    return templates.TemplateResponse("selectPoint.html", {
        "request": request,
    })
