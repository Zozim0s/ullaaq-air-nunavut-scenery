# Ullaaq Nunavik 1.0 — PROJECT_STATE

**Checkpoint date:** 2026-08-25  
**Repository:** `/home/mike/linGames/Ullaaq-Air-Nunavik`  
**Current tile:** `+58-069` (Kuujjuaq)

## Project organization

The project is normalized around `/home/mike/linGames`.

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
config/                    config templates and environment manifests
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
- `config/ortho4xp-python311-requirements.txt` once committed
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

### Current injector working-tree caution

The canonical injector is currently in an **experimental diagnostic state** following today's investigation:

- generalization topology diagnostics were added;
- generalization shape diagnostics were added;
- a `smooth0` control run was made by setting `DEFAULT_SMOOTH_ITERATIONS = 0`;
- the installed Ortho4XP copy was redeployed from the canonical repo copy.

These changes were useful for diagnosis but should not automatically be treated as final production behavior.

Before the next coding session:

```bash
cd /home/mike/linGames/Ullaaq-Air-Nunavik
git status --short
git diff -- patches/ortho4xp/O4_Ullaaq_Landcover.py
```

Then decide what diagnostic code to retain and what should be reverted or committed.

The known-good pre-diagnostic shared-network injector restored from Git HEAD earlier in the session had SHA-256:

```text
2c54b6ab208439a36bcda49818de86125e4474fd618eae3238a4ba47c080c4f2
```

Do not replace the injector wholesale again. Future changes should be small diffs against the canonical repo copy.

## Ortho4XP Python environment

Ortho4XP is running from a fresh Python 3.11 virtual environment at:

`/home/mike/linGames/Ortho4XP/venv`

Recovered known-working environment:

```text
Python 3.11.16
certifi==2026.7.22
chardet==7.6.0
charset-normalizer==3.5.1
GDAL==3.12.2
idna==3.19
numpy==2.4.6
pillow==12.3.0
pyproj==3.7.2
requests==2.34.2
rtree==1.4.1
scikit-fmm==2025.6.23
shapely==2.1.2
urllib3==2.7.0
```

The upstream Ortho4XP `requirements.txt` is obsolete for this installation and should not be used as the authoritative environment spec.

Normal launch from a fresh shell:

```bash
cd /home/mike/linGames/Ortho4XP
source venv/bin/activate
source "/home/mike/linGames/Ullaaq-Air-Nunavik/config/paths.env"
python Ortho4XP.py
```

Diagnostic mode, when deliberately required:

```bash
export ULLAAQ_DIAG_GENERALIZATION=1
```

Unset it for normal runs:

```bash
unset ULLAAQ_DIAG_GENERALIZATION
```

## Current objective

Finish a believable, computationally tractable replacement mesh for `+58-069` before expanding the feature set or processing additional tiles.

The current mesh work validates:

1. NHN-derived hydro geometry and water semantics.
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

## Hydro and water semantics

Hydro is considered **good enough for the current mesh-development phase**.

Authoritative inland-water geometry comes from NHN / HNET `Bank`.

Important semantics:

- `Bank` is the authoritative inland wet/dry boundary.
- `Littoral` is the equivalent boundary concept for sea/coast.
- `Delimiter` features are theoretical/internal water divisions and must **not** be treated as shoreline.
- HHYD waterbody polygons provide water surfaces; HNET Bank/Littoral provides authoritative boundary geometry where required.

Known-good Step 1 hydro diagnostics:

- NHN source features: `42,079`
- polygon parts retained: `42,089`
- edges after NHN water insertion: `635,638`

### Major completed fix: water classes

The landcover/water interaction is now corrected. Ecological landcover is no longer allowed to paint ordinary land classes over water surfaces in the mesh workflow.

This is a major milestone: water geometry and water semantic treatment are now sufficiently correct that the current debugging effort should **not** alter the hydro pipeline.

Hydro and ecological landcover remain separate concerns.

## Landcover semantics

NALCMS remains authoritative for ecological class assignment.

- `1,2 -> 1` taiga
- `8,11 -> 2` shrub tundra
- `10,12 -> 3` grass / true tundra
- `13,16 -> 4` barren tundra
- `14 -> 5` wetland
- `17 -> 6` town
- `18 -> 0` water, handled by hydro
- `19 -> 0` snow/ice, handled separately

Roads are not to be recovered from the NALCMS raster. They belong in a separate vector/line layer.

## Current landcover source pipeline

The durable upstream change remains a **10 ha sieve before polygonization**.

