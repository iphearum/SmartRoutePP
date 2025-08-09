# tests/test_routes.py
import pytest
from fastapi import status
import time

@pytest.mark.asyncio
async def test_full_temp_route_performance(async_client, setup_test_app):
    """Test route performance"""
    start_time = time.perf_counter()
    
    response = await async_client.post("/full_temp_route", data={
        "s_lat": 11.5,
        "s_lon": 104.9,
        "d_lat": 11.52,
        "d_lon": 104.92
    })
    
    duration = time.perf_counter() - start_time
    
    assert response.status_code == 200
    assert duration < 1.0  # Should complete within 1 second

@pytest.mark.asyncio
async def test_route_caching(async_client, setup_test_app):
    """Test route caching functionality"""
    # First request
    response1 = await async_client.post("/full_temp_route", data={
        "s_lat": 11.5,
        "s_lon": 104.9,
        "d_lat": 11.52,
        "d_lon": 104.92
    })
    
    # Second identical request (should be faster due to caching)
    start_time = time.perf_counter()
    response2 = await async_client.post("/full_temp_route", data={
        "s_lat": 11.5,
        "s_lon": 104.9,
        "d_lat": 11.52,
        "d_lon": 104.92
    })
    duration = time.perf_counter() - start_time
    
    assert response2.status_code == 200
    assert duration < 0.1  # Cached request should be very fast

def test_closest_node(test_client, setup_test_app):
    """Test closest node functionality"""
    response = test_client.get("/closest-node?lat=11.5&lon=104.9")
    assert response.status_code == 200
    assert isinstance(response.json(), int)