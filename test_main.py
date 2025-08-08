# tests/test_full_temp_route_perf.py
import time
import pytest
from httpx import AsyncClient
from main import app

pytestmark = pytest.mark.anyio  # tell pytest to run async tests

@pytest.fixture
def anyio_backend():
    return "asyncio"  # force asyncio, avoid Trio import

START = (11.568091, 104.893365)
END   = (11.557953, 104.908560)

async def test_full_temp_route_total_time():
    print(">>> START of test_full_temp_route_total_time")  # should always show with -s
    t0 = time.perf_counter()
    async with AsyncClient(app=app, base_url="http://test") as client:
        form = {"s_lat": START[0], "s_lon": START[1], "d_lat": END[0], "d_lon": END[1]}
        r = await client.post("/full_temp_route", data=form)
        print(">>> status:", r.status_code, "| ctype:", r.headers.get("content-type", ""))
        # Don’t assert HTML yet—just measure
        assert r.status_code == 200, r.text
    t1 = time.perf_counter()
    print(f">>> Total test time: {t1 - t0:.4f}s")
