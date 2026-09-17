# NUNAVIK PROJECT STATE — 2026-09-12

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

Short Northern Trees refinement session. The main result was that the denser card-native Tamarack is now behaving correctly in X-Plane and has crossed from geometry-debugging into art/material refinement.

The session identified and fixed a real foliage-face winding problem that had been largely hidden by the earlier sparse tree. After the crown was made denser, three symptoms became obvious at once:

```text
near-side tiers disappeared
foliage disappeared when viewed from above
3-D illumination was wrong
```

The cause was the diagnostic reversed winding retained from the earlier geometry investigation. With the successful -90 degree card fold, both foliage faces ended up with strong downward-facing normals. Restoring the original forward winding fixed all three symptoms together.

The denser tree was then given deterministic random jitter in tier phase and individual card transforms. This successfully broke the vertical ladders / braided crown structure without destroying the Tamarack growth grammar.

Stand density was also calibrated against the registered RmC / ML reference photography. The original 5 x 5 m spacing was far too open. A 1 x 1 m test was far too dense, producing an almost continuous vegetation slab. The current provisional dense-stand recipe is:

```text
SPACING 2 2
RANDOM  2 2
```

This gives a much more convincing dense northern woodland while retaining visible ground and individual crown structure.

The next task is deliberately artistic rather than technical: draw distinct MID and LOW furnished-branch textures. Since this is tablet-intensive work, the session stops here.

---

# 1. Executive status

The broader scenery architecture remains unchanged:

```text
Quebec MNT-HC 10 m DEM
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

Northern Trees status at end of session:

```text
card-native Tamarack generator             PROVEN
one folded card per furnished branch       PROVEN / retained
5 cards per tier dense-crown test           PROVEN
forward card winding                        FIXED / PROVEN
above-view foliage visibility               FIXED
near-side foliage visibility                FIXED
3-D foliage lighting orientation            FIXED
bounded deterministic crown jitter          PROVEN
stand-density calibration                   PROVISIONAL BASELINE FOUND
billboard/3-D material match                DEFERRED TO FULL TEXTURE STACK
LOW/MID/TOP distinct branch artwork         NEXT
normal/weather vegetation texture stack     AFTER BRANCH ART
multi-seed species population               LATER
```

---

# 2. Current Tamarack geometry

The production direction remains a cheap card-native tree rather than a high-poly botanical runtime tree.

Current representation:

```text
cheap leader / trunk
    +
folded two-triangle furnished-branch cards
```

The current card primitive remains approximately:

```text
fold angle:       ~110 degrees
fold orientation: -90 degrees around local root-tip axis
```

The current dense Blender test uses approximately:

```text
Tier Count:       24 in the working modifier test
Cards per tier:    5 LOW
                   5 MID
                   5 TOP
Primary Length:   ~0.55 m
Card Width Ratio: ~0.65
```

The generator source still carries a 26-tier default in its diagnostic printout. The 24-tier value was a live modifier tuning value during this session and should not be confused with a permanent generator default.

Important decision:

> Do not add Laminar-style multiple cards to each individual branch unless a specific viewing-angle failure proves they are needed.

The narrow Tamarack furnished branch is already represented convincingly by one folded two-triangle card. Additional per-branch cards would add alpha overlap and triangle cost without a demonstrated visual need.

---

# 3. Winding bug exposed by dense crown

The previous sparse model rendered acceptably enough that the face-orientation defect was not obvious.

After increasing crown density, the failure became unmistakable:

```text
1. near-side tiers failed to render
2. tiers failed to render from above
3. foliage illumination was physically wrong
```

The diagnostic v1.0i card source used reversed foliage faces:

```python
faces = [
    (0, 2, 1),
    (3, 0, 1),
]
```

Combined with the successful -90 degree upward fold, this made both foliage-face normals point predominantly downward.

The repair restores forward winding:

```python
faces = [
    (0, 1, 2),
    (3, 1, 0),
]
```

The per-face UV loop ordering was changed correspondingly so that the painted furnished branch remains mapped in the same visual orientation.

Result in X-Plane:

```text
near-side tiers render correctly     PASS
overhead foliage renders correctly   PASS
3-D foliage lighting direction       PASS
```

This is a genuine geometry correction and should remain in production.

Working patch lineage from this session:

```text
v1.0i  upward-fold + reversed-winding diagnostic
    -> v1.0j winding restore test
    -> v1.0k jitter pass
