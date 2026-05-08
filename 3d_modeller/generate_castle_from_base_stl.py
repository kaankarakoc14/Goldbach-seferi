"""
Custom Castle Generator — uses an existing STL as the base.

- Reads a binary STL from an absolute path (BASE_STL_PATH)
- Recenters it to (0,0), keeps bottom at z=0
- Builds a simple "mosque-like" castle on top:
  - 4 corner columns
  - 1 central larger column
  - Conical domes ("triangular-ish circular") on top of columns

Output: kale_custom_from_base.stl (binary STL)
"""

import math
import os
import struct
from typing import Iterable, List, Tuple

Vec3 = Tuple[float, float, float]
Tri = Tuple[Vec3, Vec3, Vec3]

# === INPUT ===
BASE_STL_PATH = "/Users/kaan/Downloads/Powerful Gaaris-Uusam (2).stl"

# === OUTPUT ===
OUT_NAME = "kale_custom_from_base.stl"

# Geometry knobs (kept intentionally simple)
SEGMENTS = 24  # circle resolution; larger = smoother, more triangles


def read_binary_stl(path: str) -> List[Tri]:
    with open(path, "rb") as f:
        f.read(80)
        n = struct.unpack("<I", f.read(4))[0]
        tris: List[Tri] = []
        for _ in range(n):
            f.read(12)  # normal
            v1 = struct.unpack("<fff", f.read(12))
            v2 = struct.unpack("<fff", f.read(12))
            v3 = struct.unpack("<fff", f.read(12))
            f.read(2)  # attr
            tris.append((v1, v2, v3))
    return tris


def write_binary_stl(path: str, triangles: Iterable[Tri], name: str = "model") -> None:
    triangles = list(triangles)
    with open(path, "wb") as f:
        header = name.ljust(80)[:80].encode("ascii", errors="replace")
        f.write(header)
        f.write(struct.pack("<I", len(triangles)))
        for v1, v2, v3 in triangles:
            ux, uy, uz = (v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2])
            vx, vy, vz = (v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2])
            nx = uy * vz - uz * vy
            ny = uz * vx - ux * vz
            nz = ux * vy - uy * vx
            length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            nx, ny, nz = nx / length, ny / length, nz / length
            f.write(struct.pack("<fff", nx, ny, nz))
            f.write(struct.pack("<fff", *v1))
            f.write(struct.pack("<fff", *v2))
            f.write(struct.pack("<fff", *v3))
            f.write(struct.pack("<H", 0))


def bbox(tris: Iterable[Tri]) -> Tuple[Vec3, Vec3]:
    minx = miny = minz = 1e9
    maxx = maxy = maxz = -1e9
    for a, b, c in tris:
        for x, y, z in (a, b, c):
            minx = min(minx, x)
            miny = min(miny, y)
            minz = min(minz, z)
            maxx = max(maxx, x)
            maxy = max(maxy, y)
            maxz = max(maxz, z)
    return (minx, miny, minz), (maxx, maxy, maxz)


def translate(tris: Iterable[Tri], dx: float, dy: float, dz: float) -> List[Tri]:
    out: List[Tri] = []
    for a, b, c in tris:
        out.append(
            (
                (a[0] + dx, a[1] + dy, a[2] + dz),
                (b[0] + dx, b[1] + dy, b[2] + dz),
                (c[0] + dx, c[1] + dy, c[2] + dz),
            )
        )
    return out


def _circle_xy(cx: float, cy: float, r: float, segments: int) -> List[Tuple[float, float]]:
    pts = []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def cylinder(cx: float, cy: float, z0: float, h: float, r: float, segments: int) -> List[Tri]:
    z1 = z0 + h
    ring0 = _circle_xy(cx, cy, r, segments)
    ring1 = ring0  # same xy
    tris: List[Tri] = []
    # caps
    c0 = (cx, cy, z0)
    c1 = (cx, cy, z1)
    for i in range(segments):
        j = (i + 1) % segments
        x0, y0 = ring0[i]
        x1, y1 = ring0[j]
        tris.append((c0, (x1, y1, z0), (x0, y0, z0)))
        tris.append((c1, (x0, y0, z1), (x1, y1, z1)))
    # sides
    for i in range(segments):
        j = (i + 1) % segments
        x0, y0 = ring0[i]
        x1, y1 = ring0[j]
        tris.append(((x0, y0, z0), (x1, y1, z0), (x1, y1, z1)))
        tris.append(((x0, y0, z0), (x1, y1, z1), (x0, y0, z1)))
    return tris


