# Nunavik / Ullaaq Scenery Project Status

**Checkpoint date:** 2026-08-30  
**Current tile:** `+58-069` (Kuujjuaq)  
**Session result:** First production-style wild-ground material brought to a convincing multiscale state. The rocky-tundra / bedrock class now uses a real Nunavik orthophoto-derived macro texture plus a custom lichen/weathered-rock decal. Seam removal, tiling, physical scale, and close-to-midrange rendering were validated in X-Plane. The next priority is to bring the remaining wild classes to approximately this same level so the tile can be judged as a unified visual system.

---

## Executive status

The scenery architecture remains stable:

```text
MRDEM                  -> landform / elevation
NHN / HNET Bank        -> authoritative hydrography
VEG_NORD               -> terrestrial geometry + ecological semantics
Ortho4XP               -> constrained replacement mesh + DSF construction
custom Ullaaq .ter     -> wild-ground material control
VEG_NORD-driven .for   -> 3D vegetation overlay control
road centerlines       -> human transport geometry
custom draped surfaces -> visible road / settlement ground treatment
individual .obj        -> explicit building placement
```

The engineering stack is no longer the active problem.

Current development mode:

```text
author real terrain materials
    -> validate each class at multiple scales
    -> keep ecology/geometry fixed
    -> then judge the unified regional whole
```

The first convincing production-style material is now the **bedrock / rocky-tundra** family.

---

# Major result: bedrock macro texture is effectively solved

## Source imagery

Primary source frame:

```text
~/linGames/GIS/Canada/Quebec/Orthophoto/Q10805_067_30CM_F06.TIF
```

Source properties:

```text
6471 x 9528 px
0.30 m/px
RGB
NAD83(CSRS) / MTM zone 6
EPSG:2948
```

The stock Laminar rocky-tundra terrain uses:

```text
1024 x 1024 macro
PROJECTED 1248 x 1248 m
```

Therefore the exact Québec source footprint for one equivalent macro tile is:

```text
4160 x 4160 px @ 0.30 m/px
= 1248 x 1248 m
```

This exact physical-scale match remains the basis of the bedrock material.

---

## Raw control

Original 1248 m quarry crop:

```text
work/material-lab/rock/rock_qc_A_source_4160.tif
```

Original downsampled control:

```text
work/material-lab/rock/rock_qc_A_1024.png
```

The raw orthophoto immediately outperformed the stock generic rock material in X-Plane, especially in:
- Canadian Shield fracture structure;
- long geological grain;
- subdued rock/lichen palette;
- dark vegetated seams;
- absence of the stock white/snow-confetti appearance.

The remaining problem was authored repetition, not source quality.

---

# Seamless-tile authoring result

## Method

The 4160² source was offset by half-width / half-height:

```text
2080 px x 2080 px
```

This moved the true wrap seams to the image center.

Working assets included:

```text
rock_qc_A_source_offset_2080.png
rock_qc_A_source_offset_2080.tif
```

The seam required **manual human cloning**.

This is now considered a deliberate authoring step, not a good automation target.

Reason:

> The source landscape itself contains abundant long, linear fractures, drainage seams, glacial grooves, vegetation corridors, and tonal boundaries. Automated line/discontinuity detection cannot reliably distinguish authentic geology from tile-edge artifacts.

The tile received two detailed manual scrub passes.

The final authored high-resolution master is:

```text
work/material-lab/rock/rock_qc_A_source_seam_v1.png
```

Diagnostic 2x2 tiling:

```text
work/material-lab/rock/rock_qc_A_source_seam_v1_tiled_2x2.png
```

Current result:
- no remaining obvious wrap edge;
- no rectangular seam artifact in X-Plane;
- periodicity is detectable only under deliberately hostile texture-atlas inspection;
- after prolonged manual inspection, repetition is no longer salient even to an observer who knows the source tile intimately;
- normal X-Plane perspective, terrain relief, VEG_NORD polygon boundaries, mipmapping, surrounding classes, and motion further suppress repetition.

The macro tile should now be considered **finished enough for production v1**.

Do not continue scrubbing merely because a perfect orthographic 2x2 diagnostic mathematically reveals repetition.

---

## Runtime texture

Current runtime macro should be regenerated from the final high-resolution master:

```text
rock_qc_A_source_seam_v1.png
    -> average downsample
rock_qc_A_seam_v1_1024.png
```

Production resource path:

```text
scenery/Ullaaq_Nunavik_Resources/textures/rock/rock_qc_A_seam_v1_1024.png
```

Custom terrain definition:

```text
scenery/Ullaaq_Nunavik_Resources/terrain/ullaaq_rock_test.ter
```

Current custom terrain library path:

```text
lib/ullaaq/terrain/rock_test.ter
```

VEG_NORD semantic class `5` / rocky tundra remains routed to this custom `.ter`.

---

# Macro validation

The final scrubbed macro was examined:
- nearly on the ground;
- low level;
- obliquely over long strips;
- over massive contiguous rocky-tundra areas;
- against Google Earth / ESRI imagery;
- against ground photographs from a hiking trail in the same Kuujjuaq terrain.

The large-scale match is convincing.

The custom material reproduces the real landscape grammar:

```text
broad exposed shield slabs
dark fracture / drainage networks
subdued grey-brown-green palette
vegetation in seams and depressions
small dark water pockets
long regional structural grain
```

At altitude, the custom rock no longer appears as the problem material.

Instead, neighboring stock terrain definitions increasingly stand out as:
- too pale;
- too high contrast;
- too generic;
- visually disconnected from real Nunavik imagery.

Important conclusion:

> The current custom bedrock material is becoming the visual baseline against which remaining stock materials look wrong.

---

# Ground reference findings

Ground-level photographs from the local hiking trail showed:

```text
smooth glacially worked exposed bedrock
fine fissures and weathering
light and dark lichen
moss / heath in seams and depressions
low shrub mats
occasional small conifers
very little loose gravel-like surface
```

This clarified the intended scale hierarchy:

```text
kilometre / hectometre:
    orthophoto macro
    slabs, fracture fields, dark corridors, ponds

metre / sub-metre:
    custom decal
    lichen, weathering, fine surface structure

3D:
    future heath / dwarf shrub / sedge / tiny conifer scatter
```

The decal should not try to recreate the full landscape, and the macro texture should not be expected to provide realistic centimetre-scale ground appearance.

---

# Stock decal problem identified

The stock rock material used:

```text
DECAL_LIB lib/g10/decals/rail_ballast_dry.dcl
```

At very close range this produced:

```text
dense pebble / gravel carpet
strong high-frequency aggregate texture
visual behavior unlike exposed Canadian Shield slab
```

Removing the decal entirely exposed the expected engine limitation:

```text
1024 px across 1248 m
~1.21875 m/px
```

At near-ground distance, the naked macro becomes large blurry pixels.

This is not a pipeline failure.

It proves the intended division of labor:

```text
macro -> regional / landscape structure
decal -> close-range material detail
```

---

# Stock decal anatomy

Physical stock decal:

```text
Resources/default scenery/1000 decals/rail_ballast_dry.dcl
```

Library export:

```text
lib/g10/decals/rail_ballast_dry.dcl
```

Recipe:

```text
A
1000
DECAL

DECAL_PARAMS_PROJ 8 8 -1.0 3.7 3.7 -5.0 0.0 0.0 -0.7 0 0 0 0 0 0 textures/DECAL_GA_stony_dirt3.png
DECAL_PARAMS_PROJ 2000 2000 0.0 0 0 0 0 0 0 0 0 0 0 0 0.15 textures/DECAL_LF_grey.png
```

Stock textures:

```text
DECAL_GA_stony_dirt3.png
DECAL_LF_grey.png
```

The first is a Gray + Alpha PNG.

Observed channel statistics for the stock GA texture:

```text
Gray:
    min 0
    max 255
    mean ~127.86
    stddev ~38.94

Alpha:
    min 16
    max 248
    mean ~127.84
    stddev ~28.75
```

The 8 m GA artwork is responsible for the obvious close-range gravel character.

The second 2000 m layer is broad low-frequency grayscale modulation.

---

# Custom bedrock decal source

A CC0 Poly Haven asset was selected:

```text
Lichen Rock
```

Local source directory:

```text
work/material-lab/rock/lichen_rock_4k.blend/textures
```

Files:

```text
lichen_rock_diff_4k.jpg
lichen_rock_disp_4k.png
lichen_rock_nor_gl_4k.exr
lichen_rock_rough_4k.exr
```

Poly Haven's asset license is CC0, making it suitable for derivative distributable scenery artwork.

The **roughness map** proved particularly useful as decal source material because it carries:
- lichen distribution;
- fine rock structure;
- weathering variation;
- no unwanted source color.

The diffuse remains useful as reference, but the macro orthophoto already owns terrain color.

---

# Custom bedrock decal v1 / v2

## v1

First custom detail image:

```text
work/material-lab/rock/DECAL_RGB_ullaaq_bedrock_v1.png
```

Generated from:

```text
lichen_rock_rough_4k.exr
```

Initial contrast compression:

```text
+level 38%,62%
```

Output:

```text
1024 x 1024
RGB PNG
R=G=B grayscale information
PNG truecolor storage
```

ImageMagick reports semantic `Type: Grayscale` because RGB values are equal, but PNG metadata confirms:

```text
png:IHDR.color-type-orig: 2
```

so the image is physically RGB.

## v2 higher-contrast test

Higher-contrast version:

```text
DECAL_RGB_ullaaq_bedrock_v2_contrast.png
```

Generated with:

```text
+level 30%,70%
```

This provides more visible fine detail while retaining the correct weathered-bedrock visual vocabulary.

The v2 contrast version is the current visual winner.

---

# Custom Ullaaq decal resource

Custom resource location:

```text
scenery/Ullaaq_Nunavik_Resources/decals/ullaaq_bedrock_v1.dcl
```

Custom texture directory:

```text
scenery/Ullaaq_Nunavik_Resources/decals/textures/
```

Current custom resources include:

```text
DECAL_RGB_ullaaq_bedrock_v1.png
DECAL_RGB_ullaaq_bedrock_v2_contrast.png
DECAL_LF_grey.png
```

Custom library export:

```text
lib/ullaaq/decals/bedrock_v1.dcl
```

Current bedrock `.ter` references the Ullaaq decal resource.

The 8 m physical projection and stock shader coefficients were retained for the first custom test.

Current result with v2:
- gravel character eliminated;
- lichen/weathering pattern reads plausibly near ground;
- at normal low-level flight range the decal does not appear as a separate overlay;
- no obvious 8 m repetition was observed;
- handoff between decal and macro appears clean;
- at very close range the engine's underlying macro-resolution limit remains visible, as expected.

---

# Important scale lesson

Do not evaluate X-Plane terrain material as though it were a centimetre-resolution ground renderer.

Current physical scales:

```text
macro:
    1248 m / 1024 px
    ~1.21875 m/px

custom decal:
    projected at 8 x 8 m
```

At roughly on-ground / single-digit-foot viewing distance:
- macro resolution is inherently insufficient for photorealistic ground;
- decal exists to supply plausible high-frequency structure;
- 3D vegetation will later provide another layer of actual geometric detail.

The meaningful material test range is low-level flying and normal operational viewing, not forensic crawling over the terrain surface.

---

# Potential future 3D low vegetation

The local ground photographs strongly support a future low-vegetation scatter layer.

X-Plane `.for` machinery can be used for very low vegetation, as demonstrated by existing third-party grass implementations.

Potential Nunavik ground vegetation vocabulary:

```text
heath_low       ~10–20 cm
heath_medium    ~20–35 cm
dwarf_shrub     ~30–60 cm
sedge_tuft      ~20–45 cm
tiny_spruce     ~0.5–1.5 m
lichen_moss_clump
```

This should be treated as a separate 3D material layer, not baked indiscriminately into the bedrock decal.

Likely hierarchy:

```text
macro orthophoto
    -> broad geological / ecological pattern

decal
    -> fine bedrock skin

low .for vegetation
    -> actual heath / shrub / tuft volume

forest .for
    -> larger trees where ecology warrants them
```

Do not build this layer yet unless useful for evaluating the unified wild-class set.

---

# Surficial geology side investigation

A SIGÉOM Québec surficial / morphosedimentary dataset was obtained and loaded in QGIS.

Visible relevant layer:

```text
SGM_ZONE_MORPH_QC_SO
```

Additional Quaternary / morphosedimentary layers are available in the same SIGÉOM package.

