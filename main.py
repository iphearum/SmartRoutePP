from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from api.graph_routes import router
import networkx as nx

app = FastAPI()
templates = Jinja2Templates(directory="templates")  # Path to templates folder

# Load your graph at startup
@app.on_event("startup")
def load_graph():
    import osmnx as ox
    try:
        G_osm = ox.load_graphml("my_phnom_penh.graphml")
    except:
        G_osm = ox.graph_from_place("Phnom Penh, Cambodia", network_type="drive")
        ox.save_graphml(G_osm, "my_phnom_penh.graphml")
    
    # try:
    #     # Load your embedded custom graph
    #     G_custom = ox.load_graphml("embedded.graphml")
    # except FileNotFoundError:
    #     print("embedded.graphml not found. Proceeding without it.")
    #     G_custom = nx.MultiDiGraph()
    
    #  # Combine both graphs
    # G_combined = nx.compose(G_osm, G_custom)

    # # Save the combined graph if needed
    # ox.save_graphml(G_combined, "combined.graphml")

    # Store it in app state
    app.state.G = G_osm
    
"""
app.state : special place provided by FastAPI (inherited from Starlette) to store custom application-level 
    state.
"""
#embedded file 
app.include_router(router)

#1. Test and complete the fasting:  
#3. Visualization: connect front and back 
#2. embdeded 


@app.get("/home", response_class=HTMLResponse, name="home")
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "active_page": "home"})

@app.get("/about", response_class=HTMLResponse, name="about")
async def about(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "active_page": "about"})

@app.get("/contact", response_class=HTMLResponse, name="contact")
async def contact(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "active_page": "contact"})

