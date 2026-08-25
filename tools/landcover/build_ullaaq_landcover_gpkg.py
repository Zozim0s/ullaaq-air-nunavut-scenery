#!/usr/bin/env python3
"""
Build the Ullaaq landcover GeoPackage directly from the semantic landclass raster.

Input class IDs:
    0 = fallback / hydro / ignored
    1 = northern extent taiga
    2 = shrub tundra
    3 = true tundra / grass tundra
    4 = barren tundra
    5 = wet tundra
    6 = Nunavik town

Output GeoPackage layers:
    taiga
    shrub_tundra
    grass_tundra
    barren_tundra
    wetland
    town

This deliberately uses the semantic raster as the single source of truth, so the
Step-1 vector boundaries and Step-3 raster classification cannot drift apart.
"""

import argparse
import os
import sys

import numpy as np
from osgeo import gdal, ogr, osr

gdal.UseExceptions()
ogr.UseExceptions()

CLASS_LAYERS = {
    1: "taiga",
    2: "shrub_tundra",
    3: "grass_tundra",
    4: "barren_tundra",
    5: "wetland",
    6: "town",
}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("source", help="Ullaaq semantic landclass GeoTIFF")
    p.add_argument(
        "-o", "--output",
        default="+58-069_landcover.gpkg",
        help="Output GeoPackage",
    )
    return p.parse_args()


def main():
    args = parse_args()

    if not os.path.isfile(args.source):
        sys.exit(f"Input not found: {args.source}")

    src = gdal.Open(args.source, gdal.GA_ReadOnly)
    if src is None:
        sys.exit(f"Cannot open {args.source}")

    band = src.GetRasterBand(1)
    arr = band.ReadAsArray()
    if arr is None:
        sys.exit("Could not read source raster")

    srs = osr.SpatialReference()
    srs.ImportFromWkt(src.GetProjection())
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

    gpkg_drv = ogr.GetDriverByName("GPKG")
    mem_drv = gdal.GetDriverByName("MEM")
    if gpkg_drv is None or mem_drv is None:
        sys.exit("Required GDAL/OGR driver unavailable")

    if os.path.exists(args.output):
        gpkg_drv.DeleteDataSource(args.output)

    out_ds = gpkg_drv.CreateDataSource(args.output)
    if out_ds is None:
        sys.exit(f"Could not create {args.output}")

    gt = src.GetGeoTransform()

    print(f"Source: {args.source}")
    print(f"Output: {args.output}")
    print(f"Size:   {src.RasterXSize} x {src.RasterYSize}")
    print()

    for class_id, layer_name in CLASS_LAYERS.items():
        mask_arr = (arr == class_id).astype(np.uint8)
        pixel_count = int(mask_arr.sum())

        print(f"{layer_name:15s} class {class_id}: {pixel_count:,} pixels")

        layer = out_ds.CreateLayer(
            layer_name,
            srs=srs,
            geom_type=ogr.wkbPolygon,
        )
        field = ogr.FieldDefn("class_id", ogr.OFTInteger)
        layer.CreateField(field)
        field_index = layer.GetLayerDefn().GetFieldIndex("class_id")

        if pixel_count == 0:
            continue

        mask_ds = mem_drv.Create(
            "",
            src.RasterXSize,
            src.RasterYSize,
            1,
            gdal.GDT_Byte,
        )
        mask_ds.SetGeoTransform(gt)
        mask_ds.SetProjection(src.GetProjection())
        mask_band = mask_ds.GetRasterBand(1)
        mask_band.WriteArray(mask_arr)
        mask_band.SetNoDataValue(0)
        mask_band.FlushCache()

        # Polygonize only pixels belonging to this semantic class.
        gdal.Polygonize(
            mask_band,
            mask_band,
            layer,
            field_index,
            options=["8CONNECTED=8"],
            callback=None,
        )

        # Polygonize writes the mask value (1); replace with semantic class ID.
        layer.ResetReading()
        for feat in layer:
            feat.SetField("class_id", class_id)
            layer.SetFeature(feat)

        print(f"  -> {layer.GetFeatureCount():,} polygons")

        mask_ds = None
        layer = None

    out_ds = None
    src = None
    print()
    print("Done.")


if __name__ == "__main__":
    main()
