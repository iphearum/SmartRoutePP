from shapely.geometry import Point, LineString
import heapq

class RouterEngine:
    def __init__(self, graph_data):
        self.graph_data = graph_data
        self.adj = self.build_adjacency_list()

    def build_adjacency_list(self):
        adj = {}
        for edge in self.graph_data.get("links", []):
            src = edge["source"]
            tgt = edge["target"]
            length = edge.get("length", 1.0)

            adj.setdefault(src, []).append((tgt, length))
            if not self.graph_data.get("directed", True):
                adj.setdefault(tgt, []).append((src, length))
        return adj

    def dijkstra(self, start):
        # Include ALL nodes, not just the ones in self.adj
        all_nodes = {n["id"] for n in self.graph_data["nodes"]}
        
        distances = {node: float('inf') for node in all_nodes}
        previous = {node: None for node in all_nodes}
        distances[start] = 0

        heap = [(0, start)]

        while heap:
            current_distance, current_node = heapq.heappop(heap)

            if current_distance > distances[current_node]:
                continue

            for neighbor, weight in self.adj.get(current_node, []):
                distance = current_distance + weight
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current_node
                    heapq.heappush(heap, (distance, neighbor))

        return distances, previous


    def reconstruct_path(self, previous, target):
        path = []
        current = target

        while current is not None:
            path.append(current)
            current = previous.get(current)

        path.reverse()

        if len(path) == 1 and path[0] != target:
            raise ValueError(f"Cannot reconstruct path to {target}")

        return path

    def route(self, start_id, end_id):
        if start_id not in self.adj:
            raise ValueError(f"Start node {start_id} not found in graph.")
        if end_id not in self.adj:
            raise ValueError(f"End node {end_id} not found in graph.")

        _, previous = self.dijkstra(start_id)
        path = self.reconstruct_path(previous, end_id)

        if not path or path[0] != start_id:
            raise ValueError(f"No valid path from {start_id} to {end_id}")

        geometry = self.get_path_geometry(path)
        return {
            "path": path,
            "geometry": geometry
        }

    def get_path_geometry(self, path):
        geometry = []

        # Fast lookup maps
        edge_map = {(e["source"], e["target"]): e for e in self.graph_data["links"]}
        node_map = {n["id"]: n for n in self.graph_data["nodes"]}

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]

            edge = edge_map.get((u, v)) or edge_map.get((v, u))  # for undirected fallback

            if edge and "geometry" in edge:
                geometry.extend(edge["geometry"])
            else:
                src = node_map.get(u)
                tgt = node_map.get(v)
                if not src:
                    raise ValueError(f"Missing node in node_map: {u}")
                if not tgt:
                    raise ValueError(f"Missing node in node_map: {v}")
                geometry.append([src["y"], src["x"]])
                geometry.append([tgt["y"], tgt["x"]])

        return geometry

