# NUNAVIK_PROJECT_STATE_2026-09-02

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

Repo-local DSFTool to use for all compile/decompile work:

```text
~/linGames/Ullaaq-Air-Nunavik/DSFTool
```

Reference / vegetation-development tile:

```text
+58-069  Kuujjuaq
```

Second generic-pipeline test tile:

```text
+58-070  Tasiujaq
```

**Session result:** The generic DEM / hydro / VEG_NORD tile pipeline was carried successfully into Tasiujaq, the shoreline “waterfall” artifact was removed by disabling Ortho4XP water smoothing, and the custom vegetation problem crossed a major architectural threshold. A fully custom Blender-authored 3D mesh + custom billboard was exported to an X-Plane 12 `.for`, referenced by the Ullaaq resource library, compiled into the VEG_NORD vegetation overlay, and rendered successfully in-engine across real `RmC` polygons. The test asset is intentionally an ugly neon-green low-poly cone tree. It is now a regression fixture proving the complete custom 3D vegetation path.

The project is no longer constrained to Laminar's stock spruce / fir / pine assets.

---

## 1. Executive status

The core production architecture remains:

```text
MNT-HC 10 m DEM
    -> authoritative terrain elevation

NHN / HNET Bank + Delimiter + HHYD Waterbody
    -> authoritative hydro geometry / native XP12 water

VEG_NORD
    -> terrestrial polygon geometry + ecological semantics

Ortho4XP
    -> constrained replacement mesh + DSF

custom Ullaaq .ter
    -> ground / substrate rendering

VEG_NORD-driven custom .for
    -> woody vegetation / 3D ecological structure

road / settlement layers
    -> separate human-landscape treatment
```

The active development mode has now shifted from “prove that custom vegetation control is possible” to:

```text
build real northern vegetation assets
    -> calibrate from registered Québec reference photography
    -> select recipes from VEG_NORD semantics
    -> retain one GIS skeleton for all seasons
    -> vary rendering policy rather than duplicating GIS
```

A major project principle remains:

> The GIS describes ecological structure. The rendering layer decides how that structure looks in X-Plane.

Do not inflate the VEG_NORD class taxonomy merely to create different rendering recipes.

---

## 2. Shoreline waterfall artifact: cheap win

The remaining steep / curtain-like shoreline artifacts were tested against Ortho4XP water-smoothing settings.

Working GUI values:

```text
sea_smoothing_mode = none
water_smoothing    = 0
```

Result:

```text
no shoreline waterfall issue visible
```

The previous artifact was therefore strongly associated with Ortho4XP water smoothing rather than bad NHN XY geometry, VEG_NORD, or the MNT-HC DEM itself.

Current policy:

```text
disable sea smoothing
disable inland water smoothing
```

This is accepted as the production default for the high-quality Nunavik data stack unless a later low-quality-data tile demonstrates a reason to restore smoothing selectively.

---

## 3. Permanent MNT-HC tile extraction tooling

A canonical DEM tile builder is now in place:

```text
tools/build_mnt_hc_dem_tile.py
```

Usage:

```bash
python3 tools/build_mnt_hc_dem_tile.py LAT LON
```

Known normalized outputs:

```text
~/linGames/GIS/Canada/MNT_HC/tiles/+58-069_MNT_HC_CGVD2013.tif
~/linGames/GIS/Canada/MNT_HC/tiles/+58-070_MNT_HC_CGVD2013.tif
```

The builder was validated against the known-good reference DEM with exact zero delta across the full 100 million pixels.

The production DEM policy remains:

```text
MNT-HC source datum: CGVD28
    -> HT2_2010v70
    -> CGG2013n83
    -> CGVD2013
```

Do not hand-edit normalized production DEM TIFFs.

---

## 4. Generic pipeline validation on +58-070 Tasiujaq

Tasiujaq was used as the second full-tile test of the generalized toolchain.

The result is successful enough to classify the mesh / hydro / VEG_NORD stack as generic rather than Kuujjuaq-specific.

### VEG_NORD

Canonical builder:

```text
tools/build_veg_nord_tile.py
```

`+58-070` output:

```text
18,193 features
exact extent -70..-69 / 58..59
0 invalid geometries
```

Five source codes appeared that had not occurred in the original 31-code Kuujjuaq reference set:

```text
CB
NE
RaD
TAO
TDO
```

They were added provisionally to the semantic table.

Observed explicit class coverage is therefore now:

