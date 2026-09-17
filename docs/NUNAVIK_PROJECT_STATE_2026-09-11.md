# NUNAVIK_PROJECT_STATE_202609-11

## Project

**Ullaaq Air Nunavik scenery pipeline for X-Plane 12**

Repository:

```text
~/linGames/Ullaaq-Air-Nunavik
```

Repo-local DSFTool:

```text
~/linGames/Ullaaq-Air-Nunavik/DSFTool
```

Primary vegetation-development tile:

```text
+58-069  Kuujjuaq
```

Current custom resource package:

```text
~/linGames/Ullaaq-Air-Nunavik/scenery/Ullaaq_Nunavik_Resources
```

Current Northern Trees working directory:

```text
~/linGames/Ullaaq-Air-Nunavik/work/Objects/Northern_Trees
```

Current live Tamarack forest resource:

```text
scenery/Ullaaq_Nunavik_Resources/forests/ullaaq_larix_laricina_test.for
```

Current virtual forest resource used by the vegetation DSF:

```text
lib/ullaaq/forests/tam_test.for
```

---

# Session summary

Today's session resolved two apparently related rendering problems and, importantly, proved that they were **not related**.

The first problem was the visibly soft / coarse custom `RmC` ground material beneath the developing Tamarack forest. Controlled replacement of the custom ground recipe with Laminar's complete stock conifer terrain stack restored the expected visual structure. The custom ground texture itself was not fundamentally broken; the terrain definition was simply unfinished.

The second problem was an apparent periodic "blink" in tree shadows. This looked suspicious enough to implicate the custom Larix mesh, alpha cards, atlas, or `.for` setup. A long sequence of controlled tests progressively removed those possibilities.

The decisive result was:

> **The same shadow blink is visible in completely unmodified stock X-Plane scenery at KTAN.**

The issue is therefore considered an X-Plane rendering-engine behavior / limitation rather than a defect in the Northern Trees asset pipeline.

The diagnostic substitutions were then unwound. The live vegetation chain is restored to the custom Tamarack.

Current project direction:

```text
Northern Trees / Tamarack visual refinement     ACTIVE NEXT
RmC custom ground finalization                 PARKED
tree-shadow blink                              CLOSED / ENGINE BEHAVIOR
```

---

# 1. Executive status

The established Ullaaq scenery architecture remains unchanged:

```text
Québec MNT-HC 10 m DEM
    -> authoritative terrain elevation

NHN / HNET Bank + Delimiter + HHYD
    -> authoritative hydrography

VEG_NORD
    -> terrestrial ecological polygons / semantics

Ortho4XP
    -> constrained replacement mesh

custom Ullaaq .ter
    -> ground / substrate rendering

VEG_NORD-driven custom .for
    -> woody vegetation / Northern Trees

roads / buildings / settlement layers
    -> separate human-landscape overlays
```

Current status of the Northern Trees work:

```text
card-native Tamarack generator        PROVEN
X-Plane .for export pipeline          PROVEN
custom atlas mapping                  PROVEN
custom forest placement               PROVEN
in-engine Tamarack rendering          PROVEN
tree-shadow blink                     NOT AN ASSET BUG
Tamarack appearance refinement        NEXT
final XP12 vegetation material stack  LATER, after form is satisfactory
```

Current status of the `RmC` terrain material:

```text
custom BASE macro image               PROVEN
physical macro scale                  REASONABLE / PROVEN
custom .ter plumbing                  PROVEN
missing composite stack               IDENTIFIED
missing close-range decal             IDENTIFIED
full stock stack under Tamarack       PROVEN
final custom RmC material             DEFERRED
```

---

# 2. RmC ground investigation

## Symptom

The custom `RmC` ground beneath the Tamarack stand appeared much softer / coarser than adjacent stock conifer terrain.

This was visible both close up and at a more distant range where the stock close-detail decal was no longer the dominant difference.

The custom material initially used only:

```text
BASE_TEX ../textures/hiveg/rmc_AB_1024.png
PROJECTED 1673 1673
```

The live custom texture is:

```text
scenery/Ullaaq_Nunavik_Resources/textures/hiveg/rmc_AB_1024.png
```

