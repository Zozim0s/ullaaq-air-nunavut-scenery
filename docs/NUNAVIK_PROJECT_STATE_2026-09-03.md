# NUNAVIK_PROJECT_STATE_2026-09-03

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

Repo-local DSFTool:

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

Current Blender vegetation prototype:

```text
~/linGames/Ullaaq-Air-Nunavik/work/Objects/Northern_Trees/Tamarack.blend
```

**Session result:** The first procedural northern-tree prototype was built interactively in Blender 5.2 Geometry Nodes. The prototype now produces a recognizable 3 m stunted conifer / tamarack skeleton with a tapered slightly irregular leader, bounded crown, repeated branch tiers, crown-width envelope, tapered primary branches, branch sag/recovery, and rotating whorl orientation. This proves the procedural morphology concept. The next step is not further manual node authoring: convert the known-good proof into a scripted, species-agnostic **Northern Trees** generator with human-readable parameters and eventually a small Blender UI.

---

## 1. Executive status

The project architecture remains:

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

The custom 3D vegetation export path proved on 2026-09-02 remains valid:

```text
Blender 5.2
    -> custom billboard + custom 3D mesh
    -> patched XPlaneForExporter
    -> custom .for
    -> Ullaaq library export
    -> VEG_NORD vegetation overlay
    -> repo-local DSFTool
    -> X-Plane 12
```

Today shifted the active problem again:

```text
custom vegetation export path       PROVEN
procedural tree morphology concept  PROVEN
manual Geometry Nodes workflow      TOO CUMBERSOME FOR PRODUCTION
scripted generic generator          NEXT
human-readable parameter UI         NEXT / AFTER SCRIPT CORE
```

---

## 2. Northern Trees tool: architectural direction

The intended end product is **not a tamarack generator**.

It is a species-agnostic procedural tool, provisionally:

```text
Ullaaq Northern Trees
```

The core generator should understand tree morphology rather than botanical species names.

Core morphology controls should eventually include:

```text
overall height
trunk / leader base diameter
trunk taper
leader crookedness / wander
crown start
crown end
crown-width envelope
branch-tier / whorl count
branches per tier
successive tier clocking
primary branch length
branch length envelope with height
branch departure / rise profile
branch sag and tip recovery
branch taper
branch irregularity
missing / extra branch probability
foliage distribution
seed
```

Species should be data / presets layered on top of the generic machinery:

```text
NorthernTreeGenerator
    -> species profile
    -> growth-form preset
```

Examples:

```text
species profile:
    tamarack
    black spruce

production growth-form preset:
    Tamarack_Stunted_3m
    Tamarack_Open_4m
    BlackSpruce_Sheltered_3m
    BlackSpruce_Exposed_1p5m
```

Important design conclusion:

> X-Plane ultimately needs believable growth forms, not a forestry taxonomy encoded in geometry code.

A single species may need several visually distinct growth-form presets depending on exposure, shelter, stand density, and ecological context.

---

## 3. First calibration organism: stunted tamarack

The first procedural calibration case remains a small northern tamarack / eastern larch.

Reference material supports a harsh-site / northern growth form around:

```text
height:         ~3 m
trunk diameter: ~8 cm
```

This happens to match the scale chosen independently for the prototype.

Current visual target:

```text
height             3.0 m
base trunk Ø        ~8 cm
crown start         ~0.6-0.7 m / ~22% of height
crown end           ~2.8 m / ~94% of height
primary tiers       ~13 in current proof
primary length      nominally ~0.55 m
leader              mostly straight, mildly irregular
crown               narrow, open, tiered
lower branches      nearly horizontal
middle branches     modestly ascending
upper branches      increasingly ascending
very top branches   approaching ~45 degrees upward
primary shape       shallow sag + recovered / rising tip
```

The exact numbers are not botanical requirements. They are a visual calibration target for a convincing X-Plane tree.

---

## 4. Procedural leader proof

The prototype began from Blender's default cube, which was retained as the Geometry Nodes host and renamed:

```text
TAMARACK_GEN
```

The original mesh output was replaced by generated geometry.

### Leader centerline

Initial centerline:

```text
Curve Line
Start: 0, 0, 0
End:   0, 0, 3 m
```

