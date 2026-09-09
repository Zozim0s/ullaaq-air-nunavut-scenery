# NUNAVIK PROJECT STATE — 2026-09-06

## Session summary

Short but productive Northern Trees session. The project moved from being blocked by the million-triangle botanical tamarack to a proven Laminar-style runtime workflow using a cheap woody leader plus folded, alpha-textured furnished-branch sprays.

The main result is architectural: the high-poly botanical generator remains useful as a source-art and biological reference system, while the runtime tree can be generated directly from a small vocabulary of branch-spray archetypes. We no longer need to treat the million-triangle tree as a required precursor to deployment geometry.

---

## Stock X-Plane spruce autopsy

Continued forensic analysis of Laminar's default spruce:

```text
~/linGames/X-Plane 12/Resources/default scenery/1200 forests/sum/tree_spruce_2.for
```

Relevant meshes:

```text
3D_spruce_02   0–500 m   1088 verts   1524 indices   508 tris
lod_spruce_02  0–100 m    648 verts    972 indices   324 tris

3D_spruce_11   0–500 m    929 verts   1302 indices   434 tris
lod_spruce_11  0–100 m    568 verts    852 indices   284 tris
```

Thus the close-range budgets are approximately:

```text
spruce_02: 832 tris inside 100 m, 508 tris from 100–500 m
spruce_11: 718 tris inside 100 m, 434 tris from 100–500 m
```

The close meshes decompose cleanly into repeated four-vertex, two-triangle foliage units:

```text
spruce_02 close: 648 verts / 4 = 162 spray units
spruce_11 close: 568 verts / 4 = 142 spray units
```

Most foliage units use a standardized folded two-triangle primitive. Four of the five sampled motifs had a face-normal separation of approximately 110 degrees:

```text
109.91°
109.95°
109.94°
109.93°
```

A specialized upper-crown motif used a 90-degree fold.

### Atlas reuse

The 162 close-range spruce_02 sprays use only five UV boxes:

```text
57x  (0.3125, 0.890625, 0.375, 0.921875)
53x  (0.375, 0.890625, 0.5, 0.953125)
41x  (0.40625, 0.953125, 0.5, 1.0)
 7x  (0.3125, 0.921875, 0.375, 0.953125)
 4x  (0.421822, 0.953125, 0.5, 0.992135)
```

The top three motifs account for 151 of 162 sprays (93.2%).

Physical/positional behavior suggests a graded branch vocabulary rather than rigid crown zones:

```text
large drooping spray:
    median span ~1.64 m
    median inclination proxy ~-37°
    overwhelmingly lower/middle crown

medium/general spray:
    median span ~1.17 m
    broadly distributed

small/rising spray:
    median span ~0.83 m
    increasingly important aloft

special top spray:
    7/7 occurrences in uppermost crown
    90° fold
```

Conclusion: Laminar's spruce is built from a very small vocabulary of furnished branch images mapped onto cheap folded geometry, with selection, scale, orientation, and crown position doing most of the work.

---

## Generator file lineage checked

Compared the current/downloaded generator variants.

Canonical botanical master:

```text
generator.py
generator_v0.4a(4).py
```

These are code-identical apart from final newline state. No unsaved changes were lost.

Experimental branches:

```text
generator_v0.4b_export_cards(2).py
    per-foliage-station crossed-card experiment
    now conceptually superseded

generator_v0.4c_spray_source(1).py
    projection-friendly furnished MID branch source

generator_v0.4c_mid_card_proof(1).py
    same spray-source experiment plus hand-fitted planar card proof
```

The botanical v0.4a remains the correct source/reference trunk.

---

## Runtime spray proof

Fresh runtime branch created from v0.4a logic.

Preserved:

```text
leader/trunk generation
crown stations and spacing jitter
LOW/MID/TOP branch habit
tier clocking
deterministic branch length and azimuth variation
crown envelope
```

Removed from runtime representation:

```text
primary branch tubes
secondary long-shoot geometry
short-shoot geometry
modeled needle rosettes
```

Each primary branch is represented by one Laminar-style folded spray:

```text
4 vertices
2 triangles
~110° fold
```

Default tree:

```text
13 tiers × 3 branches = 39 sprays
39 × 2 = 78 spray triangles
```

After realizing Geometry Nodes instances, evaluated mesh count:

```text
V:    220
F:    140
Tris: 202
```

