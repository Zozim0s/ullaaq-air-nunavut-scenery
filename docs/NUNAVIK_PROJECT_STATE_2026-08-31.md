# Nunavik / Ullaaq Scenery Project State

**Checkpoint date:** 2026-08-31  
**Current tile:** `+58-069` (Kuujjuaq)  
**Session result:** Began authoring the moss/heath forest-floor material family from late-day 10 cm Québec orthophotography. Confirmed that VEG_NORD forest codes are effectively rendering recipes: the middle `VEG_SBOIS` component describes the understory / forest floor, while the density suffix can drive 3D vegetation density. Built and tested the first GIMP image-pipe brush from hand-quarried moss/heath samples. The synthesis method works, but the first brush exposes geometric stamp artifacts at high opacity. Next iteration will use larger irregular samples, more feather, a larger native brush, and downscaled use.

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

Current development mode:

```text
author real terrain materials
    -> preserve VEG_NORD semantics
    -> separate substrate from 3D vegetation
    -> validate at multiple scales
    -> then judge the unified regional whole
```

The first production-style bedrock material remains frozen enough for now.

The active material problem is now the **moss + heath / ericaceous forest-floor family** used by the `Rm*` forest classes.

## Major conceptual result: VEG_NORD forest codes are nearly X-Plane recipes

The 31 `cl_carto` values remain individually addressable in the semantic lookup. They were not dissolved into one generic forest class.

For the coniferous forest family, the code structure is highly useful:

```text
R + VEG_SBOIS + CL_DENS
```

where:

```text
R   -> coniferous forest context

a   -> deciduous-shrub understory
c   -> lichen-dominated understory
cm  -> lichen + moss understory
m   -> mosses + ericaceous shrubs / heath

C   -> 41–60% tree cover
D   -> 26–40% tree cover
L   -> 10–25% tree cover
```

Examples:

```text
RmL
    coniferous forest
    moss + ericaceous/heath understory
    10–25% tree cover

RmD
    same understory family
    26–40% tree cover

RmC
    same understory family
    41–60% tree cover
```

This maps cleanly onto X-Plane responsibilities:

```text
VEG_SBOIS middle code
    -> .ter ground / forest-floor material

CL_DENS suffix
    -> primarily .for density / woody cover

TYPE_COUV prefix
    -> overstory context / species family
```

The working assumption is therefore:

> **Author the understory material first. Let the `.for` layer express most of the crown-density difference.**

Do not create unrelated `.ter` textures for `RmL`, `RmD`, and `RmC` until runtime evidence shows a real need.

## Class reference documentation created

A working class-definition reference was created for:

```text
docs/VEG_NORD_CLASS_DEFINITIONS.md
```

It records the 31 `cl_carto` values, grouped into coniferous forest / taiga, shrub / heath / tundra, rock / mineral mosaics, wet / peatland, and human / bookkeeping / hydro.

Important production note:

```text
EAU
    retained in VEG_NORD semantics for completeness
    NOT used as hydro authority

NHN / HNET Bank
    remains authoritative water geometry
```

## Forest imagery findings

### 30 cm imagery

The 2010 30 cm Kuujjuaq survey was captured on 25 August 2010 after approximately 12Z. The early passes in the north have little forest. Forest-bearing imagery farther south is affected by a low, oblique sun angle.

Observed problems:

```text
long directional conifer shadows
strong dark/light striping
recognizable individual tree crowns
fixed illumination vector
```

These make literal use of the 30 cm forest imagery dangerous for repeating `.ter` artwork.

The source remains useful for broad color statistics, forest-density comparison, macro ecological structure, and general taiga visual vocabulary, but not as a simple "crop one 1248 m square and tile it" source.

### 10 cm imagery

The 10 cm passes were flown later in the day and provide substantially better material-quarry opportunities.

Important discovery:

> The 10 cm imagery does not need to contain a complete square kilometre of one VEG_NORD class.

Forest and shrub classes are highly discontinuous. The correct workflow is therefore to extract many clean local fragments and synthesize a material.

The extra resolution is useful mainly because it allows clearer discrimination of tree crown vs ground, clearer cast-shadow identification, cleaner hand selection of substrate fragments, and better source for texture synthesis.

The final runtime macro will discard most of the raw 10 cm detail.

## RmD / RmL comparison

Late 10 cm imagery was inspected over representative `RmD` and `RmL` polygons.

### `RmD`

Observed:

```text
darker overall
more continuous woody signature
less exposed ground
stronger dark mottling
moss/heath substrate still visible beneath canopy influence
```

Semantic meaning:

```text
R   coniferous forest
m   moss + ericaceous/heath understory
D   26–40% tree cover
```

### `RmL`

Observed:

```text
lighter
more open
more visible moss/heath/lichen substrate
less continuous woody component
greater "breathing room" between conifers
```

