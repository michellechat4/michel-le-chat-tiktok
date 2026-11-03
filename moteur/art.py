import math, random, json, os
import numpy as np
import skia
from scipy import ndimage
from scipy.spatial import Voronoi
from PIL import Image, ImageDraw
from tl import *

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TF = skia.Typeface.MakeFromFile(os.path.join(ROOT, "assets", "Lilita.ttf"))
TF_EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")
INK = "#20141A"


# ---------------------------------------------------------------- outils
def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hexmix(a, b, f):
    f = max(0, min(1, f))
    ra, rb = rgb(a), rgb(b)
    return "#%02X%02X%02X" % tuple(int(ra[i] + (rb[i] - ra[i]) * f) for i in range(3))


def col(h, a=1.0):
    r, g, b = rgb(h)
    return skia.ColorSetARGB(int(255 * max(0, min(1, a))), r, g, b)


def fill(h, a=1.0, **kw):
    return skia.Paint(AntiAlias=True, Color=col(h, a), **kw)


def line(h, sw, a=1.0, **kw):
    return skia.Paint(AntiAlias=True, Color=col(h, a), Style=skia.Paint.kStroke_Style, StrokeWidth=sw,
                      StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join, **kw)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def lerp(a, b, f):
    return a + (b - a) * f


def eout(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ein(x):
    x = clamp(x)
    return x * x * x


def back(x):
    x = clamp(x)
    s = 2.2
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def poly(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def rrect(l, t, r, b, rad):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(l, t, r, b), rad, rad))
    return p


def oval(l, t, r, b):
    p = skia.Path()
    p.addOval(skia.Rect.MakeLTRB(l, t, r, b))
    return p


def shape(c, path, color, sw=6, a=1.0, ink=INK):
    c.drawPath(path, fill(color, a))
    if sw:
        c.drawPath(path, line(ink, sw, a))


def text(c, s, x, y, size, color="#FFFFFF", stroke=None, sw=0, align="center", a=1.0):
    f = skia.Font(TF, size)
    w = f.measureText(s)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    if stroke:
        c.drawString(s, x, y, f, line(stroke, sw, a))
    c.drawString(s, x, y, f, fill(color, a))
    return w


def jitter(t, seed=0):
    r = random.Random(int(t * FPS) * 131 + seed)
    return r.uniform(-1, 1), r.uniform(-1, 1)


# ---------------------------------------------------------------- personnages
def draw_cat(c, x, y, s, t, mood="bliss", vib=0.0, flip_tail=False):
    jx, jy = jitter(t, 3)
    c.save()
    c.translate(x + jx * vib, y + jy * vib)
    c.scale(s, s)
    OR, DK, CR = "#F49A3A", "#C96A1C", "#FFE1B0"
    # queue
    w = math.sin(t * 2.2) * 26
    tail = skia.Path()
    tail.moveTo(95, -35)
    tail.cubicTo(190, -20, 215, -120 + w, 165, -185 + w)
    c.drawPath(tail, line(INK, 48))
    c.drawPath(tail, line(OR, 34))
    # corps
    body = oval(-132, -235, 132, 10)
    shape(c, body, OR, 8)
    c.save()
    c.clipPath(body, skia.ClipOp.kIntersect, True)
    for i, yy in enumerate((-170, -125, -80)):
        c.drawLine(-140, yy, -92, yy + 14, line(DK, 15))
        c.drawLine(140, yy, 92, yy + 14, line(DK, 15))
    c.drawOval(skia.Rect.MakeLTRB(-78, -150, 78, 40), fill(CR))
    c.restore()
    # pattes
    for px in (-52, 52):
        shape(c, oval(px - 40, -30, px + 40, 22), CR, 7)
        c.drawLine(px - 11, -2, px - 11, 16, line(INK, 4))
        c.drawLine(px + 11, -2, px + 11, 16, line(INK, 4))
    # oreilles
    for sgn in (-1, 1):
        ear = poly([(sgn * 128, -285), (sgn * 118, -405), (sgn * 38, -350)])
        shape(c, ear, OR, 8)
        c.drawPath(poly([(sgn * 108, -310), (sgn * 106, -372), (sgn * 62, -342)]), fill("#FFA6A6"))
    # tête
    head = oval(-152, -385, 152, -160)
    shape(c, head, OR, 8)
    c.save()
    c.clipPath(head, skia.ClipOp.kIntersect, True)
    for dx, l_ in ((-34, 44), (0, 56), (34, 44)):
        c.drawLine(dx, -392, dx, -392 + l_, line(DK, 15))
    for sgn in (-1, 1):
        c.drawLine(sgn * 158, -290, sgn * 118, -282, line(DK, 13))
        c.drawLine(sgn * 150, -245, sgn * 112, -244, line(DK, 13))
    c.restore()
    # museau
    c.drawOval(skia.Rect.MakeLTRB(-58, -258, 58, -180), fill(CR))
    for sgn in (-1, 1):
        c.drawOval(skia.Rect.MakeLTRB(sgn * 100 - 26, -262, sgn * 100 + 26, -232), fill("#FF9C8F", 0.75))
    # yeux
    for sgn in (-1, 1):
        ex = sgn * 66
        if mood == "bliss" or (mood == "wink" and sgn == -1):
            p = skia.Path()
            p.moveTo(ex - 28, -278)
            p.quadTo(ex, -318, ex + 28, -278)
            c.drawPath(p, line(INK, 10))
        else:
            c.drawCircle(ex, -292, 30, fill("#FFFFFF"))
            c.drawCircle(ex, -292, 30, line(INK, 7))
            c.drawCircle(ex + 4, -288, 15, fill(INK))
            c.drawCircle(ex + 9, -294, 5, fill("#FFFFFF"))
    # nez, bouche
    c.drawPath(poly([(-13, -250), (13, -250), (0, -234)]), fill("#E8627A"))
    c.drawPath(poly([(-13, -250), (13, -250), (0, -234)]), line(INK, 4))
    m = skia.Path()
    m.moveTo(-30, -222)
    m.quadTo(-14, -202, 0, -226)
    m.quadTo(14, -202, 30, -222)
    c.drawPath(m, line(INK, 6))
    # moustaches
    for sgn in (-1, 1):
        for dy, sl in ((-232, -14), (-218, 0), (-204, 14)):
            c.drawLine(sgn * 62, dy, sgn * 158, dy + sl, line(INK, 3.5))
    c.restore()


def draw_mitt(c, x, y, s, suit=False, soot=0.0):
    col_ = "#F2F2F7" if suit else hexmix("#F7C7A0", "#4A3A34", soot)
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    shape(c, oval(-62, -44, 62, 40), col_, 7)
    for fx in (-40, -14, 12, 38):
        shape(c, rrect(fx - 15, 10, fx + 15, 66, 14), col_, 6)
    shape(c, oval(44, -22, 88, 26), col_, 6)
    c.restore()


