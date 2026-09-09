# NUNAVIK PROJECT STATE — 2026-09-09

## Session summary

Major Northern Trees debugging and tooling session. The project crossed an important threshold today: **the first custom Ullaaq Nunavik forest is now planted and rendering in X-Plane through an automated XPlaneForExporter pipeline.**

The session began with a badly malformed card-tree render left over from the 2026-09-08 test: branches were bunched to one side, giant black wedges appeared across the forest, illumination was unstable, and the final cause was unclear because both source geometry and export tooling were still evolving.

By the end of the session:

```text
procedural Geometry Nodes tree
        -> realized export mesh
        -> standardized XPlaneForExporter hierarchy
        -> real billboard object
        -> exporter materials/settings
        -> trunk UV bake into shared atlas
        -> patched XPlaneForExporter
        -> validated .for
        -> live X-Plane forest
```

The remaining visible problem is **shadow blinking/flicker**. A no-shadow diagnostic eliminates the visible blinking, so the issue is now isolated primarily to the shadow-rendering path. It remains open because the terrain imagery is also currently not rendering at full expected resolution, and the relationship between those two problems is not yet established.

The next Northern Trees task should move away from plumbing and back toward **tree mesh design**, using the stock Laminar spruce as the topology reference.

---

## Major milestone: first Ullaaq forest planted

The current larch/tamarack test forest now renders successfully in X-Plane with:

- correct 3-D card geometry
- correct card facing/winding
- foliage atlas mapping
- trunk present at correct physical dimensions
- trunk bark mapped into the shared atlas
- working distance transition to billboard trees
- automated `.for` generation through XPlaneForExporter
- forest placement through the existing VEG_NORD/X-Plane scenery path

This is the first point at which the Northern Trees system can reasonably be described as an end-to-end runtime vegetation pipeline rather than a collection of disconnected proofs.

---

# 1. Mesh topology findings

## 1.1 The folded furnished-branch primitive is still the correct basic unit

The basic runtime foliage primitive remains a folded two-triangle furnished-branch card.

Current primitive topology:

```text
vertices:
    0 = branch root / basal point
    1 = branch tip
    2 = upper wing
    3 = lower wing

normal Blender source faces:
    (0, 1, 2)
    (3, 1, 0)
```

The shared root-tip edge is the branch axis.

The stock Laminar spruce comparison had already measured a representative fold at approximately:

```text
109.93 degrees
```

which independently validates the current nominal Northern Trees fold of:

```text
110 degrees
```

The important new result today is that **fold orientation matters just as much as fold angle**.

---

## 1.2 Fold orientation: the fold must face upward

Earlier Northern Trees variants generated a valid 110-degree folded card but oriented the fold sideways around the branch axis.

In X-Plane this produced severe apparent geometry failure: the triangles appeared to collapse or bunch toward one side of the tree.

Comparison against the stock spruce showed that Laminar's folded sprays are oriented with the fold opening/ridge facing upward.

Diagnostic variants rotated the entire existing card around its local root-tip axis. The successful orientation was the equivalent of approximately:

```text
-90 degrees around the local branch +X/root-tip axis
```

Once the intact folded card was rotated into this upward-facing orientation, the gross one-sided branch bunching disappeared and the tree again read as a tree.

Production lesson:

> The card should be generated as a coherent folded spray and then oriented as a unit around the root-tip axis. Do not redesign the primitive to force an up-fold; rotate the known-good primitive.

---

## 1.3 Winding: do not reverse the source cards when using XPlaneForExporter

A major diagnostic trap was discovered.

During debugging of the hand-written direct `.for` exporter, a source variant was created with reversed foliage winding:

```text
v1.0i — UPFOLD + REVERSED WINDING TEST
```

This became wrong once the project returned to the real XPlaneForExporter.

Inspection of the add-on source showed that XPlaneForExporter deliberately reverses Blender's winding during serialization:

```text
Blender CCW
    -> exporter iterates triangle corners in reverse
    -> X-Plane CW
```