Semantic meaning:

```text
R   coniferous forest
m   moss + ericaceous/heath understory
L   10–25% tree cover
```

Current design conclusion:

```text
RmL and RmD are sibling recipes
    -> same parent moss/heath substrate
    -> different tree density
    -> possibly modest broad tonal differences later
```

Do not bake literal directional tree shadows into separate `RmL` and `RmD` textures at this stage.

## AB as a substrate control specimen

The `AB` class proved unexpectedly useful.

Visually, selected `AB` imagery resembles the `Rm*` moss/heath world **without the conifer overstory**.

It shows:

```text
moss / heath / low shrub substrate
hummocky microrelief
lighter exposed floor
darker low-shrub / wetter patches
organic tonal mottling
```

Important observation:

> The forest floor is not flat, either geometrically or tonally.

The lighter, less-shadowed areas in the `AB` imagery are particularly useful as quarry material for the `m` moss/heath forest-floor base.

Current conceptual decomposition:

```text
AB
    -> useful clean reference for open moss/heath substrate

RmL / RmD / RmC
    -> same broad substrate family
    -> conifer overstory added through .for
    -> canopy tonal influence evaluated later
```

This does not mean `AB` is literally identical to the `Rm*` understory. It is being used as a practical visual control because it exposes a similar low vegetation / moss-heath substrate without tree contamination.

## Moss/heath base-texture strategy

The bedrock workflow does not transfer directly.

Bedrock was:

```text
find representative 1248 m square
    -> make seamless
    -> downsample
    -> use as macro
```

Moss/heath forest floor is discontinuous and only appears in smaller islands between woody cover.

Therefore the current strategy is:

```text
10 cm imagery
    -> hand-quarry many clean substrate fragments
    -> remove/avoid tree crowns and strong cast shadows
    -> synthesize a continuous material
    -> later introduce broad color/tonal variation separately
```

The target is not photorealistic reconstruction of a photographed square kilometre.

The target is a **statistically convincing moss/heath ground material**.

## Manual quarry workflow established

GIMP is being used to hand-select clean floor fragments.

Method:

```text
1. inspect late-day 10 cm imagery
2. draw irregular paths around relatively clean moss/heath patches
3. avoid:
       obvious conifer crowns
       strong directional shadows
       ponds
       conspicuous exposed-rock slabs
       roads / human features
       memorable one-off shapes
4. feather selections
5. clone modestly where useful to enlarge a clean area
6. preserve source variation
7. extract fragments as transparent source exemplars
```

A first set of approximately eight samples was cut from one source frame.

Important lesson:

> Do not enlarge one small fragment endlessly with clone work. Prefer several distinct source islands of the same material.

This preserves authentic variation and reduces repetition fingerprints.

## First GIMP pipe-brush experiment

A first `.gih` image-pipe brush was built from eight moss/heath samples.

Initial practical format:

```text
canvas: 160 x 160 px
layers: 8
one sample per layer
selection mode: random
```

The brush was successfully loaded into GIMP after clearing active brush-tag filters.

Temporary user brush storage is sufficient during experimentation.

Once the technique is proven, reproducible brush sources should move into the repository, likely under a dedicated material-lab / assets path.

Possible future repo structure:

```text
assets/materials/brushes/
    source samples
    .xcf builder files
    .gih pipe brushes
    README / physical-scale notes
```

Exact final location remains TBD.

## First synthesis result

A quick first moss/heath texture was painted with the pipe brush.

Observed:

```text
method successfully creates a continuous ground field
source fragments can blend into one plausible substrate
overall material does not immediately read as a collage at normal view
```

A crude shadow mask was applied to suppress remaining directional illumination.

A colorize pass was also applied to pull the sunlit source away from its red/yellow cast.

This was strictly a fast proof iteration.

## Failure mode discovered: geometric stamp artifacts

At high opacity, the first brush produces visible geometric structure.

Test:

```text
100% opacity
    -> texture detail preserved
    -> clear rectangular / angular brush-stamp artifacts

50% opacity
    -> geometric artifacts reduced
    -> detail washed out / averaged away
```

Conclusion:

> **Opacity is not the correct control knob. Brush-tip alpha geometry is the problem.**

The current samples were effectively too square / too close to the cell boundary.

Lowering opacity only hides the geometry by blurring the material into mush.

The desired behavior is:

```text
opaque / detailed center
    +
broad irregular feathered alpha perimeter
```

not:

```text
semi-transparent square swatches
```

## Next brush iteration

Tomorrow's exact material-lab task:

```text
1. return to the 10 cm source

2. cut NEW, larger irregular swatches

3. use substantially more feather around each source selection

4. preserve transparent margins around the actual material fragment

5. build the next pipe brush at a larger native cell size

6. paint at near/full opacity

7. scale the brush DOWN in use if needed rather than enlarging tiny samples

8. test only edge blending / structural synthesis first

9. do not spend time tuning color until the alpha geometry is improved
```

