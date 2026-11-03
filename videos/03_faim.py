"""Michel a deux fois plus faim chaque jour — Gérard vend tout."""
import math, random, sys, os, json, subprocess
import numpy as np
import skia
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "moteur"))
import art
from art import (fill, line, col, hexmix, poly, rrect, oval, shape, text, jitter, clamp, lerp, eout, ein, back,
                 draw_cat, draw_gerard, draw_couch, draw_eiffel, draw_moon, draw_house, draw_car, bubble,
                 earth_rgba, STARS, wrap_rich, TF, TF_EMOJI, INK, W, H, FPS, ROWS)

# ---------------------------------------------------------------- chronologie
# (jour, durée, légende, Gérard dit, clé)
RAW = [
    (1, 3.0, "CE CHAT A DEUX FOIS | PLUS FAIM *CHAQUE JOUR.*", None, "hook"),
    (1, 2.4, "Jour 1 : 50 g de croquettes. | *25 centimes.* Tranquille.", None, ""),
    (2, 1.2, "Jour 2 : 100 g. Normal.", None, ""),
    (3, 1.2, "Il finit la gamelle. | Il la regarde.", None, ""),
    (5, 1.3, "800 g. | Gérard trouve ça mignon.", "Il est mignon !", ""),
    (7, 1.4, "3 kg. Gérard trouve ça | moins mignon.", "Encore ?", ""),
    (9, 1.5, "Il mange 3 fois son poids. | *Il pèse toujours 4 kg.*", None, ""),
    (10, 1.5, "Personne ne sait où ça va.", None, ""),
    (12, 1.6, "512 € par jour. | Gérard vend sa console.", "Bon.", "s_console"),
    (14, 1.3, "Puis la télé.", None, "s_tv"),
    (15, 1.3, "Puis le canapé.", "Bon, bon.", "s_couch"),
    (17, 1.9, "16 384 € par jour. | *Il vend sa voiture.*", "Ma voiture...", "s_car"),
    (17, 1.2, "Ça a payé une journée.", None, ""),
    (20, 1.4, "26 tonnes. | Un camion par jour.", None, "truck"),
    (22, 2.0, "524 288 € par jour. | *Il vend sa maison.*", "...", "s_house"),
    (22, 1.2, "Ça a payé une journée.", None, ""),
    (24, 2.5, "Il vend sa moustache. *40 €.* | 1,6 seconde de croquettes.", "Mes poils...", "s_must"),
    (29, 1.6, "Un seul repas pèse plus lourd | que la tour Eiffel.", None, ""),
    (31, 1.5, "La banque lui prête | 300 millions.", None, "bank"),
    (32, 1.3, "La banque ferme.", None, "s_bank"),
    (34, 1.6, "Il lance une cagnotte. | *12 €.*", "Merci Tatie.", ""),
    (37, 2.1, "17 milliards par jour. | *Il vend la tour Eiffel.*", "Désolé, Paris.", "s_eiffel"),
    (41, 1.6, "Versailles. Le Louvre. | Le Mont-Saint-Michel.", None, "pins"),
    (45, 2.4, "4 398 milliards par jour. | *Il vend la France.*", "Désolé, la France.", "s_france"),
    (45, 1.5, "Acheteur : le Luxembourg.", None, ""),
    (47, 1.6, "Plus de croquettes | que de céréales sur Terre.", None, ""),
    (50, 2.2, "140 000 milliards par jour. | *Plus que tout ce que | la planète produit.*", None, ""),
    (51, 1.4, "L'argent n'existe plus.", None, ""),
    (56, 1.4, "Les forêts. | Il n'est pas difficile.", None, ""),
    (68, 1.6, "L'atmosphère : *une gorgée.*", None, ""),
    (76, 1.7, "Les océans : *un repas.*", "Il reste du thon ?", ""),
    (82, 1.8, "La Lune : *un dessert.*", None, ""),
    (88, 3.0, "Jour 88 : *la Terre.*", "MICHEL.", "gulp"),
    (88, 1.8, "Il pèse toujours 4 kg.", None, "burp"),
    (88, 1.7, None, None, "mrrp"),
    (89, 2.8, "Jour 89. | *Il regarde Gérard.*", "...Michel ?", "stare"),
]
CARD_DUR = 2.6
BEATS = []
_t = 0.0
for d_, dur, cap, ger, key in RAW:
    BEATS.append(dict(d=d_, start=_t, dur=dur, cap=cap, ger=ger, key=key))
    _t += dur
CARD = _t
END = CARD + CARD_DUR
T, K = {}, {}
for b in BEATS:
    T.setdefault(b["d"], b["start"])
    if b["key"]:
        K[b["key"]] = b["start"]


def beat_at(t):
    cur = BEATS[0]
    for b in BEATS:
        if b["start"] <= t:
            cur = b
        else:
            break
    return cur


