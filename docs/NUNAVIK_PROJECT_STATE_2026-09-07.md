# NUNAVIK PROJECT STATE — 2026-09-07

## Session summary

Long Northern Trees / texture-authoring session. The project moved from a partially successful high-poly-to-sprite workflow to a cleaner production architecture: **the runtime tree is now designed natively as a procedural card tree, and the foliage atlas is authored directly in a raster editor.**

The major result is that both sides of the system are now substantially understood:

```text
procedural card-native tree geometry
        +
shared hand-authored vegetation atlas
        =
low-poly runtime tree
```

A rough ten-minute tablet sketch of a tamarack furnished branch was successfully mapped onto the current 26-tier tree and already produced a convincing enough result to validate the approach.

Late in the session, the Laminar `Spruce02` UV layout was extracted from the stock `.for` and overlaid on the stock atlas. This showed exactly how Laminar packs and maps the two-triangle furnished-branch units and gives us a concrete UV layout to use as the starting paint kit tomorrow.

---

## Architectural pivot: card-native generator

The previous source-oriented design still assumed that the real tree existed as a high-poly three-dimensional botanical object, with secondary branches free to leave primaries in arbitrary directions and wander through 3-D space. That was useful for morphology exploration, but it imposed unnecessary complexity on the runtime texture workflow.

Decision:

> Northern Trees production geometry should be generated directly as a card-based tree. The high-poly botanical tree is optional reference material, not a required precursor to the runtime asset.

The runtime generator now owns:

```text
leader / trunk
crown start/end
crown envelope
crown width / fat-skinny growth form
tier count and spacing
tier clocking
LOW/MID/TOP crown habits
cards per tier
card length
card width
card rise / pitch
azimuth
roll
bounded deterministic variation
```

It does not need to generate:

```text
modeled secondary long shoots
modeled short shoots
needle rosettes
high-poly furnished branches
source renders
atlas construction
```

Texture authoring is now a separate raster workflow.

---

## 26-tier baseline

The original detailed botanical tamarack used **26 tiers**. That is now the default baseline for the card-native runtime tree as well.

With the current default of three cards per tier:

```text
26 tiers × 3 cards = 78 folded sprays
78 sprays × 2 triangles = 156 foliage triangles
```

The cheap leader/trunk is additional geometry. This remains comfortably below Laminar's stock close-tree budgets.

Increasing the tier count from the earlier 13-tier proof immediately improved the visual density. Enlarging the folded card envelope also brought the runtime silhouette much closer to the intended tamarack habit before any proper atlas work was done.

---

## Clean card-native script

Created a cleaned production-oriented generator:

```text
generator_v1.0a_card_native.py
```

The modifier interface is organized around controls that make sense for the card representation.

### TREE

```text
Height
Base Diameter
Leader Wander
Leader Points
```

### CROWN

```text
Crown Start
Crown End
Tier Count              default 26
Tier Clock Step
Crown Width Scale
Crown Base Scale
Widest Point
Crown Tip Scale
```

### CARD DISTRIBUTION

```text
LOW Cards Per Tier
MID Cards Per Tier
TOP Cards Per Tier
Upper Habit Start
Top Habit Start
```

### CARD SIZE

```text
Primary Length
Card Width Ratio
LOW/MID/TOP Length Scale
LOW/MID/TOP Width Scale
```

### CARD ORIENTATION

```text
Low Rise
Mid Rise
Top Rise
```

### VARIATION

```text
Seed
Card Length Variation
Card Width Variation
Card Azimuth Variation
Card Roll Variation
Tier Spacing Variation
```

The script deliberately contains no atlas builder or botanical source-render machinery.

---

## Shared-atlas requirement

Important production constraint reaffirmed:

> All plants/trees defined by a single `.for` share one 3-D atlas.

Therefore the atlas must be planned as a **forest resource**, not as a tamarack-only texture.

Likely contents eventually include:

```text
Larix laricina
Picea mariana
other conifer resources
willow / dwarf birch / shrub resources
bark / wood strips
twig / deadwood fillers
seasonal variants where ecologically useful
reserved expansion space
```

Seasonality should be treated species-by-species rather than multiplying every species by four seasons.

For tamarack, the working sim-art plan is currently:

```text
green foliage state
gold/autumn foliage state
```

The brief pale spring flush is too short-lived to justify its own texture state. Winter treatment remains a later design decision rather than something that needs to block the first production atlas.

---

## Atlas resolution strategy

Laminar's supplied tree atlas examined in this session is:

```text
2048 × 4096
```

The Laminar layout strongly suggests modular working blocks of approximately:

```text
512 × 1024
```

For Northern Trees, the current authoring plan is:

```text
8192 × 8192 master atlas
```

