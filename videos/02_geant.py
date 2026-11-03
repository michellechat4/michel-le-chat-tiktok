"""Michel double de taille chaque jour — dézoom continu, tout est en mètres."""
import math, random, sys, os, subprocess
import numpy as np
import skia
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "moteur"))
import art
from art import (fill, line, col, hexmix, poly, rrect, oval, shape, text, jitter, clamp, lerp, eout, ein, back,
                 draw_cat, draw_gerard, draw_couch, draw_eiffel, draw_iss, draw_moon, bubble, earth_rgba, STARS,
                 wrap_rich, TF, TF_EMOJI, INK, W, H, FPS)

# ---------------------------------------------------------------- chronologie
# (jour, durée, légende, Gérard dit, phase)
RAW = [
    (1, 2.4, "CE CHAT DOUBLE DE TAILLE | *CHAQUE JOUR.*", None, ""),
    (1, 2.1, "Voici *Michel.* 40 cm, 4 kg. | Aucun problème.", None, ""),
    (2, 1.2, "Il ne rentre plus | dans son panier.", None, ""),
    (3, 1.2, "Il prend tout le canapé.", "Michel ?", ""),
    (4, 1.3, "Il passe la tête | par le plafond.", "MICHEL !", ""),
    (5, 1.2, "Le toit n'a pas tenu.", "MON TOIT !", ""),
    (6, 1.4, "Gérard appelle | son assurance.", "ALLÔ ?", ""),
    (7, 1.0, "Plus haut que les immeubles.", None, ""),
    (8, 1.2, "Sa gamelle : une piscine.", None, ""),
    (9, 1.1, "La SPA ne répond plus.", "ALLÔ ?!", ""),
    (10, 1.4, "Croquettes livrées | à la pelleteuse.", None, ""),
    (11, 1.7, "La tour Eiffel ? | *Un griffoir.*", None, ""),
    (12, 0.6, None, None, ""),
    (13, 1.1, "La tête dans les nuages.", "DESCENDS !", ""),
    (14, 0.5, None, None, ""),
    (15, 1.2, "Plus haut que le mont Blanc.", None, ""),
    (16, 1.5, "Les avions l'évitent. | *Mal.*", "PARDON !", ""),
    (17, 0.5, None, None, ""),
    (18, 0.5, None, None, ""),
    (19, 1.4, "Sa tête est *dans l'espace.*", "REVIENS !", ""),
    (20, 1.4, "Il respire quand même. | Personne ne sait comment.", None, ""),
    (21, 1.6, "L'ISS passe. | Il essaie de l'attraper.", "LÂCHE ÇA !", ""),
    (22, 0.5, None, None, ""),
    (23, 1.3, "La France : *son coussin.*", None, ""),
    (24, 1.5, "Le Sahara : *sa litière.*", "PAS LÀ !", ""),
    (25, 0.6, None, None, ""),
    (26, 1.7, "Michel a la taille | *de la Terre.*", "MICHEL...", ""),
    (27, 0.7, None, None, ""),
    (28, 2.1, "Il pèse plus lourd qu'elle. | *La Terre lui tourne autour.*", None, ""),
    (29, 1.4, "Elle lui sert de pelote.", None, ""),
    (30, 1.6, "Gérard continue | de le nourrir.", "TIENS.", ""),
    (31, 2.3, "Là, il trouve une table. | Personne ne sait pourquoi.", None, "table"),
    (31, 1.6, "Il regarde Gérard.", "Michel. Non.", "stare"),
    (31, 2.8, "Il pousse la Lune. | *Lentement.*", None, "pushm"),
    (31, 0.8, None, None, "fall"),
    (31, 1.5, "Il regarde la Terre.", "MICHEL. NON.", "look"),
    (32, 1.9, "Il recommence.", None, "pushe"),
]
CARD_DUR = 2.5
BEATS = []
_t = 0.0
for d_, dur, cap, ger, ph in RAW:
    BEATS.append(dict(d=d_, start=_t, dur=dur, cap=cap, ger=ger, ph=ph))
    _t += dur
CARD = _t
END = CARD + CARD_DUR
T = {}
PH = {}
for b in BEATS:
    T.setdefault(b["d"], b["start"])
    if b["ph"]:
        PH[b["ph"]] = b["start"]
RE = 6371e3
GRAD = {}


def beat_at(t):
    cur = BEATS[0]
    for b in BEATS:
        if b["start"] <= t:
            cur = b
        else:
            break
    return cur


def Lm(d):
    return 0.4 * 2 ** (d - 1)


def Hc(d):
    return 800 if d <= 23 else 720 if d == 24 else 620 if d == 25 else 540


def Zd(d):
    d = min(d, 31)
    return 385.0 if d <= 3 else Hc(d) / Lm(d)


def gyd(d):
    return 1560 if d <= 23 else 1440 if d == 24 else 1290 if d == 25 else 1150


def cxd(d):
    return 330 if d <= 2 else 410 if d == 3 else 480 if d <= 23 else 540


def cam(t):
    """Renvoie L(m), Z(px/m), gy, cx, jour."""
    b = beat_at(t)
    d = b["d"]
    if d <= 1:
        return Lm(1), Zd(1), gyd(1), cxd(1), 1
    if d >= 31:
        tb = PH["table"]
        f = eout((t - tb) / .6)
        return Lm(31), Zd(31), lerp(gyd(31), 1160, f), lerp(540, 320, f), d
    s = t - T[d]
    fe = eout(s / .34)
    fb = back(s / .34)
    a, c_ = Lm(d - 1), Lm(d)
    zL = a * (c_ / a) ** fb
    z = math.exp(lerp(math.log(Zd(d - 1)), math.log(Zd(d)), fe))
    return zL, z, lerp(gyd(d - 1), gyd(d), fe), lerp(cxd(d - 1), cxd(d), fe), d


def fmt_int(n):
    s = str(int(round(n)))
    out = []
    while s:
        out.append(s[-3:])
        s = s[:-3]
    return " ".join(reversed(out))