```text
36 VEG_NORD cl_carto codes
```

The Ortho4XP hard class-count assertion was updated accordingly.

### NHN hydro

Canonical builder:

```text
tools/build_nhn_hydro_tile.py
```

`+58-070` output:

```text
~/linGames/GIS/Canada/NHN/tiles/+58-070/+58-070_NHN_water.gpkg
```

Statistics:

```text
wet / output faces: 42,034
dry faces:           1,633
invalid faces:           0
overlap pairs:           0
```

The builder currently requires the Ortho4XP Python environment because it depends on Shapely.

### Full Ortho4XP build

Step 1 / Step 2 / Step 3 all exited normally.

Representative scale:

```text
Step 1 constrained edges: ~2.98 million
Step 2 triangles:         ~7.00 million
```

Bing imagery was also generated normally.

### Visual result

The most obvious success was ecological: stock X-Plane autumn / New-Hampshire-looking forest disappeared from Tasiujaq. The open tundra reads plausibly.

Tasiujaq is mostly treeless, so it is a good generic-pipeline tile but a poor forest-art calibration tile. Continue vegetation design on `+58-069`.

### Known Tasiujaq hydro issues

Two source / interpretation issues remain and are not current blockers:

1. A false NHN pond intersects the CYTQ apron. Satellite imagery shows no pond. This belongs in a future hydro corrections layer.
2. The Tasiujaq estuary is strongly tidal, with a shoreline that behaves more like a zone than a line. Future rendering should distinguish permanent water, intertidal ground, permanent land, and open-coast treatment.

Do not derail vegetation work to polish these yet.

---

## 5. Roads: current data direction

Québec RQTT is available locally:

```text
~/linGames/GIS/Canada/RQTT/OGC(GPKG)/RQTT.gpkg
```

CRS:

```text
EPSG:3798
```

Tasiujaq has approximately:

```text
85 Reseau_routier segments
```

Current production concept:

```text
RQTT all Reseau_routier
    -> backbone geometry

fine village topology / manual / orthophoto corrections
    -> local refinement

surface enrichment
    -> separate attribute / rendering stage
```

Do not filter the production ingest to only CL1 / CL4 roads.

Road visual treatment will probably require both:

```text
draped disturbed-ground / gravel scars
optional traffic network semantics
```

This remains secondary to the vegetation asset work.

---

## 6. Vegetation architecture: VEG_NORD provides species as well as density

VEG_NORD forest polygons contain enough information to select rendering recipes by more than `cl_carto` alone.

Useful attributes include:

```text
cl_carto   ecological / map class
cl_dens    tree-cover density class
ess_dom    dominant tree species
veg_sbois  understory / substrate family
type_couv  broad cover context
```

Important rule:

> Do not manufacture new GIS classes for every `(cl_carto, cl_dens, ess_dom)` combination.

Instead:

```text
cl_carto / veg_sbois
    -> ground / ecological family

cl_dens
    -> packing / woody-cover density

ess_dom
    -> dominant tree recipe
```

X-Plane itself does not know `ML`, `EN`, `RmC`, etc. The overlay generator must translate these source attributes into `POLYGON_DEF` indices and `.for` library references before DSF compilation.

---

## 7. RmC species inventory on +58-069

The densest moss/heath forest class is:

```text
RmC
```

Meaning:

```text
R  coniferous forest context
m  moss + ericaceous / heath understory
C  41–60% crown cover
```

There are only 29 `RmC` polygons in the Kuujjuaq tile.

Dominant species (`ess_dom`) counts:

```text
EN  26 polygons
ML   3 polygons
```

Interpretation:

```text
EN = épinette noire = black spruce
ML = mélèze laricin = tamarack / eastern larch
```

The three `ML` polygons are large enough that feature count understates their importance.

Approximate `superficie` totals from the queried `RmC` polygons:

```text
EN:  971.9
ML:  219.5
total 1191.4
```

Thus the `ML` polygons are approximately 18.4% of the mapped `RmC` area despite being only 3 of 29 features.

Important limitation:

```text
ess_dom = dominant species only
```

It does not encode a complete within-stand species mixture. Rendering recipes may therefore include subordinate species calibrated from imagery, but the GIS should not pretend to know percentages it does not contain.

---

## 8. Registered reference AGG_3735: exact stand identification

The Québec oblique-photo viewer can display oblique photography and VEG_NORD simultaneously, allowing photo markers and ecological polygons to be registered to each other.

