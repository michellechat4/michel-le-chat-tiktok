"""Le poisson rouge de Gérard double de taille chaque jour. Michel voulait le manger. Le poisson n'oublie rien."""
import math, random, sys, os, subprocess
import numpy as np
import skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "moteur"))
import art
from art import (fill, line, col, hexmix, poly, rrect, oval, shape, text, jitter, clamp, lerp, eout, back,
                 draw_cat, draw_gerard, draw_couch, draw_eiffel, draw_moon, earth_rgba, STARS, bubble, wrap_rich, TF, INK, W, H, FPS)

# ---------------------------------------------------------------- chiffres (calculés, pas recopiés)
L0 = 5.0                       # cm au jour 0 : petit poisson rouge d'animalerie (hypothèse, vendus vers 4-5 cm)
RECORD = 47.4                  # cm, plus long poisson rouge (Guinness World Records, 2003)
REQUIN = 6.1                   # m, aucun grand requin blanc confirmé au-delà (Wikipédia, Great white shark size)
BALEINE = (24, 30)             # m, baleine bleue adulte, fourchette usuelle (Discover Magazine)
EIFFEL = 330                   # m, avec antennes
FOSSE = 10935                  # m, Challenger Deep (Wikipédia, Mariana Trench)
KARMAN = 100                   # km, limite conventionnelle de l'espace
TERRE = 12742                  # km, diamètre moyen
LUNE = 384400                  # km, distance moyenne Terre-Lune


def cm(day):
    return L0 * 2 ** day


assert 30 < cm(3) < RECORD < cm(4)
assert cm(7) / 100 > REQUIN and BALEINE[0] < cm(9) / 100 < BALEINE[1] and cm(10) / 100 > 1.5 * BALEINE[1]
assert cm(13) / 100 > EIFFEL and cm(18) / 100 > FOSSE and cm(21) / 1e5 > KARMAN
assert cm(27) / 1e5 < TERRE < cm(28) / 1e5 and cm(32) / 1e5 < LUNE < cm(33) / 1e5
assert round(cm(13) / 100) == 410 and round(cm(18) / 1e5, 1) == 13.1 and round(cm(21) / 1e5) == 105
assert round(cm(28) / 1e5) == 13422 and round(cm(33) / 1e5) == 429497

# ---------------------------------------------------------------- chronologie
# (clé, durée, jour, légende, Gérard dit, décor)
RAW = [
    ("hook", 3.0, 0, "MICHEL VEUT MANGER | *CE POISSON ROUGE.*", None, "bocal"),
    ("regle", 3.0, 0, "Règle : chaque jour, | le poisson *double de taille.*", "Il s'appelle Bubulle.", "bocal"),
    ("j1", 2.6, 1, "Jour 1 : 10 cm. | Michel *se lèche les babines.*", None, "bocal"),
    ("j3", 3.0, 3, "Jour 3 : 40 cm. Presque | le *record du monde* (47 cm).", None, "bocal"),
    ("j4", 3.0, 4, "Jour 4 : 80 cm. | *Plus grand que Michel.*", None, "bain"),
    ("recul", 2.6, 4, "Michel *reconsidère* | la situation.", None, "bain"),
    ("j5", 3.0, 5, "Jour 5 : 1,60 m. | Il prend *toute la baignoire.*", "Mon bain…", "bain"),
    ("memo", 3.4, 5, "3 secondes de mémoire ? *Faux.* | Un poisson retient *des mois.*", None, "memo"),
    ("j7", 3.0, 7, "Jour 7 : 6,40 m. *Plus long* | qu'un *grand requin blanc.*", None, "piscine"),
    ("j9", 3.2, 9, "Jour 9 : 25,6 m. | La taille d'une *baleine bleue.*", None, "mer"),
    ("j10", 2.8, 10, "Jour 10 : 51,2 m. | *Deux baleines bleues.*", None, "mer"),
    ("j13", 3.2, 13, "Jour 13 : 410 m. Debout, | il dépasse la *tour Eiffel.*", None, "paris"),
    ("j18", 3.4, 18, "Jour 18 : 13,1 km. La *fosse des Mariannes* | (11 km) est *trop petite.*", None, "fosse"),
    ("j21", 3.0, 21, "Jour 21 : 105 km. | Son museau *touche l'espace.*", None, "limite"),
    ("entr", 3.0, 21, "Pendant ce temps, | *Michel s'entraîne.*", "Il a ses chances ?", "entr"),
    ("j28", 3.2, 28, "Jour 28 : 13 422 km. | *Plus grand que la Terre.*", None, "terre"),
    ("j33", 3.2, 33, "Jour 33 : 429 497 km. | *Plus long que la route vers la Lune.*", None, "lune"),
    ("duel", 3.2, 33, "Le combat final. | *Michel contre Bubulle.*", None, "duel"),
    ("regard", 3.0, 33, "Michel le fixe. | *Comme au jour 0.*", None, "duel"),
    ("fuite", 3.0, 33, "Bubulle a *très bonne mémoire.* | Il s'en va.", None, "duel"),
    ("fin", 4.0, 0, "Gérard rachète un poisson. | *Un tout petit.*", "Bubulle 2.", "fin"),
]
CARD_DUR = 3.2
BEATS = []
_t, _d = 0.0, 0
for key, dur, d, cap, ger_, ph_ in RAW:
    BEATS.append(dict(key=key, start=_t, dur=dur, d0=_d, d1=d, cap=cap, ger=ger_, ph=ph_))
    _t += dur
    _d = d
