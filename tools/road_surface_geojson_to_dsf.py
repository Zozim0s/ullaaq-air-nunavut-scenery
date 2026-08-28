#!/usr/bin/env python3

import json
from pathlib import Path

ROOT = Path.home() / "linGames/Ullaaq-Air-Nunavik"

SRC = ROOT / "work/+58-069/stock-overlay/+58-069_road_surface.geojson"
OUT = ROOT / "work/+58-069/stock-overlay/+58-069_road_surfaces.txt"


def area(ring):
    a = 0.0
    pts = ring[:-1] if ring and ring[0] == ring[-1] else ring
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return a * 0.5


def prepare(ring, want_ccw):
    pts = [[float(p[0]), float(p[1])] for p in ring]

    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]

    is_ccw = area(pts) > 0

    if is_ccw != want_ccw:
        pts.reverse()

    return pts


data = json.loads(SRC.read_text())

polygons = []

for feat in data["features"]:
    geom = feat.get("geometry")
    if not geom:
        continue

    if geom["type"] == "Polygon":
        polygons.append(geom["coordinates"])
    elif geom["type"] == "MultiPolygon":
        polygons.extend(geom["coordinates"])


with OUT.open("w") as f:
    f.write("A\n")
    f.write("800\n")
    f.write("DSF2TEXT\n\n")

    f.write("PROPERTY sim/planet earth\n")
    f.write("PROPERTY sim/overlay 1\n")
    f.write("PROPERTY sim/west -69\n")
    f.write("PROPERTY sim/east -68\n")
    f.write("PROPERTY sim/south 58\n")
    f.write("PROPERTY sim/north 59\n")
    f.write("PROPERTY sim/creation_agent Ullaaq_Nunavik_road_surfaces\n\n")

    f.write("POLYGON_DEF lib/ullaaq/roads/gravel_surface.pol\n\n")

    windings = 0

    for poly in polygons:
        if not poly:
            continue

        f.write("BEGIN_POLYGON 0 0 2\n")

        for i, ring in enumerate(poly):
            pts = prepare(ring, want_ccw=(i == 0))

            if len(pts) < 3:
                continue

            f.write("BEGIN_WINDING\n")
            for lon, lat in pts:
                f.write(f"POLYGON_POINT {lon:.9f} {lat:.9f}\n")
            f.write("END_WINDING\n")
            windings += 1

        f.write("END_POLYGON\n")

print(f"Wrote: {OUT}")
print(f"Surface polygons: {len(polygons)}")
print(f"Windings: {windings}")
