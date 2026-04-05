import os
from flask import Flask, request, jsonify, abort, send_file

from graph_visualize import visualize_graph_plotly
from compute_route import load_graph, save_graph, route_with_stops, clear_route_cache, get_cache_size

app = Flask(__name__)
graph_file = os.getenv("GRAPH_MAP_FILE", "map.json")
graph = load_graph(graph_file)


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
    nodes_str = request.args.get("nodes")
    if not nodes_str:
        return jsonify({"error": "'nodes' query parameter is required (comma-separated list)"}), 400

    nodes = [node.strip() for node in nodes_str.split(",") if node.strip()]
    if not nodes:
        return jsonify({"error": "At least one node must be provided"}), 400

    round_trip_str = request.args.get("round_trip", "true")
    round_trip = round_trip_str.lower() == "true"
    
    optimize_str = request.args.get("optimize", "true")
    optimize = optimize_str.lower() == "true"

    try:
        result = route_with_stops(graph, nodes, round_trip=round_trip, optimize=optimize)
    except KeyError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(result)


@app.route("/status", methods=["GET"])
def status_api():
    """Return current map state and cache information."""
    return jsonify({
        "map": graph,
        "cache_size": get_cache_size(),
        "map_file": graph_file
    })


@app.route("/modify_map", methods=["POST"])
def modify_map_api():
    global graph
    payload = request.get_json(force=True)
    new_graph = payload.get("graph")

    if not isinstance(new_graph, dict):
        return jsonify({"error": "graph must be a dict"}), 400

    existing_graph = graph

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
        graph = existing_graph  # Update global graph
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    clear_route_cache()  # Clear cache since graph has changed

    return jsonify({"graph": graph, "cache_cleared": True})


@app.route("/visualize", methods=["GET"])
def visualize_api():
    """Return interactive HTML visualization of the current map and optional route."""
    nodes_str = request.args.get("nodes")
    round_trip_str = request.args.get("round_trip", "true")
    round_trip = round_trip_str.lower() == "true"
    optimize_str = request.args.get("optimize", "true")
    optimize = optimize_str.lower() == "true"

    route = None
    title = "Warehouse Map"

    if nodes_str:
        nodes = [node.strip() for node in nodes_str.split(",") if node.strip()]
        if nodes:
            try:
                route_data = route_with_stops(graph, nodes, round_trip=round_trip, optimize=optimize)
                route = route_data["path"]
                route_type = "Optimized" if optimize else "Sequential"
                trip_type = "Round Trip" if round_trip else "One Way"
                title = f"Warehouse Route: {route_type} {trip_type} ({', '.join(nodes)})"
            except (KeyError, ValueError):
                pass  # No route, just show map

    plot_div = visualize_graph_plotly(graph, route=route, title=title)

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

    