Key lesson:

> **Build a better brush, not a weaker brush.**

The new brush should preserve the source detail of the 100% test while blending more like the 50% test.

## Physical-scale lesson

The 10 cm source should be treated in metres, not screen pixels.

Example:

```text
115 x 115 source pixels @ 0.10 m/px
    -> 11.5 x 11.5 m ground fragment
```

This is already a useful quarry fragment.

The final runtime macro does not need those source pixels one-for-one.

Avoid scaling small source pieces upward merely to fill arbitrary brush cells.

Current rule:

> **Preserve metres, not pixels.**

For the next brush, larger source swatches are preferred because they provide more natural internal variation and allow much broader feathering.

## Broad variation should be separate from brush structure

The clean moss/heath substrate does not exhibit enormous intrinsic tonal variety.

Do not invent unrealistic multicolored patches merely to make the texture "interesting."

Current planned separation:

```text
brush / source fragments
    -> fine and mesoscale structural texture

broad mask / X-Plane compositor
    -> large-scale tonal / color variation
```

Likely eventual workflow:

```text
moss_heath_A
moss_heath_B
    -> two related realizations of the same substrate

COMPOSITE_NOISE / natnoise
    -> broad spatial selection between them
```

Possible differences between A and B:

```text
slightly warmer / browner
slightly darker
modestly different saturation / olive balance
```

Do not create radically different ecological states.

## Tree-shadow question remains deliberately unresolved

The current moss/heath base should initially be authored as **shadow-neutral substrate**.

Then test the same base under:

```text
RmL -> sparse conifer .for
RmD -> medium conifer .for
RmC -> higher-density conifer .for
```

Questions to answer in X-Plane:

```text
Does 3D vegetation provide enough dark structure?

Does the scene become implausibly pale as .for vegetation recedes with distance?

Can one common moss/heath .ter serve all Rm density classes?

Do we need only diffuse broad canopy darkening rather than literal shadows?
```

If canopy influence must be baked into the terrain later, use **nondirectional broad darkening**, not photographed directional tree shadows.

## Potential low-vegetation / autogen experiment

The forest-floor texture should not be perfected in isolation before checking the 3D layer.

A cheap future test:

```text
same moss/heath .ter
    +
stock cold/low conifer .for at three clearly different densities
```

Evaluate from near-ground, low VFR altitude, several thousand feet, and medium regional viewing range.

The goal is to determine how much of the aerial "forest" signature should be carried by:

```text
.ter substrate
vs
.for woody vegetation
```

Species fidelity is not the first objective. Structural behavior comes first.

Longer-term Nunavik vegetation vocabulary may include stunted black spruce, low conifer forms, heath, dwarf shrub, sedge tufts, and tiny spruce / krummholz-like forms.

Do not build that full system yet.

## 10 cm dump imagery side discovery

A later 10 cm frame revealed an excellent view of the Kuujjuaq dump / disturbed-ground area.

This is not relevant to the wild moss/heath material, but is valuable for the later settlement phase.

Potential uses:

```text
hand-traced dump footprint in WED
disturbed-ground draped polygon
service-road geometry
scrap / rubble zones
containers / machinery / vehicles
town-edge transition reference
IH / utility / industrial ground materials
```

Important design decision:

> The dump is visually obvious from the air and is worth explicit hand placement rather than generic procedural treatment.

Retain the relevant 10 cm source frame for later settlement authoring.

## Bedrock status remains unchanged

The bedrock / rocky-tundra material remains the current visual baseline.

Current stack:

```text
real Nunavik orthophoto macro
    +
manual seam authoring
    +
custom lichen/weathered-rock decal
```

Do not continue polishing bedrock while the other classes remain placeholders.

## Terrain-class authoring philosophy after today's work

The 31 VEG_NORD classes should not automatically become 31 unique `.ter` files.

Instead:

```text
ecological code
    -> interpret component meanings
    -> identify reusable substrate family
    -> apply appropriate 3D vegetation density
    -> create variants only where runtime evidence warrants them
```

For forest classes in particular:

```text
middle code / VEG_SBOIS
    -> primary ground-material family

density suffix / CL_DENS
    -> primary .for density control
```

This is currently the most promising way to preserve real ecological semantics without exploding the texture count.

## What NOT to do next

Do not:

```text
reopen VEG_NORD geometry
redo NHN hydro
redo the mesh
return to NALCMS raster topology
over-polish bedrock
search endlessly for a mythical full-square-kilometre pure forest-floor image
bake photographed directional tree shadows into the moss/heath base
solve brush artifacts by reducing opacity until detail disappears
invent large tonal variety not present in the source
build a full custom vegetation library before the substrate test works
```

