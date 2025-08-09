# tests/conftest.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
import redis.asyncio as redis
from unittest.mock import AsyncMock, MagicMock
import networkx as nx
from main import app

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def async_client():
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def test_client():
    """Create sync test client"""
    return TestClient(app)

@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock_client = AsyncMock()
    mock_client.get.return_value = None
    mock_client.setex.return_value = True
    return mock_client

@pytest.fixture
def test_graph():
    """Create test graph"""
    G = nx.MultiDiGraph()
    # Add test nodes and edges
    G.add_node(1, x=104.9, y=11.5)
    G.add_node(2, x=104.91, y=11.51)
    G.add_node(3, x=104.92, y=11.52)
    G.add_edge(1, 2, length=100)
    G.add_edge(2, 3, length=150)
    return G

@pytest.fixture
def setup_test_app(test_graph, mock_redis):
    """Setup app with test data"""
    app.state.G = test_graph
    app.state.redis_client = mock_redis
    return app