This provides a much stronger calibration source than interpreting forest class names in the abstract.

Registered sim / photo reference near:

```text
camera approximately 58.051, -68.479
heading approximately 112 degrees
```

Sample points along the view were intersected against the canonical VEG_NORD GeoPackage.

First ~750 m of the sightline:

```text
id_seq      761400
cl_carto    RmC
ess_dom     ML
superficie  41.2
```

At approximately 1 km the view crosses into:

```text
id_seq      761471
cl_carto    RmL
ess_dom     ML
superficie  41.9
```

This is an unusually useful controlled comparison:

```text
same dominant species: tamarack
same Rm substrate family
different density class: C -> L
```

The photographed dense foreground is therefore a **tamarack-dominant RmC stand**, not a black-spruce-dominant stand.

The site is sheltered and river-adjacent, which is ecologically consistent with a dense tamarack pocket.

---

## 9. Visual target for RmC / ML tamarack

Close inspection of the registered oblique photo gives the first real asset brief.

The stand reads as:

```text
very short northern trees
roughly 1.5–4 m visual range
narrow spire-like crowns
strong local height variation
little exposed trunk at flight scale
no conventional tall boreal canopy
few large empty holes
continuous low woody / shrub matrix between crowns
```

The visible texture comes primarily from:

```text
species / color variation
height variation
crown fullness variation
```

not from carving large Perlin-style clearings into the densest class.

The `C` density class should therefore read as densely packed short woody vegetation rather than conventional 15–20 m forest.

A mature tamarack reference shows a straight central leader, relatively open branch structure, and fine feathery foliage. The northern growth form should keep that architecture while becoming much shorter, narrower, more asymmetric, and more ragged.

---

## 10. Stock Laminar forest investigation

Laminar's XP12 `1200 forests` inventory contains named spruce, fir, and pine assets but no named tamarack / larch asset found in the search.

Promising stock prototype source used earlier:

```text
Resources/default scenery/1200 forests/sum/tree_spruce_2.for
```

The stock billboard sprites could be rescaled down successfully, but retaining Laminar's full-sized 3D mesh produced a dramatic near-field size pop at the mesh LOD transition.

Removing `MESH_3D` from the custom spruce proof produced a billboard-only forest with plausible northern scale.

This established two things:

1. the forest-height problem was not the DSF overlay itself;
2. billboard and 3D geometry must represent the same physical tree dimensions.

That strongly favors authoring the billboard and near-field mesh from the same source model.

---

## 11. Asset strategy: author Ullaaq vegetation

Third-party vegetation libraries were investigated briefly.

OpenSceneryX has explicit `Larix` / `Larix laricina` objects, demonstrating that X-Plane vegetation assets exist for tamarack, but they are ordinary scenery objects rather than a directly reusable Ullaaq `.for` asset pipeline. Licensing / modification constraints also make external asset dependence unattractive for a project that will need many region-specific low plants.

Current decision:

> Author the Ullaaq northern-vegetation asset library ourselves.

This is especially important because the difficulty increases below the tree layer. Generic libraries are unlikely to provide botanically useful Labrador tea, bilberry, dwarf birch, low willow, crowberry / ericaceous mats, etc. in the exact forms required.

Expected asset tiers:

```text
TREE / TALL SHRUB
    tamarack
    black spruce
    willow / dwarf birch forms

LOW WOODY VEGETATION
    Labrador tea clumps
    bilberry / blueberry clumps
    ericaceous / crowberry mats
    low willow
    dwarf birch

GROUND MATRIX
    moss
    lichen
    sedge / graminoid
    heath
    exposed organic ground
```

Use real geometry where silhouette / parallax matters. Keep ground-matrix vegetation primarily in `.ter`, decals, normals, and sparse detail cards rather than turning every moss plant into geometry.

---

## 12. Blender authoring strategy

Current authoring environment:

```text
Blender 5.2 LTS
```

Initial thought was to use Blender 5.2 for authoring and Blender 4.2.23 as an X-Plane export station via GLB. That bridge was proven, but it is no longer required.

The production target is now direct export from Blender 5.2.

Recommended real-tree workflow:

```text
Blender source model
    -> trunk + branch architecture
    -> foliage cards / instances
    -> orthographic billboard render from same model
    -> simplified near-field 3D mesh from same model
    -> XPlaneForExporter
    -> .for
```

This guarantees that the billboard and 3D LOD represent the same organism and physical scale.

