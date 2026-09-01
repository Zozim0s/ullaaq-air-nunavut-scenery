# Ullaaq NHN hydro pipeline

This captures the clean-room process validated on tile `+58-069`.

Reference result:
- HNET Bank + Delimiter faces: 43,911
- wet faces / final NHN water features: 42,578
- dry faces: 1,333
- invalid geometry: 0
- positive-area overlaps: 0
- `.poly` WATER seeds: 42,578
- final `.mesh` inland-WATER triangles: 1,239,007

Core rule:

**HNET Bank alone is insufficient. Use HNET Bank + HNET Delimiter for topology.
Use HHYD Waterbody only to classify the resulting faces wet/dry.**

Current inland-water rendering policy:
- `water_tech=XP12`
- `ratio_water=1.0`
- `use_masks_for_inland=False`

This suppresses the legacy automatic inland-water orthophoto treatment. Imagery
support remains available for deliberate future hybrid terrain use.

## Next tile: +58-070

```bash
cd ~/linGames/Ullaaq-Air-Nunavik

python3 tools/build_nhn_hydro_tile.py 58 -70 \
  --nhn-root "$HOME/linGames/GIS/Canada/NHN" \
  --out-dir "$HOME/linGames/GIS/Canada/NHN/tiles/+58-070"
```

Then:

```bash
export ULLAAQ_NHN_WATER_GPKG="$HOME/linGames/GIS/Canada/NHN/tiles/+58-070/+58-070_NHN_water.gpkg"

python3 tools/ortho4xp_water_config.py \
  "$HOME/linGames/Ortho4XP/Ortho4XP.cfg"
```

After Ortho4XP Step 1:

```bash
python3 tools/check_ortho4xp_water_seeds.py \
  --gpkg "$ULLAAQ_NHN_WATER_GPKG" \
  --poly "$HOME/linGames/X-Plane 12/Development/Replacement Mesh/Orth4XP_Tiles/zOrtho4XP_+58-070/Data+58-070.poly"
```

The expected WATER-seed count is the feature count of the new tile's final GPKG.
Do not hard-code 42,578 outside the +58-069 reference test.