def phase(d):
    return "salon" if d <= 15 else "rue" if d <= 22 else "ville" if d <= 37 else "carte" if d <= 45 else "espace"


def cost(d):
    return .25 * 2 ** (d - 1)


def food(d):
    return .05 * 2 ** (d - 1)


SALES = {12: 250, 14: 500, 15: 400, 17: 18000, 22: 550000, 24: 40, 31: 3e8, 34: 12, 37: 1.7e10, 41: 2.7e11, 45: 3e12}


def balance(d):
    s = sum(v for k, v in SALES.items() if k <= d)
    return 3000 + s - .25 * (2 ** d - 1)


def fr1(x):
    return ("%.1f" % x).replace(".", ",")


def grp(n):
    s = str(int(round(n)))
    o = []
    while s:
        o.append(s[-3:])
        s = s[:-3]
    return " ".join(reversed(o))


def euros(v):
    a = abs(v)
    if a < 1:
        return ("%d centimes" % round(a * 100))
    if a < 100 and a != int(a):
        return fr1(a) + " €"
    if a < 1e6:
        return grp(a) + " €"
    if a < 1e9:
        x = a / 1e6
        return (fr1(x) if x < 10 else "%d" % round(x)) + " millions €"
    x = a / 1e9
    return (fr1(x) if x < 10 else grp(x)) + " milliards €"


def fmt_food(d):
    m = food(d)
    if m < 1:
        return "%d g" % round(m * 1000)
    if m < 20:
        return fr1(m) + " kg"
    if m < 1000:
        return "%d kg" % round(m)
    t_ = m / 1000
    if t_ < 1e6:
        return grp(t_) + " tonnes"
    if t_ < 1e9:
        x = t_ / 1e6
        return (fr1(x) if x < 10 else "%d" % round(x)) + " millions de tonnes"
    x = t_ / 1e9
    return (fr1(x) if x < 10 else grp(x)) + " milliards de tonnes"


# ---------------------------------------------------------------- France
def _load_fr():
    p = os.path.join(art.HERE, "france.json")
    if os.path.exists(p):
        return json.load(open(p))
    topo = json.load(open(os.path.join(art.ROOT, "donnees", "countries-50m.json")))
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

    res = {}
    for g in topo["objects"]["countries"]["geometries"]:
        if str(g.get("id")) in ("250", "442"):
            polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]]
            rr = []
            for pl in polys:
                rg = ring(pl[0])
                mx = sum(p[0] for p in rg) / len(rg)
                my = sum(p[1] for p in rg) / len(rg)
                if -7 < mx < 11 and 40 < my < 53:
                    rr.append(rg)
            res[str(g["id"])] = rr
    json.dump(res, open(p, "w"))
    return res


FR = _load_fr()
FC = (46.6, 2.6)


def proj(la, lo, R, cx, cy):
    la, lo = math.radians(la), math.radians(lo)
    a0, l0 = art.LAT0, art.LON0
    sp, cp = math.sin(a0), math.cos(a0)
    x = math.cos(la) * math.sin(lo - l0)
    y = cp * math.sin(la) - sp * math.cos(la) * math.cos(lo - l0)
    return cx + R * x, cy - R * y


# ---------------------------------------------------------------- petites pièces
GY = 1560
CATX, CATS = 300, .76
GERX, GERK = 842, .62
BOWLX = 545
MOUTH = (CATX + 2, GY - 212 * CATS)


def stamp(c, x, y, t0, t, label="VENDU", size=110, rot=-12, hold=99):
    d = t - t0
    if d < 0 or d > hold:
        return
    s = lerp(2.6, 1, clamp(d / .12)) if d < .12 else 1 + .06 * (1 - clamp((d - .12) / .15))
    a = clamp(d / .06)
    f = skia.Font(TF, size)
    w = f.measureText(label)
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    r = rrect(-w / 2 - 26, -size * .92, w / 2 + 26, size * .3, 14)
    c.drawPath(r, fill("#FFFFFF", .86 * a))
    c.drawPath(r, line("#E0202B", size * .085, a))
    c.drawString(label, -w / 2, 0, f, fill("#E0202B", a))
    c.restore()


def price(c, x, y, t0, t, label):
    d = t - t0 - .18
    if d < 0 or d > 1.3:
        return
    a = clamp(1.5 - d * 1.1)
    text(c, label, x, y - d * 48, 58, "#39D353", INK, 11, a=a)


def gone(t, t0):
    """Sortie de l'objet vendu (0 = en place, 1 = parti)."""
    return ein((t - t0 - .62) / .36) if t >= t0 else 0