The layer appears highly detailed and potentially useful for:
- exposed bedrock;
- till;
- surficial sediment;
- organic / wet deposits;
- other geomorphic modifiers.

This is promising, but it is **not currently integrated into the production scenery pipeline**.

Current decision:

> Keep surficial geology as a future modifier/reference source. Do not derail the current material-authoring pass into another GIS architecture project.

The current bedrock class was successfully authored without needing this layer.

---

# Bedrock v1 assessment

The bedrock material now has a coherent multiscale structure:

```text
real Nunavik orthophoto
    -> authentic macro geology

custom Poly Haven-derived decal
    -> plausible lichen/weathering detail

future sparse low vegetation
    -> close-range dimensional ecology
```

Current qualitative status:

```text
macro source quality             PROVEN
physical macro scale             PROVEN
manual seamless authoring        PROVEN
in-sim tiling                    ACCEPTABLE / PROVEN ENOUGH
regional geological read         PROVEN
stock decal unsuitability        PROVEN
custom decal mechanism           PROVEN
custom decal source vocabulary   PROVEN
decal-to-macro handoff           PROVEN ENOUGH
bedrock material v1              READY TO FREEZE FOR NOW
```

Do not continue polishing bedrock while the rest of the tile still uses mismatched stock materials.

---

# Updated authoring strategy

The next phase should work **through the remaining wild classes to approximately the same maturity level as bedrock**.

The purpose is not to perfect each class in isolation.

The purpose is to reach a point where the entire ecological mosaic can be judged as one visual system.

Recommended loop for each class / visual recipe:

```text
1. identify the real-world material family
2. choose representative Québec imagery
3. quarry at a physically appropriate X-Plane macro scale
4. make the macro tile seamless manually where necessary
5. validate macro at low / medium / high altitude
6. inspect stock decal behavior
7. replace decal only if stock detail vocabulary is wrong
8. stop when the class is coherent enough to evaluate beside its neighbors
9. move to the next class
```

Do not spend an hour squeezing marginal gains out of one class while neighboring materials remain placeholders.

---

# Suggested class order

Current working visual vocabulary remains:

```text
1  taiga_shrub
2  taiga_lichen
3  taiga_lichen_moss
4  taiga_moss_heath

5  shrub_tundra
6  subarctic_heath
7  erect_shrub_tundra

8  bedrock
9  bare_mineral

10 wet_tundra_peat
11 fen
12 palsa_peatland
13 salt_marsh
```

Bedrock is now the first class brought to the new standard.

A sensible next progression is:

```text
1. bare_mineral / scree
2. rock + heath transition material
3. open/subarctic heath
4. shrub / erect-shrub tundra
5. wet tundra / peat
6. fen / palsa / marsh
7. taiga ground families
```

Exact order may change depending on which stock class currently creates the most visually offensive boundaries.

The key goal is coverage of the whole visual vocabulary, not perfecting one family.

---

# Unified-whole evaluation target

Once each major wild family has:
- a plausible macro;
- acceptable close-range detail;
- compatible color / tonal vocabulary;
- no gross tiling defects;

perform a broad X-Plane review of the entire `+58-069` tile.

Evaluate:

```text
class-to-class tonal continuity
ecological transitions
rock / heath / wetland balance
forest-floor integration
regional visual coherence
low-altitude VFR appearance
medium-altitude mosaic
high-altitude landscape structure
repetition fingerprints
material boundaries
seasonal plausibility
```

Only after this unified pass should individual materials receive deeper second-generation tuning.

---

# What NOT to do next

Do not:

```text
reopen VEG_NORD geometry
redo NHN hydro
redo the mesh
return to NALCMS raster topology
over-process the successful bedrock macro
chase mathematically perfect nonrepetition
turn the surficial-geology dataset into a new pipeline immediately
perfect 3D heath before other wild classes exist
judge material quality only from near-zero-altitude screenshots
restore stock suburban Kuujjuaq autogen
```

The active problem is now visual coherence across ecological classes.

---

# Important current paths

Project:

```text
~/linGames/Ullaaq-Air-Nunavik
```

Material lab:

```text
~/linGames/Ullaaq-Air-Nunavik/work/material-lab
~/linGames/Ullaaq-Air-Nunavik/work/material-lab/rock
```