Initial trunk profile:

```text
Curve Circle
Resolution: 4
Radius:     0.04 m
```

This produced a deliberately cheap four-sided trunk suitable for X-Plane-scale testing.

### Blender 5.2 Curve to Mesh behavior

Important Blender 5.2 lesson:

`Set Curve Radius` does not by itself provide the expected taper through `Curve to Mesh` in the way initially assumed.

The working Blender 5.2 method was:

```text
Spline Parameter: Factor
    -> Map Range
       0..1 -> bottom scale..tip scale
    -> Curve to Mesh: Scale
```

For the trunk:

```text
Curve Circle radius: 0.04 m
bottom scale:        1.00   -> ~8 cm diameter
upper scale:         0.10
```

### Leader segmentation / crookedness

The leader was resampled:

```text
Resample Curve
Count: 9
```

Small lateral random displacement was added:

```text
Random Value Vector
X: -0.025 .. +0.025 m
Y: -0.025 .. +0.025 m
Z:  0
```

The displacement is multiplied by `Spline Parameter: Factor` before entering `Set Position`, so:

```text
root factor 0
    -> no displacement
    -> root remains planted at origin

upper leader
    -> increasing available lateral wander
```

The resulting leader is intentionally only mildly crooked.

### Leader smoothing

`Fillet Curve` was used after `Set Position` to soften the segmented wander.

Current proof used a Bézier fillet and visually acceptable radius; exact values are not yet production canon.

Conclusion:

> The leader needs only restrained imperfection. Most tamarack character comes from the crown and branch architecture.

---

## 5. Crown-station proof

The finished leader curve was split conceptually into:

```text
visible trunk path
    -> Curve to Mesh

crown-placement path
    -> Trim Curve
    -> Curve to Points
```

The crown zone was trimmed approximately:

```text
Start factor: 0.22
End factor:   0.94
```

The trimmed crown curve was converted into:

```text
Curve to Points
Count: 13
```

Diagnostic Ico spheres were initially instanced on the points to prove placement.

Once validated, the spheres were replaced by procedural branch whorls.

The `Trim Curve + Curve to Points` machinery was grouped into a reusable node group:

```text
CrownStations
```

---

## 6. Primary branch / whorl proof

The first branch prototype was deliberately simple:

```text
Curve Line
Start: 0, 0, 0
End:   0.55, 0, 0
```

Branch profile:

```text
Curve Circle
Resolution: 3
Radius:     0.012 m
```

This creates very cheap triangular-section primary limbs.

### Three-branch whorl

One primary branch mesh was copied through `Transform Geometry` at:

```text
0 degrees
120 degrees
240 degrees
```

and joined into one whorl.

That entire branch prototype was encapsulated as:

```text
Whorl3
```

Important interpretation:

> `Whorl3` is scaffolding / a useful base grammar, not a claim that tamarack always has exactly three branches exactly 120 degrees apart.

Later production variation should support roughly 2-4 strong primary branches, uneven azimuths, different lengths, occasional missing branches, and occasional additional shoots.

---

## 7. Primary branch shape

Straight primary branches looked too mechanical.

Inside `Whorl3`, the primary branch curve was resampled:

```text
Resample Curve
Count: 6
```

A `Set Position` stage applies a Z-offset generated from `Spline Parameter: Factor`.

### Sag

The first branch sag is generated with a `Float Curve` roughly shaped as:

```text
root      0
mid       maximum sag
outer tip 0
```

The normalized Float Curve is multiplied by approximately:

```text
-0.05 m
```

This produces a shallow ~5 cm sag through the middle of a nominal 55 cm primary branch.

### Baseline rise

A second path uses:

```text
Spline Parameter: Factor
    -> Multiply
       ~0.08 m
```

and adds the result to the sag curve.

Thus the nominal branch shape becomes:

```text
root:     0 rise
middle:   shallow sag / near-level
outer tip +~8 cm
```

This produced a much more convincing tamarack-like branch gesture than a straight stick.

### Branch taper

The same `Spline Parameter: Factor` is mapped to `Curve to Mesh: Scale`:

```text
root scale: ~1.0
tip scale:  ~0.12
```

This gives strong taper from primary branch root to tip.

---

## 8. Crown-width envelope