def fr1(x):
    return ("%.1f" % x).replace(".", ",")


def fmt_size(d):
    L = Lm(d)
    if L < 1:
        return "%d cm" % round(L * 100)
    if L < 20:
        return fr1(L) + " m"
    if L < 1000:
        return "%d m" % round(L)
    if L < 10000:
        return fr1(L / 1000) + " km"
    return fmt_int(L / 1000) + " km"


def fmt_mass(d):
    m = 4.0 * 8 ** (d - 1)
    if m < 2000:
        return "%d kg" % round(m), None
    t_ = m / 1000
    if t_ < 1e6:
        return fmt_int(t_) + " tonnes", None
    if t_ < 1e9:
        v = t_ / 1e6
        return (fr1(v) if v < 10 else "%d" % round(v)) + " millions de tonnes", None
    if t_ < 1e12:
        v = t_ / 1e9
        return (fr1(v) if v < 10 else "%d" % round(v)) + " milliards de tonnes", None
    e = int(math.floor(math.log10(m)))
    return fr1(m / 10 ** e) + " × 10", e


# ---------------------------------------------------------------- décor (généré une fois)
_r = random.Random(42)
NEIGH = []
for sgn in (-1, 1):
    x = 10.0 if sgn > 0 else -9.0
    for i in range(7):
        w = _r.uniform(7, 10)
        NEIGH.append((x if sgn > 0 else x - w, w, _r.uniform(5, 7), _r.choice(("#E58B7B", "#8FC8A2", "#CDB7E8", "#F0D07A", "#9CC7E8")), _r.choice(("#7A3B3B", "#3B5E4A", "#4F3F7A", "#7A5F2C"))))
        x += sgn * (w + _r.uniform(2, 4))
TOWN = []
for sgn in (-1, 1):
    x = 15.0
    while x < 3200:
        w = _r.uniform(14, 34) * (1 + x / 1500)
        h = _r.uniform(15, 26) if x < 900 else _r.uniform(10, 18)
        TOWN.append((sgn * x if sgn > 0 else -x - w, w, h, _r.choice(("#D9C7A8", "#C9B898", "#E3D5BC", "#BFAE92")), _r.random()))
        x += w + _r.uniform(0, 4)
TREES = [(_r.choice((-1, 1)) * _r.uniform(6, 80), _r.uniform(5, 9)) for _ in range(14)]
HILLS = [(-9000, 11000, 800, "#7FA97A"), (6500, 9000, 600, "#6E9E74"), (-26000, 26000, 1500, "#8AA9B0"), (24000, 24000, 1300, "#8AA9B0")]
CLOUDS = []
for i in range(46):
    alt = _r.uniform(1100, 3400)
    CLOUDS.append((_r.uniform(-16000, 16000), alt, _r.uniform(900, 2600), i % 3 == 0))


def draw_cloud(c, x, y, w, a):
    for dx, dy, rr in ((-.32, 0, .22), (0, -.12, .3), (.32, 0, .24), (-.1, .08, .26), (.18, .08, .24)):
        c.drawCircle(x + dx * w, y + dy * w * .6, rr * w * .75, fill("#FFFFFF", a))


def draw_plane(c, x, y, s, rot):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    shape(c, poly([(-62, -8), (-86, -50), (-66, -50), (-36, -10)]), "#E84B4B", 4)
    shape(c, rrect(-82, -18, 90, 18, 17), "#F7F8FB", 5)
    c.drawRect(skia.Rect.MakeLTRB(-78, 2, 84, 8), fill("#E84B4B"))
    shape(c, poly([(-10, 4), (34, 4), (-16, 52), (-34, 52)]), "#C9CDD8", 4)
    for wx in (-40, -20, 0, 20, 40):
        c.drawCircle(wx, -6, 4, fill("#3F6FD8"))
    c.drawCircle(70, -5, 7, fill("#3F6FD8"))
    c.restore()


def draw_paw(c, x0, y0, x1, y1, w, claws=False):
    """Patte de Michel : du corps vers (x1, y1)."""
    p = skia.Path()
    p.moveTo(x0, y0)
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2 - abs(x1 - x0) * .08
    p.quadTo(mx, my, x1, y1)
    c.drawPath(p, line(INK, w + 14))
    c.drawPath(p, line("#F49A3A", w))
    c.drawCircle(x1, y1, w * .72, fill("#FFE1B0"))
    c.drawCircle(x1, y1, w * .72, line(INK, 7))
    if claws:
        a = math.atan2(y1 - y0, x1 - x0)
        for k in (-1, 0, 1):
            aa = a + k * .55
            c.drawLine(x1 + math.cos(aa) * w * .7, y1 + math.sin(aa) * w * .7, x1 + math.cos(aa) * w * 1.15, y1 + math.sin(aa) * w * 1.15, line("#FFFFFF", 7))


# ---------------------------------------------------------------- monde
def sky(c, t, Z, gy, cx, R, ghost=False):
    c.drawImage(STARS, 0, 0)
    thick = Z * 1e5
    cols = [col("#D3F1FF"), col("#5CB8F2"), col("#1B3A7A", .85), col("#1B3A7A", 0)]
    if R > 60000:
        pos = [0, .22, .62, 1]
        if thick > 4000:
            c.drawRect(skia.Rect.MakeWH(W, H), fill("#7CC7F5"))
            pp = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, gy), (0, 0)], [col("#D3F1FF"), col("#7CC7F5")]))
            c.drawRect(skia.Rect.MakeWH(W, H), pp)
        else:
            pp = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, gy), (0, gy - thick)], cols, pos))
            c.drawRect(skia.Rect.MakeLTRB(0, 0, W, gy + 2), pp)
    elif not ghost:
        a_ = max(thick, R * .05)
        o = R + a_
        k = R / o
        pp = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((cx, gy + R), o, [col("#D3F1FF"), col("#D3F1FF"), col("#5CB8F2"), col("#1B3A7A", .85), col("#1B3A7A", 0)],
                                                                             [0, k, k + (1 - k) * .22, k + (1 - k) * .62, 1]))
        c.drawCircle(cx, gy + R, o, pp)


