import matplotlib.pyplot as plt
import numpy as np
import json
import os

class Warehouse:
    def __init__(self, name="Warehouse"):
        self.name = name
        self.access_points = {}
        self.locations = {}
        self.edges = []
        self.labels = []
        self.label_types = {
            "default": {"fontsize": 8, "color": "black", "ha": "left", "va": "top"},
            "center": {"fontsize": 8, "color": "black", "ha": "center", "va": "center"}
        }

    def layout_image(self, image_file):
        self.image_file = image_file
        self.img = plt.imread(image_file)
        return self

    def load_from_json(self, json_file):
        with open(json_file, "r") as f:
            data = json.load(f)
        self.image_file = data["layout_image"]
        complete_image_path = os.path.join(os.path.dirname(json_file), self.image_file)
        print(f"Loading warehouse layout from {json_file}, image path: {complete_image_path}")
        self.img = plt.imread(complete_image_path)
        self.name = data["name"]
        self.access_points = data["access_points"]
        self.locations = data["locations"]
        self.edges = data["edges"]
        self.labels = data["labels"] or []
        self.label_types = data["label_types"] or {}
        return self
    
    def save_to_json(self, json_file):
        with open(json_file, "w") as f:
            json.dump({
                "layout_image": self.image_file,
                "name": self.name,
                "locations": self.locations,
                "access_points": self.access_points,
                "edges": self.edges,
                "labels": self.labels,
                "label_types": self.label_types
            }, f, default=str, indent=2)

    def add_location(self, row, bay, cell, position, available=True, access_points=None, metadata=None):
        self.locations[f"R{row}_B{bay}_C{cell}"] = {
            "_id": f"R{row}_B{bay}_C{cell}",
            "warehouseID": self.name,
            "row": row,
            "bay": bay,
            "cell" : cell,
            "position": position,
            "available": available,
            "access_points" : access_points if access_points else [],
            "metadata": metadata if metadata else {}
        }
    
    def add_access_point(self, ap_id, position):
        self.access_points[ap_id] = {
            "position": position
        }

    def add_edge(self, ap1, ap2):
        p1 = np.array(self.access_points[ap1]["position"])
        p2 = np.array(self.access_points[ap2]["position"])
        self.edges.append({
            "from": ap1,
            "to": ap2,
            "distance": np.linalg.norm(p1 - p2),
            "bidirectional": True
        })

    def add_label_type(self, label_type, **metadata):
        self.label_types[label_type] = metadata

    def add_label(self, label, position, label_type="default"):
        if label_type not in self.label_types:
            raise ValueError(f"Label type '{label_type}' is not defined")
        self.labels.append({
            "label": label,
            "position": position,
            "type": label_type
        })

    def show_layout(self, fig=None, ax=None, **kwargs):
        if fig is None or ax is None:
            fig, ax = plt.subplots(figsize=(12, 8))
        ax.imshow(self.img, **kwargs)
        return fig, ax

    def show_locations(self, ax, locations=None, **kwargs):
        if locations is None:
            locations_dict = self.locations.values()
        else:
            locations_dict = [self.locations[loc] for loc in locations]
        for loc in locations_dict:
            if not loc["available"]:
                print(f"Row {loc['row']+1} Bay {loc['bay']} is not available")
                continue
            p = loc["position"]
            ax.plot(p[0], p[1], "bo", **kwargs)

    def show_access_points(self, ax, access_points=None, **kwargs):
        if access_points is None:
            access_points = self.access_points
        for ap in access_points:
            ax.plot(self.access_points[ap]["position"][0], self.access_points[ap]["position"][1], "ro", **kwargs)

    def show_spots(self, ax, spots=None, **kwargs):
        if spots is None:
            self.show_locations(ax, **kwargs)
            self.show_access_points(ax, **kwargs)
            return self
        locations = []
        access_points = []
        for spot in spots:
            if spot in self.locations:
                locations.append(spot)
            elif spot in self.access_points:
                access_points.append(spot)
            else:
                raise KeyError(f"Spot not found in warehouse: {spot}")
        self.show_locations(ax, locations, **kwargs)
        self.show_access_points(ax, access_points, **kwargs)
        return self

    def show_edges(self, ax, **kwargs):
        for edge in self.edges:
            p_from = np.array(self.access_points[edge["from"]]["position"])
            p_to = np.array(self.access_points[edge["to"]]["position"])
            ax.plot([p_from[0], p_to[0]], [p_from[1], p_to[1]], "r--", linewidth=0.5, **kwargs)

    def show_connections(self, ax, nodes=None, **kwargs):
        if nodes is None:
            nodes = self.access_points.keys()
        for node in nodes:
            p_node = np.array(self.access_points[node]["position"])
            for edge in self.edges:
                if edge["from"] == node and edge["to"] in nodes:
                    p_to = np.array(self.access_points[edge["to"]]["position"])
                    ax.plot([p_node[0], p_to[0]], [p_node[1], p_to[1]], "r--", linewidth=0.5, **kwargs)
                elif edge["to"] == node and edge["from"] in nodes and edge["bidirectional"]:
                    p_from = np.array(self.access_points[edge["from"]]["position"])
                    ax.plot([p_from[0], p_node[0]], [p_from[1], p_node[1]], "r--", linewidth=0.5, **kwargs)

    def show_path(self, ax, path):
        if not path:
            return

        pts = np.array(
            [self.access_points[node]["position"] for node in path],
            dtype=float
        )

        # Draw route line
        ax.plot(
            pts[:, 0], pts[:, 1],
            color="limegreen",
            linewidth=2.5,
            alpha=0.9,
            zorder=2
        )

        # Draw point markers
        ax.scatter(
            pts[:, 0], pts[:, 1],
            s=90,
            c="gold",
            edgecolors="darkgreen",
            linewidths=1.5,
            zorder=3
        )

        # Highlight start/end
        ax.scatter(
            pts[0, 0], pts[0, 1],
            s=150, c="deepskyblue", edgecolors="navy",
            linewidths=2, zorder=4
        )
        ax.scatter(
            pts[-1, 0], pts[-1, 1],
            s=150, c="tomato", edgecolors="darkred",
            linewidths=2, zorder=4
        )

        # Count how many times each point has already been labeled
        seen_counts = {}

        for i, (x, y) in enumerate(pts):
            key = (x, y)
            k = seen_counts.get(key, 0)
            seen_counts[key] = k + 1

            # Place repeated labels around the point
            angle = 2 * np.pi * (k % 8) / 8.0
            radius = 12 + 8 * (k // 8)   # pixels

            dx = radius * np.cos(angle)
            dy = radius * np.sin(angle)

            ax.annotate(
                str(i + 1),
                (x, y),
                xytext=(dx, dy),
                textcoords="offset points",
                ha="center",
                va="center",
                fontsize=8,
                fontweight="bold",
                color="black",
                bbox=dict(
                    boxstyle="circle,pad=0.22",
                    fc="white",
                    ec="black",
                    lw=1
                ),
                arrowprops=dict(
                    arrowstyle="-",
                    color="gray",
                    lw=0.8,
                    shrinkA=4,
                    shrinkB=4
                ),
                zorder=5
            )

    def show_picking_points(self, ax, **kwargs):
        for loc in self.locations.values():
            if loc["available"] and loc["access_points"]:
                p = loc["position"]
                #ax.plot(p[0], p[1], "go")
                for ap in loc["access_points"]:
                    ap_pos = self.access_points[ap]["position"]
                    ax.plot([p[0], ap_pos[0]], [p[1], ap_pos[1]], "b--", linewidth=0.5, **kwargs)

    def show_labels(self, ax):
        for label in self.labels:
            ax.text(label["position"][0], label["position"][1], label["label"], **self.label_types.get(label["type"], {}))