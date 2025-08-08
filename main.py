from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from api.graph_routes import router
import networkx as nx
import osmnx as ox
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load graph
    logger.info("Starting SmartRoutePP application...")
    try:
        logger.info("Loading graph from my_phnom_penh.graphml...")
        G_osm = ox.load_graphml("my_phnom_penh.graphml")
        logger.info("Graph loaded successfully from file")
    except Exception as e:
        logger.warning(f"Could not load graph from file ({e}), downloading from OSM...")
        G_osm = ox.graph_from_place(
            "Phnom Penh, Cambodia", network_type="drive")
        ox.save_graphml(G_osm, "my_phnom_penh.graphml")
        logger.info("Graph downloaded and saved successfully")

    # Store it in app state
    app.state.G = G_osm
    logger.info(f"Graph loaded with {len(G_osm.nodes)} nodes and {len(G_osm.edges)} edges")
    
    yield
    
    # Shutdown: cleanup if needed
    logger.info("Shutting down SmartRoutePP application...")


app = FastAPI(
    title="SmartRoutePP",
    description="Smart Route Planning for Phnom Penh",
    version="1.0.0",
    lifespan=lifespan
)
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
