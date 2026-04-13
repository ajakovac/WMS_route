import heapq
import re
import os
from itertools import combinations
from collections import OrderedDict
import numpy as np


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
    
    def size(self):
        return len(self.cache)


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

    return {
        "distances": distances,
        "previous": previous
    }


def get_direct_path(distances, previous, target):
    """Get a specific route from start to target from the stored route table."""
    if target not in distances:
        raise KeyError(f"Target node not found in graph: {target}")

    if distances[target] == float("inf"):
        # target not reachable from start
        return []

    path = []
    current = target

    while current is not None:
        path.append(current)
        current = previous[current]

    path.reverse()
    return path


class RouteOptimizer:
    def __init__(self, warehouse, max_cache_size=100):
        # warehouse is a warehouse layout, see for example warehouse_layout.json in the layout folder
        self.warehouse = warehouse
        self.route_cache = RouteCache(max_size=max_cache_size)
        self.nodes = None
        self.base_graph = {}
        for edge in self.warehouse.edges:
            from_node = edge["from"]
            to_node = edge["to"]
            distance = edge["distance"]
            if from_node not in self.base_graph:
                self.base_graph[from_node] = {}
            if to_node not in self.base_graph:
                self.base_graph[to_node] = {}
            self.base_graph[from_node][to_node] = distance
            if edge.get("bidirectional", False):
                self.base_graph[to_node][from_node] = distance

    def set_route(self, nodes):
        # nodes is a list of nodes, for example ["Docking", "PICK_1_1", "PICK_2_1"]
        self.nodes = nodes
        for node in nodes:
            if node not in self.warehouse.access_points and node not in self.warehouse.locations:
                raise KeyError(f"Node not found in warehouse: {node}")
        self.access_points = [ node for node in self.warehouse.access_points if not node.startswith("PICK_")]
        self.route_nodes = []
        self.pick_nodes = {}
        for node in nodes:
            if node in self.warehouse.locations:
                pick_node = self.warehouse.locations[node]["access_points"][0]
                self.route_nodes.append(pick_node)
                self.access_points.append(pick_node)
                m = re.match(r"PICK_(\d+)_(\d+)", pick_node)
                if m:
                    row = int(m.group(1))
                    bay = int(m.group(2))
                    if row not in self.pick_nodes:
                        self.pick_nodes[row] = []
                    self.pick_nodes[row].append(pick_node)
                else:
                    raise ValueError(f"Invalid pick node format: {pick_node}")
            else:
                self.route_nodes.append(node)
        self.graph = {}
        for node in self.access_points:
            edges = self.base_graph[node]
            self.graph[node] = { neighbor: edges[neighbor] for neighbor in edges if neighbor in self.access_points}
        for row, pick_nodes in self.pick_nodes.items():
            if len(pick_nodes) > 1:
                for p1, p2 in combinations(pick_nodes, 2):
                    self.graph[p1][p2] = np.linalg.norm(np.array(self.warehouse.access_points[p1]["position"]) - np.array(self.warehouse.access_points[p2]["position"]))
                    self.graph[p2][p1] = self.graph[p1][p2]
        return self
    
    def optimize_route(self, round_trip=False):
        if self.route_nodes is None:
            raise ValueError("Route nodes not set. Call set_route(nodes) first.")
        
        # Original optimized TSP logic
        route_table = {node: dijkstra(self.graph, node) for node in self.route_nodes}
        distances = [[route_table[node]["distances"][target] for target in self.route_nodes] for node in self.route_nodes]

        cost, tour = held_karp_with_path(distances, start=0, round_trip=round_trip)
        graph_tour = []
        for i, j in zip(tour[:-1], tour[1:]) :
            node = self.route_nodes[i]
            target = self.route_nodes[j]
            path = get_direct_path(route_table[node]["distances"], route_table[node]["previous"], target)
            graph_tour.append(path)
        graph_tour = [node for segment in graph_tour for node in segment[:-1]] + [self.route_nodes[tour[-1]]]
        return {"distance": cost, "path": graph_tour}


def held_karp_with_path(dist, start=0, round_trip=True):
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