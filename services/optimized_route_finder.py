# services/optimized_route_finder.py
import heapq
import time
from typing import Dict, List, Tuple, Optional
from functools import lru_cache
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

class OptimizedRouterEngine:
    def __init__(self, graph_data: dict):
        self.graph_data = graph_data
        self.adjacency_list = self._build_optimized_adjacency_list()
        self.node_lookup = self._build_node_lookup()
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def _build_optimized_adjacency_list(self) -> Dict[int, List[Tuple[int, float]]]:
        """Build optimized adjacency list with edge weights"""
        adj_list = {}
        
        for node in self.graph_data.get("nodes", []):
            adj_list[node["id"]] = []
        
        for link in self.graph_data.get("links", []):
            source = link["source"]
            target = link["target"]
            weight = link.get("length", 1.0)
            
            if source in adj_list:
                adj_list[source].append((target, weight))
        
        return adj_list
    
    def _build_node_lookup(self) -> Dict[int, Dict]:
        """Build fast node lookup"""
        return {node["id"]: node for node in self.graph_data.get("nodes", [])}
    
    @lru_cache(maxsize=1000)
    def _dijkstra_cached(self, start_id: int, end_id: int) -> Optional[Tuple[List[int], float]]:
        """Cached Dijkstra's algorithm"""
        if start_id not in self.adjacency_list or end_id not in self.adjacency_list:
            return None
        
        # Priority queue: (distance, node_id, path)
        pq = [(0, start_id, [start_id])]
        visited = set()
        
        while pq:
            current_dist, current_node, path = heapq.heappop(pq)
            
            if current_node in visited:
                continue
            
            visited.add(current_node)
            
            if current_node == end_id:
                return path, current_dist
            
            for neighbor, weight in self.adjacency_list.get(current_node, []):
                if neighbor not in visited:
                    new_dist = current_dist + weight
                    new_path = path + [neighbor]
                    heapq.heappush(pq, (new_dist, neighbor, new_path))
        
        return None
    
    async def route_async(self, start_id: int, end_id: int) -> dict:
        """Async route calculation"""
        loop = asyncio.get_event_loop()
        
        try:
            # Run pathfinding in thread pool
            result = await loop.run_in_executor(
                self.executor, 
                self._dijkstra_cached, 
                start_id, 
                end_id
            )
            
            if not result:
                raise ValueError("No path found")
            
            path, total_length = result
            
            # Build geometry in parallel
            geometry_task = loop.run_in_executor(
                self.executor,
                self._build_geometry,
                path
            )
            
            geometry = await geometry_task
            
            return {
                "path": path,
                "length": total_length,
                "geometry": geometry,
                "nodes_count": len(path)
            }
            
        except Exception as e:
            logger.error(f"Route calculation failed: {e}")
            raise
    
    def _build_geometry(self, path: List[int]) -> List[List[float]]:
        """Build geometry coordinates from path"""
        geometry = []
        
        for node_id in path:
            if node_id in self.node_lookup:
                node = self.node_lookup[node_id]
                geometry.append([node.get("y", 0), node.get("x", 0)])  # [lat, lon]
        
        return geometry