CARD = _t
END = CARD + CARD_DUR
K = {b["key"]: b["start"] for b in BEATS}
ROLL = .45
JUMPS = [b["start"] for b in BEATS if b["d1"] > b["d0"]]
FLOOR = 1565
ORF, GOLD, FIN_C = "#FF6A2B", "#FFC24D", "#FF9A4D"


def beat_at(t):
    cur = BEATS[0]
    for b in BEATS:
        if b["start"] <= t:
            cur = b
        else:
            break
    return cur


def day_at(t):
    b = beat_at(t)
    f = eout((t - b["start"]) / ROLL)
    if b["d1"] <= b["d0"] or f >= 1:
        return b["d1"]
    return lerp(b["d0"], b["d1"], f)


# ---------------------------------------------------------------- Bubulle
def fish(c, x, y, L, t, mood="calm", flip=False, rot=0.0, squash=1.0):
    """Poisson rouge, longueur L px du museau au bout de la queue, centré en (x, y)."""
    s = L / 240
    sw = clamp(7 * s, 2.5, 8) / s
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(-s if flip else s, s * squash)
    wob = math.sin(t * 7) * 10
    tail = skia.Path()
    tail.moveTo(-62, 0)
    tail.quadTo(-100, -30, -122, -66 + wob)
    tail.quadTo(-104, 0, -122, 66 + wob)
    tail.quadTo(-100, 30, -62, 0)
    tail.close()
    shape(c, tail, FIN_C, sw)
    for k in (-30, 0, 30):
        c.drawLine(-70, k * .2, -112, k + wob * .8, line("#E8501E", sw * .6, .7))
    dorsal = poly([(-30, -46), (10, -84 - wob * .3), (40, -48)])
    shape(c, dorsal, FIN_C, sw)
    shape(c, oval(-78, -56, 120, 56), ORF, sw)
    c.save()
    c.clipPath(oval(-78, -56, 120, 56), skia.ClipOp.kIntersect, True)
    c.drawOval(skia.Rect.MakeLTRB(-60, 10, 110, 70), fill(GOLD))
    for i in range(4):
        for j in range(3):
            cx_, cy_ = -40 + i * 26, -26 + j * 24
            p = skia.Path()
            p.addArc(skia.Rect.MakeLTRB(cx_ - 12, cy_ - 12, cx_ + 12, cy_ + 12), -70, 140)
            c.drawPath(p, line("#E8501E", sw * .5, .8))
    c.restore()
    c.drawOval(skia.Rect.MakeLTRB(-78, -56, 120, 56), line(INK, sw))
    pec = poly([(10, 18), (-20, 46 + wob * .4), (24, 34)])
    shape(c, pec, FIN_C, sw * .8)
    # œil
    ex, ey = 72, -14
    c.drawCircle(ex, ey, 21, fill("#FFFFFF"))
    c.drawCircle(ex, ey, 21, line(INK, sw * .8))
    if mood == "scared":
        c.drawCircle(ex + 4, ey, 6, fill(INK))
        for k in range(2):
            ph = (t * 1.6 + k * .5) % 1
            c.drawCircle(ex - 28 + ph * 6, ey - 40 + ph * 50, 7 * (1 - ph * .4), fill("#7EC8FF"))
    elif mood == "angry":
        c.drawCircle(ex + 5, ey + 2, 11, fill(INK))
        c.drawLine(ex - 22, ey - 34, ex + 20, ey - 20, line(INK, sw * 1.1))
    else:
        c.drawCircle(ex + 5, ey + 1, 11, fill(INK))
        c.drawCircle(ex + 9, ey - 4, 4, fill("#FFFFFF"))
    # bouche
    if mood == "scared":
        c.drawOval(skia.Rect.MakeLTRB(106, 6, 122, 26), fill(INK))
    else:
        c.drawCircle(114, 14, 6, line(INK, sw * .7))
    c.restore()


def bloups(c, t, x, y, n=3, sc=1.0, seed=1):
    r = random.Random(seed)
    for i in range(n):
        ph = (t * r.uniform(.6, 1.0) + r.random()) % 1
        rr = (6 + 8 * r.random()) * sc
        c.drawCircle(x + math.sin(t * 3 + i) * 8 * sc, y - ph * 160 * sc, rr, line("#FFFFFF", 3, .8 * (1 - ph)))


# ---------------------------------------------------------------- Gérard et décors (repris de la vidéo 06)
def ger(c, x, floor, s, t, stage=0, suit=False, vib=0.0, hold=None):
    """Gérard debout ; hold = 'bocal' pour un petit bocal en main."""
    c.save()
    c.translate(x, floor)
    c.scale(s, s)
    c.translate(-790, -1516)
    sw = "#F2F2F7" if suit else "#3F6FD8"
    draw_gerard(c, stage, t, suit, vib, True)
    for sg in (-1, 1):
        arm = skia.Path()
        arm.moveTo(790 + sg * 96, 1160)
        if hold:
            arm.quadTo(790 + sg * 124, 1260, 790 + sg * 60, 1272)
        else:
            arm.quadTo(790 + sg * 130, 1250, 790 + sg * 118, 1330)
        c.drawPath(arm, line(INK, 56))
        c.drawPath(arm, line(sw, 42))
    if hold:
        bowl(c, 790, 1250, .75, t, 0)
    c.restore()


