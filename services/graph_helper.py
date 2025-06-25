from shapely.geometry import Point, LineString

class GraphHelper:
    def __init__(self, graph):
        self.graph = graph

    def get_point_from_osmid(self, osmid):
        links = self.graph.get("links", [])

        for link in links: 
            if link.get('osmid') == osmid: 
                return {
                    "source": link.get("sources"),
                    "target": link.get("target")
                }
        return None
    
    def create_point(self, latlon_tuple):
        if isinstance(latlon_tuple, (list, tuple)) and len(latlon_tuple) == 2:
            lat, lon = latlon_tuple
            return Point(lon, lat)  # x = lon, y = lat
        raise ValueError(f"Expected a tuple of (lat, lon), got: {latlon_tuple}")
    
    def get_point_from_node_id(self, id: int):
        nodes = self.graph
        for node in nodes: 
            if node.get('id') == id: 
                p = Point(node.get('y'), node.get('x'))
                return{
                    "latitude": p.x, 
                    "longitude": p.y
                }
        return None
    
    def get_id_from_point(self, point:Point): 
        nodes = self.graph.get("nodes", [])
        for node in nodes: 
            if node.get("x") == point.latitude and node.get("y") == point.longitude: 
                return node.get("id")
        return None
    
    def is_point_on_edge(self, point: Point, tolerance: float = 1e-6) -> bool:
        nodes = {n['id']: (n['x'], n['y']) for n in self.graph.get("nodes", [])}
        
        for edge in self.graph.get("links", []):
            if "geometry" in edge:
                coords = [(lon, lat) for lat, lon in edge["geometry"]]  # Reversed!
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
                return True

        return False


    