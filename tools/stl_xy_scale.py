#!/usr/bin/env python3
"""
Scale STL geometry in X/Y (keep Z unchanged).

Creates new STL files (binary) with recomputed facet normals.
"""

from __future__ import annotations

import argparse
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


Vec3 = Tuple[float, float, float]
Tri = Tuple[Vec3, Vec3, Vec3]


@dataclass
class Mesh:
    triangles: List[Tri]

    def bounds(self) -> Tuple[Vec3, Vec3]:
        if not self.triangles:
            return (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
        minx = miny = minz = float("inf")
        maxx = maxy = maxz = float("-inf")
        for tri in self.triangles:
            for (x, y, z) in tri:
                if x < minx:
                    minx = x
                if y < miny:
                    miny = y
                if z < minz:
                    minz = z
                if x > maxx:
                    maxx = x
                if y > maxy:
                    maxy = y
                if z > maxz:
                    maxz = z
        return (minx, miny, minz), (maxx, maxy, maxz)

    def size(self) -> Vec3:
        b0, b1 = self.bounds()
        return (b1[0] - b0[0], b1[1] - b0[1], b1[2] - b0[2])

    def scale_xy_about_center(self, sx: float, sy: float) -> "Mesh":
        (minx, miny, _), (maxx, maxy, _) = self.bounds()
        cx = (minx + maxx) / 2.0
        cy = (miny + maxy) / 2.0

        def t(v: Vec3) -> Vec3:
            x, y, z = v
            return (cx + (x - cx) * sx, cy + (y - cy) * sy, z)

        return Mesh(triangles=[(t(a), t(b), t(c)) for (a, b, c) in self.triangles])

    def translate(self, dx: float, dy: float, dz: float) -> "Mesh":
        def t(v: Vec3) -> Vec3:
            return (v[0] + dx, v[1] + dy, v[2] + dz)

        return Mesh(triangles=[(t(a), t(b), t(c)) for (a, b, c) in self.triangles])

    def union(self, other: "Mesh") -> "Mesh":
        # No boolean: just merge triangles; slicers generally handle overlaps.
        return Mesh(triangles=[*self.triangles, *other.triangles])


def _triangle_area(a: Vec3, b: Vec3, c: Vec3) -> float:
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    cr = (
        ab[1] * ac[2] - ab[2] * ac[1],
        ab[2] * ac[0] - ab[0] * ac[2],
        ab[0] * ac[1] - ab[1] * ac[0],
    )
    return 0.5 * math.sqrt(cr[0] * cr[0] + cr[1] * cr[1] + cr[2] * cr[2])


def _quant(v: Vec3, nd: int = 5) -> Tuple[float, float, float]:
    return (round(v[0], nd), round(v[1], nd), round(v[2], nd))


def _edge_key(p: Tuple[float, float, float], q: Tuple[float, float, float]):
    if p <= q:
        return (p, q)
    return (q, p)


def triangle_components(mesh: Mesh) -> List[List[int]]:
    """Connected components by shared triangle edges (vertex keys quantized)."""
    tris = mesh.triangles
    edge_to_tris: dict = {}
    for ti, (a, b, c) in enumerate(tris):
        vs = [_quant(a), _quant(b), _quant(c)]
        for e in (
            _edge_key(vs[0], vs[1]),
            _edge_key(vs[1], vs[2]),
            _edge_key(vs[2], vs[0]),
        ):
            edge_to_tris.setdefault(e, []).append(ti)
    adj: List[set] = [set() for _ in tris]
    for tlist in edge_to_tris.values():
        if len(tlist) < 2:
            continue
        for i in range(len(tlist)):
            for j in range(i + 1, len(tlist)):
                u, v = tlist[i], tlist[j]
                adj[u].add(v)
                adj[v].add(u)
    seen = [False] * len(tris)
    comps: List[List[int]] = []
    for i in range(len(tris)):
        if seen[i]:
            continue
        stack = [i]
        seen[i] = True
        comp: List[int] = []
        while stack:
            u = stack.pop()
            comp.append(u)
            for v in adj[u]:
                if not seen[v]:
                    seen[v] = True
                    stack.append(v)
        comps.append(comp)
    return comps


def _verts_from_tri_indices(tris: List[Tri], idxs: List[int]) -> List[Vec3]:
    out: List[Vec3] = []
    for ti in idxs:
        out.extend(tris[ti])
    return out


def _centroid(pts: List[Vec3]) -> Vec3:
    sx = sy = sz = 0.0
    for (x, y, z) in pts:
        sx += x
        sy += y
        sz += z
    n = float(len(pts))
    return (sx / n, sy / n, sz / n)


def _min_dist_between_point_sets(a: List[Vec3], b: List[Vec3]) -> Tuple[float, Vec3, Vec3]:
    md = float("inf")
    pa = pb = a[0]
    for va in a:
        for vb in b:
            dx = va[0] - vb[0]
            dy = va[1] - vb[1]
            dz = va[2] - vb[2]
            d = math.sqrt(dx * dx + dy * dy + dz * dz)
            if d < md:
                md = d
                pa, pb = va, vb
    return md, pa, pb


def _vdot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _vlen(a: Vec3) -> float:
    return math.sqrt(_vdot(a, a))


def _vadd(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _vmul(a: Vec3, s: float) -> Vec3:
    return (a[0] * s, a[1] * s, a[2] * s)


def _vnorm(a: Vec3) -> Vec3:
    l = _vlen(a)
    if l == 0.0:
        return (0.0, 0.0, 1.0)
    return (a[0] / l, a[1] / l, a[2] / l)


def _vsub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _orthonormal_frame_along(d_unit: Vec3) -> Tuple[Vec3, Vec3]:
    ref = (0.0, 0.0, 1.0)
    if abs(_vdot(d_unit, ref)) > 0.95:
        ref = (0.0, 1.0, 0.0)
    u = _vnorm(_cross(d_unit, ref))
    v = _cross(d_unit, u)
    return u, v


def make_beam_box(p0: Vec3, p1: Vec3, half_h: float, half_w: float) -> Mesh:
    """Thin box beam from p0 to p1, rectangular section (2*half_h) x (2*half_w)."""
    dvec = _vsub(p1, p0)
    L = _vlen(dvec)
    if L < 1e-5:
        p1 = _vadd(p0, (0.0, 0.0, 0.35))
        dvec = (0.0, 0.0, 0.35)
        L = 0.35
    d = _vnorm(dvec)
    u, v = _orthonormal_frame_along(d)
    c = _vadd(p0, p1)
    c = (c[0] * 0.5, c[1] * 0.5, c[2] * 0.5)

    def corner(sL: float, su: float, sv: float) -> Vec3:
        return (
            c[0] + d[0] * sL * L * 0.5 + u[0] * su * half_h + v[0] * sv * half_w,
            c[1] + d[1] * sL * L * 0.5 + u[1] * su * half_h + v[1] * sv * half_w,
            c[2] + d[2] * sL * L * 0.5 + u[2] * su * half_h + v[2] * sv * half_w,
        )

    v000 = corner(-1, -1, -1)
    v100 = corner(1, -1, -1)
    v110 = corner(1, 1, -1)
    v010 = corner(-1, 1, -1)
    v001 = corner(-1, -1, 1)
    v101 = corner(1, -1, 1)
    v111 = corner(1, 1, 1)
    v011 = corner(-1, 1, 1)
    tris: List[Tri] = []
    tris += [(v000, v110, v100), (v000, v010, v110)]
    tris += [(v001, v101, v111), (v001, v111, v011)]
    tris += [(v100, v110, v111), (v100, v111, v101)]
    tris += [(v000, v001, v011), (v000, v011, v010)]
    tris += [(v010, v011, v111), (v010, v111, v110)]
    tris += [(v000, v100, v101), (v000, v101, v001)]
    return Mesh(triangles=tris)


def bridge_mesh_islands(mesh: Mesh, half_thick: float = 0.22, extend_mm: float = 0.28) -> Mesh:
    """
    Connect disconnected triangle islands with thin beams to the largest island.
    Fixes slicer 'floating' / separate body warnings on broken STL exports.
    """
    comps = triangle_components(mesh)
    if len(comps) <= 1:
        return mesh
    scored: List[Tuple[float, List[int]]] = []
    for comp in comps:
        a = sum(_triangle_area(*mesh.triangles[i]) for i in comp)
        scored.append((a, comp))
    scored.sort(key=lambda t: -t[0])
    main = scored[0][1]
    vm = _verts_from_tri_indices(mesh.triangles, main)
    (minx, miny, _), (maxx, maxy, _) = mesh.bounds()
    # Keep beams inside the piece footprint so XY bounds don't grow.
    clamp_margin = max(half_thick * 1.6, 0.35)
    out = mesh
    for _, comp in scored[1:]:
        vs = _verts_from_tri_indices(mesh.triangles, comp)
        md, pa, pb = _min_dist_between_point_sets(vs, vm)
        if md < 0.02:
            cs = _centroid(vs)
            cM = _centroid(vm)
            d = _vsub(cs, cM)
            if _vlen(d) < 0.05:
                d = (1.0, 0.0, 0.0)
            d = _vnorm(d)
            pa = _vadd(cM, _vmul(d, 0.12))
            pb = _vsub(cs, _vmul(d, 0.12))
        dseg = _vsub(pb, pa)
        if _vlen(dseg) > 1e-6:
            du = _vnorm(dseg)
            pa = _vsub(pa, _vmul(du, extend_mm))
            pb = _vadd(pb, _vmul(du, extend_mm))
        pa = (
            min(max(pa[0], minx + clamp_margin), maxx - clamp_margin),
            min(max(pa[1], miny + clamp_margin), maxy - clamp_margin),
            pa[2],
        )
        pb = (
            min(max(pb[0], minx + clamp_margin), maxx - clamp_margin),
            min(max(pb[1], miny + clamp_margin), maxy - clamp_margin),
            pb[2],
        )
        out = out.union(make_beam_box(pa, pb, half_thick, half_thick))
    return out


def make_box(min_corner: Vec3, max_corner: Vec3) -> Mesh:
    x0, y0, z0 = min_corner
    x1, y1, z1 = max_corner
    v000 = (x0, y0, z0)
    v100 = (x1, y0, z0)
    v110 = (x1, y1, z0)
    v010 = (x0, y1, z0)
    v001 = (x0, y0, z1)
    v101 = (x1, y0, z1)
    v111 = (x1, y1, z1)
    v011 = (x0, y1, z1)

    tris: List[Tri] = []
    # bottom (z0)
    tris += [(v000, v110, v100), (v000, v010, v110)]
    # top (z1)
    tris += [(v001, v101, v111), (v001, v111, v011)]
    # +X
    tris += [(v100, v110, v111), (v100, v111, v101)]
    # -X
    tris += [(v000, v001, v011), (v000, v011, v010)]
    # +Y
    tris += [(v010, v011, v111), (v010, v111, v110)]
    # -Y
    tris += [(v000, v100, v101), (v000, v101, v001)]
    return Mesh(triangles=tris)

def make_prism_from_polygon_xy(points_xy: List[Tuple[float, float]], z0: float, z1: float) -> Mesh:
    """
    Create a closed prism from a simple (non-self-intersecting) polygon in XY.
    Polygon should be CCW for outward normals consistency (not critical for STL).
    """
    if len(points_xy) < 3:
        return Mesh(triangles=[])

    # Top and bottom vertices
    bot = [(x, y, z0) for (x, y) in points_xy]
    top = [(x, y, z1) for (x, y) in points_xy]
    n = len(points_xy)

    tris: List[Tri] = []

    # Bottom fan (CW so normal points -Z)
    for i in range(1, n - 1):
        tris.append((bot[0], bot[i + 1], bot[i]))

    # Top fan (CCW so normal points +Z)
    for i in range(1, n - 1):
        tris.append((top[0], top[i], top[i + 1]))

    # Sides
    for i in range(n):
        j = (i + 1) % n
        v00 = bot[i]
        v10 = bot[j]
        v11 = top[j]
        v01 = top[i]
        tris.append((v00, v10, v11))
        tris.append((v00, v11, v01))

    return Mesh(triangles=tris)


def regular_polygon_xy(sides: int, radius: float, center: Tuple[float, float] = (0.0, 0.0), rotation_rad: float = 0.0):
    cx, cy = center
    pts: List[Tuple[float, float]] = []
    for k in range(sides):
        a = rotation_rad + (2.0 * math.pi * k) / float(sides)
        pts.append((cx + radius * math.cos(a), cy + radius * math.sin(a)))
    return pts


def _convex_hull_xy(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    # Monotonic chain hull, returns CCW hull without duplicate endpoint.
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: List[Tuple[float, float]] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: List[Tuple[float, float]] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def horse_like_peg_polygon_xy(width_mm: float, height_mm: float) -> List[Tuple[float, float]]:
    """
    Simple 'horse head' like silhouette via convex hull of a few anchor points.
    This is not an artistic knight, but it keys the part without supports.
    """
    w = width_mm
    h = height_mm
    # Anchor points roughly like a head+neck
    raw = [
        (-w * 0.50, -h * 0.35),
        (-w * 0.50, h * 0.35),
        (-w * 0.05, h * 0.52),
        (w * 0.40, h * 0.32),
        (w * 0.50, 0.0),
        (w * 0.38, -h * 0.45),
        (w * 0.05, -h * 0.55),
        (-w * 0.15, -h * 0.52),
    ]
    return _convex_hull_xy(raw)


def add_bottom_peg(mesh: Mesh, peg_poly_xy: List[Tuple[float, float]], peg_depth_mm: float = 2.2) -> Mesh:
    (minx, miny, minz), (maxx, maxy, maxz) = mesh.bounds()
    cx = (minx + maxx) / 2.0
    cy = (miny + maxy) / 2.0
    # Center peg under piece
    pts = [(cx + x, cy + y) for (x, y) in peg_poly_xy]
    peg = make_prism_from_polygon_xy(pts, minz - peg_depth_mm, minz)
    return mesh.union(peg)


def make_supportless_castle_token(
    across_mm: float,
    height_mm: float,
    base_thickness_mm: float = 2.6,
    crenel_height_mm: float = 3.2,
    wall_margin_mm: float = 1.1,
) -> Mesh:
    """
    Single-piece, supportless castle token for pentagon slots.
    - Base: regular pentagon prism (no overhang).
    - Top: 5 crenellations placed on edges, kept inside footprint.
    """
    # Use circumradius so that bounding circle diameter ~= across_mm
    r = across_mm / 2.0
    # Flat-ish orientation: one vertex up
    pent = regular_polygon_xy(5, r, rotation_rad=math.pi / 2.0)
    base = make_prism_from_polygon_xy(pent, 0.0, base_thickness_mm)

    # Single-piece tower: just a regular pentagon prism.
    # This guarantees no floating parts and no supports.
    body = make_prism_from_polygon_xy(pent, 0.0, height_mm)
    # Slightly thicker first layers for strength (fully overlapping).
    return body.union(base)


def make_supportless_castle_with_flag_and_peg(
    across_mm: float,
    height_mm: float,
    peg_w_mm: float = 8.6,
    peg_h_mm: float = 10.0,
    peg_depth_mm: float = 2.2,
    flag_w_mm: float = 7.0,
    flag_t_mm: float = 1.2,
    flag_h_mm: float = 8.0,
) -> Mesh:
    """
    Castle token with a vertical flag (supportless) and a bottom key peg.
    The peg is 'horse-like' to align with a board recess.
    """
    castle = make_supportless_castle_token(across_mm=across_mm, height_mm=height_mm, base_thickness_mm=3.0)
    (minx, miny, minz), (maxx, maxy, maxz) = castle.bounds()
    cx = (minx + maxx) / 2.0
    cy = (miny + maxy) / 2.0

    # Flag: vertical thin plate near one edge, no overhang.
    inset = max(1.2, (maxx - minx) * 0.10)
    fx = maxx - inset - flag_t_mm / 2.0
    flag = make_box(
        (fx - flag_t_mm / 2.0, cy - flag_w_mm / 2.0, maxz - 2.0),
        (fx + flag_t_mm / 2.0, cy + flag_w_mm / 2.0, maxz - 2.0 + flag_h_mm),
    )

    peg_poly = horse_like_peg_polygon_xy(peg_w_mm, peg_h_mm)
    castle = add_bottom_peg(castle.union(flag), peg_poly, peg_depth_mm=peg_depth_mm)
    return castle


def lift_to_z0(mesh: Mesh) -> Mesh:
    (minx, miny, minz), (maxx, maxy, maxz) = mesh.bounds()
    if minz == 0.0:
        return mesh
    return mesh.translate(0.0, 0.0, -minz)


def scale_to_match_board_with_clearance(
    piece: Mesh, board_scale_xy: float, clearance_total_mm: float
) -> float:
    """
    Assume board (and its slots) were uniformly scaled in XY by board_scale_xy.
    We scale the piece similarly, but subtract clearance_total_mm from the
    resulting max XY dimension to leave play.
    """
    px, py, _ = piece.size()
    base = max(px, py)
    target = max(0.01, base * board_scale_xy - clearance_total_mm)
    return target / base


def add_cavalry_saber_to_pul(
    mesh: Mesh,
    blade_submerge_mm: float = 1.15,
    blade_tip_lift_mm: float = 0.38,
    grip_lift_mm: float = 0.85,
) -> Mesh:
    """
    Çövalye (hafif kavisli değil, kompakt süvari) kılıcı: bıçağın bir kısmı pul
    kalınlığının içinde, uç alttan çıkmaz; kabza ve sap üstte tutma için.
    Tüm ekler pulun XY silüetinde kalır (yuvaya sığma).
    """
    (minx, miny, minz), (maxx, maxy, maxz) = mesh.bounds()
    cx = (minx + maxx) / 2.0
    cy = (miny + maxy) / 2.0
    thick = maxz - minz

    margin_x = max(0.55, (maxx - minx) * 0.06)
    margin_y = max(0.55, (maxy - miny) * 0.06)

    # --- Bıçak: +X yönünde diske doğru; içte tam gövde, dışarıda üst yüzeye çıkan ince segment
    x_outer_tip = maxx - margin_x * 0.55
    x_guard_inner = maxx - margin_x * 2.35
    x_blade_inner = cx - min(2.2, (maxx - minx) * 0.09)

    # Tamamen pul içinde kalan gövde (alt yüzeye dayalı, arkadan çıkmaz)
    blade_body = make_box(
        (x_blade_inner, cy - 0.48, minz),
        (x_guard_inner + 0.35, cy + 0.48, maxz - 0.12),
    )

    # Dış segment: Z'de bir kısmı gömülü, ince uç üstte (yarı gömülü görünüm)
    z_emerge_lo = max(minz + 0.12, maxz - min(blade_submerge_mm, thick * 0.55))
    z_emerge_hi = maxz + max(0.12, blade_tip_lift_mm)
    blade_emerge = make_box(
        (x_guard_inner - 0.25, cy - 0.38, z_emerge_lo),
        (x_outer_tip - 0.15, cy + 0.38, z_emerge_hi),
    )

    # Hafif kavis hissi: ikinci ince dilim (XY'de hafif ofset)
    blade_curve = make_box(
        (x_guard_inner + 0.15, cy - 0.22, z_emerge_lo + 0.08),
        (x_outer_tip - 0.55, cy + 0.62, z_emerge_hi - 0.05),
    )

    # --- Kabza (crossguard): Y geniş, ince Z
    gy0 = max(miny + margin_y, cy - 2.35)
    gy1 = min(maxy - margin_y, cy + 2.35)
    guard = make_box(
        (x_guard_inner - 0.55, gy0, maxz - 0.22),
        (x_guard_inner + 1.15, gy1, maxz + min(0.55, grip_lift_mm * 0.55)),
    )

    # --- Sap: tutma yeri, dış kenara yakın, üstte kabarık
    gx0 = max(minx + margin_x, x_guard_inner + 0.35)
    gx1 = maxx - margin_x * 0.65
    grip_core = make_box(
        (gx0, cy - 1.05, maxz - 0.08),
        (gx1, cy + 1.05, maxz + grip_lift_mm),
    )
    grip_bulge = make_box(
        (gx0 + 0.35, cy - 0.65, maxz + 0.12),
        (gx1 - 0.15, cy + 0.65, maxz + grip_lift_mm + 0.12),
    )

    return (
        mesh.union(blade_body)
        .union(blade_emerge)
        .union(blade_curve)
        .union(guard)
        .union(grip_core)
        .union(grip_bulge)
    )


def add_vertical_sword_to_pul(
    mesh: Mesh,
    sword_height_mm: float = 9.5,
    blade_len_mm: float = 10.5,
    blade_w_mm: float = 1.8,
    guard_w_mm: float = 6.2,
    guard_t_mm: float = 1.6,
    hilt_len_mm: float = 3.8,
    hilt_w_mm: float = 2.4,
    inset_mm: float = 1.2,
) -> Mesh:
    """
    Adds a supportless *vertical* sword embedded into the token.
    - All faces are vertical or flat (no overhangs), so no supports needed.
    - Stays inside the token XY bounds so it still fits the slot.
    """
    (minx, miny, minz), (maxx, maxy, maxz) = mesh.bounds()
    cx = (minx + maxx) / 2.0
    cy = (miny + maxy) / 2.0

    # Keep within XY silhouette
    x0 = minx + inset_mm
    x1 = maxx - inset_mm
    y0 = miny + inset_mm
    y1 = maxy - inset_mm

    L = min(blade_len_mm, max(3.0, x1 - x0))
    W = min(blade_w_mm, max(1.0, y1 - y0))

    # Place sword near one side (looks "stabbed"), but still inside bounds
    px = min(max(cx + (maxx - minx) * 0.22, x0 + L * 0.55), x1 - L * 0.55)
    py = cy

    # Blade footprint
    bx0 = px - L / 2.0
    bx1 = px + L / 2.0
    by0 = py - W / 2.0
    by1 = py + W / 2.0

    # Blade is "embedded": a short part goes down into the token.
    embed = min(1.4, (maxz - minz) * 0.55)
    z_blade0 = max(minz, maxz - embed)
    z_blade1 = maxz + sword_height_mm
    blade = make_box((bx0, by0, z_blade0), (bx1, by1, z_blade1))

    # Guard (crossguard) sits on the token top
    gw = min(guard_w_mm, max(3.0, y1 - y0))
    gt = min(guard_t_mm, max(1.0, x1 - x0) * 0.25)
    guard = make_box(
        (px - gt / 2.0, py - gw / 2.0, maxz),
        (px + gt / 2.0, py + gw / 2.0, maxz + 1.2),
    )

    # Hilt / grip above guard
    hl = min(hilt_len_mm, max(2.2, L * 0.45))
    hw = min(hilt_w_mm, gw * 0.45)
    hilt = make_box(
        (px - hl / 2.0, py - hw / 2.0, maxz + 1.2),
        (px + hl / 2.0, py + hw / 2.0, maxz + 1.2 + 2.6),
    )

    # Pommel cap
    pom = make_box(
        (px - hw / 2.2, py - hw / 2.2, maxz + 1.2 + 2.6),
        (px + hw / 2.2, py + hw / 2.2, maxz + 1.2 + 3.4),
    )

    return mesh.union(blade).union(guard).union(hilt).union(pom)


def _is_probably_binary_stl(data: bytes) -> bool:
    if len(data) < 84:
        return False
    # Binary STL: 80-byte header + uint32 count + 50 bytes per triangle
    tri_count = struct.unpack_from("<I", data, 80)[0]
    expected = 84 + 50 * tri_count
    if expected == len(data):
        return True
    # Many binary STLs start with "solid"; can't rely on that. Fallback: if it contains
    # non-ASCII early, treat as binary.
    head = data[:200]
    return any(b > 0x7F or b == 0 for b in head)


def load_stl(path: Path) -> Mesh:
    data = path.read_bytes()
    if _is_probably_binary_stl(data):
        return _load_binary_stl(data)
    return _load_ascii_stl(data)


def _load_binary_stl(data: bytes) -> Mesh:
    tri_count = struct.unpack_from("<I", data, 80)[0]
    offset = 84
    tris: List[Tri] = []
    # Each triangle: normal(12) + v1(12) + v2(12) + v3(12) + attr(2) = 50
    for _ in range(tri_count):
        # skip normal
        offset += 12
        v1 = struct.unpack_from("<fff", data, offset)
        offset += 12
        v2 = struct.unpack_from("<fff", data, offset)
        offset += 12
        v3 = struct.unpack_from("<fff", data, offset)
        offset += 12
        # attr
        offset += 2
        tris.append((v1, v2, v3))
    return Mesh(triangles=tris)


def _load_ascii_stl(data: bytes) -> Mesh:
    # Very small, tolerant ASCII STL parser: only reads vertex lines.
    text = data.decode("utf-8", errors="ignore").splitlines()
    verts: List[Vec3] = []
    tris: List[Tri] = []
    for ln in text:
        s = ln.strip().lower()
        if s.startswith("vertex "):
            parts = s.split()
            if len(parts) >= 4:
                try:
                    x = float(parts[1])
                    y = float(parts[2])
                    z = float(parts[3])
                    verts.append((x, y, z))
                except ValueError:
                    continue
            if len(verts) == 3:
                tris.append((verts[0], verts[1], verts[2]))
                verts = []
    return Mesh(triangles=tris)


def _normalize(v: Vec3) -> Vec3:
    l = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if l == 0.0:
        return (0.0, 0.0, 0.0)
    return (v[0] / l, v[1] / l, v[2] / l)


def save_binary_stl(mesh: Mesh, path: Path, header: bytes | None = None) -> None:
    if header is None:
        hdr_txt = f"stl_xy_scale {path.name}".encode("ascii", errors="ignore")[:80]
        header = hdr_txt.ljust(80, b" ")
    if len(header) != 80:
        header = header[:80].ljust(80, b" ")

    out = bytearray()
    out += header
    out += struct.pack("<I", len(mesh.triangles))
    for (a, b, c) in mesh.triangles:
        n = _normalize(_cross(_vsub(b, a), _vsub(c, a)))
        out += struct.pack("<fff", *n)
        out += struct.pack("<fff", *a)
        out += struct.pack("<fff", *b)
        out += struct.pack("<fff", *c)
        out += struct.pack("<H", 0)
    path.write_bytes(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="Input STL path")
    ap.add_argument("--out", dest="out", required=True, help="Output STL path")
    ap.add_argument("--sx", type=float, required=True, help="Scale factor in X")
    ap.add_argument("--sy", type=float, required=True, help="Scale factor in Y")
    args = ap.parse_args()

    inp = Path(args.inp)
    out = Path(args.out)
    mesh = load_stl(inp)
    scaled = mesh.scale_xy_about_center(args.sx, args.sy)
    save_binary_stl(scaled, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

