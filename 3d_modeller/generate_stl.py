"""
Goldbach Seferi — 3D Model Üretici (v2)
========================================
Bu script Bambu Studio (veya herhangi bir dilimleyici) ile kullanılabilecek
STL dosyaları üretir.

YENİLİKLER (v2):
  - Hücreler artık GERÇEK KUYU (cavity) şeklinde — pul içine düşer, kaymaz
  - Pointy-top hex geometrisi düzeltildi (köşelerde çakışma yok)
  - İç bölme duvarları sadece bir kez üretiliyor (deduplikasyon)
  - Pul ve kale tabanı kuyu boyutuna birebir uyumlu

Üretilen dosyalar:
  - tahta.stl  : Oyun tahtası (3 halka, 37 hücre — kuyulu yapı)
  - pul.stl    : Oyuncu pulu (kuyuya tam oturur)
  - kale.stl   : Kale figürü (pul boyutunda taban + kuleler)

Çalıştırmak için:
    python3 generate_stl.py
"""

import math
import os
import struct

# ─── Geometri parametreleri (mm cinsinden) ───
HEX_R = 13.0            # Bir hücrenin dış yarıçapı (köşeden merkeze)
WALL_THICKNESS = 1.4    # Hücreler arası bölme duvarı kalınlığı
FLOOR_THICKNESS = 1.8   # Tahta tabanı kalınlığı
WELL_DEPTH = 2.5        # Hücrelerin derinliği (pul buraya oturur)
RINGS = 3               # Halka sayısı (3 = 37 hücre)
BOARD_OUTER_R = 95.0    # Dış taban yarıçapı (flat-top, 190mm genişlik / 165mm yükseklik)

# Yazı parametreleri
TEXT_STR = "GOLDBACH SEFERI"
TEXT_PIXEL = 0.85       # Bitmap font piksel boyutu (mm)
TEXT_HEIGHT = 0.8       # Yazının taban üstüne çıkıntı yüksekliği (mm)
TEXT_Y_CENTER = -77.5   # Yazının y konumu (taban altında, hücrelerin altında)

# Pul (token) parametreleri
# Hücre içine sığacak şekilde hesaplanıyor:
#   Hücre iç yarıçapı (flat-to-flat / 2) = HEX_R * sqrt(3)/2 - WALL_THICKNESS/2
#   Pul flat-to-flat = TILE_R * sqrt(3)
#   Boşluk: 0.4mm (rahat oturma için)
TILE_R = HEX_R - WALL_THICKNESS / math.sqrt(3) - 0.4
TILE_THICKNESS = 3.0    # 2.5mm kuyu + 0.5mm üst (kavraması kolay)

# Kale parametreleri
CASTLE_BASE_R = TILE_R  # Pul ile aynı taban
CASTLE_BASE_H = TILE_THICKNESS
CASTLE_PILLAR_SIZE = 2.6
CASTLE_PILLAR_H = 7.5
CASTLE_TOWER_R = 4.5
CASTLE_TOWER_H = 13.0
CASTLE_ROOF_H = 1.2

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Pointy-top hex grid komşu yön vektörleri (her kenar için)
# Köşeler: 30°, 90°, 150°, 210°, 270°, 330° (pointy-top, vertex at top)
# Kenar i: corner i ile corner i+1 arasındaki kenar
NEIGHBOR_OFFSETS_PER_EDGE = [
    (+1, -1),  # kenar 0: NE
    ( 0, -1),  # kenar 1: NW
    (-1,  0),  # kenar 2: W
    (-1, +1),  # kenar 3: SW
    ( 0, +1),  # kenar 4: SE
    (+1,  0),  # kenar 5: E
]


# ═══════════════════════════════════════════════════════
#  STL YAZIMI (Binary format — küçük dosya boyutu)
# ═══════════════════════════════════════════════════════

def write_binary_stl(filename, triangles, name="model"):
    """triangles: list of (v1, v2, v3) tuples, each v = (x, y, z)"""
    with open(filename, 'wb') as f:
        header = name.ljust(80)[:80].encode('ascii', errors='replace')
        f.write(header)
        f.write(struct.pack('<I', len(triangles)))
        for v1, v2, v3 in triangles:
            ux, uy, uz = (v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2])
            vx, vy, vz = (v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2])
            nx = uy * vz - uz * vy
            ny = uz * vx - ux * vz
            nz = ux * vy - uy * vx
            length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
            nx, ny, nz = nx / length, ny / length, nz / length
            f.write(struct.pack('<fff', nx, ny, nz))
            f.write(struct.pack('<fff', *v1))
            f.write(struct.pack('<fff', *v2))
            f.write(struct.pack('<fff', *v3))
            f.write(struct.pack('<H', 0))


