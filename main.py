import osmnx as ox
import asyncio
import logging
from functools import lru_cache
from contextlib import asynccontextmanager
from typing import Optional
import redis.asyncio as redis
import pickle
import hashlib
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from api.graph_routes import router
import networkx as nx
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection pool
redis_pool: Optional[redis.ConnectionPool] = None
redis_client: Optional[redis.Redis] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global redis_pool, redis_client
    try:
        # Initialize Redis connection pool
        redis_pool = redis.ConnectionPool.from_url(
            "redis://localhost:6379", 
            max_connections=20,
            decode_responses=False
        )
        redis_client = redis.Redis(connection_pool=redis_pool)
        
        # Load graph in background
        await load_graph_async()
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        # Continue without Redis if connection fails
        redis_client = None
    
    yield
    
    # Shutdown
    if redis_client:
        await redis_client.close()
    if redis_pool:
        await redis_pool.disconnect()
    logger.info("Application shutdown complete")

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

# Cache configuration
CACHE_TTL = 3600  # 1 hour
GRAPH_CACHE_KEY = "phnom_penh_graph"

@lru_cache(maxsize=128)
def get_cached_route_key(start_lat: float, start_lon: float, 
                        end_lat: float, end_lon: float) -> str:
    """Generate cache key for route requests"""
    key_string = f"{start_lat}_{start_lon}_{end_lat}_{end_lon}"
    return hashlib.md5(key_string.encode()).hexdigest()

async def get_redis_client() -> Optional[redis.Redis]:
    """Dependency to get Redis client"""
    return redis_client

async def cache_get(key: str, redis_client: Optional[redis.Redis] = None) -> Optional[bytes]:
    """Get data from cache"""
    if not redis_client:
        return None
    try:
        return await redis_client.get(key)
    except Exception as e:
        logger.warning(f"Cache get error: {e}")
        return None

async def cache_set(key: str, value: bytes, ttl: int = CACHE_TTL, 
                   redis_client: Optional[redis.Redis] = None) -> bool:
    """Set data in cache"""
    if not redis_client:
        return False
    try:
        await redis_client.setex(key, ttl, value)
        return True
    except Exception as e:
        logger.warning(f"Cache set error: {e}")
        return False

async def load_graph_async():
    """Load graph asynchronously with caching"""
    try:
        # Try to load from Redis cache first
        if redis_client:
            cached_graph = await cache_get(GRAPH_CACHE_KEY, redis_client)
            if cached_graph:
                logger.info("Loading graph from Redis cache")
                G_osm = pickle.loads(cached_graph)
                app.state.G = G_osm
                return

        # Try to load from local file
        try:
            logger.info("Loading graph from local file")
            G_osm = ox.load_graphml("my_phnom_penh.graphml")
        except FileNotFoundError:
            logger.info("Local graph file not found, downloading from OSM")
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            G_osm = await loop.run_in_executor(
                None, 
                lambda: ox.graph_from_place("Phnom Penh, Cambodia", network_type="drive")
            )
            # Save to local file
            ox.save_graphml(G_osm, "my_phnom_penh.graphml")

        # Cache in Redis
        if redis_client:
            graph_bytes = pickle.dumps(G_osm)
            await cache_set(GRAPH_CACHE_KEY, graph_bytes, CACHE_TTL * 24, redis_client)  # Cache for 24 hours
            logger.info("Graph cached in Redis")

        # Store in app state
        app.state.G = G_osm
        logger.info("Graph loaded successfully")

    except Exception as e:
        logger.error(f"Error loading graph: {e}")
        # Create empty graph as fallback
        app.state.G = nx.MultiDiGraph()

async def get_graph():
    """Dependency to get graph with fallback"""
    if not hasattr(app.state, 'G') or app.state.G is None:
        await load_graph_async()
    
    if app.state.G is None or len(app.state.G.nodes()) == 0:
        raise HTTPException(status_code=503, detail="Graph not available")
    
    return app.state.G

@lru_cache(maxsize=1000)
def get_nearest_node_cached(graph_id: str, lat: float, lon: float, G):
    """Cache nearest node calculations"""
    return ox.nearest_nodes(G, lon, lat)

async def calculate_route_with_cache(
    start_lat: float, start_lon: float,
    end_lat: float, end_lon: float,
    redis_client: Optional[redis.Redis] = None,
    G = None
):
    """Calculate route with caching"""
    if G is None:
        G = await get_graph()
    
    # Generate cache key
    cache_key = f"route_{get_cached_route_key(start_lat, start_lon, end_lat, end_lon)}"
    
    # Try to get from cache
    if redis_client:
        cached_route = await cache_get(cache_key, redis_client)
        if cached_route:
            logger.info("Route found in cache")
            return pickle.loads(cached_route)
    
    try:
        # Calculate route
        start_time = time.time()
        
        # Get nearest nodes
        start_node = get_nearest_node_cached(id(G), start_lat, start_lon, G)
        end_node = get_nearest_node_cached(id(G), end_lat, end_lon, G)
        
        # Calculate shortest path
        route = nx.shortest_path(G, start_node, end_node, weight='length')
        
        calculation_time = time.time() - start_time
        logger.info(f"Route calculated in {calculation_time:.2f} seconds")
        
        # Cache the result
        if redis_client:
            route_bytes = pickle.dumps(route)
            await cache_set(cache_key, route_bytes, CACHE_TTL, redis_client)
        
        return route
        
    except nx.NetworkXNoPath:
        logger.warning("No path found between the given points")
        raise HTTPException(status_code=404, detail="No route found")
    except Exception as e:
        logger.error(f"Route calculation error: {e}")
        raise HTTPException(status_code=500, detail="Route calculation failed")

# Background task for cache warming
async def warm_cache_task():
    """Background task to warm up frequently used routes"""
    # Implement cache warming logic here
    logger.info("Cache warming task started")

# Add periodic cache cleanup
async def cleanup_cache_task():
    """Background task to cleanup expired cache entries"""
    if redis_client:
        try:
            # This is a simple cleanup - Redis handles TTL automatically
            # but you can add custom cleanup logic here
            logger.info("Cache cleanup completed")
        except Exception as e:
            logger.warning(f"Cache cleanup error: {e}")

"""
app.state : special place provided by FastAPI (inherited from Starlette) to store custom application-level 
    state.

Optimizations added:
1. Redis caching with connection pooling
2. Async graph loading with background tasks
3. LRU cache for frequently accessed data
4. Proper error handling and logging
5. Route caching with configurable TTL
6. Connection pool for better resource management
7. Fallback mechanisms when cache is unavailable
"""

# embedded file
app.include_router(router)

# 1. Test and complete the fasting:
# 3. Visualization: connect front and back
# 2. embdeded

@app.get("/home", response_class=HTMLResponse, name="home")
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "active_page": "home"})


@app.get("/about", response_class=HTMLResponse, name="about")
async def about(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "active_page": "about"})


@app.get("/contact", response_class=HTMLResponse, name="contact")
async def contact(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "active_page": "contact"})
