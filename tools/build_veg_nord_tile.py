#!/usr/bin/env python3

import argparse
import collections
import shutil
import subprocess
import sys
from pathlib import Path

from osgeo import ogr


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)


def tile_name(lat, lon):
    return f"{lat:+03d}{lon:+04d}"


def run(cmd):
    print("+ " + " ".join(map(str, cmd)))
    subprocess.run(list(map(str, cmd)), check=True)


def remove_sqlite_family(path):
    for p in (
        path,
        Path(str(path) + "-wal"),
        Path(str(path) + "-shm"),
        Path(str(path) + "-journal"),
    ):
        try:
            p.unlink()
        except FileNotFoundError:
            pass


def inspect(path, layer_name, class_field="cl_carto"):
    ds = ogr.Open(str(path), 0)
    if ds is None:
        die(f"Could not open {path}")

    layer = ds.GetLayerByName(layer_name)
    if layer is None:
        die(f"Layer {layer_name!r} missing from {path}")

    defn = layer.GetLayerDefn()
    fields = tuple(
        defn.GetFieldDefn(i).GetNameRef()
        for i in range(defn.GetFieldCount())
    )

    idx = defn.GetFieldIndex(class_field)
    if idx < 0:
        die(f"{class_field!r} missing from {path}:{layer_name}")

    counts = collections.Counter()
    invalid = 0
    empty = 0
    features = 0

    layer.ResetReading()
    for feat in layer:
        features += 1

        value = feat.GetField(idx)
        if value is None or str(value).strip() == "":
            counts["<NULL>"] += 1
        else:
            counts[str(value)] += 1

        geom = feat.GetGeometryRef()
        if geom is None or geom.IsEmpty():
            empty += 1
        elif not geom.IsValid():
            invalid += 1

    e = layer.GetExtent(force=1)

    result = {
        "features": features,
        "invalid": invalid,
        "empty": empty,
        "counts": dict(sorted(counts.items())),
        "fields": fields,
        "extent": (float(e[0]), float(e[2]), float(e[1]), float(e[3])),
        "geom": ogr.GeometryTypeToName(defn.GetGeomType()),
    }

    layer = None
    ds = None
    return result


