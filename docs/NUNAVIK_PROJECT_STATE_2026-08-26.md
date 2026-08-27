# Nunavik / Ullaaq Scenery Project State

**Checkpoint date:** 2026-08-26  
**Current tile:** `+58-069` (Kuujjuaq)  
**Session result:** No code changes; no Git commit. Major change of direction on landcover sourcing.

## Current objective

Produce a believable and computationally tractable `+58-069` replacement mesh using mature vector landcover geometry wherever possible.

The immediate next target is no longer further repair of the custom NALCMS raster-to-vector generalizer. The new primary experiment is to ingest Québec's **Végétation du Nord québécois (`VEG_NORD`)** vector data essentially as supplied, in the same spirit as the successful NHN hydro workflow.

The first two mesh comparisons should be:

1. `VEG_NORD` landcover **including its native hydro**.
2. `VEG_NORD` terrestrial landcover with **NHN/HNET Bank hydro** substituted.

Roads, settlement-specific urban treatment, VFR detail, photogrammetry, sea ice, and large-scale batching remain deferred.

---

## Working philosophy after 2026-08-26

The project has effectively joined the **vector-first** camp.

The last two sessions showed that raster landcover can be converted into attractive vector geometry, but preserving a clean shared topology through simplification and smoothing is expensive and subtle. Existing professionally generalized vector landcover may eliminate most of that problem.

New default principle:

> If a mature vector landcover product already exists, preserve its source geometry and translate its semantics rather than rebuilding its topology.

Do not simplify, smooth, dissolve, re-polygonize, or otherwise "improve" a good vector source unless a concrete downstream mesh problem requires it.

NHN hydro has already demonstrated that detailed, valid source vectors can pass through the mesh pipeline cleanly.

---

## Hydro

### Known-good source

Authoritative detailed inland-water geometry remains NHN / HNET `Bank`.

Current known-good source:

`/home/mike/linGames/X-Plane 12/Development/GIS/Canada/NHN/tiles/+58-069/+58-069_NHN_water_final.gpkg`

Known-good diagnostics:
- NHN source features: `42079`
- Polygon parts retained: `42089`
- Edges after NHN water insertion: `635638`

NHN remains the high-fidelity hydro reference.

### New hydro question

`VEG_NORD` also contains hydrography. Its water geometry appears less granular than NHN, but it may be good enough for flight-simulator use and would have the major advantage of being part of the same vector surface fabric as the vegetation data.

Tomorrow's comparison should therefore include:
- all-in-one `VEG_NORD` hydro;
- hybrid `VEG_NORD` terrestrial + NHN hydro.

Let the mesh and cockpit view decide whether NHN's extra granularity earns the added integration complexity.

---

## NALCMS raster source

NALCMS remains a useful reference and fallback source, but it is no longer the leading production path.

### Canonical working raster

Current terrestrial source:

`~/linGames/GIS/Canada/NALCMS/+58-069_NALCMS_2020/+58-069_NALCMS_2020.nowater.tif`

`nowater.tif` is the important working source because NALCMS class `18` (water) was merged into class `0` / null. NALCMS therefore carries **no water authority** in this workflow.

Conceptually:

`NALCMS source -> class 18 becomes 0/null -> terrestrial landcover processing`

### Existing Ullaaq semantic reduction

The established reduction remains:

- `1,2 -> 1` taiga
- `8,11 -> 2` shrub tundra
- `10,12 -> 3` grass / true tundra
- `13,16 -> 4` barren tundra
- `14 -> 5` wetland
- `17 -> 6` town
- water and snow/ice are not ordinary landcover classes

---

## QGIS geometry laboratory findings — 2026-08-26

QGIS was used as a rapid visual test bench to reproduce the raster-to-vector pipeline one stage at a time.

These findings supersede the earlier assumption that the 10 ha sieve or Chaikin smoothing was the primary source of the pathological topology.

### 1. Eight-connected polygonization is bad for this raster

GDAL polygonization with **8-connectedness** produced a very large population of individually invalid polygons.

A GEOS validity check on the 8-connected result showed systemic self-touch / pinch problems across the tile.

By contrast, **4-connected polygonization** produced:

- invalid geometries: `0`
- error points: `0`

This is an important correction.

If NALCMS raster vectorization is revisited, use **4-connected polygonization**, not `polygonize -8`.

### 2. Independent polygon simplification and smoothing look excellent

On 4-connected polygonized polygons:

`polygonize -> Douglas-Peucker 30 m -> Smooth 2x / offset 0.25`

produced very attractive, organic cartographic forms.

Visually this was the closest home-built geometry to the desired result.

However, simplifying and smoothing neighboring polygons independently destroys exact shared-edge coincidence:
- gaps appear;
- overlaps also occur;
- gaps are strongly concentrated around multi-way junctions, especially four-way junctions.

The geometry itself remains much saner than the old shared-chain result.

### 3. The old shared-network path was reproduced in QGIS

The following sequence was tested from polygonized data:

`dissolve by class -> polygons to lines -> dissolve all lines -> line merge -> multipart to singleparts`

All of these stages remained visually sane.

After `Multipart to singleparts`, QGIS produced:

- `175128` line features

This is in the same general structural range as the Python injector's previous:
- `140722` merged chains

### 4. Douglas-Peucker on shared chains is the direct source of the old tangles

Applying **30 m Douglas-Peucker** to the QGIS shared-chain network immediately produced:
- shortcut chords;
- line crossings;
- little triangular constructions;
- other local topology damage.

This occurs **before smoothing**.

Applying the usual smoothing afterward rounds and enlarges those defects into the familiar:
- hooks;
- loops;
- bulbs;
- pinched lobes;
- bow-tie-like tangles.

Therefore:

> Chaikin is not the root cause. The shared-chain Douglas-Peucker step is already topologically compromised before smoothing begins.

This matches the previous debug observation that `merged_chains` was sane while `generalized_natural` was not.

### 5. QGIS Simplify Coverage was investigated

QGIS/GEOS `Simplify Coverage` was tested because it simplifies polygon coverages while attempting to preserve shared topology.

Findings:
- the 8-connected polygonized source fails immediately because of invalid polygon geometry;
- the 4-connected source is individually valid;
- the 4-connected source is **not a formally valid GEOS coverage** everywhere;
- in one clipped test, coverage validation identified `609` invalid coverage edges;
- these appeared to be sparse T-junction / edge-segmentation inconsistencies rather than wholesale visual gaps;
- whole-tile coverage processing was extremely slow;
- a clipped coverage still failed the strict coverage prerequisite.

This is not the current production path.

### 6. "Pretty polygon" gap-repair proof of concept

An unsieved stress-test branch was used:

`nowater -> 4-connected polygonize -> simplify 30 m -> smooth 2x -> Fix geometries`

`Fix geometries` produced a result visually indistinguishable from the pre-fix smoothed layer.

A local clipped Difference test:

`original 4-connected polygons - fixed pretty polygons`

successfully produced explicit uncovered gap fragments.

Observed on the clipped unsieved stress test:
- Difference fragments: `4461`
- original `DN` class attribute was preserved

Merging:
- fixed pretty polygons
- Difference gap fragments

produced **100% individually valid geometry** in `Check validity`.

Formal full-coverage validation of this repaired result was not established before changing direction.

This experiment proves that aesthetically good independent generalization and valid geometry are not mutually exclusive. It may remain useful as a fallback research path outside `VEG_NORD` coverage.

### 7. Sieve status changed

The earlier 10 ha sieve remains technically useful, but it is no longer automatically assumed to be the ideal visual source.

Observations:
- `10 ha` sieve greatly reduces small polygons and junction complexity;
- it also leads to somewhat simpler / sharper generalized shapes;
- the **unsieved** source can seed richer, more organic boundaries after simplify + smooth;
- unsieved processing cost is enormous;
- post-hoc exact vector overlay / Difference is especially expensive.

If raster vectorization is revisited, compare at least:
- unsieved;
- smaller sieve such as 1–5 ha;
- 10 ha.

The correct sieve threshold may depend on the downstream generalization method.

---

## Legacy NALCMS injector

Current working injector remains:

`O4_Ullaaq_Landcover.py`

The uploaded working copy was previously named `O4_Ullaaq_Landcover(6).py`.