def heap(c, x, y, w, h, seed=3):
    if h < 2:
        return
    p = skia.Path()
    p.moveTo(x - w / 2, y)
    p.cubicTo(x - w * .32, y - h * .55, x - w * .15, y - h, x, y - h)
    p.cubicTo(x + w * .15, y - h, x + w * .32, y - h * .55, x + w / 2, y)
    p.close()
    c.drawPath(p, fill("#9A6332"))
    c.save()
    c.clipPath(p, skia.ClipOp.kIntersect, True)
    r = random.Random(seed)
    n = int(clamp(w * h / 1400, 6, 260))
    rad = clamp(w / 22, 7, 15)
    for i in range(n):
        xx, yy = x + r.uniform(-w / 2, w / 2), y - r.uniform(0, h)
        c.drawCircle(xx, yy, rad, fill(r.choice(("#7E4E25", "#B57A42", "#8E5A2E"))))
    c.restore()
    c.drawPath(p, line(INK, 5))


def sack(c, x, y, s=1.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    shape(c, rrect(-54, -130, 54, 0, 20), "#E8C24A", 6)
    shape(c, rrect(-44, -148, 44, -122, 8), "#D1A93A", 5)
    c.drawCircle(0, -72, 26, fill("#F49A3A"))
    for sgn in (-1, 1):
        c.drawPath(poly([(sgn * 24, -86), (sgn * 26, -112), (sgn * 7, -98)]), fill("#F49A3A"))
    c.restore()


def bowl(c, x, y, fullness, s=1.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    if fullness > 0:
        r = random.Random(4)
        for i in range(int(16 * fullness)):
            xx = r.uniform(-58, 58)
            yy = -62 - r.uniform(0, 22 * fullness)
            c.drawCircle(xx, yy, 11, fill(r.choice(("#8E5A2E", "#B57A42"))))
            c.drawCircle(xx, yy, 11, line(INK, 3))
    shape(c, poly([(-86, -58), (86, -58), (68, 0), (-68, 0)]), "#D9534F", 6)
    text(c, "MICHEL", 0, -20, 26, "#FFFFFF")
    c.restore()


def mouth_open(c, a):
    """Bouche ouverte de Michel par-dessus le dessin."""
    if a <= 0.02:
        return
    w, h = 21 * CATS * (1 + a * .25), 28 * CATS * a
    c.drawOval(skia.Rect.MakeLTRB(MOUTH[0] - w, MOUTH[1] - 6, MOUTH[0] + w, MOUTH[1] + h), fill(INK))
    c.drawOval(skia.Rect.MakeLTRB(MOUTH[0] - w * .55, MOUTH[1] + h * .35, MOUTH[0] + w * .55, MOUTH[1] + h * .95), fill("#E8627A"))


def stream(c, t, sx, sy, n, r0, mid_lift=120, colr=("#8E5A2E", "#B57A42", "#7E4E25"), spd=1.3):
    for i in range(n):
        ph = (t * spd + i / n) % 1
        rr = random.Random(i * 13)
        o = rr.uniform(-1, 1)
        x = lerp(sx + o * 44, MOUTH[0], ph ** 1.2)
        y = lerp(sy + o * 30, MOUTH[1] + 6, ph) - math.sin(ph * 3.14) * mid_lift + o * 18 * (1 - ph)
        rd = r0 * (1 - ph * .55)
        c.drawCircle(x, y, rd, fill(colr[i % len(colr)]))
        c.drawCircle(x, y, rd, line(INK, 2))


def foreground(c, t, d, b):
    ph = phase(d)
    suit = ph == "espace"
    key = b["key"]
    # sol
    if ph == "salon":
        pass
    elif ph == "espace":
        rk = [(-20, GY - 8), (150, GY - 16), (420, GY - 6), (700, GY - 15), (1100, GY - 8), (1100, GY + 44), (960, GY + 110), (820, GY + 86), (640, GY + 150), (430, GY + 110), (270, GY + 152), (110, GY + 92), (-20, GY + 116)]
        shape(c, poly(rk), "#74788A", 7)
        c.drawRect(skia.Rect.MakeLTRB(-20, GY + 20, 1100, GY + 31), fill("#5A5E70"))
    # gamelle + tas (derrière Michel)
    empty = key in ("burp", "mrrp", "stare")
    fullness = 1.0 if d >= 2 else 1 - clamp((t - .6) / 4)
    if d == 3 and t - T[3] > .45:
        fullness = 0
    if empty:
        fullness = 0
    if 5 <= d <= 15:
        hh = clamp((d - 5) / 15) ** .8
        heap(c, BOWLX + 22, GY - 3, lerp(170, 620, hh), lerp(60, 520, hh))
    elif d >= 20 and ph == "rue":
        hh = eout((t - K["truck"] - .55) / .7)
        if hh > 0:
            heap(c, BOWLX + 10, GY - 3, 480 * hh, 330 * hh)
    bowl(c, BOWLX, GY + 4, fullness)
    if 7 <= d <= 15:
        for k, (dx, dy) in enumerate(((150, 0), (92, 0), (118, -116))):
            if d >= 7 + k * 2:
                sack(c, BOWLX + dx - 30, GY + dy, .86)
    # flux
    if ph == "salon" and d <= 4:
        pass
    elif d >= 5 and (ph == "salon" or (ph == "rue" and d >= 20)):
        stream(c, t, BOWLX, GY - 70, int(clamp(d * 1.8, 10, 44)), lerp(7, 13, clamp(d / 22)), 74)
    elif ph == "ville":
        stream(c, t, -40, 1000, 56, 15, 40, spd=1.7)
    elif ph == "carte":
        stream(c, t, 520, 1140, 62, 16, 26, spd=2.0)
    # Gérard
    moustache = not (d >= 24 and t >= K["s_must"] + .55)
    stg = 0 if d <= 5 else 1 if d <= 7 else 2 if d <= 15 else 3
    if key in ("stare",):
        stg = 2
    if ph == "espace" and d < 76:
        stg = 3
    k = GERK
    c.save()
    c.translate(GERX - 790 * k, GY - 1498 * k)
    c.scale(k, k)
    draw_gerard(c, stg, t, suit, 0 if d < 12 else 2, moustache)
    c.restore()
    # moustache qui part
    if d == 24:
        dd = t - K["s_must"] - .55
        if 0 <= dd < 1.1:
            mx, my = GERX + 0 + 150 * dd, GY - 1498 * k + 1020 * k - 120 * dd * dd
            p = skia.Path()
            p.moveTo(mx, my)
            p.quadTo(mx - 20, my - 4, mx - 36, my + 12)
            p.quadTo(mx - 18, my + 16, mx, my + 8)
            p.quadTo(mx + 18, my + 16, mx + 36, my + 12)
            p.quadTo(mx + 20, my - 4, mx, my)
            c.drawPath(p, fill("#6A6470"))
    # Michel
    mood = "bliss"
    if key in ("mrrp", "stare"):
        mood = "open"
    elif d == 3 and t - T[3] > .45:
        mood = "open"
    draw_cat(c, CATX, GY, CATS, t, mood, 0)
    if key not in ("burp", "mrrp", "stare") and (d >= 5 or (d <= 2 and t > 2.7)):
        rate = 5 + min(d, 45) * .35
        mouth_open(c, .35 + .65 * abs(math.sin(t * rate)))
    # bulles
    if b["ger"]:
        s_ = back((t - b["start"]) / .16)
        bubble(c, GERX - 70, GY - 1498 * k + 904 * k - 62, b["ger"], 46, s_, 2)


def bg_salon(c, t, d):
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#F7DDAE"))
    for x in range(-40, W + 80, 120):
        c.drawRect(skia.Rect.MakeLTRB(x, 0, x + 60, 1490), fill("#F2D29C", .55))
    c.drawRect(skia.Rect.MakeLTRB(0, 1466, W, 1495), fill("#FFF5E0"))
    c.drawRect(skia.Rect.MakeLTRB(0, 1495, W, H), fill("#B47B4C"))
    for y in range(1540, H, 90):
        c.drawLine(0, y, W, y, line("#94613A", 5))
    # fenêtre
    win = skia.Rect.MakeLTRB(66, 702, 400, 960)
    c.drawRect(win, fill("#9BDCFA"))
    c.drawRect(win, line(INK, 24))
    c.drawRect(win, line("#FFFFFF", 16))
    c.drawLine(233, 702, 233, 960, line("#FFFFFF", 11))
    c.drawLine(66, 830, 400, 830, line("#FFFFFF", 11))
    # télé + console
    if d < 14 or t < K["s_tv"] + 1.0:
        g = gone(t, K["s_tv"]) * 900
        shape(c, rrect(640 + g, 690, 1000 + g, 900, 12), "#20202B", 7)
        c.drawRect(skia.Rect.MakeLTRB(656 + g, 706, 984 + g, 884), fill("#3F6FD8"))
        c.drawCircle(820 + g, 795, 48, fill("#FFFFFF", .22))
        c.drawPath(poly([(804 + g, 768), (804 + g, 822), (848 + g, 795)]), fill("#FFFFFF", .75))
    shape(c, rrect(700, 930, 945, 950, 5), "#7B4A2B", 5)
    if d < 12 or t < K["s_console"] + 1.0:
        g = gone(t, K["s_console"]) * 900
        shape(c, rrect(748 + g, 884, 900 + g, 932, 8), "#E8E8F0", 5)
        c.drawCircle(868 + g, 908, 7, fill("#39D353"))
        c.drawLine(762 + g, 908, 836 + g, 908, line("#9A9AAA", 5))
    # canapé
    if d < 15 or t < K["s_couch"] + 1.0:
        g = gone(t, K["s_couch"]) * 1500
        k = .76
        c.save()
        c.translate(30 - 70 * k + g, 1495 - 1490 * k)
        c.scale(k, k)
        draw_couch(c)
        c.restore()


HOUSE_X = 300


def bg_rue(c, t, d):
    sky = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 0), (0, 1400)], [col("#5CB8F2"), col("#D3F1FF")]))
    c.drawRect(skia.Rect.MakeWH(W, H), sky)
    gr = 1420
    c.drawRect(skia.Rect.MakeLTRB(0, gr, W, H), fill("#6B6E7E"))
    c.drawRect(skia.Rect.MakeLTRB(0, gr, W, gr + 26), fill("#9EA1AE"))
    for x in range(-40, W, 180):
        c.drawRect(skia.Rect.MakeLTRB(x, gr + 88, x + 100, gr + 100), fill("#F4E9B8"))
    draw_house(c, -160, 300, 330, gr, "#E58B7B", "#7A3B3B")
    draw_house(c, 880, 300, 360, gr, "#8FC8A2", "#3B5E4A")
    # maison de Gérard
    ks = K["s_house"]
    up = 0
    if t >= ks:
        up = ein((t - ks - .85) / .9) * 1500
    if up < 1400:
        c.save()
        c.translate(0, -up)
        if t >= ks + .55:
            c.drawLine(540, -600 + up * 0, 540, 920, line(INK, 8))
        draw_house(c, 220, 480, 410, gr, "#F7DDAE", "#B24B36")
        shape(c, rrect(415, gr - 150, 505, gr, 6), "#7B4A2B", 5)
        c.restore()
    else:
        c.drawRect(skia.Rect.MakeLTRB(190, gr - 12, 730, gr), fill("#7B6A5A"))
    if d == 17 or (d == 20 and False):
        pass
    # voiture
    kc = K["s_car"]
    if t < kc + 1.15:
        draw_car(c, 640 + gone(t, kc) * 800, gr + 70, 1.45, "#3F6FD8", False)
    # camion
    if d == 20:
        tt = t - T[20]
        x = lerp(-420, 560, eout(tt / .5))
        c.save()
        c.translate(x, gr + 30)
        shape(c, rrect(-180, -150, 120, -30, 6), "#E8E8F0", 6)
        text(c, "CROQUETTES", -30, -76, 38, "#E0202B")
        shape(c, rrect(124, -116, 214, -30, 12), "#E84B4B", 6)
        c.drawRect(skia.Rect.MakeLTRB(160, -102, 202, -66), fill("#CDEBFF"))
        for wx in (-120, 60, 170):
            c.drawCircle(wx, -20, 25, fill(INK))
            c.drawCircle(wx, -20, 10, fill("#B8BCC8"))
        c.restore()


