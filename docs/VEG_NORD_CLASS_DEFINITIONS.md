# VEG_NORD `cl_carto` Class Definitions

**Project:** Ullaaq Air Nunavik  
**Purpose:** Working reference for the `VEG_NORD` ecological classes preserved in the X-Plane terrain pipeline.

The `+58-069` VEG_NORD source contains 31 `cl_carto` values. The terrestrial class codes remain individually addressable in the semantic lookup and have **not** been dissolved into the coarse rendering buckets used during the original proof build.

`EAU` is retained here for completeness, but it is not used as production hydro authority. **NHN/HNET Bank defines water geometry.**

---

## Coniferous forest / taiga

| Code | Definition |
|---|---|
| `RaL` | Coniferous forest with deciduous-shrub understory, **10–25% tree cover**. |
| `RcD` | Coniferous forest with **>60% lichen ground cover**, **26–40% tree cover**. |
| `RcL` | Coniferous forest with **>60% lichen ground cover**, **10–25% tree cover**. |
| `RcmD` | Coniferous forest with **lichen + moss**, roughly 40–60% lichen cover, **26–40% tree cover**. |
| `RcmL` | Coniferous forest with **lichen + moss**, roughly 40–60% lichen cover, **10–25% tree cover**. |
| `RmC` | Coniferous forest with **mosses and ericaceous shrubs**, **41–60% tree cover**. |
| `RmD` | Coniferous forest with **mosses and ericaceous shrubs**, **26–40% tree cover**. |
| `RmL` | Coniferous forest with **mosses and ericaceous shrubs**, **10–25% tree cover**. |

### Useful decoding

- `R` = coniferous forest
- `a` = deciduous-shrub understory
- `c` = lichen-dominated understory
- `cm` = lichen + moss
- `m` = mosses / ericaceous shrubs
- `C` = 41–60% tree cover
- `D` = 26–40% tree cover
- `L` = 10–25% tree cover

This makes, for example:

- `RmL` = very open coniferous forest over moss / ericaceous-shrub ground
- `RmD` = denser version of the same ecological family
- `RcmL` = very open coniferous forest over a lichen-moss ground layer

---

## Shrub / heath / tundra

| Code | Definition |
|---|---|
| `AAB` | Low shrub in tundra, 0.3–1 m, **>70% deciduous shrub cover**. |
| `AAH` | High shrub in tundra, >1 m, **>70% deciduous shrub cover**. |
| `AB` | Low shrub, 0.3–2 m, boreal/subarctic, **>70% deciduous shrub cover**. |
| `AH` | High shrub, >2 m, boreal/subarctic, **>70% deciduous shrub cover**. |
| `LS` | Subarctic lichen-heath, <10% trees and <30% deciduous shrubs. |
| `LSA` | Subarctic lichen-heath with **30–70% deciduous shrubs**. |
| `TD` | Erect-shrub tundra, **<30% erect shrubs**. |
| `TDA` | Erect-shrub tundra with **30–70% erect shrubs**. |

---

## Rock / mineral mosaics

| Code | Definition |
|---|---|
| `LSR` | Subarctic lichen-heath with **10–50% rock/mineral substrate**. |
| `RLS` | Subarctic lichen-heath dominated by rock substrate, **50–80% exposed mineral/rock**. |
| `TDR` | Erect-shrub tundra with **10–50% rock/mineral substrate**. |
| `RTD` | Erect-shrub tundra dominated by rock substrate, **50–80% exposed mineral/rock**. |
| `AR` | Rock outcrops and fragments, **<20% vegetation**. |
| `SD` | Bare ground: sand, beaches and other essentially unvegetated ground. |

A useful material continuum for scenery authoring is:

```text
LS -> LSR -> RLS -> AR
lichen-heath -> rock/heath mosaic -> rock-dominated heath -> exposed rock
```

and similarly:

```text
TD -> TDR -> RTD -> AR
erect-shrub tundra -> rock/tundra mosaic -> rock-dominated tundra -> exposed rock
```

---

## Wet / peatland classes

| Code | Definition |
|---|---|
| `MS` | Saltwater marsh. |
| `TAA` | Arctic fen with **30–70% erect shrubs**. |
| `TAR` | Arctic fen or wet tundra. |
| `TMS` | String fen. |
| `TMU` | Uniform fen. |
| `TOP` | Palsa peatland. |

---

## Human / bookkeeping / hydro

| Code | Definition |
|---|---|
| `IH` | Human infrastructure. |
| `ILE` | Island smaller than 8 ha, retained from the topographic database. |
| `EAU` | Water. Retained in VEG_NORD semantics, but **not used as production hydro authority** in Ullaaq. NHN/HNET Bank owns water geometry. |

---

## Pipeline note

The native VEG_NORD polygon fabric is preserved through the Ullaaq mesh workflow. The original `cl_carto` value remains available during terrain assignment.

The early semantic proof build temporarily mapped the 31 classes into coarse X-Plane rendering buckets, but that was only diagnostic rendering. Individual classes such as `RmD`, `RmL`, `RcmL`, `RcD`, etc. can each be routed to separate custom `.ter` definitions when desired.

For current material authoring:

```text
NHN       -> where the water is
VEG_NORD  -> what the land is
MRDEM     -> what shape the land has
```
