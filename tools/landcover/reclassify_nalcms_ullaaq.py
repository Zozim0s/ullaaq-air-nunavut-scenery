#!/usr/bin/env python3
"""
Reclassify a clipped NALCMS 2020 raster into Ullaaq semantic landclasses.

The output preserves the source raster's dimensions, geotransform, projection,
and pixel alignment exactly. Only the class byte values are changed.

Ullaaq classes:
    0 = fallback / hydro / ignored
    1 = northern extent taiga
    2 = shrub tundra
    3 = true tundra
    4 = barren tundra
    5 = wet tundra
    6 = Nunavik town
"""

import argparse
import os
import sys

import numpy as np
from osgeo import gdal
from PIL import Image

gdal.UseExceptions()

ULLAAQ_NAMES = {
    0: "fallback / hydro / ignored",
    1: "northern extent taiga",
    2: "shrub tundra",
    3: "true tundra",
    4: "barren tundra",
    5: "wet tundra",
    6: "Nunavik town",
}

# NALCMS 2020 Level-2 -> Ullaaq semantic class.
# Classes not listed here remain 0.
NALCMS_TO_ULLAAQ = {
    1: 1,   # temperate/sub-polar needleleaf forest
    2: 1,   # sub-polar taiga needleleaf forest
    8: 2,   # temperate/sub-polar shrubland
    10: 3,  # temperate/sub-polar grassland
    11: 2,  # sub-polar/polar shrubland-lichen-moss
    12: 3,  # sub-polar/polar grassland-lichen-moss
    13: 4,  # sub-polar/polar barren-lichen-moss
    14: 5,  # wetland
    16: 4,  # barren lands
    17: 6,  # urban and built-up
    18: 0,  # water: handled by hydro
    19: 0,  # snow/ice: leave for separate treatment
}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("source", help="Clipped NALCMS source GeoTIFF")
    p.add_argument(
        "-o", "--output",
        default="+58-069_ullaaq_landclass.tif",
        help="Output Ullaaq categorical GeoTIFF",
    )
    p.add_argument(
        "--preview",
        default="+58-069_ullaaq_landclass.png",
        help="Diagnostic indexed PNG",
    )
    return p.parse_args()


def main():
    args = parse_args()

    if not os.path.isfile(args.source):
        sys.exit(f"Input not found: {args.source}")

    src = gdal.Open(args.source, gdal.GA_ReadOnly)
    if src is None:
        sys.exit(f"Cannot open {args.source}")
    if src.RasterCount < 1:
        sys.exit("Source raster has no bands")

    src_band = src.GetRasterBand(1)
    a = src_band.ReadAsArray()
    if a is None:
        sys.exit("Could not read source raster")

    out = np.zeros(a.shape, dtype=np.uint8)
    for nalcms_id, ullaaq_id in NALCMS_TO_ULLAAQ.items():
        out[a == nalcms_id] = ullaaq_id

    drv = gdal.GetDriverByName("GTiff")
    dst = drv.Create(
        args.output,
        src.RasterXSize,
        src.RasterYSize,
        1,
        gdal.GDT_Byte,
        options=["COMPRESS=DEFLATE", "PREDICTOR=2", "TILED=YES"],
    )
    dst.SetGeoTransform(src.GetGeoTransform())
    dst.SetProjection(src.GetProjection())

    dst_band = dst.GetRasterBand(1)
    dst_band.WriteArray(out)
    dst_band.SetNoDataValue(0)
    dst_band.FlushCache()

    # Preserve useful source metadata.
    dst.SetMetadata(src.GetMetadata())
    dst.SetMetadataItem("ULLAAQ_CLASS_0", ULLAAQ_NAMES[0])
    for k in range(1, 7):
        dst.SetMetadataItem(f"ULLAAQ_CLASS_{k}", ULLAAQ_NAMES[k])
    dst.FlushCache()
    dst = None

    print(f"Source: {args.source}")
    print(f"Output: {args.output}")
    print(f"Size:   {src.RasterXSize} x {src.RasterYSize}")
    print("Geotransform preserved exactly:", src.GetGeoTransform())
    print()

    values, counts = np.unique(out, return_counts=True)
    total = out.size
    print("Class coverage:")
    for value, count in zip(values, counts):
        name = ULLAAQ_NAMES.get(int(value), "unknown")
        print(
            f"  {int(value)}  {name:28s} "
            f"{int(count):10,d} px  {100.0 * count / total:6.2f}%"
        )

    # Show any NALCMS values that were not explicitly mapped.
    source_values = sorted(int(v) for v in np.unique(a))
    unmapped = [v for v in source_values if v not in NALCMS_TO_ULLAAQ]
    print()
    print("NALCMS values present:", source_values)
    print("Unmapped values:", unmapped if unmapped else "none")

    # Indexed diagnostic PNG. Colors have no compiler significance.
    palette = [
        (0, 0, 0),
        (25, 85, 40),
        (80, 125, 65),
        (165, 185, 120),
        (165, 145, 115),
        (55, 140, 125),
        (220, 45, 45),
    ]
    img = Image.fromarray(out, mode="P")
    flat = [c for rgb in palette for c in rgb]
    flat += [0, 0, 0] * (256 - len(palette))
    img.putpalette(flat)
    img.save(args.preview)
    print(f"Preview: {args.preview}")

    src = None


if __name__ == "__main__":
    main()
