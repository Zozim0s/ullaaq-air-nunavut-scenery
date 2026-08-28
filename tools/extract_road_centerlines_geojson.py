#!/usr/bin/env python3

import json
from pathlib import Path

ROOT = Path.home() / "linGames/Ullaaq-Air-Nunavik"
SRC = ROOT / "work/+58-069/stock-overlay/+58-069_roads_only.txt"
OUT = ROOT / "work/+58-069/stock-overlay/+58-069_road_centerlines.geojson"

features = []
coords = None

for raw in SRC.read_text().splitlines():
    line = raw.strip()

    if line.startswith("BEGIN_SEGMENT "):
        p = line.split()
        coords = [[float(p[-3]), float(p[-2])]]

    elif coords is not None and line.startswith("SHAPE_POINT "):
        p = line.split()
        coords.append([float(p[1]), float(p[2])])

    elif coords is not None and line.startswith("END_SEGMENT "):
        p = line.split()
        coords.append([float(p[-3]), float(p[-2])])

        if len(coords) >= 2:
            features.append({
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords,
                },
            })

        coords = None

OUT.write_text(json.dumps({
    "type": "FeatureCollection",
    "features": features,
}))

print(f"Wrote: {OUT}")
print(f"Road chains: {len(features)}")