```text
NALCMS reclass
    -> 10 ha sieve
    -> polygonize with 8-connectivity
    -> six semantic layers
    -> shared-boundary injector
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

Raw 10 ha polygonization:

- `4,300` polygons
- `2,127,810` polygon vertices

Polygonization must use 8-connectivity. A previous default 4-connected polygonization inflated the result to roughly `60,012` polygons and was rejected.

## Diagnostic raster experiments

Mode filtering was tested but is **not part of the current production pipeline**:

- 3x3 mode: `10,300` polygons / `1,271,285` vertices
- 5x5 mode: `7,971` polygons / `934,926` vertices
- 5x5 mode + second 10 ha sieve: `6,006` polygons / `1,600,046` vertices

The production change retained from this work is the **10 ha sieve only**.

Important new interpretation after today's debugging:

> The 10 ha sieve removes small connected regions, but it does **not** simplify the pixelated boundary of a large surviving region.

Therefore a large retained NALCMS class can still carry extensive 30 m raster stair-steps, rectangular bays, fingers, hooks, and crenellations into polygonization.

## Canonical Ortho4XP landcover injector

Canonical repository copy:

`patches/ortho4xp/O4_Ullaaq_Landcover.py`

Installed working copy:

`/home/mike/linGames/Ortho4XP/src/O4_Ullaaq_Landcover.py`

The repository copy is canonical. The Ortho4XP tree is a deployment/working target.

The shared-network injector:

1. loads six semantic polygon layers;
2. dissolves each class;
3. builds one shared/noded class-boundary network;
4. separates town geometry;
5. line-merges degree-2 fragments;
6. performs conservative junction cleanup;
7. simplifies natural chains;
8. optionally applies Chaikin smoothing;
9. pins graph endpoints;
10. restores town edges unchanged;
11. inserts the result as `DUMMY` constraints.

Baseline production-era geometry settings before today's control test:

- simplify tolerance: `30 m`
- Chaikin iterations: `2`
- Chaikin offset: `0.25`
- smoothing max angle: `180 deg`

Current experimental control setting:

- simplify tolerance: `30 m`
- Chaikin iterations: `0`

Do not interpret `smooth0` as the final desired visual treatment. It was a diagnostic control.

## Stable shared-graph diagnostics

For the 10 ha source, the graph cleanup stage has repeatedly produced the same core counts:

- junction micro-clusters collapsed: `9,317`
- junction nodes collapsed: `21,604`
- internal edges removed: `23,505`
- rejected clusters, oversize: `1,440`
- rejected clusters, diameter/valence: `1,906`
- tiny tangle faces pruned: `202`
- graph edges removed with those faces: `447`
- short dangling graph edges pruned: `11`
- curved sparse chains caught by current guard: `31,303`
- raw shared lines: `840,671`
- merged chains: `140,722`
- raw shared vertices: `2,145,614`
- merged-chain vertices: `1,380,430`

These stable counts are useful because they show that today's diagnostic experiments changed only the downstream generalization treatment, not the basic shared graph construction.

## Generalization diagnostics performed 2026-08-25

### 1. Topology diagnostic

A diagnostic-only STRtree audit compared original merged chains with their generalized candidates.

Result:

```text
0 new self-intersecting chains
8,739 chains involved in 4,377 new network-intersection pairs
```

Interpretation:

- generalization does create thousands of new pairwise crossings;
- however, QGIS inspection showed that the highlighted conflict chains explain only a minority of the visually objectionable shapes;
- the new crossings are a real secondary defect, but not the main source of the widespread boxy/hooks/loop-like geometry.

### 2. Shape-fidelity diagnostic

Measured generalized chain displacement and shortening:

```text
Hausdorff m (p50/p90/p95/p99/max):
13.52 / 30.23 / 34.57 / 43.67 / 144.06

relative Hausdorff (p50/p90/p95/p99/max):
0.0442 / 0.2175 / 0.3536 / 0.3536 / 0.4223

retained length ratio (p01/p05/p50/p95/p99):
0.5981 / 0.6452 / 0.8166 / 1.0000 / 1.0000
```

Top-1% diagnostic counts:

- absolute Hausdorff: `1,408` chains
- relative Hausdorff: `3,910` chains
- length change: `1,408` chains

QGIS inspection again showed that these statistical outliers only weakly coincided with the widespread objectionable geometry.

Conclusion: Hausdorff/length-collapse outliers are not the principal explanation.

### 3. Smoothing control: Chaikin disabled

A controlled `smooth0` run kept the 30 m simplification but disabled Chaikin smoothing.

Result:

```text
Shared boundary lines:
840,671 -> 140,722

Shared boundary vertices:
2,145,614 -> 1,380,430 -> 732,345

Final shared boundary lines:
138,177

Constrained edges added:
486,260

