# Nunavik / Ullaaq Scenery Project State

**Checkpoint date:** 2026-08-29  
**Current tile:** `+58-069` (Kuujjuaq)  
**Session result:** The custom terrain-material pipeline is now proven end-to-end with real Nunavik orthophotography. A raw 30 cm Québec source patch, downsampled at the exact physical scale of Laminar's stock rocky-tundra material, rendered successfully in X-Plane and already looks materially better than the stock generic rock. The next problem is no longer pipeline engineering; it is texture authoring, especially seamless tiling, signature-feature suppression, and controlled tonal/color treatment.

---

## Executive status

The full scenery stack remains proven and stable enough for authoring:

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

Current authoring order remains:

```text
1. wild ecological classes
2. urban agglomerations / settlements
3. custom .obj modeling as settlement work demands it
4. airports last
```

Geometry, hydro and mesh are frozen unless a concrete downstream problem requires revisiting them.

The important new transition is:

```text
pipeline validation -> COMPLETE ENOUGH
material archaeology -> COMPLETE ENOUGH
real terrain authoring -> NOW ACTIVE
```

---

# Major result of 2026-08-29: real Nunavik texture pipeline PROVEN

The day's decisive proof was for the VEG_NORD **rocky tundra** bucket, class `5`.

Current semantic mapping in:

```text
~/linGames/Ortho4XP/src/O4_DSF_Utils.py
```

was changed from:

```python
5: "lib/g10/terrain10/rock_pol_sdry_sflat.ter",     # rocky tundra
```

to:

```python
5: "lib/ullaaq/terrain/rock_test.ter",              # rocky tundra
```

This routes the existing VEG_NORD class geometry to a custom Ullaaq terrain resource without changing mesh geometry or ecological semantics.

The in-sim result is unambiguous: raw, real Kuujjuaq-area aerial imagery already reads more convincingly as Canadian Shield rock/tundra than the stock Laminar material.

The pipeline is therefore proven:

```text
Québec orthophoto
    -> physical-scale source crop
    -> downsample to Laminar macro scale
    -> custom Ullaaq texture
    -> custom .ter
    -> library export
    -> Ortho4XP class routing
    -> Step 3 DSF
    -> X-Plane renderer
```

---

# Québec orthophoto source discovery

## Index dataset

Local root:

```text
~/linGames/GIS/Canada/Quebec/Orthophoto
```

Downloaded index:

```text
Index_Imagerie_orthorectifiee.gpkg
```

Layers:

```text
Index_Orthomosaique
Index_Orthophotographie
```

The index contains, among other fields:

```text
NOM_FICHIER
TELECHARGEMENT_FICHIER
DATE_ACQUISITION
HEURE_GMT
SAISON
RESOLUTION_METRE
FORMAT
COULEUR
BITS_PIXEL
CAMERA
TYPE_CAMERA
PROJET
PLUS_RECENTE
```

Visual inspection of the index in QGIS is now the preferred discovery method. The overwhelming majority of Québec's high-resolution aerial coverage is in the south, while about **16 Nunavik settlements** have discrete high-resolution coverage islands, including Kuujjuaq.

Important Kuujjuaq coverage pattern:

```text
15 cm imagery -> concentrated around the town / built-up area
30 cm imagery -> much broader surrounding wild-terrain coverage
```

This is a very useful division of labor:

```text
15 cm town imagery
    -> future roads, gravel lots, disturbed ground, roofs, yards, settlement reference

30 cm regional imagery
    -> current bare-rock, tundra, heath and other wild-ground texture authoring
```

The broader 30 cm imagery is therefore the current texture quarry.

---

## Kuujjuaq 30 cm project

The index census exposed:

```text
RESOLUTION_METRE = 0.30
COULEUR           = Couleur naturelle
PROJET            = 2010_VillagesNordiques_30cm
```

A representative downloaded frame used today:

```text
Q10805_067_30CM_F06.TIF
```

Path:

```text
~/linGames/GIS/Canada/Quebec/Orthophoto/Q10805_067_30CM_F06.TIF
```

`gdalinfo`:

```text
Size:        6471 x 9528 px
Pixel Size:  0.300000 m
Bands:       RGB Byte
CRS:         NAD83(CSRS) / MTM zone 6
EPSG:        2948
```

Ground dimensions are approximately:

```text
6471 * 0.30 ~= 1941 m
9528 * 0.30 ~= 2858 m
```

The imagery is visually excellent for the task: real fractured shield structure, subdued grey/beige rock, brown/green lichen and tundra, narrow dark vegetated seams, and small ponds/depressions.

A warm/red cast is visible in parts of the source. This may reflect the source overflight illumination and/or survey color processing. Do **not** bake in aggressive color correction until texture tiling and neutral comparison are under control.

---

# Stock rocky-tundra material anatomy

Stock terrain definition:

```text
~/linGames/X-Plane 12/Resources/default scenery/1000 world terrain/terrain10/rock_pol_sdry_sflat.ter
```

Inspected with:

```text
tools/inspect_xplane_terrain.py
```

Key recipe:

```text
BASE_TEX
    ../textures10/soil/rock_pol_wet_sflat_d.dds
    1024 x 1024

PROJECTED
    1248 x 1248 m

BORDER_TEX
    ../textures10/border/hard.png

SUPER_ROUGHNESS
    0.5

AUTO_HEADING
NO_ALPHA
COMPOSITE_BORDERS

DECAL_LIB
    lib/g10/decals/rail_ballast_dry.dcl
```

Important finding:

> This stock rock material has **no `COMPOSITE_TEX`, no `COMPOSITE_NOISE`, and no `COMPOSITE_PARAMS`**.

It is much simpler than the conifer/tundra specimens studied earlier. For this class, Laminar effectively uses one kilometre-scale macro image plus a close-range decal.

The stock macro physical scale is:

```text
1248 m / 1024 px = 1.21875 m/px
```

The 30 cm Québec imagery therefore maps perfectly to the same physical footprint with a:

```text
4160 x 4160 px source crop
```

because:

```text
4160 * 0.30 m = 1248 m
```

This exact scale match is a major convenience.

---

# First real source crop

Material-lab directory:

```text
~/linGames/Ullaaq-Air-Nunavik/work/material-lab/rock
```

Source frame:

```text
Q10805_067_30CM_F06.TIF
```

Exact first quarry crop:

```bash
gdal_translate \
  -srcwin 1155 2684 4160 4160 \
  "$SRC" \
  "$LAB/rock_qc_A_source_4160.tif"
```

This is exactly:

```text
4160 x 4160 px
0.30 m/px
1248 x 1248 m on the ground
```

It was then downsampled to Laminar's 1024² macro size with:

```bash
gdal_translate \
  -of PNG \
  -outsize 1024 1024 \
  -r average \
  "$LAB/rock_qc_A_source_4160.tif" \
  "$LAB/rock_qc_A_1024.png"
```

Result:

```text
rock_qc_A_1024.png
1024 x 1024
8-bit sRGB
```

The stock comparison PNG is:

```text
stock_rock_pol_wet_sflat_d.png
1024 x 1024
8-bit sRGB
```

Both are clean RGB images with no format mismatch.

The raw Québec source was intentionally left **unprocessed** for the first in-sim test.

No:

```text
seam fixing
pond removal
signature-feature removal
color grading
contrast tuning
manual sharpening
```

was performed before the proof.

This preserves a clean control specimen.

---

# Custom rock resource

Custom texture installed under:

```text
scenery/Ullaaq_Nunavik_Resources/textures/rock/rock_qc_A_1024.png
```

Stock hard border copied locally under:

```text
scenery/Ullaaq_Nunavik_Resources/textures/shared/hard.png
```

Custom terrain definition:

```text
scenery/Ullaaq_Nunavik_Resources/terrain/ullaaq_rock_test.ter
```

