#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    echo "Source this script rather than executing it:"
    echo "  source tools/ullaaq_ortho4xp_env.sh"
    exit 1
fi

cd "$HOME/linGames/Ortho4XP" || return

export ULLAAQ_NHN_WATER_GPKG="$HOME/linGames/GIS/Canada/NHN/rebuild/+58-069_2026-09-01/+58-069_NHN_water_candidate.gpkg"

export ULLAAQ_VEGNORD_GPKG="$HOME/linGames/Ullaaq-Air-Nunavik/work/+58-069/landcover/+58-069_VEG_NORD_tile.gpkg"

export ULLAAQ_LANDCOVER_GPKG="$ULLAAQ_VEGNORD_GPKG"

source venv/bin/activate

echo "Ullaaq Ortho4XP environment ready."
echo "NHN water: $ULLAAQ_NHN_WATER_GPKG"
echo "VEG_NORD:  $ULLAAQ_VEGNORD_GPKG"