Therefore reversing the source mesh as well caused a **double reversal**.

Runtime symptoms with the double-reversed source included:

- foliage visible from ground-level angles
- foliage disappearing from above
- shadows still present when the visible branch triangles vanished
- incorrect or very dark illumination

Restoring the original Blender winding:

```text
(0, 1, 2)
(3, 1, 0)
```

immediately restored correct above/below rendering and normal-looking illumination.

Production rule:

> Northern Trees source geometry must use normal Blender winding. XPlaneForExporter owns the Blender-to-X-Plane winding conversion.

The reversed-winding generator variant should be retained only as a historical diagnostic, not as a production basis.

---

## 1.4 Current diagnostic tree topology

The current test tree was intentionally simplified during diagnosis so that renderer problems were easier to see.

Current diagnostic structure:

```text
12 tiers
3 branches/cards per tier
fixed azimuth pattern
no tier clocking / no helical rotation
upward-facing folded sprays
wind frozen
```

The realized current mesh reported:

```text
208 Blender vertices
134 faces
196 triangles
```

The triangle count breaks down consistently with the intended simplified geometry:

```text
12 tiers × 3 sprays × 2 triangles = 72 foliage triangles
remaining triangles = leader/trunk geometry
```

This is a debugging tree, not the intended final tamarack topology.

---

## 1.5 Stock Spruce02 remains the production topology reference

The stock Laminar spruce inspection is now more important than ever because the basic export/render pipeline is functioning.

Relevant stock findings retained for the next stage:

### Main `3D_spruce_02` mesh

Approximately:

```text
508 triangles total
```

A useful decomposition from inspection was roughly:

```text
~162 folded two-triangle spray units  -> ~324 triangles
~122 additional single-triangle facets
~62 woody/trunk triangles
```

### Close `lod_spruce_02` mesh

Adds approximately:

```text
324 triangles
≈ 162 additional two-triangle spray units
```

inside the close LOD range.

Therefore the stock tree is not simply a collection of identical folded two-triangle cards. Its crown combines:

- folded two-triangle sprays
- additional single facets/planes
- woody structure
- an extra close-range foliage mesh

The stock crown is also **irregularly distributed around the full 360 degrees** rather than following a visually obvious helix.

A previous top-view comparison showed Northern Trees' regular tier clocking much more clearly than the stock spruce. That regularity should now be reduced.

---

## 1.6 Next topology target

The next mesh-design session should move the runtime tree closer to the stock spruce grammar rather than merely increasing card count.

Priority questions:

1. How are Laminar's extra single-triangle facets positioned relative to each folded spray?
2. Which of those facets are effectively upper/lower coverage surfaces for the furnished branch?
3. How much additional coverage does the close 0–100 m mesh provide?
4. How irregular is the azimuth distribution within each height band?
5. How much branch-card scale variation exists within a single crown zone?
6. How does Laminar avoid a visible procedural helix while still using a compact texture vocabulary?
7. Which topology features matter most when viewed from above, where aviation scenery exposes weaknesses mercilessly?

The goal is not to copy the spruce literally. It is to adopt the parts of its topology that solve known rendering/view-coverage problems while preserving tamarack morphology.

---

# 2. Direct `.for` exporter debugging

## 2.1 Why the direct exporter was built

Repeated manual export through Blender/XPlaneForExporter had become too slow for rapid renderer debugging.

A direct `.for` writer was created to:

- evaluate the Geometry Nodes tree
- triangulate it
- write `MESH`, `VERTEX`, and `IDX` directly
- package textures
- provide a fast one-button debugging loop

Several versions were useful diagnostically:

```text
v0.3  success/failure popup + persistent log
v0.4  frozen wind
v0.5  geometric face normals
v0.6  mesh-part isolation: FOLIAGE / TRUNK
```

The direct exporter was valuable because it made binary isolation tests extremely cheap.

---

## 2.2 Giant black wedges isolated to the trunk path

The malformed tree initially showed huge black wedges/strips extending many metres from each tree.