Uniform branch lengths produced a cylindrical radio-antenna silhouette.

The 13 crown stations were assigned a height-normalized parameter:

```text
Index
    -> Map Range
       0..12 -> 0..1
```

A `Float Curve` then controls whorl scale with a broad crown envelope.

Current visual intent:

```text
bottom crown        moderate width
lower-middle crown  maximum width
upper crown         rapidly narrowing
top                  very short branches
```

Approximate conceptual control points used during the experiment:

```text
crown factor 0.00 -> scale ~0.70
crown factor 0.35 -> scale ~1.00
crown factor 0.75 -> scale ~0.55
crown factor 1.00 -> scale ~0.20
```

This was a major improvement. The crown stopped reading as a cylinder and began to read as a narrow northern conifer.

---

## 9. Successive whorl clocking

All whorls initially had identical azimuth and therefore formed obvious vertical branch columns.

A simple deterministic clocking step was added:

```text
Index
    -> Multiply by ~0.646 radians
       (~37 degrees)
    -> Combine XYZ: Z
    -> Euler to Rotation
    -> Rotate Instances
```

Successive whorls therefore rotate approximately:

```text
0°
37°
74°
111°
148°
...
```

This broke up the ladder / cage effect very effectively while preserving clear tiering.

The exact 37° value is a visual device, not a botanical claim.

---

## 10. Upper-branch angle experiment: important failure / lesson

Reference silhouettes show that branch departure becomes progressively more ascending toward the crown top, with the highest branches approaching roughly 45° upward.

Two attempted ways of adding that behavior were rejected.

### Failure A: rotate the completed whorl around Y

Applying height-dependent Y rotation to the whole three-branch whorl caused:

```text
one radial branch -> upward
one radial branch -> roughly sideways
one radial branch -> downward
```

This is geometrically wrong for a radial whorl.

Rule:

> Do not create branch departure angle by tilting the completed whorl.

### Failure B: vertically stretch the completed whorl

Using anisotropic instance scale with increasing Z toward the top did steepen upper branches, but it exaggerated the sag/recovery shape into obvious hooked / U-shaped branches.

Rule:

> Do not create upper-crown branch attitude by vertically stretching the finished whorl.

### Correct direction

Branch rise / departure must be decided **inside the individual branch construction before radial copies are made**.

The `Whorl3` rise term was therefore exposed as a group input during the session.

The exact clean parameterization remains unfinished.

Likely next production solution should stay simple, e.g. crown zones:

```text
LOW
    nearly horizontal primary departure

MID
    modest ascending departure

TOP
    strongly ascending, approaching ~35-45°
```

A small number of discrete branch-habit recipes may be visually sufficient and much easier to maintain than a continuously deformed completed whorl.

---

## 11. Current Geometry Nodes organization

The graph was manually reorganized near session end to reduce noodle clutter.

Useful current conceptual groups:

```text
leader machinery
    -> finished trunk curve

CrownStations
    -> 13 crown points + local rotation

Whorl3
    -> generic three-primary-branch geometry

Instance on Points
    -> places Whorl3 on CrownStations

Rotate Instances
    -> successive whorl clocking around Z only

crown envelope
    -> controls whorl scale by height

Join Geometry
    -> trunk + crown
```

Even after cleanup, the node graph is already too complex for comfortable manual development.

That is the central workflow conclusion of the day.

---

## 12. Workflow decision: stop pushing noodles around

Manual Geometry Nodes authoring was valuable because it exposed the actual geometry and proved each mechanism interactively.

It is not the desired production authoring method.

Next step:

> Translate the current known-good procedural proof into Python which constructs and wires the Geometry Nodes graph reproducibly.

The script should become the source of truth for generator structure.

Geometry Nodes should remain visible and editable, but should be generated rather than hand-maintained.

Conceptual future API:

```python
NorthernTree(
    height=3.0,
    trunk_diameter=0.08,
    leader_wander=0.025,

    crown_start=0.22,
    crown_end=0.94,
    tier_count=13,

    branches_per_tier=3,
    primary_length=0.55,
    branch_radius=0.012,

    sag=0.05,
    rise=0.08,
    tier_clock_deg=37,

    seed=0,
)
```

Exact API is TBD.

---