def gerbub(c, t, b, x, y):
    if not b["ger"]:
        return
    f = skia.Font(TF, 50)
    w = f.measureText(b["ger"])
    xx = clamp(x - 20, w / 2 + 44, W - w / 2 - 44)
    bubble(c, xx, y, b["ger"], 50, back((t - b["start"] - .35) / .16), 2)


def wall(c, base="#F7DDAE", stripe="#F2D29C", floor="#7B4A2B"):
    c.drawRect(skia.Rect.MakeWH(W, H), fill(base))
    for x in range(0, W, 120):
        c.drawRect(skia.Rect.MakeLTRB(x, 0, x + 60, FLOOR), fill(stripe, .55))
    c.drawRect(skia.Rect.MakeLTRB(0, FLOOR - 34, W, FLOOR), fill("#FFF5E0"))
    c.drawRect(skia.Rect.MakeLTRB(0, FLOOR, W, H), fill(floor))
    c.drawLine(0, FLOOR, W, FLOOR, line(INK, 7))
    for i in range(5):
        c.drawLine(i * 240 + 60, FLOOR + 2, i * 300 - 180, H, line(INK, 4, .35))


def window(c, x, y, w=240, h=300, sky="#9BDCFA"):
    win = skia.Rect.MakeLTRB(x, y, x + w, y + h)
    c.drawRect(win, fill(sky))
    c.drawRect(win, line(INK, 22))
    c.drawRect(win, line("#FFFFFF", 14))
    c.drawLine(x + w / 2, y, x + w / 2, y + h, line("#FFFFFF", 10))
    c.drawLine(x, y + h / 2, x + w, y + h / 2, line("#FFFFFF", 10))


def bowl(c, x, base, s, t, fish_px, mood="calm", bulge=0.0):
    """Bocal rond posé en (x, base). fish_px = longueur du poisson en px (repère du bocal)."""
    c.save()
    c.translate(x, base)
    c.scale(s, s)
    R = 150
    cy = -R + 10
    c.drawCircle(0, cy, R, fill("#BFE8FF", .55))
    c.save()
    pp = skia.Path()
    pp.addCircle(0, cy, R)
    c.clipPath(pp, skia.ClipOp.kIntersect, True)
    c.drawRect(skia.Rect.MakeLTRB(-R, cy - R * .55, R, cy + R), fill("#6CC3F0", .55))
    c.drawRect(skia.Rect.MakeLTRB(-R, cy + R * .7, R, cy + R), fill("#E8C27A"))
    c.restore()
    if fish_px > 0:
        sq = 1.0 - .25 * bulge
        fish(c, math.sin(t * 1.3) * (R - fish_px * .5) * .35 * (1 - bulge), cy + 18, fish_px, t, mood, flip=math.cos(t * 1.3) < 0 and bulge < .5, squash=sq)
        if fish_px < 120:
            bloups(c, t, 30, cy - 10, 3, .5, 4)
    c.drawCircle(0, cy, R, line(INK, 8))
    p = skia.Path()
    p.addArc(skia.Rect.MakeLTRB(-R + 22, cy - R + 22, R - 22, R - 22 + cy), 200, 50)
    c.drawPath(p, line("#FFFFFF", 12, .8))
    shape(c, rrect(-78, cy - R - 10, 78, cy - R + 18, 10), "#BFE8FF", 6)
    if bulge > .5:
        for k in range(3):
            c.drawLine(R * .6 + k * 8, cy - 40 + k * 30, R * .8 + k * 10, cy - 20 + k * 40, line(INK, 4))
    c.restore()


def table(c, x, top, w=420):
    shape(c, rrect(x - w / 2, top, x + w / 2, top + 40, 10), "#9B6A3C", 7)
    for lx in (x - w / 2 + 30, x + w / 2 - 60):
        shape(c, rrect(lx, top + 36, lx + 30, FLOOR, 6), "#7B4A2B", 6)


# ---------------------------------------------------------------- scènes
PXCM_BOCAL = 4.6