Previous project-control rule still stands:
- promote one copy to the canonical filename;
- stop spawning numbered production copies.

No code was changed on 2026-08-26.

### Previous shared-network diagnostics

From the 10 ha build:

- junction micro-clusters collapsed: `9317`
- junction nodes collapsed: `21604`
- internal edges removed: `23505`
- rejected clusters, oversize: `1440`
- rejected clusters, diameter/valence: `1906`
- tiny tangle faces pruned: `202`
- graph edges removed with those faces: `447`
- short dangling graph edges pruned: `11`
- curved sparse chains caught by current guard: `31303`

Boundary counts:
- raw shared lines: `840671`
- merged chains: `140722`
- final shared boundary lines: `138639`

Vertex counts:
- raw shared: `2,145,614`
- merged chains: `1,380,430`
- generalized natural: `2,197,611`

Debug GeoPackage:

`/home/mike/Downloads/ullaaq_+58-069_debug.gpkg`

Layers:
- `raw_shared`
- `merged_chains`
- `generalized_natural`
- `town_fixed`
- `final_shared`

These data remain useful as a reference, but further repair of this generalizer is **not tomorrow's first priority**.

---

## New primary landcover source: Québec `VEG_NORD`

### Product

Québec MRNF / MFFP:

**Végétation du Nord québécois**

Primary polygon layer:

`VEG_NORD`

This is a professionally generalized northern Québec vector vegetation product. It visually matches the kind of topology and cartographic generalization the project was trying to manufacture from NALCMS.

Published minimum mapping units are approximately:
- vegetation: `16 ha`
- wetlands: `3 ha`

The raw geometry is visually excellent:
- organic boundaries;
- moderate vertex density;
- narrow and irregular ecological forms retained where useful;
- no raster staircase;
- no home-built Chaikin / Douglas-Peucker pathology.

### Geometry observations

On the raw `VEG_NORD` layer:
- `Check validity`: **100% valid**
- QGIS `Validate coverage`: fails on at least one formal coverage inconsistency

The coverage failure is **not presently considered important** because the intended experiment is to inject the raw source geometry without coverage-aware transformations.

Do not run:
- simplify;
- smooth;
- dissolve;
- fix coverage;
- re-polygonize;

unless Triangle4XP / Ortho4XP demonstrates a concrete reason.

### Sheet layout

The `+58-069` X-Plane tile intersects **five** 1:250,000 vegetation sheets.

Four provide essentially all of the tile:
- `24K` — Kuujjuaq
- `24J` — Lac Ralleau
- `24F` — Lac Hérodier
- `24G` — Lac Saffray

A fifth sheet intersects only a tiny sliver of the X-Plane tile.

For the first build, use all intersecting sheets rather than omit the marginal one.

### Download status

The full Québec SQLite archive:

`Veg_nord_SQL.zip`

is approximately `5.7 GB`.

The full download repeatedly fails / is extremely slow from the government server.

Per-sheet downloads work and are therefore the practical path for now.

Preferred format:
- **SQLite**

The full dataset is still desirable for the local GIS archive if a successful download can eventually be obtained.

### Intended ingestion model

Treat `VEG_NORD` like NHN:

`sheet SQLite -> query/merge by X-Plane tile bounds -> clip -> semantic class mapping -> inject source polygons`

No geometry generalization stage by default.

The exact `VEG_NORD` attribute-to-Ullaaq class mapping still needs to be developed.

---

## Other promising vector landcover sources

Three vector trails emerged at the end of the session.

### 1. Québec `VEG_NORD`

Current priority.

Best regional candidate for Nunavik because:
- professionally mapped for northern Québec;
- good-looking vector geometry;
- northern ecological semantics;
- hydro included;
- already available by NTS sheet.

### 2. Canadian Land Cover Circa 2000 — Vector (`LCC2000-V`)

Canada-wide vector landcover.

Although old, the age is not considered a serious problem for the current scenery purpose. Large-scale ecological landcover can be somewhat dated if the geometry is good; current hydro and settlement sources can override more time-sensitive features.

It is also valuable as a **methodological reference**.

Published/documented processing trail includes approximately:

`30 m classified raster -> 3x3 majority filter -> sieve clusters under 9 pixels -> raster-to-polygon -> smoothed/simplified outlines`

This is strikingly close to the workflow independently explored in Ullaaq.

Potential methodology contact:
- **Alexandre Beaulieu**, Natural Resources Canada / Canada Centre for Mapping and Earth Observation

He was cited in the historical processing trail and remains in federal geospatial service. If needed, a concise technical inquiry could ask whether old processing specifications, scripts, ArcInfo workflows, tolerances, or topology-preservation details survive.

### 3. Overture Maps `land_cover`

Global vector landcover derived from ESA WorldCover 2020.

Relevant global classes include:
- forest
- shrub
- grass
- crop
- wetland
- barren
- snow
- urban
- moss
- mangrove

Distributed as global vector polygons / GeoParquet with bounding-box extraction.

This is the most promising scalability lead outside Québec and Canada.

It should be tested over `+58-069` after the `VEG_NORD` ingestion path is established.

---

## Key lesson from the vector-source search

The existence and quality of `VEG_NORD`, LCC2000-V, and Overture demonstrate that the raster-to-vector task being attempted is **possible**.

The project was not chasing an impossible representation. It was rediscovering a mature cartographic generalization problem whose successful solutions already exist in professional datasets.

The project should therefore:
1. exploit those mature vector products where available;
2. use them as forensic references if custom raster vectorization is ever needed elsewhere.

---

## Deferred work

Do not mix these into the immediate `VEG_NORD` ingestion experiment:
- roads from a dedicated line source
- settlement-specific urban terrain / textures
- VFR-quality settlement detail
- photogrammetry / procedural reconstruction
- batch automation for the rest of Nunavik
- sea ice
- further repair of the NALCMS shared-chain generalizer
- global Overture integration until the local vector ingestion path works

---

## Project-control rules

1. Treat repository/filesystem and source datasets as the source of truth, not chat history.
2. Maintain one canonical `O4_Ullaaq_Landcover.py`.
3. Stop creating numbered production copies.
4. Name experiments by operation/source rather than `final2`, `mode5`, etc.
5. Change one pipeline stage at a time.
6. Commit known-good code states before geometry experiments.
7. End each substantial session with a checkpoint.
8. Keep this file current before switching threads or subsystems.
9. Preserve mature source vector topology unless a downstream failure proves modification is necessary.
10. Prefer direct A/B mesh builds over theoretical topology repair when source vectors are already valid.

---

## Next development task — 2026-08-27

### Primary task

Develop tooling to ingest **`VEG_NORD`** for `+58-069`.

Initial sequence:

1. Obtain all five intersecting per-sheet SQLite packages.
2. Inspect schema and identify the exact `VEG_NORD` class fields.
3. Query / merge the sheet polygons covering `+58-069`.
4. Clip to the exact X-Plane tile bounds.
5. Build the semantic translation from `VEG_NORD` classes to Ullaaq terrain classes.
6. Preserve raw source geometry.
7. Produce an initial mesh build.

### First A/B mesh experiment

Build two versions with otherwise identical settings:

**A. `VEG_NORD` one-stop-shop**
- native vegetation
- native `VEG_NORD` hydro

**B. Hybrid**
- `VEG_NORD` terrestrial landcover
- NHN/HNET Bank hydro

Compare in X-Plane:
- mesh stability
- shoreline detail
- small lakes / islands
- rivers
- ecological boundary quality
- constraint / vertex load
- visible benefit of NHN's higher hydro granularity

### Secondary research after the first successful vector build

- inspect LCC2000-V geometry and class mapping;
- pull Overture `land_cover` over `+58-069`;
- compare both against `VEG_NORD`, NALCMS, and the flown landscape;
- only return to custom raster vectorization if existing vector sources fail a concrete requirement.

---

## End-of-session status

No code was written or modified on 2026-08-26.  
No Git commit was made.

The major result was architectural:

> Stop forcing NALCMS raster geometry through a custom topology generalizer as the default path. Test mature vector landcover directly.

`VEG_NORD` is now the primary landcover candidate for Nunavik 1.0.

The next session starts with ingestion tooling, not topology surgery.