Breakdown:

```text
leader:         124 tris
branch sprays:   78 tris
-------------------------
runtime tree:   202 tris
```

This is the key breakthrough of the session. The million-triangle botanical tree and the 202-triangle runtime tree can coexist as different representations of the same procedural growth grammar.

Runtime proof scripts created:

```text
generator_v0.5a_runtime_spray_proof.py
generator_v0.5b_runtime_spray_realized.py
```

---

## UV atlas proof

Built a three-cell diagnostic atlas and mapped LOW/MID/TOP spray classes to separate UV islands.

Diagnostic result:

```text
LOW -> warm/orange cell
MID -> green cell
TOP -> blue cell
```

A white diagonal marker across each cell confirmed that the shared root-to-tip fold edge remains continuous across both triangles.

This proved the complete mapping chain:

```text
branch habit
    -> spray archetype
    -> UV island
    -> shared atlas material
```

Script:

```text
generator_v0.6a_uv_atlas_proof.py
```

---

## Botanical MID source render

Reused the v0.4c spray-source concept as an offline source-art generator.

Generated one projection-friendly furnished MID branch with:

```text
brown diagnostic wood
green diagnostic needles
transparent background
orthographic capture
```

The first render included stray scene geometry; this was fixed by isolating the source branch during rendering.

Clean source image:

```text
renders/tamarack_mid_spray_source.png
```

Source-render scripts:

```text
generator_v0.7a_mid_source_render.py
generator_v0.7b_mid_source_render.py
generator_v0.7c_mid_source_render_isolated.py
```

The clean source sprite retains the primary branch, secondary long shoots, and needle clusters clearly enough to serve as runtime artwork.

---

## First real textured runtime spray

Integrated the rendered MID branch into the runtime atlas while leaving LOW and TOP as diagnostic colors.

Scripts:

```text
generator_v0.8a_mid_texture_atlas_proof.py
generator_v0.8b_mid_texture_autoalign.py
generator_v0.8c_mid_texture_root_anchor.py
```

The source branch initially crossed the folded geometry at the wrong angle. Auto-alignment improved this, and root/tip anchoring then placed the rendered branch root directly at the trunk attachment point.

Current state:

- MID furnished-branch artwork is visibly attached to the trunk.
- Alpha transparency works.
- The folded two-triangle representation works.
- Some rendered needle/secondary areas appear pale or grey.
- LOW/TOP remain diagnostic geometry in the current proof and should not be mistaken for missing texture.
- Grey/pale MID detail is not catastrophic and is likely a source-art/material/filtering issue rather than a fundamental geometry or UV failure.

No need to solve this immediately. The workflow itself is now proven.

---

## Current architectural decision

Northern Trees should support two representations:

### Botanical/source representation

High-detail procedural branch/tree geometry used for:

- species morphology development
- furnished-branch sprite generation
- whole-tree billboard generation
- possible bespoke mid/high-detail scenery assets

### Runtime forest representation

Direct low-poly generation using:

- cheap leader/trunk
- small vocabulary of furnished-branch spray archetypes
- folded two-triangle spray geometry
- atlas UV selection
- crown-position-dependent scaling/orientation/selection
- whole-tree billboard at long range

The botanical million-triangle model is no longer a deployment bottleneck because it is not required to exist as the runtime asset.

---

## Next session

Recommended next steps:

1. Temporarily apply the MID sprite to all spray classes to inspect the 202-triangle tree without diagnostic LOW/TOP colors.
2. Determine whether pale/grey foliage is caused primarily by source rendering, alpha filtering, or double lighting.
3. Try a flat/emissive diagnostic runtime material and/or stronger source colors.
4. Once the MID representation reads cleanly, generate proper LOW and TOP furnished-branch source sprites.
5. Assemble a real tamarack branch atlas.
6. Test the complete low-poly tamarack in X-Plane.
7. Later add billboard LOD and, only if justified, close-only underside/detail geometry.

---

## Stopping point

Major workflow proof completed.

The project began the session effectively blocked by a ~1.17 million-triangle procedural tamarack. It ends with a 202-triangle runtime tree using the same crown grammar, proven UV-atlas routing, successful transparent furnished-branch rendering, and a first real textured MID spray attached correctly to the trunk.

The remaining work is refinement, atlas authoring, and engine validation rather than fundamental geometry rescue.
