from shapely.geometry import Point, LineString

class GraphHelper:
    def __init__(self, graph):
        self.graph = graph

    def get_point_from_osmid(self, osmid):
        """
        Get (latitude, longitude) from a serialized graph (JSON-style node_link_data).
        """
        nodes = self.graph.get("links", [])
        for node in nodes: 
            if node.get('osmid') == osmid: 
                return(node.get('source'), node.get('target'))
            
        return None
    def get_point_from_node_id(self, point:Point):
        nodes = self.graph.get("node", [])
        for node in nodes: 
            if (node.get('y'),node.get('x')) == point:
                print(node.get('y'), node.get('x'))
            else: 
                print("hello world")

    def create_point(self, latlon_tuple):
        """
        Convert (latitude, longitude) to a Shapely Point.
        """
        if isinstance(latlon_tuple, (list, tuple)) and len(latlon_tuple) == 2:
            lat, lon = latlon_tuple
            return Point(lon, lat)  # x = lon, y = lat
        raise ValueError(f"Expected a tuple of (lat, lon), got: {latlon_tuple}")

    def is_point_on_node(self, point: Point) -> bool:
        """
        Check if the point matches any node in the graph.
        """
        for _, data in self.graph.nodes(data=True):
            node_point = Point(data['x'], data['y'])
            if point.equals(node_point):
                return True
        return False

    def is_point_on_edge(self, point: Point, edge_geometry: LineString) -> bool:
        """
        Check if the point lies exactly on the edge geometry.
        """
        return edge_geometry.distance(point) == 0

    def distance_to_edge(self, point: Point, edge_geometry: LineString) -> float:
        """
        Compute the distance from the point to the edge geometry.
        """
        return edge_geometry.distance(point)