It is a copy of Laminar's stock `rock_pol_sdry_sflat.ter` with only the macro and local border texture paths changed.

Expected key lines:

```text
BASE_TEX ../textures/rock/rock_qc_A_1024.png
BORDER_TEX ../textures/shared/hard.png
PROJECTED 1248 1248
SUPER_ROUGHNESS 0.5
DECAL_LIB lib/g10/decals/rail_ballast_dry.dcl
```

Library export:

```text
EXPORT lib/ullaaq/terrain/rock_test.ter terrain/ullaaq_rock_test.ter
```

Virtual resource:

```text
lib/ullaaq/terrain/rock_test.ter
```

This is now routed to VEG_NORD class `5` / rocky tundra.

---

# Runtime result of first raw-rock test

The result already beats the stock material in the problem areas that motivated the experiment.

Observed improvement:

```text
stock rock
    -> high-contrast pale/white generic motifs
    -> obvious repeated visual fingerprints
    -> reads partly as snow-confetti / generic alpine rock

raw Québec replacement
    -> coherent Canadian Shield fracture structure
    -> long geological grain
    -> dark lichen/vegetation seams
    -> restrained highlights
    -> much less arbitrary white patterning
    -> reads as actual exposed shield terrain
```

The visual improvement is already present **before any artistic processing**.

This proves that authentic Nunavik source structure survives the 30 cm -> 1.22 m/px reduction well enough to work as X-Plane macro terrain.

---

# Current visual defects: these are now authoring problems, not pipeline failures

## 1. Tiling / seam artifacts

The current raw crop is not seamless.

Visible rectangular/repeating artifacts now appear inside the larger class-5 polygons.

This is the main task for the next session.

Important nuance:

```text
VEG_NORD polygons are often dense/small
    -> polygon boundaries naturally interrupt or obscure some repetition

large rocky-tundra polygons
    -> texture repeats remain visible
    -> hard edge / signature-pattern artifacts become obvious
```

Therefore dense semantic polygons help, but they do **not** remove the need for a properly seamless macro texture.

The latest runtime frame clearly exposes the problem in a larger rocky area.

---

## 2. Signature features

The raw 1248 m source patch includes real-world features that may become recognizable when repeated:

```text
small ponds
large dark seams
distinctive fracture geometry
isolated strong tonal blobs
```

Some of these survive downsampling and can become repetition fingerprints.

Do not sterilize all geological structure. The goal is to remove only the features that announce the tile boundary or make exact repeats obvious.

---

## 3. Tonal/color mismatch

The raw Québec source is generally:

```text
darker
warmer / somewhat red-brown
more photographic
```

than neighboring stock Laminar classes.

Do not simply force it to match the stock rock artwork. The stock visual vocabulary is part of the problem.

Longer-term, neighboring tundra classes should likely move toward the same real-photographic Nunavik vocabulary.

For the immediate rock pass, color work should be modest and controlled:

```text
raise mids if needed
reduce excessive warm/red cast if still present after neutral comparison
compress only problematic extremes
preserve natural subdued rock/lichen palette
```

---

## 4. Stock decal remains active

The custom rock test intentionally retains:

```text
DECAL_LIB lib/g10/decals/rail_ballast_dry.dcl
```

This is a suspiciously generic close-range choice for Canadian Shield bedrock, but it was deliberately held constant so that the first proof changed only the macro artwork.

Do **not** tune the decal at the same time as the first seamless-macro pass.

Possible later A/B:

```text
same processed macro texture
    + stock rail_ballast_dry.dcl
vs
same processed macro texture
    + decal disabled or replaced
```

One variable at a time.

---

# Tomorrow's immediate plan: 2026-08-30

Primary goal:

> **Gain deliberate control over the rock macro texture and make it tile cleanly without destroying the real Nunavik geological vocabulary.**

Recommended sequence:

```text
1. Preserve rock_qc_A_1024.png as immutable raw control.

2. Create a working copy for seamless-tile authoring.

3. In GIMP, use offset/wrap inspection so the true tile seams move to the center.

4. Heal/clone only the seam and strongest repetition fingerprints.

5. Keep broad geological grain and tonal distribution intact.

6. Make a gentle first tonal/color pass only if needed.

7. Export processed 1024² RGB texture.

8. Swap only BASE_TEX in ullaaq_rock_test.ter.

9. Re-run Step 3 only for +58-069.

10. Compare raw control vs processed version from the same fixed X-Plane view.

11. Inspect large class-5 polygons specifically; small dense polygons are not a sufficient tiling test.
```

A useful first processed filename would be something like:

```text
rock_qc_A_seam_v1.png
```

Do not overwrite:

```text
rock_qc_A_1024.png
```

That raw texture is now the control for all subsequent authoring comparisons.

---

# Secondary texture-authoring direction

Once bare rock is under control, likely order is:

```text
1. bedrock / rocky tundra      <- current
2. bare mineral / scree
3. rock + heath transition
4. open heath / tundra
5. lower/shrub tundra
6. wet/boggy surfaces
7. forest ground later
```

Forest ground is not urgent because:
- the current forest texture is acceptable;
- VEG_NORD-driven `.for` autogen will increasingly cover the forest macro surface;
- bare/open ground remains fully exposed and therefore benefits most from better base material.

The design strategy is intentionally to cut our teeth on the worst/most exposed elements first.

---

# Settlement imagery direction

The 15 cm Kuujjuaq town imagery was also visually inspected today and is very high quality.

It will be valuable later for:

```text
road and shoulder color
compacted gravel
parking / storage yards
disturbed ground
roof colors
building footprints / spacing
service areas
small local material reference
```

Do not divert into town authoring yet. Save this source advantage for the settlement phase.

---

# Composite-material investigation: enough learned, now parked

The previous RcmL conifer material lab was continued today with controlled cyan/magenta diagnostics.

The stock-style RcmL recipe was:

```text
BASE_TEX ../textures/hiveg/coni_cld_dry_flat_c.dds
PROJECTED 1673 1673
COMPOSITE_TEX ../textures/hiveg/coni_cld_dry_flat_c2.dds
COMPOSITE_PROJECTED 1673 1673
COMPOSITE_PARAMS 0.104000 0.850000 0.248000 1.820000 2.050000 0.260000
COMPOSITE_NOISE ../textures/shared/natnoise.png
DECAL_LIB lib/g10/decals/maquify_1_alpha_key.dcl
```

This natural configuration was restored after the diagnostics.

## Important empirical compositor results

Using exact 8-bit constant noise values under stock parameters:

```text
166 -> BASE / cyan
167 -> intermediate
168 -> intermediate
169 -> COMPOSITE / magenta
```

Therefore the transfer from noise value to BASE/COMPOSITE is continuous but very steep around this range.

A four-band `166 | 167 | 168 | 169` diagnostic texture and a full grayscale ramp proved that `COMPOSITE_NOISE` is sampled spatially and projected/repeated over the terrain independently of VEG_NORD polygon geometry.

Practical parameter behavior found:

```text
p1
    lower  -> narrower/harder value transition
    higher -> wider/softer value transition
    practical role: transfer width / softness

p2
    lower  -> probe window driven toward COMPOSITE
    higher -> probe window driven toward BASE
    practical role: transfer bias / position-like control

p3
    lower  -> broader/fewer spatial noise bands
    higher -> narrower/more frequent spatial bands
    practical role: noise spatial frequency / inverse ground scale

p4
    higher -> broader spatial feathering across hard source-noise boundaries
    practical role: spatial filtering / feathering width

p5
    constant-noise 168 clean test:
      0.500 -> BASE / cyan
      2.050 -> intermediate lavender
      4.000 -> COMPOSITE / magenta
    practical role: transfer-function control; exact shader math unresolved

p6
    constant-noise 168:
      stock 0.260 -> intermediate lavender
      0.600 -> COMPOSITE / magenta
    practical role: transfer-function control; exact shader math unresolved
```

