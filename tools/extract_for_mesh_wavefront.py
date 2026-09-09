#!/usr/bin/env python3

import sys
from pathlib import Path

if len(sys.argv) != 4:
    raise SystemExit(
        f"Usage: {sys.argv[0]} input.for mesh_name output.obj"
    )

src = Path(sys.argv[1])
mesh_name = sys.argv[2]
dst = Path(sys.argv[3])

lines = src.read_text().splitlines()

verts = []
indices = []

for i, line in enumerate(lines):
    p = line.split()

    if not p:
        continue

    if p[0] == "MESH" and len(p) >= 6 and p[1] == mesh_name:
        vcount = int(p[4])
        icount = int(p[5])

        j = i + 1

        while j < len(lines) and len(verts) < vcount:
            q = lines[j].split()

            if q and q[0] == "VERTEX":
                vals = list(map(float, q[1:]))

                if len(vals) < 8:
                    raise RuntimeError(
                        f"Bad VERTEX line at {j+1}"
                    )

                # X-Plane forest vertex:
                # x y z  nx ny nz  u v ...
                verts.append({
                    "pos": vals[0:3],
                    "normal": vals[3:6],
                    "uv": vals[6:8],
                })

            j += 1

        while j < len(lines) and len(indices) < icount:
            q = lines[j].split()

            if not q:
                j += 1
                continue

            if q[0] in ("IDX", "IDX10"):
                indices.extend(int(x) for x in q[1:])
            elif q[0] == "MESH":
                break

            j += 1

        indices = indices[:icount]
        break

else:
    raise SystemExit(f"Mesh not found: {mesh_name}")

if len(verts) != vcount:
    raise SystemExit(
        f"Expected {vcount} vertices, found {len(verts)}"
    )

if len(indices) != icount:
    raise SystemExit(
        f"Expected {icount} indices, found {len(indices)}"
    )

dst.parent.mkdir(parents=True, exist_ok=True)

with dst.open("w") as f:
    f.write(f"# Extracted from {src.name}\n")
    f.write(f"# Mesh: {mesh_name}\n\n")

    for v in verts:
        x, y, z = v["pos"]
        f.write(f"v {x} {y} {z}\n")

    f.write("\n")

    for v in verts:
        u, vv = v["uv"]
        f.write(f"vt {u} {vv}\n")

    f.write("\n")

    for v in verts:
        nx, ny, nz = v["normal"]
        f.write(f"vn {nx} {ny} {nz}\n")

    f.write("\n")

    for n in range(0, len(indices), 3):
        a, b, c = indices[n:n+3]

        # Wavefront indexing starts at 1.
        a += 1
        b += 1
        c += 1

        # Same source index selects position, UV, and normal.
        f.write(
            f"f {a}/{a}/{a} {b}/{b}/{b} {c}/{c}/{c}\n"
        )

print(f"Wrote:     {dst}")
print(f"Vertices:  {len(verts)}")
print(f"Triangles: {len(indices) // 3}")