The immediate problem is specifically:

> **Make an irregular, well-feathered high-opacity pipe brush that synthesizes clean moss/heath floor without geometric stamp artifacts.**

## Important current paths

Project:

```text
~/linGames/Ullaaq-Air-Nunavik
```

Material lab:

```text
~/linGames/Ullaaq-Air-Nunavik/work/material-lab
```

Existing bedrock lab:

```text
~/linGames/Ullaaq-Air-Nunavik/work/material-lab/rock
```

Suggested moss/heath lab location:

```text
~/linGames/Ullaaq-Air-Nunavik/work/material-lab/moss-heath
```

Custom resource package:

```text
~/linGames/Ullaaq-Air-Nunavik/scenery/Ullaaq_Nunavik_Resources
```

VEG_NORD tile:

```text
~/linGames/Ullaaq-Air-Nunavik/work/+58-069/landcover/+58-069_VEG_NORD_tile.gpkg
```

NHN water:

```text
/home/mike/linGames/X-Plane 12/Development/GIS/Canada/NHN/tiles/+58-069/+58-069_NHN_water_final.gpkg
```

Ortho4XP semantic patch:

```text
~/linGames/Ortho4XP/src/O4_DSF_Utils.py
```

Class reference:

```text
docs/VEG_NORD_CLASS_DEFINITIONS.md
```

## Project-control rules

1. Filesystem/repository and source datasets remain the source of truth.
2. Preserve the proven MRDEM + NHN + native VEG_NORD architecture.
3. NHN remains hydro authority.
4. Keep geometry generation separate from material assignment.
5. Keep macro, decal, `.for`, roads, human ground, and `.obj` layers conceptually separate.
6. Preserve the individual VEG_NORD `cl_carto` codes even when multiple codes share one rendering recipe.
7. For forest classes, begin from `VEG_SBOIS` as the ground-material recipe and treat `CL_DENS` primarily as vegetation-density information.
8. Keep raw quarry imagery and source fragments separate from derived brushes/runtime textures.
9. Preserve physical scale; do not enlarge source fragments merely to satisfy arbitrary brush-cell sizes.
10. Use broad tonal masks/compositor variation separately from fine brush synthesis.
11. Change one rendering variable at a time in controlled tests.
12. Do not solve geometric brush artifacts by washing out the material with low opacity.
13. Move successful material-lab tools/resources into the repository only after the technique is proven.
14. End substantial sessions with an updated project checkpoint.

## Git / reproducibility

Git status was not verified at session end.

Before committing:

```bash
cd ~/linGames/Ullaaq-Air-Nunavik
git status
```

Confirm that:

```text
docs/VEG_NORD_CLASS_DEFINITIONS.md
```

is added to the repository.

Do not commit throwaway GIMP brush experiments unless they are intentionally being preserved as part of the material-lab history.

Once the brush workflow is proven, preserve source sample images, builder `.xcf`, final `.gih` pipe brush, and a brief README / scale note inside the repository.

## Next session: exact resume point

Primary objective:

> **Build moss/heath pipe-brush v2 with larger, more irregular, more heavily feathered source fragments.**

Sequence:

```text
1. Open the late-day 10 cm source imagery.

2. Identify larger clean moss/heath floor regions.

3. Draw irregular selections well inside contaminated/tree-shadow boundaries.

4. Feather substantially more than the first-pass swatches.

5. Preserve transparent margins around the true irregular material fragment.

6. Build a larger-cell random .gih pipe brush.

7. Paint a small test area at or near 100% opacity.

8. Scale the brush down in use if needed.

9. Compare against today's 100% and 50% tests.

10. Judge only:
       edge blending
       stamp geometry
       retained detail
       continuous-surface read

11. If successful, then revisit:
       broad shadow-neutralization
       olive/brown color balance
       large-scale mask/compositor variation

12. After a plausible m substrate exists, test it under different .for densities for RmL / RmD / RmC.
```

## End-of-day assessment

2026-08-31 established the conceptual architecture for the first non-rock wild-ground family.

The key breakthrough is that VEG_NORD forest codes can be read almost directly as scenery instructions:

```text
forest type
    +
understory / forest-floor material
    +
tree-cover density
```

The `m` family is therefore being authored first as a **moss + heath / ericaceous substrate**, with conifer density treated as a separate 3D layer.

Late-day 10 cm imagery provides enough clean local fragments to quarry the material even though no large pure patch exists in nature.

The first random image-pipe brush proved that hand-selected orthophoto fragments can be synthesized into a continuous substrate. It also exposed the next specific problem: high-opacity square-ish brush tips leave geometric artifacts, while lowering opacity merely washes out the texture.

Tomorrow's fix is straightforward:

> **larger irregular swatches + broader feather + larger native brush + high-opacity painting + downscaled use.**

The method is promising enough to continue.