BANK = (540, 1330)


def bg_ville(c, t, d):
    sky = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 0), (0, 1400)], [col("#141A44"), col("#39356E"), col("#E8785A")], [0, .62, 1]))
    c.drawRect(skia.Rect.MakeWH(W, H), sky)
    c.drawCircle(160, 720, 52, fill("#F6F1D0"))
    # tour Eiffel
    ke = K["s_eiffel"]
    up = 0
    if t >= ke:
        up = ein((t - ke - .9) / 1.0) * 1700
    c.save()
    c.translate(650, 1280 - up)
    if t >= ke + .55 and up < 1600:
        c.drawLine(0, -620, 0, -1900, line("#C9CBD6", 6))
    if up < 1600:
        draw_eiffel(c, 560)
    c.restore()
    for ri, (yb, colr, bl) in enumerate(ROWS[:2]):
        for (x, w, h, wins, rnd) in bl:
            c.drawRect(skia.Rect.MakeLTRB(x, yb - h, x + w, H), fill(colr))
            c.drawRect(skia.Rect.MakeLTRB(x, yb - h, x + w, H), line(INK, 3))
            for (wx, wy, r) in wins:
                c.drawRect(skia.Rect.MakeLTRB(wx, wy, wx + 18, wy + 30), fill("#FFD966" if r < .6 else "#241F38"))
    # banque
    if 31 <= d <= 32:
        x, y = BANK
        s_ = back((t - T[31]) / .25)
        c.save()
        c.translate(x, y + 200)
        c.scale(s_, s_)
        c.translate(0, -200)
        shape(c, poly([(-300, -180), (0, -300), (300, -180)]), "#E8E2D2", 7)
        shape(c, rrect(-280, -180, 280, 150, 6), "#F2ECDC", 7)
        for cx_ in (-225, -125, 125, 225):
            shape(c, rrect(cx_ - 22, -150, cx_ + 22, 150, 4), "#FFFFFF", 5)
        text(c, "BANQUE", 0, -210, 54, INK)
        shape(c, rrect(-62, -40, 62, 150, 6), "#5A4630", 6)
        c.restore()
        if d == 32:
            stamp(c, x, y - 40, T[32] + .1, t, "FERMÉ", 118, -10)
    # sol : trottoir
    c.drawRect(skia.Rect.MakeLTRB(0, 1480, W, H), fill("#8E91A0"))
    c.drawRect(skia.Rect.MakeLTRB(0, 1480, W, 1496), fill("#B9BCC8"))
    for x in range(-20, W, 150):
        c.drawLine(x, 1496, x - 60, H, line("#7A7D8C", 4))


