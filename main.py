from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from api.graph_routes import router
import networkx as nx
import osmnx as ox


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load graph
    try:
        G_osm = ox.load_graphml("my_phnom_penh.graphml")
    except:
        G_osm = ox.graph_from_place(
            "Phnom Penh, Cambodia", network_type="drive")
        ox.save_graphml(G_osm, "my_phnom_penh.graphml")

    # Store it in app state
    app.state.G = G_osm
    
    yield
    
    # Shutdown: cleanup if needed
    pass


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")  # Path to templates folder


# Include API routes
app.include_router(router)


@app.get("/home", response_class=HTMLResponse, name="home")
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "active_page": "home"})


@app.get("/about", response_class=HTMLResponse, name="about")
async def about(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "active_page": "about"})


@app.get("/contact", response_class=HTMLResponse, name="contact")
async def contact(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "active_page": "contact"})
