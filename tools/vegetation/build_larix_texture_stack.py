#!/usr/bin/env python3
"""
Build first-pass X-Plane 12 Larix vegetation support textures.

Creates, from the existing albedo textures:
    3-D NML  : flat tangent normals + translucency mask in blue
    3-D SM   : provisional weather/snow mask from albedo alpha
    BB NML   : flat tangent normals + translucency mask in blue
    BB SM    : provisional weather/snow mask from albedo alpha

This is deliberately a CONTROL stack, not final art.  The goal is to get the
full SHADER_2D / SHADER_3D material plumbing active before adding detailed
normal or weather behavior.

X-Plane 12 vegetation NORMAL_TRANSLUCENCY:
    R/G = tangent-space normal X/Y
    B   = translucency (255 foliage, 0 solid wood)

The 3-D trunk strip defaults to the current Ullaaq Larix UV reservation:
    U 0.00000 .. 0.03125
    V 0.75000 .. 1.00000

PNG image coordinates are top-down, while UV V is bottom-up, so the script
converts the rectangle automatically.

Requires: Pillow
    python3 -m pip install Pillow
"""

from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image


def parse_uv_rect(text: str):
    vals = [float(x.strip()) for x in text.split(",")]
    if len(vals) != 4:
        raise argparse.ArgumentTypeError("UV rect must be u0,v0,u1,v1")
    u0, v0, u1, v1 = vals
    if not (0 <= u0 <= u1 <= 1 and 0 <= v0 <= v1 <= 1):
        raise argparse.ArgumentTypeError("UV values must satisfy 0<=u0<=u1<=1 and 0<=v0<=v1<=1")
    return u0, v0, u1, v1


def build_maps(
    albedo_path: Path,
    nml_path: Path,
    sm_path: Path,
    *,
    trunk_uv=None,
    alpha_threshold: int = 8,
):
    im = Image.open(albedo_path).convert("RGBA")
    w, h = im.size
    px = im.load()

    # RGB normal/translucency texture:
    # R/G = neutral tangent normal, B = translucency.
    nml = Image.new("RGB", (w, h), (128, 128, 0))
    npx = nml.load()

    # Provisional weather mask, RGB for maximum compatibility.
    # Preserve the albedo alpha as a soft coverage mask.
    sm = Image.new("RGB", (w, h), (0, 0, 0))
    spx = sm.load()

    for y in range(h):
        for x in range(w):
            a = px[x, y][3]
            visible = a >= alpha_threshold
            b = 255 if visible else 0
            npx[x, y] = (128, 128, b)
            spx[x, y] = (a, a, a)

    # Solid trunk / leader region: translucency B = 0.
    if trunk_uv is not None:
        u0, v0, u1, v1 = trunk_uv
        x0 = max(0, min(w, round(u0 * w)))
        x1 = max(0, min(w, round(u1 * w)))

        # UV V=1 is image top, UV V=0 is image bottom.
        y0 = max(0, min(h, round((1.0 - v1) * h)))
        y1 = max(0, min(h, round((1.0 - v0) * h)))

        for y in range(y0, y1):
            for x in range(x0, x1):
                if px[x, y][3] >= alpha_threshold:
                    npx[x, y] = (128, 128, 0)

    nml.save(nml_path)
    sm.save(sm_path)

    print(f"{albedo_path.name}: {w}x{h}")
    print(f"  -> {nml_path}")
    print(f"  -> {sm_path}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--atlas",
        default="larix_laricina_atlas_test2.png",
        help="3-D albedo atlas",
    )
    p.add_argument(
        "--billboard",
        default="larix_laricina_billboard_test1.png",
        help="2-D billboard albedo",
    )
    p.add_argument(
        "--outdir",
        default=".",
        help="output directory (default: current directory)",
    )
    p.add_argument(
        "--trunk-uv",
        type=parse_uv_rect,
        default=parse_uv_rect("0.0,0.75,0.03125,1.0"),
        help="3-D solid-wood UV rect u0,v0,u1,v1",
    )
    p.add_argument(
        "--alpha-threshold",
        type=int,
        default=8,
        help="alpha value treated as visible for translucency (default 8)",
    )
    args = p.parse_args()

    atlas = Path(args.atlas)
    billboard = Path(args.billboard)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    build_maps(
        atlas,
        outdir / "larix_laricina_atlas_NML.png",
        outdir / "larix_laricina_atlas_SM.png",
        trunk_uv=args.trunk_uv,
        alpha_threshold=args.alpha_threshold,
    )

    # At billboard distance, treating the visible crown as foliage is a good
    # neutral first-pass control.  We can carve the trunk later if necessary.
    build_maps(
        billboard,
        outdir / "larix_laricina_billboard_NML.png",
        outdir / "larix_laricina_billboard_SM.png",
        trunk_uv=None,
        alpha_threshold=args.alpha_threshold,
    )


if __name__ == "__main__":
    main()

