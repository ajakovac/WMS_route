import requests
import json

BASE = "http://127.0.0.1:5000"


def print_response(name, resp):
    print(f"--- {name} (status {resp.status_code}) ---")
    try:
        print(json.dumps(resp.json(), indent=2))
    except Exception:
        print(resp.text)


def main():
    # 1) modify_map with diff updates and auto-compute routes from Entrance
    diff_graph = {
        "Aisle_A": {"Shelf_3": 2},
        "Shelf_3": {"Aisle_A": 2, "Packing": 4}
    }

    r = requests.post(
        f"{BASE}/modify_map",
        json={"graph": diff_graph, "start": "Entrance"}
    )
    print_response("modify_map", r)
    assert r.status_code == 200
    assert r.json().get("routes") is not None

    # 2) get_route with specific target
    r = requests.get(f"{BASE}/get_route", params={"target": "Packing"})
    print_response("get_route target=Packing", r)
    assert r.status_code == 200
    assert r.json()["target"] == "Packing"
    assert r.json()["start"] == "Entrance"

    # 3) get_route with different target
    r = requests.get(f"{BASE}/get_route", params={"target": "Shelf_1"})
    print_response("get_route target=Shelf_1", r)
    assert r.status_code == 200
    assert r.json()["target"] == "Shelf_1"

    # 4) set_start to change starting point (cleaner API)
    r = requests.post(
        f"{BASE}/set_start",
        json={"start": "Shelf_1"}
    )
    print_response("set_start to Shelf_1", r)
    assert r.status_code == 200
    assert r.json()["start"] == "Shelf_1"
    assert r.json()["routes_count"] > 0

    # 5) get_route now uses Shelf_1 as start
    r = requests.get(f"{BASE}/get_route", params={"target": "Packing"})
    print_response("get_route target=Packing (from Shelf_1)", r)
    assert r.status_code == 200
    assert r.json()["start"] == "Shelf_1"
    assert r.json()["path"][-1] == "Packing"

    # 6) change start again using set_start (alternative method)
    r = requests.post(
        f"{BASE}/set_start",
        json={"start": "Shelf_2"}
    )
    print_response("set_start to Shelf_2", r)
    assert r.status_code == 200
    assert r.json()["start"] == "Shelf_2"

    # 7) status shows current state
    r = requests.get(f"{BASE}/status")
    print_response("status", r)
    assert r.status_code == 200
    assert r.json()["current_start"] == "Shelf_2"

    print("\n✅ All tests passed.")


if __name__ == "__main__":
    main()