Number of edges after landcover insertion:
907,764
```

For comparison, the earlier `smooth2` run produced:

```text
generalized natural vertices: 2,197,611
final shared boundary lines: 138,639
```

Chaikin therefore adds a very large number of vertices, but visual inspection showed that disabling it **did not remove the characteristic hooks, boxes, fingers, and near-loops**.

Conclusion: Chaikin smoothing is not the root cause.

### 4. `raw_shared` vs `merged_chains` visual comparison

This was the decisive localization test.

At known problem locations in QGIS:

- `raw_shared` already contains the same boxy hooks, fingers, near-loops, and crenellated forms;
- `merged_chains` lies almost directly on the same geometry;
- `generalized_natural` mainly simplifies that pre-existing shape.

Therefore the objectionable geometry is already present **before**:

- chain merging,
- junction micro-cluster collapse as a source of the gross shapes,
- tangle-face pruning as a source of the gross shapes,
- 30 m simplification,
- Chaikin smoothing.

The previous working hypothesis that the defect was localized to `merged_chains -> generalized_natural` is rejected.

## Current diagnosis

The primary geometry problem has moved upstream.

Current best model:

```text
NALCMS 30 m categorical raster
    -> reclass
    -> 10 ha sieve removes small regions
    -> large surviving regions retain pixel-scale crenellated boundaries
    -> polygonize
    -> dissolve/shared-boundary extraction
    -> raw_shared already contains boxy hooks/fingers/near-loops
    -> downstream graph/generalization mostly preserves or cosmetically alters them
```

This is a much better-defined problem than the earlier suspected topology failure.

The likely missing operation is **boundary generalization at the raster/vector source stage**, not another local repair inside the shared-network injector.

A zero-cost confirmation remains available: compare the boundary of `+58-069_landcover_10ha.gpkg` directly with `raw_shared` at the known QGIS problem locations. It is expected to coincide closely, but this has not yet been formally recorded as tested.

## Debug artifacts

Canonical debug GeoPackage:

`work/+58-069/debug/ullaaq_+58-069_debug.gpkg`

Core layers:

- `raw_shared`
- `merged_chains`
- `generalized_natural`
- `town_fixed`
- `final_shared`

Diagnostic builds additionally produced layers including:

- `generalization_self_conflicts`
- `generalization_network_conflicts`
- `generalization_hausdorff_abs_p99`
- `generalization_hausdorff_rel_p99`
- `generalization_length_change_p99`

These diagnostics were useful for elimination and may be retained temporarily, but they are not production requirements.

## What was accomplished in this session

1. Restored and verified the correct shared-network injector after an erroneous whole-file replacement.
2. Re-established canonical repo -> Ortho4XP deployment discipline.
3. Recovered a stable Python 3.11 Ortho4XP environment and captured its package manifest.
4. Confirmed the 10 ha landcover source is being used from the normalized project workspace.
5. Confirmed the shared-network graph builds repeatably with stable counts.
6. Added topology diagnostics without changing mesh geometry.
7. Measured `4,377` new network-intersection pairs and proved they are not the main visual defect.
8. Added shape diagnostics and showed the worst Hausdorff/length outliers are also not the main visual defect.
9. Ran a `smooth0` control and acquitted Chaikin smoothing as the root cause.
10. Compared `raw_shared`, `merged_chains`, and `generalized_natural` in QGIS and localized the gross geometry problem upstream of generalization.
11. Corrected water-class behavior so ecological terrain no longer paints over water, a major milestone for the mesh pipeline.

## Next development task

Do **not** broaden scope yet.

The next problem is:

> Generalize the 30 m categorical landcover boundary before or during vectorization so broad ecological regions retain their meaningful shape without carrying pixel-scale crenellation into the constrained mesh.

Before writing new code:

1. inspect `+58-069_landcover_10ha.gpkg` directly against `raw_shared` at the known problem locations;
2. review which existing raster/vector generalization operations preserve categorical topology and shared boundaries;
3. choose one small controlled experiment;
4. keep hydro unchanged;
5. keep the 10 ha sieve as the baseline unless the experiment specifically tests a source-stage alternative;
6. compare the same known QGIS locations before attempting another full mesh build.

Potential future approaches to evaluate, not yet selected:

- categorical boundary smoothing/generalization before polygonization;
- topology-preserving simplification of polygon boundaries immediately after polygonization and before the shared-network injector;
- a controlled raster neighborhood/generalization operation that reduces boundary crenellation without reintroducing the excessive polygon fragmentation seen in earlier mode-filter tests.

Do not simply add more local guards to `generalized_natural`: today's tests show the main shapes already exist in `raw_shared`.

## Deferred work

Keep these separate until the core mesh is stable:

- roads
- settlement/urban terrain treatment
- VFR settlement detail
- photogrammetry/procedural reconstruction
- dynamic sea ice
- additional Nunavik tiles
- large-scale batching/automation

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
