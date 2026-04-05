import heapq
import json
import os
from itertools import combinations
from collections import OrderedDict

class RouteCache:
    def __init__(self, max_size=100):
        self.max_size = max_size
        self.cache = OrderedDict()

    def get(self, key):
        if key in self.cache:
            self.cache.move_to_end(key)  # Mark as recently used
            return self.cache[key]
        return None

    def set(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                # Remove least recently used
                self.cache.popitem(last=False)
        self.cache[key] = value

    def clear(self):
        self.cache.clear()


route_cache = RouteCache(max_size=100)


def get_cache_size():
    """Get the current size of the route cache."""
    return len(route_cache.cache)


def clear_route_cache():
    """Clear the route cache. Call this when the graph is modified."""
    route_cache.clear()


def load_graph(path):
    """Load a graph from a JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Graph file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        graph = json.load(f)

    if not isinstance(graph, dict):
        raise ValueError("Graph JSON must be a dictionary of adjacency mappings")

    return graph


def save_graph(path, graph):
    """Persist graph structure to a JSON file."""
    if not isinstance(graph, dict):
        raise ValueError("Graph must be a dictionary")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)


def dijkstra(graph, start):
    """
    Compute shortest paths from 'start' in a weighted graph.

    Parameters
    ----------
    graph : dict
        Dictionary of the form:
        {
            node1: {neighbor1: weight1, neighbor2: weight2, ...},
            node2: {neighbor3: weight3, ...},
            ...
        }
    start : hashable
        Start node.

    Returns
    -------
    distances : dict
        Shortest known distances from start to every reachable node.
    previous : dict
        Predecessor dictionary for path reconstruction.
    """

    # Initial distances: infinity for all nodes except the start
    distances = {node: float("inf") for node in graph}
    distances[start] = 0

    # To reconstruct paths
    previous = {node: None for node in graph}

    # Priority queue entries: (current_distance, node)
    priority_queue = [(0, start)]

    # Optional set for finalized nodes
    visited = set()

    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)

        # Skip if already processed
        if current_node in visited:
            continue
        visited.add(current_node)

        # Check all neighbors
        for neighbor, weight in graph[current_node].items():
            if weight < 0:
                raise ValueError("Dijkstra's algorithm requires non-negative weights.")

            new_distance = current_distance + weight

            # Relaxation step
            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous[neighbor] = current_node
                heapq.heappush(priority_queue, (new_distance, neighbor))

    return distances, previous

class SingleRoute:
    def __init__(self, graph, start):
        self.graph = graph
        self.start = start
        if self.start not in self.graph:
            raise KeyError(f"Start node not found in graph: {self.start}")
        cached = route_cache.get(start)
        if cached:
            self.distances = cached.distances
            self.previous = cached.previous
        else:
            self.distances, self.previous = dijkstra(self.graph, self.start)
            route_cache.set(start, self)
            

    def get_route(self, target):
        """Get a specific route from start to target from the stored route table."""
        if target not in self.graph:
            raise KeyError(f"Target node not found in graph: {target}")

        if self.distances[target] == float("inf"):
            # target not reachable from start
            return {
                "distance": float("inf"),
                "path": []
            }

        path = []
        current = target

        while current is not None:
            path.append(current)
            current = self.previous[current]

        path.reverse()
        return {
            "distance": self.distances[target],
            "path": path
        }

def route_with_stops(graph, nodes, round_trip=True, optimize=True):
    
    if not optimize:
        # Follow nodes in given order without optimization
        total_distance = 0
        full_path = []
        route_table = {}
        
        for i in range(len(nodes) - 1):
            start_node = nodes[i]
            end_node = nodes[i + 1]
            
            if start_node not in route_table:
                route_table[start_node] = SingleRoute(graph, start_node)
            
            segment = route_table[start_node].get_route(end_node)
            if segment["distance"] == float("inf"):
                raise ValueError(f"No path from {start_node} to {end_node}")
            
            total_distance += segment["distance"]
            if full_path:
                # Avoid duplicating nodes at junctions
                full_path.extend(segment["path"][1:])
            else:
                full_path.extend(segment["path"])
        
        if round_trip and len(nodes) > 1:
            # Add return trip from last to first
            last_node = nodes[-1]
            first_node = nodes[0]
            
            if last_node not in route_table:
                route_table[last_node] = SingleRoute(graph, last_node)
            
            return_segment = route_table[last_node].get_route(first_node)
            if return_segment["distance"] == float("inf"):
                raise ValueError(f"No path from {last_node} to {first_node}")
            
            total_distance += return_segment["distance"]
            full_path.extend(return_segment["path"][1:])
        
        return {"distance": total_distance, "path": full_path}
    
    # Original optimized TSP logic
    route_table = {node: SingleRoute(graph, node) for node in nodes}
    distances = [[route_table[node].distances[target] for target in nodes] for node in nodes]

    if round_trip:
        cost, tour = held_karp_with_path(distances, start=0, round_trip=True)
    else:
        end = len(nodes) - 1
        cost, tour = held_karp_with_path(distances, start=0, round_trip=False, end=end)
    graph_tour = [ route_table[nodes[i]].get_route(nodes[j])["path"] for i, j in zip(tour[:-1], tour[1:]) ]
    graph_tour = [node for segment in graph_tour for node in segment[:-1]] + [nodes[tour[-1]]]
    return {"distance": cost, "path": graph_tour}


def held_karp_with_path(dist, start=0, round_trip=True, end=None):
    """
    Solve the TSP path problem exactly with Held-Karp dynamic programming.

    Parameters
    ----------
    dist : list[list[float]]
        Distance matrix, where dist[i][j] is the cost from node i to node j.
    start : int
        Index of the starting node.
    round_trip : bool
        If True, return to the start node.
        If False, end at the specified end node.
    end : int or None
        Index of the ending node. If None, defaults to start for round_trip, or n-1 for one-way.

    Returns
    -------
    best_cost : float
        Total cost of the optimal tour.
    best_tour : list[int]
        Optimal tour as a list of node indices.
        If round_trip=True, includes the return to start.
        Example: [0, 2, 1, 3, 0]
        If round_trip=False:
        Example: [0, 2, 1, 3]
    """

    n = len(dist)
    if n == 0:
        return 0, []
    if n == 1:
        return (0, [start, start]) if round_trip else (0, [start])

    if end is None:
        end = start if round_trip else n - 1

    dp = {}

    # Initialize paths start -> k
    for k in range(n):
        if k == start:
            continue
        subset = frozenset([start, k])
        dp[(subset, k)] = (dist[start][k], start)

    # Build larger subsets
    for size in range(3, n + 1):
        for subset_tuple in combinations(range(n), size):
            if start not in subset_tuple:
                continue

            subset = frozenset(subset_tuple)

            for j in subset:
                if j == start:
                    continue

                prev_subset = subset - {j}
                best_cost = float("inf")
                best_parent = None

                for i in prev_subset:
                    if i == start:
                        continue

                    prev_cost, _ = dp[(prev_subset, i)]
                    candidate_cost = prev_cost + dist[i][j]

                    if candidate_cost < best_cost:
                        best_cost = candidate_cost
                        best_parent = i

                dp[(subset, j)] = (best_cost, best_parent)

    full_set = frozenset(range(n))

    if round_trip:
        # Original round trip logic: choose best ending and add return cost
        best_cost = float("inf")
        last_node = None

        for j in range(n):
            if j == start:
                continue

            path_cost, _ = dp[(full_set, j)]
            total_cost = path_cost + dist[j][start]

            if total_cost < best_cost:
                best_cost = total_cost
                last_node = j
    else:
        # One-way: use fixed end if specified, else best end
        if end is not None and end != start:
            last_node = end
            if (full_set, last_node) not in dp:
                return float("inf"), []
            best_cost, _ = dp[(full_set, last_node)]
        else:
            # Best end
            best_cost = float("inf")
            last_node = None

            for j in range(n):
                if j == start:
                    continue

                path_cost, _ = dp[(full_set, j)]

                if path_cost < best_cost:
                    best_cost = path_cost
                    last_node = j

    # Reconstruct path
    reverse_path = [last_node]
    subset = full_set
    current = last_node

    while current != start:
        _, parent = dp[(subset, current)]
        reverse_path.append(parent)
        subset = subset - {current}
        current = parent

    reverse_path.reverse()
    best_tour = reverse_path

    if round_trip:
        best_tour.append(start)

    return best_cost, best_tour