def scene_bocal(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    wall(c)
    window(c, 90, 640)
    table(c, 650, 1240)
    day = day_at(t)
    px = cm(day) * PXCM_BOCAL
    bulge = clamp((day - 2) / 1)
    bowl(c, 650, 1244, 1.15, t, px, "scared" if key == "j3" else "calm", bulge)
    # Michel assis devant, il fixe
    mood = "open"
    draw_cat(c, 260, FLOOR + 10, .62, t, mood, 0)
    if key == "j1":
        # langue
        u = clamp(math.sin(clamp(d_ / 1.2) * math.pi * 3))
        c.drawOval(skia.Rect.MakeLTRB(248, FLOOR - 128, 274, FLOOR - 128 + 34 * u), fill("#FF7A8A"))
        if d_ > 1.2:
            bubble(c, 300, 1180, "mrrp…", 52, back((d_ - 1.2) / .16), -3)
    if key == "regle":
        gx = lerp(1320, 940, eout((d_ - .1) / .5))
        ger(c, gx, FLOOR + 14, .62, t, 0)
        gerbub(c, t, b, gx - 90, 1110)
    if key == "j3" and d_ > 1.4:
        bubble(c, 820, 900, "47 cm", 52, back((d_ - 1.4) / .16), 3, color="#FFE14D")


def bathtub(c, x0, x1, top, bot):
    shape(c, rrect(x0, top, x1, bot, 60), "#FFFFFF", 8)
    for fx in (x0 + 60, x1 - 100):
        shape(c, rrect(fx, bot - 10, fx + 40, bot + 40, 10), "#C9962E", 6)


def scene_bain(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    # carrelage
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#CFEFF2"))
    for x in range(0, W, 90):
        c.drawLine(x, 560, x, FLOOR, line("#A9D9DE", 4))
    for y in range(560, FLOOR, 90):
        c.drawLine(0, y, W, y, line("#A9D9DE", 4))
    c.drawRect(skia.Rect.MakeLTRB(0, FLOOR, W, H), fill("#7FA8C9"))
    c.drawLine(0, FLOOR, W, FLOOR, line(INK, 7))
    # robinet
    shape(c, rrect(118, 1060, 150, 1180, 10), "#C9CED8", 5)
    shape(c, rrect(118, 1060, 230, 1092, 10), "#C9CED8", 5)
    # baignoire 170 cm = 600 px
    x0, x1, top = 140, 140 + 600, 1180
    PX = 600 / 170
    c.drawRect(skia.Rect.MakeLTRB(x0 + 18, top + 30, x1 - 18, top + 60), fill("#6CC3F0"))
    day = day_at(t)
    L = cm(day) * PX
    mood = "angry" if key == "recul" else "calm"
    fish(c, (x0 + x1) / 2 + 10, top + 8, L, t, mood, flip=key == "recul")
    c.save()
    c.clipPath(skia.Path().addRect(skia.Rect.MakeLTRB(0, top + 40, W, H)), skia.ClipOp.kIntersect, True)
    bathtub(c, x0, x1, top, 1500)
    c.restore()
    c.drawLine(x0 + 30, top + 40, x1 - 30, top + 40, line(INK, 7))
    # Michel (≈ 46 cm de long) sur le rebord droit
    if key == "j5":
        mx = None
    else:
        mx = lerp(x1 - 20, 930, eout((d_ - .6) / .5)) if key == "recul" else x1 - 20
    if mx is None:
        draw_cat(c, 830, FLOOR + 10, .45, t, "open", 0)
    else:
        draw_cat(c, mx, top + 46, .5, t, "open", 1.5 if key == "recul" else 0)
    if key == "j4" and d_ > 1.0:
        # règle
        yy = top - 230
        c.drawLine(x0 + 300 - L / 2 + 10, yy, x0 + 300 + L / 2 + 10, yy, line(INK, 6))
        text(c, "80 cm", x0 + 310, yy - 20, 48, "#FFE14D", INK, 9, a=clamp((d_ - 1) / .2))
    if key == "recul" and d_ > 1.3:
        bubble(c, 880, 1000, "…", 60, back((d_ - 1.3) / .16), 4)
    if key == "j5":
        gx = lerp(1320, 1000, eout((d_ - .2) / .5))
        c.save()
        c.translate(gx, FLOOR + 14)
        c.scale(.58, .58)
        c.translate(-790, -1516)
        draw_gerard(c, 2, t)
        shape(c, rrect(690, 1100, 900, 1330, 60), "#FFFFFF", 8)  # serviette
        c.drawLine(700, 1180, 890, 1180, line("#D9534F", 12))
        c.restore()
        gerbub(c, t, b, gx - 40, 1040)
        bloups(c, t, 520, top + 20, 4, 1.2, 9)


def scene_memo(c, t, b):
    d_ = t - b["start"]
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#14324A"))
    rr = random.Random(2)
    for i in range(30):
        x0, ph = rr.uniform(0, W), rr.random()
        y = 1700 - ((t * 80 + ph * 1200) % 1200)
        c.drawCircle(x0, y, rr.uniform(4, 12), line("#9BDCFA", 3, .5))
    z = lerp(1.0, 1.15, eout(d_ / 3))
    fish(c, 330, 1330, 700 * z, t, "angry")
    # bulle de pensée : Michel, jour 0
    u = back((d_ - .3) / .25)
    for k, (bx, by, br) in enumerate(((520, 1150, 16), (580, 1090, 24))):
        c.drawCircle(bx, by, br * u, fill("#FFFFFF"))
        c.drawCircle(bx, by, br * u, line(INK, 5))
    cx, cy, R = 780, 860, 230
    c.save()
    c.translate(cx, cy)
    c.scale(u, u)
    c.drawCircle(0, 0, R, fill("#F7DDAE"))
    pp = skia.Path()
    pp.addCircle(0, 0, R)
    c.save()
    c.clipPath(pp, skia.ClipOp.kIntersect, True)
    draw_cat(c, 0, R * .95, .62, t, "open", 0)
    c.drawRect(skia.Rect.MakeLTRB(-R, -R, R, R), fill("#E8D9B8", .25))
    c.restore()
    c.drawCircle(0, 0, R, line(INK, 8))
    text(c, "JOUR 0", 0, -R + 70, 46, "#FFFFFF", INK, 8)
    c.restore()
    if d_ > 1.6:
        s_ = back((d_ - 1.6) / .18)
        c.save()
        c.translate(780, 1180)
        c.rotate(-5)
        c.scale(s_, s_)
        shape(c, rrect(-190, -50, 190, 50, 12), "#D9534F", 6)
        text(c, "N'OUBLIE PAS", 0, 18, 50, "#FFFFFF")
        c.restore()


def sky_grad(c, a, b_, y0=400, y1=1400):
    p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, y0), (0, y1)], [col(a), col(b_)]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)


