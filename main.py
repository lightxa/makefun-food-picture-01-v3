"""Molten chocolate fondant with vanilla ice cream. Stdlib only, deterministic.

Writes one 1024x1024 PNG to $MAKEFUN_OUTPUT_DIR/entry.png (default /output).
A close three-quarter view: a dark chocolate fondant, its glossy molten centre
spilling across a matte black plate, a melting scoop of vanilla ice cream,
fresh raspberries, a mint leaf, cocoa dust and a chocolate drizzle. Warm
dramatic side light from the upper left against a deep dark background.
"""
import math
import os
import random
import struct
import zlib

W = 1024
H = 1024

rnd = random.Random(20261115)


def clamp(v, lo=0, hi=255):
    return lo if v < lo else hi if v > hi else v


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return (int(lerp(c1[0], c2[0], t)), int(lerp(c1[1], c2[1], t)),
            int(lerp(c1[2], c2[2], t)))


# ---------------------------------------------------------------- pixel buffer
pix = bytearray(W * H * 3)


def set_px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        pix[i] = c[0]
        pix[i + 1] = c[1]
        pix[i + 2] = c[2]


def blend_px(x, y, c, a):
    if 0 <= x < W and 0 <= y < H and a > 0:
        i = (y * W + x) * 3
        if a >= 1:
            pix[i] = c[0]
            pix[i + 1] = c[1]
            pix[i + 2] = c[2]
        else:
            pix[i] = int(pix[i] + (c[0] - pix[i]) * a)
            pix[i + 1] = int(pix[i + 1] + (c[1] - pix[i + 1]) * a)
            pix[i + 2] = int(pix[i + 2] + (c[2] - pix[i + 2]) * a)


def fill_circle(cx, cy, r, c, a=1.0):
    r2 = r * r
    y0 = max(0, int(cy - r))
    y1 = min(H - 1, int(cy + r) + 1)
    for y in range(y0, y1):
        dy = y - cy
        dx = int(math.sqrt(max(0, r2 - dy * dy)))
        x0 = max(0, int(cx - dx))
        x1 = min(W - 1, int(cx + dx))
        for x in range(x0, x1 + 1):
            if a >= 1:
                set_px(x, y, c)
            else:
                blend_px(x, y, c, a)


def fill_ellipse(cx, cy, rx, ry, c, a=1.0):
    y0 = max(0, int(cy - ry))
    y1 = min(H - 1, int(cy + ry) + 1)
    for y in range(y0, y1):
        dy = (y - cy) / ry
        dx = int(rx * math.sqrt(max(0.0, 1.0 - dy * dy)))
        x0 = max(0, int(cx - dx))
        x1 = min(W - 1, int(cx + dx))
        for x in range(x0, x1 + 1):
            if a >= 1:
                set_px(x, y, c)
            else:
                blend_px(x, y, c, a)


def thick_line(x0, y0, x1, y1, half, c, a=1.0):
    length = math.hypot(x1 - x0, y1 - y0)
    steps = max(2, int(length / 3))
    for s in range(steps + 1):
        t = s / steps
        fill_circle(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, half, c, a)


def speckle(x, y):
    """Deterministic fine grain in [0, 1)."""
    h = math.sin(x * 12.9898 + y * 78.233) * 43758.5453
    return h - math.floor(h)


# ---------------------------------------------------------------- background
# Deep dark backdrop, warm amber glow pooling in from the upper left.
for y in range(H):
    t = y / (H - 1)
    base = mix((44, 30, 24), (10, 8, 9), t)
    row = y * W * 3
    for x in range(W):
        gl = max(0.0, 1.0 - math.hypot((x - 190) / 760.0, (y - 150) / 760.0))
        warm = 1.0 + 0.42 * gl
        sp = 0.94 + 0.06 * speckle(x, y)
        i = row + x * 3
        pix[i] = clamp(int(base[0] * sp * warm))
        pix[i + 1] = clamp(int(base[1] * sp * warm))
        pix[i + 2] = clamp(int(base[2] * sp * warm))
# a soft warm halo behind the cake, upper left of centre
for y in range(120, 560):
    for x in range(80, 700):
        d = math.hypot((x - 380) / 330.0, (y - 330) / 260.0)
        if d < 1:
            blend_px(x, y, (255, 176, 96), 0.10 * (1 - d))

