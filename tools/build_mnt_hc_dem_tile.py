#!/usr/bin/env python3
"""
Build one X-Plane one-degree DEM tile from the Québec MNT-HC mosaic.

Ullaaq Air Nunavik production workflow:

    MNT-HC (CGVD28)
        -> exact one-degree source-grid extraction, no horizontal resampling
        -> CGVD28 -> NAD83(CSRS) ellipsoidal height via HT2_2010v70
        -> NAD83(CSRS) ellipsoidal height -> CGVD2013 via CGG2013n83
        -> Float32 GeoTIFF
        -> QA and optional comparison against a reference DEM

The vertical correction applied at every valid DEM pixel is therefore:

    H_CGVD2013 = H_CGVD28 + N_HT2 - N_CGG2013

implemented through PROJ vgridshift operations rather than by sampling the
grid files ourselves.

Default project locations match the current Ullaaq workstation layout, but
all important paths are overridable.

Example, production output:

    python3 tools/build_mnt_hc_dem_tile.py 58 -70

Example, validation output:

    python3 tools/build_mnt_hc_dem_tile.py 58 -70 \
        --out-dir work/+58-070/dem-validation \
        --compare "$HOME/linGames/GIS/Canada/MNT_HC/tiles/+58-070_MNT_HC_CGVD2013.tif"

Dependencies:
    numpy
    pyproj
    GDAL Python bindings (osgeo)

The script intentionally fails loudly on source-grid, CRS, coverage, nodata,
vertical-grid, or comparison-QA problems.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple


def die(message: str, code: int = 2) -> "None":
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def tile_name(lat: int, lon: int) -> str:
    return f"{lat:+03d}{lon:+04d}"


def tile_bounds(lat: int, lon: int) -> Tuple[float, float, float, float]:
    west = float(lon)
    south = float(lat)
    east = west + 1.0
    north = south + 1.0
    return west, south, east, north


def resolve_default_grid(filename: str) -> Path:
    candidates = [
        Path.home() / ".local" / "share" / "proj" / filename,
    ]

    try:
        from pyproj import datadir
        candidates.extend(
            [
                Path(datadir.get_user_data_dir()) / filename,
                Path(datadir.get_data_dir()) / filename,
            ]
        )
    except Exception:
        pass

    for path in candidates:
        if path.is_file():
            return path.resolve()

    searched = "\n    ".join(str(p) for p in candidates)
    die(
        f"Could not find PROJ vertical grid {filename!r}.\n"
        f"Searched:\n    {searched}\n"
        f"Supply it explicitly with the appropriate --ht2-grid/--cgg-grid option."
    )


def require_dependencies():
    try:
        import numpy as np
    except ImportError:
        die("numpy is required.")

    try:
        from osgeo import gdal, osr
    except ImportError:
        die(
            "GDAL Python bindings are required (import osgeo failed). "
            "On Ubuntu this is commonly provided by python3-gdal."
        )

    try:
        from pyproj import Transformer, network
    except ImportError:
        die("pyproj is required.")

    gdal.UseExceptions()
    try:
        network.set_network_enabled(False)
    except Exception:
        pass

    return np, gdal, osr, Transformer


@dataclass
class RunningStats:
    count: int = 0
    minimum: float = math.inf
    maximum: float = -math.inf
    total: float = 0.0
    total_sq: float = 0.0

    def add(self, np, values) -> None:
        if values.size == 0:
            return
        vals = values.astype("float64", copy=False)
        self.count += int(vals.size)
        vmin = float(np.min(vals))
        vmax = float(np.max(vals))
        self.minimum = min(self.minimum, vmin)
        self.maximum = max(self.maximum, vmax)
        self.total += float(np.sum(vals, dtype="float64"))
        self.total_sq += float(np.sum(vals * vals, dtype="float64"))

    @property
    def mean(self) -> float:
        return self.total / self.count if self.count else math.nan

    @property
    def rmse(self) -> float:
        return math.sqrt(self.total_sq / self.count) if self.count else math.nan


def almost_integer(value: float, tol: float = 1e-6) -> int:
    rounded = int(round(value))
    if abs(value - rounded) > tol:
        die(f"Expected source-grid alignment, got non-integral pixel coordinate {value:.12f}")
    return rounded


def source_window(gdal, src, lat: int, lon: int, args):
    gt = src.GetGeoTransform()
    if gt is None:
        die("Source raster has no geotransform.")

    if abs(gt[2]) > 1e-14 or abs(gt[4]) > 1e-14:
        die(f"Rotated/skewed source rasters are not supported. Geotransform: {gt}")

    px = float(gt[1])
    py = float(gt[5])

    if px <= 0 or py >= 0:
        die(f"Expected north-up geographic source grid; got pixel size ({px}, {py}).")

    if args.expected_pixel_size > 0:
        tol = max(1e-12, args.expected_pixel_size * 1e-8)
        if abs(px - args.expected_pixel_size) > tol or abs(abs(py) - args.expected_pixel_size) > tol:
            die(
                "Unexpected MNT-HC pixel size. "
                f"Expected ±{args.expected_pixel_size}, got ({px}, {py})."
            )

    west, south, east, north = tile_bounds(lat, lon)

    xoff = almost_integer((west - gt[0]) / px)
    yoff = almost_integer((north - gt[3]) / py)
    width = almost_integer((east - west) / px)
    height = almost_integer((south - north) / py)

    if args.expected_size > 0 and (width != args.expected_size or height != args.expected_size):
        die(
            f"Unexpected one-degree tile size {width} x {height}; "
            f"expected {args.expected_size} x {args.expected_size}."
        )

    if xoff < 0 or yoff < 0 or xoff + width > src.RasterXSize or yoff + height > src.RasterYSize:
        die(
            f"Tile {tile_name(lat, lon)} lies outside source raster coverage.\n"
            f"Requested source window: x={xoff}:{xoff+width}, y={yoff}:{yoff+height}\n"
            f"Source size: {src.RasterXSize} x {src.RasterYSize}"
        )

    return (xoff, yoff, width, height), gt


def source_epsg(osr, src) -> Optional[int]:
    wkt = src.GetProjection()
    if not wkt:
        return None

    srs = osr.SpatialReference()
    srs.ImportFromWkt(wkt)

    try:
        srs.AutoIdentifyEPSG()
    except Exception:
        pass

    if not bool(srs.IsGeographic()):
        die("MNT-HC source CRS is not geographic.")

    code = srs.GetAuthorityCode(None)
    if code is None:
        code = srs.GetAuthorityCode("GEOGCS")

    try:
        return int(code) if code is not None else None
    except (TypeError, ValueError):
        return None


def make_raw_tile(gdal, src, raw_tmp: Path, window, tile: str):
    xoff, yoff, width, height = window

    options = gdal.TranslateOptions(
        format="GTiff",
        srcWin=[xoff, yoff, width, height],
        outputType=gdal.GDT_Float32,
        creationOptions=[
            "TILED=YES",
            "COMPRESS=DEFLATE",
            "PREDICTOR=3",
            "BIGTIFF=IF_SAFER",
        ],
    )

    ds = gdal.Translate(str(raw_tmp), src, options=options)
    if ds is None:
        die("gdal.Translate failed while extracting the raw tile.")

    ds.SetMetadataItem("ULLAAQ_TILE", tile)
    ds.SetMetadataItem("ULLAAQ_VERTICAL_DATUM", "CGVD28")
    ds.FlushCache()
    ds = None


def proj_grid_path(path: Path) -> str:
    text = str(path.resolve())
    if any(ch.isspace() for ch in text):
        die(
            f"PROJ grid path contains whitespace, which this script deliberately refuses: {text}\n"
            "Move/copy the grid to a path without spaces or pass another grid path."
        )
    return text


def build_vertical_transformer(Transformer, ht2: Path, cgg: Path):
    ht2_s = proj_grid_path(ht2)
    cgg_s = proj_grid_path(cgg)

    # Input/output x,y are longitude/latitude in degrees.
    #
    # Forward HT2 vgridshift:
    #     CGVD28 gravity-related height -> NAD83(CSRS) ellipsoidal height
    #
    # Inverse CGG2013 vgridshift:
    #     NAD83(CSRS) ellipsoidal height -> CGVD2013 gravity-related height
    #
    # Thus z=0 produces exactly the local CGVD28 -> CGVD2013 correction.
    pipeline = (
        "+proj=pipeline "
        "+step +proj=unitconvert +xy_in=deg +xy_out=rad "
        f"+step +proj=vgridshift +grids={ht2_s} +multiplier=1 "
        f"+step +inv +proj=vgridshift +grids={cgg_s} +multiplier=1 "
        "+step +proj=unitconvert +xy_in=rad +xy_out=deg"
    )

    try:
        return Transformer.from_pipeline(pipeline), pipeline
    except Exception as exc:
        die(f"Could not build PROJ vertical transformation pipeline:\n{exc}")


def valid_mask(np, arr, nodata):
    mask = np.isfinite(arr)
    if nodata is not None:
        if math.isnan(float(nodata)):
            mask &= ~np.isnan(arr)
        else:
            mask &= arr != nodata
    return mask


def create_normalized_tile(np, gdal, Transformer, raw_path: Path, out_tmp: Path, ht2: Path, cgg: Path, args, tile: str):
    src = gdal.Open(str(raw_path), gdal.GA_ReadOnly)
    if src is None:
        die(f"Could not open extracted raw tile: {raw_path}")

    band = src.GetRasterBand(1)
    nodata = band.GetNoDataValue()
    gt = src.GetGeoTransform()
    projection = src.GetProjection()

    driver = gdal.GetDriverByName("GTiff")
    dst = driver.Create(
        str(out_tmp),
        src.RasterXSize,
        src.RasterYSize,
        1,
        gdal.GDT_Float32,
        options=[
            "TILED=YES",
            "COMPRESS=DEFLATE",
            "PREDICTOR=3",
            "BIGTIFF=IF_SAFER",
        ],
    )
    if dst is None:
        die(f"Could not create output GeoTIFF: {out_tmp}")

    dst.SetGeoTransform(gt)
    dst.SetProjection(projection)
    out_band = dst.GetRasterBand(1)
    if nodata is not None:
        out_band.SetNoDataValue(nodata)

    transformer, pipeline = build_vertical_transformer(Transformer, ht2, cgg)

    correction_stats = RunningStats()
    valid_pixels = 0
    total_pixels = src.RasterXSize * src.RasterYSize

    # Longitudes do not vary with row on this north-up grid.
    x = np.arange(src.RasterXSize, dtype="float64")
    lon_1d = gt[0] + (x + 0.5) * gt[1]

    for yoff in range(0, src.RasterYSize, args.chunk_rows):
        rows = min(args.chunk_rows, src.RasterYSize - yoff)

        arr = band.ReadAsArray(0, yoff, src.RasterXSize, rows)
        if arr is None:
            die(f"Could not read DEM rows {yoff}:{yoff+rows}")

        arr = arr.astype("float32", copy=False)
        mask = valid_mask(np, arr, nodata)

        y = np.arange(yoff, yoff + rows, dtype="float64")
        lat_1d = gt[3] + (y + 0.5) * gt[5]

        # Broadcast to full pixel-center coordinate arrays.
        lon = np.broadcast_to(lon_1d[None, :], (rows, src.RasterXSize))
        lat = np.broadcast_to(lat_1d[:, None], (rows, src.RasterXSize))
        zero = np.zeros((rows, src.RasterXSize), dtype="float64")

        try:
            _, _, correction = transformer.transform(lon, lat, zero, errcheck=True)
        except Exception as exc:
            die(
                f"PROJ vertical transformation failed at rows {yoff}:{yoff+rows}:\n{exc}\n"
                "Check that both Canadian vertical grids cover this tile."
            )

        correction = np.asarray(correction, dtype="float64")

        finite_corr = np.isfinite(correction)
        if not bool(np.all(finite_corr)):
            bad = int(np.size(finite_corr) - np.count_nonzero(finite_corr))
            die(f"PROJ returned {bad} non-finite vertical corrections in rows {yoff}:{yoff+rows}.")

        vals = correction[mask]
        correction_stats.add(np, vals)
        valid_pixels += int(np.count_nonzero(mask))

        if vals.size and float(np.max(np.abs(vals))) > args.max_abs_correction:
            die(
                "Vertical correction exceeded smoke-test limit. "
                f"Observed |correction| up to {float(np.max(np.abs(vals))):.6f} m; "
                f"limit is {args.max_abs_correction:.3f} m.\n"
                "This usually means the wrong vertical grid, transform direction, or CRS is in play."
            )

        out = arr.astype("float64")
        out[mask] += correction[mask]
        out = out.astype("float32")

        out_band.WriteArray(out, 0, yoff)

        done = yoff + rows
        pct = 100.0 * done / src.RasterYSize
        print(f"\rApplying vertical datum: {done:5d}/{src.RasterYSize} rows ({pct:6.2f}%)", end="", flush=True)

    print()

    valid_pct = 100.0 * valid_pixels / total_pixels
    if valid_pct + 1e-12 < args.min_valid_percent:
        die(
            f"Valid DEM coverage is only {valid_pct:.6f}%; "
            f"required minimum is {args.min_valid_percent:.6f}%."
        )

    dst.SetMetadataItem("ULLAAQ_TILE", tile)
    dst.SetMetadataItem("ULLAAQ_VERTICAL_DATUM_SOURCE", "CGVD28")
    dst.SetMetadataItem("ULLAAQ_VERTICAL_DATUM_TARGET", "CGVD2013(CGG2013)")
    dst.SetMetadataItem("ULLAAQ_HT2_GRID", ht2.name)
    dst.SetMetadataItem("ULLAAQ_CGG_GRID", cgg.name)
    dst.SetMetadataItem("ULLAAQ_VERTICAL_PIPELINE", pipeline)
    dst.SetMetadataItem("ULLAAQ_CORRECTION_MIN_M", f"{correction_stats.minimum:.9f}")
    dst.SetMetadataItem("ULLAAQ_CORRECTION_MAX_M", f"{correction_stats.maximum:.9f}")
    dst.SetMetadataItem("ULLAAQ_CORRECTION_MEAN_M", f"{correction_stats.mean:.9f}")
    dst.SetMetadataItem("ULLAAQ_VALID_PERCENT", f"{valid_pct:.9f}")

    out_band.FlushCache()
    dst.FlushCache()
    out_band = None
    dst = None
    band = None
    src = None

    return correction_stats, valid_pixels, total_pixels


def raster_signature(gdal, path: Path):
    ds = gdal.Open(str(path), gdal.GA_ReadOnly)
    if ds is None:
        die(f"Could not open raster: {path}")
    sig = {
        "width": ds.RasterXSize,
        "height": ds.RasterYSize,
        "gt": tuple(float(v) for v in ds.GetGeoTransform()),
        "projection": ds.GetProjection(),
        "nodata": ds.GetRasterBand(1).GetNoDataValue(),
    }
    ds = None
    return sig


def compare_rasters(np, gdal, candidate: Path, reference: Path, chunk_rows: int, tolerance: float):
    ca = gdal.Open(str(candidate), gdal.GA_ReadOnly)
    rb = gdal.Open(str(reference), gdal.GA_ReadOnly)

    if ca is None:
        die(f"Could not open comparison candidate: {candidate}")
    if rb is None:
        die(f"Could not open comparison reference: {reference}")

    if (ca.RasterXSize, ca.RasterYSize) != (rb.RasterXSize, rb.RasterYSize):
        die(
            "Reference comparison failed: raster dimensions differ: "
            f"{ca.RasterXSize}x{ca.RasterYSize} vs {rb.RasterXSize}x{rb.RasterYSize}."
        )

    gt_a = ca.GetGeoTransform()
    gt_b = rb.GetGeoTransform()
    if any(abs(a - b) > 1e-12 for a, b in zip(gt_a, gt_b)):
        die(f"Reference comparison failed: geotransforms differ:\n{gt_a}\n{gt_b}")

    ba = ca.GetRasterBand(1)
    bb = rb.GetRasterBand(1)
    nd_a = ba.GetNoDataValue()
    nd_b = bb.GetNoDataValue()

    diff_stats = RunningStats()
    max_abs = 0.0
    compared = 0
    mask_mismatch = 0

    for yoff in range(0, ca.RasterYSize, chunk_rows):
        rows = min(chunk_rows, ca.RasterYSize - yoff)
        a = ba.ReadAsArray(0, yoff, ca.RasterXSize, rows).astype("float64")
        b = bb.ReadAsArray(0, yoff, ca.RasterXSize, rows).astype("float64")

        ma = valid_mask(np, a, nd_a)
        mb = valid_mask(np, b, nd_b)

        mask_mismatch += int(np.count_nonzero(ma ^ mb))
        common = ma & mb
        if not bool(np.any(common)):
            continue

        diff = a[common] - b[common]
        diff_stats.add(np, diff)
        compared += int(diff.size)
        max_abs = max(max_abs, float(np.max(np.abs(diff))))

    ca = None
    rb = None

    if mask_mismatch:
        die(f"Reference comparison failed: {mask_mismatch} pixels differ in valid/nodata state.")

    passed = max_abs <= tolerance
    return {
        "compared": compared,
        "mean": diff_stats.mean,
        "rmse": diff_stats.rmse,
        "min": diff_stats.minimum,
        "max": diff_stats.maximum,
        "max_abs": max_abs,
        "tolerance": tolerance,
        "passed": passed,
    }


def atomic_replace(tmp: Path, final: Path) -> None:
    os.replace(tmp, final)


def parse_args():
    p = argparse.ArgumentParser(
        description="Build an exact one-degree Québec MNT-HC DEM tile normalized from CGVD28 to CGVD2013."
    )
    p.add_argument("lat", type=int, help="South edge latitude, e.g. 58 for +58-070")
    p.add_argument("lon", type=int, help="West edge longitude, e.g. -70 for +58-070")

    p.add_argument(
        "--source",
        type=Path,
        default=Path.home() / "linGames" / "GIS" / "Canada" / "MNT_HC" / "MNT_HC_24K.vrt",
        help="MNT-HC mosaic/VRT source.",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path.home() / "linGames" / "GIS" / "Canada" / "MNT_HC" / "tiles",
        help="Output directory.",
    )
    p.add_argument("--ht2-grid", type=Path, help="Path to ca_nrc_HT2_2010v70.tif.")
    p.add_argument("--cgg-grid", type=Path, help="Path to ca_nrc_CGG2013n83.tif.")

    p.add_argument(
        "--compare",
        type=Path,
        help="Optional known-good normalized DEM to compare numerically.",
    )
    p.add_argument(
        "--compare-tol",
        type=float,
        default=1e-4,
        help="PASS threshold for maximum absolute candidate/reference difference in metres (default: 1e-4).",
    )

    p.add_argument(
        "--chunk-rows",
        type=int,
        default=128,
        help="Rows transformed per block (default: 128). Lower this if memory is tight.",
    )
    p.add_argument(
        "--min-valid-percent",
        type=float,
        default=100.0,
        help="Required valid-pixel coverage percentage (default: 100).",
    )
    p.add_argument(
        "--max-abs-correction",
        type=float,
        default=5.0,
        help="Smoke-test limit for absolute datum correction in metres (default: 5).",
    )

    p.add_argument(
        "--expected-epsg",
        type=int,
        default=4269,
        help="Expected horizontal source EPSG code (default: 4269; set 0 to disable).",
    )
    p.add_argument(
        "--expected-pixel-size",
        type=float,
        default=0.0001,
        help="Expected source pixel size in degrees (default: 0.0001; set 0 to disable).",
    )
    p.add_argument(
        "--expected-size",
        type=int,
        default=10000,
        help="Expected one-degree output dimension (default: 10000; set 0 to disable).",
    )

    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing output files.",
    )
    return p.parse_args()


def main():
    args = parse_args()

    if args.chunk_rows <= 0:
        die("--chunk-rows must be > 0.")
    if not (0 < args.min_valid_percent <= 100):
        die("--min-valid-percent must be in (0, 100].")
    if args.max_abs_correction <= 0:
        die("--max-abs-correction must be > 0.")
    if args.compare_tol < 0:
        die("--compare-tol must be >= 0.")

    np, gdal, osr, Transformer = require_dependencies()

    source = args.source.expanduser().resolve()
    out_dir = args.out_dir.expanduser().resolve()
    compare = args.compare.expanduser().resolve() if args.compare else None

    if not source.is_file():
        die(f"MNT-HC source does not exist: {source}")
    if compare is not None and not compare.is_file():
        die(f"Comparison reference does not exist: {compare}")

    ht2 = args.ht2_grid.expanduser().resolve() if args.ht2_grid else resolve_default_grid("ca_nrc_HT2_2010v70.tif")
    cgg = args.cgg_grid.expanduser().resolve() if args.cgg_grid else resolve_default_grid("ca_nrc_CGG2013n83.tif")

    if not ht2.is_file():
        die(f"HT2 grid does not exist: {ht2}")
    if not cgg.is_file():
        die(f"CGG2013 grid does not exist: {cgg}")

    out_dir.mkdir(parents=True, exist_ok=True)

    tile = tile_name(args.lat, args.lon)
    raw = out_dir / f"{tile}_MNT_HC_raw.tif"
    normalized = out_dir / f"{tile}_MNT_HC_CGVD2013.tif"
    raw_tmp = out_dir / f".{raw.name}.tmp.tif"
    normalized_tmp = out_dir / f".{normalized.name}.tmp.tif"

    for path in (raw, normalized):
        if path.exists() and not args.force:
            die(f"Output already exists: {path}\nUse --force to replace it.")

    for tmp in (raw_tmp, normalized_tmp):
        if tmp.exists():
            tmp.unlink()

    src = gdal.Open(str(source), gdal.GA_ReadOnly)
    if src is None:
        die(f"Could not open source raster: {source}")
    if src.RasterCount < 1:
        die("Source raster has no bands.")

    epsg = source_epsg(osr, src)
    if args.expected_epsg and epsg != args.expected_epsg:
        die(f"Unexpected source CRS EPSG:{epsg}; expected EPSG:{args.expected_epsg}.")

    window, gt = source_window(gdal, src, args.lat, args.lon, args)
    xoff, yoff, width, height = window
    west, south, east, north = tile_bounds(args.lat, args.lon)

    print(f"Tile:                 {tile}")
    print(f"Bounds:               {west:g}..{east:g} / {south:g}..{north:g}")
    print(f"Source:               {source}")
    print(f"Source EPSG:          {epsg if epsg is not None else 'unknown'}")
    print(f"Source pixel:         {gt[1]:.10f}, {gt[5]:.10f}")
    print(f"Source window:        x={xoff}, y={yoff}, {width} x {height}")
    print(f"HT2 grid:             {ht2}")
    print(f"CGG2013 grid:         {cgg}")
    print(f"Raw output:           {raw}")
    print(f"Normalized output:    {normalized}")
    print()

    print("Extracting exact source-grid tile...")
    make_raw_tile(gdal, src, raw_tmp, window, tile)
    src = None
    atomic_replace(raw_tmp, raw)

    print("Applying CGVD28 -> CGVD2013 vertical normalization...")
    correction_stats, valid_pixels, total_pixels = create_normalized_tile(
        np, gdal, Transformer, raw, normalized_tmp, ht2, cgg, args, tile
    )
    atomic_replace(normalized_tmp, normalized)

    sig = raster_signature(gdal, normalized)
    valid_pct = 100.0 * valid_pixels / total_pixels

    print()
    print("DEM QA")
    print(f"  Raster size:         {sig['width']} x {sig['height']}")
    print(f"  Valid pixels:        {valid_pixels:,} / {total_pixels:,} ({valid_pct:.6f}%)")
    print("  Vertical correction:")
    print(f"    min:               {correction_stats.minimum:+.9f} m")
    print(f"    max:               {correction_stats.maximum:+.9f} m")
    print(f"    mean:              {correction_stats.mean:+.9f} m")
    print("  Source-grid extract: PASS")
    print("  Vertical normalize:  PASS")

    if compare is not None:
        print()
        print(f"Comparing against reference: {compare}")
        result = compare_rasters(
            np, gdal, normalized, compare, args.chunk_rows, args.compare_tol
        )
        print(f"  Pixels compared:     {result['compared']:,}")
        print(f"  Delta min:           {result['min']:+.9f} m")
        print(f"  Delta max:           {result['max']:+.9f} m")
        print(f"  Delta mean:          {result['mean']:+.9f} m")
        print(f"  RMSE:                {result['rmse']:.9f} m")
        print(f"  Max abs delta:       {result['max_abs']:.9f} m")
        print(f"  Tolerance:           {result['tolerance']:.9f} m")
        print(f"  Reference compare:   {'PASS' if result['passed'] else 'FAIL'}")

        if not result["passed"]:
            raise SystemExit(1)

    print()
    print("PASS")
    print(f"Production DEM: {normalized}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        raise SystemExit(130)
