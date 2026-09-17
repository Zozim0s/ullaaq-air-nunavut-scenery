# NUNAVIK PROJECT STATE — 2026-09-14

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

Current Larix atlas source:

```text
work/Objects/Northern_Trees/Atlas/larix_laricina.xcf
```

Current runtime atlas export:

```text
work/Objects/Northern_Trees/Atlas/larix_laricina_atlas_test2.png
```

Current live forest resource:

```text
scenery/Ullaaq_Nunavik_Resources/forests/ullaaq_larix_laricina_test.for
```

Current virtual forest resource:

```text
lib/ullaaq/forests/tam_test.for
```

---

# Session summary

Northern Trees moved decisively out of basic card-geometry debugging and into **species-art / crown-grammar / material-stack refinement**.

The Larix albedo atlas now has distinct furnished-branch artwork for the three crown zones:

```text
LOW
MID
TOP / HIGH
```

The artwork is still intentionally simple and becomes muddy after repeated downsampling, but in-engine it reads acceptably at the intended viewing scale. A conventional sharpen/contrast/alpha-tightening experiment was performed on the atlas preview, but the softer original artwork was judged preferable because X-Plane's filtering is already extremely aggressive.

The generator was then updated so LOW, MID, and TOP each use their own atlas motif. The top remained the weakest part of the tree from side views, which led to two useful structural experiments:

```text
1. Laminar-style TOP axial foliage fin
2. live card fold-angle control
```

Both mechanisms are now available in the generator.

The important visual-policy decision of the session is:

> **Optimize the tree primarily for oblique / overhead flight viewing, not for forensic eye-level inspection.**

From above, the current card-native Tamarack reads much better than close side views suggest.

Late in the session, a sparse `4-3-3` / `12-tier` tree was tested. It is too open to replace the dense-stand form, but it works well enough to preserve as a likely second growth form.

Immediate next work:

```text
complete the Larix vegetation texture stack
    -> balance billboard and 3-D material response
    -> then generate several distinct trees / seeds
       to reduce repetition at forest scale
```

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
LOW/MID/TOP distinct albedo motifs          PROVEN
three-tier atlas routing                     PROVEN
TOP-only axial fin                           PROVEN AS EXPERIMENTAL CONTROL
live fold-angle control                      PROVEN
dense-stand baseline                         RETAINED
sparse growth-form candidate                 IDENTIFIED
full vegetation normal/weather stack         NEXT
billboard / 3-D material balancing           NEXT
multi-seed individual population             AFTER MATERIAL STACK
additional species                           LATER
```

---

# 2. Larix atlas: alpha state

The current atlas is being treated as the first real **alpha Larix albedo atlas**.

It now contains:

```text
trunk strip
MID furnished branch
LOW furnished branch
TOP / HIGH furnished branch
```

The artwork remains hand-authored / manually transformed.

Important practical lesson:

> Needle-level detail is brutally reduced by the time the atlas reaches runtime scale.

Attempts to preserve every small needle cluster through transformations are not worth the authoring cost unless a particular motif is demonstrably failing.

The important surviving information is:

```text
outer silhouette
branch axis
internal negative space
relative foliage mass
LOW/MID/TOP structural differences
```

The TOP motif remains the best candidate for a future hand-drawn refinement because:

```text
it is small
it scales badly from larger sprites
it is structurally distinct
its authoring cost is limited
```

---

# 3. Sharpening experiment

A conventional non-generative image-processing pass was tested on the available atlas preview.

Three variants were produced:

```text
A  conservative
B  medium
C  aggressive
```

Operations included only:

```text
unsharp masking
modest contrast increase
small alpha-edge tightening
```

No AI art / generative repainting was used.

Result:

> The original softer / muddier artwork is probably better.

Reason:

```text
X-Plane downsampling and filtering are already ruthless
extra sharpening risks crunchy edges / halos
the branch art only needs to survive as coherent crown mass
```

Decision:

> Keep the current softer atlas as the albedo baseline. Sharpened variants are diagnostics only.

---

# 4. Generator lineage from this session

Starting point:

```text
generator_v1.0k_jitter_pass.py
```

This contained the working:

```text
forward winding
-90 degree card-fold orientation
LOW/MID/TOP crown zones
5-card dense test
deterministic tier/card jitter
trunk atlas mapping
single shared Larix branch motif
```

## v1.0l — distinct three-tier atlas routing

Created:

```text
generator_v1.0l_three_tier_atlas.py
```

Change:

```text
LOW -> distinct LOW motif
MID -> original MID motif
TOP -> compact TOP / HIGH motif
```

No crown-placement or jitter logic was intentionally changed.

The generator continues to use the existing LOW / MID / TOP crown grammar, but each source card now samples different Larix artwork.

---

# 5. TOP crown problem

Once LOW / MID / TOP were separated, TOP remained the strangest part of the tree in side views.

Observed behavior:

```text
from above:
    generally acceptable
    cards overlap into plausible crown mass

