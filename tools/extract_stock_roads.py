#!/usr/bin/env python3

from pathlib import Path

ROOT = Path.home() / "linGames/Ullaaq-Air-Nunavik"

src = ROOT / "work/+58-069/stock-overlay/+58-069_stock.txt"
out = ROOT / "work/+58-069/stock-overlay/+58-069_roads_only.txt"

lines = src.read_text().splitlines()

network_defs = [x for x in lines if x.startswith("NETWORK_DEF ")]

segments = []
inside = False
current = []

for line in lines:
    if line.startswith("BEGIN_SEGMENT "):
        inside = True
        current = [line]
        continue

    if inside:
        current.append(line)

        if line.startswith("END_SEGMENT "):
            segments.extend(current)
            segments.append("")
            current = []
            inside = False

with out.open("w") as f:
    f.write("A\n")
    f.write("800\n")
    f.write("DSF2TEXT\n\n")

    f.write("PROPERTY sim/planet earth\n")
    f.write("PROPERTY sim/overlay 1\n")
    f.write("PROPERTY sim/west -69\n")
    f.write("PROPERTY sim/east -68\n")
    f.write("PROPERTY sim/south 58\n")
    f.write("PROPERTY sim/north 59\n")
    f.write("PROPERTY sim/creation_agent Ullaaq_Nunavik_roads_proof\n\n")

    for line in network_defs:
        f.write(line + "\n")

    f.write("\n")

    for line in segments:
        f.write(line + "\n")

print(f"Wrote: {out}")
print(f"Network definitions: {len(network_defs)}")
print(f"Road segments: {sum(1 for x in lines if x.startswith('BEGIN_SEGMENT '))}")