def cone(cx: float, cy: float, z0: float, h: float, r_base: float, segments: int) -> List[Tri]:
    """Simple cone (circular base, point apex)."""
    z1 = z0 + h
    apex = (cx, cy, z1)
    ring = _circle_xy(cx, cy, r_base, segments)
    tris: List[Tri] = []
    # base cap
    c0 = (cx, cy, z0)
    for i in range(segments):
        j = (i + 1) % segments
        x0, y0 = ring[i]
        x1, y1 = ring[j]
        tris.append((c0, (x1, y1, z0), (x0, y0, z0)))
    # sides
    for i in range(segments):
        j = (i + 1) % segments
        x0, y0 = ring[i]
        x1, y1 = ring[j]
        tris.append(((x0, y0, z0), (x1, y1, z0), apex))
    return tris


def frustum(cx: float, cy: float, z0: float, h: float, r0: float, r1: float, segments: int) -> List[Tri]:
    """Truncated cone (mountain / pedestal)."""
    z1 = z0 + h
    ring0 = _circle_xy(cx, cy, r0, segments)
    ring1 = _circle_xy(cx, cy, r1, segments)
    tris: List[Tri] = []
    c0 = (cx, cy, z0)
    c1 = (cx, cy, z1)
    # caps
    for i in range(segments):
        j = (i + 1) % segments
        x0, y0 = ring0[i]
        x1, y1 = ring0[j]
        tris.append((c0, (x1, y1, z0), (x0, y0, z0)))
    for i in range(segments):
        j = (i + 1) % segments
        x0, y0 = ring1[i]
        x1, y1 = ring1[j]
        tris.append((c1, (x0, y0, z1), (x1, y1, z1)))
    # sides
    for i in range(segments):
        j = (i + 1) % segments
        x00, y00 = ring0[i]
        x01, y01 = ring0[j]
        x10, y10 = ring1[i]
        x11, y11 = ring1[j]
        tris.append(((x00, y00, z0), (x01, y01, z0), (x11, y11, z1)))
        tris.append(((x00, y00, z0), (x11, y11, z1), (x10, y10, z1)))
    return tris


def main() -> None:
    base = read_binary_stl(BASE_STL_PATH)
    (minx, miny, minz), (maxx, maxy, maxz) = bbox(base)

    # Recenter to (0,0) and bottom to z=0
    cx = (minx + maxx) / 2.0
    cy = (miny + maxy) / 2.0
    base = translate(base, -cx, -cy, -minz)
    top_z = maxz - minz

    bw = (maxx - minx)
    bh = (maxy - miny)
    base_r = min(bw, bh) / 2.0

    # Proportions derived from base size (kept intentionally simple)
    col_r = max(0.9, base_r * 0.10)
    col_h = max(10.0, base_r * 0.95)
    dome_h = max(6.0, base_r * 0.55)
    dome_r = col_r * 1.35

    # More majestic center
    center_col_r = col_r * 1.75
    center_col_h = col_h * 1.45
    center_dome_h = dome_h * 1.35
    center_dome_r = dome_r * 1.55

    # "Mountain" pedestal under the columns (castle on a hill)
    mound_h = max(4.0, base_r * 0.55)
    mound_r0 = base_r * 0.95
    # Keep a wider top so corner columns don't look like floating
    mound_r1 = base_r * 0.55

    # Column positions (a bit inset from edges)
    inset = base_r * 0.58
    pts = [
        (+inset, +inset),
        (+inset, -inset),
        (-inset, +inset),
        (-inset, -inset),
    ]

    tris: List[Tri] = []
    tris.extend(base)

    # pedestal first
    tris.extend(frustum(0.0, 0.0, top_z, mound_h, mound_r0, mound_r1, SEGMENTS))
    z_start = top_z + mound_h
    # Let small columns start a bit lower to visibly "touch" the mound
    z_start_small = top_z + mound_h * 0.65

    # 4 corner columns + domes
    for x, y in pts:
        tris.extend(cylinder(x, y, z_start_small, col_h, col_r, SEGMENTS))
        tris.extend(cone(x, y, z_start_small + col_h, dome_h, dome_r, SEGMENTS))

    # central main column + dome
    tris.extend(cylinder(0.0, 0.0, z_start, center_col_h, center_col_r, SEGMENTS))
    tris.extend(cone(0.0, 0.0, z_start + center_col_h, center_dome_h, center_dome_r, SEGMENTS))

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUT_NAME)
    write_binary_stl(out_path, tris, name="GoldbachCastleCustom")
    print("Wrote:", out_path)
    print("Base bbox (mm):", round(bw, 2), "x", round(bh, 2), "x", round(top_z, 2))
    print("Triangles:", len(tris))


if __name__ == "__main__":
    main()

