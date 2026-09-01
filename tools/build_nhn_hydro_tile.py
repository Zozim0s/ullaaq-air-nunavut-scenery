#!/usr/bin/env python3
"""
Build one NHN inland-water tile for the Ullaaq/Ortho4XP pipeline.

Topology: HNET Bank + HNET Delimiter + exact 1-degree tile boundary.
Wet/dry classification: HHYD Waterbody representative-point test.

Example:
  python tools/build_nhn_hydro_tile.py 58 -70 \
    --nhn-root "$HOME/linGames/GIS/Canada/NHN" \
    --out-dir "$HOME/linGames/GIS/Canada/NHN/tiles/+58-070"
"""

from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess, time
from datetime import datetime, timezone
from pathlib import Path
from osgeo import ogr, osr
from shapely import wkb
from shapely.geometry import LineString, MultiLineString, MultiPolygon, box
from shapely.ops import polygonize, unary_union
from shapely.prepared import prep
from shapely.strtree import STRtree

BANK_LAYER = "nhn_hnet_Bank_1"
DELIM_LAYER = "nhn_hnet_Delimiter_1"
WATER_LAYER = "nhn_hhyd_Waterbody_2"

def tag(lat, lon):
    return f"{lat:+03d}{lon:+04d}"

def run(cmd):
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.run(cmd, check=True)

def sha256(path, block=8*1024*1024):
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(block)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def src_meta(path):
    s = path.stat()
    return {
        "path": str(path.resolve()),
        "size_bytes": s.st_size,
        "mtime_utc": datetime.fromtimestamp(s.st_mtime, timezone.utc).isoformat(),
    }

def open_layer(path, name):
    ds = ogr.Open(str(path))
    if ds is None:
        raise RuntimeError(f"Could not open {path}")
    lyr = ds.GetLayerByName(name)
    if lyr is None:
        raise RuntimeError(f"Layer {name!r} not found in {path}")
    return ds, lyr

def shp(ogr_geom):
    return wkb.loads(bytes(ogr_geom.ExportToWkb()))

def iter_lines(g):
    if g is None or g.is_empty:
        return
    if g.geom_type in ("LineString", "LinearRing"):
        yield LineString(g.coords)
    elif g.geom_type in ("MultiLineString", "GeometryCollection"):
        for part in g.geoms:
            yield from iter_lines(part)

def iter_polys(g):
    if g is None or g.is_empty:
        return
    if g.geom_type == "Polygon":
        yield g
    elif g.geom_type in ("MultiPolygon", "GeometryCollection"):
        for part in g.geoms:
            yield from iter_polys(part)

def read_lines(path, layer):
    ds, lyr = open_layer(path, layer)
    stats = {"source_features": 0, "line_parts_retained": 0,
             "invalid_input_geometries": 0, "non_line_parts_dropped": 0}
    out = []
    for feat in lyr:
        stats["source_features"] += 1
        og = feat.GetGeometryRef()
        if og is None:
            continue
        g = shp(og)
        if not g.is_valid:
            stats["invalid_input_geometries"] += 1
        parts = list(iter_lines(g))
        out.extend(parts)
        stats["line_parts_retained"] += len(parts)
        if g.geom_type == "GeometryCollection":
            stats["non_line_parts_dropped"] += sum(
                p.geom_type not in ("LineString", "LinearRing", "MultiLineString")
                for p in g.geoms
            )
        elif g.geom_type not in ("LineString", "LinearRing", "MultiLineString"):
            stats["non_line_parts_dropped"] += 1
    ds = None
    return out, stats

def read_polys(path, layer):
    ds, lyr = open_layer(path, layer)
    stats = {"source_features": 0, "polygon_parts_retained": 0,
             "invalid_input_geometries": 0, "features_without_area": 0}
    out = []
    for feat in lyr:
        stats["source_features"] += 1
        og = feat.GetGeometryRef()
        if og is None:
            stats["features_without_area"] += 1
            continue
        g = shp(og)
        if not g.is_valid:
            stats["invalid_input_geometries"] += 1
            g = g.buffer(0)
        parts = [p for p in iter_polys(g) if not p.is_empty and p.area > 0]
        if not parts:
            stats["features_without_area"] += 1
            continue
        out.extend(parts)
        stats["polygon_parts_retained"] += len(parts)
    ds = None
    return out, stats

def srs4326():
    s = osr.SpatialReference()
    s.ImportFromEPSG(4326)
    return s

def write_gpkg(path, layer_name, geoms, geom_type, attrs=None):
    drv = ogr.GetDriverByName("GPKG")
    if path.exists():
        drv.DeleteDataSource(str(path))
    ds = drv.CreateDataSource(str(path))
    lyr = ds.CreateLayer(layer_name, srs=srs4326(), geom_type=geom_type, options=["SPATIAL_INDEX=YES"])
    if attrs:
        for key, ftype in attrs[0][0].items():
            lyr.CreateField(ogr.FieldDefn(key, ftype))
    defn = lyr.GetLayerDefn()
    for i, g in enumerate(geoms):
        feat = ogr.Feature(defn)
        if attrs:
            for key, value in attrs[i][1].items():
                feat.SetField(key, value)
        if geom_type == ogr.wkbMultiLineString and g.geom_type == "LineString":
            g = MultiLineString([g])
        if geom_type == ogr.wkbMultiPolygon and g.geom_type == "Polygon":
            g = MultiPolygon([g])
        feat.SetGeometry(ogr.CreateGeometryFromWkb(g.wkb))
        if lyr.CreateFeature(feat) != 0:
            raise RuntimeError(f"Failed writing feature {i} to {path}")
    ds = None

