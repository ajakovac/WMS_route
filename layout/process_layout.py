import re
import numpy as np
import json

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from warehouse.warehouse_route import Warehouse


WH = Warehouse(name="WH_Test").layout_image("warehouse-layout.png")
WH.add_label("Packing", [110, 423])
WH.add_label("Receiving\nand shipping", [70, 485])
WH.add_label("Docking", [125, 550])
WH.add_label("Warehouse\noffice", [415, 670], label_type="center")
WH.add_label("Pallet Racking", [295, 387])
WH.add_label("Pallet Racking\n&Pick Shelving", [650, 387])
WH.add_label("MHE\ncharging", [730, 450], label_type="center")

bbox=dict(
        boxstyle="round,pad=0.5",
        facecolor="#f0f0f0",
        edgecolor="#333333",
        linewidth=1.5
    )
WH.add_label_type("row_label", fontsize=10, color="red", ha="left", va="center", bbox=bbox)
for i in range(9):
    WH.add_label(f"R{i+1}", [85 + i * 79, 90], label_type="row_label")
for i in range(9,15):
    WH.add_label(f"R{i+1}", [240 + (i-9) * 79, 460], label_type="row_label")


###############

WH.add_access_point("Docking", [150,570])


sx = 66
sy = 76
dx1 = 79
dx2 = 20

def fill_columns(row, num_columns):
    for i in range(num_columns):
        nbay = 2*(num_columns-i-1)+1
        WH.add_location(
            row=row,
            bay=nbay,
            cell=1,
            position=[sx + (row-1)*dx1, sy + 19 + i * 39],
            available=True,
            access_points=[f"PICK_{row}_{nbay}"]
        )
        WH.add_location(
            row = row,
            bay = nbay,
            cell  = 2,
            position = [sx + row*dx1-dx2, sy + 19 + i * 39],
            available = True,
            access_points = [f"PICK_{row}_{nbay}"]
        )
        WH.add_access_point(f"PICK_{row}_{nbay}", [sx + (row-0.5)*dx1 - dx2/2, sy + 19 + i * 39])
        WH.add_location(
            row = row,
            bay = nbay+1,
            cell = 1,
            position = [sx + (row-1)*dx1, sy + i * 39],
            available = True,
            access_points = [f"PICK_{row}_{nbay+1}"]
        )
        WH.add_location(
            row = row,
            bay = nbay+1,
            cell = 2,
            position = [sx + row*dx1-dx2, sy + i * 39],
            available = True,
            access_points = [f"PICK_{row}_{nbay+1}"]
        )
        WH.add_access_point(f"PICK_{row}_{nbay+1}", [sx + (row-0.5)*dx1 - dx2/2, sy + i * 39])

for row in range(1,3):
    fill_columns(row, 7)
for row in range(3,8):
    fill_columns(row, 8)
for row in range(8,10):
    fill_columns(row, 8)
for WHloc in WH.locations:
    loc = WH.locations[WHloc]
    if loc["row"] == 3 and loc["bay"] in [1,2] and loc["cell"] == 1:
        WH.locations[WHloc]["available"] = False
    if loc["row"] == 3 and loc["bay"] ==1:
        WH.locations[WHloc]["access_points"] = ["AP_3A"]


sx = 282
sy = 455

def fill_columns(row, cell, num_columns):
    for nbay in range(num_columns):
        WH.add_location(
            row = row,
            bay = nbay,
            cell = cell,
            position = [sx + 23*(cell-1) + (row-9-cell)*dx1, sy + nbay * 14.5],
            available = True,
            access_points = [f"PICK_{row}_{nbay+1}"]
        )
        WH.add_access_point(f"PICK_{row}_{nbay+1}", [sx +11.5 + (row-10.5)*dx1, sy + nbay * 14.5])


fill_columns(10, 1, 7)
for row in range(11,15):
    fill_columns(row, 1, 7)
    fill_columns(row, 2, 7)
fill_columns(15, 2, 7)

sx = 96
sy = 368

for row in range(1,3):
    WH.add_access_point(f"AP_{row}", [sx + (row-1)*dx1, sy])
    for bay in range(1,15):
        WH.add_edge(f"AP_{row}", f"PICK_{row}_{bay}")
WH.add_access_point("AP_3A", [sx + 2*dx1, sy])
WH.add_edge("AP_1", "AP_2")
WH.add_edge("AP_2", "AP_3A")
for bay in range(2,17):
    WH.add_edge(f"AP_3A", f"PICK_3_{bay}")

sy = 420
WH.add_access_point(f"AP_3", [sx + 2*dx1, sy])
WH.add_edge("AP_3", "AP_3A")
for bay in range(1,8):
    WH.add_edge(f"AP_3", f"PICK_10_{bay}")

for row in range(4,10):
    WH.add_access_point(f"AP_{row}", [sx + (row-1)*dx1, sy])
    for bay in range(1,17):
        WH.add_edge(f"AP_{row}", f"PICK_{row}_{bay}")
    if f"PICK_{row+7}_1" in WH.access_points:
        for bay in range(1,8):
            WH.add_edge(f"AP_{row}", f"PICK_{row+7}_{bay}")
    if row > 3:
        WH.add_edge(f"AP_{row}", f"AP_{row-1}")

sy = 570
for row in range(3,9):
    WH.add_access_point(f"AP_{row+7}", [sx + (row-1)*dx1, sy])
    WH.add_edge(f"AP_{row+7}", f"AP_{row}")
    for bay in range(1,7):
        WH.add_edge(f"AP_{row+7}", f"PICK_{row+7}_{bay}")
    if row > 3:
        WH.add_edge(f"AP_{row+7}", f"AP_{row+6}")

WH.add_edge("AP_10", "Docking")

WH.save_to_json("warehouse_layout.json")