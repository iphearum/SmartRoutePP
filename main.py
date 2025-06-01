from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from router.graph_routes import router

app = FastAPI()
templates = Jinja2Templates(directory="templates")  # Path to templates folder

# Load your graph at startup
@app.on_event("startup")
def load_graph():
    import osmnx as ox
    try:
        app.state.G = ox.load_graphml("phnom_penh.graphml")
    except:
        app.state.G = ox.graph_from_place("Phnom Penh, Cambodia", network_type="drive")
        ox.save_graphml(app.state.G, "phnom_penh.graphml")

app.include_router(router)

# Route to display map with a point
@app.get("/map", response_class=HTMLResponse)
def show_map(request: Request, lat: float = 11.5564, lon: float = 104.9282):
    return templates.TemplateResponse("map.html", {
        "request": request,
        "lat": lat,
        "lon": lon
    })
