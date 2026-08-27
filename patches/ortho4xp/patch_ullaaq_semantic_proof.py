#!/usr/bin/env python3
"""Patch Ortho4XP O4_DSF_Utils.py for Ullaaq Semantic Proof Build 1.

Changes only Step-3 terrestrial semantic selection:
  * prefer VEG_NORD cl_carto from ULLAAQ_VEGNORD_GPKG / ULLAAQ_LANDCOVER_GPKG;
  * rasterize the vector classes in memory for fast triangle-barycentre lookup;
  * map VEG_NORD codes to nine temporary diagnostic terrain buckets;
  * retain the old raster sampler as a fallback;
  * print both bucket and source cl_carto triangle counts.

Hydro is intentionally NOT patched here. Point ULLAAQ_NHN_WATER_GPKG back to the
known-good NHN/HNET Bank GeoPackage before rebuilding Step 1.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
import re
import shutil
import sys


NEW_ULLAAQ_BLOCK = r'''# Ullaaq experimental semantic-terrain support.
#
# Semantic Proof Build 1 prefers VEG_NORD vector attributes, using the same
# GeoPackage that supplies Step-1 terrestrial constraints.  The vector layer is
# rasterized in memory only as a fast lookup table for millions of triangle
# barycentres; the actual mesh boundaries remain the native VEG_NORD constraints
# inserted in Step 1.
#
# Override the vector source with ULLAAQ_VEGNORD_GPKG.  Otherwise
# ULLAAQ_LANDCOVER_GPKG is used.  ULLAAQ_VEGNORD_RASTER_SIZE controls lookup
# resolution (8192 by default, roughly 4-14 m/pixel across this tile).
ULLAAQ_LANDCLASS_DEFAULT = os.path.expanduser(
    "~/Ullaaq-Air-Nunavut-Scenery/source/Landcover/+58-069/+58-069_ullaaq_landclass.tif"
)

ULLAAQ_BUCKET_NAMES = {
    0: "fallback/open",
    1: "forest/taiga",
    2: "shrub",
    3: "open heath/tundra",
    4: "low tundra",
    5: "rocky tundra",
    6: "wetland",
    7: "barren/exposed",
    8: "developed",
}

# Temporary diagnostic palette.  These are deliberately provisional stock
# X-Plane terrains chosen to make VEG_NORD polygon classes visible in runtime.
ULLAAQ_TERRAIN_DEFS = {
    0: "lib/g10/terrain10/tun_sp_pol_sdry_fl.ter",      # fallback / ILE / unknown
    1: "lib/g10/terrain10/coni_vcld_sdry_fl.ter",       # R* forest / taiga
    2: "lib/g10/terrain10/tun_shrb_vcld_sdry_fl.ter",   # AB/AH/AAB/AAH shrub
    3: "lib/g10/terrain10/tun_sp_pol_sdry_fl.ter",      # LS/LSA open heath
    4: "lib/g10/terrain10/tun_grass_vcld_sdry_fl.ter",  # TD/TDA low tundra
    5: "lib/g10/terrain10/rock_pol_sdry_sflat.ter",     # rocky tundra
    6: "lib/g10/terrain10/tun_wetl_vcld_wet_lo.ter",    # wetland
    7: "lib/g10/terrain10/bare_scree_pol_sdry.ter",     # barren / exposed
    8: "lib/g10/terrain10/north_crptwn_irr.ter",        # IH developed, diagnostic
}


def _vegnord_bucket_for_code(code):
    """Map VEG_NORD cl_carto to a coarse diagnostic terrain bucket."""
    code = (code or "").strip().upper()

    # Water remains authoritative through Ortho4XP/NHN tri_type, not through
    # terrestrial semantic assignment.  If an ordinary-land triangle samples
    # EAU, leave it visibly as fallback and report the EAU count downstream.
    if not code or code in {"EAU", "ILE"}:
        return 0

    # Rocky variants must be tested before the generic R* forest rule.
    if code in {"LSR", "RLS", "TDR", "RTD"}:
        return 5
    if code.startswith("R"):
        return 1
    if code in {"AB", "AH", "AAB", "AAH"}:
        return 2
    if code in {"LS", "LSA"}:
        return 3
    if code in {"TD", "TDA"}:
        return 4
    if code in {"TAR", "TAA", "TMS", "TMU", "TOP", "MS"}:
        return 6
    if code in {"AR", "SD"}:
        return 7
    if code == "IH":
        return 8

    return 0


class UllaaqVegNordSampler:
    """Fast VEG_NORD cl_carto lookup for Step-3 triangle barycentres.

    Step 1 already cuts the mesh on the authoritative polygon boundaries.  For
    Step 3 we only need to identify which polygon contains a triangle barycentre.
    Doing millions of point-in-polygon tests would be needlessly expensive, so
    the cl_carto codes are burned once into an in-memory byte raster covering
    exactly the current 1x1-degree DSF tile.
    """

    def __init__(self, filename, tile_lon, tile_lat, layer_name="veg_nord"):
        if not HAS_GDAL:
            raise RuntimeError("Ullaaq VEG_NORD semantics require Python GDAL/osgeo.")

        self.filename = filename
        self.tile_lon = float(tile_lon)
        self.tile_lat = float(tile_lat)
        self.size = int(os.environ.get("ULLAAQ_VEGNORD_RASTER_SIZE", "8192"))
        if self.size < 1024 or self.size > 32768:
            raise RuntimeError(
                "ULLAAQ_VEGNORD_RASTER_SIZE must be between 1024 and 32768"
            )

        self.ds = gdal.OpenEx(filename, gdal.OF_VECTOR | gdal.OF_READONLY)
        if self.ds is None:
            raise RuntimeError(f"Cannot open VEG_NORD GeoPackage: {filename}")

        layer = self.ds.GetLayerByName(layer_name)
        if layer is None:
            raise RuntimeError(
                f"VEG_NORD layer {layer_name!r} not found in {filename}"
            )
        layer_defn = layer.GetLayerDefn()
        if layer_defn.GetFieldIndex("cl_carto") < 0:
            raise RuntimeError("VEG_NORD layer is missing required field cl_carto")

        codes = set()
        layer.ResetReading()
        for feat in layer:
            code = (feat.GetField("cl_carto") or "").strip()
            if code:
                codes.add(code)
        layer.ResetReading()

        if len(codes) > 254:
            raise RuntimeError(
                f"Too many VEG_NORD cl_carto values for byte lookup raster: {len(codes)}"
            )

        self.codes = sorted(codes)
        self.code_to_value = {code: i + 1 for i, code in enumerate(self.codes)}
        self.value_to_code = {value: code for code, value in self.code_to_value.items()}

        mem_driver = gdal.GetDriverByName("MEM")
        mem = mem_driver.Create("", self.size, self.size, 1, gdal.GDT_Byte)
        if mem is None:
            raise RuntimeError("Could not create VEG_NORD in-memory lookup raster")

        pixel = 1.0 / self.size
        mem.SetGeoTransform(
            (self.tile_lon, pixel, 0.0, self.tile_lat + 1.0, 0.0, -pixel)
        )
        wgs84 = osr.SpatialReference()
        wgs84.ImportFromEPSG(4326)
        wgs84.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        mem.SetProjection(wgs84.ExportToWkt())
        band = mem.GetRasterBand(1)
        band.Fill(0)

        for code in self.codes:
            escaped = code.replace("'", "''")
            layer.SetAttributeFilter("cl_carto = '{}'".format(escaped))
            err = gdal.RasterizeLayer(
                mem,
                [1],
                layer,
                burn_values=[self.code_to_value[code]],
            )
            if err != 0:
                layer.SetAttributeFilter(None)
                raise RuntimeError(f"Rasterizing VEG_NORD cl_carto={code!r} failed")

        layer.SetAttributeFilter(None)
        layer.ResetReading()

        self.array = band.ReadAsArray()
        if self.array is None:
            raise RuntimeError("Could not read VEG_NORD lookup raster")
        self.mem = mem

    def sample_with_code(self, lon, lat):
        col = int((float(lon) - self.tile_lon) * self.size)
        row = int((self.tile_lat + 1.0 - float(lat)) * self.size)

        if col < 0 or row < 0 or col >= self.size or row >= self.size:
            return 0, "OUTSIDE"

        value = int(self.array[row, col])
        code = self.value_to_code.get(value, "UNCLASSIFIED")
        return _vegnord_bucket_for_code(code), code

    def sample(self, lon, lat):
        return self.sample_with_code(lon, lat)[0]


class UllaaqLandclassSampler:
    """Legacy raster sampler retained as a fallback."""

    def __init__(self, filename):
        if not HAS_GDAL:
            raise RuntimeError("Ullaaq landclass requires Python GDAL/osgeo.")
        self.filename = filename
        self.ds = gdal.Open(filename, gdal.GA_ReadOnly)
        if self.ds is None:
            raise RuntimeError(f"Cannot open Ullaaq landclass raster: {filename}")

        self.band = self.ds.GetRasterBand(1)
        self.array = self.band.ReadAsArray()
        if self.array is None:
            raise RuntimeError(f"Cannot read Ullaaq landclass raster: {filename}")

        self.gt = self.ds.GetGeoTransform()
        self.inv_gt = gdal.InvGeoTransform(self.gt)
        if self.inv_gt is None:
            raise RuntimeError("Could not invert Ullaaq landclass geotransform.")

        src_srs = osr.SpatialReference()
        src_srs.ImportFromWkt(self.ds.GetProjection())
        src_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        wgs84 = osr.SpatialReference()
        wgs84.ImportFromEPSG(4326)
        wgs84.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        self.to_raster = osr.CoordinateTransformation(wgs84, src_srs)
        self.width = self.ds.RasterXSize
        self.height = self.ds.RasterYSize

    def sample(self, lon, lat):
        x, y, _ = self.to_raster.TransformPoint(lon, lat)
        px, py = gdal.ApplyGeoTransform(self.inv_gt, x, y)
        col = int(px)
        row = int(py)

        if col < 0 or row < 0 or col >= self.width or row >= self.height:
            return 0

        return int(self.array[row, col])
'''


OLD_BUILD_INIT = '''def build_dsf(tile, download_queue):

    landclass_file = os.environ.get(
        "ULLAAQ_LANDCLASS_TIF",
        ULLAAQ_LANDCLASS_DEFAULT,
    )
    landclass_sampler = None
    if os.path.isfile(landclass_file):
        try:
            landclass_sampler = UllaaqLandclassSampler(landclass_file)
            UI.vprint(1, "-> Ullaaq landclass raster:", landclass_file)
        except Exception as e:
            UI.vprint(1, "   WARNING: Ullaaq landclass disabled:", repr(e))
    else:
        UI.vprint(
            1,
            "   WARNING: Ullaaq landclass raster not found:",
            landclass_file,
            "Using fallback tundra.",
        )

    dico_customzl = zone_list_to_ortho_dico(tile)
'''

NEW_BUILD_INIT = '''def build_dsf(tile, download_queue):

    landclass_sampler = None

    # Semantic Proof Build 1: prefer the exact VEG_NORD vector source used by
    # Step 1.  The legacy raster remains available as a fallback so this patch
    # does not break older tiles/workflows.
    vegnord_file = os.environ.get(
        "ULLAAQ_VEGNORD_GPKG",
        os.environ.get("ULLAAQ_LANDCOVER_GPKG", ""),
    ).strip()
    if vegnord_file:
        vegnord_file = os.path.expanduser(vegnord_file)

    if vegnord_file and os.path.isfile(vegnord_file):
        try:
            landclass_sampler = UllaaqVegNordSampler(
                vegnord_file,
                tile.lon,
                tile.lat,
            )
            UI.vprint(1, "-> Ullaaq VEG_NORD semantic source:", vegnord_file)
            UI.vprint(
                1,
                "   VEG_NORD lookup raster:",
                landclass_sampler.size,
                "x",
                landclass_sampler.size,
            )
            UI.vprint(
                1,
                "   VEG_NORD cl_carto values:",
                " ".join(landclass_sampler.codes),
            )
        except Exception as e:
            UI.vprint(1, "   WARNING: VEG_NORD semantic lookup disabled:", repr(e))
            landclass_sampler = None

    if landclass_sampler is None:
        landclass_file = os.environ.get(
            "ULLAAQ_LANDCLASS_TIF",
            ULLAAQ_LANDCLASS_DEFAULT,
        )
        if os.path.isfile(landclass_file):
            try:
                landclass_sampler = UllaaqLandclassSampler(landclass_file)
                UI.vprint(1, "-> Ullaaq legacy landclass raster:", landclass_file)
            except Exception as e:
                UI.vprint(1, "   WARNING: Ullaaq landclass disabled:", repr(e))
        else:
            UI.vprint(
                1,
                "   WARNING: no VEG_NORD semantic source or legacy landclass raster;",
                "using fallback open tundra.",
            )

    dico_customzl = zone_list_to_ortho_dico(tile)
'''

OLD_SAMPLE = '''            class_id = (
                landclass_sampler.sample(bary_lon, bary_lat)
                if landclass_sampler is not None
                else 0
            )
            if class_id not in ullaaq_class_to_terrain_idx:
                class_id = 0
'''

NEW_SAMPLE = '''            if landclass_sampler is None:
                class_id = 0
                source_code = "NO_SAMPLER"
            elif hasattr(landclass_sampler, "sample_with_code"):
                class_id, source_code = landclass_sampler.sample_with_code(
                    bary_lon, bary_lat
                )
            else:
                class_id = landclass_sampler.sample(bary_lon, bary_lat)
                source_code = None

            if class_id not in ullaaq_class_to_terrain_idx:
                class_id = 0
            if source_code is not None:
                ullaaq_source_code_counts[source_code] += 1
'''

OLD_COUNTS = '''    ullaaq_class_counts = defaultdict(int)
'''

NEW_COUNTS = '''    ullaaq_class_counts = defaultdict(int)
    ullaaq_source_code_counts = defaultdict(int)
'''

OLD_STATS = '''    if ullaaq_class_counts:
        UI.vprint(1, "-> Ullaaq landclass triangle counts")
        for class_id in sorted(ULLAAQ_TERRAIN_DEFS):
            UI.vprint(
                1,
                "   class",
                class_id,
                ":",
                ullaaq_class_counts.get(class_id, 0),
                "tris ->",
                ULLAAQ_TERRAIN_DEFS[class_id],
            )
'''

NEW_STATS = '''    if ullaaq_class_counts:
        UI.vprint(1, "-> Ullaaq semantic terrain triangle counts")
        for class_id in sorted(ULLAAQ_TERRAIN_DEFS):
            UI.vprint(
                1,
                "   class",
                class_id,
                "(" + ULLAAQ_BUCKET_NAMES.get(class_id, "?") + ")",
                ":",
                ullaaq_class_counts.get(class_id, 0),
                "tris ->",
                ULLAAQ_TERRAIN_DEFS[class_id],
            )

    if ullaaq_source_code_counts:
        UI.vprint(1, "-> Ullaaq VEG_NORD cl_carto triangle counts")
        for code in sorted(ullaaq_source_code_counts):
            UI.vprint(
                1,
                "  ",
                code,
                ":",
                ullaaq_source_code_counts[code],
                "tris -> class",
                _vegnord_bucket_for_code(code),
                "(" + ULLAAQ_BUCKET_NAMES.get(_vegnord_bucket_for_code(code), "?") + ")",
            )
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly 1 anchor, found {count}")
    return text.replace(old, new, 1)


def patch_text(text: str) -> str:
    # Replace the complete old Ullaaq constants + raster sampler while leaving
    # the following quad-tree code untouched.
    pattern = re.compile(
        r"# Ullaaq experimental landclass support\..*?\n\nquad_init_level = 3",
        re.DOTALL,
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(
            "Ullaaq support block: expected exactly 1 block before quad_init_level, "
            f"found {len(matches)}"
        )
    text = pattern.sub(NEW_ULLAAQ_BLOCK + "\n\nquad_init_level = 3", text, count=1)

    text = replace_once(text, OLD_BUILD_INIT, NEW_BUILD_INIT, "build_dsf sampler init")
    text = replace_once(text, OLD_COUNTS, NEW_COUNTS, "triangle counters")
    text = replace_once(text, OLD_SAMPLE, NEW_SAMPLE, "land triangle semantic sample")
    text = replace_once(text, OLD_STATS, NEW_STATS, "semantic count diagnostics")
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "target",
        nargs="?",
        default="src/O4_DSF_Utils.py",
        help="Path to canonical O4_DSF_Utils.py (default: src/O4_DSF_Utils.py)",
    )
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target.is_file():
        print(f"ERROR: target not found: {target}", file=sys.stderr)
        return 2

    original = target.read_text(encoding="utf-8")
    if "class UllaaqVegNordSampler" in original:
        print("Already patched: UllaaqVegNordSampler is present.")
        return 0

    try:
        patched = patch_text(original)
        ast.parse(patched, filename=str(target))
    except Exception as exc:
        print(f"ERROR: patch aborted without modifying target: {exc}", file=sys.stderr)
        return 3

    backup = target.with_name(target.name + ".pre-vegnord-semantic")
    if not backup.exists():
        shutil.copy2(target, backup)
    else:
        print(f"Backup already exists, leaving it untouched: {backup}")

    target.write_text(patched, encoding="utf-8")

    print(f"Patched: {target}")
    print(f"Backup:  {backup}")
    print("AST check: PASS")
    print()
    print("Expected new diagnostics:")
    print("  -> Ullaaq VEG_NORD semantic source:")
    print("  -> Ullaaq semantic terrain triangle counts")
    print("  -> Ullaaq VEG_NORD cl_carto triangle counts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