def far_land(c, t, d, Z, gy, cx):
    for x, w, h, cc in HILLS:
        ph = h * Z
        if ph < 3 or ph > 2500:
            continue
        X = cx + x * Z
        Wd = w * Z
        if X + Wd / 2 < -50 or X - Wd / 2 > W + 50:
            continue
        p = skia.Path()
        p.moveTo(X - Wd / 2, gy)
        p.cubicTo(X - Wd / 4, gy - ph * .2, X - Wd / 6, gy - ph, X, gy - ph)
        p.cubicTo(X + Wd / 6, gy - ph, X + Wd / 4, gy - ph * .2, X + Wd / 2, gy)
        p.close()
        c.drawPath(p, fill(cc))
    # mont Blanc
    h = 4807 * Z
    if 12 < h < 3000:
        X = cx + 4300 * Z
        Wd = 7600 * Z
        pts = [(X - Wd / 2, gy), (X - Wd * .28, gy - h * .42), (X - Wd * .16, gy - h * .38), (X, gy - h), (X + Wd * .13, gy - h * .55), (X + Wd * .27, gy - h * .44), (X + Wd / 2, gy)]
        shape(c, poly(pts), "#7E90A8", 5)
        snow = [(X, gy - h), (X + Wd * .10, gy - h * .64), (X + Wd * .03, gy - h * .68), (X - Wd * .02, gy - h * .58), (X - Wd * .08, gy - h * .68), (X - Wd * .13, gy - h * .63)]
        c.drawPath(poly(snow), fill("#FFFFFF"))
        c.drawPath(poly(snow), line(INK, 3))


def town(c, t, d, Z, gy, cx, shake):
    # arbres
    for x, h in TREES:
        ph = h * Z
        if ph < 4:
            continue
        X = cx + x * Z
        if -80 < X < W + 80:
            c.drawRect(skia.Rect.MakeLTRB(X - ph * .05, gy - ph * .4, X + ph * .05, gy), fill("#7B5A3A"))
            c.drawCircle(X, gy - ph * .62, ph * .36, fill("#4FA863"))
            if ph > 40:
                c.drawCircle(X, gy - ph * .62, ph * .36, line(INK, 4))
    # immeubles
    for x, w, h, cc, rr in TOWN:
        ph = h * Z
        if ph < 2:
            continue
        X0, X1 = cx + x * Z, cx + (x + w) * Z
        if X1 < -5 or X0 > W + 5:
            continue
        c.drawRect(skia.Rect.MakeLTRB(X0, gy - ph, X1, gy + 1), fill(cc))
        c.drawRect(skia.Rect.MakeLTRB(X0, gy - ph - ph * .1, X1, gy - ph), fill("#5F6880"))
        if ph > 40:
            c.drawRect(skia.Rect.MakeLTRB(X0, gy - ph, X1, gy + 1), line(INK, 3))
            nx, ny = max(int((X1 - X0) / 26), 1), max(int(ph / 34), 1)
            for i in range(nx):
                for j in range(ny):
                    xx = X0 + (i + .25) * (X1 - X0) / nx
                    yy = gy - ph + (j + .25) * ph / ny
                    c.drawRect(skia.Rect.MakeLTRB(xx, yy, xx + .5 * (X1 - X0) / nx, yy + .5 * ph / ny), fill("#4C5A78"))
    # voisins
    for x, w, h, cc, rc in NEIGH:
        ph = h * Z
        if ph < 2:
            continue
        X0, X1 = cx + x * Z, cx + (x + w) * Z
        if X1 < -60 or X0 > W + 60:
            continue
        sw = 5 if ph > 30 else 0
        shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(X0, gy - ph, X1, gy + 1)), cc, sw)
        shape(c, poly([(X0 - ph * .06, gy - ph), ((X0 + X1) / 2, gy - ph * 1.45), (X1 + ph * .06, gy - ph)]), rc, sw)
        if ph > 40:
            for fx in (.18, .6):
                r = skia.Rect.MakeLTRB(X0 + (X1 - X0) * fx, gy - ph * .72, X0 + (X1 - X0) * (fx + .22), gy - ph * .3)
                c.drawRect(r, fill("#CDEBFF"))
                c.drawRect(r, line(INK, 3))