First real species target:

```text
RmC / ML tamarack
```

Do not over-engineer Geometry Nodes before one convincing hand-built / simple procedural tamarack exists.

---

## 13. Custom 3D vegetation pipeline proof

A deliberately ugly low-poly “tree” was created to prove the complete pipeline before investing in real art.

The test geometry is approximately:

```text
3 m tall
1 m crown width
cone crown
short cylinder trunk
neon green diagnostic texture
```

Blender source / test workspace used during the session:

```text
~/linGames/Ullaaq-Air-Nunavik/work/Objects/Test/Replacme_Tree.blend
```

The typo in `Replacme_Tree.blend` is real. Do not lose the file because of the spelling.

### Required forest hierarchy

The XPlaneForExporter hierarchy must be:

```text
TAM_TEST_FOREST              top-level collection / forest root
└── 01 Trees                 numbered child collection / forest layer
    └── TAM_TEST             EMPTY object / tree wrapper
        ├── TAM_TEST_billboard
        └── TAM_TEST_mesh
```

Important exporter quirk:

```text
01 Trees     works
01-Trees     fails
```

The exporter parses the first whitespace-delimited token as an integer layer number.

The tree wrapper must be an **Empty object**, not another Collection.

### Billboard

Test billboard:

```text
1 m wide
3 m tall
centered at Z = 1.5 m
vertical quad
UV mapped
```

Exporter material:

```text
Albedo -> ullaaq_tam_test_bb_ALB.png
Blend Hash enabled
```

### 3D mesh

The 3D mesh must also have:

```text
UV map
material slot
XPlaneForExporter Albedo
```

Test 3D texture:

```text
ullaaq_tam_test_3d_ALB.png
```

Apply object Location before export so the exporter writes the desired physical vertex coordinates rather than a mesh centered around the object's local origin.

For the 3 m test tree the correct exported vertical range is approximately:

```text
0.0 .. 3.0 m
```

### Tree-wrapper settings used

```text
Weighted Importance = 1
Max. Tree Height     = 3.0
Use custom LOD       = off
Group                = 0
```

### Forest settings used

```text
Spacing      5.0 5.0
Randomness   1.0 1.0
Cast Shadow  on
Has Seasons  off
Density Params off
Choice Params  off
Height Params  off
```

---

## 14. Test textures / resource files

Diagnostic textures:

```text
scenery/Ullaaq_Nunavik_Resources/textures/ullaaq_tam_test_bb_ALB.png
scenery/Ullaaq_Nunavik_Resources/textures/ullaaq_tam_test_3d_ALB.png
```

The billboard texture is transparent with a neon-green tree-shaped test mark.

The 3D texture is neon green with a dark grid so UV failures are obvious.

Generated test forest:

```text
scenery/Ullaaq_Nunavik_Resources/forests/ullaaq_tam_test_.for
```

Library mapping used:

```text
EXPORT lib/ullaaq/forests/tam_test.for forests/ullaaq_tam_test_.for
```

The disposable `RmC` vegetation overlay was retargeted to:

```text
POLYGON_DEF lib/ullaaq/forests/tam_test.for
```

The existing `RmC` polygons were deliberately reused unchanged so the test altered only the vegetation asset, not geometry or density semantics.

---

## 15. XPlaneForExporter: Blender 5.2 compatibility patches

The official XPlaneForExporter is old enough to require small compatibility fixes.

The important result of the session is that it now runs **directly under Blender 5.2**, so the temporary Blender 4.2 / GLB shuttle can be retired.

### Patch 1: removed Blender API call

The exporter called:

```python
mesh.calc_normals_split()
```

This API is no longer available in current Blender.

Compatibility form:

```python
if hasattr(mesh, "calc_normals_split"):
    mesh.calc_normals_split()
```

This allows the exporter to continue working on older Blender while not failing on 5.2.

### Patch 2: correct exported texture paths

The stock exporter mishandled Blender paths and could write invalid paths such as:

```text
TEXTURE linGames/Ullaaq-Air-Nunavik/scenery/...
```

`forest_header.py` was patched so material paths are resolved to absolute filesystem locations and then written relative to the exported `.for` directory.

Verified direct Blender 5.2 output:

```text
SHADER_2D
    TEXTURE ../textures/ullaaq_tam_test_bb_ALB.png

SHADER_3D
    TEXTURE ../textures/ullaaq_tam_test_3d_ALB.png
```

This removes the previous manual post-export `sed` repair.

