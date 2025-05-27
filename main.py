from fastapi import FastAPI
from router.graph_routes import router

app = FastAPI()

# Load your graph at startup
@app.on_event("startup")
def load_graph():
    import osmnx as ox
    import networkx as nx
    from shapely.geometry import LineString

    try:
        app.state.G = ox.load_graphml("phnom_penh.graphml")
    except:
        app.state.G = ox.graph_from_place("Phnom Penh, Cambodia", network_type="drive")
        ox.save_graphml(app.state.G, "phnom_penh.graphml")

app.include_router(router)
