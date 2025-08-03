# test/test_route_duration.py

import time
import pytest
from httpx import AsyncClient
from main import app  # or wherever you define FastAPI app

@pytest.mark.asyncio
async def test_route_duration():
    async with AsyncClient(app=app, base_url="http://test") as client:
        start_id = 1
        end_id = 20
        
        start = time.time()
        response = await client.get(f"/route?start_id={start_id}&end_id={end_id}")
        end = time.time()
        duration = end - start

        print(f"Route duration: {duration:.4f} seconds")
        
        assert response.status_code == 200
        data = response.json()
        assert "geometry" in data
        assert "path" in data
        assert "length" in data
        assert duration < 3  # you can change this based on expected performance