### Preserve patches in the repository

The local Blender add-on lives under the user's Blender configuration and can be overwritten by reinstalling the exporter.

The project should retain a repository patch, e.g.:

```text
patches/XPlaneForExporter_blender52.patch
```

covering both:

```text
forest_tables.py   calc_normals_split compatibility
forest_header.py   texture-path handling
```

Treat this patch as production tooling, not an incidental workstation tweak.

---

## 16. Forest exporter debugging notes

Useful failure signatures discovered today:

### Wrong layer name

Bad:

```text
01-Trees
```

Failure:

```text
UnboundLocalError: local variable 'layer_number' ...
```

Good:

```text
01 Trees
```

### Billboard has no material

Forest logger:

```text
E002: Tree vert_quad had no 1st slot or no material in its first slot
E011: ... contains no valid tree containers
```

`E011` is downstream. Fix `E002` first.

### Export appears to fail silently

The exporter writes validation failures into the Blender text block:

```text
ForestLogger.log
```

Inspect this before guessing.

### Blender 4.2 / 5.2 mesh crash

Traceback ending with:

```text
AttributeError: 'Mesh' object has no attribute 'calc_normals_split'
```

Fix with the compatibility patch above.

### File chooser confusion

The folder icon beside the forest `File Name` field only chooses the destination. It does not perform the export.

Actual action:

```text
Scene Properties
    -> XPlaneForExporter
    -> Export X-Plane Forest
```

---

## 17. In-engine proof: custom low-poly forest

The generated custom forest was compiled into the `+58-069` vegetation DSF and loaded in X-Plane 12.

Result:

> **PASS: one forest of low-poly neon-green custom 3D trees.**

At ground level X-Plane rendered the custom cone/cylinder geometry in quantity.

At cockpit altitude the neon forest followed the real VEG_NORD `RmC` polygon boundaries and remained coherent across the landscape.

This proves, end-to-end:

```text
Blender 5.2
    custom billboard
    custom 3D mesh
    UVs
    custom materials
        ↓
patched XPlaneForExporter
        ↓
custom .for
        ↓
Ullaaq library export
        ↓
VEG_NORD vegetation overlay
        ↓
DSFTool compilation
        ↓
X-Plane 12
        ↓
custom 3D vegetation rendered in-engine
```

This is the key architectural result of the day.

The neon test asset should be retained as a regression fixture because it is cheap, unmistakable, and simultaneously tests:

```text
mesh export
billboard export
UV / material paths
physical scale
forest hierarchy
library resolution
DSF polygon placement
X-Plane forest rendering
LOD behavior
```

Do not “clean it up” into a realistic asset. Its ugliness is diagnostic value.

---

## 18. Repo-local DSFTool policy

Use this binary for DSF compile / decompile work:

```text
~/linGames/Ullaaq-Air-Nunavik/DSFTool
```

Canonical shell pattern:

```bash
cd "$HOME/linGames/Ullaaq-Air-Nunavik"
DSFTOOL="$PWD/DSFTool"
```

Avoid snippets containing `exit` when they are intended to be pasted directly into the user's interactive shell. An earlier path-check block used `exit 1`, which exited the terminal shell and looked like a terminal crash.

---

## 19. Production forest-overlay direction

The existing proof generator remains:

```text
tools/make_rcml_forest_overlay.py
```

It is hard-coded to the old `RcmL` proof and should not yet be blindly replaced.

The disposable `RmC` test was generated separately and used approximately:

```text
29 source RmC features
31 forest polygons
32 windings
DSF density 160 / 255
```

Once the real species recipes are visually credible, create one canonical generic vegetation-overlay builder that:

1. accepts tile coordinates;
2. reads the canonical VEG_NORD tile;
3. preserves polygon holes / windings;
4. selects `.for` definitions from ecological attributes;
5. can emit multiple `POLYGON_DEF` entries;
6. uses `ess_dom` for dominant-species recipe selection;
7. uses density semantics without inventing new GIS classes.

Conceptual future dispatch:

```text
RmC + ML
    -> dense tamarack-dominant recipe

RmL + ML
    -> sparse tamarack-dominant recipe

RmC + EN
    -> dense black-spruce-dominant recipe

RmL + EN
    -> sparse black-spruce-dominant recipe
```

These are rendering recipes, not new `cl_carto` values.

---

## 20. Seasonal consequence

Species-aware rendering is important for the planned four-season scenery system.

