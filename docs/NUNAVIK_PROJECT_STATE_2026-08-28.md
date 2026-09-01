# Nunavik / Ullaaq Scenery Project State

**Checkpoint date:** 2026-08-28  
**Current tile:** `+58-069` (Kuujjuaq)  
**Session result:** Full scenery stack declared proven. The project has moved out of pipeline-validation mode and into authoring/design. Immediate design focus is wild ecological terrain. A material-lab workflow is now being built by reverse-engineering XP12 `.ter` behavior with controlled cyan/magenta diagnostics.

---

## Executive status

The engineering stack is now proven far enough to begin scenery authoring.

Current architecture:

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

The user explicitly called the stack proved on 2026-08-28.

The planned authoring order is now:

```text
1. wild ecological classes
2. urban agglomerations / settlements
3. custom .obj modeling as settlement work demands it
4. airports last
```

This ordering gives the biggest regional visual payoff first. There are only 14 settlements in the intended Nunavik scope, so settlement scenery can be heavily hand-curated once the wild landscape is working.

Geometry/hydro remain frozen unless a concrete downstream problem demonstrates a need to revisit them.

---

## Authoritative base-mesh stack remains unchanged

Production doctrine remains:

> **NHN tells us where the water is. VEG_NORD tells us what the land is. MRDEM tells us what shape the land has.**

Current authoritative sources:

```text
MRDEM
    terrain elevation / landform

NHN / HNET Bank
    water / shoreline authority

VEG_NORD
    terrestrial polygon geometry
    cl_carto ecological semantics

Ortho4XP
    constrained mesh and DSF construction
```

Native VEG_NORD geometry remains unsimplified and unsmoothed in production. The retired NALCMS raster-topology workflow should not be revived unless a new requirement specifically calls for it.

Known-good replacement mesh remains stable in X-Plane from low altitude through high cruise altitude.

---

# Full-stack validation completed

## 1. Custom `.ter` path: PROVEN

A Git-controlled resource package now exists at:

```text
~/linGames/Ullaaq-Air-Nunavik/scenery/Ullaaq_Nunavik_Resources
```

Active X-Plane symlink:

```text
~/linGames/X-Plane 12/Custom Scenery/Ullaaq_Nunavik_Resources
    -> ~/linGames/Ullaaq-Air-Nunavik/scenery/Ullaaq_Nunavik_Resources
```

Key terrain resource:

```text
scenery/Ullaaq_Nunavik_Resources/terrain/ullaaq_rcml_test.ter
```

Virtual library export:

```text
EXPORT lib/ullaaq/terrain/rcml_test.ter terrain/ullaaq_rcml_test.ter
```

`RcmL` is still semantically classed as the existing forest/taiga bucket, but Step 3 contains an exact source-code override that routes only `RcmL` to:

```text
lib/ullaaq/terrain/rcml_test.ter
```

The custom path has been proven repeatedly with extreme diagnostic textures:

```text
BASE_TEX       -> solid cyan test texture
COMPOSITE_TEX  -> solid magenta test texture
```

At runtime, the expected organic `RcmL` polygons become cyan/magenta while neighboring classes remain stock terrain. This proves:

```text
VEG_NORD source code
    -> semantic lookup
    -> exact RcmL terrain override
    -> custom library namespace
    -> custom .ter
    -> custom textures
    -> X-Plane renderer
```

### Current Ortho4XP semantic patch

Patch target:

```text
~/linGames/Ortho4XP/src/O4_DSF_Utils.py
```

Custom terrain constant:

```python
ULLAAQ_RCML_TERRAIN_DEF = "lib/ullaaq/terrain/rcml_test.ter"
```

Triangle assignment conceptually remains:

```python
if source_code == "RcmL":
    terrain_idx = ullaaq_rcml_terrain_idx
else:
    terrain_idx = ullaaq_class_to_terrain_idx[class_id]
```

The semantic source code remains intact; rendering is overridden separately.

---

## 2. VEG_NORD-driven `.for` vegetation: PROVEN

`RcmL` was used as the forest proof class.

