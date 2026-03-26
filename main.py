import heapq
import json
import os

from flask import Flask, request, jsonify, abort, send_file
import matplotlib.pyplot as plt
import networkx as nx
import plotly.graph_objects as go
import plotly.offline as pyo


def dijkstra(graph, start, target=None):
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
    target : hashable, optional
        If given, the algorithm stops once the target is reached.

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

        # Early stop if target reached
        if target is not None and current_node == target:
            break

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


def reconstruct_path(previous, start, target):
    """
    Reconstruct the shortest path from start to target
    using the predecessor dictionary.
    """
    path = []
    current = target

    while current is not None:
        path.append(current)
        current = previous[current]

    path.reverse()

    if not path or path[0] != start:
        return None  # target not reachable from start

    return path


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


def visualize_graph(graph, route=None, title="Warehouse Map"):
    """Visualize the graph and optionally highlight a route."""
    G = nx.Graph()

    # Add weighted edges
    for node, neighbors in graph.items():
        for neighbor, weight in neighbors.items():
            G.add_edge(node, neighbor, weight=weight)

    pos = nx.spring_layout(G, seed=42)

    plt.figure(figsize=(10, 8))
    nx.draw_networkx_nodes(G, pos, node_color="lightblue", node_size=800)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold")

    # Draw base edges
    nx.draw_networkx_edges(G, pos, edge_color="gray", width=1.0)

    # Draw weights
    edge_labels = nx.get_edge_attributes(G, "weight")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color="black")

    # Highlight route if available
    if route:
        # route is list of nodes in order
        route_edges = list(zip(route, route[1:]))
        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=route_edges,
            edge_color="red",
            width=3.0,
            style="solid",
        )
        nx.draw_networkx_nodes(
            G,
            pos,
            nodelist=route,
            node_color="orange",
            node_size=900,
        )

def visualize_graph_plotly(graph, route=None, title="Warehouse Map"):
    """Generate interactive Plotly visualization of the graph."""
    G = nx.Graph()

    # Add weighted edges
    for node, neighbors in graph.items():
        print(node, neighbors)
        for neighbor, weight in neighbors.items():
            G.add_edge(node, neighbor, weight=weight)

    pos = nx.spring_layout(G, seed=42)

    # Create edge traces
    edge_x = []
    edge_y = []
    edge_text = []
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_text.append(f"{edge[2]['weight']}")

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=2, color='gray'),
        hoverinfo='text',
        text=edge_text,
        mode='lines'
    )

    # Highlight route edges if provided
    if route:
        route_edge_x = []
        route_edge_y = []
        route_edges = list(zip(route, route[1:]))
        for u, v in route_edges:
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            route_edge_x.extend([x0, x1, None])
            route_edge_y.extend([y0, y1, None])

        route_edge_trace = go.Scatter(
            x=route_edge_x, y=route_edge_y,
            line=dict(width=4, color='red'),
            hoverinfo='skip',
            mode='lines'
        )

    # Create node traces
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
        if route and node in route:
            node_color.append('orange')
        else:
            node_color.append('lightblue')

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        textposition="top center",
        hoverinfo='text',
        marker=dict(
            showscale=False,
            color=node_color,
            size=20,
            line_width=2
        )
    )

    # Create figure
    fig = go.Figure(data=[edge_trace, node_trace])
    if route:
        fig.add_trace(route_edge_trace)

    fig.update_layout(
        title=title,
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )

    return pyo.plot(fig, output_type='div', include_plotlyjs=True)


class WarehouseNavigator:
    """Warehouse graph route planner."""

    def __init__(self, graph, start = None):
        if not isinstance(graph, dict):
            raise ValueError("Graph must be a dict")
        self._start = start
        if self._start is None:
            if "default_start" in graph:
                self._start = graph["default_start"]
                del graph["default_start"]
            else:
                self._start = next(iter(graph))  # Just pick the first node as default start
        self.graph = graph
        self._routes = {}  # Dictionary: target -> {"distance": ..., "path": ...}
        self.compute_route()

    def compute_route(self):
        """Compute shortest paths from start to all reachable nodes and store results."""
        if self._start not in self.graph:
            raise KeyError(f"Start node '{self._start}' not found in graph")
        distances, previous = dijkstra(self.graph, self._start)
        self._routes = {}

        # Store routes to all reachable targets
        for target in self.graph:
            path = reconstruct_path(previous, self._start, target)
            if path is not None:
                self._routes[target] = {
                    "distance": distances[target],
                    "path": path
                }

    def get_route(self, target):
        """Get a specific route to target from the stored route table."""
        if not self._routes:
            raise RuntimeError("No routes computed yet. Call compute_route first.")

        if target not in self._routes:
            raise KeyError(f"No route to target '{target}' from start '{self._start}'")

        return {
            "start": self._start,
            "target": target,
            "distance": self._routes[target]["distance"],
            "path": self._routes[target]["path"],
        }

    def get_all_routes(self):
        """Get all computed routes from current start node."""
        if not self._routes:
            raise RuntimeError("No routes computed yet. Call compute_route first.")

        routes = {}
        for target, route_data in self._routes.items():
            routes[target] = {
                "start": self._start,
                "target": target,
                "distance": route_data["distance"],
                "path": route_data["path"],
            }
        return routes

    def starting_point(self, start=None):
        """Return the current starting point."""
        if start is not None:
            self._start = start
            self.compute_route()
        return self._start