A series of tests eliminated several hypotheses:

### Billboard test

The billboard texture was replaced with a fully transparent image.

Result:

```text
no change
```

Therefore the wedges were not the mandatory final 2-D billboard.

### Mesh `NO_SHADOW`

Normal tree shadows disappeared, but the giant wedges remained.

Result:

```text
wedges were not ordinary shadows cast by the 3-D mesh
```

### Foliage-only export

The direct exporter was modified to export only polygons using the foliage material.

Result:

```text
foliage rendered without the giant wedges
```

### Trunk-only export

The same exporter emitted only the trunk material polygons.

Logged trunk dimensions were completely sane:

```text
124 triangles
372 exported vertices
X = -0.0364 .. +0.0364 m
Y = approximately 0 .. 3.0004 m vertical
Z = -0.0364 .. +0.0364 m
```

Yet X-Plane produced the giant wedges.

Therefore the source trunk itself did not contain multi-metre geometry.

---

## 2.3 Synthetic trunk control

A completely independent synthetic `.for` writer generated a simple square trunk:

```text
height: 3.0 m
width: 0.08 m
4 sides
8 triangles
wind: 0
NO_SHADOW
```

X-Plane rendered a clean forest of narrow vertical sticks.

This proved that:

- basic `.for` syntax was valid
- X-Plane could render a simple direct-written trunk correctly
- coordinate scale was sane
- `MESH` / `VERTEX` / `IDX` syntax was fundamentally usable

However, because the procedural trunk had previously rendered correctly through XPlaneForExporter, the production conclusion was not to continue reverse-engineering the direct writer.

The exact reason the procedural trunk became wedges through the hand-written path was **not conclusively pinned down**.

---

## 2.4 Production decision: direct writer becomes diagnostic-only

The direct writer exposed too many low-level details that XPlaneForExporter already handles correctly:

- coordinate conversion
- triangle winding reversal
- split normals
- UV splits
- serialized vertex-table construction
- vertex-group wind weights
- mesh-property serialization
- forest hierarchy semantics
- material/shader directives

Decision:

> Keep the direct `.for` writer as a diagnostic instrument, but do not make it the production Northern Trees exporter.

The production path now automates the known-good patched XPlaneForExporter instead.

---

# 3. What we learned about XPlaneForExporter

## 3.1 Export operator

The installed add-on is:

```text
io_scene_xplane_for
```

The real export operator is:

```text
bl_idname: export.xplane_for
class: EXPORT_OT_XPlaneFor
module: io_scene_xplane_for.forest_export
```

It is scriptable as:

```python
bpy.ops.export.xplane_for(filepath=...)
```

The exporter writes one or more `.for` files discovered from the current scene hierarchy.

---

## 3.2 Forest hierarchy contract

Inspection of the exporter source established the actual hierarchy rules.

Every visible **top-level collection** in the scene is treated as a potential forest root.

A valid forest root contains child collections whose names begin with:

```text
<int><space>
```

For example:

```text
01 Trees
```

Inside each layer collection, valid tree containers are:

```text
EMPTY objects
with children
with no parent of their own
visible in the current view layer
```

Current generated hierarchy:

```text
__NTXP_LARIX_FOREST__
└── 01 Trees
    └── __NTXP_LARIX_LARICINA_TEST__      [EMPTY]
        ├── __NTXP_LARIX_BILLBOARD__      [vertical rectangle]
        └── __NTXP_LARIX_3D__             [complex mesh]
```

Because all visible top-level collections are considered candidate forests, the builder temporarily excludes ordinary workshop/source collections while invoking the exporter, then restores their visibility state afterward.

---

## 3.3 How the exporter classifies tree children

The add-on does not require magic child names. It classifies geometry structurally.

### Vertical rectangle

A child mesh with:

```text
4 edges
rectangular geometry
vertical orientation
```

is treated as the required tree billboard.

The billboard material's `xplane_for.texture_path` supplies the 2-D forest texture.