Source filter result:

```text
cl_carto = RcmL
source features: 1,439
```

Extracted source:

```text
work/+58-069/forest/rcml.geojson
```

Generator:

```text
tools/make_rcml_forest_overlay.py
```

Generated DSF2TEXT:

```text
work/+58-069/forest/+58-069_rcml_forests.txt
```

Proof statistics:

```text
forest polygons: 1,453
windings:        1,516
density:         160 / 255
```

Forest resource used for the proof:

```text
lib/vegetation/forests/conifers/cold_low.for
```

Compiled overlay:

```text
scenery/Ullaaq_Nunavik_Vegetation/Earth nav data/+50-070/+58-069.dsf
```

Runtime result:
- dense conifers appeared only inside the organic `RcmL` polygons;
- holes/open areas were respected;
- ground terrain and 3D vegetation are now proven as independent ecological layers.

The wild-ecology stack is therefore:

```text
VEG_NORD class
      |\
      | -> base mesh -> .ter ground material
      |
      -> overlay   -> .for vegetation
```

`cl_dens` and richer VEG_NORD fields remain available for later production density/species rules. The proof intentionally used a flat density.

---

## 3. Roads: geometry and visible surface control PROVEN

Stock Global Scenery tile was successfully restored and decompiled:

```text
~/linGames/X-Plane 12/Global Scenery/X-Plane 12 Global Scenery/Earth nav data/+50-070/+58-069.dsf
```

Decompiled text:

```text
work/+58-069/stock-overlay/+58-069_stock.txt
```

Important finding: the stock Kuujjuaq “Beltway, Maryland” appearance was primarily produced by stock industrial autogen plus broad dark paved roads. The stock urban `.ags` should not be restored as production scenery.

Stock tile contains:

```text
275 BEGIN_SEGMENT road segments
```

Road extraction tool:

```text
tools/extract_stock_roads.py
```

Road-only DSF2TEXT:

```text
work/+58-069/stock-overlay/+58-069_roads_only.txt
```

The stock subtype used here resolves through `lib/g10/roads.net` to broad asphalt residential road artwork with streetlights and vehicle rules. This directly explains the inappropriate suburban look.

A custom Ullaaq `.net` was then proven. A minimal gravel road definition produced visibly narrower, light-colored roads. `SEGMENT_DRAPED` fixed the initial close-range disappearance problem.

The minimal `.net` did not provide good junction artwork, producing wedges/gaps/caps at intersections. The resulting architectural decision is:

```text
road centerlines
      |\
      | -> buffered / unioned draped polygon surfaces
      |
      -> .net network retained as possible future traffic skeleton
```

Traffic is not a current priority, but preserving a network gives us a future path to sparse, pickup-dominated circulation without forcing stock road surfaces.

### Road surface geometry proof

Stock road segments were parsed to centerlines, projected into UTM zone 19N, buffered by 3.5 m, and unioned using GDAL/OGR.

Result:

```text
Layer: road_surface
Geometry: Polygon
Feature Count: 1
CRS: EPSG:32619
Extent:
  518252.301100, 6430105.703426
  539119.843227, 6467817.501198
```

The single polygon is expected: intersecting streets fuse into one continuous draped road surface, solving `.net` junction gaps geometrically.

Runtime tests established that road geometry and visible road treatment are under Ullaaq control.

---

## 4. Settlement ground / urban layer: proof achieved

A broad draped ground-treatment experiment under the Kuujjuaq road network rendered successfully. It is not final art and does not perfectly match all roads or recent development, but that mismatch is understood as a source-data/date artifact rather than a pipeline failure.

The important engineering result is that human-landscape ground treatment can be layered independently from the wild base mesh and from the road network.

Real-world reference confirms that Kuujjuaq contains a mixture of paved and unpaved streets, rather than the earlier assumption that essentially all streets were gravel. Production road classes can therefore distinguish at least:

```text
paved streets
compacted gravel streets
service tracks / access roads
airport pavement handled separately
```

---

## 5. Individual `.obj` placement: PROVEN