def clip(src, src_layer, dst, dst_layer, bbox):
    x0, y0, x1, y1 = bbox
    if dst.exists():
        dst.unlink()
    run([
        "ogr2ogr", "-f", "GPKG", str(dst), str(src), src_layer,
        "-nln", dst_layer,
        "-spat", str(x0), str(y0), str(x1), str(y1),
        "-clipsrc", str(x0), str(y0), str(x1), str(y1),
        "-nlt", "CONVERT_TO_LINEAR",
        "-lco", "SPATIAL_INDEX=YES",
    ])

def overlap_audit(polys, eps=1e-15):
    tree = STRtree(polys)
    pairs = overlaps = 0
    for i, g in enumerate(polys):
        for j in tree.query(g, predicate="intersects"):
            j = int(j)
            if j <= i:
                continue
            pairs += 1
            inter = g.intersection(polys[j])
            if not inter.is_empty and inter.area > eps:
                overlaps += 1
    return pairs, overlaps

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lat", type=int)
    ap.add_argument("lon", type=int)
    ap.add_argument("--nhn-root", type=Path,
                    default=Path.home()/"linGames/GIS/Canada/NHN")
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    if shutil.which("ogr2ogr") is None:
        raise SystemExit("ogr2ogr not found in PATH")

    t = tag(args.lat, args.lon)
    bbox = (args.lon, args.lat, args.lon+1, args.lat+1)
    root = args.nhn_root.expanduser()
    hnet = root/"rhn_nhn_hnet.gpkg"
    hhyd = root/"rhn_nhn_hhyd.gpkg"
    out = args.out_dir.expanduser()
    raw = out/"raw"; norm = out/"normalized"; qa = out/"qa"
    for d in (out, raw, norm, qa):
        d.mkdir(parents=True, exist_ok=True)

    bank_raw = raw/f"{t}_NHN_Bank_raw.gpkg"
    delim_raw = raw/f"{t}_NHN_Delimiter_raw.gpkg"
    water_raw = raw/f"{t}_NHN_Waterbody_raw.gpkg"

    started = time.time()
    clip(hnet, BANK_LAYER, bank_raw, "bank", bbox)
    clip(hnet, DELIM_LAYER, delim_raw, "delimiter", bbox)
    clip(hhyd, WATER_LAYER, water_raw, "waterbody", bbox)

    bank, bank_stats = read_lines(bank_raw, "bank")
    delim, delim_stats = read_lines(delim_raw, "delimiter")
    waterbody, water_stats = read_polys(water_raw, "waterbody")

    write_gpkg(norm/f"{t}_NHN_Bank_lines.gpkg", "bank", bank, ogr.wkbMultiLineString)
    write_gpkg(norm/f"{t}_NHN_Delimiter_lines.gpkg", "delimiter", delim, ogr.wkbMultiLineString)
    write_gpkg(norm/f"{t}_NHN_Waterbody_polygons.gpkg", "waterbody", waterbody, ogr.wkbMultiPolygon)

    print("Noding Bank + Delimiter + exact tile boundary...")
    noded = unary_union(bank + delim + [box(*bbox).boundary])

    print("Polygonizing...")
    faces = [p for p in polygonize(noded) if not p.is_empty and p.area > 0]

    print("Classifying faces against HHYD Waterbody...")
    wetmask = prep(unary_union(waterbody))
    wet_flags = [1 if wetmask.covers(p.representative_point()) else 0 for p in faces]
    wet = [p for p, flag in zip(faces, wet_flags) if flag]
    dry = len(faces) - len(wet)

    write_gpkg(qa/f"{t}_NHN_Bank_Delimiter_faces.gpkg",
               "faces", faces, ogr.wkbMultiPolygon)
    attrs = [({"wet": ogr.OFTInteger}, {"wet": flag}) for flag in wet_flags]
    write_gpkg(qa/f"{t}_NHN_Bank_Delimiter_classified.gpkg",
               "faces", faces, ogr.wkbMultiPolygon, attrs=attrs)

    final = out/f"{t}_NHN_water.gpkg"
    write_gpkg(final, "water", wet, ogr.wkbMultiPolygon)

    invalid_faces = sum(not p.is_valid for p in faces)
    invalid_wet = sum(not p.is_valid for p in wet)
    pairs, overlaps = overlap_audit(wet)

    report = {
        "tile": {"name": t, "lat": args.lat, "lon": args.lon,
                 "bbox_epsg4326": bbox},
        "method": {
            "topology": "HNET Bank + HNET Delimiter + exact tile boundary",
            "classification": "HHYD Waterbody representative-point wet/dry",
            "crs": "EPSG:4326",
        },
        "sources": {"hnet": src_meta(hnet), "hhyd": src_meta(hhyd)},
        "bank": bank_stats,
        "delimiter": delim_stats,
        "waterbody": water_stats,
        "faces": {"total": len(faces), "wet": len(wet), "dry": dry,
                  "invalid": invalid_faces},
        "final_water": {
            "path": str(final.resolve()),
            "features": len(wet),
            "invalid": invalid_wet,
            "positive_area_overlaps": overlaps,
            "intersection_candidate_pairs": pairs,
            "sha256": sha256(final),
        },
        "elapsed_seconds": round(time.time()-started, 3),
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }
    report_path = out/f"{t}_NHN_water_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")

    print()
    print(f"Faces total:                 {len(faces)}")
    print(f"Wet faces / output features: {len(wet)}")
    print(f"Dry faces:                   {dry}")
    print(f"Invalid faces:               {invalid_faces}")
    print(f"Invalid final water:         {invalid_wet}")
    print(f"Positive-area overlaps:      {overlaps}")
    print(f"Final:  {final}")
    print(f"Report: {report_path}")

    if invalid_faces or invalid_wet or overlaps:
        raise SystemExit("FAIL")
    print("PASS")

if __name__ == "__main__":
    main()