This gives substantial working room for many vegetation resources. The master can always be downsampled for deployment if required.

An 8K runtime forest atlas is plausible because X-Plane clearly supports 8K textures elsewhere, but use of an 8K texture specifically in a `.for` should still be verified in-engine before it becomes a hard production dependency.

---

## Bark texture

Selected a production-ready CC0 bark source:

```text
https://cc0-textures.com/t/st-bark-12
```

The source is a seamless 4K bark texture. Since the final atlas strip is heavily downsampled and much of the trunk will be obscured by foliage, no elaborate anti-repetition treatment is necessary.

GIMP workflow used:

```text
Filters -> Map -> Tile
```

A simple tall repeated strip is sufficient for this use.

Working conclusion: bark is not a bottleneck. Species identity will be carried far more strongly by crown geometry and furnished-branch artwork.

---

## Primary larch art source

Pinned the 1819 **North American Sylva** plate as the primary source/reference for *Larix laricina* furnished-branch artwork:

```text
Plate 153
Larix laricina
original caption: American Larch / Larix americana
```

Reason:

- orthographic botanical presentation
- clear branch structure
- clear short-shoot / needle arrangement
- no photographic perspective distortion
- no depth-of-field problems
- easier to trace/paint cleanly than to extract from natural photographs

Photos remain useful as secondary color/detail reference but are poor primary extraction sources because of perspective, focus, background, and occlusion.

Alternate public-domain scans of the plate were inspected, but the practical route is to paint/trace over the plate rather than try to perfectly remove aged paper, yellowing, and reverse-page bleed-through.

The Huion drawing tablet works correctly under Linux without additional setup.

---

## First hand-painted furnished branch

A very quick larch furnished-branch test was traced/painted in GIMP from the botanical plate.

This was intentionally crude. The goal was only to test whether hand-authored botanical art survives:

```text
transparent PNG
    -> atlas mapping
    -> folded two-triangle cards
    -> repeated 26-tier tree
```

The result was surprisingly good for a roughly ten-minute sketch. It immediately read more naturally than the earlier procedural comb-like source render because the secondary structure could be authored directly for the card representation.

Current working art directory:

```text
~/linGames/Ullaaq-Air-Nunavik/work/Objects/Northern_Trees/Atlas/
```

Current working files:

```text
larix_laricina.xcf
larix_laricina_atlas_test.png
```

---

## First atlas-mapped card-native tree

Created test script:

```text
generator_v1.0b_atlas_test.py
```

Important implementation change:

> UVs are assigned **per polygon loop / per face**, not merely per shared mesh vertex.

This matters because the folded spray consists of two physical triangles sharing a root-tip edge, but the two texture triangles may be mapped independently.

The first rough painted branch was loaded with alpha and applied to the card-native tree. LOW/MID/TOP temporarily shared the same test motif so that the experiment isolated mapping rather than artwork variety.

Result:

- alpha works
- branch imagery reads on the folded geometry
- the 26-tier crown looks recognizably tree-like
- the basic raster-authoring architecture is proven
- branch/trunk attachment now reduces to UV/root-anchor placement rather than a fundamental geometry problem

---

## Branch/trunk attachment insight

The physical card root already originates at/near the leader. The remaining attachment problem is the relationship between that physical root and the **painted basal/root point** of the furnished branch.

Production rule:

```text
physical card root
    -> exact painted basal point
    -> short woody stem overlaps / enters trunk region
```

The branch card can be buried slightly into the leader so the trunk hides the join.

The texture art should give the branch a definite basal point and enough opaque woody material near that point to tolerate overlap with the trunk.

---

## Stock Laminar Spruce02 UV autopsy

User supplied:

```text
tree_spruce_2.for
trees_3D1_ALB_fa.dds
```

The `.for` contains:

```text
SCALE_X 2048
SCALE_Y 4096
```

Relevant mesh:

```text
MESH 3D_spruce_02 ... 1088 vertices, 1524 indices
```

Therefore:

```text
1524 / 3 = 508 triangles
```

Parsed UV extent for `3D_spruce_02` is approximately:

```text
U 0.253 .. 0.500
V 0.750 .. 1.000
```

This fits a snapped atlas region of:

```text
U 0.25 .. 0.50
V 0.75 .. 1.00
```

which corresponds exactly to:

```text
512 × 1024 pixels
```

inside the 2048 × 4096 atlas.

This confirms the practical species/material-block scale observed visually earlier in the day.

---

## Folded-spray example from Spruce02

A representative stock spray uses vertices 80–83.

Physical faces:

```text
face A: 80, 81, 82
face B: 80, 83, 81
```

Shared edge:

```text
80 <-> 81
```

The measured physical face-normal separation is approximately:

```text
109.93°
```

which validates the 110° folded-card primitive independently chosen for Northern Trees.