def house(c, t, d, Z, gy, cx):
    """Coupe de la maison de Gérard : x de -3,2 à 6,3 m."""
    x0, x1 = cx - 3.2 * Z, cx + 6.3 * Z
    if x1 - x0 < 6:
        return
    H1, H2 = 2.6 * Z, 5.4 * Z
    sw = max(3, min(10, Z * .05))
    if d <= 5:
        # étage
        c.drawRect(skia.Rect.MakeLTRB(x0, gy - H2, x1, gy - H1), fill("#BFD9EE"))
        # rez-de-chaussée
        c.drawRect(skia.Rect.MakeLTRB(x0, gy - H1, x1, gy), fill("#F7DDAE"))
        step = Z * .32
        if step > 14:
            xs = x0 % (step * 2) - step * 2
            while xs < x1:
                if xs > x0 - step and xs < W:
                    c.drawRect(skia.Rect.MakeLTRB(xs, gy - H1, xs + step, gy), fill("#F2D29C", .55))
                xs += step * 2
        # fenêtre
        wx0, wx1 = cx - .7 * Z, cx + .29 * Z
        wy0, wy1 = gy - 2.25 * Z, gy - 1.45 * Z
        rc = skia.Rect.MakeLTRB(wx0, wy0, wx1, wy1)
        c.drawRect(rc, fill("#9BDCFA"))
        c.drawRect(rc, line(INK, sw + 6))
        c.drawRect(rc, line("#FFFFFF", sw + 1))
        c.drawLine((wx0 + wx1) / 2, wy0, (wx0 + wx1) / 2, wy1, line("#FFFFFF", sw))
        c.drawLine(wx0, (wy0 + wy1) / 2, wx1, (wy0 + wy1) / 2, line("#FFFFFF", sw))
        # tableau
        fx, fy = cx + 1.36 * Z, gy - 1.9 * Z
        s_ = Z * .24
        shape(c, rrect(fx - s_, fy - s_ * .7, fx + s_, fy + s_ * .7, 5), "#7B4A2B", sw)
        c.drawRect(skia.Rect.MakeLTRB(fx - s_ * .85, fy - s_ * .55, fx + s_ * .85, fy + s_ * .55), fill("#BFE6FF"))
        c.drawPath(poly([(fx - s_ * .85, fy + s_ * .55), (fx - s_ * .2, fy - s_ * .25), (fx + s_ * .4, fy + s_ * .55)]), fill("#6F8FA8"))
        # plancher
        c.drawRect(skia.Rect.MakeLTRB(x0, gy - H1 - sw, x1, gy - H1 + sw), fill("#7B6A5A"))
        c.drawRect(skia.Rect.MakeLTRB(x0, gy - H1 - sw, x1, gy - H1 + sw), line(INK, 3))
        # murs extérieurs
        for xx in (x0, x1):
            c.drawLine(xx, gy, xx, gy - H2, line(INK, sw + 8))
            c.drawLine(xx, gy, xx, gy - H2, line("#FFF5E0", sw + 1))
        # toit
        if d <= 4:
            shape(c, poly([(x0 - Z * .5, gy - H2), ((x0 + x1) / 2, gy - 8 * Z), (x1 + Z * .5, gy - H2)]), "#B24B36", sw)
    else:
        # ruines
        for (a, b, hh) in ((0, .1, .9), (.1, .2, .55), (.82, .92, .7), (.92, 1, 1.0), (.3, .4, .22), (.5, .6, .16), (.68, .78, .3)):
            c.drawRect(skia.Rect.MakeLTRB(lerp(x0, x1, a), gy - H1 * hh, lerp(x0, x1, b), gy), fill("#D9C7A8"))
            if x1 - x0 > 40:
                c.drawRect(skia.Rect.MakeLTRB(lerp(x0, x1, a), gy - H1 * hh, lerp(x0, x1, b), gy), line(INK, 3))


def debris(c, t, d, Z, gy, cx, L):
    # plâtre du plafond (jour 4)
    if T[4] <= t < T[5]:
        tt = t - T[4]
        for i in range(42):
            r = random.Random(i + 7)
            a = r.uniform(-3.0, -.15)
            v = r.uniform(180, 720)
            x = cx + r.uniform(-260, 260) + math.cos(a) * v * tt
            y = gy - 2.6 * Z + math.sin(a) * v * tt + 1500 * tt * tt
            s = r.uniform(8, 30)
            c.save()
            c.translate(x, y)
            c.rotate(r.uniform(0, 360) + tt * r.uniform(-500, 500))
            shape(c, poly([(-s, -s * .5), (s * .8, -s * .7), (s, s * .5), (-s * .4, s * .7)]), r.choice(("#F7DDAE", "#FFF5E0", "#BFD9EE", "#7B6A5A")), 3)
            c.restore()
    # toit qui s'envole (jour 5)
    if T[5] <= t < T[6] + .8:
        tt = t - T[5]
        x0, x1 = cx - 3.2 * Z, cx + 6.3 * Z
        c.save()
        c.translate((x0 + x1) / 2 + 500 * tt, gy - 8 * Z - 150 - 900 * tt - 1100 * tt * tt)
        c.rotate(tt * 180)
        wr = (x1 - x0) / 2 + Z * .5
        hr = (8 - 5.4) * Z
        shape(c, poly([(-wr, hr * .5), (0, -hr * .5), (wr, hr * .5)]), "#B24B36", 7)
        c.restore()


def gerard_world(c, t, d, Z, gy, cx, L, ger_text):
    k = Z / 350
    wx = max(1.23, .62 * L if d >= 3 else 1.23)
    stage = 0 if d <= 2 else 1 if d == 3 else 2 if d <= 5 else 3
    X = cx + wx * Z
    hpx = 612 * k
    if hpx > 3:
        c.save()
        c.translate(X - 790 * k, gy - 1490 * k)
        c.scale(k, k)
        draw_gerard(c, stage, t, False, 2 if d >= 4 else 0)
        c.restore()
    else:
        c.drawCircle(X, gy - 2, 3, fill("#3F6FD8"))
    if d >= 6 and d <= 12 and d != 11:
        # étiquette
        y_ = gy - max(hpx, 0) - 26
        c.drawLine(X, y_ - 68, X, y_ - 6, line(INK, 12))
        c.drawLine(X, y_ - 68, X, y_ - 6, line("#FFE14D", 6))
        c.drawPath(poly([(X - 18, y_ - 22), (X + 18, y_ - 22), (X, y_ + 2)]), fill("#FFE14D"))
        c.drawPath(poly([(X - 18, y_ - 22), (X + 18, y_ - 22), (X, y_ + 2)]), line(INK, 4))
        text(c, "GÉRARD", min(X, W - 130), y_ - 84, 44, "#FFFFFF", INK, 9)
    if ger_text and d <= 12:
        anchor_y = gy - max(hpx, 0) - (205 if d >= 6 else 50)
        bx = clamp(X - 80, 170, W - 180)
        s_ = back((t - beat_at(t)["start"]) / .16)
        bubble(c, bx, anchor_y, ger_text, 48, s_, 2)


