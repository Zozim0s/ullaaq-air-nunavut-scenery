# Ullaaq Nunavik 1.0 — PROJECT_STATE

**Checkpoint date:** 2026-08-25
**Repository:** `/home/mike/linGames/Ullaaq-Air-Nunavik`
**Current tile:** `+58-069` (Kuujjuaq)

## Project organization

The project is now normalized around `/home/mike/linGames`.

```text
/home/mike/linGames/
├── GIS/                  # authoritative large GIS datasets
├── Ortho4XP/             # external tool / installed working copy
├── Ullaaq-Air-Nunavik/   # project Git repository
├── X-Plane 12/           # runtime target
└── SteamLibrary/
```

Canonical project repo:

`/home/mike/linGames/Ullaaq-Air-Nunavik`

Important repo areas:

```text
config/                    config templates
docs/                      project state and reference notes
patches/ortho4xp/          canonical Ullaaq Ortho4XP patches
tools/hydro/               hydro processing tools
tools/landcover/           NALCMS processing tools
work/+58-069/              ignored derived/intermediate tile workspace
output/                    ignored generated scenery
source/                    ignored project-owned large source data
reference/                 ignored third-party/reference material
```

Current tile workspace:

```text
work/+58-069/
├── builds
├── debug
├── diagnostics
├── dsf-decompile
├── hydro
├── landcover
├── mesh
├── ortho4xp
└── scratch
```

Current landcover work products:

```text
work/+58-069/landcover/
├── +58-069_landclass_10ha.gpkg
├── +58-069_landclass_sieve_10ha.tif
├── +58-069_landcover_10ha.gpkg
└── +58-069_landcover.gpkg
```

`+58-069_landcover_10ha.gpkg` is the current production candidate.
`+58-069_landcover.gpkg` is retained as the pre-sieve A/B baseline.

## Git / project-control state

The repo is under Git and GitHub.

Tracked project infrastructure includes:

- `.gitignore`
- `config/paths.env.example`
- `docs/`
- `patches/ortho4xp/O4_Ullaaq_Landcover.py`
- `tools/hydro/grhq_to_osm_v2.py`
- `tools/landcover/build_ullaaq_landclass_mask.py`
- `tools/landcover/build_ullaaq_landcover_gpkg.py`
- `tools/landcover/reclassify_nalcms_ullaaq.py`

Large datasets and generated work remain ignored under `/source/`, `/work/`, `/reference/`, and `/output/`.

Machine-local absolute paths belong in `config/paths.env`, which is ignored. Portable examples belong in `config/paths.env.example`.

Canonical roots for this machine:

```bash
ULLAAQ_ROOT="/home/mike/linGames/Ullaaq-Air-Nunavik"
GIS_ROOT="/home/mike/linGames/GIS"
ORTHO4XP_ROOT="/home/mike/linGames/Ortho4XP"
XPLANE_ROOT="/home/mike/linGames/X-Plane 12"
ULLAAQ_TILE="+58-069"
ULLAAQ_LANDCOVER_GPKG="$ULLAAQ_ROOT/work/$ULLAAQ_TILE/landcover/${ULLAAQ_TILE}_landcover_10ha.gpkg"
ULLAAQ_DEBUG_GPKG="$ULLAAQ_ROOT/work/$ULLAAQ_TILE/debug/ullaaq_${ULLAAQ_TILE}_debug.gpkg"
```

## Current objective

Finish a believable, computationally tractable replacement mesh for `+58-069` before expanding the feature set or processing additional tiles.

The current mesh build validates:

1. NHN-derived hydro geometry.
2. NALCMS-derived ecological landcover boundaries.
3. Ortho4XP / Triangle4XP behavior with the constrained mesh.

Deferred for now:

- road network integration
- urban / settlement terrain textures
- VFR settlement-detail layer
- photogrammetry / procedural settlement reconstruction
- sea ice
- batching across Nunavik

## Authoritative GIS sources

Large national/regional datasets remain outside the Git repo:

```text
/home/mike/linGames/GIS/Canada/
├── MRDEM/
├── NALCMS/
└── NHN/
```

Do not duplicate them into the repository.

## Hydro pipeline

Hydro is considered good enough for the current mesh-development phase.

Authoritative inland-water geometry comes from NHN / HNET `Bank`.

Known-good Step 1 diagnostics:

- NHN source features: `42,079`
- polygon parts retained: `42,089`
- edges after NHN water insertion: `635,638`

Important decision: **NHN/HNET Bank is the authoritative wet/dry boundary for inland water.** `Delimiter` features are not shoreline.

Hydro remains separate from ecological landcover generalization.

## Landcover semantics

NALCMS remains authoritative for ecological class assignment.

- `1,2 -> 1` taiga
- `8,11 -> 2` shrub tundra
- `10,12 -> 3` grass / true tundra
- `13,16 -> 4` barren tundra
- `14 -> 5` wetland
- `17 -> 6` town
- water and snow/ice are not ordinary ecological landcover classes

Roads are not to be recovered from the NALCMS raster. They belong in a separate vector/line layer.

## Current landcover source pipeline

The durable upstream change is a **10 ha sieve before polygonization**.