```

Promote the working changes to the canonical generator once the current tree state is safely saved in the repository.

---

# 4. Deterministic jitter pass

Once the denser crown rendered correctly, its remaining artificiality came from regular tier/card organization rather than insufficient foliage.

A new deterministic jitter pass was added.

Current variation channels:

```text
whole-tier azimuth phase variation
per-card azimuth variation
per-card roll variation
per-card rise variation
per-tier crown-width variation
existing card-length variation
existing card-width variation
existing tier-spacing variation
```

All variation remains deterministic from `Seed`.

Important implementation rule:

> Separate hash channels are used for different variation quantities so that long cards, rolled cards, raised cards, etc. do not become unintentionally correlated.

Useful starting values used for the current result are approximately:

```text
Tier Azimuth Variation    full unique tier phase
Card Azimuth Variation    ~ +/- 6 deg
Card Roll Variation       ~ +/- 8 deg
Rise Variation            ~ +/- 4 deg
Crown Width Variation     ~ +/- 8%
Card Length Variation     ~ 0.15
Card Width Variation      ~ 0.10
Tier Spacing Variation    ~ 0.15
```

Visual result:

```text
vertical branch ladders / braids       strongly reduced
crown edge                              more irregular
individual branch attitude             less repetitive
overall Tamarack silhouette             preserved
```

Current decision:

> The within-tree randomization is now strong enough. Do not increase it merely for novelty.

The next obvious source of repetition is variation between whole trees, not within the current individual.

---

# 5. Future multi-seed species population

The long-term `.for` design should contain multiple deterministic individuals for each species / growth-form recipe.

Working target:

```text
~6 seeds per species / growth form
```

Conceptually:

```text
Larix laricina
    Tamarack_Stunted_3m
        seed 00
        seed 01
        seed 02
        seed 03
        seed 04
        seed 05
```

Important distinction:

```text
Seed variation
    -> individual expression of one growth form

Growth-form variation
    -> different ecological / morphological recipe
       exposed, sheltered, shorter, broader, juvenile, etc.
```

A seed should vary tier phase, card jitter, leader wander, small width/length differences, etc. It should not silently change the ecological growth form.

Each seed should eventually have:

```text
matching 3-D mesh
matching billboard silhouette
```

so that LOD transition does not collapse several distinct near-field trees into one repeated distant shape.

---

# 6. Stand-density calibration against RmC / ML reference

The current calibration target remains the registered RmC stand dominated by Tamarack (`ess_dom = ML`).

`RmC` is the densest moss/heath conifer class in the current forest-family set:

```text
R   coniferous forest
m   moss + ericaceous / heath understory
C   41-60% tree cover
```

The original forest test used:

```text
SPACING 5 5
RANDOM  1 1
```

This rendered as scattered trees over tundra and was much too open for the RmC reference.

Rapid manual `.for` experiments established the density bracket:

```text
SPACING 5 5
    far too open

SPACING 1 1
    far too dense
    crowns knit into a near-continuous slab

intermediate ~1.5 m
    still too closed / plantation-like

SPACING 2 2
    visually close to the reference density
    ground remains visible
    individual trees remain resolvable
