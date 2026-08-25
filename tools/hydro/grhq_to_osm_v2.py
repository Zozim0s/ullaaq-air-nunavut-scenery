#!/usr/bin/env python3
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path
from shapely import wkb

src = Path("/home/mike/linGames/X-Plane 12/Development/Replacement Mesh/source/Hydro/+58-069/+58-069_GRHQ_water_clipped.gpkg")
dst = Path("/home/mike/Ortho4XP/OSM_data/+50-070/+58-069/custom_water/grhq_water.osm")

conn = sqlite3.connect(src)
cur = conn.cursor()

root = ET.Element("osm", version="0.6", generator="GRHQ_to_Ortho4XP")

next_node = -1
next_way = -1
next_rel = -1

def add_ring(coords):
    global next_node, next_way
    refs = []

    for coord in coords:
        x, y = coord[0], coord[1]
        nid = next_node
        next_node -= 1

        ET.SubElement(
            root,
            "node",
            id=str(nid),
            lon=f"{x:.10f}",
            lat=f"{y:.10f}",
            version="1",
        )
        refs.append(nid)

    wid = next_way
    next_way -= 1

    way = ET.SubElement(root, "way", id=str(wid), version="1")
    for nid in refs:
        ET.SubElement(way, "nd", ref=str(nid))

    return wid

def gpkg_to_shapely(blob):
    flags = blob[3]
    envelope_code = (flags >> 1) & 0b111
    envelope_sizes = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}

    if envelope_code not in envelope_sizes:
        raise ValueError(f"Unsupported GeoPackage envelope code: {envelope_code}")

    return wkb.loads(blob[8 + envelope_sizes[envelope_code]:])

cur.execute("""
SELECT column_name
FROM gpkg_geometry_columns
WHERE table_name = 'water'
""")
row = cur.fetchone()

if row is None:
    raise RuntimeError("No geometry column registered for layer 'water'")

geom_column = row[0]
cur.execute(f'SELECT "{geom_column}" FROM "water"')

count = 0

for (blob,) in cur:
    if blob is None:
        continue

    geom = gpkg_to_shapely(blob)

    if geom.geom_type == "Polygon":
        polygons = [geom]
    elif geom.geom_type == "MultiPolygon":
        polygons = list(geom.geoms)
    else:
        continue

    for poly in polygons:
        if poly.is_empty:
            continue

        outer_way = add_ring(poly.exterior.coords)

        rel_id = next_rel
        next_rel -= 1
        rel = ET.SubElement(root, "relation", id=str(rel_id), version="1")

        ET.SubElement(
            rel,
            "member",
            type="way",
            ref=str(outer_way),
            role="outer",
        )

        for ring in poly.interiors:
            inner_way = add_ring(ring.coords)
            ET.SubElement(
                rel,
                "member",
                type="way",
                ref=str(inner_way),
                role="inner",
            )

        ET.SubElement(rel, "tag", k="type", v="multipolygon")
        ET.SubElement(rel, "tag", k="natural", v="water")
        count += 1

conn.close()
dst.parent.mkdir(parents=True, exist_ok=True)

tree = ET.ElementTree(root)

# Ortho4XP's legacy OSM parser is line-oriented, so the XML must be
# pretty-printed with each node/way/member/tag and closing </osm> on its own line.
ET.indent(tree, space="  ")
tree.write(dst, encoding="utf-8", xml_declaration=True)

print(f"Wrote {count:,} water polygons")
print(dst)
print("Output is line-formatted for Ortho4XP's legacy OSM parser.")