def draw_gerard(c, stage, t, suit=False, vib=0.0, moustache=True):
    """stage 0..4 — Gérard, assis côté droit du canapé (coordonnées du salon)."""
    jx, jy = jitter(t, 9)
    c.save()
    c.translate(jx * vib, jy * vib)
    soot = 1.0 if stage >= 4 else 0.0
    skin = "#F7C7A0"
    sweater = "#F2F2F7" if suit else hexmix("#3F6FD8", "#6C7390", soot * 0.45)
    pants = "#D8D8E2" if suit else "#3A3F55"
    # jambes
    shape(c, rrect(690, 1290, 890, 1372, 36), pants, 7)
    shape(c, rrect(712, 1340, 788, 1500, 26), pants, 7)
    shape(c, rrect(800, 1340, 876, 1500, 26), pants, 7)
    shape(c, rrect(692, 1470, 792, 1516, 20), "#23202C", 6)
    shape(c, rrect(796, 1470, 896, 1516, 20), "#23202C", 6)
    # torse
    shape(c, rrect(680, 1096, 900, 1340, 66), sweater, 8)
    # bras gauche posé
    arm = skia.Path()
    arm.moveTo(872, 1160)
    arm.quadTo(930, 1270, 830, 1306)
    c.drawPath(arm, line(INK, 62))
    c.drawPath(arm, line(sweater, 48))
    # tête
    hx, hy = 790, 1000
    if stage >= 2:
        hx -= 8 * math.sin(t * 40) * (stage - 1) * 0.4
    if suit:
        c.drawRect(skia.Rect.MakeLTRB(742, 1060, 838, 1108), fill("#BFC3D2"))
    shape(c, oval(hx - 112, hy - 10, hx - 80, hy + 40), skin, 6)
    shape(c, oval(hx + 80, hy - 10, hx + 112, hy + 40), skin, 6)
    shape(c, oval(hx - 95, hy - 96, hx + 95, hy + 92), skin, 8)
    # cheveux
    hc = "#B9BDC8" if soot else "#8A8F9C"
    if stage <= 1:
        p = skia.Path()
        p.moveTo(hx - 88, hy - 34)
        p.quadTo(hx - 70, hy - 108, hx + 10, hy - 104)
        p.quadTo(hx + 80, hy - 104, hx + 90, hy - 30)
        p.quadTo(hx + 30, hy - 74, hx - 88, hy - 34)
        p.close()
        shape(c, p, hc, 6)
    else:
        spikes = {2: 34, 3: 62, 4: 96}[min(stage, 4)]
        for i in range(9):
            a_ = lerp(-2.45, -0.69, i / 8)
            x0, y0 = hx + 80 * math.cos(a_), hy + 80 * math.sin(a_)
            w_ = math.sin(t * 30 + i) * 6
            c.drawLine(x0, y0, x0 + (80 + spikes) * 0.5 * math.cos(a_) + w_, y0 + (80 + spikes) * 0.5 * math.sin(a_), line(hc, 16))
    # lunettes + yeux
    if stage == 3:   # plissés
        for sgn in (-1, 1):
            ex = hx + sgn * 38
            c.drawLine(ex - 18, hy - 16, ex + 18, hy - 4 if sgn < 0 else hy - 28, line(INK, 8))
            c.drawLine(ex - 18, hy + 4, ex + 18, hy - 4 if sgn < 0 else hy - 28, line(INK, 8))
    else:
        for sgn in (-1, 1):
            ex = hx + sgn * 38
            rr = {0: 6, 1: 7, 2: 11, 4: 15}.get(min(stage, 4), 7)
            c.drawCircle(ex, hy - 12, rr if not soot else 7, fill(INK))
    for sgn in (-1, 1):
        ex = hx + sgn * 38
        c.drawCircle(ex, hy - 12, 30, line(INK, 6))
    c.drawLine(hx - 8, hy - 12, hx + 8, hy - 12, line(INK, 6))
    if stage >= 4:
        for dx, dy in ((-22, -22), (-10, 6), (-38, 0)):
            c.drawLine(hx - 38, hy - 12, hx - 38 + dx * .9, hy - 12 + dy * .9, line(INK, 3))
        # cendres + fumée
        for dx, dy, rx, ry in ((-58, -58, 16, 9), (46, -62, 12, 7), (62, 18, 13, 8), (-66, 26, 10, 6)):
            c.drawOval(skia.Rect.MakeLTRB(hx + dx - rx, hy + dy - ry, hx + dx + rx, hy + dy + ry), fill("#8E8A90", .55))
        for i in range(3):
            ph = (t * .9 + i * .33) % 1
            rs_ = 14 + ph * 26
            c.drawCircle(hx - 40 + i * 40 + math.sin(t * 3 + i) * 10, hy - 150 - ph * 90, rs_, fill("#C9CBD6", .55 * (1 - ph)))
    # moustache + bouche
    if stage <= 1:
        p = skia.Path()
        p.moveTo(hx - 26, hy + 48)
        p.quadTo(hx, hy + 66 - stage * 18, hx + 26, hy + 48)
        c.drawPath(p, line(INK, 6))
    elif stage == 2:
        c.drawOval(skia.Rect.MakeLTRB(hx - 14, hy + 44, hx + 14, hy + 70), fill(INK))
    else:
        shape(c, rrect(hx - 36, hy + 42, hx + 36, hy + 74, 8), "#FFFFFF", 6)
        for dx in (-18, 0, 18):
            c.drawLine(hx + dx, hy + 42, hx + dx, hy + 74, line(INK, 3))
    must = "#6A6470"
    p = skia.Path()
    p.moveTo(hx, hy + 22)
    p.quadTo(hx - 34, hy + 16, hx - 58, hy + 40)
    p.quadTo(hx - 30, hy + 46, hx, hy + 34)
    p.quadTo(hx + 30, hy + 46, hx + 58, hy + 40)
    p.quadTo(hx + 34, hy + 16, hx, hy + 22)
    p.close()
    if moustache:
        c.drawPath(p, fill(must))
    if stage in (2, 3):
        for i in range(2):
            ph = (t * 1.8 + i * .5) % 1
            c.drawCircle(hx + 104 + ph * 18, hy - 60 + ph * 60, 9 * (1 - ph * .4), fill("#7EC8FF"))
    if suit:
        c.drawCircle(hx, hy, 128, fill("#BEE8FF", 0.22))
        c.drawCircle(hx, hy, 128, line("#E9F6FF", 10))
        c.drawCircle(hx, hy, 128, line(INK, 3))
        p = skia.Path()
        p.addArc(skia.Rect.MakeLTRB(hx - 106, hy - 106, hx + 106, hy + 106), 200, 60)
        c.drawPath(p, line("#FFFFFF", 9, 0.8))
    c.restore()


def gerard_stage(n):
    return 0 if n <= 2 else 1 if n <= 5 else 2 if n <= 8 else 3 if n <= 12 else 4


def draw_couch(c):
    TE, TD = "#2F9C8F", "#1F7A70"
    for lx in (170, 950):
        c.drawRect(skia.Rect.MakeLTRB(lx, 1425, lx + 34, 1490), fill(INK))
    shape(c, rrect(135, 1085, 1005, 1325, 54), TD, 8)
    for lx in (420, 715):
        c.drawLine(lx, 1100, lx, 1310, line(INK, 5, 0.5))
    shape(c, rrect(105, 1296, 1035, 1440, 34), TE, 8)
    c.drawLine(570, 1300, 570, 1436, line(INK, 5, 0.5))
    shape(c, rrect(70, 1178, 190, 1446, 48), TE, 8)
    shape(c, rrect(950, 1178, 1070, 1446, 48), TE, 8)


def draw_group(c, t, n, suit=False, mood="bliss", vib=0.0, hand_lift=0.0):
    """Canapé + Michel + Gérard + bras qui caresse, en coordonnées du salon."""
    draw_couch(c)
    stage = gerard_stage(n)
    draw_gerard(c, stage, t, suit, vib * 0.35)
    draw_cat(c, 360, 1312, 1.0, t, mood, vib)
    # bras + main
    ph = math.cos(stroke_phase(t) * 2 * math.pi)
    hx = 360 + 74 * ph
    hy = 905 + 14 * math.sin(stroke_phase(t) * 2 * math.pi) - hand_lift
    sw = "#F2F2F7" if suit else hexmix("#3F6FD8", "#6C7390", 0.45 if stage >= 4 else 0)
    arm = skia.Path()
    arm.moveTo(715, 1140)
    arm.quadTo(640, 960 - hand_lift * 0.4, hx + 62, hy + 2)
    c.drawPath(arm, line(INK, 62))
    c.drawPath(arm, line(sw, 48))
    c.save()
    c.translate(hx, hy)
    c.rotate(14 * ph * 0.4)
    draw_mitt(c, 0, 0, 1.0, suit, 0)
    c.restore()


def draw_rings(c, x, y, t, n, maxr=800, speed=None, count=5, hue=None, width=None):
    f = clamp(n / 20)
    color = hue or hexmix("#FFFFFF", "#FF3B30", f)
    speed = speed or (90 + n * 30)
    gap = maxr / count
    for i in range(count):
        r = (t * speed + i * gap) % maxr
        a = (1 - r / maxr) * (0.25 + 0.45 * clamp(n / 8))
        c.drawCircle(x, y, r + 4, line(color, width or (3 + n * 0.9), a))


# ---------------------------------------------------------------- SALON
_salon_rng = random.Random(11)
SHARDS = []
for i in range(70):
    a = _salon_rng.uniform(0, 2 * math.pi)
    SHARDS.append(dict(x=_salon_rng.uniform(80, 420), y=_salon_rng.uniform(720, 1000),
                       vx=math.cos(a) * _salon_rng.uniform(150, 1100), vy=math.sin(a) * _salon_rng.uniform(100, 800) - 150,
                       s=_salon_rng.uniform(16, 62), w=_salon_rng.uniform(-9, 9), a=_salon_rng.uniform(0, 6),
                       g=_salon_rng.uniform(1.2, 3.4)))
LEAVES = [(random.Random(i).uniform(-1, 1), random.Random(i * 7 + 1).uniform(0, 1)) for i in range(12)]