Stock X-Plane object resources were inspected for temporary building stand-ins.

Useful stock airport library object:

```text
lib/airport/Common_Elements/Miscellaneous/const_trailer_white.obj
```

Physical source:

```text
Resources/default scenery/airport scenery/
Common_Elements/Miscellaneous/const_trailer_1.obj
```

Additional stock variants:

```text
const_trailer_green.obj
const_trailer_rusty.obj
```

Multiple trailer objects were successfully placed in the Kuujjuaq scene, proving direct object placement.

This changed the settlement strategy: stock “autogen” is not the desired rubric. The preferred architecture is explicit/procedural object placement from real settlement structure.

---

# Settlement authoring strategy

Nunavik housing has a strong shared design language across communities: modular/prefabricated northern buildings, likely produced by a small number of southern suppliers and delivered by sealift.

Common visual traits observed in Street View/reference imagery:
- simple rectangular modular volumes;
- shallow gable roofs or simple flat/low-slope institutional masses;
- buildings elevated above ground rather than conventional landscaped foundations;
- smooth/light lower siding with more colorful/textured gable or upper treatment;
- recurring window/door proportions;
- exterior stairs/porches;
- repeated HVAC/service details;
- extremely limited conventional lawn treatment, but natural vegetation persists between buildings.

This is ideal for a modular object kit.

Conceptual residential authoring model:

```text
small set of base meshes
    + footprint length / width
    + roof pitch
    + single/double module
    + lower siding color
    + upper/gable siding color/texture
    + window pattern
    + door position
    + stairs / porch
    + foundation height
    + service attachments
    -> dozens of credible house variants
```

Each community will also contain one or more distinctive civic/institutional structures. Those should be modeled explicitly where they are visually important.

Practical town hierarchy:

```text
ordinary housing fabric
    -> modular/procedural kit

repeated civic/institutional types
    -> semi-custom regional kit

true landmarks
    -> custom .obj models
```

Because the scope is only 14 small settlements, heavy hand-curation is affordable and preferred over generic autogen.

The Québec northern-village photogrammetric/topographic dataset remains particularly interesting for this later phase because it can provide surveyed building/road/infrastructure structure. It is not required for the current wild-terrain work.

---

# Wild-land authoring taxonomy

VEG_NORD keeps all of its semantic classes. The design layer groups them into a much smaller set of reusable visual materials and modifiers.

## Four broad landscape families

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

Special/non-wild codes:

```text
EAU  -> NHN owns actual water geometry
IH   -> settlement/human-landscape authoring
ILE  -> bookkeeping/infer appropriate ecology later
```

## Working 13-recipe visual vocabulary

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

The class code remains authoritative semantics. The 13 recipes are a rendering vocabulary, not a replacement ecological classification.

Likely modifiers include:

```text
tree density
shrub density / stature
rock exposure
wetland structure
lichen / moss / heath balance
```

A key design principle is that mixed classes such as heath+rock should eventually be rendered as mixtures of reusable material ingredients rather than as unrelated “paint bucket” textures.

---

# Material-lab work started

The current challenge is to author custom terrain without spending weeks in blind X-Plane trial-and-error.

The working loop is becoming:

```text
real imagery / reference
        -> inspect source at multiple physical scales
        -> author macro texture pair
        -> author close-range decal
        -> diagnostic material test in XP12
        -> production ecology
```

High-resolution Québec aerial/orthophoto data may become important source material for direct texture authoring. The likely use is not naive tiled orthophoto, but texture synthesis and scale separation from real Nunavik surfaces.

---

## Terrain inspector tool

Created:

```text
tools/inspect_xplane_terrain.py
```

The tool:
- parses a `.ter`;
- resolves relative image dependencies;
- builds an index of XP12 `library.txt` exports;
- resolves `DECAL_LIB` virtual paths;
- follows `.dcl` files;
- calls ImageMagick `identify` on contributing images;
- exposes projection scales and shader parameters.

ImageMagick 7 reads Laminar DDS files directly, so the material lab does not require a separate DDS-conversion stage for inspection.