Size:

```text
1024 x 1024
```

Material-lab source:

```text
work/material-lab/Forest/AB_Q21662_236-250.png
```

Source size:

```text
16384 x 16384
```

Material-lab downsample:

```text
work/material-lab/Forest/AB_Q21662_236-250_1024.png
```

The installed `rmc_AB_1024.png` was confirmed to be byte/image-identical to the material-lab 1024 version.

---

# 3. Physical projection scale was not the error

The source orthophoto is approximately:

```text
0.10 m / pixel
```

A 16384 px master therefore represents approximately:

```text
1638.4 m
```

The `.ter` uses:

```text
PROJECTED 1673 1673
```

That is only about 2.1% larger than the source footprint and therefore physically reasonable.

At runtime:

```text
1673 m / 1024 px = ~1.634 m/px
```

This is also essentially the same macro density used by Laminar's stock conifer terrain.

Conclusion:

> The softness was not caused by an obvious projection-scale mistake.

The earlier suspicion of a factor-of-16 projection error is rejected.

---

# 4. Stock conifer terrain anatomy

Stock terrain inspected:

```text
$HOME/linGames/X-Plane 12/Resources/default scenery/1000 world terrain/terrain10/coni_vcld_sdry_fl.ter
```

Relevant stock recipe:

```text
A
800
TERRAIN

BASE_TEX ../textures10/hiveg/coni_cld_dry_flat_c.dds
BORDER_TEX ../textures10/border/soft.png
PROJECTED 1673 1673
SUPER_ROUGHNESS 0.5

COMPOSITE_TEX ../textures10/hiveg/coni_cld_dry_flat_c2.dds
COMPOSITE_PROJECTED 1673 1673
COMPOSITE_PARAMS 0.104000 0.850000 0.248000 1.820000 2.050000 0.260000
COMPOSITE_NOISE ../textures10/shared/natnoise.png

NO_ALPHA
COMPOSITE_BORDERS
DECAL_LIB lib/g10/decals/maquify_1_alpha_key.dcl
```

Local copies already present in the Ullaaq resource package:

```text
textures/hiveg/coni_cld_dry_flat_c.dds
textures/hiveg/coni_cld_dry_flat_c2.dds
textures/shared/natnoise.png
```

The custom `RmC` terrain before the test had effectively been reduced to:

```text
A
800
TERRAIN

BASE_TEX ../textures/hiveg/coni_cld_dry_flat_c.dds
BORDER_TEX ../textures/border/soft.png
PROJECTED 1673 1673
SUPER_ROUGHNESS 0.5
NO_ALPHA
```

Thus it was missing:

```text
COMPOSITE_TEX
COMPOSITE_PROJECTED
COMPOSITE_PARAMS
COMPOSITE_NOISE
COMPOSITE_BORDERS
DECAL_LIB
```

---

# 5. Full-stock-stack RmC control

A controlled test replaced the stripped custom `RmC` terrain recipe with the complete stock conifer stack while leaving the Tamarack vegetation overlay intact.

The tested custom `.ter` was:

```text
A
800
TERRAIN

BASE_TEX ../textures/hiveg/coni_cld_dry_flat_c.dds
BORDER_TEX ../textures/border/soft.png
PROJECTED 1673 1673
SUPER_ROUGHNESS 0.5

COMPOSITE_TEX ../textures/hiveg/coni_cld_dry_flat_c2.dds
COMPOSITE_PROJECTED 1673 1673
COMPOSITE_PARAMS 0.104000 0.850000 0.248000 1.820000 2.050000 0.260000
COMPOSITE_NOISE ../textures/shared/natnoise.png

NO_ALPHA
COMPOSITE_BORDERS
DECAL_LIB lib/g10/decals/maquify_1_alpha_key.dcl
```

Result:

> The ground beneath the Tamarack stand became visually comparable to the neighboring stock terrain.

This cleanly demonstrated that the previous custom-ground softness was not caused by:

```text
Tamarack forest rendering
Larix atlas residency
VEG_NORD polygon geometry
RmC DSF assignment
custom source-image scale
```