def bg_carte(c, t, d):
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#2B86DE"))
    art.LAT0, art.LON0 = math.radians(FC[0]), math.radians(FC[1])
    f = eout((t - T[41]) / .4)
    R = lerp(5200, 3150, f)
    cx, cy = 540, 1040
    img, x0, y0 = earth_rgba(R, 0, 0, None, 0.0, cx, cy)
    c.drawImage(img, x0, y0)
    # France
    ks = K["s_france"]
    red = clamp((t - ks - .05) / .12) if t >= ks else 0
    for code, colr, base in (("250", "#7FD08C", .55),):
        for rg in FR[code]:
            pts = [proj(la, lo, R, cx, cy) for lo, la in rg]
            p = poly(pts)
            c.drawPath(p, fill(hexmix(colr, "#E0202B", red), base + .4 * red))
            c.drawPath(p, line("#123B2A", 5))
    # épingles
    for i, (name, la, lo, dt, tx, ty) in enumerate((("VERSAILLES", 48.80, 2.13, .1, 0, -112), ("LOUVRE", 48.86, 2.34, .55, 190, -26), ("MONT-ST-MICHEL", 48.64, -1.51, 1.0, -30, -26))):
        tb = K["pins"] + dt
        if tb <= t:
            x, y = proj(la, lo, R, cx, cy)
            if d == 41:
                c.drawCircle(x, y, 14, fill("#E0202B"))
                c.drawCircle(x, y, 14, line("#FFFFFF", 4))
                lx_ = clamp(x + tx, 210, W - 210)
                text(c, name, lx_, y + ty, 42, "#FFFFFF", INK, 9)
                stamp(c, lx_, y + ty + 54, tb + .1, t, "VENDU", 34, -7)
    # Luxembourg
    if d == 45 and t >= K["s_france"] + 2.2:
        lx, ly = proj(49.7, 6.1, R, cx, cy)
        s_ = back((t - K["s_france"] - 2.2) / .2)
        for rg in FR["442"]:
            p = poly([proj(la, lo, R, cx, cy) for lo, la in rg])
            c.drawPath(p, fill("#39D353"))
            c.drawPath(p, line(INK, 4))
        c.drawLine(lx + 90, ly - 95, lx + 8, ly - 8, line(INK, 12))
        c.drawLine(lx + 90, ly - 95, lx + 8, ly - 8, line("#FFE14D", 6))
        text(c, "LUXEMBOURG", clamp(lx + 40, 240, W - 240), ly - 110, 62 * s_, "#FFFFFF", INK, 12)
    if d == 45:
        x, y = proj(FC[0], FC[1], R, cx, cy)
        stamp(c, x, y + 60, ks + .05, t, "VENDU", 170, -13)
    return R