Known cosmetic issue: format-version lines (`800`, `1000`) are still printed as pseudo-directives. Harmless; clean up later.

Material-lab working directory:

```text
work/material-lab
```

---

# Stock `.ter` anatomy learned so far

## Conifer specimen

Stock source:

```text
terrain10/coni_vcld_sdry_fl.ter
```

Recipe:

```text
BASE_TEX
  coni_cld_dry_flat_c.dds
  1024 x 1024

PROJECTED
  1673 x 1673 m
  ~1.63 m/px

COMPOSITE_TEX
  coni_cld_dry_flat_c2.dds
  1024 x 1024

COMPOSITE_PROJECTED
  1673 x 1673 m

COMPOSITE_PARAMS
  0.104000 0.850000 0.248000 1.820000 2.050000 0.260000

COMPOSITE_NOISE
  natnoise.png

DECAL_LIB
  lib/g10/decals/maquify_1_alpha_key.dcl

DECAL texture
  RGBA_DECAL_shrub_dirt_sdry3.png

DECAL projection
  30 x 30 m
```

BASE/COMPOSITE comparison:

```text
RGB RMSE:   0.229353
Alpha RMSE: 0
```

Thus the two macro RGB realizations differ substantially numerically but share exactly the same alpha channel.

The two macro images are visually very similar by design. They appear to be two realizations of the same ecological material, allowing variation without changing the terrain's identity.

---

## Tundra specimen

Stock source:

```text
terrain10/tun_sp_cld_sdry_fl.ter
```

Recipe:

```text
BASE_TEX
  tund_sp_cld_sdry_flat_c.dds
  2048 x 2048

PROJECTED
  2456 x 2456 m
  ~1.20 m/px

COMPOSITE_TEX
  tund_sp_cld_sdry_flat_c2.dds
  2048 x 2048

COMPOSITE_PROJECTED
  2456 x 2456 m

COMPOSITE_PARAMS
  0.104000 0.850000 0.248000 1.820000 2.050000 0.260000

COMPOSITE_NOISE
  natnoise.png

DECAL_LIB
  lib/g10/decals/grass_and_stony_dirt_1.dcl

DECAL texture
  RGBA_DECAL_grass+stony_dirt.png

DECAL projection
  9 x 9 m
```

BASE/COMPOSITE comparison:

```text
RGB RMSE:   0.215908
Alpha RMSE: 0
```

Again, BASE and COMPOSITE are visually related macro realizations with exactly identical alpha.

The tundra decal packs a colored green/vegetation detail in RGB and a gray stony detail in alpha. The decal coefficients use source-color relationships to decide where those close-range details appear.

---

# Composite-noise corpus analysis

Stock XP12 terrain corpus contains only a tiny set of recurring `COMPOSITE_NOISE + COMPOSITE_PARAMS` recipes.

Across 1,816 terrain definitions:

```text
484  fornoise.png  0.104000 0.850000 0.248000 1.820000 2.050000 0.260000
454  natnoise.png  0.104000 0.850000 0.248000 1.820000 2.050000 0.260000
320  crpnoise.png  0.144000 0.525000 0.362000 1.820000 2.050000 0.260000
232  natnoise.png  0.104000 0.850000 0.292000 4.920000 2.050000 0.260000
175  fornoise.png  0.104000 0.850000 0.292000 1.820000 2.050000 0.260000
147  frcnoise.png  0.350000 0.030000 0.070000 3.700000 0.400000 0.700000
  4  natnoise.png  0.104000 0.850000 0.292000 1.820000 2.050000 0.260000
```

Interpretation at current confidence:

```text
natnoise  -> general natural organic variation
fornoise  -> harder/patchier organic natural variation
crpnoise  -> crop/irrigated-crop variation
frcnoise  -> urban fabric variation
```

`frcnoise` is strongly paired with the urban parameter preset. `crpnoise` is strongly paired with crop terrain. Natural terrain overwhelmingly uses the standard `natnoise` or `fornoise` preset.

This strongly suggests Laminar uses a few generic variation grammars rather than hand-tuning every terrain shader.