Representative UVs:

```text
80 = (0.46872395, 0.96876299)
81 = (0.50000000, 0.95312500)
82 = (0.42182249, 0.95312500)
83 = (0.50000000, 0.99213499)
```

Key conclusion:

> Laminar maps the two triangles separately and packs the combined UV island around the actual branch artwork. The artwork is not constrained to a regular square card cell.

The shared fold/root-tip edge follows the primary woody axis of the furnished branch.

---

## Laminar atlas-layout lesson

Overlaying the extracted Spruce02 UV map on the stock atlas made the production method obvious.

The 512 × 1024 block contains:

```text
left side:
    tall narrow bark / leader UV strips

remaining area:
    several irregular furnished-branch UV islands
    small fillers
    larger branch motifs
```

The islands are packed around actual artwork, not standardized rectangular slots.

A small texture vocabulary is reused many times by geometry. Variation comes from:

```text
card selection
scale
rise
azimuth
roll
crown position
tier spacing
procedural placement
```

not from giving every physical branch a unique texture.

This is now the preferred Northern Trees atlas model.

---

## Artist-facing furnished-branch rule

Important note for future painting:

> Furnished-branch elements should be conceived as paired/mirrored growth originating at a common **basal point**.

The basal point is the branch attachment/root. The two physical triangles are mapped separately, with a shared fold/branch-axis extending away from that basal origin.

The atlas art does not need to be geometrically symmetrical, but the artist should think in terms of a coherent furnished branch growing out from a definite basal attachment point, with visual mass distributed across the two mapped triangles.

This is the key paint grammar to preserve while adapting the Spruce02 UV islands to larch artwork.

---

## Spruce02 UV paint kit

Generated UV paint-kit guides directly from `3D_spruce_02`.

Guide coloring:

```text
cyan   outer UV-island boundaries
red    fold / high-angle shared edges
yellow interior triangulation / shared edges
```

Two transparent atlas-sized guide layers were generated:

### Laminar-scale guide

```text
canvas: 2048 × 4096
Spruce02 guide: 512 × 1024
position: upper-left
```

### High-resolution Northern Trees guide

```text
canvas: 8192 × 8192
Spruce02 guide: 1024 × 2048
position: upper-left
```

These were bundled for download as:

```text
spruce02_uv_paintkit_guides.zip
```

Overlaying the guide on the stock atlas in GIMP verified that the extracted UV layout correctly matches the texture artwork.

---

## Current atlas-authoring decision

For the first production larch block, do **not** invent a new UV packing scheme yet.

Instead:

> Start from the known-good Laminar `Spruce02` UV layout and paint larch resources into those existing islands.

This gives an immediate, production-shaped layout with:

- bark strips
- large branch islands
- medium branch islands
- small/top/filler islands
- known folded-card geometry relationships

Later, once the workflow is mature, the Northern Trees generator can own its own manifest and custom UV packing if that becomes worthwhile.

---

## Next session — 2026-09-08

Primary goal:

> Paint the first real larch element using the Spruce02 UV paint kit and test it immediately.

Recommended sequence:

1. Inspect the Spruce02 guide and identify exactly which UV islands will serve which larch roles.
2. Mark each island with artist-facing information:
   - basal/root point
   - shared fold / branch axis
   - outer island boundary
   - intended motif role
3. Decide the first island to paint, likely a large furnished branch.
4. Paint one larch element in GIMP using the botanical plate as morphology reference.
5. Map that one element in the card-native generator.
6. Test in Blender before painting anything else.
7. Adjust artwork or UV assumptions if necessary.
8. Repeat element-by-element until the larch branch vocabulary is complete.
9. Add bark once branch mapping is settled.
10. Later duplicate/recolor the green larch artwork for the gold/autumn state.

The critical workflow is deliberately incremental:

```text
paint one element
    -> map it
    -> test it
    -> correct
    -> paint next element
```

Do not paint an entire atlas before validating the first few islands.

---

## Stopping point

The low-poly tree problem is no longer blocked by geometry or by the need to derive textures from a million-triangle botanical model.

At end of session:

- card-native generator is established
- 26-tier runtime structure is established
- high-resolution raster authoring workflow is established
- CC0 bark source is selected
- North American Sylva is pinned as the primary larch morphology/art source
- first hand-drawn larch branch works on the tree
- alpha-textured folded-card mapping works
- per-face UV mapping is implemented
- stock Spruce02 UV mapping has been reverse-engineered
- 110° fold is independently validated against Laminar geometry
- Spruce02 paint-kit guides exist at runtime and high-resolution atlas scale
- tomorrow's task is now concrete: paint and test the first real furnished-branch island

The remaining challenge is art direction and atlas vocabulary, not fundamental runtime architecture.