# ═══════════════════════════════════════════════════════
#  GEOMETRİ YARDIMCILARI (POINTY-TOP HEX)
# ═══════════════════════════════════════════════════════

def hex_corners_pointy(cx, cy, radius, z):
    """Pointy-top altıgenin 6 köşesi (vertex at top, flat sides on left/right).
    Köşeler: 30°, 90°, 150°, 210°, 270°, 330°"""
    return [
        (cx + radius * math.cos(math.radians(30 + 60 * i)),
         cy + radius * math.sin(math.radians(30 + 60 * i)),
         z)
        for i in range(6)
    ]


def hex_corners_flat(cx, cy, radius, z):
    """Flat-top altıgenin 6 köşesi (flat at top/bottom, vertex on left/right).
    Köşeler: 0°, 60°, 120°, 180°, 240°, 300°"""
    return [
        (cx + radius * math.cos(math.radians(60 * i)),
         cy + radius * math.sin(math.radians(60 * i)),
         z)
        for i in range(6)
    ]


def _hex_prism_from_corners(corners_fn, cx, cy, z_base, height, radius):
    bot = corners_fn(cx, cy, radius, z_base)
    top = corners_fn(cx, cy, radius, z_base + height)
    bot_c = (cx, cy, z_base)
    top_c = (cx, cy, z_base + height)
    tris = []
    for i in range(6):
        tris.append((bot_c, bot[(i + 1) % 6], bot[i]))
    for i in range(6):
        tris.append((top_c, top[i], top[(i + 1) % 6]))
    for i in range(6):
        n = (i + 1) % 6
        tris.append((bot[i], bot[n], top[n]))
        tris.append((bot[i], top[n], top[i]))
    return tris


def hex_prism(cx, cy, z_base, height, radius):
    """Pointy-top altıgen prizma."""
    return _hex_prism_from_corners(hex_corners_pointy, cx, cy, z_base, height, radius)


def hex_prism_flat(cx, cy, z_base, height, radius):
    """Flat-top altıgen prizma (dış taban için)."""
    return _hex_prism_from_corners(hex_corners_flat, cx, cy, z_base, height, radius)


def cuboid(cx, cy, z_base, w, d, h):
    """(cx, cy) merkezinde, (w × d × h) boyutlarında dikdörtgen prizma."""
    x0, x1 = cx - w / 2, cx + w / 2
    y0, y1 = cy - d / 2, cy + d / 2
    z0, z1 = z_base, z_base + h
    p = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ]
    return [
        (p[0], p[2], p[1]), (p[0], p[3], p[2]),       # alt
        (p[4], p[5], p[6]), (p[4], p[6], p[7]),       # üst
        (p[0], p[1], p[5]), (p[0], p[5], p[4]),       # -Y
        (p[2], p[3], p[7]), (p[2], p[7], p[6]),       # +Y
        (p[3], p[0], p[4]), (p[3], p[4], p[7]),       # -X
        (p[1], p[2], p[6]), (p[1], p[6], p[5]),       # +X
    ]


def oriented_wall(x1, y1, x2, y2, z_base, thickness, height):
    """(x1,y1) -> (x2,y2) çizgisi boyunca dikdörtgen duvar."""
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    length = math.hypot(x2 - x1, y2 - y1)
    angle = math.atan2(y2 - y1, x2 - x1)
    half_l, half_t = length / 2, thickness / 2
    local = [
        (-half_l, -half_t, z_base), (half_l, -half_t, z_base),
        (half_l, half_t, z_base), (-half_l, half_t, z_base),
        (-half_l, -half_t, z_base + height), (half_l, -half_t, z_base + height),
        (half_l, half_t, z_base + height), (-half_l, half_t, z_base + height),
    ]
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    p = [
        (cx + lx * cos_a - ly * sin_a, cy + lx * sin_a + ly * cos_a, lz)
        for lx, ly, lz in local
    ]
    return [
        (p[0], p[2], p[1]), (p[0], p[3], p[2]),
        (p[4], p[5], p[6]), (p[4], p[6], p[7]),
        (p[0], p[1], p[5]), (p[0], p[5], p[4]),
        (p[2], p[3], p[7]), (p[2], p[7], p[6]),
        (p[3], p[0], p[4]), (p[3], p[4], p[7]),
        (p[1], p[2], p[6]), (p[1], p[6], p[5]),
    ]