E_C = (540, 970)


def bg_espace(c, t, d, b):
    c.drawImage(STARS, 0, 0)
    key = b["key"]
    # Terre
    heat = clamp((d - 47) / 9) ** 1.5 * .55
    if d >= 56:
        heat = lerp(.55, 1, clamp((t - T[56]) / .8))
    boil = clamp((t - T[76]) / 1.0) if d >= 76 else 0
    clouds = 1 - clamp((d - 50) / 6)
    art.LAT0, art.LON0 = math.radians(25), math.radians(8 + t * 7)
    R0 = 300
    R = R0
    cx, cy = E_C
    gulp_t = K["gulp"]
    alpha_gone = False
    if key == "gulp":
        f = (t - gulp_t - .3) / 2.4
        if f > 0:
            e = clamp(f) ** 1.8
            R = max(lerp(R0, 2, e), 2)
            cx = lerp(E_C[0], MOUTH[0], e)
            cy = lerp(E_C[1], MOUTH[1], e)
            if f >= 1:
                alpha_gone = True
    elif key in ("burp", "mrrp", "stare"):
        alpha_gone = True
    if not alpha_gone:
        pos = (cx, cy)
        if R > 6:
            if d < 68 or (d == 68 and t - T[68] < .8):
                a_ = 1 - (clamp((t - T[68]) / .8) if d == 68 else 0)
                pp = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((cx, cy), R * 1.13, [col("#6FC5FF", .85 * a_), col("#6FC5FF", .85 * a_), col("#6FC5FF", 0)], [0, 1 / 1.13, 1]))
                c.drawCircle(cx, cy, R * 1.13, pp)
            if d == 68:
                stream(c, t, E_C[0], E_C[1] + 160, 60, 12, 40, ("#BEE8FF", "#FFFFFF", "#6FC5FF"), 2.6)
            img, x0, y0 = earth_rgba(max(R, 8), heat, boil, None, clouds, cx, cy)
            c.drawImage(img, x0, y0)
            c.drawCircle(cx, cy, R, line(INK, 4))
    # Lune
    if d == 82:
        tt = t - T[82]
        f = clamp(tt / 1.5)
        mx = lerp(1140, MOUTH[0], ein(f))
        my = lerp(640, MOUTH[1], ein(f))
        rm = lerp(84, 8, ein(f))
        if f < .98:
            draw_moon(c, mx, my, rm, t, "wow")
    if d == 76 and False:
        pass
    # flux
    if key not in ("gulp", "burp", "mrrp", "stare") and d != 82:
        if d == 68:
            pass
        elif d >= 76:
            stream(c, t, E_C[0], E_C[1] + 160, 92, 16, 40, ("#6FC5FF", "#2B86DE", "#BEE8FF"), 2.4)
        elif d >= 56:
            stream(c, t, E_C[0], E_C[1] + 160, 92, 16, 40, ("#3E9E5A", "#7B5A3A", "#8E5A2E"), 2.4)
        else:
            stream(c, t, E_C[0], E_C[1] + 160, 80, 15, 40, spd=2.2)
    elif key == "gulp":
        f = (t - gulp_t - .3) / 2.4
        if 0 < f < 1:
            rk = random.Random(9)
            for i in range(70):
                ph = (t * 3 + i / 70) % 1
                x = lerp(cx, MOUTH[0], ph) + rk.uniform(-1, 1) * R * (1 - ph)
                y = lerp(cy, MOUTH[1], ph) + rk.uniform(-1, 1) * R * (1 - ph)
                c.drawCircle(x, y, 6 + 12 * (1 - ph), fill(rk.choice(("#5BBF6B", "#7A3A1E", "#2B86DE"))))