def draw_salon(c, t, n):
    # mur
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#F7DDAE"))
    for x in range(-40, W + 80, 120):
        c.drawRect(skia.Rect.MakeLTRB(x, 0, x + 60, 1490), fill("#F2D29C", 0.55))
    # fissures du mur
    if n >= 11:
        cr = line(INK, 5, 0.75)
        for pts in ([(640, 620), (610, 720), (660, 800), (620, 900)], [(1030, 1010), (980, 960), (1010, 900), (960, 850)],
                    [(40, 1120), (70, 1060), (35, 1020)]):
            k = len(pts) if n >= 12 else len(pts) - 1
            c.drawPath(poly(pts[:k], close=False), cr)
    # plinthe + sol
    c.drawRect(skia.Rect.MakeLTRB(0, 1466, W, 1495), fill("#FFF5E0"))
    c.drawRect(skia.Rect.MakeLTRB(0, 1495, W, H), fill("#B47B4C"))
    for i, y in enumerate(range(1540, H, 90)):
        c.drawLine(0, y, W, y, line("#94613A", 5))
    c.drawOval(skia.Rect.MakeLTRB(60, 1520, 1020, 1720), fill("#D9534F"))
    c.drawOval(skia.Rect.MakeLTRB(130, 1548, 950, 1692), line("#F7DDAE", 8))
    # fenêtre
    since13 = t - T[13]
    c.save()
    win = skia.Rect.MakeLTRB(68, 712, 432, 1006)
    sky = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 712), (0, 1006)], [col("#6FC6F5"), col("#D8F3FF")]))
    c.drawRect(win, sky)
    c.save()
    c.clipRect(win)
    for bx, bw, bh, bc in ((70, 90, 110, "#8BA2BF"), (170, 70, 70, "#A5B7CF"), (250, 100, 140, "#7E96B5"), (360, 80, 90, "#A5B7CF")):
        c.drawRect(skia.Rect.MakeLTRB(bx, 1006 - bh, bx + bw, 1006), fill(bc))
    if n < 13:
        c.drawPath(poly([(120, 712), (190, 712), (80, 1006), (68, 1006), (68, 860)]), fill("#FFFFFF", 0.35))
        if n == 12:
            cc = line("#FFFFFF", 4)
            cx, cy = 250, 860
            r = random.Random(3)
            prog = clamp((t - T[12]) / 0.5)
            for i in range(14):
                a = r.uniform(0, 6.28)
                l_ = r.uniform(70, 230) * prog
                c.drawLine(cx, cy, cx + math.cos(a) * l_, cy + math.sin(a) * l_, cc)
    else:
        for pts in ([(68, 712), (150, 712), (68, 790)], [(432, 1006), (432, 930), (360, 1006)], [(432, 712), (370, 712), (432, 760)]):
            c.drawPath(poly(pts), fill("#D8F3FF", 0.9))
            c.drawPath(poly(pts), line("#FFFFFF", 3))
    c.restore()
    fr = line("#FFFFFF", 18)
    c.drawRect(win, line(INK, 26))
    c.drawRect(win, fr)
    if n < 13:
        c.drawLine(250, 712, 250, 1006, line("#FFFFFF", 12))
        c.drawLine(68, 860, 432, 860, line("#FFFFFF", 12))
    shape(c, rrect(44, 1006, 456, 1032, 8), "#FFF5E0", 6)
    c.restore()
    # bocal
    bjx, bjy = jitter(t, 21)
    bx, by = 118 + bjx * clamp(n / 8) * 4, 950 + bjy * clamp(n / 8) * 3
    if n < 13:
        c.drawCircle(bx, by, 56, fill("#BDEBFF", 0.55))
        fishx = bx + (6 if n >= 3 else math.sin(t * 2) * 18)
        fishy = by + 10
        c.save()
        c.translate(fishx, fishy)
        if n >= 3:
            c.scale(1.15, 1.15)
        c.drawPath(poly([(14, 0), (36, -14), (36, 14)]), fill("#FF7A2F"))
        c.drawOval(skia.Rect.MakeLTRB(-24, -14, 20, 14), fill("#FF7A2F"))
        c.drawCircle(-12, -3, 7 if n >= 3 else 4, fill("#FFFFFF"))
        c.drawCircle(-14, -3, 3, fill(INK))
        if n >= 3:
            c.drawOval(skia.Rect.MakeLTRB(-24, 4, -16, 11), fill(INK))
        c.restore()
        c.drawCircle(bx, by, 56, line(INK, 6))
        c.drawCircle(bx, by, 56, line("#FFFFFF", 2, 0.6))
    # tableau
    if n < 9 or (n == 9 and t - T[9] < 0.6):
        drop = 0
        ang = 0
        if n >= 5:
            ang = 8
        if n >= 7:
            ang = 22
        if n >= 9:
            drop = 2400 * (t - T[9]) ** 2
            ang = 22 + (t - T[9]) * 300
        ang += math.sin(t * 34) * clamp((n - 3) / 6) * 3
        c.save()
        c.translate(850, 690 + drop)
        c.rotate(ang)
        c.drawLine(0, 0, 0, 22, line(INK, 4))
        shape(c, rrect(-108, 22, 108, 180, 6), "#7B4A2B", 6)
        c.drawRect(skia.Rect.MakeLTRB(-92, 38, 92, 164), fill("#BFE6FF"))
        c.drawPath(poly([(-92, 164), (-30, 76), (24, 164)]), fill("#6F8FA8"))
        c.drawPath(poly([(-14, 164), (46, 100), (92, 164)]), fill("#88A7BE"))
        c.drawCircle(60, 62, 14, fill("#FFD84D"))
        c.restore()
    # plante
    fall = 0
    if n >= 8:
        fall = 74 * eout((t - T[8]) / 0.4)
    c.save()
    c.translate(70, 1490)
    c.rotate(-fall)
    pc = "#3E9E5A"
    bare = clamp((n - 6) / 6)
    for i in range(7):
        a = lerp(-155, -25, i / 6)
        if i / 7 < bare:
            continue
        p = skia.Path()
        ex, ey = math.cos(math.radians(a)) * 150, -60 + math.sin(math.radians(a)) * 170
        p.moveTo(0, -60)
        p.quadTo(ex * .4 - 26, ey * .6, ex, ey)
        p.quadTo(ex * .6 + 26, ey * .5, 0, -60)
        p.close()
        shape(c, p, pc, 5)
    shape(c, poly([(-44, -70), (44, -70), (32, 0), (-32, 0)]), "#D9794B", 6)
    c.restore()
    if n >= 6:
        for i, (lx, ly) in enumerate(LEAVES):
            p = (t * .5 + i * .13) % 1
            c.drawOval(skia.Rect.MakeLTRB(70 + lx * 60 + p * 60, 1300 + p * 210, 90 + lx * 60 + p * 60, 1312 + p * 210), fill(pc, 1 - p))
    # TOC TOC
    if T[6] <= t < T[7]:
        for k, (dt, tx, ty, rot) in enumerate(((0.1, 870, 930, -8), (0.45, 985, 790, 7), (0.8, 900, 660, -6))):
            if t >= T[6] + dt:
                s = back((t - T[6] - dt) / 0.18)
                c.save()
                c.translate(tx, ty)
                c.rotate(rot)
                c.scale(s, s)
                text(c, "TOC !", 0, 0, 62, "#FF3B30", "#FFFFFF", 12)
                c.restore()
    # boîte de nuit
    club = T[8] <= t < T[9]
    if club:
        ballx, bally = 600, 690
        drop = eout((t - T[8]) / 0.2)
        by_ = lerp(380, bally, drop)
        c.drawLine(ballx, 380, ballx, by_ - 60, line(INK, 5))
        for i, h_ in enumerate(("#FF3BB0", "#34D1FF", "#FFE14D", "#7CFF6B", "#B46BFF", "#FF7A2F")):
            a = t * 2.2 + i
            ex, ey = ballx + math.cos(a) * 1300, by_ + abs(math.sin(a)) * 1300
            c.drawPath(poly([(ballx, by_), (ex - 90, ey), (ex + 90, ey)]), fill(h_, 0.22))
        gr = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((ballx - 16, by_ - 16), 70, [col("#FFFFFF"), col("#A9B6C9")]))
        c.drawCircle(ballx, by_, 58, gr)
        c.drawCircle(ballx, by_, 58, line(INK, 6))
    # groupe
    jump = 0
    if n >= 8:
        jump = abs(math.sin(t * 32)) * clamp((n - 7) / 5) * 14
    c.save()
    c.translate(0, -jump)
    draw_rings(c, 360, 1090, t, n, maxr=lerp(300, 1500, clamp(n / 13)), count=4 + min(n // 2, 5))
    draw_group(c, t, n, False, "bliss", vib=clamp(n / 13) ** 1.3 * 16)
    c.restore()
    if club:
        lunette(c)
    # poussière / éclats
    if since13 >= 0:
        for sh in SHARDS:
            tt = since13 * 1.15
            gx = sh["x"] + sh["vx"] * tt
            gy = sh["y"] + sh["vy"] * tt + 900 * tt * tt
            s = sh["s"] * (1 + tt * sh["g"])
            c.save()
            c.translate(gx, gy)
            c.rotate(math.degrees(sh["a"] + sh["w"] * tt))
            p = poly([(-s * .5, -s * .3), (s * .55, -s * .55), (s * .15, s * .6)])
            c.drawPath(p, fill("#C9F0FF", 0.82))
            c.drawPath(p, line("#FFFFFF", 3))
            c.restore()
        if n == 13 and since13 < 0.18:
            c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", 0.9 * (1 - since13 / 0.18)))
        # le poisson, projeté, surpris
        tt = since13
        fx, fy = 118 + 720 * tt, 950 - 620 * tt + 500 * tt * tt
        c.save()
        c.translate(fx, fy)
        c.rotate(tt * 500)
        c.scale(2.0, 2.0)
        c.drawPath(poly([(14, 0), (36, -14), (36, 14)]), fill("#FF7A2F"))
        c.drawOval(skia.Rect.MakeLTRB(-24, -14, 20, 14), fill("#FF7A2F"))
        c.drawCircle(-12, -3, 7, fill("#FFFFFF"))
        c.drawCircle(-13, -3, 3, fill(INK))
        c.restore()


def lunette(c):
    # Michel met des lunettes pour la boîte de nuit
    jump_y = 0
    c.save()
    c.translate(360, 1312 - 292 + jump_y)
    for sgn in (-1, 1):
        shape(c, rrect(sgn * 66 - 46, -26, sgn * 66 + 46, 34, 16), "#14121C", 4, ink="#000000")
    c.drawLine(-24, -10, 24, -10, line("#14121C", 9))
    c.drawLine(-92, -14, -60, 8, line("#FFFFFF", 5, 0.8))
    c.drawLine(40, -14, 72, 8, line("#FFFFFF", 5, 0.8))
    c.restore()


# ---------------------------------------------------------------- RUE
def draw_house(c, x, w, h, ground, body, roof, broken=False):
    shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(x, ground - h, x + w, ground)), body, 7)
    shape(c, poly([(x - 30, ground - h), (x + w / 2, ground - h - w * .42), (x + w + 30, ground - h)]), roof, 7)
    # fenêtres
    for fx in (x + w * .14, x + w * .58):
        for fy in (ground - h + 28, ground - h + h * .52):
            rc = skia.Rect.MakeLTRB(fx, fy, fx + w * .28, fy + h * .28)
            c.drawRect(rc, fill("#2C3550" if broken else "#CDEBFF"))
            c.drawRect(rc, line(INK, 5))


def draw_car(c, x, y, s, body, blink, flip=0):
    c.save()
    c.translate(x, y)
    c.rotate(flip)
    c.scale(s, s)
    shape(c, rrect(-80, -44, 80, 0, 16), body, 5)
    shape(c, poly([(-44, -44), (-26, -78), (34, -78), (54, -44)]), "#CDEBFF", 5)
    for wx in (-48, 48):
        c.drawCircle(wx, 2, 19, fill(INK))
        c.drawCircle(wx, 2, 8, fill("#B8BCC8"))
    if blink:
        for bx in (-80, 80):
            c.drawCircle(bx, -28, 26, fill("#FFB000", 0.45))
            c.drawCircle(bx, -28, 12, fill("#FFD34D"))
    c.restore()


TILES = [(random.Random(i).uniform(-1, 1), random.Random(i + 50).uniform(0.4, 1), random.Random(i + 90).uniform(0, 6)) for i in range(40)]