def compare(candidate, reference):
    problems = []

    if candidate["features"] != reference["features"]:
        problems.append(
            f"feature count differs: "
            f"{candidate['features']} vs {reference['features']}"
        )

    if candidate["counts"] != reference["counts"]:
        problems.append("cl_carto census differs")

    if candidate["fields"] != reference["fields"]:
        problems.append("field schema differs")

    if candidate["geom"] != reference["geom"]:
        problems.append(
            f"geometry type differs: "
            f"{candidate['geom']} vs {reference['geom']}"
        )

    if candidate["invalid"] != reference["invalid"]:
        problems.append(
            f"invalid count differs: "
            f"{candidate['invalid']} vs {reference['invalid']}"
        )

    for a, b, name in zip(
        candidate["extent"],
        reference["extent"],
        ("west", "south", "east", "north"),
    ):
        if abs(a - b) > 1e-9:
            problems.append(
                f"{name} extent differs: {a:.12f} vs {b:.12f}"
            )

    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lat", type=int)
    ap.add_argument("lon", type=int)

    ap.add_argument(
        "--source",
        type=Path,
        default=(
            Path.home()
            / "linGames/GIS/Canada/veg_nord/"
              "Veg_nord_SQL/veg_nord_53.sqlite"
        ),
    )

    ap.add_argument("--source-layer", default="veg_53")
    ap.add_argument("--class-field", default="cl_carto")
    ap.add_argument("--out-dir", type=Path)
    ap.add_argument("--compare", type=Path)
    ap.add_argument("--compare-layer", default="veg_nord")
    ap.add_argument("--force", action="store_true")

    args = ap.parse_args()

    ogr2ogr = shutil.which("ogr2ogr")
    if not ogr2ogr:
        die("ogr2ogr not found on PATH")

    tile = tile_name(args.lat, args.lon)
    west = args.lon
    south = args.lat
    east = west + 1
    north = south + 1

    source = args.source.expanduser().resolve()
    if not source.is_file():
        die(f"VEG_NORD source not found: {source}")

    if args.out_dir:
        out_dir = args.out_dir.expanduser().resolve()
    else:
        out_dir = (
            Path.cwd() / "work" / tile / "landcover"
        ).resolve()

    out_dir.mkdir(parents=True, exist_ok=True)

    source_gpkg = out_dir / f"{tile}_VEG_NORD_source.gpkg"
    tile_gpkg = out_dir / f"{tile}_VEG_NORD_tile.gpkg"

    existing = [p for p in (source_gpkg, tile_gpkg) if p.exists()]
    if existing and not args.force:
        die(
            "Output exists; use --force:\n  "
            + "\n  ".join(map(str, existing))
        )

    if args.force:
        remove_sqlite_family(source_gpkg)
        remove_sqlite_family(tile_gpkg)

    print(f"Tile:                 {tile}")
    print(f"Bounds:               {west}..{east} / {south}..{north}")
    print(f"Master source:        {source}")
    print(f"Source layer:         {args.source_layer}")
    print(f"Selected source:      {source_gpkg}")
    print(f"Production tile:      {tile_gpkg}")
    print()

    print("Stage 1: select complete polygons intersecting tile")
    run([
        ogr2ogr,
        "-f", "GPKG",
        "-t_srs", "EPSG:4326",
        "-spat_srs", "EPSG:4326",
        "-spat", west, south, east, north,
        "-dim", "XY",
        "-nlt", "MULTIPOLYGON",
        "-preserve_fid",
        "-nln", "veg_nord_source",
        source_gpkg,
        source,
        args.source_layer,
    ])

    print()
    print("Stage 2: exact one-degree clip")
    run([
        ogr2ogr,
        "-f", "GPKG",
        "-clipsrc", west, south, east, north,
        "-dim", "XY",
        "-nlt", "MULTIPOLYGON",
        "-preserve_fid",
        "-nln", "veg_nord",
        tile_gpkg,
        source_gpkg,
        "veg_nord_source",
    ])

    print()
    print("Running QA...")

    srcqa = inspect(
        source_gpkg,
        "veg_nord_source",
        args.class_field,
    )

    tileqa = inspect(
        tile_gpkg,
        "veg_nord",
        args.class_field,
    )

    print()
    print("VEG_NORD QA")
    print(f"  Selected features:  {srcqa['features']:,}")
    print(f"  Tile features:      {tileqa['features']:,}")
    print(f"  Geometry:           {tileqa['geom']}")
    print(f"  Invalid geometry:   {tileqa['invalid']:,}")
    print(f"  Empty geometry:     {tileqa['empty']:,}")
    print(
        "  Source extent:      "
        f"({srcqa['extent'][0]:.6f}, {srcqa['extent'][1]:.6f}) - "
        f"({srcqa['extent'][2]:.6f}, {srcqa['extent'][3]:.6f})"
    )
    print(
        "  Tile extent:        "
        f"({tileqa['extent'][0]:.6f}, {tileqa['extent'][1]:.6f}) - "
        f"({tileqa['extent'][2]:.6f}, {tileqa['extent'][3]:.6f})"
    )

    print("  cl_carto census:")
    width = max(map(len, tileqa["counts"]))
    for key, value in tileqa["counts"].items():
        print(f"    {key:<{width}}  {value:>8,}")

    failures = []

    if tileqa["features"] == 0:
        failures.append("zero output features")

    if tileqa["invalid"]:
        failures.append(
            f"{tileqa['invalid']} invalid output geometries"
        )

    if tileqa["empty"]:
        failures.append(
            f"{tileqa['empty']} empty output geometries"
        )

    if tileqa["counts"].get("<NULL>", 0):
        failures.append("null/empty cl_carto values")

    tw, ts, te, tn = tileqa["extent"]
    if (
        tw < west - 1e-9
        or ts < south - 1e-9
        or te > east + 1e-9
        or tn > north + 1e-9
    ):
        failures.append("output extent lies outside tile")

    if args.compare:
        ref_path = args.compare.expanduser().resolve()
        refqa = inspect(
            ref_path,
            args.compare_layer,
            args.class_field,
        )

        problems = compare(tileqa, refqa)

        print()
        print(f"Reference:            {ref_path}")
        print(f"  Candidate features: {tileqa['features']:,}")
        print(f"  Reference features: {refqa['features']:,}")
        print(
            "  cl_carto census:    "
            + ("PASS" if tileqa["counts"] == refqa["counts"] else "FAIL")
        )
        print(
            "  Field schema:       "
            + ("PASS" if tileqa["fields"] == refqa["fields"] else "FAIL")
        )
        print(
            "  Geometry type:      "
            + ("PASS" if tileqa["geom"] == refqa["geom"] else "FAIL")
        )
        print(
            "  Reference QA:       "
            + ("PASS" if not problems else "FAIL")
        )

        for problem in problems:
            print(f"    - {problem}")

        failures.extend(problems)

    print()

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"  - {failure}")
        raise SystemExit(1)

    print("PASS")
    print(f"Source selection: {source_gpkg}")
    print(f"Production tile:  {tile_gpkg}")
    print("Layer:            veg_nord")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        die(f"ogr2ogr failed with exit status {exc.returncode}")
    except KeyboardInterrupt:
        raise SystemExit(130)