def scene(c, t):
    b = beat_at(t)
    d = b["d"]
    ph = phase(d)
    key = b["key"]
    since = t - b["start"]
    amp = (1 - clamp(since / .18)) * clamp(d / 25) * 12
    for k_, big in (("s_house", 20), ("s_eiffel", 20), ("s_france", 30)):
        if k_ in K and 0 <= t - K[k_] < .28:
            amp = max(amp, big * (1 - (t - K[k_]) / .28))
    if key == "gulp" and 1.2 < t - K["gulp"] < 2.75:
        amp = 16
    jx, jy = jitter(t, 2)
    zz = 1 + 2.2 * amp / W
    if key == "stare":
        zz *= 1 + .16 * eout((t - K["stare"]) / 2.4)
    c.save()
    c.translate(540, 1200 if key == "stare" else 960)
    c.scale(zz, zz)
    c.translate(-540 + jx * amp, -(1200 if key == "stare" else 960) + jy * amp)
    p0 = None
    if ph == "salon":
        bg_salon(c, t, d)
    elif ph == "rue":
        bg_rue(c, t, d)
    elif ph == "ville":
        bg_ville(c, t, d)
    elif ph == "carte":
        bg_carte(c, t, d)
    else:
        bg_espace(c, t, d, b)
    foreground(c, t, d, b)
    # tampons
    if ph == "salon":
        if key == "s_console" or (d == 12):
            stamp(c, 826, 930, K["s_console"], t, "VENDU", 62, -10, 1.0)
            price(c, 830, 830, K["s_console"], t, "+250 €")
        if d == 14:
            stamp(c, 820, 830, K["s_tv"], t, "VENDU", 100, -10, 1.0)
            price(c, 820, 700, K["s_tv"], t, "+500 €")
        if d == 15:
            stamp(c, 540, 1230, K["s_couch"], t, "VENDU", 120, -8, 1.0)
            price(c, 540, 1090, K["s_couch"], t, "+400 €")
    elif ph == "rue":
        if d == 17 and t < K["s_car"] + 1.1:
            stamp(c, 620, 1310, K["s_car"], t, "VENDU", 86, -10, 1.0)
            price(c, 610, 1190, K["s_car"], t, "+18 000 €")
        if d == 22 and t < K["s_house"] + 1.5:
            stamp(c, 460, 1190, K["s_house"], t, "VENDU", 130, -12, 1.4)
            price(c, 460, 1020, K["s_house"], t, "+550 000 €")
    elif ph == "ville":
        if d == 24:
            price(c, GERX - 40, 1060, K["s_must"] + .3, t, "+40 €")
        if d == 37 and t < K["s_eiffel"] + 1.8:
            stamp(c, 650, 1000, K["s_eiffel"], t, "VENDU", 120, -11, 1.7)
    if key == "burp":
        s_ = back((t - K["burp"]) / .16)
        bubble(c, CATX + 150, GY - 400, "Burp.", 60, s_, -4)
    if key == "mrrp":
        s_ = back((t - K["mrrp"]) / .18)
        bubble(c, CATX + 170, GY - 410, "mrrp ?", 62, s_, -4)
    c.restore()
    if ph in ("rue", "ville", "carte", "espace") and d in (17, 24, 41, 47) and t - T[d] < .16:
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", 1 - (t - T[d]) / .16))