Bedrock high-resolution master:

```text
work/material-lab/rock/rock_qc_A_source_seam_v1.png
```

Bedrock runtime macro:

```text
work/material-lab/rock/rock_qc_A_seam_v1_1024.png
```

Poly Haven source:

```text
work/material-lab/rock/lichen_rock_4k.blend/textures/
```

Custom resource package:

```text
~/linGames/Ullaaq-Air-Nunavik/scenery/Ullaaq_Nunavik_Resources
```

Custom rock terrain:

```text
scenery/Ullaaq_Nunavik_Resources/terrain/ullaaq_rock_test.ter
```

Custom decal:

```text
scenery/Ullaaq_Nunavik_Resources/decals/ullaaq_bedrock_v1.dcl
```

Custom decal textures:

```text
scenery/Ullaaq_Nunavik_Resources/decals/textures/
```

VEG_NORD tile:

```text
work/+58-069/landcover/+58-069_VEG_NORD_tile.gpkg
```

NHN water:

```text
/home/mike/linGames/X-Plane 12/Development/GIS/Canada/NHN/tiles/+58-069/+58-069_NHN_water_final.gpkg
```

Ortho4XP semantic patch:

```text
~/linGames/Ortho4XP/src/O4_DSF_Utils.py
```

---

# Project-control rules

1. Filesystem/repository and source datasets remain the source of truth.
2. Preserve the proven MRDEM + NHN + native VEG_NORD architecture.
3. NHN remains hydro authority.
4. Keep geometry generation separate from material assignment.
5. Keep macro, decal, `.for`, roads, human ground, and `.obj` layers conceptually separate.
6. Change one rendering variable at a time in material experiments.
7. Keep raw quarry crops immutable.
8. Preserve high-resolution seamless masters separately from runtime downsampled assets.
9. Human seam authoring is acceptable and expected for visually important macro textures.
10. Judge repetition in representative X-Plane viewing conditions, not only texture-atlas diagnostics.
11. Do not over-polish one material before the neighboring material vocabulary exists.
12. Keep the 31 VEG_NORD semantic classes intact even when multiple classes share visual recipes.
13. Use mature stock shader recipes where possible and replace only components proven visually wrong.
14. End substantial sessions with an updated project checkpoint.

---

# Git / reproducibility

Git status was not verified at session end.

Before committing:

```bash
cd ~/linGames/Ullaaq-Air-Nunavik
git status
```

Confirm that:
- final bedrock macro resources are in the repository;
- custom `.dcl` and texture assets are preserved;
- only intended material-lab source files are tracked;
- large raw GIS / orthophoto source files remain excluded as appropriate;
- Ortho4XP semantic changes outside the main repo remain mirrored or documented.

Suggested commit theme:

```text
Author first Nunavik bedrock material
```

---

# Next session

Primary objective:

> Bring the remaining wild ecological material families to the same approximate level as bedrock so the whole tile can be judged as a coherent system.

Start by identifying the next most visually disruptive stock class adjacent to the current custom bedrock areas.

For that class:

```text
1. identify its VEG_NORD semantics
2. identify representative real terrain
3. select / quarry authentic imagery
4. build a physically scaled macro
5. make it tile cleanly
6. inspect the stock decal
7. replace only if necessary
8. validate at several operational viewing ranges
9. stop once it is coherent enough to compare with bedrock
10. move to the next class
```

Do not seek final perfection yet.

The current milestone is a **unified Nunavik material vocabulary**, not thirteen individually perfected textures.

---

# End-of-day assessment

2026-08-30 established the first convincing production-style terrain material for Nunavik 1.0.

The rocky-tundra / bedrock class now demonstrates that the intended authoring model works:

```text
authoritative ecological geometry
    +
real Nunavik orthophoto at exact physical macro scale
    +
manual seamless authoring
    +
custom close-range decal from appropriate CC0 surface material
    +
future sparse 3D vegetation
```

The result holds together from low-level flight through regional-altitude views and visually resembles real Kuujjuaq shield terrain far more closely than the stock generic material.

The best next move is therefore not more bedrock tuning.

It is to **work the remaining classes forward to the same point and then judge the landscape as a unified whole.**
