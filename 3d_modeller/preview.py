"""STL önizleme görüntüsü oluştur (4 panel: tahta üst, tahta yan, pul, kale)"""
import struct
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def read_binary_stl(filename):
    triangles = []
    with open(filename, 'rb') as f:
        f.read(80)
        n = struct.unpack('<I', f.read(4))[0]
        for _ in range(n):
            f.read(12)
            v1 = struct.unpack('<fff', f.read(12))
            v2 = struct.unpack('<fff', f.read(12))
            v3 = struct.unpack('<fff', f.read(12))
            f.read(2)
            triangles.append([v1, v2, v3])
    return np.array(triangles)


def render_stl(filename, ax, color='#5099d6', edge='#1c4f7a',
               elev=30, azim=-45, title='', linewidth=0.3):
    tris = read_binary_stl(filename)
    poly = Poly3DCollection(tris, facecolors=color, edgecolors=edge,
                            linewidths=linewidth, alpha=0.95)
    ax.add_collection3d(poly)

    pts = tris.reshape(-1, 3)
    mins = pts.min(axis=0)
    maxs = pts.max(axis=0)
    centers = (mins + maxs) / 2
    span = (maxs - mins).max() / 2 * 1.05

    ax.set_xlim(centers[0] - span, centers[0] + span)
    ax.set_ylim(centers[1] - span, centers[1] + span)
    ax.set_zlim(centers[2] - span, centers[2] + span)
    ax.set_box_aspect([1, 1, 1])
    ax.view_init(elev=elev, azim=azim)
    ax.set_title(title, fontsize=11, fontweight='bold', pad=8)

    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.grid(False)
    ax.xaxis.pane.set_visible(False)
    ax.yaxis.pane.set_visible(False)
    ax.zaxis.pane.set_visible(False)


def main():
    fig = plt.figure(figsize=(14, 9), facecolor='#f5f5f5')

    # Tahta - üstten (kuyular net görünür)
    ax1 = fig.add_subplot(221, projection='3d')
    render_stl(os.path.join(OUT_DIR, 'tahta.stl'), ax1,
               color='#dadada', edge='#333333', elev=85, azim=-90,
               title='TAHTA — ÜSTTEN BAKIŞ\n(37 kuyu hücresi)',
               linewidth=0.4)

    # Tahta - yandan (kuyu derinliği görünür)
    ax2 = fig.add_subplot(222, projection='3d')
    render_stl(os.path.join(OUT_DIR, 'tahta.stl'), ax2,
               color='#dadada', edge='#333333', elev=20, azim=-50,
               title='TAHTA — YANDAN BAKIŞ\n(2.5 mm derinlik)',
               linewidth=0.3)

    # Pul
    ax3 = fig.add_subplot(223, projection='3d')
    render_stl(os.path.join(OUT_DIR, 'pul.stl'), ax3,
               color='#5099d6', edge='#1c4f7a', elev=25, azim=-30,
               title='PUL\n(kuyuya tam oturur)')

    # Kale
    ax4 = fig.add_subplot(224, projection='3d')
    render_stl(os.path.join(OUT_DIR, 'kale.stl'), ax4,
               color='#d65050', edge='#7a1c1c', elev=20, azim=-30,
               title='KALE\n(kale konumu hücresine oturur)')

    plt.tight_layout()
    out = os.path.join(OUT_DIR, 'onizleme.png')
    plt.savefig(out, dpi=120, bbox_inches='tight', facecolor='#f5f5f5')
    print(f"Önizleme oluşturuldu: {out}")


if __name__ == "__main__":
    main()