def scene_piscine(c, t, b):
    d_ = t - b["start"]
    sky_grad(c, "#5CB8F2", "#D3F1FF")
    c.drawRect(skia.Rect.MakeLTRB(0, 1180, W, H), fill("#7CC46E"))
    c.drawLine(0, 1180, W, 1180, line(INK, 6))
    # piscine vue de dessus inclinée
    pool = rrect(60, 1240, 1020, 1640, 30)
    shape(c, pool, "#3FB6E8", 8)
    c.drawPath(rrect(60, 1240, 1020, 1640, 30), line("#FFFFFF", 14, .9))
    c.drawPath(pool, line(INK, 5))
    PX = 140
    fish(c, 540, 1470, cm(day_at(t)) / 100 * PX, t, "calm")
    # silhouette du grand requin blanc, 6 m, en pointillé
    u = clamp((d_ - 1.0) / .3)
    if u > 0:
        sx0, sx1, sy = 540 - 3 * PX * 1.0, 540 + 3 * PX * 1.0, 1450
        sh = skia.Path()
        sh.moveTo(sx1, sy)
        sh.quadTo(sx1 - 120, sy - 70, sx0 + 140, sy - 40)
        sh.lineTo(sx0 + 60, sy - 110)
        sh.lineTo(sx0 + 80, sy)
        sh.lineTo(sx0 + 60, sy + 90)
        sh.lineTo(sx0 + 140, sy + 30)
        sh.quadTo(sx1 - 120, sy + 60, sx1, sy)
        sh.moveTo(540 - 40, sy - 55)
        sh.lineTo(540 + 10, sy - 130)
        sh.lineTo(540 + 70, sy - 52)
        c.drawPath(sh, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=7, Color=col("#FFFFFF", u),
                                  PathEffect=skia.DashPathEffect.Make([22, 14], 0)))
        text(c, "REQUIN BLANC : 6 m", 540, 1140, 48, "#FFFFFF", INK, 9, a=u)
    # Gérard sur sa chaise de plage, Michel au bord
    ger(c, 950, 1170, .26, t, 2)
    draw_cat(c, 140, 1230, .2, t, "open", 0)


def sea(c, t, y=1180, colr="#2B86DE"):
    c.drawRect(skia.Rect.MakeLTRB(0, y, W, H), fill(colr))
    p = skia.Path()
    p.moveTo(0, y)
    for i in range(0, W + 40, 40):
        p.lineTo(i, y + math.sin(i / 60 + t * 3) * 8)
    c.drawPath(p, line("#FFFFFF", 6, .7))


def boat(c, x, y, s, t):
    c.save()
    c.translate(x, y + math.sin(t * 2.5) * 6)
    c.scale(s, s)
    c.rotate(math.sin(t * 2) * 3)
    hull = poly([(-150, -40), (150, -40), (110, 30), (-110, 30)])
    shape(c, hull, "#D9534F", 7)
    c.drawLine(0, -40, 0, -230, line(INK, 8))
    shape(c, poly([(6, -220), (110, -60), (6, -60)]), "#FFFFFF", 6)
    draw_cat(c, -70, -36, .22, t, "open", 0)
    c.restore()


def scene_mer(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    sky_grad(c, "#5CB8F2", "#D3F1FF")
    PX = 34 if key == "j9" else lerp(34, 17, eout(d_ / .6))
    y = 1180
    sea(c, t, y)
    # baleine bleue (25 m) en pointillé sous l'eau
    wl = 25 * PX
    wx = 540
    L = cm(day_at(t)) / 100 * PX
    fish(c, 540, 1400, L, t, "calm")
    wh = skia.Path()
    wh.moveTo(wx + wl / 2, 1430)
    wh.quadTo(wx + wl / 2 - 40, 1340, wx, 1350)
    wh.quadTo(wx - wl * .3, 1360, wx - wl / 2 + 40, 1420)
    wh.lineTo(wx - wl / 2, 1370)
    wh.lineTo(wx - wl / 2 + 10, 1440)
    wh.lineTo(wx - wl / 2, 1500)
    wh.lineTo(wx - wl / 2 + 40, 1440)
    wh.quadTo(wx, 1520, wx + wl / 2, 1430)
    wh.offset(0, 50)
    if key == "j9":
        c.drawPath(wh, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=7, Color=col("#FFFFFF", .9),
                                  PathEffect=skia.DashPathEffect.Make([22, 14], 0)))
    text(c, "BALEINE BLEUE : 25 m", 540, 1650, 46, "#FFFFFF", INK, 9)
    boat(c, 870, y + 10, .55 if key == "j9" else lerp(.55, .3, eout(d_ / .6)), t)
    if key == "j10":
        # deuxième silhouette
        c.save()
        c.translate(-wl / 2, 0)
        c.drawPath(wh, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=7, Color=col("#FFE14D", clamp((d_ - .8) / .2)),
                                  PathEffect=skia.DashPathEffect.Make([22, 14], 0)))
        c.restore()
        c.save()
        c.translate(wl / 2, 0)
        c.drawPath(wh, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=7, Color=col("#FFE14D", clamp((d_ - .8) / .2)),
                                  PathEffect=skia.DashPathEffect.Make([22, 14], 0)))
        c.restore()


