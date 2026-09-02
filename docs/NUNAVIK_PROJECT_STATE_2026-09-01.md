# NUNAVIK_PROJECT_STATE_2026-09-01

## Project

**Ullaaq Air Nunavik scenery pipeline for X-Plane 12**

Repository:

```text
~/linGames/Ullaaq-Air-Nunavik
```

Ortho4XP working tree:

```text
~/linGames/Ortho4XP
```

Reference tile:

```text
+58-069
```

Current development tile directory:

```text
~/linGames/X-Plane 12/Development/Replacement Mesh/Orth4XP_Tiles/zOrtho4XP_+58-069
```

The reference tile has now validated the core replacement-mesh stack:

- authoritative NHN hydro
- authoritative VEG_NORD landcover boundaries
- explicit VEG_NORD semantic classification
- native X-Plane 12 water
- custom terrain materials
- Québec MNT-HC 10 m DEM normalized to CGVD2013

The build is visually successful. Remaining water-margin elevation artifacts are presently classified as **polish**, not a pipeline blocker.

---

## 1. Hydro: validated production method

The authoritative hydro source is no longer ordinary OSM water.

The working method is:

1. HNET Bank supplies bank geometry.
2. HNET Delimiter completes the hydro face topology.
3. HHYD Waterbody classifies polygonized faces as wet/dry.
4. Wet faces are retained individually and clipped to the one-degree tile.
5. These polygons are injected into Ortho4XP as native `WATER`.

Important: **do not dissolve the wet faces**. The validated topology intentionally preserves the Bank + Delimiter face structure.

Validated source for `+58-069`:

```text
~/linGames/GIS/Canada/NHN/rebuild/+58-069_2026-09-01/+58-069_NHN_water_candidate.gpkg
```

Layer:

```text
water
```

Validated hydro statistics:

```text
Bank raw features:                  88,334
Bank normalized output:             88,334
Bank line parts:                    88,392
Point components dropped:                4

Waterbody raw:                      42,576
Waterbody normalized features:      42,568
Waterbody polygon parts:            42,578
Waterbody lines dropped:                22
Waterbody no-area features:              8

Delimiter features:                  1,111
Delimiter line parts:                1,112

Polygonized faces:                  43,911
Wet faces:                          42,578
Dry faces:                           1,333
Invalid faces:                           0
Positive-area overlap pairs:             0
```

Final candidate:

```text
42,578 multipolygons
```

The Step 1 water-seed invariant is now a hard QA gate:

```text
NHN water features: 42578
.poly WATER seeds:  42578
PASS
```

Reference checker:

```bash
python3 tools/check_ortho4xp_water_seeds.py \
  --gpkg "$ULLAAQ_NHN_WATER_GPKG" \
  --poly "$TILE/Data+58-069.poly"
```

The final `.poly` from the successful 2026-09-01 build contained:

```text
Total regions: 42593
attr 1  WATER:       42578
attr 2:                  2
attr 8:                  8
attr 16:                 3
attr 32:                 2
```

### NHN Ortho4XP hook hardening

`src/O4_Vector_Map.py` was changed so that Ullaaq hydro is no longer allowed to use a hard-coded `+58-069` fallback file.

Production behavior should now be:

```text
ordinary Ortho4XP build with no Ullaaq environment
    -> ordinary OSM water path

Ullaaq build with ULLAAQ_NHN_WATER_GPKG set
    -> authoritative NHN path

Ullaaq build with VEG_NORD enabled but NHN missing/unset
    -> fail loudly rather than silently falling back to OSM
```

This fixed a real failure encountered today: a Step 1 build silently used ordinary/custom OSM water because the running Ortho4XP process had not inherited the NHN environment variable.

Successful NHN injection now announces:

```text
-> Dealing with inland water (Ullaaq NHN authority)
    * NHN source features: 42578
    * Polygon parts retained: 42578
    * Number of indexed NHN water polygons: 42578
    * Encoding NHN water with no additional simplification.
    * Ullaaq NHN water encoding complete.
```

---

## 2. VEG_NORD landcover geometry

Canonical reference source:

```text
~/linGames/Ullaaq-Air-Nunavik/work/+58-069/landcover/+58-069_VEG_NORD_tile.gpkg
```

Layer:

```text
veg_nord
```

Reference tile source feature count:

```text
16,227
```

Water features skipped:

```text
2,071
```

Geometry policy remains:

```text
preserve source coordinates
no class dissolve
no simplification
no smoothing
```

Successful Step 1 geometry statistics:

```text
VEG_NORD noded boundary fragments:    1,577,758
VEG_NORD noded boundary vertices:     3,335,358

Merged source chains:                    43,923
Merged source vertices:               1,801,523

Hydro constraint lines:                 637,994
VEG_NORD line parts after hydro trim:   136,881
Chains after trim/merge:                136,635
Vertices after trim/merge:            1,818,440

Boundary lines encoded:                 136,635
Constrained edges added:              1,683,057

Final constrained edges:              2,508,291
```

The hydro-protection count of approximately `637,994` is a useful signature of the correct NHN + VEG_NORD Step 1. A failed build using the wrong water source produced only about `416,817` hydro constraint lines.

---

## 3. VEG_NORD semantic classification

The old coarse prefix classifier has been replaced by an explicit semantic table covering all 31 observed `cl_carto` values.

Observed source codes:

```text
AAB AAH AB AH AR EAU IH ILE LS LSA LSR MS RLS RTD
RaL RcD RcL RcmD RcmL RmC RmD RmL SD TAA TAR TD
TDA TDR TMS TMU TOP
```

`UNCLASSIFIED` is not a source class. It is the sampling sentinel.

The current implementation retains both:

- explicit source-code semantics
- coarse material buckets for current terrain dispatch / diagnostics

Current broad material buckets:

```text
0 fallback/open
1 forest/taiga
2 shrub
3 open heath/tundra
4 low tundra
5 rocky tundra
6 wetland
7 barren/exposed
8 developed
```

Special custom terrain tests remain in place for:

```text
rocky tundra -> lib/ullaaq/terrain/rock_test.ter
IH           -> lib/ullaaq/terrain/ih_test.ter
RcmL         -> lib/ullaaq/terrain/rcml_test.ter
RmC          -> lib/ullaaq/terrain/rmc_test.ter
```

### Exact-vector fallback

The semantic sampler still uses an `8192 x 8192` lookup raster for speed.

If a triangle barycentre lands on raster value zero, the sampler now performs an exact OGR polygon lookup.

Successful Step 3 QA:

```text
EAU reaching semantic terrain dispatcher: 131358
UNCLASSIFIED triangles:                   4470
OUTSIDE triangles:                           0
unknown cl_carto triangles:                  0

exact vector fallback:
    queries: 7888
    hits:    3418
    misses:  4470
```

This is a clear improvement over the previous roughly 7,776 `UNCLASSIFIED` triangles.

The explicit 31-code table is therefore validated:

```text
unknown cl_carto triangles: 0
```

### Current EAU policy

`EAU` is deliberately **not** allowed to override NHN hydro.

Where VEG_NORD says `EAU` but the authoritative NHN-derived mesh says land, the semantic dispatcher reports the disagreement and uses terrestrial fallback/open material.

Current count:

```text
EAU -> 131,358 triangles
```

This is a QA/disagreement layer, not a classifier failure.

The fallback/open total is internally accounted for:

```text
EAU           131358
ILE             6416
UNCLASSIFIED     4470
              ------
class 0        142244
```

Future work should map the spatial distribution of EAU/NHN disagreement, but it is not presently a blocker.

---

## 4. DEM: Québec MNT-HC

HRDEM was investigated first but is not a continuous solution in southern Nunavik.

Coverage tests:

```text
HRDEM 1 m DSM/DTM:
    +58-069 ~3.9167%
    +58-070 0%

HRDEM 2 m:
    +58-069 ~3.9199%
    +58-070 0%
```

The useful continuous baseline is Québec **MNT-HC**, approximately 10 m hydro-coherent DEM coverage from roughly 50N to 63N.

Workspace:

```text
~/linGames/GIS/Canada/MNT_HC
```

Sixteen 1:50,000 sheets covering `+58-069` and `+58-070` were downloaded:

```text
024K01 through 024K16
```

Notable sheets:

```text
024K01 KUUJJUAQ
024K12 TASIUJAQ
```

Combined VRT:

```text
~/linGames/GIS/Canada/MNT_HC/MNT_HC_24K.vrt
```

VRT characteristics:

```text
size:       20000 x 10000
CRS:        NAD83 EPSG:4269
origin:     -70, 59
pixel:      0.0001, -0.0001
extent:     -70..-68, 58..59
Float32
valid:      100%
```

Raw tile cuts:

```text
~/linGames/GIS/Canada/MNT_HC/tiles/+58-069_MNT_HC_raw.tif
~/linGames/GIS/Canada/MNT_HC/tiles/+58-070_MNT_HC_raw.tif
```

Each is:

```text
10000 x 10000
exact one-degree extent
same source grid
```

---

## 5. Vertical datum normalization

MNT-HC uses **CGVD28**.

Project target is **CGVD2013 / CGG2013**.

PROJ grids installed locally:

```text
~/.local/share/proj/ca_nrc_HT2_2010v70.tif
~/.local/share/proj/ca_nrc_CGG2013n83.tif
```

Chosen transform:

```text
CGVD28
 -> HT2_2010v70
 -> CGG2013n83
 -> CGVD2013
```

Horizontal coordinates are unchanged.

Representative vertical corrections:

```text
SW  (-70,58):       -0.3637 m
NW  (-70,59):       -0.2455 m
SE  (-68,58):       -0.2653 m
NE  (-68,59):       -0.1930 m
center (-69,58.5):  -0.2417 m
Tasiujaq:           -0.2992 m
```

Normalization script:

```text
~/linGames/GIS/Canada/MNT_HC/apply_vertical_datum.py
```

Production normalized outputs:

```text
~/linGames/GIS/Canada/MNT_HC/tiles/+58-069_MNT_HC_CGVD2013.tif
~/linGames/GIS/Canada/MNT_HC/tiles/+58-070_MNT_HC_CGVD2013.tif
```

Correction ranges:

```text
+58-069:
    min  -0.311996 m
    max  -0.125521 m
    mean -0.229213 m

+58-070:
    min  -0.364999 m
    max  -0.103009 m
    mean -0.281017 m
```

Tile seam correction continuity at longitude -69:

```text
min delta:      -0.000056997 m
max delta:      +0.000030518 m
mean delta:     +0.000000720 m
max absolute:    0.000056997 m
```

Essentially perfect.

Do not modify the normalized production TIFFs further.

---

## 6. MNT-HC Ortho4XP validation

The successful reference build used:

```text
custom_dem=/home/mike/linGames/GIS/Canada/MNT_HC/tiles/+58-069_MNT_HC_CGVD2013.tif
```

Ortho4XP requires Step 1 and Step 2 to use the same elevation base. Changing `custom_dem` after Step 1 triggered:

```text
ERROR: Cached raster elevation does not match the current custom DEM specs.
       You must run Step 1 and Step 2 with the same elevation base.
```

Therefore the correct rule is:

```text
new DEM -> Step 1 -> Step 2 -> Step 3
```

The GUI did not reliably persist the `custom_dem` path to the tile cfg during initial testing. The setting must be explicitly verified before building.

A decisive confirmation that the 10 m DEM was actually consumed came from the Step 2 Triangle command:

```text
10000 10000
```

The old elevation base had appeared as:

```text
3673 3673
```

Successful MNT-HC Step 2:

```text
Input vertices:                  2,509,057
Input segments:                  2,508,291

Mesh vertices:                   3,003,453
Mesh triangles:                  5,997,109
Mesh edges:                      9,000,561
Interior boundary edges:         2,966,143
Constrained subsegments:         2,975,938

Approximate heap memory:         885 MB
Step 2 time:                     1m1s
```

The mesh topology remains essentially the same size as the previous 30 m build. The benefit of the new DEM is therefore improved elevation detail rather than simply brute-force triangle proliferation.

---

## 7. Step 3 / DSF result

Successful semantic Step 3:

```text
VEG_NORD lookup raster: 8192 x 8192
Number of buckets:      900

Final DSF nodes:         7,123,939
Cross-pool triangles:      321,471
Encoded DSF size:          144.6 MB

Completed in:             2m16s
```

The first Step 3 attempt was manually interrupted. The second completed successfully.

---

## 8. Visual validation in X-Plane 12