app = Flask(__name__)
graph_file = os.getenv("GRAPH_MAP_FILE", "map.json")
current_navigator = None


def get_current_navigator():
    global current_navigator
    if current_navigator is None:
        graph = load_graph(graph_file)
        current_navigator = WarehouseNavigator(graph)
    return current_navigator


@app.after_request
def add_cors_headers(response):
    """Add CORS headers to all responses."""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


@app.route("/", methods=["GET"])
def index():
    """Serve the frontend."""
    return send_file("frontend.html")


@app.route("/get_route", methods=["GET"])
def get_route_api():
    navigator = get_current_navigator()
    target = request.args.get("target")

    if not target:
        return jsonify({"error": "'target' query parameter is required"}), 400

    if not navigator._routes:
        return jsonify({"error": "No routes computed yet. Call /set_start first."}), 404

    try:
        route = navigator.get_route(target)
    except KeyError as e:
        return jsonify({"error": str(e)}), 404

    return jsonify(route)


@app.route("/set_start", methods=["POST"])
def set_start_api():
    """Change the starting point and compute all routes from it."""
    payload = request.get_json(force=True)
    start = payload.get("start")

    if not start:
        return jsonify({"error": "'start' is required"}), 400

    navigator = get_current_navigator()
    try:
        navigator.starting_point(start)
    except KeyError as e:
        return jsonify({"error": str(e)}), 404

    return jsonify({
        "start": navigator.starting_point(),
        "routes_count": len(navigator._routes),
        "routes": navigator.get_all_routes()
    })


@app.route("/status", methods=["GET"])
def status_api():
    """Return current map state and computed routes from start node."""
    navigator = get_current_navigator()

    routes_info = None
    start_node = None
    if navigator._routes:
        routes_info = navigator.get_all_routes()
        start_node = navigator.starting_point()

    return jsonify({
        "map": navigator.graph,
        "current_start": start_node,
        "routes": routes_info,
        "map_file": graph_file
    })


@app.route("/modify_map", methods=["POST"])
def modify_map_api():
    payload = request.get_json(force=True)
    new_graph = payload.get("graph")

    if not isinstance(new_graph, dict):
        return jsonify({"error": "graph must be a dict"}), 400

    existing_graph = load_graph(graph_file)

    # Merge new values into existing graph (partial update semantics)
    for node, neighbors in new_graph.items():
        if not isinstance(neighbors, dict):
            return jsonify({"error": "Each node in graph must map to a dict of neighbors"}), 400

        if node not in existing_graph:
            existing_graph[node] = {}

        existing_graph[node].update(neighbors)

        # Ensure bidirectional entries are preserved/updated too
        for neighbor_node, weight in neighbors.items():
            if neighbor_node not in existing_graph:
                existing_graph[neighbor_node] = {}
            existing_graph[neighbor_node][node] = weight

    try:
        save_graph(graph_file, existing_graph)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    navigator = get_current_navigator()

    start = payload.get("start")
    if start is None or start == navigator.starting_point():
        try:
            navigator.compute_route()
        except KeyError as e:
            return jsonify({"error": str(e)}), 404
    else:
        try:
            navigator.starting_point(start)
        except KeyError as e:
            return jsonify({"error": str(e)}), 404
    routes_info = navigator.get_all_routes()

    return jsonify({"graph": existing_graph, "start": start, "routes": routes_info})


@app.route("/visualize", methods=["GET"])
def visualize_api():
    """Return interactive HTML visualization of the current map and optional route."""
    navigator = get_current_navigator()

    target = request.args.get("target")
    route = None
    title = "Warehouse Map"

    if target:
        try:
            route_data = navigator.get_route(target)
            route = route_data["path"]
            title = f"Warehouse Shortest Route: {navigator.starting_point()} → {target}"
        except KeyError:
            pass  # No route, just show map

    plot_div = visualize_graph_plotly(navigator.graph, route=route, title=title)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
    </head>
    <body>
        <h1>{title}</h1>
        {plot_div}
    </body>
    </html>
    """

    return html


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)

    