def scene_paris(c, t, b):
    d_ = t - b["start"]
    sky_grad(c, "#F7B267", "#FFE9B8")
    G = 1640
    PX = 2.2
    # immeubles
    r = random.Random(3)
    x = -20
    while x < W:
        w_ = r.uniform(90, 160)
        h_ = r.uniform(110, 200)
        shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(x, G - h_, x + w_, G)), "#B58FA0", 5)
        x += w_ + 6
    c.save()
    c.translate(330, G)
    draw_eiffel(c, EIFFEL * PX)
    c.restore()
    text(c, "330 m", 330, G - EIFFEL * PX - 26, 46, "#FFFFFF", INK, 9)
    c.drawRect(skia.Rect.MakeLTRB(0, G - 10, W, H), fill("#2B86DE"))
    c.drawLine(0, G - 10, W, G - 10, line(INK, 6))
    L = cm(day_at(t)) / 100 * PX
    rise = eout((d_ - .1) / .7)
    fish(c, 780, G + 30 - L / 2 * rise, L, t, "calm", rot=-90)
    if d_ > 1.0:
        text(c, "410 m", 780, G - L * rise - 6, 46, "#FFE14D", INK, 9, a=clamp((d_ - 1) / .2))


def scene_fosse(c, t, b):
    d_ = t - b["start"]
    sky_grad(c, "#5CB8F2", "#D3F1FF", 400, 900)
    S = 820                      # surface
    PXK = 62                     # px par km
    bottom = S + FOSSE / 1000 * PXK
    water = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, S), (0, bottom)], [col("#2B86DE"), col("#0B1D4A")]))
    c.drawRect(skia.Rect.MakeLTRB(0, S, W, H), water)
    # fond marin avec la fosse
    p = poly([(0, S + 260), (300, S + 330), (440, bottom), (600, bottom), (760, S + 330), (W, S + 280), (W, H), (0, H)])
    shape(c, p, "#5E4A3A", 7)
    c.drawLine(880, S, 880, bottom, line("#FFFFFF", 4, .7))
    text(c, "11 km", 960, (S + bottom) / 2, 46, "#FFFFFF", INK, 9)
    L = cm(day_at(t)) / 1e5 * PXK
    sink = eout(d_ / .8)
    fish(c, 520, lerp(S + 200, bottom - L / 2 + 10, sink), L, t, "calm", rot=-90)
    boat(c, 260, S + 6, .3, t)
    pw = skia.Path()
    pw.moveTo(0, S)
    for i in range(0, W + 40, 40):
        pw.lineTo(i, S + math.sin(i / 60 + t * 3) * 8)
    c.drawPath(pw, line("#FFFFFF", 6, .7))


def scene_limite(c, t, b):
    d_ = t - b["start"]
    p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 500), (0, 1600)], [col("#06061A"), col("#7EC8FF")]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    rr = random.Random(8)
    for i in range(120):
        y = rr.uniform(480, 900)
        c.drawCircle(rr.uniform(0, W), y, rr.choice((1.2, 2, 2.6)), fill("#FFFFFF", clamp((950 - y) / 400)))
    G = 1660
    PXK = 8.6
    shape(c, oval(-600, G - 40, W + 600, G + 1200), "#2B86DE", 7)
    ky = G - KARMAN * PXK
    c.drawPath(skia.Path().moveTo(0, ky).lineTo(W, ky),
               skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6, Color=col("#FFE14D"), PathEffect=skia.DashPathEffect.Make([26, 16], 0)))
    text(c, "ESPACE : 100 km", 830, ky - 24, 44, "#FFE14D", INK, 9)
    L = cm(day_at(t)) / 1e5 * PXK
    rise = eout(d_ / .8)
    fish(c, 400, G + 10 - L / 2 * rise, L, t, "calm", rot=-90)
    art.draw_iss(c, 800, ky + 160, .6, 8)


def scene_entr(c, t, b):
    d_ = t - b["start"]
    wall(c)
    window(c, 90, 640)
    # poster du poisson, griffé
    shape(c, rrect(560, 640, 980, 940, 8), "#FFF5E0", 7)
    fish(c, 770, 790, 300, t, "calm")
    n = int(clamp(d_ / 2.2) * 4)
    for k in range(n):
        for j in range(3):
            c.drawLine(640 + k * 80 + j * 18, 680, 610 + k * 80 + j * 18, 900, line(INK, 6))
    # Michel au sol, bandeau
    hop = abs(math.sin(t * 7)) * 30
    draw_cat(c, 370, FLOOR + 10 - hop, .6, t, "open", 1.0)
    c.drawRect(skia.Rect.MakeLTRB(370 - 95, FLOOR + 10 - hop - 225, 370 + 95, FLOOR + 10 - hop - 200), fill("#D9534F"))
    gx = lerp(1320, 900, eout((d_ - .2) / .5))
    ger(c, gx, FLOOR + 14, .6, t, 1)
    gerbub(c, t, b, gx - 60, 1070)


def scene_terre(c, t, b):
    d_ = t - b["start"]
    c.drawImage(STARS, 0, 0)
    R = 280
    cx, cy = 540, 1160
    img, x0, y0 = earth_rgba(R, cx=cx, cy=cy)
    c.drawImage(img, x0, y0)
    c.drawCircle(cx, cy, R, line(INK, 7))
    L = cm(day_at(t)) / 1e5 / TERRE * 2 * R
    fish(c, 540, lerp(1900, 760, eout((d_ - .1) / .9)), L, t, "calm")
    c.drawLine(cx - R, 1500, cx + R, 1500, line("#FFFFFF", 5))
    text(c, "TERRE : 12 742 km", cx, 1570, 46, "#FFFFFF", INK, 9)