from the side:
    discrete upper tiers become conspicuous
    leader appears as a mast with horizontal foliage shelves
    scaled TOP art can look like small green fans / tufts
```

Important conclusion:

> The TOP problem is not simply lack of foliage. It is a presentation-plane / crown-grammar problem.

Adding indiscriminate density would likely create a bottlebrush rather than solve the viewing-angle failure.

---

# 6. Laminar-style axial foliage fin

Inspection of Laminar's default spruce geometry reaffirmed that furnished branches sometimes include an additional near-vertical card running along the branch / card fold axis.

This directly addresses the Tamarack TOP failure:

```text
main folded card
    -> strong overhead footprint

axial fin
    -> additional side-view presentation plane
```

Created:

```text
generator_v1.0m_top_axial_fin.py
```

The experiment adds:

```text
one two-triangle axial fin per TOP branch
```

The fin:

```text
shares the TOP branch root-tip axis
uses the exact same TOP atlas UV mapping
inherits the same branch placement / rise / jitter transforms
```

Exposed controls:

```text
TOP Axial Fin Length Scale
TOP Axial Fin Width Scale
```

Initial defaults:

```text
Length = 1.0
Width  = 0.55
```

The first result clearly added useful side-view volume but was too strong.

A reduced-fin test used approximately:

```text
Length = 0.8
Width  = 0.35
```

This was substantially cleaner.

---

# 7. Cards-per-tier experiments

The dense tree had previously used:

```text
LOW = 5
MID = 5
TOP = 5
```

Two upper-crown tests were compared:

```text
1) 5-4-3 cards per tier
   no axial-fin rescaling

2) 5-5-3 cards per tier
   axial fin L=0.8 W=0.35
```

Visual conclusion:

```text
5-4-3
    -> better crown grammar
    -> upper crown attenuates more naturally
    -> less sense of maintaining full lower-crown complexity aloft

reduced axial fin
    -> useful tuning
    -> cleans up the side view
    -> secondary to card-count structure
```

Likely combined direction:

```text
5-4-3
    +
restrained TOP axial fin
```

This is not yet declared a frozen production recipe.

---

# 8. Live card fold-angle control

A new pass promoted card fold angle from a baked source-mesh constant to a live Geometry Nodes control.

Created:

```text
generator_v1.0n_fold_angle_control.py
```

New control:

```text
Card Fold Angle
```

Semantics:

```text
180 deg = flat card
110 deg = previous baseline
 90 deg = right-angle fold
lower values = increasingly acute / closed fold
```

The source card remains only a UV-bearing scaffold. Geometry Nodes rewrites the wing positions around the local root-tip axis at runtime.

This allows rapid fold-angle testing without repainting or remapping the atlas.

---

# 9. Fold-angle visual tests

A deliberately radical comparison was made:

```text
45 deg
90 deg
```

## 45 degrees

Observed:

```text
very closed / acute
strong side presentation
cards begin to read as folded shutters / blades
plan-view footprint collapses too much
lower/middle crown becomes overly compressed
```

Useful as a boundary test, but not a likely production value.

## 90 degrees

Observed:

```text
more plausible
better side-view body than 110
still reads as furnished branches
does not collapse into the 45-degree shutter effect
```

However, after reviewing the tree from above, the design priority was clarified.

---

# 10. Viewing-angle doctrine

Expected X-Plane viewing angle is predominantly:

```text
oblique / overhead from aircraft
```

Therefore:

> **Optimize for the airplane looking down through an oblique cone, not for an observer standing beside the tree.**

The overhead view showed that the current tree reads substantially better than forensic close side views suggest.

A more acute fold helps the side view but reduces horizontal projected foliage area.

Approximate relative plan-view width of the fold:

```text
110 deg -> ~82% of flat-card width
 90 deg -> ~71%
 45 deg -> ~38%
```

Therefore a globally aggressive fold can solve the wrong problem.

Current design implication:

```text
LOW / MID
    should probably retain a relatively open fold
    to preserve useful overhead crown footprint