Example:

```text
black spruce
    -> evergreen

tamarack
    -> green summer
    -> yellow / gold fall
    -> bare winter
    -> fresh light green spring
```

Owning the source assets makes this tractable.

Keep the GIS / semantic skeleton season-independent.

Preferred architecture:

```text
one ecological GIS skeleton
    -> summer rendering policy
    -> fall rendering policy
    -> winter rendering policy
    -> spring rendering policy
```

Do not duplicate the GIS for seasons.

---

## 21. Git / checkpoint policy

This session reached a real known-good architecture checkpoint:

```text
custom 3D vegetation pipeline proven in X-Plane 12
```

The Git checkpoint workflow was invoked at session end.

The useful tracked state should include, where project policy allows:

```text
XPlaneForExporter Blender 5.2 patch
resource library export
custom neon test .for
custom neon billboard texture
custom neon 3D texture
any canonical tooling / documentation changes
```

Generated work products and disposable source/intermediate files should remain outside Git according to existing repository policy.

No commit hash is recorded in this state note.

---

## 22. Immediate next steps

### A. Preserve exporter patch cleanly

Confirm the repository contains a reproducible patch for the two XPlaneForExporter modifications.

The workstation add-on under `~/.config/blender/...` is not sufficient as the sole copy.

### B. Start the first real tamarack

Use the registered `AGG_3735` `RmC / ML` stand as the primary visual target.

First-pass modeling priorities:

```text
1. silhouette
2. physical scale
3. central leader / branch architecture
4. feathery foliage mass
5. crown openness
6. billboard-to-3D LOD consistency
```

Do not prioritize individual needle realism.

A reasonable first real asset remains:

```text
~3 m tamarack
roughly 10–20 primary branches
small set of foliage-card variants
2–4 derived whole-tree variants
```

### C. Render the billboard from the same model

The billboard and near-field mesh should derive from the same Blender source so their scale and silhouette agree through LOD transitions.

### D. Calibrate density only after the tree looks right

The densest `RmC / ML` reference does not contain huge clearings.

Do not use broad `DENSITY_PARAMS` noise to fake stand variation at this stage.

Use:

```text
species mixture
height variation
crown variation
packing
```

before introducing large-scale density modulation.

### E. Black spruce next

Once tamarack works, build the `EN` recipe using the same production pipeline.

Then use `ess_dom` to dispatch ML vs EN stands rather than forcing every `RmC` polygon through one forest definition.

### F. Understory after trees

The eventual northern vegetation library will require low woody species / communities, likely via cheap crossed cards / clumps and ground materials rather than high-detail meshes.

Do not begin this until the tree asset and export path are boring and repeatable.

---

## 23. Things explicitly not to forget

- `+58-069` remains the forest / vegetation art calibration tile.
- `+58-070` remains the second generic-pipeline proof and open-tundra validation tile.
- VEG_NORD `ess_dom` is dominant species only, not a full mixture percentage.
- The registered `AGG_3735` foreground is polygon `761400`, `RmC`, `ML`.
- Around 1 km along that view the class becomes `761471`, `RmL`, still `ML`.
- Tamarack is a key seasonal species and justifies species-aware rendering.
- Dense northern forest means dense packing of very short trees, not a tall conventional canopy.
- Keep billboard and 3D source scales identical.
- Apply object Location before forest export where needed.
- Forest layer collection names require an integer followed by whitespace, e.g. `01 Trees`.
- Tree wrappers must be Empty objects.
- Billboard and 3D mesh both need UVs and exporter materials / Albedo paths.
- Exporter errors may be hidden in `ForestLogger.log`.
- Keep the neon cone forest as a permanent regression test.
- Use repo-local `./DSFTool`.
- Avoid `exit` in paste-ready interactive shell snippets.
- Preserve the Blender 5.2 exporter compatibility patch in Git.
- Do not create more VEG_NORD classes merely to distinguish species rendering recipes.
- Do not let vegetation art derail the hydro corrections backlog or vice versa.

---

## 24. Current project posture

The core mesh and semantic architecture is now proven across more than one tile.

The project has also crossed the custom-autogen threshold:

> **Ullaaq can now author and render its own 3D ecological assets rather than merely selecting among Laminar's stock vegetation.**

The remaining challenge is no longer “can X-Plane do this?”

It is now the far more pleasant problem:

```text
what does Nunavik actually look like,
and how cheaply can we make X-Plane believe it?
```