```

A later positional-randomness test used:

```text
SPACING 2 2
RANDOM  2 2
```

This improved local stand structure by breaking the evenly sprinkled appearance and producing:

```text
close pairs / small clumps
irregular holes
less visible placement-grid structure
more natural local spacing
```

Current provisional RmC recipe:

```text
SPACING 2 2
RANDOM  2 2
```

Decision:

> Freeze this as the current dense-stand baseline rather than continuing to chase density through tree geometry.

Remaining discrepancy with the reference is now mainly stand heterogeneity and low woody matrix rather than raw stem count.

Possible later mechanisms:

```text
multiple tree seeds
height / growth-form mixtures
species mixtures where VEG_NORD supports them
low shrub / sapling forest layer
broad density modulation / DENSITY_PARAMS experiment
```

Do not add these until the core Tamarack art and material stack are farther along.

---

# 7. Billboard / 3-D illumination mismatch

A persistent illumination difference remains between:

```text
near-field 3-D Tamarack
farther billboard Tamarack
```

A test attempted to move both shader blocks toward Laminar's stock vegetation setup by adding:

```text
SUPER_ROUGHNESS 1.0
NORMAL_TRANSLUCENCY
```

without yet supplying the complete matching normal/weather texture stack.

Result:

> The billboard / 3-D illumination difference became dramatically worse.

Interpretation:

The current Larix material stack is intentionally incomplete. Laminar's stock spruce uses a coordinated vegetation stack including:

```text
albedo
normal texture
weather/material texture
roughness
normal translucency
blend/hash behavior
```

Applying only part of that shader behavior to the current provisional art is not a meaningful final calibration.

Decision:

> Treat the current billboard / 3-D illumination mismatch as an artifact of the incomplete texture stack and defer it.

Do not spend time tuning the temporary albedo images around an incomplete material model.

Return to the simpler known-good shader configuration until the proper full vegetation texture stack is available.

---

# 8. Current texture/atlas state

The runtime tree still deliberately reuses the same hand-authored Larix furnished-branch motif across the LOW / MID / TOP card classes.

This was the right choice while debugging:

```text
UV mapping
fold orientation
winding
lighting
card density
procedural placement
```

Those systems are now sufficiently stable that the texture vocabulary can expand.

The current one-card-per-branch architecture is retained.

Important conclusion from the in-engine tests:

> The narrow Larix branch does not currently need Laminar-style multiple foliage cards per furnished branch.

The folded two-triangle primitive already supplies enough apparent volume for the small northern Tamarack at intended viewing distances.

---

# 9. Next task: draw MID and LOW furnished branches

Immediate next session:

> Draw distinct MID and LOW Larix furnished-branch artwork.

This is intentionally the next task before normal/weather-map work because the underlying albedo vocabulary must exist first.

Recommended authoring sequence:

```text
1. preserve the currently working furnished-branch element as the control
2. draw MID branch artwork
3. map MID to its intended UV island
4. test immediately in Blender / X-Plane if useful
5. draw LOW branch artwork
6. map LOW to its intended UV island
7. retain distinct TOP / upper-crown treatment
8. only then build the full vegetation material stack
```

The branch artwork remains a tablet / GIMP task and is expected to be comparatively time-consuming.

Do not begin normals/weather-map tuning before the LOW/MID/TOP albedo branch vocabulary is sufficiently established.

---

# 10. After LOW/MID branch art

Once the LOW/MID/TOP furnished-branch albedo set is stable, proceed to the proper vegetation texture/material stack.

Likely order:

```text
3-D albedo atlas finalization
    -> 3-D normal map
    -> 3-D weather/material map

billboard albedo finalization
    -> billboard normal map
    -> billboard weather/material map

then enable / tune the full stock-like shader behavior
    -> roughness
    -> normal translucency
    -> blend/hash / alpha behavior
```

Only after the complete stack is present should the billboard/3-D illumination transition be calibrated seriously.

---

# 11. Deferred work

Do not mix the following into the next branch-painting session:

```text
final RmC ground material stack
billboard vs 3-D illumination matching
normal/weather map authoring before branch albedo vocabulary exists
DENSITY_PARAMS experiments
multi-seed `.for` population generation
additional species
black spruce
low woody understory / shrub layers
seasonal Tamarack gold state
whole-tree billboard family generation
settlement / road work
```

---

# 12. Stopping point

This was a short but high-value session.

The dense card-native Tamarack now:

```text
renders correctly from the side
renders correctly from above
has corrected face normals / lighting orientation
has convincing internal randomization
retains a narrow northern Tamarack silhouette
works at plausible dense-stand spacing
no longer needs geometry rescue
```

The geometry should now be treated as sufficiently stable for texture authoring.

Immediate next task:

> **Draw the MID and LOW furnished-branch elements.**

After that, complete the normal/weather vegetation texture stack and revisit the deferred billboard/3-D material transition.