def scene_lune(c, t, b):
    d_ = t - b["start"]
    c.drawImage(STARS, 0, 0)
    ex, mx, y = 110, 110 + 800, 1250
    img, x0, y0 = earth_rgba(46, cx=ex, cy=y)
    c.drawImage(img, x0, y0)
    c.drawCircle(ex, y, 46, line(INK, 5))
    draw_moon(c, mx, y, 30, t, "scared")
    c.drawPath(skia.Path().moveTo(ex, y + 110).lineTo(mx, y + 110),
               skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5, Color=col("#FFFFFF"), PathEffect=skia.DashPathEffect.Make([18, 12], 0)))
    text(c, "384 400 km", (ex + mx) / 2, y + 180, 50, "#FFFFFF", INK, 9)
    L = cm(day_at(t)) / 1e5 / LUNE * 800
    u = eout(d_ / .9)
    fish(c, ex + L / 2 - 40, lerp(1900, 990, u), L, t, "calm")


def scene_duel(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    c.drawImage(STARS, 0, 0)
    # sol lunaire
    shape(c, oval(-400, 1400, W + 400, 2600), "#C9CBD6", 8)
    for (x, y, r) in ((180, 1520, 40), (760, 1480, 30), (520, 1660, 60), (950, 1620, 28)):
        c.drawOval(skia.Rect.MakeLTRB(x - r, y - r * .4, x + r, y + r * .4), fill("#A7A9B8"))
    if key == "fuite":
        u = eout(d_ / 1.6)
        L = lerp(1800, 30, u)
        fx, fy = lerp(1280, 900, u), lerp(900, 640, u)
        fish(c, fx, fy, L, t, "scared")
        if u < .95:
            r = random.Random(4)
            for i in range(30):
                yy = fy + r.uniform(-1, 1) * L * .25
                c.drawLine(fx - 60, yy, fx - 60 - r.uniform(100, 500), yy, line("#FFFFFF", 4, .6 * (1 - u)))
    else:
        z = 1.0 if key == "duel" else lerp(1.0, 1.08, eout(d_ / 2.5))
        fish(c, 1280, 900, 1800 * z, t, "angry" if key == "duel" else "scared", flip=True)
    # Michel, casque
    mz = .55 if key != "regard" else lerp(.55, .85, eout(d_ / 1.2))
    mx, my = 300, 1500
    draw_cat(c, mx, my, mz, t, "wink" if key == "fuite" and d_ > 1.8 else "open", 0)
    c.drawCircle(mx, my - 270 * mz, 190 * mz, fill("#BEE8FF", .22))
    c.drawCircle(mx, my - 270 * mz, 190 * mz, line("#E9F6FF", 10 * mz))
    c.drawCircle(mx, my - 270 * mz, 190 * mz, line(INK, 4))
    if key == "fuite" and d_ > 1.9:
        bubble(c, 420, 1080, "mrrp.", 56, back((d_ - 1.9) / .16), -3)


def scene_fin(c, t, b):
    d_ = t - b["start"]
    wall(c)
    window(c, 90, 640)
    table(c, 650, 1240)
    bowl(c, 650, 1244, 1.15, t, 22, "scared")
    draw_cat(c, 260, FLOOR + 10, .62, t, "wink" if d_ > 2.6 else "open", 0)
    gx = lerp(1320, 960, eout((d_ - .1) / .5))
    ger(c, gx, FLOOR + 14, .62, t, 0)
    gerbub(c, t, b, gx - 90, 1000)
    if d_ > 2.0:
        u = clamp(math.sin(clamp((d_ - 2.0) / .8) * math.pi * 2))
        c.drawOval(skia.Rect.MakeLTRB(248, FLOOR - 128, 274, FLOOR - 128 + 34 * u), fill("#FF7A8A"))


# ---------------------------------------------------------------- HUD, légende, carton
def heat_c(day):
    u = clamp(day / 33)
    stops = [(0, "#59E36A"), (.3, "#D7F03A"), (.55, "#FFC531"), (.8, "#FF7A1F"), (.97, "#FF2E2E"), (1, "#FF2EA6")]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if a <= u <= b:
            return hexmix(ca, cb, (u - a) / (b - a))
    return "#FF2EA6"


def fit(s, size, maxw):
    f = skia.Font(TF, size)
    while f.measureText(s) > maxw and size > 20:
        size -= 2
        f = skia.Font(TF, size)
    return size


def nb(n):
    s = "%d" % n
    out = ""
    while len(s) > 3:
        out = " " + s[-3:] + out
        s = s[:-3]
    return s + out


def size_txt(c_):
    if c_ < 99.5:
        return "%d CM" % round(c_)
    m = c_ / 100
    if m < 10:
        return ("%.2f M" % m).replace(".", ",")
    if m < 99.95:
        return ("%.1f M" % m).replace(".", ",")
    if m < 999.5:
        return "%d M" % round(m)
    k = m / 1000
    if k < 99.95:
        return ("%.1f KM" % k).replace(".", ",")
    return "%s KM" % nb(round(k))


assert size_txt(cm(13)) == "410 M" and size_txt(cm(18)) == "13,1 KM" and size_txt(cm(21)) == "105 KM" and size_txt(cm(5)) == "1,60 M"


def hud(c, t, b):
    fin = b["key"] == "fin"
    day = 0 if fin else day_at(t)
    colr = heat_c(day)
    d_ = t - b["start"]
    pop = 1 + .14 * (1 - eout(d_ / .22)) if (b["d1"] != b["d0"]) else 1.0
    c.save()
    c.translate(540, 262)
    c.scale(pop, pop)
    pan = rrect(-420, -135, 420, 135, 44)
    c.drawPath(pan, fill("#14121C", .94))
    c.drawPath(pan, line(colr, 8))
    head = "TAILLE DE BUBULLE 2" if fin else "TAILLE DE BUBULLE"
    big = size_txt(cm(day))
    low = "Jour %d" % round(day)
    text(c, head, 0, -88, fit(head, 38, 770), "#C9C6D8")
    text(c, big, 0, 32, fit(big, 112, 780), colr)
    text(c, low, 0, 106, fit(low, 44, 780), "#FFFFFF")
    c.restore()


def caption(c, t):
    b = beat_at(t)
    if not b["cap"]:
        return
    d_ = t - b["start"]
    s = back(d_ / .17)
    size = 70
    f = skia.Font(TF, size)
    while True:
        lines = wrap_rich(b["cap"], f, 980)
        sp = f.measureText(" ") * 1.6
        wmax = max(sum(f.measureText(w) for w, _ in ln) + sp * (len(ln) - 1) for ln in lines)
        if (wmax <= 1000 and len(lines) <= 2) or size <= 44:
            break
        size -= 2
        f = skia.Font(TF, size)
    lh = size * 1.16
    top = 412
    hgt = lh * len(lines)
    c.save()
    c.translate(540, top + hgt / 2)
    c.scale(s, s)
    c.translate(-540, -(top + hgt / 2))
    y = top + size * .86
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
    c.translate(540, 760)
    c.scale(s, s)
    text(c, "À SUIVRE :", 0, 0, 86, "#FFFFFF")
    text(c, "BUBULLE 2, JOUR 1.", 0, 128, 86, "#FFD93B")
    c.restore()
    a = clamp((d_ - .5) / .25)
    for i, l in enumerate(("Très approximatif : départ à 5 cm,",
                           "×2 par jour, échelle à peu près.",
                           "Record réel : 47,4 cm (Guinness).",
                           "Requin blanc : 6 m. Baleine bleue : 24-30 m.",
                           "Aucun poisson ne grandit comme ça.",
                           "Bubulle va bien.")):
        s_ = fit(l, 44, 960)
        text(c, l, 540, 1060 + i * 62, s_, "#A9A6BC", a=a)


SCN = dict(bocal=scene_bocal, bain=scene_bain, memo=scene_memo, piscine=scene_piscine, mer=scene_mer, paris=scene_paris, fosse=scene_fosse,
           limite=scene_limite, entr=scene_entr, terre=scene_terre, lune=scene_lune, duel=scene_duel, fin=scene_fin)


def shake_amp(t):
    amp = 0
    for tk in JUMPS:
        d_ = t - tk
        if 0 <= d_ < .22:
            amp = max(amp, 9 * (1 - d_ / .22))
    d_ = t - K["fuite"]
    if 0 <= d_ < .5:
        amp = max(amp, 22 * (1 - d_ / .5))
    return amp


def burst(c, t):
    """Flash + cercles d'eau au début de chaque doublement."""
    for tk in JUMPS:
        d_ = t - tk
        if 0 <= d_ < .3:
            a = 1 - d_ / .3
            for k in range(3):
                c.drawCircle(540, 1150, 200 + d_ * 2400 + k * 90, line("#FFFFFF", 10, .6 * a))
            if d_ < .08:
                c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", .6 * (1 - d_ / .08)))


def frame(c, t):
    if t >= CARD:
        card(c, t)
        return
    b = beat_at(t)
    amp = shake_amp(t)
    jx, jy = jitter(t, 2)
    zz = 1 + 2.2 * amp / W
    c.save()
    c.translate(540, 960)
    c.scale(zz, zz)
    c.translate(-540 + jx * amp, -960 + jy * amp)
    SCN[b["ph"]](c, t, b)
    c.restore()
    burst(c, t)
    hud(c, t, b)
    caption(c, t)


_sp = [K["j4"], K["memo"], K["j9"], K["j13"], K["entr"], K["duel"], K["fin"], CARD, END]
SPL = [("s_%d" % i, a, z) for i, (a, z) in enumerate(zip([0] + _sp, _sp))]


def png(t, path):
    from PIL import Image
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    s = skia.Surface(arr)
    with s as c:
        frame(c, t)
    Image.fromarray(arr[..., :3]).save(path)


if __name__ == "__main__":
    print("durée %.1f s, carton %.1f" % (END, CARD))
    print({b["key"]: round(b["start"], 1) for b in BEATS})
    if sys.argv[1:2] == ["png"]:
        os.makedirs("pc", exist_ok=True)
        for ts in sys.argv[2:]:
            png(float(ts), "pc/t%06.2f.png" % float(ts))
    if sys.argv[1:2] == ["keys"]:
        os.makedirs("pc", exist_ok=True)
        for b in BEATS:
            png(b["start"] + b["dur"] * .7, "pc/%05.1f_%s.png" % (b["start"], b["key"]))
        png(CARD + 1.5, "pc/card.png")
    if sys.argv[1:2] == ["render"]:
        only = sys.argv[2:]
        os.makedirs("sc", exist_ok=True)
        for name, a, b in SPL:
            if only and name not in only:
                continue
            f0, f1 = round(a * FPS), round(b * FPS)
            tmp, final = f"sc/{name}.tmp.mp4", f"sc/{name}.mp4"
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