Its UV rectangle determines the emitted `TREE` pixel coordinates.

### Horizontal rectangle

A rectangular horizontal child can become a `Y_QUAD`.

Northern Trees does not currently use one.

### Complex mesh

A child with more than one polygon that is not classified as a billboard becomes a 3-D complex object and is emitted as:

```text
MESH ...
...
MESH_3D <mesh-name>
```

This is the mechanism used for the current real tree.

---

## 3.4 Mesh settings live on the mesh datablock

The discovered `XPlaneForMeshSettings` fields are:

```text
lod_near
lod_far
wind_bend_ratio
branch_stiffness
wind_speed
no_shadow
```

Current diagnostic values are:

```text
LOD = 0 .. 500 m
wind_bend_ratio = 0
branch_stiffness = 0
wind_speed = 0
```

Wind remains intentionally frozen while geometry/rendering issues are isolated.

---

## 3.5 Tree-wrapper settings

The Empty tree container carries:

```text
weighted_importance
max_height
use_custom_lod
custom_lod
tree_group
```

Current values:

```text
weighted_importance = 1
max_height ≈ 3.0006 m
use_custom_lod = False
tree_group = 0
```

For a one-tree test layer, the exporter converts the relative weight to:

```text
frequency = 100
```

---

## 3.6 Forest-root settings

The root collection carries:

```text
spacing
randomness
cast_shadow
perlin density/choice/height switches
seasons
max LOD
skip-surface flags
output file_name
group weights
```

Current test forest values:

```text
spacing = (5, 5)
randomness = (1, 1)
Perlin features = off
seasons = off
choice groups = off
skip water = true
```

Shadows are currently being treated separately because of the open flicker issue.

---

## 3.7 Material settings

The exporter material property group includes:

```text
texture_path
texture_path_normal
texture_path_normal_ratio
texture_path_weather
has_luma_values
luma_values
blend_mode
no_blend_level
blend_hash_level
specular controls
bump controls
no_shadow
shadow_blend
normal_mode
```

For the current foliage path, `BLEND_HASH` remains the working alpha mode.

A test using:

```text
NO_BLEND 0.5
```

did **not** eliminate the blinking and, before the trunk UV bake existed, caused the trunk to disappear because it sampled transparent atlas regions.

Therefore the alpha mode is not currently considered the primary shadow-flicker cause.

---

## 3.8 What XPlaneForExporter does to the mesh

Current realized Blender tree:

```text
208 vertices
134 faces
196 triangles
```

Current XPlaneForExporter output:

```text
MESH vertex count = 292
index count = 588
triangles = 196
```

The increased serialized vertex count is expected because the exporter creates X-Plane vertices from combinations of:

```text
position
split normal / face normal
UV
wind-group weights
```

Vertices are split where those attributes differ and identical serialized vertices are then reused.

The exporter also performs the Blender-to-X-Plane coordinate conversion and reverses triangle winding.

This is precisely the kind of detail that should remain inside the known-good exporter rather than being reimplemented in Northern Trees.

---

# 4. Automated export-builder pipeline

## 4.1 Reason for automation

Manual XPlaneForExporter setup was becoming an iteration bottleneck.

A complete export requires more than pressing the exporter button:

- realize the procedural source
- create the forest hierarchy
- create and place the billboard object
- provide the billboard texture
- create/configure 3-D mesh children
- set forest properties
- set tree-wrapper properties
- set mesh LOD/wind/shadow settings
- set material texture/blend settings
- package textures
- export
- inspect the logger

Repeating those panel operations for every topology iteration would be slow and error-prone.

Decision:

> Northern Trees should own an automated X-Plane asset-build stage. XPlaneForExporter should remain the serializer at the end of that stage.

---

## 4.2 Builder v0.2 — first successful end-to-end export

`build_northern_tree_export_rig_v0.2.py` successfully automated:

```text
selected procedural tree
    -> evaluate/realize Geometry Nodes
    -> ensure active conventional UV map
    -> create clean generated forest collection
    -> create "01 Trees"
    -> create tree-wrapper Empty
    -> create vertical billboard quad
    -> create 3-D complex mesh child
    -> configure forest/tree/mesh/material properties
    -> copy atlas + billboard to resource texture directory
    -> temporarily hide other root collections
    -> invoke bpy.ops.export.xplane_for(...)
    -> validate emitted .for
```

Successful export log:

```text
Source: NORTHERN_TREE_CARD_NATIVE_V10I_UPFOLD_REVERSED_WINDING_TEST
Realized mesh: 208 verts, 134 faces, 196 tris
Tree height: 3.0006 m
Billboard physical width: 1.1438 m
UV layers: ['UVMap']

Operator result: ['FINISHED']
ForestLogger.log:
S000: Export finished without errors

Exported .for:
bytes = 31073
MESH tables = 1
VERTEX lines = 292
TREE lines = 1
```

Emitted directives included:

```text
SHADER_2D
SHADER_3D
SCALE_X 512
SCALE_Y 1024
SPACING 5 5
RANDOM 1 1
MESH 3D_larix_laricina_test 0 500 292 588 ...
TREE ...
MESH_3D 3D_larix_laricina_test
```

This is the production-path milestone of the session.

---

## 4.3 Active UV bug in first builder attempt

The first rig-builder attempt reached the real exporter but failed because the realized Blender mesh contained a UV layer without an active UV pointer.

XPlaneForExporter contains code equivalent to:

```python
mesh.uv_layers[eval_obj.data.uv_layers.active.name]
```

and assumes `.active` is not `None`.

The builder was updated to:

```text
verify a conventional UV layer exists
set active_index = 0 explicitly
verify the active UV again
```

The same validation is applied to the generated billboard.

This fix allowed the automated export to complete successfully.

---

# 5. Trunk atlas mapping

## 5.1 Why the trunk texture initially failed

The procedural generator already had a temporary Blender trunk-texturing system.

It generated semantic point attributes:

```text
ullaaq_trunk_u
ullaaq_trunk_v
```

with conceptual ranges:

```text
u = 0 .. 1 around the trunk profile
v = 0 .. 1 from root to tip
```

The Blender shader used those named attributes directly.

XPlaneForExporter does not serialize arbitrary shader-node attributes as texture coordinates. It reads the active conventional UV layer.

Therefore foliage exported correctly because branch cards already had real UVs, while the trunk did not.

---

## 5.2 Trunk UV bake added to export builder

`build_northern_tree_export_rig_v0.5_trunk_uv.py` adds a production export-stage bake.

The builder:

```text
realizes Geometry Nodes
identifies trunk polygons by trunk material
reads ullaaq_trunk_u/v point attributes
writes corresponding per-loop values into active UVMap
preserves foliage UVs unchanged
continues through XPlaneForExporter
```

The bark reservation in the 8192 master atlas is:

```text
width  = 256 px
height = 2048 px
```

therefore normalized atlas range:

```text
U = 0.00000 .. 0.03125
V = 0.75000 .. 1.00000
```

The bake also handles the circumference seam per polygon. A face crossing the profile seam is mapped as:

```text
0.75 -> 1.00
```

rather than interpolating backward:

```text
0.75 -> 0.00
```

because UVs are written on loops and can therefore split cleanly at the seam without modifying the physical mesh topology.

Runtime result:

> Trunk bark texture is now confirmed visible in X-Plane.

This should remain part of the production export builder.

---

# 6. Billboard state

The automated rig builder now creates and positions the required vertical billboard object automatically.

The current billboard texture is still the existing test asset:

```text
larix_laricina_billboard_test1.png
512 × 1024 RGBA
```

The current test crop produces the emitted `TREE` rectangle approximately:

```text
s = 0
t = 128
w = 512
h = 768
offset = 256
```

Billboards render correctly in X-Plane at distance.

Not yet automated:

> rendering/generating a new billboard texture directly from each generated procedural tree.

That remains an export-tool milestone after the mesh topology is improved.