def draw_rue(c, t, n):
    g = 1420
    hot = clamp((n - 15) / 2)
    sky = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, 0), (0, g)], [col(hexmix("#5CB8F2", "#E8622C", hot)), col(hexmix("#D3F1FF", "#FFC36B", hot))]))
    c.drawRect(skia.Rect.MakeWH(W, H), sky)
    # sol
    c.drawRect(skia.Rect.MakeLTRB(0, g, W, H), fill("#6B6E7E"))
    c.drawRect(skia.Rect.MakeLTRB(0, g, W, g + 26), fill("#9EA1AE"))
    for x in range(-40, W, 180):
        c.drawRect(skia.Rect.MakeLTRB(x, g + 150, x + 100, g + 164), fill("#F4E9B8"))
    # voisins
    t16 = t - T[16]
    for i, (x, w, h, b, r, rot, vx) in enumerate(((-70, 310, 360, "#E58B7B", "#7A3B3B", -24, -520),
                                                   (780, 310, 400, "#8FC8A2", "#3B5E4A", 26, 560),
                                                   (150, 200, 250, "#CDB7E8", "#4F3F7A", -40, -160),
                                                   (690, 180, 220, "#F0D07A", "#7A5F2C", 44, 200))):
        c.save()
        if t16 >= 0:
            d = t16 - i * 0.05
            d = max(d, 0)
            c.translate(x + w / 2 + vx * d, g - 900 * d * d * 2 - 280 * d)
            c.rotate(rot * d * 3)
            c.translate(-(x + w / 2), -g)
        draw_house(c, x, w, h, g, b, r, broken=n >= 13)
        c.restore()
    # maison de Michel
    ruins = n >= 17
    t17 = t - T[17]
    hx, hw, hh = 310, 460, 480
    if not ruins:
        draw_house(c, hx, hw, hh, g, "#F7DDAE", "#B24B36", broken=True)
        # fenêtre géante ouverte sur Michel
        c.save()
        rc = skia.Rect.MakeLTRB(hx + 90, g - 300, hx + 370, g - 60)
        c.drawRect(rc, fill("#F7DDAE"))
        c.clipRect(rc)
        c.translate(hx + 230, g - 165)
        c.scale(0.3, 0.3)
        c.translate(-570, -1200)
        draw_group(c, t, 13, False, "bliss", vib=25)
        c.restore()
        c.drawRect(rc, line(INK, 8))
    else:
        c.drawRect(skia.Rect.MakeLTRB(hx - 30, g - 18, hx + hw + 30, g + 4), fill("#7B6A5A"))
        c.save()
        c.translate(540, g - 0)
        c.scale(0.5, 0.5)
        c.translate(-570, -1495)
        draw_group(c, t, 14, False, "bliss", vib=25)
        c.restore()
    # voitures
    blink = (t * 6) % 1 < .5
    cars = ((180, g + 92, "#D9534F", 0.95), (880, g + 92, "#3F6FD8", 0.95), (530, g + 118, "#F2B035", 1.15))
    for i, (x, y, cc, s) in enumerate(cars):
        fl = 0
        dy = 0
        dx = 0
        if t16 >= 0:
            d = max(0, t16 - i * .12)
            fl = (-1) ** i * d * 620
            dy = -1200 * d + 700 * d * d
            dx = (x - 540) * d * 2.6
        jx, jy = jitter(t, i + 40)
        draw_car(c, x + dx + jx * 4, y + dy + jy * 4, s, cc, blink, fl)
    # tuiles
    if t >= T[15]:
        tt = t - T[15]
        for i, (a, sp, rr) in enumerate(TILES):
            k = (tt * sp * 1.3 + i * .04)
            x = 540 + a * 680 * k
            y = g - 620 - 560 * k + 300 * k * k
            c.save()
            c.translate(x, y)
            c.rotate(rr * 80 + tt * 600 * a)
            c.drawRect(skia.Rect.MakeLTRB(-22, -9, 22, 9), fill("#B24B36"))
            c.drawRect(skia.Rect.MakeLTRB(-22, -9, 22, 9), line(INK, 3))
            c.restore()
    # ondes
    draw_rings(c, 540, g - 200, t, n, maxr=1300, count=6)
    # onde de choc
    if t17 >= 0:
        for k in range(3):
            r = (t17 - k * .28) * 1500
            if r > 0:
                c.drawCircle(540, g - 150, r, line("#FFFFFF", 80 - k * 20, clamp(1 - r / 2400)))
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", clamp(1 - t17 / .22) * .9))
        for k in range(50):
            rr = random.Random(k)
            a = rr.uniform(0, 6.28)
            d = (t17 * rr.uniform(500, 1500))
            x, y = 540 + math.cos(a) * d, g - 150 + math.sin(a) * d
            sz = rr.uniform(8, 34)
            c.drawRect(skia.Rect.MakeLTRB(x - sz, y - sz * .6, x + sz, y + sz * .6), fill(rr.choice(("#F7DDAE", "#B24B36", "#7B6A5A"))))


# ---------------------------------------------------------------- PARIS
def eiffel_path(h):
    """Silhouette de la tour, base au (0,0), haut en (0,-h)."""
    u = h / 100
    pts = [(-30, 0), (-22, 0), (-13, -22), (-10.5, -30), (-5, -56), (-1.6, -90), (0, -100),
           (1.6, -90), (5, -56), (10.5, -30), (13, -22), (22, 0), (30, 0), (22, -20), (15, -30), (8, -56), (-8, -56), (-15, -30), (-22, -20)]
    return poly([(x * u, y * u) for x, y in pts])


def draw_eiffel(c, h, body="#3A2F3F"):
    u = h / 100
    c.save()
    arch = skia.Path()
    arch.moveTo(-34 * u, 0)
    arch.lineTo(-24 * u, -18 * u)
    arch.lineTo(-13 * u, -33 * u)
    arch.lineTo(-5 * u, -62 * u)
    arch.lineTo(-1.7 * u, -92 * u)
    arch.lineTo(0, -102 * u)
    arch.lineTo(1.7 * u, -92 * u)
    arch.lineTo(5 * u, -62 * u)
    arch.lineTo(13 * u, -33 * u)
    arch.lineTo(24 * u, -18 * u)
    arch.lineTo(34 * u, 0)
    arch.lineTo(19 * u, 0)
    arch.quadTo(0, -24 * u, -19 * u, 0)
    arch.close()
    c.drawPath(arch, fill(body))
    c.drawPath(arch, line(INK, 5))
    # croisillons
    ln = line("#7E6F86", 2.5)
    for y0, y1, w0, w1 in ((-3, -18, 28, 20), (-22, -33, 19, 12), (-36, -60, 11, 5), (-63, -90, 4.4, 1.6)):
        steps = 4
        for i in range(steps):
            a0, a1 = i / steps, (i + 1) / steps
            ya, yb = lerp(y0, y1, a0) * u, lerp(y0, y1, a1) * u
            wa, wb = lerp(w0, w1, a0) * u, lerp(w0, w1, a1) * u
            c.drawLine(-wa, ya, wb * .55, yb, ln)
            c.drawLine(wa, ya, -wb * .55, yb, ln)
    for py, pw in ((-19, 25), (-34, 15), (-63, 6.5)):
        c.drawRect(skia.Rect.MakeLTRB(-pw * u, py * u - 4, pw * u, py * u + 4), fill(body))
        c.drawRect(skia.Rect.MakeLTRB(-pw * u, py * u - 4, pw * u, py * u + 4), line(INK, 3))
    c.restore()


_pr = random.Random(5)
ROWS = []
for row, (ybase, hmin, hmax, wmin, wmax, colr) in enumerate(((1300, 200, 330, 90, 170, "#6D5E86"), (1400, 200, 320, 110, 190, "#4F4468"), (1520, 170, 280, 130, 220, "#352F4C"))):
    x = -60
    bl = []
    while x < W + 60:
        w = _pr.uniform(wmin, wmax)
        h = _pr.uniform(hmin, hmax)
        wins = []
        for ix in range(int((w - 16) // 34)):
            for iy in range(int((h - 50) // 54)):
                wins.append((x + 14 + ix * 34, ybase - h + 40 + iy * 54, _pr.random()))
        bl.append((x, w, h, wins, _pr.random()))
        x += w
    ROWS.append((ybase, colr, bl))

BUBBLES = [(205, 830, "OH !", -4), (800, 880, "ÇA VA, OUI ?!", 4), (280, 1040, "MICHEL !!!", -3), (810, 1090, "ON DORT ICI !", 3)]


def draw_paris(c, t, n):
    t18 = t - T[18]
    t21 = t - T[21]
    t22 = t - T[22]
    # ciel de nuit
    sky = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, 0), (0, 1400)], [col("#141A44"), col("#39356E"), col("#E8785A")], [0, .62, 1]))
    c.drawRect(skia.Rect.MakeWH(W, H), sky)
    r_ = random.Random(2)
    for i in range(90):
        x, y = r_.uniform(0, W), r_.uniform(0, 1000)
        c.drawCircle(x, y, r_.uniform(1, 3), fill("#FFFFFF", r_.uniform(.3, .9)))
    c.drawCircle(150, 700, 54, fill("#F6F1D0"))
    # tour Eiffel
    tx, ty, th = 540, 1270, 620
    lean = 0
    if t >= T[20]:
        lean = 14 * eout((t - T[20]) / 0.5) + math.sin(t * 34) * 1.2
    c.save()
    if t21 >= 0:
        d = t21
        c.translate(tx + 250 * d * d, ty - 1700 * d * d - 240 * d)
        c.rotate(lean + 240 * d * d)
    else:
        c.translate(tx, ty)
        c.rotate(lean)
    if t21 < 0.9:
        draw_eiffel(c, th)
        if t21 >= 0:
            # flammes du décollage
            for k in range(6):
                fl = 90 + 60 * math.sin(t * 50 + k)
                x_ = lerp(-200, 200, k / 5)
                c.drawPath(poly([(x_ - 34, 0), (x_ + 34, 0), (x_, fl * 1.8)]), fill("#FFB000"))
                c.drawPath(poly([(x_ - 16, 0), (x_ + 16, 0), (x_, fl)]), fill("#FFF3B0"))
    c.restore()
    # immeubles
    for ri, (yb, colr, bl) in enumerate(ROWS):
        for (x, w, h, wins, rnd) in bl:
            c.save()
            sh = 0
            if t22 >= 0:
                d = clamp(t22 * 1.6 - abs(x + w / 2 - 540) / 900)
                sh = (x + w / 2 - 540) / 540 * 80 * d
                c.translate(x + w / 2, yb)
                c.rotate(sh)
                c.scale(1, 1 - d * .85)
                c.translate(-(x + w / 2), -yb)
            jx, jy = jitter(t, ri * 100 + int(x))
            c.translate(jx * 4, jy * 3)
            c.drawRect(skia.Rect.MakeLTRB(x, yb - h, x + w, H), fill(colr))
            c.drawPath(poly([(x - 6, yb - h), (x + 12, yb - h - 28), (x + w - 12, yb - h - 28), (x + w + 6, yb - h)]), fill(hexmix(colr, "#101020", .35)))
            c.drawRect(skia.Rect.MakeLTRB(x, yb - h, x + w, H), line(INK, 3))
            wake = eout((t18 - 0.05) / 0.8)
            for (wx, wy, r) in wins:
                on = r < wake * 1.05
                c.drawRect(skia.Rect.MakeLTRB(wx, wy, wx + 18, wy + 30), fill("#FFD966" if on else "#241F38"))
            c.restore()
    # sol : le canapé, seul au milieu de tout ça
    c.save()
    c.translate(540, 1560)
    c.scale(0.25, 0.25)
    c.translate(-570, -1495)
    draw_group(c, t, 18, False, "bliss", vib=20)
    c.restore()
    draw_rings(c, 540, 1460, t, n, maxr=1500, count=7)
    # râleurs
    if T[19] <= t < T[20] + 0.2:
        for i, (x, y, s_, rot) in enumerate(BUBBLES):
            d = t - T[19] - i * .16
            if d >= 0:
                bubble(c, x, y, s_, 46, back(d / .16), rot)
    # dôme
    if t22 >= 0:
        rad = eout(t22 / 1.2) * 1650
        pp = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
            (540, 1500), max(rad, 1), [col("#FFFFFF"), col("#FFF3B0"), col("#FF8A1F"), col("#FF3B10", .85), col("#FF3B10", 0)], [0, .35, .62, .92, 1]))
        c.drawRect(skia.Rect.MakeWH(W, H), pp)
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", clamp(1 - t22 / .14)))