def pip(c, t, d, ger_text):
    t0 = T[13]
    if t < t0:
        return
    px, py = 190, 1450
    big = 1.0
    r = 142 * back((t - t0) / .25)
    clip = skia.Path()
    clip.addCircle(px, py, r)
    c.save()
    c.clipPath(clip, skia.ClipOp.kIntersect, True)
    bg = "#BFE6FF" if d < 17 else hexmix("#BFE6FF", "#0A0A22", clamp((d - 17) / 3))
    c.drawCircle(px, py, r, fill(bg))
    if d >= 19:
        rr = random.Random(5)
        for i in range(22):
            c.drawCircle(px + rr.uniform(-r, r), py + rr.uniform(-r, r), rr.uniform(1, 2.6), fill("#FFFFFF", .85))
    suit = d >= 19
    k = r / 142 * .78
    c.translate(px, py + 18 * r / 142)
    c.scale(k, k)
    c.translate(-790, -1010)
    st = 2 if d < 16 else 3
    if d >= 31:
        st = 3 if beat_at(t)["ph"] == "pushm" else 2
    draw_gerard(c, st, t, suit, 3)
    c.restore()
    c.drawCircle(px, py, r, line("#FFFFFF", 9))
    c.drawCircle(px, py, r + 4, line(INK, 3))
    c.save()
    c.translate(px, py - r + 2)
    c.drawPath(rrect(-92, -22, 92, 24, 12), fill("#E02B2B"))
    c.drawPath(rrect(-92, -22, 92, 24, 12), line("#FFFFFF", 4))
    text(c, "GÉRARD", 0, 14, 34, "#FFFFFF")
    c.restore()
    if ger_text:
        s_ = back((t - beat_at(t)["start"]) / .16)
        f = skia.Font(TF, 50)
        w_ = f.measureText(ger_text)
        bubble(c, max(px + 150 + w_ / 2, 420), py + 72, ger_text, 50, s_, -2, tail=False)


def earth_at(c, cx_, cy_, R, heat=0, clouds=1.0):
    img, x0, y0 = earth_rgba(R, heat, 0, None, clouds, cx_, cy_)
    c.drawImage(img, x0, y0)
    if R < 2000:
        c.drawCircle(cx_, cy_, R, line(INK, 3 if R < 200 else 4))


TABLE_EDGE = 930


def draw_table(c, y, a=1.0):
    c.save()
    # pied
    c.drawRect(skia.Rect.MakeLTRB(TABLE_EDGE - 90, y + 40, TABLE_EDGE - 40, H + 40), fill("#7B4A2B"))
    c.drawRect(skia.Rect.MakeLTRB(TABLE_EDGE - 90, y + 40, TABLE_EDGE - 40, H + 40), line(INK, 5))
    # plateau
    p = rrect(-60, y, TABLE_EDGE, y + 46, 8)
    c.drawPath(p, fill("#B7773F"))
    c.drawPath(p, line(INK, 6))
    for xx in range(60, TABLE_EDGE, 190):
        c.drawLine(xx, y + 12, xx + 90, y + 12, line("#8E5A2E", 3))
        c.drawLine(xx + 70, y + 30, xx + 150, y + 30, line("#8E5A2E", 3))
    c.restore()