---

# 7. Shadow blinking / renderer issue

## 7.1 Symptom

With shadows enabled, the tree/forest shows a repeated blinking or flickering state.

The effect is most obvious in the shadows rather than in the visible tree mesh itself.

Earlier in debugging, malformed geometry made it difficult to distinguish illumination, alpha, topology, and shadow problems. With the geometry now working, the remaining flicker can be treated separately.

---

## 7.2 Alpha-mode test

A diagnostic builder changed only the 3-D shader from:

```text
BLEND_HASH
```

to:

```text
NO_BLEND 0.5
```

Result:

```text
blinking remained
```

The trunk also disappeared in that test because the trunk UV bake had not yet been implemented and hard alpha cutoff sampled transparent atlas areas.

Conclusion:

> The current blinking is not solved by replacing BLEND_HASH with a hard alpha cutoff.

---

## 7.3 No-shadow test

A subsequent diagnostic disabled both:

```text
forest-wide shadow casting
3-D mesh shadow casting
```

while returning to the known-good `BLEND_HASH` rendering path.

Result:

```text
no visible blinking
```

The visible tree geometry remained stable.

This strongly implicates the X-Plane shadow-rendering path rather than the core 3-D mesh.

However, the test is not enough to establish the underlying renderer cause.

---

## 7.4 Shadow issue remains OPEN

Shadows were manually re-enabled in the `.for` after trunk UV mapping was confirmed.

The current position is:

> Keep the shadow blinking issue open. Do not let it block topology work.

Potentially related observation:

- the underlying terrain imagery is currently not rendering at full expected resolution

It is plausible that terrain LOD, texture streaming, depth precision, or shadow projection behavior could interact visually with forest shadows, but **no causal connection has been established**.

The correct future experiment is to revisit shadow flicker once terrain rendering is itself known-good.

---

# 8. Current working pipeline

The recommended production/debugging pipeline is now:

```text
Northern Trees procedural generator
        |
        | normal Blender winding
        | upward-facing folded sprays
        | semantic trunk_u / trunk_v attributes
        v
Northern Trees export builder
        |
        | realize Geometry Nodes
        | ensure active UVMap
        | bake trunk attributes into atlas UVs
        | create clean export hierarchy
        | create billboard object
        | assign materials/settings
        | package textures
        v
patched XPlaneForExporter
        |
        | classify billboard / complex meshes
        | split normals and UV vertices
        | reverse winding for X-Plane
        | convert coordinates
        | serialize forest syntax
        v
Ullaaq_Nunavik_Resources/forests/*.for
        v
X-Plane
```

The hand-written direct `.for` exporter should remain available only for narrow diagnostics.

---

# 9. Important production rules established today

1. **Use normal Blender triangle winding.** XPlaneForExporter reverses it itself.
2. **Folded furnished-branch cards must be oriented upward around their root-tip axis.**
3. **Do not infer production topology from a debugging tree.** The current 12×3 tree is intentionally simplified.
4. **Use XPlaneForExporter as the production serializer.** Do not maintain a second complete `.for` implementation.
5. **Automate the scene preparation, not the serializer.**
6. **Every visible top-level Blender collection is a potential forest root.** Isolate the generated forest during export.
7. **Forest layer collections must begin with an integer and a space**, e.g. `01 Trees`.
8. **Tree containers are top-level Empties inside the layer collection with child geometry.**
9. **Vertical rectangular child = billboard. Complex multi-polygon child = MESH_3D.**
10. **Mesh LOD/wind settings live on the mesh datablock.**
11. **XPlaneForExporter requires an active conventional UV map.**
12. **Shader-only/named geometry attributes do not become X-Plane UVs automatically.** Bake them into `UVMap` first.
13. **Per-loop UVs are the correct place to solve trunk profile seams.**
14. **Keep wind frozen until geometry and rendering are stable.**
15. **Keep the shadow flicker separate from mesh topology work unless new evidence connects them.**

---