# ---------------------------------------------------------------- table + plate
# Dark walnut table in the lower half, barely visible in the gloom.
for y in range(560, H):
    for x in range(W):
        t = (y - 560) / 464.0
        c = mix((38, 26, 20), (16, 12, 11), t)
        sp = 0.93 + 0.07 * speckle(x, y)
        blend_px(x, y, (clamp(int(c[0] * sp)), clamp(int(c[1] * sp)),
                        clamp(int(c[2] * sp))), 0.85)
# faint table grain streaks
for k in range(7):
    gy = 600 + k * 58 + rnd.random() * 24
    for x in range(0, W, 5):
        blend_px(x, int(gy + 2 * math.sin(x * 0.01 + k)), (6, 5, 5), 0.3)

# Matte black ceramic plate: a wide ellipse seen from a three-quarter angle,
# with a thin warm rim catching the light on its upper left edge.
fill_ellipse(512, 668, 428, 208, (30, 27, 28))
fill_ellipse(512, 664, 414, 196, (38, 34, 35))
fill_ellipse(512, 660, 396, 182, (44, 39, 40))
# plate sheen: a soft warm wash upper left, fading to the right
for y in range(480, 860):
    for x in range(96, 930):
        d = math.hypot((x - 512) / 414.0, (y - 664) / 196.0)
        if d < 1:
            gl = max(0.0, 1.0 - math.hypot((x - 300) / 420.0,
                                           (y - 540) / 300.0))
            if gl > 0:
                blend_px(x, y, (255, 196, 130), 0.07 * gl)
# thin rim highlight along the plate's upper left arc
for a in range(180, 330):
    th = math.radians(a)
    px = 512 + 414 * math.cos(th)
    py = 664 + 196 * math.sin(th)
    fill_circle(px, py, 2.2, (150, 118, 96), 0.5)
# soft contact shadow under where the cake and scoop will sit
for y in range(560, 820):
    for x in range(180, 880):
        d = math.hypot((x - 520) / 380.0, (y - 690) / 110.0)
        if d < 1:
            blend_px(x, y, (0, 0, 0), 0.34 * (1 - d))

# ---------------------------------------------------------------- fondant cake
# A tall dark chocolate fondant, centre-left, domed top, slightly tapered body.
# Silhouette: domed top (ellipse cap) over a body that bulges then tucks in.
CAKE_CX, CAKE_TOP, CAKE_BASE = 430, 356, 626


def cake_half_width(y):
    """Half-width of the cake silhouette at height y."""
    if y < 428:  # domed top
        t = (y - CAKE_TOP) / (428 - CAKE_TOP)
        return 196 * math.sqrt(max(0.0, 1.0 - (1 - t) ** 2)) + 6
    if y < 560:  # body, gentle bulge
        t = (y - 428) / 132.0
        return 196 - 14 * t + 10 * math.sin(t * math.pi)
    # base tuck
    t = (y - 560) / (CAKE_BASE - 560)
    return 192 - 26 * t


for y in range(CAKE_TOP, CAKE_BASE + 1):
    hw = cake_half_width(y)
    for x in range(int(CAKE_CX - hw), int(CAKE_CX + hw) + 1):
        u = (x - CAKE_CX) / hw
        v = (y - CAKE_TOP) / (CAKE_BASE - CAKE_TOP)
        # base: rich dark chocolate, lighter on the domed top, darker at base
        c = mix((96, 52, 30), (46, 24, 15), min(1.0, v * 1.15))
        # baked crumb texture: fine mottling
        mot = 0.5 + 0.5 * math.sin(u * 26.0 + 4.0 * math.sin(v * 22.0))
        mot *= 0.5 + 0.5 * math.sin(v * 34.0 + u * 9.0 + 1.3)
        if mot > 0.62:
            c = mix(c, (128, 74, 42), (mot - 0.62) * 0.9)
        elif mot < 0.30:
            c = mix(c, (30, 15, 9), (0.30 - mot) * 0.9)
        # warm side light from the upper left
        gl = max(0.0, 1.0 - math.hypot((u + 0.42) / 0.75,
                                       (v - 0.22) / 0.62))
        c = (clamp(int(c[0] + 52 * gl)), clamp(int(c[1] + 30 * gl)),
             clamp(int(c[2] + 14 * gl)))
        # cool shadow on the far right edge
        if u > 0.72:
            c = mix(c, (18, 10, 8), (u - 0.72) * 1.6)
        # thin bright rim on the lit left edge
        if -0.99 < u < -0.90 and 0.15 < v < 0.85:
            c = mix(c, (255, 196, 130), 0.45)
        set_px(x, y, c)