def bubble(c, x, y, s, size, scale=1.0, rot=0, tail=True, color="#FFFFFF", ink=INK):
    f = skia.Font(TF, size)
    w = f.measureText(s)
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(scale, scale)
    pad = 26
    p = rrect(-w / 2 - pad, -size * .85 - 8, w / 2 + pad, size * .35 + 8, 26)
    if tail:
        p.moveTo(-18, size * .35 + 4)
        p.lineTo(-2, size * .35 + 44)
        p.lineTo(26, size * .35 + 4)
        p.close()
        c.drawPath(p, fill(color))
        c.drawPath(p, line(ink, 7))
        c.drawRect(skia.Rect.MakeLTRB(-14, size * .35 - 2, 22, size * .35 + 10), fill(color))
    else:
        c.drawPath(p, fill(color))
        c.drawPath(p, line(ink, 7))
    c.drawString(s, -w / 2, 0, f, fill(ink))
    c.restore()


# ---------------------------------------------------------------- TERRE
def _load_land():
    cache = os.path.join(HERE, "land.npz")
    if os.path.exists(cache):
        d = np.load(cache)
        return d["hi"], d["lo"], d["cloud"]
    topo = json.load(open(os.path.join(ROOT, "donnees", "land-10m.json")))
    tr = topo["transform"]
    sx, sy = tr["scale"]
    tx, ty = tr["translate"]
    arcs = []
    for a in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in a:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)

    def ring(ids):
        out = []
        for i in ids:
            pts = arcs[i] if i >= 0 else arcs[~i][::-1]
            out.extend(pts if not out else pts[1:])
        return out

    w_, h_ = 8192, 4096
    img = Image.new("L", (w_, h_), 0)
    dr = ImageDraw.Draw(img)
    conv = lambda pts: [((lo + 180) / 360 * w_, (90 - la) / 180 * h_) for lo, la in pts]
    for g in topo["objects"]["land"]["geometries"]:
        polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]]
        for pl in polys:
            dr.polygon(conv(ring(pl[0])), fill=255)
            for hole in pl[1:]:
                dr.polygon(conv(ring(hole)), fill=0)
    arr = np.array(img, dtype=np.float32)
    hi = ndimage.gaussian_filter(arr, 1.6).astype(np.uint8)
    lo = np.array(Image.fromarray(hi).resize((2048, 1024), Image.BILINEAR))
    lo = ndimage.gaussian_filter(lo.astype(np.float32), 1.0).astype(np.uint8)
    rs = np.random.RandomState(4)
    nz = rs.rand(1024, 2048).astype(np.float32)
    cl = ndimage.gaussian_filter(nz, (9, 22), mode="wrap") * 1.0
    cl2 = ndimage.gaussian_filter(rs.rand(1024, 2048).astype(np.float32), (3, 8), mode="wrap")
    cl = (cl - cl.mean()) / cl.std() + 0.4 * (cl2 - cl2.mean()) / cl2.std()
    cl = ((cl + 3) / 6 * 255).clip(0, 255).astype(np.uint8)
    np.savez_compressed(cache, hi=hi, lo=lo, cloud=cl)
    return hi, lo, cl


LAND_HI, LAND_LO, CLOUD = _load_land()
LAT0, LON0 = math.radians(48.85), math.radians(2.35)
EX, EY = 540, 1040


def _sample(tex, u, v):
    h, w = tex.shape
    x = u * w
    y = np.clip(v * h, 0, h - 1.001)
    x0 = np.floor(x).astype(np.int32)
    y0 = y.astype(np.int32)
    fx = (x - x0).astype(np.float32)
    fy = (y - y0).astype(np.float32)
    x0 %= w
    x1 = (x0 + 1) % w
    a = tex[y0, x0].astype(np.float32)
    b = tex[y0, x1].astype(np.float32)
    c_ = tex[y0 + 1, x0].astype(np.float32)
    d = tex[y0 + 1, x1].astype(np.float32)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c_ * (1 - fx) + d * fx) * fy


def carr(h):
    return np.array(rgb(h), dtype=np.float32)


def earth_rgba(R, heat=0.0, boil=0.0, wave_t=None, clouds=1.0, cx=EX, cy=EY):
    """Renvoie (image RGBA prémultipliée, x0, y0) pour la zone visible du disque."""
    x0 = int(max(0, cx - R - 3))
    x1 = int(min(W, cx + R + 3))
    y0 = int(max(0, cy - R - 3))
    y1 = int(min(H, cy + R + 3))
    ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    x = (xs + .5 - cx) / R
    y = -(ys + .5 - cy) / R
    r2 = x * x + y * y
    inside = r2 < 1.0
    z = np.sqrt(np.clip(1 - r2, 0, 1))
    sp, cp = math.sin(LAT0), math.cos(LAT0)
    lat = np.arcsin(np.clip(z * sp + y * cp, -1, 1))
    lon = LON0 + np.arctan2(x, z * cp - y * sp)
    u = (lon + math.pi) / (2 * math.pi)
    v = (math.pi / 2 - lat) / math.pi
    tex = LAND_HI if R > 1200 else LAND_LO
    m = _sample(tex, u, v) / 255.0
    gy, gx = np.gradient(m)
    grad = np.sqrt(gx * gx + gy * gy) + 1e-4
    sd = (m - 0.5) / grad
    land = np.clip(sd + .5, 0, 1)
    edge = np.clip(1 - np.abs(sd) / 2.2, 0, 1)
    # couleurs
    ocean = carr("#2B86DE") * (1 - boil) + carr("#3B3340") * boil
    ground = carr("#5BBF6B") * (1 - heat) + carr("#7A3A1E") * heat
    ice = np.clip((np.abs(lat) - 1.20) / .03, 0, 1)[..., None] * (1 - heat)
    img = ocean[None, None, :] * (1 - land[..., None]) + ground[None, None, :] * land[..., None]
    img = img * (1 - ice) + carr("#F2FAFF") * ice
    # bord des côtes
    ink = carr("#123B2A") * (1 - heat) + carr("#3A1A10") * heat
    img = img * (1 - edge[..., None] * .9) + ink * edge[..., None] * .9
    if wave_t is not None:
        ang = np.arcsin(np.clip(np.sqrt(r2), 0, 1))
        w_ = np.sin(ang * 44 - wave_t * 14)
        band = np.clip((w_ - .78) * 8, 0, 1) * (1 - land)
        img = img * (1 - band[..., None]) + carr("#EAF8FF") * band[..., None]
    if clouds > 0:
        cl = _sample(CLOUD, u, v) / 255.0
        ca = np.clip((cl - .60) * 16, 0, 1) * .9 * clouds
        cc = carr("#FFFFFF") * (1 - heat) + carr("#8C7E78") * heat
        img = img * (1 - ca[..., None]) + cc * ca[..., None]
    # ombrage franc
    d = (x * -0.45 + y * 0.5 + z * 0.74)
    sh = np.clip((d - 0.12) * 14, 0, 1) * .28 + .72
    img = img * sh[..., None]
    # bord antialiasé
    rr = np.sqrt(r2)
    alpha = np.clip((1 - rr) * R + .5, 0, 1)
    out = np.zeros(img.shape[:2] + (4,), dtype=np.uint8)
    out[..., :3] = np.clip(img * alpha[..., None], 0, 255)
    out[..., 3] = (alpha * 255).astype(np.uint8)
    return skia.Image.fromarray(out, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType), x0, y0


def project(lat, lon, R):
    la, lo = math.radians(lat), math.radians(lon)
    sp, cp = math.sin(LAT0), math.cos(LAT0)
    cosc = sp * math.sin(la) + cp * math.cos(la) * math.cos(lo - LON0)
    x = math.cos(la) * math.sin(lo - LON0)
    y = cp * math.sin(la) - sp * math.cos(la) * math.cos(lo - LON0)
    return EX + R * x, EY - R * y, cosc


_star_arr = np.zeros((H, W, 4), dtype=np.uint8)
_star_arr[..., 3] = 255
_star_arr[..., :3] = (6, 6, 20)
_ss = skia.Surface(_star_arr)
with _ss as _c:
    _rr = random.Random(77)
    for gx, gy, gr, gc in ((850, 400, 620, "#2A1E5C"), (120, 1500, 700, "#123A5C")):
        _p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((gx, gy), gr, [col(gc, .75), col(gc, 0)]))
        _c.drawRect(skia.Rect.MakeWH(W, H), _p)
    for i in range(520):
        _c.drawCircle(_rr.uniform(0, W), _rr.uniform(0, H), _rr.choice((1, 1, 1.4, 1.4, 2, 2.8)), fill(_rr.choice(("#FFFFFF", "#FFE9C7", "#C7E2FF")), _rr.uniform(.35, 1)))