TOP
    may benefit from a tighter fold
    because it needs more side-view structure
```

Potential later direction:

```text
LOW  ~105-115 deg
MID  ~100-110 deg
TOP   ~90-100 deg
```

The current generator exposes one global fold-angle control. Per-zone fold angles are a possible later refinement if testing justifies them.

---

# 11. Dense-stand baseline remains

The previously established dense RmC / ML stand baseline remains:

```text
SPACING 2 2
RANDOM  2 2
```

This remains the current reference for the densest Tamarack-dominant stand.

The forest-scale problem is increasingly not raw stem density, but repetition and lack of population heterogeneity.

---

# 12. Sparse growth-form experiment

A deliberately sparse tree was tested:

```text
LOW = 4
MID = 3
TOP = 3

Tier Count = 12
```

Result:

```text
individual branch grammar reads clearly
leader / branch relationship is very legible
tree has a convincing open / stunted northern character
too sparse to replace the dense RmC form
useful as a distinct growth-form candidate
```

Decision:

> Preserve this as a possible sparse / poor-site / open-woodland Tamarack form rather than treating it as a failed dense-tree configuration.

This strengthens the long-term population architecture:

```text
species
    -> growth form
        -> multiple deterministic seeds
```

Possible Larix growth forms now include at least:

```text
dense / sheltered / stand-forming
medium
sparse / exposed / poor-site
```

Exact production names and parameters remain TBD.

---

# 13. Population strategy after material work

Once the texture/material stack is stable, the next major anti-repetition tool should be multiple actual trees rather than more complexity inside one tree.

Working target remains approximately:

```text
~6 deterministic seeds per species / growth form
```

Each seed should vary within one growth grammar:

```text
tier phase
card jitter
leader wander
small branch length / width differences
small crown-width differences
```

A seed should not silently change the ecological growth form.

Longer-term:

```text
Larix laricina
    dense form
        seed 00
        seed 01
        ...

    sparse form
        seed 00
        seed 01
        ...
```

Each individual should eventually have:

```text
matching 3-D mesh
matching billboard silhouette
```

This should reduce repetition much more effectively at forest scale than trying to make one universal Tamarack infinitely complicated.

---

# 14. Immediate next task — full vegetation texture stack

Tomorrow's primary task:

> **Build the complete Larix vegetation texture stack and balance billboard versus 3-D.**

The current albedo is intentionally provisional, so material response should no longer be tuned piecemeal.

Recommended order:

```text
3-D albedo atlas
    -> 3-D normal map
    -> 3-D weather/material map

billboard albedo
    -> billboard normal map
    -> billboard weather/material map

then enable / tune coordinated vegetation shader behavior
    -> SUPER_ROUGHNESS
    -> NORMAL_TRANSLUCENCY
    -> BLEND_HASH / alpha behavior
```

The goal is to make:

```text
near-field 3-D tree
farther billboard tree
```

match in:

```text
brightness
color / saturation
apparent foliage density
material response
silhouette
```

Only after the full stack exists should billboard / 3-D balance be judged seriously.

---

# 15. After material-stack completion

Once billboard and 3-D presentation are acceptably matched:

```text
1. generate several deterministic individuals
2. test forest-level repetition
3. establish dense / medium / sparse growth forms
4. build matching billboard variants
5. only then move toward additional species such as black spruce
```

Do not begin additional species while Larix still lacks a stable material / LOD stack.

---

# 16. Deferred work

Do not mix the following into the immediate texture-stack session:

```text
final RmC ground material stack
additional tree species
black spruce
seasonal gold Tamarack
low woody understory / shrub layers
DENSITY_PARAMS experiments
settlement / road work
major crown-geometry redesign
perfect eye-level tree rendering
```

The current tree geometry is sufficiently mature to support material work.

---

# 17. Stopping point

The session ended with a much clearer Northern Trees design space.

The Larix asset now has:

```text
distinct LOW / MID / TOP branch art
working crown-zone atlas routing
working deterministic card jitter
working axial-fin experiment
live card fold-angle control
a dense stand baseline
a plausible sparse growth-form candidate
```

Most importantly, the visual target is now explicit:

> **Flight-view credibility takes priority over perfect ground-level botanical inspection.**

Immediate next session:

```text
build full Larix vegetation texture stack
    -> balance 3-D and billboard appearance
```

After that:

```text
generate multiple deterministic trees / growth forms
    -> reduce repetition at forest scale
```
