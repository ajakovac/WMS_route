# WMS Route Service

Warehouse route planning microservice with Dijkstra shortest-path algorithm and map persistence.

## Features

- Load warehouse graph from `map.json`
- Compute shortest route(s) from a given start node
- Get single route to a target from precomputed table
- Partial map updates via `/modify_map` (merge mode)
- Change start node using `/set_start`
- Inspect map and route state via `/status`
- Visual graph output with Matplotlib (optional)

## Files

- `main.py` - service + route logic + endpoints
- `map.json` - graph data
- `frontend.html` - web UI dashboard with controls and map editor
- `test_route_service.py` - script testing endpoints
- `wms_cli.py` - command-line client for invoking REST endpoints

## Dependencies

- Python 3
- Flask
- networkx
- matplotlib
- plotly (for interactive visualization)
- requests (for test client)

Install dependencies:

```bash
pip install flask networkx matplotlib plotly requests
```

## Run service

```bash
cd /home/antal/Documents/WMS_route
python3 main.py
```

## Endpoints

### POST `/modify_map`

Partial update graph, merge changes, persist to map.json.

Request:

```json
{
  "graph": {
    "Aisle_A": {"Shelf_3": 2},
    "Shelf_3": {"Aisle_A": 2, "Packing": 4}
  },
  "start": "Entrance"
}
```

Response includes current graph and optionally recomputed routes.

### POST `/set_start`

Set the start node and compute all routes from it.

Request:

```json
{ "start": "Shelf_1" }
```

### GET `/get_route?target=<node>`

Get shortest route to a target from current start.

### GET `/status`

Returns current map, route table, current start, and map file path.

### GET `/visualize`

Returns an interactive Plotly visualization of the warehouse map.

- `GET /visualize` - Full map
- `GET /visualize?target=<node>` - Map with highlighted route to target

### GET `/`

Serves the frontend dashboard (web UI).

## Web Frontend

A complete web dashboard is available at `http://127.0.0.1:5000/` with:

- **Control Panel**: Set start node, query routes, visualize map
- **Visualization**: Interactive Plotly map display (updated in real-time)
- **Map Editor**: JSON textarea to edit warehouse graph directly

Simply open your browser and navigate to `http://127.0.0.1:5000/` after running the service.

## CLI client

Use this script to call the service from the command line:

```bash
python3 wms_cli.py frontend                           # Open web dashboard
python3 wms_cli.py modify_map map.json --start Entrance
python3 wms_cli.py set_start Shelf_1
python3 wms_cli.py get_route Packing
python3 wms_cli.py status
python3 wms_cli.py visualize                          # Full map
python3 wms_cli.py visualize --target Packing         # Map with route
```

## Test script

Run while service is running:

```bash
python3 test_route_service.py
```

## Notes

- `map.json` is updated in-place by `/modify_map` after merging new nodes/edges.
- Fill in graph as a dictionary of neighbor weight maps.
- `get_route` requires prior compute via `/set_start`.