# 10. Files / scripts created or materially advanced today

Diagnostic direct-export path:

```text
export_northern_tree_for_v0.3.py
export_northern_tree_for_v0.4_frozen_wind.py
export_northern_tree_for_v0.5_flat_face_normals.py
export_northern_tree_for_v0.6_part_filter.py
write_synthetic_trunk_for.py
inspect_for_mesh.py
```

Exporter introspection:

```text
probe_xplane_for_exporter.py
probe_xplane_for_exporter_v0.2.py
probe_xplane_for_operator_details.py
probe_xplane_for_scene_rig.py
probe_xplane_for_schema.py
probe_xplane_for_nested_schema.py
probe_xplane_for_tree_contract.py
```

Production automation path:

```text
build_northern_tree_export_rig_v0.1.py
build_northern_tree_export_rig_v0.2.py
build_northern_tree_export_rig_v0.3_shadow_alpha_test.py
build_northern_tree_export_rig_v0.4_no_shadows_test.py
build_northern_tree_export_rig_v0.5_trunk_uv.py
```

Topology diagnostic patch:

```text
restore_card_winding_for_xplanefor.py
```

Current runtime output:

```text
scenery/Ullaaq_Nunavik_Resources/forests/
    ullaaq_larix_laricina_test.for
```

Current working art:

```text
work/Objects/Northern_Trees/Atlas/
    larix_laricina_atlas_test2.png
    larix_laricina_billboard_test1.png
```

---

# 11. Next session — mesh topology

Primary goal:

> Move the Northern Trees runtime mesh closer to the topology and view coverage of Laminar's stock spruce while preserving tamarack morphology.

Recommended sequence:

1. Return to `3D_spruce_02` and `lod_spruce_02` as topology references.
2. Classify every stock foliage primitive into useful categories:
   - folded two-triangle spray
   - isolated/supplementary single triangle
   - woody/trunk facet
   - close-LOD-only foliage
3. Inspect representative folded sprays together with neighboring single facets to determine their geometric relationship.
4. Determine whether the extra facets primarily provide:
   - top coverage
   - underside coverage
   - side coverage
   - silhouette breakup
   - branch-axis fill
5. Compare stock azimuth distribution against the current fixed three-branch diagnostic tree.
6. Replace obvious regular clocking with bounded irregular 360-degree placement.
7. Reintroduce a higher tier count gradually, using the earlier 26-tier tamarack baseline as the botanical target rather than jumping straight to maximum density.
8. Add the first supplementary facets/planes around selected furnished branches.
9. Export through `build_northern_tree_export_rig_v0.5_trunk_uv.py` or its next production successor.
10. Test specifically from:
    - ground level
    - low oblique aircraft view
    - directly above
    - medium 3-D LOD distance
    - billboard transition distance
11. Only after topology is convincing, design the close-range secondary mesh analogous to `lod_spruce_02`.
12. Keep wind disabled during this work.
13. Keep shadow flicker logged as a separate renderer issue.

The next design question is no longer "can X-Plane render our tree?"

It is:

> What is the cheapest topology that gives tamarack convincing volumetric coverage from the viewing angles an aircraft actually exposes?

---

## Stopping point

The session closes at a natural architectural boundary.

The difficult plumbing is now sufficiently automated that future iterations can focus on vegetation design rather than repeated exporter setup.

At end of 2026-09-09:

- the first Ullaaq Nunavik custom forest is planted
- the card fold orientation problem is solved
- the winding/export interaction is understood
- the giant trunk-wedge failure is bypassed by returning to XPlaneForExporter
- the exporter hierarchy contract is reverse-engineered
- exporter settings can be generated programmatically
- the complete `.for` build is automated
- the trunk is atlas-mapped through a real UV bake
- billboards work
- shadow flicker is isolated enough to remain an independent open issue
- the current topology is known to be only a diagnostic simplification
- the next development target is the stock-spruce-inspired runtime mesh

The Northern Trees project has moved from **pipeline discovery** into **mesh refinement**.
