#!/usr/bin/env python3
"""
Build an Ullaaq categorical landclass compiler mask from the existing
+58-069_landcover.gpkg.

Output class IDs:
    0 = fallback / unclassified
    1 = northern extent taiga
    2 = shrub tundra
    3 = true tundra (grass tundra)
    4 = barren tundra
    5 = wet tundra

The GeoTIFF is written in EPSG:4326 with exact 1-degree tile bounds.
Nearest-neighbour handling is used throughout because these are categorical
classes, not continuous data.
"""

import argparse
import os
import sys
import tempfile

import numpy as np
from osgeo import gdal, ogr, osr
from PIL import Image

gdal.UseExceptions()
ogr.UseExceptions()

CLASS_MAP = {
    "taiga": 1,
    "shrub_tundra": 2,
    "grass_tundra": 3,
    "barren_tundra": 4,
    "wetland": 5,
}

CLASS_NAMES = {
    0: "fallback / unclassified",
    1: "northern extent taiga",
    2: "shrub tundra",
    3: "true tundra",
    4: "barren tundra",
    5: "wet tundra",
}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        "gpkg",
        nargs="?",
        default="+58-069_landcover.gpkg",
        help="Input landcover GeoPackage",
    )
    p.add_argument(
        "-o",
        "--output",
        default="+58-069_ullaaq_landclass.tif",
        help="Output categorical GeoTIFF",
    )
    p.add_argument(
        "--preview",
        default="+58-069_ullaaq_landclass.png",
        help="Diagnostic PNG preview",
    )
    p.add_argument("--west", type=float, default=-69.0)
    p.add_argument("--east", type=float, default=-68.0)
    p.add_argument("--south", type=float, default=58.0)
    p.add_argument("--north", type=float, default=59.0)

    # Approx. 30 m at the middle of this tile:
    # ~30 m north/south and ~30 m east/west at 58.5 N.
    p.add_argument("--width", type=int, default=1965)
    p.add_argument("--height", type=int, default=3711)
    return p.parse_args()


def make_mask(args):
    src = ogr.Open(args.gpkg, 0)
    if src is None:
        raise RuntimeError(f"Cannot open {args.gpkg}")

    for layer_name in CLASS_MAP:
        if src.GetLayerByName(layer_name) is None:
            raise RuntimeError(f"Missing layer: {layer_name}")
    src = None

    driver = gdal.GetDriverByName("GTiff")
    ds = driver.Create(
        args.output,
        args.width,
        args.height,
        1,
        gdal.GDT_Byte,
        options=[
            "COMPRESS=DEFLATE",
            "PREDICTOR=2",
            "TILED=YES",
            "BIGTIFF=IF_SAFER",
        ],
    )
    if ds is None:
        raise RuntimeError(f"Could not create {args.output}")

    pixel_w = (args.east - args.west) / args.width
    pixel_h = (args.north - args.south) / args.height

    ds.SetGeoTransform(
        (args.west, pixel_w, 0.0, args.north, 0.0, -pixel_h)
    )

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    ds.SetProjection(srs.ExportToWkt())

    band = ds.GetRasterBand(1)
    band.Fill(0)
    band.SetNoDataValue(0)

    # Rasterize each semantic layer into the same categorical band.
    # ALL_TOUCHED=FALSE preserves the source classification conservatively.
    for layer_name, class_id in CLASS_MAP.items():
        print(f"Rasterizing {layer_name:15s} -> {class_id}")
        opts = gdal.RasterizeOptions(
            bands=[1],
            burnValues=[class_id],
            layers=[layer_name],
            allTouched=False,
        )
        gdal.Rasterize(ds, args.gpkg, options=opts)

    band.FlushCache()
    ds.FlushCache()
    ds = None


def report_and_preview(args):
    ds = gdal.Open(args.output)
    band = ds.GetRasterBand(1)
    a = band.ReadAsArray()

    values, counts = np.unique(a, return_counts=True)
    total = a.size

    print()
    print(f"Output: {args.output}")
    print(f"Size:   {ds.RasterXSize} x {ds.RasterYSize}")
    print(
        f"Bounds: {args.west}, {args.south} -> "
        f"{args.east}, {args.north}"
    )
    print()
    print("Class coverage:")
    for value, count in zip(values, counts):
        name = CLASS_NAMES.get(int(value), "unknown")
        pct = 100.0 * count / total
        print(f"  {int(value)}  {name:28s} {count:10,d} px  {pct:6.2f}%")

    # Diagnostic indexed PNG. The colors are only for inspection; the compiler
    # consumes the byte class IDs in the GeoTIFF.
    palette = [
        (0, 0, 0),          # 0 fallback
        (32, 92, 54),       # 1 taiga
        (91, 132, 82),      # 2 shrub tundra
        (157, 170, 112),    # 3 true tundra
        (176, 157, 126),    # 4 barren tundra
        (77, 139, 164),     # 5 wet tundra
    ]

    img = Image.fromarray(a.astype(np.uint8), mode="P")
    flat_palette = []
    for rgb in palette:
        flat_palette.extend(rgb)
    flat_palette.extend([0, 0, 0] * (256 - len(palette)))
    img.putpalette(flat_palette)
    img.save(args.preview)

    print(f"Preview: {args.preview}")
    ds = None


def main():
    args = parse_args()

    if not os.path.isfile(args.gpkg):
        sys.exit(f"Input not found: {args.gpkg}")

    make_mask(args)
    report_and_preview(args)


if __name__ == "__main__":
    main()