# ═══════════════════════════════════════════════════════
#  BITMAP FONT (5x7 piksel) — yazı kabartması için
# ═══════════════════════════════════════════════════════

FONT = {
    'G': ['.XXX.', 'X...X', 'X....', 'X.XXX', 'X...X', 'X...X', '.XXX.'],
    'O': ['.XXX.', 'X...X', 'X...X', 'X...X', 'X...X', 'X...X', '.XXX.'],
    'L': ['X....', 'X....', 'X....', 'X....', 'X....', 'X....', 'XXXXX'],
    'D': ['XXXX.', 'X...X', 'X...X', 'X...X', 'X...X', 'X...X', 'XXXX.'],
    'B': ['XXXX.', 'X...X', 'X...X', 'XXXX.', 'X...X', 'X...X', 'XXXX.'],
    'A': ['.XXX.', 'X...X', 'X...X', 'XXXXX', 'X...X', 'X...X', 'X...X'],
    'C': ['.XXXX', 'X....', 'X....', 'X....', 'X....', 'X....', '.XXXX'],
    'H': ['X...X', 'X...X', 'X...X', 'XXXXX', 'X...X', 'X...X', 'X...X'],
    'S': ['.XXXX', 'X....', 'X....', '.XXX.', '....X', '....X', 'XXXX.'],
    'E': ['XXXXX', 'X....', 'X....', 'XXXX.', 'X....', 'X....', 'XXXXX'],
    'F': ['XXXXX', 'X....', 'X....', 'XXXX.', 'X....', 'X....', 'X....'],
    'I': ['XXXXX', '..X..', '..X..', '..X..', '..X..', '..X..', 'XXXXX'],
    'R': ['XXXX.', 'X...X', 'X...X', 'XXXX.', 'X.X..', 'X..X.', 'X...X'],
    ' ': ['.....', '.....', '.....', '.....', '.....', '.....', '.....'],
}


def render_text_pixels(text, x_center, y_center, z_base, height,
                        pixel_size, char_spacing_pixels=1):
    """Verilen yazıyı kabartma (raised pixel) olarak üret."""
    text = text.upper()
    char_w = 5 * pixel_size + char_spacing_pixels * pixel_size
    total_width = len(text) * char_w - char_spacing_pixels * pixel_size

    tris = []
    for i, ch in enumerate(text):
        if ch not in FONT:
            continue
        char_x_left = x_center - total_width / 2 + i * char_w
        char_y_top = y_center + 7 * pixel_size / 2

        for row, line in enumerate(FONT[ch]):
            for col, c in enumerate(line):
                if c == 'X':
                    px = char_x_left + col * pixel_size + pixel_size / 2
                    py = char_y_top - row * pixel_size - pixel_size / 2
                    tris.extend(cuboid(px, py, z_base,
                                       pixel_size, pixel_size, height))
    return tris


# ═══════════════════════════════════════════════════════
#  HEX GRID MATEMATİĞİ (POINTY-TOP)
# ═══════════════════════════════════════════════════════

def get_cell_position(q, r, hex_r=HEX_R):
    """Pointy-top hex grid: axial koordinattan piksel koordinata."""
    x = hex_r * math.sqrt(3) * (q + r / 2)
    y = hex_r * 1.5 * r
    return (x, y)


def get_all_cells(rings):
    """Belirtilen halka sayısındaki tüm hücrelerin (q, r) listesi."""
    cells = []
    for q in range(-rings, rings + 1):
        for r in range(-rings, rings + 1):
            if abs(-q - r) <= rings:
                cells.append((q, r))
    return cells


# ═══════════════════════════════════════════════════════
#  MODEL ÜRETİCİLERİ
# ═══════════════════════════════════════════════════════

