#!/usr/bin/env python3
"""Command-line client for WMS Route Service (HTTP API)."""

import argparse
import json
import sys

import requests

BASE = "http://127.0.0.1:5000"


def run_modify_map(graph_path, start=None):
    with open(graph_path, "r", encoding="utf-8") as f:
        graph = json.load(f)

    body = {"graph": graph}
    if start:
        body["start"] = start

    r = requests.post(f"{BASE}/modify_map", json=body)
    r.raise_for_status()
    print(json.dumps(r.json(), indent=2))


def run_set_start(start):
    r = requests.post(f"{BASE}/set_start", json={"start": start})
    r.raise_for_status()
    print(json.dumps(r.json(), indent=2))


def run_get_route(target):
    r = requests.get(f"{BASE}/get_route", params={"target": target})
    r.raise_for_status()
    print(json.dumps(r.json(), indent=2))


def run_status():
    r = requests.get(f"{BASE}/status")
    r.raise_for_status()
    print(json.dumps(r.json(), indent=2))


def run_visualize(target=None):
    params = {}
    if target:
        params["target"] = target
    r = requests.get(f"{BASE}/visualize", params=params)
    r.raise_for_status()
    print("Open browser to:", f"{BASE}/visualize" + ("?" + "&".join(f"{k}={v}" for k, v in params.items()) if params else ""))


def run_frontend():
    print(f"Open browser to: {BASE}/")
    print("Frontend is running at the root path.")


def main():
    parser = argparse.ArgumentParser(description="WMS Route Service CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("modify_map", help="Push latest graph JSON and optionally set start")
    p.add_argument("graph", help="Path to graph JSON file")
    p.add_argument("--start", help="Start node for route computation", default=None)

    p = sub.add_parser("set_start", help="Set start node and compute all routes")
    p.add_argument("start", help="Start node")

    p = sub.add_parser("get_route", help="Get route to target from current start")
    p.add_argument("target", help="Target node")

    p = sub.add_parser("status", help="Get current service state")

    p = sub.add_parser("visualize", help="Open browser visualization")
    p.add_argument("--target", help="Target node to highlight route", default=None)

    p = sub.add_parser("frontend", help="Open the web frontend dashboard")

    args = parser.parse_args()

    try:
        if args.cmd == "modify_map":
            run_modify_map(args.graph, args.start)
        elif args.cmd == "set_start":
            run_set_start(args.start)
        elif args.cmd == "get_route":
            run_get_route(args.target)
        elif args.cmd == "status":
            run_status()
        elif args.cmd == "visualize":
            run_visualize(args.target)
        elif args.cmd == "frontend":
            run_frontend()    except requests.exceptions.HTTPError as exc:
        print(f"HTTP error: {exc}\n{exc.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