STARS = skia.Image.fromarray(_star_arr.copy(), colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kOpaque_AlphaType)

R_FINAL = 390
_RKEYS = [(T[23], 9000), (T[23] + .35, 4400), (T[24], 4400), (T[24] + .3, 1150), (T[25], 1150), (T[25] + .3, 500), (T[26], 500), (T[27], 420), (T[28], R_FINAL)]


def earth_R(t):
    for (a, ra), (b, rb) in zip(_RKEYS, _RKEYS[1:]):
        if a <= t < b:
            f = eout((t - a) / max(b - a, 1e-3))
            return math.exp(lerp(math.log(ra), math.log(rb), f))
    return R_FINAL


# Voronoï : les fissures sont les futures lignes de fracture
_vr = random.Random(12)
_seeds = []
while len(_seeds) < 26:
    a, rr = _vr.uniform(0, 6.283), math.sqrt(_vr.uniform(0, 1)) * .98
    x, y = rr * math.cos(a), rr * math.sin(a)
    if all((x - p[0]) ** 2 + (y - p[1]) ** 2 > .075 for p in _seeds):
        _seeds.append((x, y))
_far = [(3 * math.cos(i / 16 * 6.283), 3 * math.sin(i / 16 * 6.283)) for i in range(16)]
_vor = Voronoi(np.array(_seeds + _far))
FRAGS = []
for i, s_ in enumerate(_seeds):
    reg = _vor.regions[_vor.point_region[i]]
    if -1 in reg or not reg:
        continue
    pts = [tuple(_vor.vertices[v]) for v in reg]
    pr = random.Random(i + 300)
    FRAGS.append(dict(seed=s_, pts=pts, v=pr.uniform(560, 1500), rot=pr.uniform(-110, 110)))
CRACKS = []
for (a, b) in _vor.ridge_vertices:
    if a < 0 or b < 0:
        continue
    p, q = _vor.vertices[a], _vor.vertices[b]
    if max(np.hypot(*p), np.hypot(*q)) > 2.5:
        continue
    pn, qn = np.array(p), np.array(q)
    # coupe au bord
    if np.hypot(*pn) > 1 and np.hypot(*qn) > 1:
        continue
    for _ in range(2):
        if np.hypot(*pn) > 1:
            lo_, hi_ = 0.0, 1.0
            for _i in range(18):
                m_ = (lo_ + hi_) / 2
                if np.hypot(*(pn + (qn - pn) * m_)) > 1:
                    lo_ = m_
                else:
                    hi_ = m_
            pn = pn + (qn - pn) * hi_
        pn, qn = qn, pn
    CRACKS.append((float(np.hypot(*((pn + qn) / 2))), pn, qn))
CRACKS.sort(key=lambda e: e[0])


def draw_cracks(c, prog, t):
    if prog <= 0:
        return
    count = prog * len(CRACKS)
    path = skia.Path()
    for i, (d, p, q) in enumerate(CRACKS):
        if i >= count:
            break
        f = clamp(count - i)
        e = p + (q - p) * f
        path.moveTo(EX + p[0] * R_FINAL, EY + p[1] * R_FINAL)
        # tracé brisé
        mid = (p + e) / 2 + np.array([q[1] - p[1], p[0] - q[0]]) * .08
        path.lineTo(EX + mid[0] * R_FINAL, EY + mid[1] * R_FINAL)
        path.lineTo(EX + e[0] * R_FINAL, EY + e[1] * R_FINAL)
    glow = 8 + 18 * prog
    c.drawPath(path, line("#FF5A10", glow * 1.5, .75, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, glow)))
    c.drawPath(path, line("#FFB020", 8 + 5 * prog))
    c.drawPath(path, line("#FFF7D0", 3 + 2 * prog))


def draw_moon(c, x, y, r, t, face="angry"):
    shape(c, oval(x - r, y - r, x + r, y + r), "#C9CBD6", 6)
    for dx, dy, rr in ((-.5, -.5, .16), (.45, -.55, .12), (.5, .45, .18), (-.55, .55, .1)):
        c.drawCircle(x + dx * r, y + dy * r, rr * r, fill("#A7A9B8"))
    if face == "angry":
        for sgn in (-1, 1):
            c.drawLine(x + sgn * r * .55, y - r * .32, x + sgn * r * .14, y - r * .12, line(INK, r * .09))
            c.drawCircle(x + sgn * r * .32, y - r * .03, r * .08, fill(INK))
        p = skia.Path()
        p.moveTo(x - r * .3, y + r * .48)
        p.quadTo(x, y + r * .25, x + r * .3, y + r * .48)
        c.drawPath(p, line(INK, r * .08))
    else:
        for sgn in (-1, 1):
            c.drawCircle(x + sgn * r * .32, y - r * .12, r * .2, fill("#FFFFFF"))
            c.drawCircle(x + sgn * r * .32, y - r * .12, r * .2, line(INK, 4))
            c.drawCircle(x + sgn * r * .32, y - r * .1, r * .08, fill(INK))
        c.drawOval(skia.Rect.MakeLTRB(x - r * .16, y + r * .25, x + r * .16, y + r * .62), fill(INK))


def draw_iss(c, x, y, s, rot):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    for dx in (-110, 70):
        for dy in (-62, 22):
            shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(dx, dy, dx + 40, dy + 40)), "#2B5BB5", 3)
    c.drawLine(-120, 0, 120, 0, line("#D4D7E0", 8))
    shape(c, rrect(-40, -17, 40, 17, 9), "#ECEEF4", 4)
    shape(c, rrect(-14, -30, 14, 30, 8), "#ECEEF4", 4)
    c.restore()


CITIES = [("MARSEILLE", 43.3, 5.37, T[23] + .25, T[24]), ("MOSCOU", 55.75, 37.6, T[24] + .22, T[25]), ("NEW YORK", 40.7, -74, T[25] + .22, T[26])]
_ar = random.Random(8)
IMPACTS = []
for i in range(30):
    a = _ar.uniform(0, 6.28)
    rr_ = math.sqrt(_ar.uniform(0.02, .9))
    IMPACTS.append((T[32] + i * 1.55 / 30, rr_ * math.cos(a), rr_ * math.sin(a), _ar.uniform(0, 6.28)))


def draw_terre(c, t, n):
    c.drawImage(STARS, 0, 0)
    R = earth_R(t)
    heat = clamp((t - T[32]) / (T[37] - T[32])) ** 1.5
    boil = clamp((t - T[36]) / 1.0)
    clouds = 1 - clamp((t - T[34]) / .8)
    atm = 1 - clamp((t - T[34]) / 1.0)
    wave = t if T[30] <= t < T[32] else None
    # Lune
    if t >= T[29]:
        tm = t - T[29]
        bang = 0
        if t < T[30]:
            for dt in (0.25, 0.65):
                if t - T[29] >= dt:
                    bang = max(bang, 1 - clamp((t - T[29] - dt) / .18))
        mx = lerp(1250, 895, eout(tm / .35)) - bang * 26
        my = 748 + bang * 16
        # décollage de la Lune pendant le final
        draw_moon(c, mx, my, 86, t, "angry" if t < T[35] else "wow")
    # halo
    if atm > 0:
        pp = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((EX, EY), R * 1.16, [col("#6FC5FF", .9 * atm), col("#6FC5FF", .9 * atm), col("#6FC5FF", 0)], [0, R / (R * 1.16), 1]))
        c.drawCircle(EX, EY, R * 1.16, pp)
    img, x0, y0 = earth_rgba(R, heat, boil, wave, clouds)
    sx, sy = 0, 0
    if t >= T[37]:
        jx, jy = jitter(t, 66)
        sx, sy = jx * 7, jy * 7
    c.drawImage(img, x0 + sx, y0 + sy)
    if R < 1000:
        c.drawCircle(EX + sx, EY + sy, R, line(INK, 4))
    # atmosphère arrachée
    if T[34] <= t < T[35] + .8:
        tt = t - T[34]
        for i in range(70):
            r_ = random.Random(i + 900)
            a = r_.uniform(0, 6.283)
            k = (tt * r_.uniform(.5, 1.1) + r_.uniform(0, .4))
            x = EX + math.cos(a) * R * (1 + k * 1.25)
            y = EY + math.sin(a) * R * (1 + k * 1.25)
            x2 = EX + math.cos(a) * R * (1 + (k + .12) * 1.25)
            y2 = EY + math.sin(a) * R * (1 + (k + .12) * 1.25)
            c.drawLine(x, y, x2, y2, line("#9BDDFF", r_.uniform(4, 13), clamp(1 - k)))
    # villes
    for name, la, lo, a, b in CITIES:
        if a <= t < b:
            x, y, cz = project(la, lo, R)
            s_ = back((t - a) / .15)
            c.drawCircle(x, y, 13 * s_, fill("#FF3B30"))
            c.drawCircle(x, y, 13 * s_, line("#FFFFFF", 4))
            rr = (t - a) * 180
            c.drawCircle(x, y, rr, line("#FF3B30", 5, clamp(1 - rr / 170)))
            yy = y - 28
            xx = clamp(x, 200, W - 200)
            text(c, name, xx, yy, 58 * s_, "#FFFFFF", INK, 12)
    # Michel = point chaud
    pulse = 1 + .2 * math.sin(t * 24)
    if t < T[35]:
        c.drawCircle(EX + sx, EY + sy, 12 * pulse, fill("#FF3B30"))
        c.drawCircle(EX + sx, EY + sy, 12 * pulse, line("#FFFFFF", 4))
    if t >= T[35]:
        s_ = eout((t - T[35]) / .4)
        rad = 240 * s_ * pulse
        pp = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((EX, EY), max(rad, 1), [col("#FFFFFF"), col("#FFE14D", .95), col("#FF8A1F", .5), col("#FF8A1F", 0)], [0, .3, .62, 1]))
        c.drawCircle(EX, EY, max(rad, 1), pp)
        for k in range(14):
            a = k / 14 * 6.283 + t * .9
            c.drawLine(EX + math.cos(a) * rad * .62, EY + math.sin(a) * rad * .62, EX + math.cos(a) * rad * 1.1, EY + math.sin(a) * rad * 1.1, line("#FFE14D", 9, .85 * s_))
    # ondes
    draw_rings(c, EX, EY, t, n, maxr=1250, count=6, speed=620, hue="#FF6A5C" if t < T[35] else "#FFD34D", width=4 + n * .22)
    # ISS
    if T[28] <= t < T[29]:
        f = (t - T[28]) / (T[29] - T[28])
        jx, jy = jitter(t, 70)
        draw_iss(c, lerp(-140, 1220, f) + jx * 5, 740 + jy * 5, 1.15, -8 + jx * 4)
    # TOC TOC
    if T[29] <= t < T[30]:
        for k, dt in enumerate((0.25, 0.65)):
            d = t - T[29] - dt
            if d >= 0:
                c.save()
                c.translate(860 - k * 170, 650 + k * 30)
                s_ = back(d / .14)
                c.scale(s_, s_)
                text(c, "TOC !", 0, 0, 64, "#FF3B30", "#FFFFFF", 12)
                c.restore()
    # astéroïdes
    for ti, ix, iy, ang in IMPACTS:
        d = t - ti
        if -0.16 <= d < 0:
            k = -d / .16
            hx, hy = EX + ix * R_FINAL, EY + iy * R_FINAL
            sx_, sy_ = hx + math.cos(ang) * 1000 * k, hy + math.sin(ang) * 1000 * k
            c.drawLine(sx_, sy_, sx_ + math.cos(ang) * 160, sy_ + math.sin(ang) * 160, line("#FFB020", 10, .8))
            shape(c, oval(sx_ - 15, sy_ - 15, sx_ + 15, sy_ + 15), "#6D6470", 4)
        elif 0 <= d < .55:
            hx, hy = EX + ix * R_FINAL, EY + iy * R_FINAL
            rad = eout(d / .55) * 90
            a = 1 - d / .55
            pp = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((hx, hy), max(rad, 1), [col("#FFFFFF", a), col("#FFB020", a), col("#FF3B10", 0)]))
            c.drawCircle(hx, hy, max(rad, 1), pp)
    # fissures
    prog = clamp((t - T[37]) / (T41 - .4 - T[37]))
    c.save()
    c.translate(sx, sy)
    draw_cracks(c, prog ** 1.2, t)
    c.restore()
    # blanc d'annonce
    if T41 - 0.3 <= t < T41:
        pass