```text
NALCMS reclass
    -> 10 ha sieve
    -> polygonize with 8-connectivity
    -> six semantic layers
    -> existing shared-boundary injector
```

The 10 ha sieve was selected after direct comparison with ESRI imagery in QGIS.

Findings:

- fine-scale NALCMS class boundaries often do not correlate precisely with visible imagery;
- tiny class islands are frequently unnecessary for realism;
- the 10 ha sieve removes substantial classification clutter while preserving broad ecological structure;
- skinny raster-road features disappear, which is desirable because roads come from another source;
- 10 ha is the current production candidate, not necessarily the final threshold.

Current 10 ha polygon counts:

- taiga: `556`
- shrub tundra: `1,802`
- grass tundra: `1,392`
- barren tundra: `541`
- wetland: `2`
- town: `7`
- total: `4,300`

Raw 10 ha polygonization: `2,127,810` polygon vertices.

## Diagnostic raster experiments

Mode filtering was tested but is **not part of the current production pipeline**:

- 3x3 mode: `10,300` polygons / `1,271,285` vertices
- 5x5 mode: `7,971` polygons / `934,926` vertices
- 5x5 mode + second 10 ha sieve: `6,006` polygons / `1,600,046` vertices

The production change retained from this work is the **10 ha sieve only**.

## Canonical Ortho4XP landcover injector

Canonical repository copy:

`patches/ortho4xp/O4_Ullaaq_Landcover.py`

Installed working copy:

`/home/mike/linGames/Ortho4XP/src/O4_Ullaaq_Landcover.py`

The repository copy is canonical. The Ortho4XP tree is a deployment/working target.

The injector:

1. loads six semantic polygon layers;
2. dissolves each class;
3. builds one shared/noded class-boundary network;
4. separates town geometry;
5. line-merges degree-2 fragments;
6. performs conservative junction cleanup;
7. simplifies natural chains at `30 m`;
8. applies two Chaikin passes at offset `0.25`;
9. pins graph endpoints;
10. restores town edges unchanged;
11. inserts the result as `DUMMY` constraints.

Current geometry settings:

- simplify tolerance: `30 m`
- Chaikin iterations: `2`
- Chaikin offset: `0.25`
- smoothing max angle: `180 deg`

## Current 10 ha build diagnostics

- junction micro-clusters collapsed: `9,317`
- junction nodes collapsed: `21,604`
- internal edges removed: `23,505`
- rejected clusters, oversize: `1,440`
- rejected clusters, diameter/valence: `1,906`
- tiny tangle faces pruned: `202`
- graph edges removed with those faces: `447`
- short dangling graph edges pruned: `11`
- curved sparse chains caught by current guard: `31,303`

Boundary counts:

- raw shared lines: `840,671`
- merged chains: `140,722`
- final shared boundary lines: `138,639`

Vertex counts:

- raw shared: `2,145,614`
- merged chains: `1,380,430`
- generalized natural: `2,197,611`

The 30 m simplification substantially reduces geometry, but two Chaikin passes add the vertex count back.

## Current defect

Debug-stage inspection localized the remaining tangles:

- `raw_shared`: raster-like but topologically sane
- `merged_chains`: still sane
- `generalized_natural`: odd local circles, hooks, bow-ties, connector chords, and other pathological geometry appear
- `final_shared`: carries those defects forward; town geometry is restored intentionally

Therefore the 10 ha sieve and hydro are **not** causing the current tangles.

The defect is localized to:

```text
merged_chains
    -> 30 m Douglas-Peucker simplification
    -> 2x Chaikin smoothing
    -> generalized_natural
```

The present sparse-chain guard is insufficient.

## Debug artifacts

The injector debug GeoPackage contains:

- `raw_shared`
- `merged_chains`
- `generalized_natural`
- `town_fixed`
- `final_shared`

Canonical future debug location: `work/+58-069/debug/`.

Do not use `~/Downloads` as a project working directory.

## Next development task

Do not broaden scope.

Target only the landcover generalizer.

Goal: prevent `merged_chains -> generalized_natural` from creating pathological local geometry while retaining the shared-network/topology-preserving approach.

Likely first experiment:

1. evaluate every simplified open chain geometrically, not only chains reduced to fewer than four coordinates;
2. compare simplified chains to originals using Hausdorff distance and/or length-to-chord collapse;
3. retry locally at a smaller tolerance when simplification materially distorts gross shape;
4. keep junction endpoints pinned;
5. inspect the same known tangle locations in the debug GeoPackage before another full mesh build.

Do not change the hydro pipeline or 10 ha sieve in response to this defect.

## Project-control rules

1. Git and project files are the source of truth.
2. Maintain one canonical `O4_Ullaaq_Landcover.py`.
3. Do not create numbered production copies.
4. Keep authoritative large GIS data under `/home/mike/linGames/GIS`.
5. Keep derived per-tile products under `work/<tile>/`.
6. Keep generated work products out of Git.
7. Name experimental products by operation and parameter.
8. Change one pipeline stage at a time.
9. Commit known-good code/config/docs checkpoints before new geometry experiments.
10. End each substantial session by updating this file and/or adding a short session note.
11. Before switching threads, make a session handoff checkpoint.
12. Roads, urban textures, photogrammetry, sea ice, and batching remain separate future workstreams until the core mesh is stable.