---

## Composite noise image anatomy

Known shared texture root:

```text
Resources/default scenery/1000 world terrain/textures10/shared
```

Noise files inspected:

```text
natnoise.png   1024x1024 GrayscaleAlpha
fornoise.png   1024x1024 GrayscaleAlpha
crpnoise.png   2048x2048 GrayscaleAlpha
frcnoise.png   1024x1024 Grayscale
```

Alpha in `natnoise`, `fornoise`, and `crpnoise` is effectively opaque baggage rather than a meaningful second noise channel.

Example `natnoise` alpha statistics:

```text
min    0.964706
max    1
mean   0.999666
stddev 0.002319
```

The useful content is the grayscale field.

`crpnoise` consists of four closely related, not identical, 1024² quadrants. Quadrant RMSE against the first is about 0.034, suggesting deliberate near-variants for repetition reduction.

---

# Major compositor breakthrough: cyan/magenta diagnostic

The natural source textures were too visually similar to expose the composite machinery clearly. The existing diagnostic textures solved this.

Current diagnostic concept:

```text
BASE_TEX       -> cyan
COMPOSITE_TEX  -> magenta
```

This makes the compositor visible directly in-engine.

Observed with fully settled soft reloads:

```text
COMPOSITE_NOISE = natnoise
    -> large irregular cyan and magenta domains inside RcmL

COMPOSITE_NOISE = solid black (0.0)
    -> RcmL becomes entirely cyan
    -> BASE_TEX selected

COMPOSITE_NOISE = solid white (1.0)
    -> RcmL becomes entirely magenta
    -> COMPOSITE_TEX selected

COMPOSITE_NOISE = ~0.5 gray
    -> RcmL remains cyan / BASE side

COMPOSITE_NOISE = ~0.8
    -> RcmL is already magenta / COMPOSITE side
```

Therefore:

```text
low composite-noise values
    -> BASE realization

high composite-noise values
    -> COMPOSITE realization

natural noise field
    -> broad spatial selection between the two
```

The mapping is **not a simple linear 50/50 color crossfade**. Mid-gray did not yield purple; it remained on the BASE side. There is a transfer/threshold function controlled by `COMPOSITE_PARAMS` or related shader machinery.

The threshold/transfer point is now bracketed approximately between:

```text
0.50 -> BASE
0.80 -> COMPOSITE
```

Do not yet assign a semantic meaning to any individual `COMPOSITE_PARAMS` coefficient. Earlier guesses involving `0.248` or `0.850` were not supported by the controlled runtime results.

This is the exact experiment to continue next session.

---

# Important lesson about soft reload

A full engine restart is **not** required for every `.ter` experiment.

Developer soft reload does pick up the material changes, but the scene must be allowed to finish rebuilding/rendering before interpreting the result. Several earlier frames were captured while the scenery was still in a transient reload state, leading to misleading comparisons.

Current laboratory rule:

```text
1. change exactly one material variable
2. soft reload scenery
3. wait for full visual settle
4. use a conspicuous diagnostic texture when possible
5. only then record the result
```

The cyan/magenta test is the preferred compositor diagnostic because it turns subtle shader selection into an obvious binary visual signal.

---

# What NOT to conclude from today's discarded tests

Earlier natural-texture A/B tests of:
- `natnoise` vs `fornoise`;
- constant black/gray/white noise while using similar natural textures;
- BASE alpha black/gray/white;
- decal present/absent;

were muddied by either subtle artwork, uncertain scene settling, or both.

Do **not** treat those earlier runtime visual conclusions as authoritative.

The file-forensics results remain valid. The cyan/magenta controlled compositor results are the trustworthy runtime evidence.

The decal still needs a clean, conspicuous diagnostic test later if we need to understand its exact visual contribution.

---

# Current experimental state: IMPORTANT

The custom `RcmL` terrain is intentionally left in **diagnostic mode**, not production mode.

At session end, the important state is:

```text
BASE_TEX
    diagnostic cyan rcml_test_base.png

COMPOSITE_TEX
    diagnostic magenta rcml_test_composite.png

COMPOSITE_NOISE
    a constant probe value from the current threshold experiment
    DO NOT ASSUME WHICH ONE; inspect before continuing
```

The stock/natural configuration is backed up in various session copies, including earlier `.ter` backups. Before a production commit, restore the normal natural texture paths and known-good natural noise recipe.

Start next session by running:

```bash
TER="$HOME/linGames/Ullaaq-Air-Nunavik/scenery/Ullaaq_Nunavik_Resources/terrain/ullaaq_rcml_test.ter"

grep -E \
'^(BASE_TEX|COMPOSITE_TEX|COMPOSITE_NOISE|COMPOSITE_PARAMS|DECAL_LIB)' \
"$TER"
```

Do not trust memory for the currently selected constant-noise file.

---

# High-resolution imagery direction

High-resolution aerial imagery is increasingly likely to be used for **direct authoring of our own texture assets**, not merely as visual reference.

Potential role:

```text
satellite imagery
    -> kilometre/hectometre landscape organization

aerial / orthophoto imagery
    -> metre-scale material structure

ground photography
    -> centimetre/metre surface appearance
```

Likely production approach:

```text
high-res real imagery
    -> representative clean ecological patches
    -> remove/balance unwanted lighting/shadows/infrastructure
    -> synthesize seamless macro realization A
    -> synthesize related macro realization B
    -> derive close-range decal vocabulary
    -> X-Plane .ter
```

The Laminar compositor architecture strongly suggests that BASE and COMPOSITE should be **two related realizations of the same ecological surface**, not radically different terrain states.

Potential Québec data sources identified for later investigation include:
- current MRNF orthorectified imagery around settlements;
- older high-resolution northern-village orthophoto coverage;
- northern Québec oblique aerial photo bank;
- BDVA 2K northern Indigenous-village photogrammetric/topographic products.

The BDVA-style photogrammetric data is likely more valuable for settlement reconstruction than for wild terrain.

---

# Important paths

Project repo:

```text
~/linGames/Ullaaq-Air-Nunavik
```

Current tile work root:

```text
~/linGames/Ullaaq-Air-Nunavik/work/+58-069
```

VEG_NORD exact tile:

```text
~/linGames/Ullaaq-Air-Nunavik/work/+58-069/landcover/+58-069_VEG_NORD_tile.gpkg
layer: veg_nord
features: 16,227
```

NHN authoritative water:

```text
/home/mike/linGames/X-Plane 12/Development/GIS/Canada/NHN/tiles/+58-069/+58-069_NHN_water_final.gpkg
```

Ortho4XP:

```text
~/linGames/Ortho4XP
```

Semantic patch target:

```text
~/linGames/Ortho4XP/src/O4_DSF_Utils.py
```

Canonical landcover injector:

```text
~/linGames/Ortho4XP/src/O4_Ullaaq_Landcover.py
```

Custom resource package:

```text
~/linGames/Ullaaq-Air-Nunavik/scenery/Ullaaq_Nunavik_Resources
```

Custom RcmL terrain:

```text
~/linGames/Ullaaq-Air-Nunavik/scenery/Ullaaq_Nunavik_Resources/terrain/ullaaq_rcml_test.ter
```

Material inspector:

```text
~/linGames/Ullaaq-Air-Nunavik/tools/inspect_xplane_terrain.py
```

Material lab:

```text
~/linGames/Ullaaq-Air-Nunavik/work/material-lab
```

Forest overlay generator:

```text
~/linGames/Ullaaq-Air-Nunavik/tools/make_rcml_forest_overlay.py
```

Stock-overlay road extraction tool:

```text
~/linGames/Ullaaq-Air-Nunavik/tools/extract_stock_roads.py
```

Stock road decompile:

```text
~/linGames/Ullaaq-Air-Nunavik/work/+58-069/stock-overlay/+58-069_stock.txt
```

Road-only DSF2TEXT:

```text
~/linGames/Ullaaq-Air-Nunavik/work/+58-069/stock-overlay/+58-069_roads_only.txt
```