# crackled top: short darker fissures across the dome, like a baked crust
for _ in range(46):
    cx = CAKE_CX - 150 + rnd.random() * 300
    cy = CAKE_TOP + 8 + rnd.random() * 62
    ln = 8 + rnd.random() * 22
    ang = rnd.random() * math.pi
    thick_line(cx, cy, cx + ln * math.cos(ang), cy + ln * math.sin(ang) * 0.5,
               1.6, (34, 18, 11), 0.75)

# ---------------------------------------------------------------- molten centre
# A spoon-cut opening on the cake's front-right face: molten chocolate pours
# out of the cut and runs down the cake onto the plate in a glossy river.
def molten_blob(cx, cy, rx, ry, base, hi, a=1.0):
    """Glossy molten chocolate patch with a bright specular streak."""
    y0 = max(0, int(cy - ry))
    y1 = min(H - 1, int(cy + ry) + 1)
    for y in range(y0, y1):
        dy = (y - cy) / ry
        dx = int(rx * math.sqrt(max(0.0, 1.0 - dy * dy)))
        for x in range(max(0, int(cx - dx)), min(W - 1, int(cx + dx) + 1)):
            u = (x - cx) / rx
            v = (y - cy) / ry
            r = math.hypot(u, v)
            if r > 1:
                continue
            c = mix(hi, base, min(1.0, r * 1.2))
            # ripples in the flowing chocolate
            rip = 0.5 + 0.5 * math.sin(v * 16.0 + 3.0 * math.sin(u * 8.0))
            if rip > 0.82:
                c = mix(c, (214, 128, 62), (rip - 0.82) * 0.4)
            # specular streak along the flow
            gl = max(0.0, 1.0 - math.hypot((u + 0.18) / 0.30,
                                           (v - 0.05) / 0.55))
            c = (clamp(int(c[0] + 120 * gl)), clamp(int(c[1] + 70 * gl)),
                 clamp(int(c[2] + 30 * gl)))
            if a >= 1:
                set_px(x, y, c)
            else:
                blend_px(x, y, c, a)


# the cut face itself, glowing warm molten chocolate
molten_blob(512, 505, 74, 62, (88, 44, 20), (196, 108, 48))
# a drip escaping the cut and running down the cake face
molten_blob(530, 552, 30, 52, (80, 40, 18), (180, 98, 44))
molten_blob(540, 606, 16, 18, (76, 38, 17), (168, 92, 40))
# the river: molten chocolate pooling and flowing across the plate
molten_blob(560, 668, 150, 52, (84, 42, 19), (190, 104, 46), 0.98)
molten_blob(648, 706, 96, 40, (78, 38, 18), (182, 98, 44), 0.98)
molten_blob(716, 736, 52, 26, (74, 36, 17), (172, 92, 42), 0.98)
# bright gloss beads riding on the river
for bx, by, br in [(520, 648, 9), (596, 676, 12), (668, 700, 8),
                   (724, 730, 6), (470, 660, 7)]:
    fill_ellipse(bx, by, br, br * 0.45, (255, 214, 150), 0.85)
# thin sauce fingers reaching out from the pool
for fx, fy, fl in [(700, 742, 46), (640, 748, 38), (588, 722, 30)]:
    thick_line(fx, fy, fx + fl, fy + 10, 4.5, (86, 44, 20), 0.95)
    thick_line(fx, fy - 2, fx + fl, fy + 8, 1.8, (210, 122, 56), 0.8)

