import heapq

def dijkstra(graph, start):
    distances = {}
    previous = {}
    heap = [(0, start)]

    while heap:
        current_distance, current_node = heapq.heappop(heap)

        if current_node in distances:
            continue  # Already visited with the shortest path

        distances[current_node] = current_distance

        for neighbor, weight in graph.get(current_node, []):
            if neighbor not in distances:
                heapq.heappush(heap, (current_distance + weight, neighbor))
                previous[neighbor] = current_node
        

    return distances, previous

def reconstruct_path(previous, target):
    path = []
    while target in previous or path == []:  # allow for direct start->target path
        path.append(target)
        target = previous.get(target)
        if target is None and path[-1] != target:
            break
    return path[::-1]


def build_adjacency_list(graph_data):
    adj = {}
    for edge in graph_data.get("links", []):
        src = edge["source"]
        tgt = edge["target"]
        length = edge.get("length", 1.0)

        if src not in adj:
            adj[src] = []
        if tgt not in adj:
            adj[tgt] = []

        adj[src].append((tgt, length))

        if not graph_data.get("directed", True):
            adj[tgt].append((src, length))  # undirected
    return adj