## 13. Human-readable parameter interface

The scripted generator should expose meaningful named Geometry Nodes group inputs rather than raw anonymous values.

First useful interface can simply be the Geometry Nodes modifier panel itself.

Target parameter vocabulary:

```text
TREE
    Height
    Base Diameter
    Leader Crookedness
    Seed

CROWN
    Crown Start
    Crown End
    Tier Count
    Maximum Width
    Widest Point

BRANCHES
    Primary Length
    Branch Base Radius
    Sag
    Lower Rise / Habit
    Middle Rise / Habit
    Upper Rise / Habit
    Whorl Rotation Step

VARIATION
    Length Variation
    Angular Variation
    Missing Branch Probability
```

Later, a small custom Blender sidebar can provide a cleaner Ullaaq-specific interface.

Conceptual future panel:

```text
Ullaaq Vegetation

Species Profile:  Tamarack
Growth Form:      Stunted 3 m

Height            [ 3.00 ]
Crown Width       [ .... ]
Tier Count        [ 13   ]

Branch Habit
Lower             [ .... ]
Middle            [ .... ]
Upper             [ .... ]
Sag               [ .... ]

Variation
Seed              [ 17 ]
[ Randomize ]

[ Generate Variant ]
[ Bake Export Mesh ]
[ Render Billboard ]
```

Architecture principle:

```text
Python
    -> builds / maintains Geometry Nodes machinery

Geometry Nodes group inputs
    -> stable parameter API

optional Blender UI
    -> human-friendly controls
```

The UI should manipulate parameters, not contain the geometry-generation logic itself.

---

## 14. Future export integration

The longer-term Northern Trees tool can eventually automate the known X-Plane asset pipeline.

Potential flow:

```text
load species / growth-form preset
    -> choose / randomize seed
    -> generate tree variant
    -> realize instances / bake export mesh
    -> assign production materials
    -> render orthographic billboard from same source organism
    -> prepare XPlaneForExporter hierarchy
    -> export .for
```

Important existing rule from the 2026-09-02 proof:

> Billboard and near-field 3D mesh should derive from the same source model and physical dimensions.

This avoids the severe LOD size pop observed when stock billboard and stock 3D geometry did not represent the same northern-scale tree.

The current neon cone regression fixture should remain separate and unchanged as the exporter / X-Plane plumbing test.

---

## 15. Relation to VEG_NORD

The procedural asset generator must remain separate from GIS semantics.

VEG_NORD continues to provide:

```text
cl_carto
    -> ecological / ground family

cl_dens
    -> woody-cover density / packing semantics

ess_dom
    -> dominant-species recipe selection
```

The Northern Trees tool generates visual assets / variants.

The vegetation-overlay builder later decides which asset recipes to deploy in each polygon.

Do not manufacture new VEG_NORD classes merely to represent different procedural tree morphologies.

Possible future dispatch remains conceptually:

```text
RmC + ML
    -> dense tamarack-dominant stand recipe

RmL + ML
    -> sparse tamarack-dominant stand recipe

RmC + EN
    -> dense black-spruce-dominant stand recipe

RmL + EN
    -> sparse black-spruce-dominant stand recipe
```

Asset growth form and forest packing are rendering policy, not GIS taxonomy.

---

## 16. Seasonal consequence

The generic Northern Trees system supports the existing season-independent GIS architecture.

Example tamarack rendering policy:

```text
summer
    green foliage

fall
    yellow / gold foliage

winter
    bare branch structure

spring
    fresh light green foliage
```

Preferred architecture remains:

```text
one ecological GIS skeleton
    -> seasonal rendering policy / materials / asset variants
```

Do not duplicate GIS by season.

---

## 17. Current important paths

Project repository:

```text
~/linGames/Ullaaq-Air-Nunavik
```

Current procedural tree prototype:

```text
~/linGames/Ullaaq-Air-Nunavik/work/Objects/Northern_Trees/Tamarack.blend
```

Previous custom vegetation proof workspace:

```text
~/linGames/Ullaaq-Air-Nunavik/work/Objects/Test/Replacme_Tree.blend
```

Resource package:

```text
~/linGames/Ullaaq-Air-Nunavik/scenery/Ullaaq_Nunavik_Resources
```