# ---------------------------------------------------------------- BOUM
_EARTH_FINAL = None


def _earth_final():
    global _EARTH_FINAL
    if _EARTH_FINAL is None:
        img, x0, y0 = earth_rgba(R_FINAL, 1.0, 1.0, None, 0.0)
        _EARTH_FINAL = (img, x0, y0)
    return _EARTH_FINAL


_br = random.Random(101)
SPARKS = [(_br.uniform(0, 6.283), _br.uniform(180, 1900), _br.uniform(3, 12), _br.choice(("#FFFFFF", "#FFE14D", "#FF8A1F", "#FF4B10"))) for _ in range(420)]
ROCKS = [(_br.uniform(0, 6.283), _br.uniform(180, 1100), _br.uniform(10, 44), _br.uniform(-200, 200), _br.randint(5, 8)) for _ in range(110)]


def draw_boom(c, t):
    tau = t - T41
    c.drawImage(STARS, 0, 0)
    # anneau plat (façon planète de film)
    if tau < 3.2:
        for k, (spd, cc, sw) in enumerate(((1250, "#FFFFFF", 26), (900, "#FFD34D", 40), (620, "#FF6A1F", 60))):
            rx = tau * spd + 200
            a = clamp(1 - tau / 2.8)
            c.save()
            c.translate(EX, EY)
            c.rotate(-16)
            c.drawOval(skia.Rect.MakeLTRB(-rx, -rx * .17, rx, rx * .17), line(cc, sw * (1 + tau * .5), a))
            c.restore()
    # noyau
    core_a = clamp(1.25 - tau / 2.6)
    if core_a > 0:
        rad = R_FINAL * (0.8 + 2.3 * eout(tau / 1.1))
        pp = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((EX, EY), rad, [col("#FFFFFF", core_a), col("#FFF3B0", core_a), col("#FF8A1F", core_a * .8), col("#FF3B10", core_a * .35), col("#FF3B10", 0)], [0, .25, .5, .78, 1]))
        c.drawCircle(EX, EY, rad, pp)
    # étincelles
    if tau < 3.4:
        for a, v, sz, cc in SPARKS:
            d = v * (1 - math.exp(-1.6 * tau)) / 1.6 + 35 * tau
            x, y = EX + math.cos(a) * (d + 60), EY + math.sin(a) * (d + 60)
            al = clamp(1.25 - tau / 3)
            c.drawLine(x, y, x + math.cos(a) * sz * 2.5, y + math.sin(a) * sz * 2.5, line(cc, sz * .55, al))
    # fragments
    img, x0, y0 = _earth_final()
    for fr in FRAGS:
        sx_, sy_ = fr["seed"]
        norm = math.hypot(sx_, sy_) + .15
        d = fr["v"] * (1 - math.exp(-2.6 * tau)) / 2.6 + 26 * tau
        dx, dy = sx_ / norm * d, sy_ / norm * d
        pts = [(EX + p[0] * R_FINAL, EY + p[1] * R_FINAL) for p in fr["pts"]]
        cx_, cy_ = EX + sx_ * R_FINAL, EY + sy_ * R_FINAL
        c.save()
        c.translate(dx, dy)
        c.translate(cx_, cy_)
        c.rotate(fr["rot"] * (1 - math.exp(-1.2 * tau)) * 1.6)
        c.translate(-cx_, -cy_)
        path = poly(pts)
        disc = skia.Path()
        disc.addCircle(EX, EY, R_FINAL)
        c.clipPath(path, skia.ClipOp.kIntersect, True)
        c.clipPath(disc, skia.ClipOp.kIntersect, True)
        c.drawImage(img, x0, y0)
        c.restore()
        c.save()
        c.translate(dx, dy)
        c.translate(cx_, cy_)
        c.rotate(fr["rot"] * (1 - math.exp(-1.2 * tau)) * 1.6)
        c.translate(-cx_, -cy_)
        res = skia.Op(path, disc, skia.PathOp.kIntersect_PathOp)
        hot = clamp(1 - tau / 2.2)
        target = res if res is not None else path
        c.drawPath(target, line("#FFB020", 9, hot))
        c.drawPath(target, line(INK, 4, 1 - hot))
        c.restore()
    # roches
    for a, v, sz, w, sides in ROCKS:
        d = v * (1 - math.exp(-1.9 * tau)) / 1.9 + 22 * tau
        x, y = EX + math.cos(a) * (d + 120), EY + math.sin(a) * (d + 120)
        c.save()
        c.translate(x, y)
        c.rotate(w * tau)
        r_ = random.Random(int(sz * 100))
        p = poly([(math.cos(i / sides * 6.283) * sz * r_.uniform(.6, 1.1), math.sin(i / sides * 6.283) * sz * r_.uniform(.6, 1.1)) for i in range(sides)])
        shape(c, p, "#5B4048", 3)
        c.restore()
    # Lune éjectée
    if tau < 2.6:
        mx = 895 + 900 * tau * tau * .4 + 200 * tau
        my = 748 - 220 * tau
        c.save()
        c.translate(mx, my)
        c.rotate(tau * 200)
        c.translate(-mx, -my)
        draw_moon(c, mx, my, 86, t, "wow")
        c.restore()
    # flash
    if tau < .45:
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", 1 - tau / .45))
    # fin : le canapé flotte
    e = t - E0
    if e >= -0.4:
        draw_end(c, t, e)


def sun_face(c, x, y, r, t, scared):
    for k in range(16):
        a = k / 16 * 6.283 + t * .4
        c.drawLine(x + math.cos(a) * r * 1.1, y + math.sin(a) * r * 1.1, x + math.cos(a) * r * 1.42, y + math.sin(a) * r * 1.42, line("#FFC531", r * .11))
    pp = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((x, y), r * 2.2, [col("#FFD34D", .55), col("#FFD34D", 0)]))
    c.drawCircle(x, y, r * 2.2, pp)
    shape(c, oval(x - r, y - r, x + r, y + r), "#FFD93B", 6)
    for sgn in (-1, 1):
        c.drawCircle(x + sgn * r * .36, y - r * .16, r * .24, fill("#FFFFFF"))
        c.drawCircle(x + sgn * r * .36, y - r * .16, r * .24, line(INK, 4))
        dx = -r * .08
        c.drawCircle(x + sgn * r * .36 + dx, y - r * .1, r * .1, fill(INK))
    p = skia.Path()
    p.moveTo(x - r * .4, y + r * .46)
    for i in range(1, 7):
        p.lineTo(x - r * .4 + i * r * .133, y + r * .46 + (r * .1 if i % 2 else 0))
    c.drawPath(p, line(INK, r * .07))
    ph = (t * 1.2) % 1
    c.drawCircle(x + r * .88, y - r * .38 + ph * r * .6, r * .1, fill("#7EC8FF"))


def draw_end(c, t, e):
    # dérive
    arrive = eout((e + .4) / 2.0)
    gy = lerp(2500, 1180, arrive) + math.sin(t * .9) * 12
    gx = 540 + math.sin(t * .6) * 10
    rot = lerp(-34, -5, arrive) + math.sin(t * .7) * 3
    # Soleil
    if e >= 3.0:
        s = eout((e - 3.0) / .6)
        sun_face(c, lerp(1300, 860, s), lerp(420, 770, s), 112, t, True)
    lift = 0
    if e >= 3.5:
        lift = eout((e - 3.5) / .5) * 170
    if e >= 5.15:
        lift = 170 * (1 - ein((e - 5.15) / (5.5 - 5.15)))
    mood = "bliss"
    if 1.9 <= e < 3.1:
        mood = "open"
    elif e >= 3.1:
        mood = "wink"
    c.save()
    c.translate(gx, gy)
    c.rotate(rot)
    c.scale(.78, .78)
    c.translate(-570, -1250)
    draw_group(c, t, 13, True, mood, vib=0, hand_lift=lift)
    c.restore()
    if 1.9 <= e < 3.1:
        d = (e - 1.9)
        bubble(c, gx - 250, gy - 400, "mrrp ?", 62, back(d / .2), -4)
    if e >= 3.9:
        d = e - 3.9
        bubble(c, 680, 620, "NON.", 66, back(d / .18), 3)