It was simply an unfinished `.ter` stack.

---

# 6. Ground-material conclusion

The custom `RmC` ground should eventually be completed as a full multiscale terrain material:

```text
custom RmC BASE macro
        +
custom RmC COMPOSITE sibling
        +
noise/compositor recipe
        +
appropriate close-range DECAL
```

The stock composite should not become the final art.

A future custom companion such as:

```text
rmc_AB_1024_c2.*
```

will need to be authored as a second macro realization rather than merely duplicating the base.

The ground material is now understood well enough that it does not need further debugging.

Decision:

> **Park RmC ground finalization until the Tamarack trees look the way we want.**

The tree/ground relationship should be judged as a unified visual system once the Tamarack silhouette, density, color and material response are closer to production quality.

---

# 7. Tree-shadow blink: original symptom

The developing Tamarack showed a conspicuous shadow artifact.

At close inspection the shadow appeared to cycle through approximately three discrete-looking states.

Observed behavior included:

```text
dark horizontal / flattened-looking shadow structures
periodic cycling / blink
different apparent shadow character with viewing distance
```

At first this could plausibly have been caused by:

```text
bad Larix card geometry
alpha-card shadow handling
BLEND_HASH
atlas transparency
missing normal/translucency material setup
incorrect .for LOD configuration
forest placement
X-Plane shadow-map behavior
```

The investigation therefore proceeded through controlled substitutions.

---

# 8. Larix `.for` state during diagnosis

Relevant custom shader header:

```text
A
800
FOREST

SHADER_2D
    TEXTURE ../textures/larix_laricina_billboard_test1.png
    BLEND_HASH 0

SHADER_3D
    TEXTURE ../textures/larix_laricina_atlas_test2.png
    BLEND_HASH 0

SCALE_X 1024
SCALE_Y 2048
SPACING 5 5
RANDOM 1 1
```

Current main mesh form:

```text
MESH 3D_larix_laricina_test 0 500 308 588 0.0 0.0 0.0
```

Important points:

```text
3D mesh shadow range is 0-500 m
wind/deformation parameters are zero
```

Therefore continuous wind motion was not a plausible explanation for the cycling.

---

# 9. Opaque-atlas test

To test whether alpha transparency was causing the blink, the Larix 3D atlas was replaced with a version whose alpha channel was forced fully opaque.

Diagnostic atlas:

```text
larix_laricina_atlas_test2_opaque.png
```

Result:

> **The same blink remained with the same pattern.**

This proved that ordinary alpha transparency in the 3D Larix atlas was not required to trigger the behavior.

It did not by itself identify the engine mechanism, but it removed one major custom-asset suspect.

---

# 10. Stock spruce shader comparison

Laminar's stock spruce file was inspected:

```text
$HOME/linGames/X-Plane 12/Resources/default scenery/1200 forests/sum/tree_spruce_2.for
```

Stock XP12 shader stack:

```text
SHADER_2D
    TEXTURE ../textures/trees_bb1_ALB.png
    TEXTURE_NORMAL 1 ../textures/trees_bb1_NML.png
    WEATHER ../textures/trees_bb1_SM.png
    BLEND_HASH 0.5
    SUPER_ROUGHNESS 1.0
    NORMAL_TRANSLUCENCY

SHADER_3D
    TEXTURE ../textures/trees_3D1_ALB.png
    TEXTURE_NORMAL 1 ../textures/trees_3D1_NML.png
    WEATHER ../textures/trees_3D1_SM.png
    BLEND_HASH 0.5
    SUPER_ROUGHNESS 1.0
    NORMAL_TRANSLUCENCY
```

Stock spruce mesh structure:

```text
MESH 3D_spruce_02   0 500 ...
MESH 3D_spruce_11   0 500 ...
MESH lod_spruce_02  0 100 ...
MESH lod_spruce_11  0 100 ...
```

Tree declarations:

```text
TREE ... spruce_02
MESH_3D 3D_spruce_02
MESH_3D lod_spruce_02

TREE ... spruce_11
MESH_3D 3D_spruce_11
MESH_3D lod_spruce_11
```