def generate_board():
    """Oyun tahtası: kuyulu altıgen ızgara + yazılı taban."""
    cells = get_all_cells(RINGS)
    cell_set = set(cells)

    tris = []

    # 1. Alt taban — FLAT-TOP altıgen (hücreler pointy-top, dış flat-top)
    # Bu sayede üst ve alt kısımlar düz olur ve yazıya uygun alan oluşur
    tris.extend(hex_prism_flat(0, 0, 0, FLOOR_THICKNESS, BOARD_OUTER_R))

    # 2. Dış çerçeve (perimetreyi WELL_DEPTH boyu yükselten katı duvar)
    # Bu sayede dıştan bakınca tahta düz görünür, içeride kuyular vardır
    # En kolay yol: dış hexin içine doğru, hücre dış sınırına kadar dolu kısım
    # Bunu iki adımda yapacağız:
    #   a) Tüm tahtayı (max_dist) tam yüksekliğe çıkar (FLOOR + WELL)
    #   b) Sonra her hücrenin tepesine "delik" açmak yerine,
    #      sadece çerçeveyi (cells'in dışındaki alanı) WELL_DEPTH yüksekliğe çıkar
    #
    # Çünkü STL'de boolean subtraction yok, bunu farklı yapıyoruz:
    #   - Her hücrenin etrafına 6 duvar koyalım (paylaşılan olanlar tek sefer)
    #   - Dış kenarlarda da duvar var (hücre yoksa o kenar dış kenardır)

    # 3. Hücre duvarları (iç bölmeler ve dış çerçeve)
    seen_edges = set()

    for (q, r) in cells:
        cx, cy = get_cell_position(q, r)
        corners = hex_corners_pointy(cx, cy, HEX_R, FLOOR_THICKNESS)

        for edge_i in range(6):
            c1 = corners[edge_i]
            c2 = corners[(edge_i + 1) % 6]

            # Bu kenarın komşusu (hücre var mı?)
            dq, dr = NEIGHBOR_OFFSETS_PER_EDGE[edge_i]
            neighbor = (q + dq, r + dr)

            if neighbor in cell_set:
                # İç kenar — sadece bir kez üret (deduplikasyon)
                edge_key = tuple(sorted([
                    (round(c1[0], 1), round(c1[1], 1)),
                    (round(c2[0], 1), round(c2[1], 1))
                ]))
                if edge_key in seen_edges:
                    continue
                seen_edges.add(edge_key)

            # Duvar üret
            tris.extend(oriented_wall(c1[0], c1[1], c2[0], c2[1],
                                       FLOOR_THICKNESS, WALL_THICKNESS, WELL_DEPTH))

    # 4. Dış çerçeve (frame): perimeter dışındaki bölgeyi WELL_DEPTH'e çıkar
    # Bu, tahtaya çerçeveli/sınırlı bir görünüm verir
    # Yapım: dış hexin içinde, hücrelerin perimeterinin biraz dışında kalan ince bir bant
    # Basitlik için bunu atlıyoruz, dış kenarda hücre duvarı zaten var

    # 5. Kale konumlarını işaretle (küçük + işareti taban yüzeyinde)
    midR = RINGS // 2
    castle_positions = [(-RINGS, midR), (RINGS, -midR)]
    for q, r in castle_positions:
        if (q, r) in cell_set:
            cx, cy = get_cell_position(q, r)
            # Hafif kabarık + işareti, kuyunun içinde tabanda
            tris.extend(cuboid(cx, cy, FLOOR_THICKNESS, 4.5, 0.7, 0.4))
            tris.extend(cuboid(cx, cy, FLOOR_THICKNESS, 0.7, 4.5, 0.4))

    # 6. "GOLDBACH SEFERI" yazısı — tabanın alt kısmında (hücrelerin altında)
    tris.extend(render_text_pixels(
        TEXT_STR,
        x_center=0,
        y_center=TEXT_Y_CENTER,
        z_base=FLOOR_THICKNESS,
        height=TEXT_HEIGHT,
        pixel_size=TEXT_PIXEL,
    ))

    return tris


def generate_tile():
    """Oyuncu pulu: kuyuya tam oturan altıgen disk."""
    tris = []
    # Ana gövde (pointy-top)
    tris.extend(hex_prism(0, 0, 0, TILE_THICKNESS, TILE_R))
    # Üstte küçük çıkıntı (parmak tutamacı)
    tris.extend(hex_prism(0, 0, TILE_THICKNESS, 0.6, TILE_R * 0.45))
    return tris