# ---------------------------------------------------------------- ice cream scoop
# A scoop of vanilla bean ice cream at the cake's right, softly melting.
ICE_CX, ICE_CY, ICE_R = 728, 552, 108
for y in range(ICE_CY - ICE_R, ICE_CY + ICE_R + 1):
    for x in range(ICE_CX - ICE_R, ICE_CX + ICE_R + 1):
        dx, dy = x - ICE_CX, y - ICE_CY
        r = math.hypot(dx, dy) / ICE_R
        if r > 1:
            continue
        # cream base, warm-lit upper left, cool shadow lower right
        c = mix((252, 244, 226), (206, 188, 162), min(1.0, r * 1.1))
        lit = max(0.0, 1.0 - math.hypot((dx / ICE_R + 0.35) / 0.8,
                                        (dy / ICE_R + 0.35) / 0.8))
        c = (clamp(int(c[0] + 6 * lit)), clamp(int(c[1] + 4 * lit)),
             clamp(int(c[2] + 2 * lit)))
        if dx > 30 and dy > 20:
            c = mix(c, (168, 148, 122), 0.28 * min(1.0, r))
        # soft scooped swirls
        sw = 0.5 + 0.5 * math.sin(math.atan2(dy, dx) * 3.0 + r * 9.0)
        if sw > 0.74:
            c = mix(c, (232, 220, 196), (sw - 0.74) * 1.2)
        elif sw < 0.26:
            c = mix(c, (214, 196, 170), (0.26 - sw) * 1.0)
        set_px(x, y, c)
# vanilla bean flecks
for _ in range(60):
    ang = rnd.random() * 2 * math.pi
    rr = rnd.random() * 0.92
    fx = ICE_CX + ICE_R * rr * math.cos(ang)
    fy = ICE_CY + ICE_R * rr * math.sin(ang)
    fill_ellipse(fx, fy, 2.2, 1.4, (72, 56, 40), 0.9)
# melting skirt where the scoop meets the plate, and one slow drip
fill_ellipse(728, 652, 118, 26, (244, 234, 214), 0.95)
fill_ellipse(728, 648, 100, 18, (252, 244, 228), 0.9)
fill_ellipse(796, 668, 34, 12, (240, 230, 210), 0.9)
fill_ellipse(662, 664, 26, 10, (240, 230, 210), 0.9)
thick_line(788, 640, 800, 700, 7, (246, 236, 216), 0.95)
fill_circle(800, 704, 9, (244, 234, 214), 0.95)
# bright highlight on the scoop's lit crown
fill_ellipse(688, 492, 42, 20, (255, 252, 244), 0.75)

# ---------------------------------------------------------------- raspberries
def raspberry(cx, cy, r):
    """One raspberry: a cluster of glossy drupelets with a tiny stem."""
    fill_circle(cx, cy, r, (122, 18, 34))
    for _ in range(26):
        ang = rnd.random() * 2 * math.pi
        rr = rnd.random() * 0.78
        dx = int(r * rr * math.cos(ang))
        dy = int(r * rr * math.sin(ang))
        shade = rnd.random()
        if shade < 0.35:
            c = (196, 42, 66)
        elif shade < 0.7:
            c = (168, 26, 50)
        else:
            c = (222, 74, 96)
        fill_circle(cx + dx, cy + dy, max(3, int(r * 0.20)), c, 0.95)
        fill_circle(cx + dx - 2, cy + dy - 2, max(1, int(r * 0.08)),
                    (255, 150, 170), 0.8)
    # highlight on the lit side
    fill_ellipse(cx - r * 0.38, cy - r * 0.42, r * 0.30, r * 0.18,
                 (255, 170, 185), 0.55)
    # tiny green calyx on top
    for k in range(5):
        ang = -math.pi / 2 + (k - 2) * 0.5
        thick_line(cx, cy - r * 0.85,
                   cx + int(9 * math.cos(ang)), cy - r * 0.85
                   + int(9 * math.sin(ang)), 1.8, (52, 96, 48), 0.95)


raspberry(318, 640, 34)
raspberry(372, 690, 28)
raspberry(812, 726, 30)
raspberry(258, 700, 22)

