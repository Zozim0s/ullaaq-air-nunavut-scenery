# NUNAVIK PROJECT STATE — 2026-09-17

## Northern Trees / Larix laricina

### Session objective
Complete the first full Larix texture/material stack, calibrate the 3-D-to-billboard transition, compare against a stock X-Plane forest, and determine the next major work item.

---

## 1. Full Larix texture stack

Built the first control texture stack for the custom Larix forest asset.

Generated support maps for both the 3-D atlas and billboard:

- `larix_laricina_atlas_NML.png`
- `larix_laricina_atlas_SM.png`
- `larix_laricina_billboard_NML.png`
- `larix_laricina_billboard_SM.png`

Current intended shader structure:

```text
SHADER_2D
    TEXTURE ../textures/larix_laricina_billboard_test1_082.png
    TEXTURE_NORMAL 1 ../textures/larix_laricina_billboard_NML.png
    WEATHER ../textures/larix_laricina_billboard_SM.png
    BLEND_HASH 0.5
    SUPER_ROUGHNESS 1.0
    NORMAL_TRANSLUCENCY

SHADER_3D
    TEXTURE ../textures/larix_laricina_atlas_test2.png
    TEXTURE_NORMAL 1 ../textures/larix_laricina_atlas_NML.png
    WEATHER ../textures/larix_laricina_atlas_SM.png
    BLEND_HASH 0.5
    SUPER_ROUGHNESS 1.0
    NORMAL_TRANSLUCENCY
```

The full stack loads successfully. Earlier concern that the material stack itself was responsible for the large 3-D/billboard luminance mismatch was not supported by controlled tests.

---

## 2. Billboard luminance calibration

Initial testing used the sparse Larix growth form. In that state the billboard appeared substantially brighter than the 3-D tree.

Measured visible-pixel mean luminance:

- 3-D atlas: ~61.7
- billboard: ~97.2

A temporary billboard at 65% RGB brightness brought the sparse-tree transition much closer.

After returning to the denser intended tree geometry, the result reversed: the 0.65 billboard became clearly too dark relative to the 3-D crown.

The original billboard at 1.00 was then clearly too bright.

Current working value:

- **billboard RGB multiplier: 0.82**

This is close enough for now. Do not spend more time on fine calibration until the rest of the forest system is complete.

Current billboard texture:

`larix_laricina_billboard_test1_082.png`

Live texture directory:

`scenery/Ullaaq_Nunavik_Resources/textures/`

---

## 3. Stock forest comparison and LOD investigation

A flyover of the default forest near Schefferville was used as a control.

The stock forest shows a distinct middle-distance regime, but it transitions much more gracefully than the custom Larix stand.

The stock spruce `.for` was inspected directly:

```text
MESH 3D_spruce_02  0 500 1088 1524 ...
MESH lod_spruce_02 0 100  648  972 ...
```

and:

```text
TREE ...
MESH_3D 3D_spruce_02
MESH_3D lod_spruce_02
```

Interpretation:

- `3D_spruce_02` = main 3-D mesh, active from 0–500 m
- `lod_spruce_02` = additional close-detail mesh, active only from 0–100 m
- beyond the main mesh range, the billboard carries the tree

Triangle counts:

- stock main spruce mesh: 1524 / 3 = **508 tris**
- stock close-detail mesh: 972 / 3 = **324 tris**
- close range can therefore display both meshes simultaneously

The close-detail mesh is additive, not a replacement middle-distance tree. Therefore the custom Larix is not missing a stock-style intermediate mesh between 100–500 m.

---

## 4. Current Larix `.for` geometry / LOD state

Current live forest resource:

`scenery/Ullaaq_Nunavik_Resources/forests/ullaaq_larix_laricina_test.for`

Relevant current structure:

```text
SCALE_X 512
SCALE_Y 1024
SPACING 2 2
RANDOM 1 1

MESH 3D_larix_laricina_test 0 300 812 1092 0.0 0.0 0.0 NO_SHADOW
...
TREE 0 128 512 768 256 100 3.0006499 3.0006452 1 1 __NTXP_LARIX_LARICINA_TEST__
MESH_3D 3D_larix_laricina_test
```

Triangle count:

- 1092 / 3 = **364 tris**

The tree is approximately 3 m tall.

The original mesh range was 0–500 m. That produced an obvious weak/dark middle-distance band before the billboard took over.

LOD handoff experiments:

- **500 m**: clearly too far; 3-D tree visually starves before billboard handoff
- **300 m**: substantially better
- **250 m**: worse; billboard takeover felt too early
- **350 m**: tested after 250; not preferred over 300
- **current working value: 300 m**

Decision: freeze at **300 m** for now.

Likely explanation: the stock spruce is roughly 10–15 m tall and can remain visually coherent to 500 m. The custom Larix is only ~3 m tall, so its card geometry becomes too small/subpixel much sooner.

---

## 5. Current visual result

The forest is now much closer to a usable whole:

- full 3-D material stack works
- billboard and 3-D luminance are reasonably close at the current 0.82 multiplier
- the severe middle-distance trough was greatly reduced by shortening the 3-D mesh range to 300 m
- the remaining LOD transition is acceptable enough to defer further tuning

Do not spend significant additional time on:
- exact billboard brightness
- sub-300/350 m LOD micro-tuning
- close-detail supplemental mesh
- shadow behavior

until the full forest system is complete and can be judged in context.

---

## 6. Next major task: custom ground texture

The logical next step is to finish and tune the custom RmC ground material.

Existing base texture:

`rmc_AB_1024.png`

Earlier testing established that the softness / apparent low resolution was not simply a bad base texture. The custom `.ter` was missing the fuller material stack used by Laminar terrain.

Stock conifer terrain reference:

```text
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

Earlier full-stack tests using Laminar-style composite/noise/decal behavior brought the custom ground much closer to stock apparent resolution.

### Tomorrow's starting point

1. Locate the current RmC `.ter`.
2. Inspect its present directives.
3. Locate the stock conifer `.ter` used as the reference.
4. Build the missing custom composite/detail texture for RmC.
5. Wire a complete custom terrain stack.
6. Test from:
   - ground level
   - low flight
   - normal forest-viewing altitude
7. Tune only after the full terrain stack is functioning.

---

## 7. Freeze points at end of session

For the next session, treat these as provisional baselines:

- Larix geometry: **dense intended tree**, not the sparse diagnostic form
- 3-D mesh range: **0–300 m**
- billboard brightness multiplier: **0.82**
- `SPACING 2 2`
- `RANDOM 1 1`
- full NML / SM material stack enabled
- do not return to LOD tuning until after ground material work
- next focus: **custom RmC ground texture/material stack**