def generate_castle():
    """Kale figürü: pul tabanı + 4 köşe sütunu + merkez kule."""
    tris = []

    # Hex taban (pul ile aynı boyutta — kuyuya oturur)
    tris.extend(hex_prism(0, 0, 0, CASTLE_BASE_H, CASTLE_BASE_R))

    # 4 köşe sütunu (kare desen)
    pillar_offset = CASTLE_BASE_R * 0.55
    for px, py in [(-pillar_offset, -pillar_offset),
                   (pillar_offset, -pillar_offset),
                   (pillar_offset, pillar_offset),
                   (-pillar_offset, pillar_offset)]:
        tris.extend(cuboid(px, py, CASTLE_BASE_H,
                           CASTLE_PILLAR_SIZE, CASTLE_PILLAR_SIZE,
                           CASTLE_PILLAR_H))
        # Sütun tepesinde mazgallar (battlement)
        tris.extend(cuboid(px - 1.0, py, CASTLE_BASE_H + CASTLE_PILLAR_H,
                           0.9, CASTLE_PILLAR_SIZE, 1.3))
        tris.extend(cuboid(px + 1.0, py, CASTLE_BASE_H + CASTLE_PILLAR_H,
                           0.9, CASTLE_PILLAR_SIZE, 1.3))

    # Merkez kule (yüksek hex prizma)
    tris.extend(hex_prism(0, 0, CASTLE_BASE_H,
                          CASTLE_TOWER_H, CASTLE_TOWER_R))
    # Çatı (küçük çıkıntılı şapka)
    tris.extend(hex_prism(0, 0, CASTLE_BASE_H + CASTLE_TOWER_H,
                          CASTLE_ROOF_H, CASTLE_TOWER_R + 0.5))
    # Bayrak direği
    tris.extend(cuboid(0, 0, CASTLE_BASE_H + CASTLE_TOWER_H + CASTLE_ROOF_H,
                       0.7, 0.7, 3.5))
    # Bayrak (küçük dikdörtgen)
    tris.extend(cuboid(1.4, 0, CASTLE_BASE_H + CASTLE_TOWER_H + CASTLE_ROOF_H + 2.2,
                       1.8, 0.4, 1.3))

    return tris


# ═══════════════════════════════════════════════════════
#  ANA İŞLEM
# ═══════════════════════════════════════════════════════

def compute_bbox(triangles):
    xs, ys, zs = [], [], []
    for v1, v2, v3 in triangles:
        for v in (v1, v2, v3):
            xs.append(v[0])
            ys.append(v[1])
            zs.append(v[2])
    return (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))


def main():
    print("Goldbach Seferi — STL üretici (v2 — kuyulu tahta)")
    print("=" * 50)

    print("\n[1/3] Tahta üretiliyor (3 halka, 37 hücre, gerçek kuyular)...")
    board_tris = generate_board()
    out = os.path.join(OUT_DIR, 'tahta.stl')
    write_binary_stl(out, board_tris, 'GoldbachBoard')
    bbox = compute_bbox(board_tris)
    print(f"  ✓ {out}")
    print(f"    Üçgen: {len(board_tris)}")
    print(f"    Boyut: {bbox[0]:.1f} × {bbox[1]:.1f} × {bbox[2]:.1f} mm")
    print(f"    Kuyu derinliği: {WELL_DEPTH} mm")

    print("\n[2/3] Pul üretiliyor...")
    tile_tris = generate_tile()
    out = os.path.join(OUT_DIR, 'pul.stl')
    write_binary_stl(out, tile_tris, 'GoldbachTile')
    bbox = compute_bbox(tile_tris)
    print(f"  ✓ {out}")
    print(f"    Üçgen: {len(tile_tris)}")
    print(f"    Boyut: {bbox[0]:.1f} × {bbox[1]:.1f} × {bbox[2]:.1f} mm")
    print(f"    Pul yarıçapı: {TILE_R:.2f} mm | Kalınlık: {TILE_THICKNESS} mm")

    print("\n[3/3] Kale üretiliyor...")
    castle_tris = generate_castle()
    out = os.path.join(OUT_DIR, 'kale.stl')
    write_binary_stl(out, castle_tris, 'GoldbachCastle')
    bbox = compute_bbox(castle_tris)
    print(f"  ✓ {out}")
    print(f"    Üçgen: {len(castle_tris)}")
    print(f"    Boyut: {bbox[0]:.1f} × {bbox[1]:.1f} × {bbox[2]:.1f} mm")

    print("\n" + "=" * 50)
    print("Tüm dosyalar üretildi!")
    print(f"\nKonum: {OUT_DIR}")
    print("\nÖnerilen baskı ayarları:")
    print("  • Filament: PLA")
    print("  • Katman yüksekliği: 0.20 mm")
    print("  • Doluluk: %15-20")
    print("  • Destek: Gerek yok")


if __name__ == "__main__":
    main()