# ---------------------------------------------------------------- mint leaf
def mint_leaf(cx, cy, length, angle_deg):
    """One pointed mint leaf with a pale central vein."""
    ang = math.radians(angle_deg)
    ca, sa = math.cos(ang), math.sin(ang)
    for s in range(-length, length + 1):
        t = s / length
        wdt = 30 * (1 - t * t) ** 0.7 + 2
        for w in range(int(-wdt), int(wdt) + 1):
            x = int(cx + s * ca - w * sa)
            y = int(cy + s * sa + w * ca)
            # serrated edge: skip a few edge pixels for a toothed look
            edge = abs(w) / max(1.0, wdt)
            if edge > 0.82 and int(abs(s) * 3 + abs(w)) % 5 < 2:
                continue
            c = mix((34, 96, 48), (76, 150, 82), max(0.0, 1 - edge))
            if abs(w) < 3:
                c = mix(c, (190, 220, 150), 0.55)
            set_px(x, y, c)
    # side veins
    for k in range(1, 5):
        t = k / 5.0
        bx = cx + (t * length - length * 0.5) * ca
        by = cy + (t * length - length * 0.5) * sa
        thick_line(bx, by, bx + 16 * sa, by - 16 * ca, 1.2,
                   (150, 190, 120), 0.7)


mint_leaf(838, 622, 52, -28)
mint_leaf(872, 668, 40, -58)

# ---------------------------------------------------------------- drizzle + cocoa
# Chocolate sauce drizzle looping across the plate
for seg in [((180, 780), (300, 740), (430, 780), (560, 736)),
            ((620, 800), (720, 762), (820, 796), (900, 758))]:
    pts = []
    for i in range(41):
        t = i / 40.0
        bx = (1 - t) ** 3 * seg[0][0] + 3 * (1 - t) ** 2 * t * seg[1][0] \
            + 3 * (1 - t) * t ** 2 * seg[2][0] + t ** 3 * seg[3][0]
        by = (1 - t) ** 3 * seg[0][1] + 3 * (1 - t) ** 2 * t * seg[1][1] \
            + 3 * (1 - t) * t ** 2 * seg[2][1] + t ** 3 * seg[3][1]
        pts.append((bx, by))
    for i in range(len(pts) - 1):
        thick_line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                   4.5, (52, 26, 14), 0.9)
        thick_line(pts[i][0], pts[i][1] - 1.5, pts[i + 1][0],
                   pts[i + 1][1] - 1.5, 1.4, (168, 96, 46), 0.55)
# cocoa dust over the cake top and the plate around it
for _ in range(420):
    ang = rnd.random() * 2 * math.pi
    rr = rnd.random()
    dx = CAKE_CX + 200 * rr * math.cos(ang)
    dy = 400 + 210 * rr * math.sin(ang) * 0.6
    fill_circle(int(dx), int(dy), 1.6, (58, 36, 22), 0.55)
for _ in range(160):
    dx = CAKE_CX - 150 + rnd.random() * 300
    dy = CAKE_TOP + rnd.random() * 80
    fill_circle(int(dx), int(dy), 1.5, (70, 44, 26), 0.6)
# a few sea-salt flakes catching the light on the molten river
for _ in range(12):
    sx = 480 + rnd.random() * 260
    sy = 640 + rnd.random() * 90
    fill_ellipse(sx, sy, 3.0, 1.8, (255, 250, 240), 0.95)

# ---------------------------------------------------------------- steam
# Faint warm steam curling off the hot fondant.
for band in range(3):
    bx = 380 + band * 70
    for y in range(180, 360):
        t = (360 - y) / 180.0
        wob = 18 * math.sin(y * 0.04 + band * 2.2)
        for x in range(int(bx + wob - 20), int(bx + wob + 21)):
            dd = abs(x - (bx + wob)) / 20.0
            if dd < 1:
                blend_px(x, y, (255, 240, 224),
                         0.06 * (1 - dd) * (0.3 + 0.7 * t))

# ---------------------------------------------------------------- vignette
for y in range(H):
    for x in range(W):
        d = math.hypot((x - 512) / 720.0, (y - 600) / 720.0)
        if d > 0.68:
            blend_px(x, y, (6, 4, 4), min(0.42, (d - 0.68) * 1.1))


# ---------------------------------------------------------------- PNG encoder
def chunk(ctype, data):
    out = struct.pack(">I", len(data)) + ctype + data
    out += struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)
    return out


def write_png(path):
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += pix[y * W * 3:(y + 1) * W * 3]
    idat = zlib.compress(bytes(raw), 9)
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", idat) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(path)
    print(f"wrote {path} ({W}x{H}, {size} bytes)")


if __name__ == "__main__":
    main()
