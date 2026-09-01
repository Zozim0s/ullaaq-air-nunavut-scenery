#!/usr/bin/env python3
"""Compare authoritative NHN water-feature count to Ortho4XP Step-1 WATER seeds."""

from __future__ import annotations
import argparse
from collections import Counter
from pathlib import Path
from osgeo import ogr

def clean_lines(path):
    with path.open() as f:
        for line in f:
            s = line.split("#", 1)[0].strip()
            if s:
                yield s

def parse_poly(path):
    it = iter(clean_lines(path))
    nverts = int(next(it).split()[0])
    for _ in range(nverts): next(it)
    nsegs = int(next(it).split()[0])
    for _ in range(nsegs): next(it)
    nholes = int(next(it).split()[0])
    for _ in range(nholes): next(it)
    nregions = int(next(it).split()[0])
    attrs = Counter()
    for _ in range(nregions):
        q = next(it).split()
        attrs[int(float(q[3]))] += 1
    return nregions, attrs

def feature_count(gpkg, layer_name):
    ds = ogr.Open(str(gpkg))
    if ds is None:
        raise SystemExit(f"Could not open {gpkg}")
    lyr = ds.GetLayerByName(layer_name)
    if lyr is None:
        raise SystemExit(f"Layer {layer_name!r} not found in {gpkg}")
    n = lyr.GetFeatureCount()
    ds = None
    return n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpkg", type=Path, required=True)
    ap.add_argument("--layer", default="water")
    ap.add_argument("--poly", type=Path, required=True)
    args = ap.parse_args()

    expected = feature_count(args.gpkg.expanduser(), args.layer)
    total, attrs = parse_poly(args.poly.expanduser())
    actual = attrs[1]

    print(f"Total .poly regions: {total}")
    for k, v in sorted(attrs.items()):
        print(f"attr {k:>3}: {v}")
    print()
    print(f"NHN water features: {expected}")
    print(f".poly WATER seeds:  {actual}")
    print("PASS" if actual == expected else "FAIL")
    raise SystemExit(0 if actual == expected else 1)

if __name__ == "__main__":
    main()
