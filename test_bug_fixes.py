"""
Unit tests to validate bug fixes and optimizations.
"""
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Mock external dependencies that we can't install
sys.modules['shapely'] = Mock()
sys.modules['shapely.geometry'] = Mock()
sys.modules['shapely.geometry'].Point = Mock()
sys.modules['shapely.geometry'].LineString = Mock()

# Add current directory to path
sys.path.insert(0, os.getcwd())

from services.route_finder import RouterEngine
from api.graph_routes import validate_coordinates
from fastapi import HTTPException


def test_coordinate_validation():
    """Test input validation for coordinates."""
    # Valid coordinates should pass
    assert validate_coordinates(11.5, 104.8) == True
    
    # Invalid latitude should raise exception
    with pytest.raises(HTTPException):
        validate_coordinates(95.0, 104.8)  # lat > 90
    
    with pytest.raises(HTTPException):
        validate_coordinates(-95.0, 104.8)  # lat < -90
    
    # Invalid longitude should raise exception
    with pytest.raises(HTTPException):
        validate_coordinates(11.5, 185.0)  # lon > 180
    
    with pytest.raises(HTTPException):
        validate_coordinates(11.5, -185.0)  # lon < -180


def test_route_finder_node_validation():
    """Test that node validation checks actual node existence, not just adjacency."""
    graph_data = {
        "nodes": [
            {"id": 1, "x": 104.8, "y": 11.5},
            {"id": 2, "x": 104.9, "y": 11.6}
        ],
        "links": []  # No edges, so no adjacency
    }
    
    router = RouterEngine(graph_data)
    
    # These nodes exist in graph but have no edges
    # Should raise ValueError about no valid path, not "node not found"
    with pytest.raises(ValueError) as exc_info:
        router.route(1, 2)
    
    # The error should be about no path, not missing nodes
    assert "No valid path" in str(exc_info.value)


def test_route_finder_missing_node():
    """Test that missing nodes are properly detected."""
    graph_data = {
        "nodes": [
            {"id": 1, "x": 104.8, "y": 11.5},
            {"id": 2, "x": 104.9, "y": 11.6}
        ],
        "links": []
    }
    
    router = RouterEngine(graph_data)
    
    # Node 999 doesn't exist
    with pytest.raises(ValueError) as exc_info:
        router.route(1, 999)
    
    assert "End node 999 not found in graph" in str(exc_info.value)


def test_router_engine_caching():
    """Test that the route caching works properly."""
    graph_data = {
        "nodes": [
            {"id": 1, "x": 104.8, "y": 11.5},
            {"id": 2, "x": 104.9, "y": 11.6}
        ],
        "links": [
            {"source": 1, "target": 2, "length": 100}
        ]
    }
    
    router = RouterEngine(graph_data)
    
    # First call should compute
    distances1, _ = router.dijkstra(1)
    
    # Second call should use cache (same result)
    distances2, _ = router.dijkstra(1)
    
    assert distances1 == distances2
    
    # Verify cache is used by checking the cache info
    cache_info = router._cached_dijkstra.cache_info()
    assert cache_info.hits > 0


def test_build_adjacency_list():
    """Test adjacency list building."""
    graph_data = {
        "nodes": [
            {"id": 1, "x": 104.8, "y": 11.5},
            {"id": 2, "x": 104.9, "y": 11.6}
        ],
        "links": [
            {"source": 1, "target": 2, "length": 100}
        ]
    }
    
    router = RouterEngine(graph_data)
    adj = router.build_adjacency_list()
    
    # Should have adjacency for node 1
    assert 1 in adj
    assert len(adj[1]) == 1
    assert adj[1][0] == (2, 100)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])