Do not overclaim exact mathematical names for p5/p6. The practical behavior is enough for authoring.

Key methodological lesson:

> Ramp/striped noise is good for spatial behavior; constant noise is required to separate spatial sampling from value-transfer behavior.

The six-number compositor is now understood well enough that we do **not** need to spend more authoring time reverse-engineering it unless a future material specifically requires it.

Laminar appears to reuse a small number of known-good presets across hundreds of terrain definitions. Reuse a stock natural preset unless there is a concrete reason not to.

---

# RcmL state after diagnostics

`ullaaq_rcml_test.ter` was restored to the natural conifer pair:

```text
BASE_TEX ../textures/hiveg/coni_cld_dry_flat_c.dds
PROJECTED 1673 1673
COMPOSITE_TEX ../textures/hiveg/coni_cld_dry_flat_c2.dds
COMPOSITE_PROJECTED 1673 1673
COMPOSITE_PARAMS 0.104000 0.850000 0.248000 1.820000 2.050000 0.260000
COMPOSITE_NOISE ../textures/shared/natnoise.png
DECAL_LIB lib/g10/decals/maquify_1_alpha_key.dcl
```

The fluorescent cyan/magenta diagnostic textures remain useful lab assets but are no longer the intended runtime RcmL state.

---

# Production ecology taxonomy remains

VEG_NORD semantics remain authoritative.

Broad families:

### Taiga

```text
RaL
RcD
RcL
RcmD
RcmL
RmC
RmD
RmL
```

### Tundra / shrub / heath

```text
AAB
AAH
AB
AH
LS
LSA
TD
TDA
```

### Rock / mineral mosaics

```text
LSR
RLS
TDR
RTD
AR
SD
```

### Wet / boggy

```text
MS
TAA
TAR
TMS
TMU
TOP
```

Special/non-wild:

```text
EAU -> NHN owns actual water geometry
IH  -> settlement/human-landscape authoring
ILE -> bookkeeping / infer later
```

Working 13-recipe visual vocabulary remains:

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

Mixed classes should ultimately reuse a smaller library of material ingredients rather than each becoming a completely unrelated texture family.

---

# Proven vegetation / human-layer results remain unchanged

## VEG_NORD-driven `.for`

RcmL forest overlay proof remains valid:

```text
source features: 1,439
forest polygons: 1,453
windings:        1,516
density:         160 / 255
```

Generator:

```text
tools/make_rcml_forest_overlay.py
```

Runtime proved independent ecological ground material + `.for` tree placement.

## Roads

Stock road geometry extraction and custom visible-surface control remain proven.

Production architecture remains:

```text
road centerlines
      |\
      | -> buffered / unioned draped polygon surfaces
      |
      -> optional .net traffic skeleton later
```

## Settlement ground / `.obj`

Broad settlement ground treatment and direct `.obj` placement remain proven. Production towns should be modular/hand-curated rather than restored stock suburban autogen.

---

# Important current paths

## Project

```text
~/linGames/Ullaaq-Air-Nunavik
```

## Current tile

```text
~/linGames/Ullaaq-Air-Nunavik/work/+58-069
```

## Material lab

```text
~/linGames/Ullaaq-Air-Nunavik/work/material-lab
~/linGames/Ullaaq-Air-Nunavik/work/material-lab/rock
```

## Québec imagery

```text
~/linGames/GIS/Canada/Quebec/Orthophoto
~/linGames/GIS/Canada/Quebec/Orthophoto/Index_Imagerie_orthorectifiee.gpkg
~/linGames/GIS/Canada/Quebec/Orthophoto/Q10805_067_30CM_F06.TIF
```

## Rock lab assets

