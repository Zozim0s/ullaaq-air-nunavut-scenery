# Nunavik / Ullaaq Scenery Project State

**Checkpoint date:** 2026-08-25  
**Current tile:** `+58-069` (Kuujjuaq)

## Current objective

Finish a believable, computationally tractable `+58-069` replacement mesh before expanding to roads, urban treatment, or additional tiles.

The present build validates:
- NHN-derived hydro geometry
- NALCMS-derived ecological landcover boundaries
- Ortho4XP / Triangle4XP behavior with the constrained mesh

Roads and settlement-specific urban textures are out of scope for the present build.

## Current production pipeline

### Hydro

Authoritative inland-water geometry comes from NHN / HNET `Bank`.

Current Step 1 source:

`/home/mike/linGames/X-Plane 12/Development/GIS/Canada/NHN/tiles/+58-069/+58-069_NHN_water_final.gpkg`

Known-good diagnostics:
- NHN source features: `42079`
- Polygon parts retained: `42089`
- Edges after NHN water insertion: `635638`

Hydro is considered good enough for the present mesh experiment.

### Landcover

NALCMS remains authoritative for ecological class assignment.

Class reduction:
- `1,2 -> 1` taiga
- `8,11 -> 2` shrub tundra
- `10,12 -> 3` grass / true tundra
- `13,16 -> 4` barren tundra
- `14 -> 5` wetland
- `17 -> 6` town
- water and snow/ice are not ordinary landcover classes

### New upstream generalization step

The durable pipeline change is a **10 ha sieve before polygonization**:

`NALCMS reclass -> 10 ha sieve -> polygonize -8 -> six semantic layers -> existing shared-boundary injector`

The 10 ha raster visually preserved the landscape-scale ecological signal while removing many tiny class islands and skinny features such as roads that should come from separate line sources.

Current source:

`+58-069_landcover_10ha.gpkg`

Expected layer counts:
- taiga: `556`
- shrub_tundra: `1802`
- grass_tundra: `1392`
- barren_tundra: `541`
- wetland: `2`
- town: `7`

Total: `4300`

Raw 10 ha polygonization: `2,127,810` polygon vertices.

## Canonical injector

Current working injector: `O4_Ullaaq_Landcover.py`

The uploaded working copy is presently named `O4_Ullaaq_Landcover(6).py`. Promote one copy to the canonical filename before further development and stop spawning numbered production copies.

The injector:
1. dissolves each semantic class,
2. builds one shared/noded boundary network,
3. keeps town geometry separate,
4. line-merges degree-2 fragments,
5. performs conservative junction cleanup,
6. simplifies natural chains at `30 m`,
7. performs `2` Chaikin passes at offset `0.25`,
8. pins graph endpoints,
9. restores town edges,
10. inserts the shared result as `DUMMY` constraints.

Current geometry settings:
- simplify: `30 m`
- Chaikin iterations: `2`
- Chaikin offset: `0.25`
- max smoothing angle: `180 deg`

Current source override:

`ULLAAQ_LANDCOVER_GPKG=/home/mike/linGames/X-Plane 12/Development/Forest Scenery/+58-069_NALCMS_2020/+58-069_landcover_10ha.gpkg`

## Current build diagnostics

The 10 ha source entered the injector successfully with a cold cache.

Observed processing:
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

The 30 m simplification reduces geometry substantially, but two Chaikin passes add the vertex count back.

Debug GeoPackage:

`/home/mike/Downloads/ullaaq_+58-069_debug.gpkg`

Layers:
- `raw_shared`
- `merged_chains`
- `generalized_natural`
- `town_fixed`
- `final_shared`

## Current defect

The 10 ha sieve is **not** the source of the remaining local tangles.

Debug inspection indicates:
- `raw_shared`: raster-like but topologically sane
- `merged_chains`: still sane
- `generalized_natural`: local circles, hooks, bow-ties, straight connector chords, and similar odd geometry appear
- `final_shared`: carries those defects forward; blocky town geometry is restored intentionally

So the defect is localized to:

`merged shared graph -> 30 m Douglas-Peucker simplification -> 2x Chaikin`

The present sparse-chain guard is not sufficient.

**Do not change the sieve or hydro pipeline in response to this defect.**

## Deferred work

Do not mix these into the current mesh-debugging loop:
- roads from a dedicated line source
- urban / settlement terrain and textures
- VFR-quality settlement detail
- photogrammetry / procedural reconstruction
- batch processing for the rest of Nunavik
- sea ice

## Project-control rules

1. Treat the repository/filesystem as the source of truth, not chat history.
2. Maintain one canonical `O4_Ullaaq_Landcover.py`.
3. Stop creating numbered production copies.
4. Name experimental source products by operation, e.g. `sieve10ha`.
5. Change one pipeline stage at a time.
6. Commit known-good states before geometry experiments.
7. End each substantial work session with a short checkpoint.
8. Keep this file current before switching threads or subsystems.

## Next development task

Pause feature work until the project layout is stabilized.

When development resumes, target only the generalizer.

Goal: prevent `merged_chains -> generalized_natural` from creating pathological local geometry while retaining the shared-network approach.

Likely first experiment:
- evaluate every simplified open chain geometrically, not only sparse `<4 point` results;
- compare simplified chain to the original using Hausdorff distance and/or length-to-chord collapse;
- retry locally at smaller tolerance when simplification materially distorts the original;
- keep junction endpoints pinned;
- inspect the same known tangle locations in the debug GPKG before another full mesh build.

The 10 ha sieve remains the current production landcover source unless later flight testing shows a more aggressive threshold is warranted.
