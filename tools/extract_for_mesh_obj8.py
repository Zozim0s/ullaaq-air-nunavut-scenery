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

vertices = []
indices = []
vcount = None
icount = None
found = False

for i, line in enumerate(lines):
    p = line.split()
    if not p:
        continue

    if p[0] == "MESH" and len(p) >= 6 and p[1] == mesh_name:
        found = True
        vcount = int(p[4])
        icount = int(p[5])

        j = i + 1

        # Read this mesh's vertices.
        while j < len(lines) and len(vertices) < vcount:
            q = lines[j].split()
            if q and q[0] == "VERTEX":
                vals = q[1:]
                if len(vals) < 8:
                    raise RuntimeError(f"Bad VERTEX line: {lines[j]}")
                # OBJ8 VT needs xyz, normal xyz, uv.
                vertices.append(vals[:8])
            j += 1

        # Read this mesh's index table.
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

        break

if not found:
    raise SystemExit(f"Mesh not found: {mesh_name}")

if len(vertices) != vcount:
    raise SystemExit(
        f"Vertex count mismatch: expected {vcount}, got {len(vertices)}"
    )

if len(indices) < icount:
    raise SystemExit(
        f"Index count mismatch: expected {icount}, got {len(indices)}"
    )

indices = indices[:icount]

dst.parent.mkdir(parents=True, exist_ok=True)

with dst.open("w") as f:
    f.write("A\n")
    f.write("800\n")
    f.write("OBJ\n\n")

    f.write("TEXTURE trees_3D1_ALB_fa.png\n")
    f.write("TEXTURE_NORMAL 1.0 trees_3D1_NML_fa.png\n\n")

    f.write(f"POINT_COUNTS {vcount} 0 0 {icount}\n\n")

    for v in vertices:
        f.write("VT " + " ".join(v) + "\n")

    f.write("\n")

    n = 0
    while n < len(indices):
        chunk = indices[n:n+10]
        if len(chunk) == 10:
            f.write("IDX10 " + " ".join(map(str, chunk)) + "\n")
        else:
            for idx in chunk:
                f.write(f"IDX {idx}\n")
        n += len(chunk)

    f.write("\n")
    f.write("ATTR_no_blend 0.5\n")
    f.write(f"TRIS 0 {icount}\n")

print(f"Wrote:     {dst}")
print(f"Vertices:  {vcount}")
print(f"Indices:   {icount}")
print(f"Triangles: {icount // 3}")
