#!/usr/bin/env python3

import json
from pathlib import Path

ROOT = Path.home() / "linGames/Ullaaq-Air-Nunavik"
SRC = ROOT / "work/+58-069/forest/rcml.geojson"
OUT = ROOT / "work/+58-069/forest/+58-069_rcml_forests.txt"

FOREST = "lib/vegetation/forests/conifers/cold_low.for"
DENSITY = 160


def signed_area(ring):
    """Positive = CCW, negative = CW."""
    a = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        a += x1 * y2 - x2 * y1
    return a / 2.0


def prepare_ring(ring, want_ccw):
    pts = [(float(p[0]), float(p[1])) for p in ring]

    # DSF closes the winding itself; don't duplicate the terminal point.
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]

    is_ccw = signed_area(pts + [pts[0]]) > 0

    if is_ccw != want_ccw:
        pts.reverse()

    return pts


with SRC.open() as f:
    data = json.load(f)

with OUT.open("w") as out:
    out.write("A\n")
    out.write("800\n")
    out.write("DSF2TEXT\n\n")

    out.write("PROPERTY sim/planet earth\n")
    out.write("PROPERTY sim/overlay 1\n")
    out.write("PROPERTY sim/west -69\n")
    out.write("PROPERTY sim/east -68\n")
    out.write("PROPERTY sim/south 58\n")
    out.write("PROPERTY sim/north 59\n")
    out.write("PROPERTY sim/creation_agent Ullaaq_Nunavik_RcmL_forest_proof\n\n")

    out.write(f"POLYGON_DEF {FOREST}\n\n")

    polygon_count = 0
    winding_count = 0

    for feature in data["features"]:
        geom = feature.get("geometry")
        if not geom:
            continue

        gtype = geom["type"]
        coords = geom["coordinates"]

        if gtype == "Polygon":
            polygons = [coords]
        elif gtype == "MultiPolygon":
            polygons = coords
        else:
            continue

        for poly in polygons:
            if not poly:
                continue

            # One BEGIN_POLYGON contains the outer winding plus any holes.
            out.write(f"BEGIN_POLYGON 0 {DENSITY} 2\n")

            for i, ring in enumerate(poly):
                # X-Plane requires outer rings CCW and holes CW.
                pts = prepare_ring(ring, want_ccw=(i == 0))

                if len(pts) < 3:
                    continue

                out.write("BEGIN_WINDING\n")
                for lon, lat in pts:
                    out.write(f"POLYGON_POINT {lon:.9f} {lat:.9f}\n")
                out.write("END_WINDING\n")
                winding_count += 1

            out.write("END_POLYGON\n")
            polygon_count += 1

print(f"Wrote: {OUT}")
print(f"Forest polygons: {polygon_count}")
print(f"Windings: {winding_count}")
print(f"Density: {DENSITY}/255")