def heat_c(d):
    stops = [(1, "#59E36A"), (10, "#D7F03A"), (17, "#FFC531"), (24, "#FF7A1F"), (37, "#FF2E2E"), (47, "#FF2EA6"), (76, "#D9C3FF"), (89, "#FFFFFF")]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if a <= d <= b:
            return hexmix(ca, cb, (d - a) / (b - a))
    return "#FFFFFF"


def fit(s, size, maxw):
    f = skia.Font(TF, size)
    while f.measureText(s) > maxw and size > 20:
        size -= 2
        f = skia.Font(TF, size)
    return size


def hud(c, t, d):
    since = t - T[d]
    pop = 1 + .13 * (1 - eout(since / .22)) if d > 1 else 1.0
    colr = heat_c(d)
    c.save()
    c.translate(540, 262)
    c.scale(pop, pop)
    pan = rrect(-420, -135, 420, 135, 44)
    c.drawPath(pan, fill("#14121C", .94))
    c.drawPath(pan, line(colr, 8))
    if d <= 50:
        head = "JOUR %d · %s de croquettes" % (d, fmt_food(d))
        text(c, head, 0, -88, fit(head, 38, 770), "#C9C6D8")
        big = euros(cost(d))
        text(c, big, 0, 32, fit(big, 118, 780), colr)
        bal = balance(d)
        sign = "−" if bal < 0 else ""
        low = "Compte de Gérard : " + sign + euros(bal)
        text(c, low, 0, 106, fit(low, 44, 780), "#FF8A7A" if bal < 0 else "#FFFFFF")
    else:
        head = "JOUR %d · ration du jour" % d
        text(c, head, 0, -88, 38, "#C9C6D8")
        m = food(d)
        e = int(math.floor(math.log10(m)))
        lab = fr1(m / 10 ** e) + " × 10"
        f = skia.Font(TF, 104)
        fe = skia.Font(TF, 58)
        w0 = f.measureText(lab)
        we = fe.measureText(str(e))
        wk = f.measureText(" kg")
        x = -(w0 + we + wk) / 2
        c.drawString(lab, x, 30, f, fill(colr))
        c.drawString(str(e), x + w0 + 2, -22, fe, fill(colr))
        c.drawString(" kg", x + w0 + we + 2, 30, f, fill(colr))
        text(c, "Compte de Gérard : n'existe plus", 0, 106, 44, "#FF8A7A")
    c.restore()


def caption(c, t):
    b = beat_at(t)
    if not b["cap"]:
        return
    d_ = t - b["start"]
    s = back(d_ / .17)
    size = 72
    f = skia.Font(TF, size)
    lines = wrap_rich(b["cap"], f, 980)
    lh = size * 1.16
    top = 412
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


def card(c, t):
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#000000"))
    d_ = t - CARD
    if d_ < .2:
        return
    s = back((d_ - .2) / .22)
    c.save()
    c.translate(540, 780)
    c.scale(s, s)
    text(c, "À SUIVRE :", 0, 0, 86, "#FFFFFF")
    text(c, "IL A ENCORE FAIM.", 0, 132, 100, "#FFD93B")
    c.restore()
    a = clamp((d_ - .5) / .25)
    text(c, "Ration × 2 par jour, depuis 50 g à 25 centimes (5 €/kg).", 540, 1085, 36, "#A9A6BC", a=a)
    text(c, "Économie très approximative. Le Luxembourg n'a pas été consulté.", 540, 1137, 33, "#A9A6BC", a=a)


def frame(c, t):
    if t >= CARD:
        card(c, t)
        return
    scene(c, t)
    hud(c, t, beat_at(t)["d"])
    caption(c, t)


SPL = [("f_a", 0, T[17]), ("f_b", T[17], T[31]), ("f_c", T[31], T[47]), ("f_d", T[47], K["gulp"]), ("f_e", K["gulp"], CARD), ("f_f", CARD, END)]


def png(t, path):
    from PIL import Image
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    s = skia.Surface(arr)
    with s as c:
        frame(c, t)
    Image.fromarray(arr[..., :3]).save(path)


if __name__ == "__main__":
    print("durée %.1f s, carton %.1f" % (END, CARD))
    if sys.argv[1:2] == ["render"]:
        only = sys.argv[2:]
        os.makedirs("sf", exist_ok=True)
        for name, a, b in SPL:
            if only and name not in only:
                continue
            f0, f1 = round(a * FPS), round(b * FPS)
            tmp, final = f"sf/{name}.tmp.mp4", f"sf/{name}.mp4"
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