Road centerlines:

```text
~/linGames/Ullaaq-Air-Nunavik/work/+58-069/stock-overlay/+58-069_road_centerlines.geojson
```

Road surface geometry:

```text
~/linGames/Ullaaq-Air-Nunavik/work/+58-069/stock-overlay/+58-069_road_surface_utm.gpkg
layer: road_surface
```

---

# Project-control rules

1. Filesystem/repository and source datasets remain the source of truth.
2. Preserve the proven MRDEM + NHN + native VEG_NORD geometry architecture.
3. NHN remains hydro authority.
4. Keep geometry generation separate from semantic/material assignment.
5. `.ter`, `.for`, road surfaces/networks, settlement ground, and `.obj` buildings are separate layers with separate responsibilities.
6. Change one material variable at a time during shader experiments.
7. Prefer grotesquely obvious diagnostic textures over subtle natural A/B comparisons when reverse-engineering rendering behavior.
8. Wait for X-Plane scenery reload to fully settle before recording a result.
9. Keep generated `/work`, source archives, and large outputs out of Git as already configured.
10. Preserve patch mirrors for changes made in the separate Ortho4XP tree.
11. Keep the 31 VEG_NORD semantic classes intact even when several share rendering recipes.
12. Do not enter settlement micro-detail before the wild ecological material vocabulary is established.
13. End substantial sessions with an updated project checkpoint.

---

# Git status / reproducibility

Final Git status was **not re-verified in the conversation after all 2026-08-28 experiments**.

Do not assume the current state is committed.

At the start or end of the next session:

```bash
cd ~/linGames/Ullaaq-Air-Nunavik
git status
```

Before committing, restore any intentionally diagnostic terrain files unless the commit is explicitly meant to preserve the material-lab experiment.

The Ortho4XP semantic patch lives outside the main Ullaaq repository, so ensure its current version remains mirrored/preserved under the Ullaaq project before declaring the milestone reproducible.

---

# Next session: exact starting point

Do **not** begin by painting final tundra art.

Finish the compositor transfer-function experiment first while the cyan/magenta diagnostic is active.

Known bracket:

```text
noise 0.50 -> BASE / cyan
noise 0.80 -> COMPOSITE / magenta
```

Create/test:

```text
0.60
0.70
0.75
```

Recommended first probe:

```text
0.70
```

Decision tree:

```text
if 0.70 -> BASE:
    test 0.75

if 0.70 -> COMPOSITE:
    test 0.60
```

Use soft reload, wait for the scene to finish rendering, and keep the diagnostic BASE/COMPOSITE colors until the threshold/transition behavior is understood.

After that:

```text
1. restore natural RcmL terrain recipe
2. clean up / formalize material-lab tooling
3. choose first production wild recipe, probably heath/tundra rather than forest
4. obtain representative high-resolution real imagery
5. author two related macro realizations
6. build/choose an appropriate close-range decal
7. validate at multiple altitudes
8. expand to the remaining wild families
```

The likely first production target remains one of the open tundra/heath classes (`LS` or `TD`) because it allows terrain-material work to be evaluated without 3D forest density obscuring the ground.

---

# End-of-day assessment

2026-08-28 marks the transition from **engineering proof** to **scenery authoring**.

The project can now independently control:

```text
landform
water
wild ecological boundaries
terrain material
3D vegetation
roads
human-landscape ground treatment
individual buildings
```

That is the complete functional scenery stack needed for Nunavik 1.0.

The immediate challenge is no longer whether X-Plane can display the data. It is how to turn the authoritative ecology into a coherent visual language with minimal blind iteration.

Today's material-lab work significantly reduced that problem. The stock `.ter` system is not an unknowable pile of DDS files: it is a small, repeatable architecture built around two related macro realizations, a noise-driven spatial selector, and close-range decal detail. The cyan/magenta diagnostic has made the compositor directly observable.

Tomorrow starts by locating the BASE/COMPOSITE transfer point between noise values 0.50 and 0.80. After that, we can begin authoring the actual North.
