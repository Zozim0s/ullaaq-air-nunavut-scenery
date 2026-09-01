#!/usr/bin/env python3

import argparse
import os
import subprocess
from pathlib import Path

XP = Path.home() / "linGames/X-Plane 12"
DEFAULT_SCENERY = XP / "Resources/default scenery"


IMAGE_DIRECTIVES = {
    "BASE_TEX",
    "BORDER_TEX",
    "COMPOSITE_TEX",
    "COMPOSITE_NOISE",
    "NORMAL_METALNESS",
    "NORMAL_TEX",
}


def build_library_index():
    index = {}

    for lib in DEFAULT_SCENERY.rglob("library.txt"):
        try:
            lines = lib.read_text(errors="replace").splitlines()
        except OSError:
            continue

        for raw in lines:
            line = raw.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split(None, 2)
            if len(parts) != 3:
                continue

            directive, virtual, actual = parts

            if directive not in {
                "EXPORT",
                "EXPORT_BACKUP",
                "EXPORT_EXTEND",
            }:
                continue

            candidate = (lib.parent / actual).resolve()

            # Prefer the first real file found.
            if virtual not in index and candidate.exists():
                index[virtual] = candidate

    return index


def identify(path):
    if not path.exists():
        return "MISSING"

    try:
        result = subprocess.run(
            ["magick", "identify", str(path)],
            text=True,
            capture_output=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception as exc:
        return f"identify failed: {exc}"


def resolve_relative(owner, value):
    return (owner.parent / value).resolve()


def parse_file(path):
    records = []

    for raw in path.read_text(errors="replace").splitlines():
        line = raw.strip()

        if not line or line.startswith("#"):
            continue

        parts = line.split()
        records.append((parts[0], parts[1:]))

    return records


def inspect_decal(path):
    print()
    print("DECAL")
    print(f"  file: {path}")

    for directive, args in parse_file(path):
        if directive in {"A", "DECAL"}:
            continue

        if directive == "DECAL_PARAMS_PROJ":
            print(f"  {directive}: {' '.join(args)}")

            if args:
                texture = resolve_relative(path, args[-1])
                print(f"    texture: {texture}")
                print(f"    image:   {identify(texture)}")
        else:
            print(f"  {directive}: {' '.join(args)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("terrain", type=Path)
    args = parser.parse_args()

    terrain = args.terrain.expanduser().resolve()

    if not terrain.exists():
        raise SystemExit(f"Terrain not found: {terrain}")

    library = build_library_index()

    print("=" * 72)
    print(terrain.name)
    print("=" * 72)
    print(f"file: {terrain}")
    print()

    for directive, values in parse_file(terrain):
        if directive in {"A", "TERRAIN"}:
            continue

        value = " ".join(values)

        if directive in IMAGE_DIRECTIVES and values:
            path = resolve_relative(terrain, values[0])

            print(directive)
            print(f"  source: {values[0]}")
            print(f"  file:   {path}")
            print(f"  image:  {identify(path)}")
            print()

        elif directive == "DECAL_LIB" and values:
            virtual = values[0]
            resolved = library.get(virtual)

            print("DECAL_LIB")
            print(f"  virtual: {virtual}")

            if resolved:
                print(f"  file:    {resolved}")
                inspect_decal(resolved)
            else:
                print("  file:    UNRESOLVED")

            print()

        else:
            print(f"{directive}: {value}")


if __name__ == "__main__":
    main()