# ---------------------------------------------------------------- HUD
def heat_col(n):
    stops = [(0, "#59E36A"), (6, "#D7F03A"), (10, "#FFC531"), (13, "#FF7A1F"), (17, "#FF2E2E"), (26, "#FF2EA6"), (35, "#D9C3FF"), (41, "#FFFFFF")]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if a <= n <= b:
            return hexmix(ca, cb, (n - a) / (b - a))
    return "#FFFFFF"


def fmt_mult(n):
    s = str(2 ** n)
    parts = []
    while s:
        parts.append(s[-3:])
        s = s[:-3]
    return " ".join(reversed(parts))


def draw_hud(c, t, n, alpha=1.0):
    if alpha <= 0:
        return
    b = beat_at(t)
    since = t - T.get(n, 0)
    pop = 1 + .16 * (1 - eout(since / .22)) if n > 0 else 1.0
    color = heat_col(n)
    jx, jy = jitter(t, 500)
    sh = clamp((n - 8) / 25) * 7
    c.save()
    c.translate(540 + jx * sh, 262 + jy * sh)
    c.scale(pop, pop)
    pan = rrect(-420, -135, 420, 135, 44)
    c.drawPath(pan, fill("#14121C", alpha * .94))
    c.drawPath(pan, line(color, 8, alpha))
    text(c, "CARESSE N° %d" % n if n else "AVANT LA PREMIÈRE CARESSE", 0, -88, 36, "#C9C6D8", a=alpha)
    text(c, "%d dB" % db(n), 0, 34, 132, color, a=alpha)
    label = "× %s" % fmt_mult(n)
    size = 54
    f = skia.Font(TF, size)
    tot = label + " plus fort"
    while f.measureText(tot) > 770:
        size -= 2
        f = skia.Font(TF, size)
    text(c, tot if n else "volume normal", 0, 106, size, "#FFFFFF", a=alpha)
    c.restore()


SPC = 1.6


def wrap_rich(s, f, maxw):
    """*mot* = surligné. Renvoie lignes de [(mot, surligné)]."""
    words = []
    hl = False
    for w in s.split(" "):
        if w == "|":
            words.append(("|", False))
            continue
        start = w.startswith("*")
        end = w.endswith("*")
        if start:
            hl = True
        words.append((w.replace("*", ""), hl))
        if end:
            hl = False
    lines = [[]]
    sp = f.measureText(" ") * SPC
    cur = 0
    for w, h_ in words:
        if w == "|":
            lines.append([])
            cur = 0
            continue
        ww = f.measureText(w)
        if lines[-1] and cur + sp + ww > maxw:
            lines.append([])
            cur = 0
        lines[-1].append((w, h_))
        cur += ww + (sp if cur else 0)
    return lines


def draw_caption(c, t):
    b = beat_at(t)
    if not b["cap"]:
        return
    d = t - b["cap_start"]
    s = back(d / .17)
    size = 76
    f = skia.Font(TF, size)
    lines = wrap_rich(b["cap"], f, 950)
    lh = size * 1.16
    top = 415
    hgt = lh * len(lines) + (58 if b["sub"] else 0)
    c.save()
    c.translate(540, top + hgt / 2)
    c.scale(s, s)
    c.translate(-540, -(top + hgt / 2))
    y = top + size * .86
    sp = f.measureText(" ") * SPC
    for ln in lines:
        wd = sum(f.measureText(w) for w, _ in ln) + sp * (len(ln) - 1)
        x = 540 - wd / 2
        for w, h_ in ln:
            c.drawString(w, x, y, f, line(INK, 15))
            c.drawString(w, x, y, f, fill("#FFE14D" if h_ else "#FFFFFF"))
            x += f.measureText(w) + sp
        y += lh
    if b["sub"]:
        text(c, b["sub"], 540, y + 4, 46, "#FFFFFF", INK, 9)
    c.restore()


STICKERS = {1: "📚", 2: "🥶", 5: "🧹", 7: "\U0001F3CD", 9: "🪚", 10: "😖", 12: "\u2708"}
_FE = skia.Font(TF_EMOJI, 110)


def draw_sticker(c, t, n):
    if n not in STICKERS or t < T[n] or t >= T[n] + beat_at(t)["dur"]:
        return
    d = t - T[n]
    s = back(d / .16)
    c.save()
    c.translate(600, 860)
    c.rotate(-6)
    c.scale(s, s)
    c.drawCircle(0, 0, 86, fill("#FFFFFF"))
    c.drawCircle(0, 0, 86, line(INK, 7))
    e = STICKERS[n]
    w = _FE.measureText(e)
    c.drawString(e, -w / 2, 40, _FE, fill("#000000"))
    c.restore()


def draw_pip(c, t, n, big=0.0):
    px, py, r = 190, 1420, lerp(142, 165, big)
    t0 = T[14]
    if t < t0:
        return
    s = back((t - t0) / .25)
    r *= s
    clip = skia.Path()
    clip.addCircle(px, py, r)
    # fond selon le lieu
    c.save()
    c.clipPath(clip, skia.ClipOp.kIntersect, True)
    if t < T[17]:
        bg = "#F7DDAE"
    elif t < T[23]:
        bg = "#2E2A5E"
    else:
        bg = "#0A0A22"
    c.drawCircle(px, py, r, fill(bg))
    if t >= T[23]:
        rr = random.Random(5)
        for i in range(24):
            c.drawCircle(px + rr.uniform(-r, r), py + rr.uniform(-r, r), rr.uniform(1, 2.6), fill("#FFFFFF", .85))
    suit = t >= T[27]
    k = r / 142 * .36
    c.translate(px, py + 36 * r / 142)
    c.scale(k, k)
    c.translate(-540, -1200)
    draw_group(c, t, n, suit, "bliss", vib=18)
    c.restore()
    c.drawCircle(px, py, r, line("#FFFFFF", 9))
    c.drawCircle(px, py, r + 4, line(INK, 3))
    # étiquette
    c.save()
    c.translate(px, py - r + 2)
    c.drawPath(rrect(-86, -22, 86, 24, 12), fill("#E02B2B"))
    c.drawPath(rrect(-86, -22, 86, 24, 12), line("#FFFFFF", 4))
    c.drawCircle(-64, 1, 8, fill("#FFFFFF", .6 + .4 * math.sin(t * 8)))
    text(c, "MICHEL", 8, 14, 34, "#FFFFFF")
    c.restore()


# ---------------------------------------------------------------- image complète
def scene_name(t):
    for name, a, b in SCENES:
        if a <= t < b:
            return name, a
    return "carton", CARD


def draw_card(c, t):
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#000000"))
    d = t - CARD
    if d < .1:
        return
    s = back((d - .1) / .22)
    c.save()
    c.translate(540, 830)
    c.scale(s, s)
    text(c, "À SUIVRE :", 0, 0, 88, "#FFFFFF", None)
    text(c, "LE SOLEIL", 0, 130, 142, "#FFD93B", None)
    c.restore()
    c.drawString
    a = clamp((d - .35) / .25)
    text(c, "+10 dB = 2× plus fort à l'oreille · dB à 1 m de Michel", 540, 1120, 37, "#A9A6BC", a=a)
    text(c, "Physique très approximative. Michel va bien.", 540, 1172, 37, "#A9A6BC", a=a)


def draw_frame(c, t):
    n = level(t)
    name, t0 = scene_name(t)
    if name == "carton":
        draw_card(c, t)
        return
    since = t - T.get(n, 0)
    # tremblement
    base = clamp(n / 13) ** 2 * 7 + (clamp((n - 13) / 28) * 10)
    imp = (1 - clamp(since / .22)) * clamp(n / 9) * 22
    if name == "boum":
        tau = t - T41
        base = 0
        imp = 60 * math.exp(-tau * 1.7) if tau < 3 else 0
    if T41 - .55 <= t < T41:
        base = imp = 0     # silence avant le boum
    jx, jy = jitter(t, 1)
    c.save()
    amp = base + imp
    zz = 1 + 2.2 * amp / W
    c.translate(540, 960)
    c.scale(zz, zz)
    c.translate(-540 + jx * amp, -960 + jy * amp)
    # zoom d'entrée de scène (dé-zoom)
    d = t - t0
    if name in ("rue", "paris", "terre") and d < .32:
        z = lerp(1.7, 1.0, eout(d / .32))
        c.translate(540, 1100)
        c.scale(z, z)
        c.translate(-540, -1100)
    if name == "salon":
        draw_salon(c, t, n)
    elif name == "rue":
        draw_rue(c, t, n)
    elif name == "paris":
        draw_paris(c, t, n)
    elif name == "terre":
        draw_terre(c, t, n)
    else:
        draw_boom(c, t)
    c.restore()
    if name in ("rue", "paris", "terre") and d < .16:
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", 1 - d / .16))
    if name == "salon":
        draw_sticker(c, t, n)
    if name in ("rue", "paris", "terre"):
        big = clamp((t - T[37]) / .3) if t >= T[37] else 0
        draw_pip(c, t, n, big)
    # HUD
    hud_a = 1.0
    if t >= E0 + 2.0:
        hud_a = 1 - clamp((t - E0 - 2.0) / .5)
    draw_hud(c, t, n, hud_a)
    # légende
    if name == "boum" and t - T41 > 1.5 and t < E0:
        s_ = back((t - T41 - 1.5) / .2)
        c.save()
        c.translate(540, 490)
        c.scale(s_, s_)
        text(c, "41 caresses.", 0, 26, 96, "#FFE14D", INK, 20)
        c.restore()
    else:
        draw_caption(c, t)


def render_png(t, path):
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    s = skia.Surface(arr)
    with s as c:
        draw_frame(c, t)
    Image.fromarray(arr[..., :3]).save(path)