def scene(c, t):
    L, Z, gy, cx, d = cam(t)
    b = beat_at(t)
    ph = b["ph"]
    R = RE * Z
    # secousse à chaque jour
    since = t - T[d]
    final = d >= 31
    amp = 0 if final else (1 - clamp(since / .22)) * clamp(d / 8) * 14
    jx, jy = jitter(t, 2)
    zz = 1 + 2.2 * amp / W
    c.save()
    c.translate(540, 960)
    c.scale(zz, zz)
    c.translate(-540 + jx * amp, -960 + jy * amp)

    sky(c, t, Z, gy, cx, R, d >= 28)
    # nuages derrière
    if 0.006 < Z < 3:
        for x, alt, w, front in CLOUDS:
            if front:
                continue
            pw = w * Z
            a_ = clamp((pw - 16) / 60) * clamp((2600 - pw) / 1000)
            if a_ > 0:
                draw_cloud(c, cx + x * Z, gy - alt * Z, pw, a_ * .9)
    # sol
    art.LAT0, art.LON0 = math.radians(48.85 - 90), math.radians(2.35)
    if not final and d < 28:
        if R > 60000:
            far_land(c, t, d, Z, gy, cx)
            c.drawRect(skia.Rect.MakeLTRB(0, gy, W, H + 80), fill("#5BBF6B"))
            for yy_, hh_ in ((60, 34), (150, 56), (270, 90)):
                c.drawRect(skia.Rect.MakeLTRB(0, gy + yy_, W, gy + yy_ + hh_), fill("#52B062"))
            if Z > .4:
                roadh = max(6 * Z, 8)
                c.drawRect(skia.Rect.MakeLTRB(0, gy, W, gy + roadh), fill("#8E91A0"))
        else:
            cl_ = clamp((3400 - R) / 1500)
            earth_at(c, cx, gy + R, R, 0, cl_)
    if Z > 0.08 and R > 60000:
        town(c, t, d, Z, gy, cx, 0)
    if R > 60000:
        house(c, t, d, Z, gy, cx)
    if d <= 5:
        # sol intérieur
        x0, x1 = cx - 3.2 * Z, cx + 6.3 * Z
        c.drawRect(skia.Rect.MakeLTRB(x0, gy, x1, H + 80), fill("#B47B4C"))
        for j in range(1, 5):
            yy = gy + j * .24 * Z
            if yy < H:
                c.drawLine(x0, yy, x1, yy, line("#94613A", 4))
        if d <= 3:
            c.drawOval(skia.Rect.MakeLTRB(cx - .55 * Z, gy + .12 * Z, cx + 1.8 * Z, gy + .62 * Z), fill("#D9534F"))
    # tour Eiffel
    th = 330 * Z
    if 6 < th < 4000:
        X = cx + 232 * Z
        lean = 0
        if d >= 11:
            f_ = clamp((t - T[11] - .25) / 1.0)
            lean = 11 * f_
            if d == 11:
                lean += math.sin(t * 60) * 1.3
        c.save()
        c.translate(X, gy)
        c.rotate(lean)
        draw_eiffel(c, th)
        c.restore()
    # canapé (écrasé après le jour 3)
    if d <= 6 and Z > 40:
        k = Z / 350
        c.save()
        c.translate(cx - 360 * k, gy - 1490 * k)
        c.scale(k, k)
        if d >= 4:
            c.translate(570, 1490)
            c.scale(1.05, .45)
            c.translate(-570, -1490)
        draw_couch(c)
        c.restore()
    debris(c, t, d, Z, gy, cx, L)
    # gamelle
    if 5 <= d <= 12:
        bx, by = 92, gy + 2
        s_ = 1.0
        shape(c, poly([(bx - 86, by - 54), (bx + 86, by - 54), (bx + 68, by), (bx - 68, by)]), "#D9534F", 6)
        for i in range(9):
            r_ = random.Random(i)
            c.drawCircle(bx + r_.uniform(-62, 62), by - 58 - r_.uniform(0, 16), 11, fill("#8E5A2E"))
            c.drawCircle(bx + r_.uniform(-62, 62), by - 58 - r_.uniform(0, 16), 11, line(INK, 3))
    # Gérard derrière Michel quand il est encore à côté
    if not final and d <= 12 and d <= 2:
        pass
    # --- Michel
    s = (L * Z) / 405.0
    seat = 0.0
    if d <= 3:
        seat = (.51 * Z) * (1 - clamp((t - T[3]) / .3) if d == 3 else 1)
    base_y = gy - seat
    if d >= 28 and not final:
        base_y = gy
    mood = "bliss" if d < 26 else "open"
    if d == 21:
        mood = "open"
    vib = 0
    # Terre sous lui puis en orbite
    orbit = d >= 28 and not final
    e_pos = None
    if d >= 26 or final:
        pass
    if orbit or final:
        rE = max(R, 52)
    # orbite : la Terre derrière Michel sur la moitié du tour
    earth_front = True
    if orbit:
        f = t - T[28]
        ang = f * 2.1
        if d == 28:
            g = eout(f / .8)
            rx, ry = lerp(0, 410, g), lerp(R + 20, 120, g)
            ex = cx + rx * math.sin(ang)
            ey = gy - 240 + (ry if g > .5 else lerp(R + 240, ry, g * 2)) * math.cos(ang)
        else:
            ex, ey = cx + 410 * math.sin(ang), gy - 240 + 120 * math.cos(ang)
        earth_front = math.cos(ang) > 0
        art.LAT0, art.LON0 = math.radians(18), math.radians(10 + t * 60)
        e_pos = (ex, ey)
        if d == 29:   # pelote : petit coup de patte
            ex = cx + 330 + 40 * math.sin((t - T[29]) * 12)
            ey = gy - 90 - abs(math.sin((t - T[29]) * 6)) * 120
            earth_front = True
            e_pos = (ex, ey)
        if d == 30:
            ex, ey = cx + 370, gy - 40
            earth_front = True
            e_pos = (ex, ey)
        if not earth_front:
            earth_at(c, ex, ey, rE, 0, 1.0)
    # table
    table_y = None
    if final:
        f = eout((t - PH["table"]) / .7)
        table_y = lerp(2050, 1160, f)
        draw_table(c, table_y)
    # Lune et Terre sur la table
    mx, my, mrot = None, None, 0
    ex_f, ey_f = None, None
    if final:
        art.LAT0, art.LON0 = math.radians(18), math.radians(10 + t * 8)
        rE = 64
        rM = 48
        e0x = 650
        e0y = table_y - rE + 6
        mx0, my0 = 792, table_y - rM + 4
        mx, my = mx0, my0
        ex_f, ey_f = e0x, e0y
        if t >= PH["pushm"]:
            tp = t - PH["pushm"]
            dur = PH["fall"] - PH["pushm"]
            prog = clamp((tp - .5) / (dur - .5))
            mx = lerp(mx0, TABLE_EDGE + 8, prog ** 1.25)
            mrot = (mx - mx0) * 1.2
            if tp >= dur:
                td = tp - dur
                mx = TABLE_EDGE + 8 + 110 * td
                my = my0 + 2100 * td * td
                mrot += td * 500
        if t >= PH["pushe"]:
            tp = t - PH["pushe"]
            prog = clamp((tp - .35) / (PH["pushe"] + 1.9 - PH["pushe"] - .35))
            ex_f = lerp(e0x, TABLE_EDGE - 8, prog ** 1.2)
        # croisement : la Terre derrière la Lune
        earth_at(c, ex_f, ey_f, rE, 0, 1.0)
        if my < H + 100:
            c.save()
            c.translate(mx, my)
            c.rotate(mrot)
            c.translate(-mx, -my)
            draw_moon(c, mx, my, rM, t, "wow")
            c.restore()
    # le chat
    if not (d < 3 and False):
        if d <= 12 and d >= 3:
            pass
        draw_cat(c, cx, base_y, s, t, "open" if final else mood, vib)
    # panier
    if d <= 2:
        k = Z / 350
        bw = .28 * Z
        by = base_y + 2
        shape(c, oval(cx - bw, by - .1 * Z, cx + bw, by + .05 * Z), "#C9975B", 6)
        for i in range(-3, 4):
            c.drawLine(cx + i * bw * .26, by - .09 * Z, cx + i * bw * .26, by + .04 * Z, line("#8E6A3A", 3))
    # griffoir
    if d == 11:
        tt = t - T[11]
        if tt > .15:
            sx0, sy0 = cx + 150 * s, gy - 130 * s
            X = cx + 232 * Z
            tx_ = X - 66 + 22 * math.sin(tt * 24)
            ty_ = gy - th * .52 + 40 * math.sin(tt * 19)
            draw_paw(c, sx0, sy0, tx_, ty_, 64, True)
            for i in range(10):
                r_ = random.Random(i + int(t * 30))
                c.drawLine(tx_ + 30, ty_, tx_ + 30 + r_.uniform(10, 90), ty_ + r_.uniform(-60, 60), line("#FFD34D", 4))
    # ISS
    if d == 21:
        tt = t - T[21]
        f = tt / 1.6
        ix = lerp(-160, 1240, f)
        iy = gy - 900 + 20 * math.sin(tt * 4)
        draw_iss(c, ix, iy, .9, -6)
        hx = clamp(ix, cx + 300, 1000)
        draw_paw(c, cx + 250, gy - 290, hx, iy + 95 + 40 * math.sin(tt * 16), 62, True)
    # avion
    if d == 16:
        tt = t - T[16]
        hit = .62
        ex_, ey_ = cx - 232, gy - 742
        if tt < hit:
            f = tt / hit
            draw_plane(c, lerp(-170, ex_ - 58, f), lerp(ey_ - 60, ey_, f), 1.05, 3)
        else:
            k = tt - hit
            draw_plane(c, ex_ - 70 - 340 * k, ey_ + 900 * k * k + 60 * k, 1.05, 3 - 460 * k)
            for i in range(7):
                a = i / 7 * 6.28 + k * 7
                st = 1 - clamp(k / .6)
                c.drawCircle(ex_ + math.cos(a) * 80 * (.4 + k), ey_ + math.sin(a) * 52 * (.4 + k), 12 * st, fill("#FFE14D"))
                c.drawCircle(ex_ + math.cos(a) * 80 * (.4 + k), ey_ + math.sin(a) * 52 * (.4 + k), 12 * st, line(INK, 3))
    # Terre devant
    if orbit and earth_front:
        ex, ey = e_pos
        earth_at(c, ex, ey, rE, 0, 1.0)
        if d == 29:
            draw_paw(c, cx + 100, gy - 90, ex - 60, ey + 18, 56)
    # croquettes qui montent vers Michel (jour 30)
    if d == 30:
        ex, ey = e_pos
        for i in range(32):
            ph_ = ((t - T[30]) * 1.4 + i / 32) % 1
            x_ = lerp(ex - 20, cx + 40, ph_)
            y_ = lerp(ey - 30, gy - 300, ph_) - math.sin(ph_ * 3.14) * 90
            c.drawCircle(x_, y_, 8, fill("#8E5A2E"))
            c.drawCircle(x_, y_, 8, line(INK, 2))
    if d == 13:
        dr = (t - T[13]) * 30
        for xx, yy, ww in ((cx - 330 + dr, gy - 410, 470), (cx + 340 - dr, gy - 430, 520), (cx - 60 + dr * .5, gy - 370, 400)):
            draw_cloud(c, xx, yy, ww, .95)
    # nuages devant
    if 0.03 < Z < 3:
        for x, alt, w, front in CLOUDS:
            if not front:
                continue
            pw = w * Z
            a_ = clamp((pw - 40) / 60) * clamp((1800 - pw) / 700)
            if a_ > 0:
                draw_cloud(c, cx + x * Z, gy - alt * Z, pw, a_ * .92)
    # Gérard au sol
    if not final and d <= 12:
        gerard_world(c, t, d, Z, gy, cx, L, b["ger"])
    if d == 15:
        text(c, "MONT BLANC", 880, gy - 4807 * Z - 30, 50, "#FFFFFF", INK, 10)
    # pointeurs géographiques
    if d == 23:
        s_ = back((t - T[23]) / .16)
        ax, ay = cx + 250, gy + 12
        c.drawLine(ax + 150, ay + 96, ax + 8, ay + 8, line(INK, 14))
        c.drawLine(ax + 150, ay + 96, ax + 8, ay + 8, line("#FFE14D", 7))
        text(c, "LA FRANCE", ax + 180, ay + 170, 60 * s_, "#FFFFFF", INK, 11)
    if d == 24:
        # Sahara : 23° N, 8° E
        la, lo = math.radians(23), math.radians(8)
        sp, cp = math.sin(art.LAT0), math.cos(art.LAT0)
        xx = math.cos(la) * math.sin(lo - art.LON0)
        yy = cp * math.sin(la) - sp * math.cos(la) * math.cos(lo - art.LON0)
        px_, py_ = cx + R * xx, gy + R - R * yy
        s_ = back((t - T[24]) / .16)
        c.drawCircle(px_, py_, 18 * s_, fill("#FF3B30"))
        c.drawCircle(px_, py_, 18 * s_, line("#FFFFFF", 5))
        text(c, "LITIÈRE", px_ + 200, py_ + 22, 62 * s_, "#FFFFFF", INK, 11)
    # patte finale
    if final:
        shx, shy = cx + 130, base_y - 170
        rest = (cx + 170, base_y - 40)
        px_, py_ = rest
        if ph == "pushm":
            tp = t - PH["pushm"]
            g = eout(tp / .5)
            px_ = lerp(rest[0], mx - rM - 42, g)
            py_ = lerp(rest[1], my - 6, g)
        elif ph == "fall":
            tp = t - PH["fall"]
            px_ = lerp(TABLE_EDGE - 40, rest[0], eout((tp - .25) / .5))
            py_ = lerp(table_y - 40, rest[1], eout((tp - .25) / .5))
        elif ph == "pushe":
            tp = t - PH["pushe"]
            g = eout(tp / .35)
            px_ = lerp(rest[0], ex_f - rE - 42, g)
            py_ = lerp(rest[1], ey_f - 4, g)
        if ph in ("pushm", "fall", "pushe"):
            draw_paw(c, shx, shy, px_, py_, 58)
    c.restore()