The completed reference build was loaded in X-Plane and inspected around Kuujjuaq / the Koksoak and nearby rocky terrain.

### PASS: hydro geometry

Water bodies and river geometry look good.

NHN boundaries are crisp and convincing.

No evidence that VEG_NORD is corrupting authoritative hydro.

### PASS: landcover

The landclass mosaic reads naturally at flight scale.

The class boundaries no longer exhibit the earlier pathological vector-generalization behavior.

Current custom rocky/forest/developed material experiments remain visible and usable for continued material design.

### PASS: 10 m DEM

The MNT-HC DEM produces a clear visual improvement over the previous elevation source.

Most noticeable improvements:

- riverbanks
- small drainage cuts
- benches
- rocky highland relief
- smaller-scale topographic structure
- general terrain “read” at low altitude

This improvement is significant enough that MNT-HC should become the baseline DEM source for the covered part of Nunavik.

---

## 9. Known issue: water-margin Z artifact

A visible artifact remains along some water margins.

Symptoms:

- water surface is visibly lower than adjacent land
- shoreline geometry itself is accurate
- steep connecting faces appear between land and water
- XP12 textures these faces as bright water/cliff-like curtains

The clearest screenshots show islands and shorelines with near-vertical blue/white faces descending from the terrestrial edge to the water surface.

This is currently assessed as a **polish issue**, not a reason to reject the new DEM/hydro/landcover pipeline.

Current working hypothesis:

```text
land shoreline vertices
    retain local MNT-HC terrain elevation

        large local delta-Z

water-side vertices
    are flattened/smoothed to a lower water elevation
```

The artifact follows the hydro boundary closely, which strongly suggests a Step 2 water-elevation/post-processing issue rather than bad XY hydro geometry, landcover geometry, or DEM seams.

Relevant Step 2 stages:

```text
Post processing of altitudes according to vector data
    Smoothing inland water.
    Smoothing of sea water.
    Treatment of airports, roads and patches.
```

### Next diagnostic

Trace the code responsible for:

```text
Smoothing inland water.
Smoothing of sea water.
```

Starting point:

```bash
cd "$HOME/linGames/Ortho4XP"

grep -Rni -C 8 \
  'Smoothing inland water\|smooth.*water\|water.*smooth' \
  src/
```

Questions to answer:

1. How is water elevation selected?
2. Is it one elevation per polygon or connected component?
3. Is mean/minimum/another statistic used?
4. Are shoreline vertices shared with land or duplicated?
5. Which vertices are modified during water smoothing?
6. Does the algorithm make assumptions that differ from our dense NHN face topology?
7. Is the discontinuity already present in `Data+58-069.mesh`, or introduced later by XP12 water/bathymetry handling?

Do not change NHN geometry, VEG_NORD geometry, or the production MNT-HC DEM until this has been isolated.

---

## 10. Ortho4XP environment for Ullaaq builds

Launch Ortho4XP from the shell in which the Ullaaq variables are exported.

Reference tile:

```bash
cd "$HOME/linGames/Ortho4XP"

export ULLAAQ_NHN_WATER_GPKG="$HOME/linGames/GIS/Canada/NHN/rebuild/+58-069_2026-09-01/+58-069_NHN_water_candidate.gpkg"

export ULLAAQ_VEGNORD_GPKG="$HOME/linGames/Ullaaq-Air-Nunavik/work/+58-069/landcover/+58-069_VEG_NORD_tile.gpkg"

export ULLAAQ_LANDCOVER_GPKG="$ULLAAQ_VEGNORD_GPKG"
```

The GUI process inherits environment variables only when launched from that shell. Exporting variables in another terminal after Ortho4XP is already running does not affect the existing process.

---

## 11. Water rendering policy

Current XP12 water settings:

```text
water_tech=XP12
ratio_water=1.0
use_masks_for_inland=False
```

Policy:

- authoritative hydro geometry comes from NHN
- water renders as native XP12 water
- do not accidentally drape ordinary orthophoto imagery over inland water
- imagery remains available for future deliberate hybrid terrain work

---

## 12. Current terrain-material state

The material pipeline itself is proven.

Existing experiments include:

```text
rock_test.ter
ih_test.ter
rcml_test.ter
rmc_test.ter
```

Recent rock-material work showed:

- native/raw textures are preferable to heavy source processing
- high-opacity decal brushes can reveal geometric repetition
- reduced opacity hides repetition but washes out detail
- next texture iteration should use larger source brushes, larger brush construction, more feathering, and then downsample

The current goal is still to validate the complete terrain stack before investing heavily in final art direction.

---

## 13. Next tile: +58-070

`+58-070` is the intended generalization tile.

It contains Tasiujaq / CYTQ near the western side of the tile.

The normalized MNT-HC DEM already exists:

```text
~/linGames/GIS/Canada/MNT_HC/tiles/+58-070_MNT_HC_CGVD2013.tif
```

The generic hydro builder is intended to support it:

```bash
cd ~/linGames/Ullaaq-Air-Nunavik

python3 tools/build_nhn_hydro_tile.py 58 -70 \
  --nhn-root "$HOME/linGames/GIS/Canada/NHN" \
  --out-dir "$HOME/linGames/GIS/Canada/NHN/tiles/+58-070"
```

Before beginning the full `+58-070` build, we still need a generic VEG_NORD tile extractor. The current reference VEG_NORD GPKG is tile-specific.

`+58-071` will later be useful as a seam test because Tasiujaq lies close to the western edge of `+58-070`.

---

## 14. DEM source hierarchy going forward

Working regional strategy:

```text
MNT-HC 10 m
    -> continuous production baseline roughly 50N-63N

HRDEM / ArcticDEM 1-2 m
    -> higher-resolution replacement where coverage exists

All elevation sources
    -> normalize to CGVD2013 before mosaicking/use
```

Northern Nunavik above the MNT-HC footprint still needs final coverage planning, but ArcticDEM/HRDEM coverage exists farther north and is the likely complement.

Source blending and seam treatment between DEM families remain future work.

---

## 15. Pipeline status at end of 2026-09-01

### Validated

```text
NHN Bank + Delimiter hydro reconstruction              PASS
HHYD wet/dry classification                            PASS
42,578-water-region invariant                          PASS
NHN native XP12 water rendering                        PASS
VEG_NORD geometry insertion                            PASS
VEG_NORD hydro protection                              PASS
Explicit 31-code semantic taxonomy                     PASS
Exact-vector semantic fallback                         PASS
Unknown source codes = 0                               PASS
OUTSIDE triangles = 0                                  PASS
MNT-HC 10 m DEM ingestion                              PASS
CGVD28 -> CGVD2013 normalization                       PASS
Step 1 / Step 2 DEM consistency                        PASS
Step 2 mesh build                                      PASS
Step 3 DSF build                                       PASS
Visual hydro check                                     PASS
Visual landcover check                                 PASS
Visual MNT-HC terrain-detail improvement               PASS
```

### Known non-blocking issues

```text
Water-margin land/water elevation discontinuity        POLISH / INVESTIGATE
EAU vs NHN disagreement                                QA / MAP LATER
4,470 remaining UNCLASSIFIED triangles                 MINOR QA
Terrain materials                                      DESIGN ITERATION
```

---

## 16. Immediate next steps

1. Preserve/commit the successful `+58-069` pipeline state.
2. Quickly investigate the water-margin Z discontinuity in Ortho4XP Step 2.
3. Avoid altering the validated NHN, VEG_NORD, or MNT-HC source products while diagnosing it.
4. Once the shoreline issue is understood or accepted as polish, generalize the pipeline to `+58-070`.
5. Build a generic VEG_NORD tile-extraction tool.
6. Run the same hard QA invariants on `+58-070`.
7. Use Tasiujaq and eventually the `+58-070 / +58-071` seam to test cross-tile reproducibility.
8. Only after the stack is robust across multiple tiles should substantial effort shift back to final material design and autogen.

---

## 17. Key conclusion

The `+58-069` reference tile has done its job.

The project now has a coherent, high-fidelity replacement-mesh pipeline in which:

```text
MNT-HC defines elevation
NHN defines hydro
VEG_NORD defines terrestrial ecology
X-Plane 12 renders native water
custom terrain definitions provide the visual material layer
```

The remaining shoreline Z artifact is narrow enough to investigate independently.

The next engineering milestone is no longer “can this work?”

It is:

**Can the validated pipeline be made generic, repeatable, and boring across Nunavik?**
