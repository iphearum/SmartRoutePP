import math
from shapely.geometry import Point, LineString
from copy import deepcopy

class GraphHelper:
    def __init__(self, graph):
        if isinstance(graph, list):
            raise TypeError("Expected graph to be a dict with 'nodes' and 'links', but got a list.")
        self.graph = graph
        self.original_graph = graph  # Keep reference instead of deepcopy
        self.temp_nodes = []
        self.temp_edges = []

    def get_graph(self, include_temp=True):
        if not include_temp:
            return self.graph
        
        # Only create copy when temporary data exists
        if not self.temp_nodes and not self.temp_edges:
            return self.graph
            
        combined = {
            "nodes": self.graph["nodes"] + self.temp_nodes,
            "links": self.graph["links"] + self.temp_edges,
            "directed": self.graph.get("directed", True)
        }
        return combined

    def add_temp_point(self, lat: float, lon: float, connect=True, connection_distance=0.0005):
        all_ids = [n.get('id', 0) for n in self.original_graph["nodes"]] + [n.get('id', 0) for n in self.temp_nodes]
        new_id = min(all_ids + [0]) - 1

        temp_node = {
            'id': new_id,
            'x': lon,
            'y': lat,
            'temp': True
        }
        self.temp_nodes.append(temp_node)

        if connect:
            self._connect_temp_point(new_id, lon, lat, connection_distance)
        return new_id

    def _connect_temp_point(self, node_id: int, lon: float, lat: float, max_distance: float = 0.005):
        point = Point(lon, lat)
        found = False
        attempts = 0
        while not found and attempts < 5:
            for node in self.original_graph.get("nodes", []): 
                node_point = Point(node.get('x'), node.get('y'))
                if point.distance(node_point) <= max_distance:
                    self.temp_edges.append({
                        'source': node_id,
                        'target': node.get('id'),
                        'temp': True
                    })
                    self.temp_edges.append({
                        'source': node.get('id'),
                        'target': node_id,
                        'temp': True
                    })
                    found = True
                    break
            if not found:
                max_distance *= 2
                attempts += 1

    def clear_temp_points(self):
        self.temp_nodes = []
        self.temp_edges = []

    def prepare_for_routing(self, source_lat: float, source_lon: float,
                            target_lat: float, target_lon: float):
        self.clear_temp_points()
        source_id = self.add_temp_point(source_lat, source_lon)
        target_id = self.add_temp_point(target_lat, target_lon)
        return source_id, target_id

    def get_point_from_osmid(self, osmid):
        links = self.graph.get("links", [])
        for link in links:
            if link.get('osmid') == osmid:
                return {
                    "source": link.get("source"),
                    "target": link.get("target")
                }
        return None

    def create_point(self, lon: float, lat: float):
        return Point(lon, lat)

    def get_point_from_node_id(self, id: int):
        for node in self.graph.get("nodes", []):
            if node.get('id') == id:
                return {
                    "latitude": node.get('y'),
                    "longitude": node.get('x')
                }
        return None

    def get_id_from_point(self, point: Point):
        for node in self.graph.get("nodes", []):
            if node.get("x") == point.x and node.get("y") == point.y:
                return node.get("id")
        return None

    def is_point_on_edge(self, lat: float, lon: float, tolerance: float = 1e-5) -> bool:
        nodes = {n['id']: (n['x'], n['y']) for n in self.graph.get("nodes", [])}
        point = self.create_point(lon, lat)

        for edge in self.graph.get("links", []):
            if "geometry" in edge:
                coords = [(lon, lat) for lon, lat in edge["geometry"]]
                line = LineString(coords)
            else:
                src = edge.get("source")
                tgt = edge.get("target")
                if src in nodes and tgt in nodes:
                    src_coords = nodes[src]
                    tgt_coords = nodes[tgt]
                    line = LineString([src_coords, tgt_coords])
                else:
                    continue

            if line.distance(point) < tolerance:
                print(f"Point is on edge from {src} to {tgt} with distance: {line.distance(point)}")
                return True

        return False

    def closest_node(self, lat: float, lon: float): 
        point = Point(lon, lat)
        min_distance = float('inf')
        closest_node_id = None

        for node in self.graph.get("nodes", []): 
            node_lat = node.get('y')
            node_lon = node.get('x')
            distance = self.__haversine(lon, lat, node_lon, node_lat)

            if distance < min_distance:
                min_distance = distance
                closest_node_id = node['id']

        return closest_node_id

    def distance_to_the_point(self, lat: float, lon: float):
        """Find the distance from the given point to the closest node in the graph."""
        closest_id = self.closest_node(lat, lon)
        if closest_id is None:
            return None
            
        # Find the closest node coordinates
        for node in self.graph.get("nodes", []):
            if node.get('id') == closest_id:
                node_lat = node.get('y')
                node_lon = node.get('x')
                return {
                    "closest_node_id": closest_id,
                    "distance_meters": self.__haversine(lon, lat, node_lon, node_lat),
                    "node_coordinates": {"lat": node_lat, "lon": node_lon}
                }
        return None

    # helper method calculate the distance between lat and lon
    def __haversine(self, lon1, lat1, lon2, lat2):
        R = 6371000  # Earth radius in meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        d_phi = math.radians(lat2 - lat1)
        d_lambda = math.radians(lon2 - lon1)

        a = math.sin(d_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
   