# ---------------------------------------------------------------- HUD / légendes
def heat(d):
    stops = [(1, "#59E36A"), (8, "#D7F03A"), (13, "#FFC531"), (19, "#FF7A1F"), (24, "#FF2EA6"), (28, "#D9C3FF"), (32, "#FFFFFF")]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if a <= d <= b:
            return hexmix(ca, cb, (d - a) / (b - a))
    return "#FFFFFF"


def hud(c, t, d):
    since = t - T[d]
    pop = 1 + .14 * (1 - eout(since / .22)) if d > 1 else 1.0
    colr = heat(d)
    c.save()
    c.translate(540, 262)
    c.scale(pop, pop)
    pan = rrect(-420, -135, 420, 135, 44)
    c.drawPath(pan, fill("#14121C", .94))
    c.drawPath(pan, line(colr, 8))
    text(c, "JOUR %d" % d, 0, -86, 40, "#C9C6D8")
    text(c, fmt_size(d), 0, 36, 128, colr)
    m, e = fmt_mass(d)
    lab = m
    f = skia.Font(TF, 46)
    if e is None:
        text(c, lab, 0, 106, 46, "#FFFFFF")
    else:
        w0 = f.measureText(lab + " kg")
        fe = skia.Font(TF, 28)
        we = fe.measureText(str(e))
        x = -(w0 + we) / 2
        c.drawString(lab, x, 106, f, fill("#FFFFFF"))
        x2 = x + f.measureText(lab)
        c.drawString(str(e), x2 + 2, 86, fe, fill("#FFFFFF"))
        c.drawString(" kg", x2 + we + 2, 106, f, fill("#FFFFFF"))
    c.restore()