Repo-local DSFTool:

```text
~/linGames/Ullaaq-Air-Nunavik/DSFTool
```

VEG_NORD reference tile:

```text
~/linGames/Ullaaq-Air-Nunavik/work/+58-069/landcover/+58-069_VEG_NORD_tile.gpkg
```

---

## 18. Suggested future source layout

Not yet implemented, but the scripted tool should probably live under a dedicated Blender tooling subtree, e.g.:

```text
tools/blender/northern_trees/
    generator.py
    profiles.py
    presets.py
    ui.py
```

Possible responsibility split:

```text
generator.py
    generic morphology / Geometry Nodes construction

profiles.py
    species-level architectural tendencies

presets.py
    production growth-form parameter sets

ui.py
    optional human-facing Blender panel
```

Keep the core generator independent of X-Plane export glue where practical.

---

## 19. Immediate next session

Primary objective:

> Build **Northern Trees v0.1** as a scripted, species-agnostic Geometry Nodes generator which reproduces the known-good parts of `Tamarack.blend`.

Recommended sequence:

```text
1. Preserve Tamarack.blend unchanged as the visual / node prototype.

2. Create initial Python tooling under a Northern Trees source directory.

3. Script creation of a fresh Geometry Nodes group.

4. Reproduce the leader:
       3 m line
       taper
       9-point resample
       restrained X/Y wander
       planted root
       smoothing

5. Reproduce CrownStations:
       crown start / end
       tier count
       point orientation

6. Reproduce generic whorl geometry:
       branches per tier
       nominal primary length
       branch taper
       sag / recovery
       baseline rise

7. Reproduce crown envelope and successive tier clocking.

8. Expose named group inputs.

9. Confirm editing those inputs in the Geometry Nodes modifier updates the tree live.

10. Only after the scripted version reproduces today's silhouette, continue morphology work:
       low / mid / upper branch-habit zones
       irregular branch count / spacing
       length variation
       secondary branchlets
       foliage cards
```

Do not manually continue adding substantial node machinery to `Tamarack.blend` before the scripted reproduction exists.

---

## 20. Things explicitly not to forget

- `Tamarack.blend` is the current hand-built procedural-tree proof:

```text
~/linGames/Ullaaq-Air-Nunavik/work/Objects/Northern_Trees/Tamarack.blend
```

- The concept is proven: Geometry Nodes can generate a recognizable northern-conifer skeleton at the required physical scale.
- The target tool is **Northern Trees**, not a species-specific tamarack script.
- Species belong in profiles / presets, not generator branching logic where avoidable.
- Growth-form presets are at least as important as nominal species.
- Keep the leader only mildly irregular.
- Crown silhouette carries much of the species / growth-form read.
- Repeated branch tiers are useful, but perfect identical 120° whorls are scaffolding, not final biology.
- Successive whorl clocking around the trunk works well and cheaply.
- Branch sag + recovered / rising tip is visually important.
- Branch taper is cheap and necessary.
- Crown-width envelope is a high-value control.
- Do not tilt completed whorls around Y to create branch departure.
- Do not vertically stretch completed whorls to create upper-branch angle.
- Upper branch attitude should originate in branch construction before radial copies are made.
- The current graph already demonstrates why manual Geometry Nodes maintenance will not scale.
- Python should create / maintain the graph.
- Named Geometry Nodes inputs can provide the first human-readable UI.
- A custom Blender sidebar can come later.
- Keep billboard and 3D mesh derived from the same generated tree.
- Preserve the neon-green cone forest as a separate regression fixture for the export pipeline.
- Use repo-local `./DSFTool` for DSF compile/decompile work.

---

## 21. Current project posture

The project has crossed two successive vegetation thresholds in two days:

```text
2026-09-02
    custom 3D vegetation export / X-Plane rendering path proven

2026-09-03
    procedural northern-tree morphology path proven
```

The remaining problem is no longer whether Ullaaq can create its own tree assets.

It can.

The next problem is engineering the authoring system so that creating and tuning those assets is fast, reproducible, understandable, and reusable across species and northern growth forms.

The correct next move is therefore:

> **Turn today's hand-built Geometry Nodes specimen into the scripted, parameterized, species-agnostic Northern Trees tool.**