```text
work/material-lab/rock/rock_qc_A_source_4160.tif
work/material-lab/rock/rock_qc_A_1024.png
work/material-lab/rock/stock_rock_pol_wet_sflat_d.png
```

## Custom resource package

```text
~/linGames/Ullaaq-Air-Nunavik/scenery/Ullaaq_Nunavik_Resources
```

## Custom rock terrain

```text
~/linGames/Ullaaq-Air-Nunavik/scenery/Ullaaq_Nunavik_Resources/terrain/ullaaq_rock_test.ter
```

## Custom rock texture

```text
~/linGames/Ullaaq-Air-Nunavik/scenery/Ullaaq_Nunavik_Resources/textures/rock/rock_qc_A_1024.png
```

## Custom RcmL terrain

```text
~/linGames/Ullaaq-Air-Nunavik/scenery/Ullaaq_Nunavik_Resources/terrain/ullaaq_rcml_test.ter
```

## Ortho4XP semantic patch

```text
~/linGames/Ortho4XP/src/O4_DSF_Utils.py
```

## Canonical VEG_NORD tile

```text
~/linGames/Ullaaq-Air-Nunavik/work/+58-069/landcover/+58-069_VEG_NORD_tile.gpkg
layer: veg_nord
features: 16,227
```

## NHN water

```text
/home/mike/linGames/X-Plane 12/Development/GIS/Canada/NHN/tiles/+58-069/+58-069_NHN_water_final.gpkg
```

## Stock rock `.ter`

```text
~/linGames/X-Plane 12/Resources/default scenery/1000 world terrain/terrain10/rock_pol_sdry_sflat.ter
```

## Terrain inspector

```text
~/linGames/Ullaaq-Air-Nunavik/tools/inspect_xplane_terrain.py
```

---

# Shell setup reminder for Ortho4XP work

Typical project variables used in the current workflow:

```bash
export ULLAAQ_LANDCOVER_GPKG="$HOME/linGames/Ullaaq-Air-Nunavik/work/+58-069/landcover/+58-069_VEG_NORD_tile.gpkg"
export ULLAAQ_VEGNORD_GPKG="$ULLAAQ_LANDCOVER_GPKG"
export ULLAAQ_NHN_WATER_GPKG="$HOME/linGames/X-Plane 12/Development/GIS/Canada/NHN/tiles/+58-069/+58-069_NHN_water_final.gpkg"
```

The current texture-only iteration generally requires **Step 3 only** after changing the terrain mapping or texture resource. No need to rerun Step 1/mesh when geometry is unchanged.

---

# Do not redo / do not regress

Do **not**:

```text
reopen raster-derived landcover topology work
resimplify or smooth VEG_NORD geometry without a demonstrated need
redo hydro geometry
redo the replacement mesh for texture-only changes
restore stock suburban Kuujjuaq autogen
assume every ecology needs a bespoke six-parameter compositor recipe
spend more time decoding p5/p6 without a concrete authoring problem
color-grade the raw orthophoto so aggressively that it merely imitates the flawed stock palette
overwrite the raw rock_qc_A_1024.png control texture
```

The engineering stack is not the problem now. The current problem is visual material design.

---

# Resume point

Tomorrow, begin here:

```text
1. Open:
   work/material-lab/rock/rock_qc_A_1024.png

2. Preserve it untouched as the raw control.

3. Make a working seamless-tile copy.

4. Offset/wrap by half-width and half-height in GIMP.

5. Remove the seam and strongest signature features while preserving real shield structure.

6. Export a v1 processed tile.

7. Replace only BASE_TEX target texture.

8. Re-run Ortho4XP Step 3 only.

9. Test from the same large rocky-tundra area where rectangular repeats are currently visible.

10. Compare raw vs processed before touching the decal.
```

The key fact to carry forward is:

> **Real 30 cm Québec orthophotography, downsampled to the stock 1248 m / 1024 px macro scale, already works in X-Plane. The next job is to make it behave like authored repeating terrain rather than a repeated aerial photograph.**