def caption(c, t):
    b = beat_at(t)
    if not b["cap"]:
        return
    d_ = t - b["start"]
    s = back(d_ / .17)
    size = 74
    f = skia.Font(TF, size)
    lines = wrap_rich(b["cap"], f, 960)
    lh = size * 1.16
    top = 415
    hgt = lh * len(lines)
    c.save()
    c.translate(540, top + hgt / 2)
    c.scale(s, s)
    c.translate(-540, -(top + hgt / 2))
    y = top + size * .86
    sp = f.measureText(" ") * 1.6
    for ln in lines:
        wd = sum(f.measureText(w) for w, _ in ln) + sp * (len(ln) - 1)
        x = 540 - wd / 2
        for w, h_ in ln:
            c.drawString(w, x, y, f, line(INK, 15))
            c.drawString(w, x, y, f, fill("#FFE14D" if h_ else "#FFFFFF"))
            x += f.measureText(w) + sp
        y += lh
    c.restore()


STK = {6: "\U0001F4DE", 8: "\U0001F3CA", 9: "\U0001F4F5", 10: "\U0001F69C", 29: "\U0001F9F6"}
_FE = skia.Font(TF_EMOJI, 104)


def sticker(c, t, d):
    if d not in STK or t >= T[d] + beat_at(T[d])["dur"]:
        return
    s = back((t - T[d]) / .16)
    c.save()
    c.translate(905, 760)
    c.rotate(6)
    c.scale(s, s)
    c.drawCircle(0, 0, 82, fill("#FFFFFF"))
    c.drawCircle(0, 0, 82, line(INK, 7))
    e = STK[d]
    c.drawString(e, -_FE.measureText(e) / 2, 38, _FE, fill("#000000"))
    c.restore()


def card(c, t):
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#000000"))
    d_ = t - CARD
    if d_ < .25:
        return
    s = back((d_ - .25) / .22)
    c.save()
    c.translate(540, 760)
    c.scale(s, s)
    text(c, "JOUR 32 :", 0, 0, 86, "#FFFFFF")
    text(c, "LA TERRE TOMBE", 0, 128, 104, "#FFD93B")
    text(c, "DE LA TABLE.", 0, 240, 104, "#FFD93B")
    c.restore()
    a = clamp((d_ - .6) / .25)
    text(c, "Taille × 2 et poids × 8 par jour, depuis 40 cm et 4 kg.", 540, 1130, 37, "#A9A6BC", a=a)
    text(c, "Physique très approximative. Michel n'a aucun remords.", 540, 1182, 37, "#A9A6BC", a=a)


def frame(c, t):
    if t >= CARD:
        card(c, t)
        return
    b = beat_at(t)
    d = b["d"]
    scene(c, t)
    sticker(c, t, d)
    if d >= 13:
        pip(c, t, d, b["ger"])
    hud(c, t, d)
    caption(c, t)


SCENES = [("g_a", 0, T[8]), ("g_b", T[8], T[17]), ("g_c", T[17], T[26]), ("g_d", T[26], PH["table"]), ("g_e", PH["table"], CARD), ("g_f", CARD, END)]


def png(t, path):
    from PIL import Image
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    s = skia.Surface(arr)
    with s as c:
        frame(c, t)
    Image.fromarray(arr[..., :3]).save(path)


if __name__ == "__main__":
    print("durée %.1f, table %.1f, carton %.1f" % (END, PH["table"], CARD))
    if sys.argv[1:] == ["render"] or sys.argv[1:2] == ["render"]:
        only = sys.argv[2:]
        os.makedirs("sg", exist_ok=True)
        for name, a, b in SCENES:
            if only and name not in only:
                continue
            f0, f1 = round(a * FPS), round(b * FPS)
            tmp, final = f"sg/{name}.tmp.mp4", f"sg/{name}.mp4"
            p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                  "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", "60", tmp], stdin=subprocess.PIPE)
            arr = np.zeros((H, W, 4), dtype=np.uint8)
            sf = skia.Surface(arr)
            for i in range(f0, f1):
                arr[..., :] = 0
                with sf as c:
                    frame(c, i / FPS)
                arr[..., 3] = 255
                p.stdin.write(arr.tobytes())
            p.stdin.close()
            if p.wait() == 0:
                os.rename(tmp, final)
            print("ok", name, f1 - f0, flush=True)
    elif sys.argv[1:]:
        from PIL import Image
        days = [float(x) for x in sys.argv[1:]]
        ims = []
        for i, k in enumerate(days):
            png(k, "pg/%02d.png" % i)
            ims.append("pg/%02d.png" % i)
        cols = 8
        rows = (len(ims) + cols - 1) // cols
        sh = Image.new("RGB", (cols * 244, rows * 430), "#333")
        for i, p in enumerate(ims):
            sh.paste(Image.open(p).resize((240, 427)), ((i % cols) * 244, (i // cols) * 430))
        sh.save("pg/_sheet.png")
