#!/usr/bin/env python3
"""Audit or apply Ullaaq's current Ortho4XP water-rendering policy."""

from __future__ import annotations
import argparse, shutil
from datetime import datetime
from pathlib import Path

DESIRED = {
    "water_tech": "XP12",
    "ratio_water": "1.0",
    "use_masks_for_inland": "False",
}

def parse(text):
    d = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        d[k.strip()] = v.strip()
    return d

def rewrite(text):
    seen = set()
    out = []
    for raw in text.splitlines():
        if "=" in raw and not raw.lstrip().startswith("#"):
            key = raw.split("=", 1)[0].strip()
            if key in DESIRED:
                out.append(f"{key}={DESIRED[key]}")
                seen.add(key)
                continue
        out.append(raw)
    for key, val in DESIRED.items():
        if key not in seen:
            out.append(f"{key}={val}")
    return "\n".join(out) + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cfg", type=Path)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    path = args.cfg.expanduser()
    text = path.read_text()
    current = parse(text)
    ok = True

    for key, wanted in DESIRED.items():
        got = current.get(key, "<missing>")
        match = got == wanted
        ok &= match
        print(f"{key:24} {got:16} wanted {wanted:8} [{'OK' if match else 'CHANGE'}]")

    if not args.apply:
        raise SystemExit(0 if ok else 1)
    if ok:
        print("Already configured.")
        return

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(path.name + f".pre-ullaaq-water-{stamp}")
    shutil.copy2(path, backup)
    path.write_text(rewrite(text))
    print(f"Backup:  {backup}")
    print(f"Updated: {path}")
    print("Restart Ortho4XP before using the new settings.")

if __name__ == "__main__":
    main()