This confirmed that the current single Larix `0-500 m` mesh is not inherently an illegal configuration. The stock tree simply adds an extra close-range mesh.

The richer Laminar normal/weather/translucency material stack remains relevant for eventual Tamarack material quality, but it did not explain the shadow blink.

---

# 11. Old cone regression fixture

The old neon-green custom cone tree was then substituted into the same vegetation polygons.

Old regression fixture:

```text
forests/ullaaq_tam_test_.for
```

Relevant structure:

```text
SHADER_2D
    TEXTURE ../textures/ullaaq_tam_test_bb_ALB.png
    BLEND_HASH 0

SHADER_3D
    TEXTURE ../textures/ullaaq_tam_test_3d_ALB.png

MESH Cone 0 500 466 558 1.0 1.0 10.0

TREE 0 0 512 1024 256 100 3 3 1 1 TAM_TEST
MESH_3D Cone
```

This tree uses ordinary closed cone geometry rather than the Larix folded-card crown.

Result:

```text
close shadow:
    dark
    comparatively crisp
    stable

more distant shadow:
    more diffuse
    blinking / cycling
```

This was a major result.

The simple cone reproducing the distant blink strongly weakened the hypothesis that Larix folded-card topology was responsible.

---

# 12. Initial stock-spruce transplant tests were invalid

An attempt was made to transplant Laminar's stock spruce `.for` into the Ullaaq resource package.

The first copies rendered incorrectly with conspicuous pale / blue card backgrounds.

Investigation showed the stock `.for` names files such as:

```text
trees_bb1_ALB.png
trees_3D1_ALB.png
```

while the installed payload actually contains DDS albedo files:

```text
trees_bb1_ALB.dds
trees_bb1_ALB_fa.dds
trees_bb1_ALB_sp.dds
trees_bb1_ALB_wi.dds

trees_3D1_ALB.dds
trees_3D1_ALB_fa.dds
trees_3D1_ALB_sp.dds
trees_3D1_ALB_wi.dds
```

Normal / weather resources include:

```text
trees_bb1_NML.png
trees_bb1_SM.png
trees_bb1_SM_wi.png

trees_3D1_NML.png
trees_3D1_NML_fa.png
trees_3D1_NML_wi.png
trees_3D1_SM.png
```

Because the transplanted test tree was visibly malformed, its shadow behavior was considered inconclusive.

Do not use those broken transplanted-stock tests as evidence.

---

# 13. Native Laminar spruce control

The correct Laminar library export was found:

```text
$HOME/linGames/X-Plane 12/Resources/default scenery/1200 forests/library.txt
```

Export:

```text
EXPORT lib/vegetation/trees/coniferous/spruce_medium.for sum/tree_spruce_2.for
```

Therefore the canonical stock virtual resource is:

```text
lib/vegetation/trees/coniferous/spruce_medium.for
```

The vegetation DSF for `+58-069` was identified correctly:

```text
scenery/Ullaaq_Nunavik_Vegetation/Earth nav data/+50-070/+58-069.dsf
```

The other same-tile overlay DSFs are separate:

```text
scenery/Ullaaq_Nunavik_Buildings/Earth nav data/+50-070/+58-069.dsf
scenery/Ullaaq_Nunavik_Roads/Earth nav data/+50-070/+58-069.dsf
scenery/Ullaaq_Nunavik_RoadSurfaces/Earth nav data/+50-070/+58-069.dsf
```

The Vegetation DSF decompiled as:

```text
0 ter
0 obj
1 pol
0 net
```

Its sole forest definition was:

```text
POLYGON_DEF lib/ullaaq/forests/tam_test.for
```

For the native control, that definition was temporarily replaced directly with:

```text
POLYGON_DEF lib/vegetation/trees/coniferous/spruce_medium.for
```

This bypassed all custom resource-library transplant issues and forced X-Plane to resolve Laminar's spruce from its native installed package.

Result:

> **Blinkage remained.**

This was strong evidence that the behavior was not specific to the Northern Trees asset.

---

# 14. Final control: completely unmodified scenery at KTAN

The final test moved away from Ullaaq entirely.

Location:

```text
KTAN
Taunton Municipal Airport
```

The scenery there was left completely unmodified.

Result:

> **The same shadow blink / cycling behavior was observable in stock X-Plane scenery.**

This is the decisive control.

At this point the custom Larix tree, custom vegetation DSF, custom forest resource, custom atlas, and custom scenery package are all removed from the causal chain.

---

# 15. Shadow ticket closed

Final evidence chain:

```text
custom Larix tree                 -> blink
opaque Larix 3D atlas             -> blink
simple closed cone regression tree-> blink
native Laminar spruce             -> blink
completely unmodified KTAN scenery-> blink
```

Conclusion:

> **Tree-shadow blink is X-Plane rendering-engine behavior, not a Northern Trees bug.**

The exact internal mechanism was not proven and does not need to be reverse-engineered for the project.

The observed close/distant difference is consistent with some form of shadow-distance optimization / lower-resolution shadow representation, but that mechanism remains an inference rather than a project requirement.

Practical interpretation:

X-Plane is designed primarily to render scenery from a moving aircraft viewpoint. Some shadow behavior that becomes conspicuous when a free camera is parked close to one tree and watched carefully may be visually acceptable during normal flight.

Project policy:

```text
do not modify Larix geometry to fix this
do not disable shadows merely to hide it
do not spend further asset-development time on it
do not treat it as a regression in Northern Trees
```

Ticket:

```text
TREE SHADOW BLINK
STATUS: CLOSED
DISPOSITION: X-PLANE ENGINE BEHAVIOR
ASSET-SIDE FIX: NONE
```

---

# 16. Diagnostic DSF work and restoration

Repo-local DSFTool was used:

```text
~/linGames/Ullaaq-Air-Nunavik/DSFTool
```

The correct vegetation DSF:

```text
scenery/Ullaaq_Nunavik_Vegetation/Earth nav data/+50-070/+58-069.dsf
```

was backed up before native-stock substitution as:

```text
+58-069.dsf.pre-stock-spruce-test
```

After testing, the vegetation DSF was restored.

Verification after restoration:

```text
24:POLYGON_DEF lib/ullaaq/forests/tam_test.for
```

---

# 17. Live forest library chain restored

During diagnostics, `library.txt` was temporarily redirected to the cone and transplanted stock spruce resources.

The live chain has now been restored.

Verified `library.txt` line:

```text
EXPORT lib/ullaaq/forests/tam_test.for forests/ullaaq_larix_laricina_test.for
```

Verified Vegetation DSF definition:

```text
POLYGON_DEF lib/ullaaq/forests/tam_test.for
```

Therefore the live resource chain is again:

```text
+58-069 Vegetation DSF
        |
        v
lib/ullaaq/forests/tam_test.for
        |
        v
scenery/Ullaaq_Nunavik_Resources/library.txt
        |
        v
forests/ullaaq_larix_laricina_test.for
        |
        v
current custom Tamarack
```

This is the intended state for the next session.

---

# 18. Temporary diagnostic debris

A temporary transplanted stock-spruce tree was created under:

```text
scenery/Ullaaq_Nunavik_Resources/forests/stock_spruce_test/
```

It is no longer part of the live resource chain.

It may be deleted after one final in-engine confirmation that the restored Tamarack appears normally.

The `.pre-stock-spruce-test` vegetation DSF backup can likewise be retained through the end of the current workday and removed later once the restored state is confirmed.

The old neon cone remains useful as a permanent regression fixture:

```text
forests/ullaaq_tam_test_.for
```

Do not delete the cone fixture merely because today's diagnostic use is finished.

---

# 19. Northern Trees status carried forward

The production direction established earlier remains valid:

> Generate the runtime tree natively as a low-poly card tree. Do not require the million-triangle botanical tree as an intermediate deployment asset.

Current baseline remains approximately:

```text
26 crown tiers
3 folded sprays / tier
78 furnished-branch units
2 triangles / furnished branch
156 foliage triangles
+ cheap leader / trunk geometry
```

The current Tamarack has successfully passed:

```text
procedural generation
Blender realization
custom .for export
custom atlas mapping
library export
VEG_NORD vegetation-overlay placement
X-Plane rendering
shadow-regression investigation
```

The asset pipeline is therefore no longer under suspicion.

The next work is artistic / morphological refinement rather than pipeline rescue.

---

# 20. Next Tamarack work

Next session should return to the Tamarack itself.

Priority areas:

```text
whole-tree silhouette
crown taper
branch-tier spacing
branch/card density
LOW / MID / TOP crown habits
upper-crown character
branch length variation
card width / furnished-branch fullness
trunk visibility
tree-height calibration
individual-tree variation
atlas color/value balance
in-engine read at normal flight distances
```

The current rough atlas has already proven the mapping concept.

The next goal is not merely to make a technically valid tree.

The goal is to make the tree read convincingly as a northern Tamarack in the actual Nunavik landscape.

---

# 21. XP12 vegetation material work remains later

Laminar's spruce comparison showed the richer production shader stack:

```text
TEXTURE_NORMAL
WEATHER
BLEND_HASH 0.5
SUPER_ROUGHNESS 1.0
NORMAL_TRANSLUCENCY
```

Our current Tamarack shader is intentionally simpler.

These features should be revisited once morphology and atlas appearance are satisfactory.

Do not confuse:

```text
material incompleteness
```

with:

```text
shadow blink
```

Today's stock controls proved the blink exists independently of the custom material.

A sensible sequence is:

```text
1. get Tamarack form right
2. get atlas appearance right
3. validate normal flight-distance read
4. then add / tune the full XP12 material stack
```

---

# 22. RmC ground finalization is deliberately parked

Do not spend the next session polishing the ground.

The full-stock-stack experiment already answered the engineering question.

Known eventual work:

```text
restore custom RmC BASE art
author custom COMPOSITE companion
tune COMPOSITE_PARAMS if necessary
retain / replace appropriate natnoise
select or author suitable close decal
evaluate tree-ground palette together
```

Reason for deferral:

> The finished Tamarack will materially affect how the forest floor should be graded and detailed.

Ground and tree should ultimately be tuned as one visual system.

---

# 23. Do not redo / do not regress

Do not reopen the following without new evidence:

```text
Larix alpha as cause of shadow blink
Larix folded-card topology as cause of shadow blink
single 0-500 m 3D mesh as cause of shadow blink
custom vegetation DSF as cause of shadow blink
custom scenery package as cause of shadow blink
```

All were overtaken by the native-stock / KTAN controls.

Do not "fix" the blink by degrading the asset.

Do not remove shadows as a production workaround merely because `NO_SHADOW` eliminates the symptom.

Do not restart the ground-material diagnosis from projection scale. `PROJECTED 1673` is physically reasonable and matches the stock conifer macro scale.

Do not mistake the unfinished `RmC` `.ter` recipe for a bad orthophoto source.

Do not rebuild terrain geometry, hydro, or the base mesh for these texture/forest issues.

Continue to use the repo-local DSFTool:

```text
~/linGames/Ullaaq-Air-Nunavik/DSFTool
```

---

# 24. Resume point

At the beginning of the next session:

1. Confirm the restored Tamarack is visible in `+58-069`.
2. Remove temporary stock-spruce diagnostic resources only after that confirmation.
3. Leave the RmC ground material alone for now.
4. Resume visual refinement of the Tamarack.
5. Judge changes primarily from the normal X-Plane use case, not from pathological free-camera shadow inspection.
6. Once tree form and atlas appearance are strong, revisit the proper XP12 normal / translucency / weather material stack.
7. Finalize the RmC BASE + COMPOSITE + DECAL system only after the tree is visually settled.

---

# 25. End-of-session posture

Today began with two suspicious rendering symptoms that appeared close enough together to suggest a common cause.

They were successfully separated.

Ground issue:

```text
CAUSE:
unfinished custom .ter stack

STATUS:
understood, deferred
```

Shadow issue:

```text
CAUSE:
X-Plane stock rendering behavior

STATUS:
closed
```

Northern Trees itself exits the session in good standing.

The correct next move is therefore uncomplicated:

> **Keep building the Tamarack.**
