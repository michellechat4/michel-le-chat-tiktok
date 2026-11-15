"""Michel ne court plus après le laser. Gérard double la puissance chaque jour : 1 mW (classe 2), 1 W (classe 4),
le tapis qui fume, le soleil de midi, l'acier découpé, le mur du voisin, le ciel… puis un point rouge sur la Lune.
Quand Gérard montre la Lune, Michel regarde le doigt."""
import math, random, sys, os, subprocess
import importlib.util as _u
import numpy as np
import skia
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "moteur"))
import art
from art import (fill, line, col, hexmix, poly, rrect, oval, shape, text, jitter, clamp, lerp, eout, ein, back,
                 draw_cat, draw_gerard, draw_couch, draw_moon, earth_rgba, STARS, bubble, wrap_rich, TF, INK, W, H, FPS)

# décor du salon, Gérard debout et outils repris de la vidéo 08
_sp = _u.spec_from_file_location("saut08", os.path.join(HERE, "08_saut.py"))
V8 = _u.module_from_spec(_sp)
_sp.loader.exec_module(V8)
sky_grad, fit, nb, FLOOR, ger_debout, pigeon = V8.sky_grad, V8.fit, V8.nb, V8.FLOOR, V8.ger, V8.pigeon

# ---------------------------------------------------------------- chiffres (calculés, pas recopiés)
P1 = 1e-3                 # W, jour 1 : 1 mW
CLASSE2 = 1e-3            # W, limite d'un laser continu de classe 2 (guide lasers du CNRS, chap. 4)
CLASSE4 = 0.5             # W, la classe 4 commence à 500 mW en continu (Berkeley Lab, EHS)
SOLEIL_SOL = 1000         # W/m², « de l'ordre de 1 000 W/m² » (Connaissance des Énergies, puissance crête)
DECOUPE = (1000, 1500)    # W, découpe de l'acier de 2 mm : fibre de 1 à 1,5 kW (Hellopro)
EPAIS = 6000              # W, « 6 kW et plus pour des plaques épaisses » (Hellopro)
LUNE = 384400             # km, distance moyenne Terre-Lune (valeur standard, déjà utilisée vidéo 08)
C_KM = 299792.458         # km/s, vitesse de la lumière
TACHE = 1.9               # km, faisceau d'1 seconde d'arc sur la Lune (T. Murphy, « Lunar Laser Ranging: the millimeter challenge »)
SOLEIL_LUNE = 1361        # W/m², constante solaire (valeur standard ; la Lune n'a pas d'atmosphère)


def pw(d):
    return P1 * 2 ** (d - 1)


AIRE = math.pi * (TACHE * 1000 / 2) ** 2          # m²
ECL = lambda d: pw(d) / AIRE                       # W/m² dans la tache (pertes dans l'air ignorées)
T_LUM = LUNE / C_KM

assert pw(1) == CLASSE2 and pw(9) < CLASSE4 <= pw(10) and round(pw(10) * 1000) == 512
assert round(pw(6) * 1000) == 32 and round(pw(17), 1) == 65.5
assert pw(20) < SOLEIL_SOL < pw(21) and round(pw(21)) == 1049
assert DECOUPE[1] < pw(22) and pw(23) < EPAIS < pw(24) and round(pw(24)) == 8389
assert round(pw(26)) == 33554 and round(pw(28)) == 134218
assert round(pw(43) / 1e9, 2) == 4.40
assert round(AIRE / 1e6, 2) == 2.84
assert ECL(42) < SOLEIL_LUNE < ECL(43) and round(ECL(43)) == 1551
assert round(T_LUM, 1) == 1.3


def fr(x, n=0):
    return (("%." + str(n) + "f") % x).replace(".", ",")


# ---------------------------------------------------------------- chronologie
# (clé, durée, jour, légende, Gérard dit, décor)
RAW = [
    ("hook", 3.0, 1, "GÉRARD VA METTRE UN POINT ROUGE | *SUR LA LUNE.*", None, "lune"),
    ("regle", 3.4, 1, "Michel ne court plus après le laser. | Gérard *double la puissance* chaque jour.", "Allez, Michel !", "salon"),
    ("j1", 3.2, 1, "Jour 1 : 1 milliwatt. | *Un laser de classe 2.*", None, "salon"),
    ("loi", 3.6, 1, "En France, au-delà de la classe 2 : | *réservé à des usages pros.*", None, "salon"),
    ("veto", 3.6, 1, "Conseil de véto : finir le jeu | par *une vraie proie à attraper.*", "Il s'en fiche.", "salon"),
    ("j6", 3.0, 6, "Jour 6 : %d milliwatts. | Michel *bâille.*" % round(pw(6) * 1000), None, "salon"),
    ("j10", 3.4, 10, "Jour 10 : %d milliwatts. | *Classe 4 : danger pour les yeux.*" % round(pw(10) * 1000), "Lunettes !", "salon"),
    ("j17", 3.4, 17, "Jour 17 : %s watts. | *Le tapis fume.*" % fr(pw(17), 1), None, "salon"),
    ("j21", 3.6, 21, "Jour 21 : %s watts. | Le soleil de midi *sur 1 m².*" % nb(round(pw(21))), None, "salon"),
    ("j24", 3.6, 24, "Jour 24 : %s watts. | De quoi *découper de l'acier épais.*" % nb(round(pw(24))), None, "salon"),
    ("j26", 3.4, 26, "Jour 26 : %s watts. | Le point rouge *passe chez le voisin.*" % nb(round(pw(26))), None, "salon"),
    ("michel", 2.8, 26, "Michel n'a *rien fait.*", None, "salon"),
    ("j28", 3.2, 28, "Jour 28 : %s watts. | Gérard vise *le ciel.*" % nb(round(pw(28))), None, "salon"),
    ("j43", 3.8, 43, "Jour 43 : %s milliards de watts. | *Un point rouge sur la Lune.*" % fr(pw(43) / 1e9, 1), None, "lune"),
    ("dist", 3.4, 43, "%s km. | La lumière y va *en %s seconde.*" % (nb(LUNE), fr(T_LUM, 1)), None, "lune"),
    ("calc", 3.8, 43, "Une tache de 2 km, plus lumineuse | *que le Soleil sur la Lune.*", None, "lune"),
    ("doigt", 3.6, 43, "Quand Gérard montre la Lune, | *Michel regarde le doigt.*", None, "lune"),
    ("fin", 3.4, 43, "Enfin, une proie | *qu'il peut attraper.*", "AÏE !", "lune"),
    ("fin2", 2.8, 43, "Jour 44 ?", "Mars.", "lune"),
]
CARD_DUR = 4.0
BEATS = []
_t, _d = 0.0, 1
for key, dur, d, cap, ger_, dec in RAW:
    BEATS.append(dict(key=key, start=_t, dur=dur, d0=_d, d1=d, cap=cap, ger=ger_, dec=dec))
    _t += dur
    _d = d
CARD = _t
END = CARD + CARD_DUR
K = {b["key"]: b["start"] for b in BEATS}
JUMPS = sorted(b["start"] for b in BEATS if b["d1"] > b["d0"])
ROLL = .7


def beat_at(t):
    cur = BEATS[0]
    for b in BEATS:
        if b["start"] <= t:
            cur = b
        else:
            break
    return cur


def d_at(t):
    b = beat_at(t)
    f = eout((t - b["start"]) / ROLL)
    if b["d1"] <= b["d0"] or f >= 1:
        return b["d1"]
    return lerp(b["d0"], b["d1"], f)


# ---------------------------------------------------------------- éléments
HX, HY = 790, 1000          # tête de Gérard assis
MCX, MCY, MS = 330, 1318, .55
HAND = (575, 1185)          # main droite de Gérard assis
WALL_HOLE = (470, 975)      # trou dans le mur (jour 24-26)
WIN = (190, 1050)           # fenêtre


def red_dot(c, x, y, d, t, a=1.0):
    """Point rouge : taille et halo croissent avec la puissance (échelle log)."""
    u = clamp((d - 1) / 42)
    r = 13 + 20 * u
    gl = 30 + 160 * u
    fl = 1 + .08 * math.sin(t * 37) + .05 * math.sin(t * 23)
    p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((x, y), gl * fl, [col("#FF2A2A", .55 * a), col("#FF2A2A", 0)]))
    c.drawCircle(x, y, gl * fl, p)
    c.drawCircle(x, y, r * fl, fill("#FF3030", a))
    c.drawCircle(x, y, r * .5 * fl, fill(hexmix("#FFB0B0", "#FFFFFF", u), a))


def beam(c, x0, y0, x1, y1, d, a=1.0):
    u = clamp((d - 1) / 42)
    w_ = 2 + 16 * u
    c.drawLine(x0, y0, x1, y1, line("#FF3030", w_ * 2.4, (.08 + .25 * u) * a))
    c.drawLine(x0, y0, x1, y1, line("#FF4A4A", w_, (.25 + .5 * u) * a))
    if u > .5:
        c.drawLine(x0, y0, x1, y1, line("#FFD6D6", w_ * .35, a))


def pen(c, x, y, ang, s=1.0, d=1):
    """Pointeur laser tenu en (x, y), orienté ang (radians)."""
    c.save()
    c.translate(x, y)
    c.rotate(math.degrees(ang))
    c.scale(s, s)
    big = clamp((d - 20) / 10)
    L_ = 70 + 50 * big
    R_ = 11 + 9 * big
    shape(c, rrect(-30, -R_, L_, R_, R_ * .8), hexmix("#9AA0B5", "#3A3F55", big), 5)
    c.drawCircle(L_ - 4, 0, R_ * .5, fill("#FF3030"))
    c.drawRect(skia.Rect.MakeLTRB(0, -R_ - 2, 14, -R_ + 4), fill("#FF5A3B"))
    c.restore()
    return x + math.cos(ang) * (L_ - 4) * s, y + math.sin(ang) * (L_ - 4) * s


def goggles(c, x, y):
    for sg in (-1, 1):
        shape(c, oval(x + sg * 38 - 36, y - 46, x + sg * 38 + 36, y + 22), "#2FD07A", 6, .55)
    c.drawLine(x - 74, y - 12, x - 104, y - 6, line(INK, 10))
    c.drawLine(x + 74, y - 12, x + 104, y - 6, line(INK, 10))


def smoke(c, x, y, t, n=4, a=1.0, scale=1.0):
    for k in range(n):
        ph = (t * .7 + k / n) % 1
        c.drawCircle(x + math.sin(t * 2 + k * 2) * 20 * scale, y - ph * 220 * scale, (14 + 30 * ph) * scale, fill("#8E8A90", .5 * (1 - ph) * a))


def sparks(c, x, y, t, n=16, a=1.0):
    rr = random.Random(int(t * 30))
    for k in range(n):
        an = rr.uniform(-math.pi, 0)
        ln = rr.uniform(30, 120)
        c.drawLine(x, y, x + math.cos(an) * ln, y + math.sin(an) * ln + 30, line(rr.choice(("#FFE14D", "#FFFFFF", "#FF8A1F")), 4, a))


def mouse_toy(c, x, y, s=1.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    p = skia.Path()
    p.moveTo(40, -6)
    p.quadTo(80, -30, 110, 0)
    c.drawPath(p, line(INK, 6))
    shape(c, oval(-50, -40, 46, 10), "#B5BACB", 6)
    shape(c, oval(-56, -60, -24, -28), "#FFA6A6", 5)
    c.drawCircle(-34, -20, 5, fill(INK))
    c.restore()


def dot_path(t, key, d_):
    """Où vise Gérard dans le salon."""
    if key in ("j24",):
        return WALL_HOLE[0] + math.cos(d_ * 2.6) * 70, WALL_HOLE[1] + math.sin(d_ * 2.6) * 55
    if key in ("j26", "michel"):
        return WALL_HOLE
    if key == "j28":
        u = eout(clamp(d_ / .8))
        return lerp(500, WIN[0], u), lerp(1620, WIN[1], u)
    # au sol, devant le canapé : le point se balade
    x = 560 + 230 * math.sin(t * 1.3) + 60 * math.sin(t * 3.1)
    y = 1625 + 25 * math.sin(t * 2.2)
    if key == "j17" or key == "j21":
        x = 560 + 90 * math.sin(t * .6)
    return x, y


def scorch(c, d):
    if d < 16.5:
        return
    rr = random.Random(3)
    n = int(min(9, (d - 16) * 2))
    for k in range(n):
        x = rr.uniform(330, 800)
        y = 1620 + rr.uniform(-20, 25)
        c.drawOval(skia.Rect.MakeLTRB(x - 34, y - 10, x + 34, y + 10), fill("#2A1A14", .55))


def wall_cut(c, t, key, d_):
    """Découpe circulaire dans le mur (jours 24 à 28)."""
    x, y = WALL_HOLE
    if key == "j24":
        prog = clamp(d_ / 3.2)
        p = skia.Path()
        p.addArc(skia.Rect.MakeLTRB(x - 70, y - 55, x + 70, y + 55), 0, 360 * prog)
        c.drawPath(p, line("#2A1A14", 10))
        c.drawPath(p, line("#FF8A1F", 4, .8))
        return
    # trou percé : on voit chez le voisin
    c.drawOval(skia.Rect.MakeLTRB(x - 72, y - 57, x + 72, y + 57), fill("#3B2E4A"))
    c.save()
    c.clipPath(oval(x - 72, y - 57, x + 72, y + 57), skia.ClipOp.kIntersect, True)
    if key in ("j26", "michel"):
        # yeux du voisin
        for sg in (-1, 1):
            c.drawCircle(x + sg * 24, y + 8, 15, fill("#FFFFFF"))
            c.drawCircle(x + sg * 24 + 3, y + 10, 7, fill(INK))
        c.drawLine(x - 42, y - 22, x - 10, y - 10, line("#FFFFFF", 6))
        c.drawLine(x + 42, y - 22, x + 10, y - 10, line("#FFFFFF", 6))
    c.restore()
    c.drawOval(skia.Rect.MakeLTRB(x - 72, y - 57, x + 72, y + 57), line(INK, 7))
    c.drawOval(skia.Rect.MakeLTRB(x - 78, y - 62, x + 78, y + 62), line("#2A1A14", 6, .6))


# ---------------------------------------------------------------- panneaux (zone du mur)
PY0, PY1 = 640, 880


def panel(c, a=1.0, y0=PY0, y1=PY1):
    p = rrect(60, y0, 1020, y1, 34)
    c.drawPath(p, fill("#14121C", .92 * a))
    c.drawPath(p, line("#FFFFFF", 6, a))


def panel_loi(c, t, d_):
    a = clamp((d_ - .3) / .25)
    if a <= 0:
        return
    panel(c, a)
    text(c, "CLASSE 2 : 1 mW MAXIMUM", 540, 722, 54, "#59E36A", INK, 9, a=a)
    text(c, "au-delà : vente réservée", 540, 790, 42, "#FFFFFF", a=a)
    text(c, "à une liste d'usages professionnels", 540, 846, 36, "#C9C6D8", a=a)


def panel_c4(c, t, d_):
    a = clamp((d_ - .5) / .25)
    if a <= 0:
        return
    panel(c, a)
    shape(c, poly([(170, 690), (240, 820), (100, 820)]), "#FFE14D", 6, a)
    text(c, "!", 170, 808, 80, INK, a=a)
    text(c, "CLASSE 4 : DÈS 500 mW", 620, 740, 54, "#FF5A3B", INK, 9, a=a)
    text(c, "yeux, peau, risque d'incendie", 620, 812, 40, "#FFFFFF", a=a)


def sun_icon(c, x, y, r, t, a=1.0):
    for k in range(12):
        an = k / 12 * 6.283 + t * .5
        c.drawLine(x + math.cos(an) * r * 1.2, y + math.sin(an) * r * 1.2, x + math.cos(an) * r * 1.6, y + math.sin(an) * r * 1.6, line("#FFC531", 8, a))
    shape(c, oval(x - r, y - r, x + r, y + r), "#FFE14D", 6, a)


def panel_soleil(c, t, d_):
    a = clamp((d_ - .6) / .25)
    if a <= 0:
        return
    panel(c, a)
    sun_icon(c, 170, 760, 50, t, a)
    text(c, "SOLEIL DE MIDI :", 330, 735, 40, "#FFFFFF", align="left", a=a)
    text(c, "environ 1 000 W / m²", 330, 795, 56, "#FFE14D", INK, 9, align="left", a=a)
    text(c, "LASER : %s W" % nb(round(pw(21))), 330, 852, 40, "#FF5A5A", INK, 7, align="left", a=a)


def panel_acier(c, t, d_):
    a = clamp((d_ - .6) / .25)
    if a <= 0:
        return
    panel(c, a)
    text(c, "DÉCOUPE LASER DE L'ACIER", 540, 712, 46, "#FFFFFF", INK, 7, a=a)
    text(c, "1 à 1,5 kW : tôle de 2 mm", 540, 782, 44, "#C9C6D8", a=a)
    text(c, "6 kW et + : plaques épaisses", 540, 846, 44, "#FFE14D", INK, 7, a=a)


# ---------------------------------------------------------------- salon
def ger_arm(c, tip, sw="#3F6FD8"):
    arm = skia.Path()
    arm.moveTo(712, 1150)
    arm.quadTo(650, 1230, tip[0], tip[1])
    c.drawPath(arm, line(INK, 60))
    c.drawPath(arm, line(sw, 46))
    art.draw_mitt(c, tip[0], tip[1], .42)


def scene_salon(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    day = d_at(t)
    V8.salon(c, t, b, night=False, holed=False)
    if key in ("j24", "j26", "michel", "j28"):
        wall_cut(c, t, key, d_)
    scorch(c, day)
    draw_couch(c)
    # Michel couché, blasé
    mood = "bliss"
    if key == "michel" and d_ > .5:
        mood = "wink"
    if key == "j6" and 1.0 < d_ < 2.4:
        mood = "bliss"
    vib = 0
    draw_cat(c, MCX, MCY, MS, t, mood, vib)
    if key == "j6" and 1.0 < d_ < 2.4:
        # bâillement
        u = math.sin(clamp((d_ - 1.0) / 1.4) * math.pi)
        c.drawOval(skia.Rect.MakeLTRB(MCX - 20 * u, MCY - 130 - 30 * u, MCX + 20 * u, MCY - 112 + 10 * u), fill("#8A2F3A"))
        text(c, "*bâille*", MCX, MCY - 260, 40, "#FFFFFF", INK, 7, a=u)
    if key in ("regle", "j1", "loi", "j6", "j10") and int(t * 1.2) % 3 == 0:
        for k in range(3):
            ph = (t * .8 + k / 3) % 1
            text(c, "z", MCX + 70 + ph * 60, MCY - 230 - ph * 100, 30 + 20 * ph, "#FFFFFF", INK, 5, a=1 - ph)
    if key == "veto":
        u = back(clamp((d_ - .2) / .3))
        mouse_toy(c, 560, 1640, .9 * u)
    # Gérard assis, bras tendu, laser
    stage = 0
    if key in ("j17", "j21", "j24"):
        stage = 2
    if key in ("j26", "michel"):
        stage = 3 if d_ < 1.5 else 2
    draw_gerard(c, stage, t, False, 0, True)
    if day >= 9.5:
        goggles(c, HX, HY)
    tx, ty = dot_path(t, key, d_)
    ang = math.atan2(ty - HAND[1], tx - HAND[0])
    ger_arm(c, HAND)
    tip = pen(c, HAND[0], HAND[1] - 10, ang, .9, day)
    if key == "j28":
        # le faisceau sort par la fenêtre et monte dans le ciel
        beam(c, tip[0], tip[1], tx, ty, day)
        u = eout(clamp((d_ - .6) / .5))
        if u > 0:
            c.save()
            c.clipPath(skia.Path().addRect(skia.Rect.MakeLTRB(70, 980, 310, 1280)), skia.ClipOp.kIntersect, True)
            beam(c, WIN[0], WIN[1], lerp(WIN[0], 40, u), lerp(WIN[1], 900, u), day)
            pigeon(c, 110 + 150 * clamp((d_ - 1.2) / 1.5), 1200 - 100 * clamp((d_ - 1.2) / 1.5), .9, t)
            c.restore()
            if d_ > 1.6:
                bubble(c, 300, 920, "ROUCOU ?!", 44, back((d_ - 1.6) / .16), -5)
        red_dot(c, tx, ty, day, t, .7)
    else:
        beam(c, tip[0], tip[1], tx, ty, day)
        red_dot(c, tx, ty, day, t)
    if day >= 16.5 and key not in ("j28",):
        smoke(c, tx, ty - 10, t, 4, clamp((day - 16.5) / 1), 1 + .02 * (day - 17))
    if key in ("j24", "j26"):
        sparks(c, tx, ty, t, 18)
    if day >= 20.5:
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#FF3030", .06 + .04 * math.sin(t * 20)))
    if key == "j26" and d_ > .9:
        bubble(c, 300, 840 + 60, "MICHEL !!!", 56, back((d_ - .9) / .16), -6)
    if key == "michel":
        bubble(c, 300, 900, "MICHEL !!!", 56, 1.0, -6)
        if d_ > .8:
            text(c, "?", MCX + 120, MCY - 300, 90, "#FFE14D", INK, 10, a=clamp((d_ - .8) / .15))
    # panneaux
    if key == "loi":
        panel_loi(c, t, d_)
    elif key == "j10":
        panel_c4(c, t, d_)
    elif key == "j21":
        panel_soleil(c, t, d_)
    elif key == "j24":
        panel_acier(c, t, d_)
    # bulle de Gérard
    if b["ger"]:
        f = skia.Font(TF, 52)
        w = f.measureText(b["ger"])
        bx = clamp(HX + 20, w / 2 + 44, W - w / 2 - 44)
        by = HY - 190
        if key == "j10":
            bx, by = 330, 1000
        bubble(c, bx, by, b["ger"], 52, back((d_ - .4) / .16), 3)


# ---------------------------------------------------------------- dehors, la nuit
MOON = (560, 850, 165)
SPOT = (MOON[0] - 50, MOON[1] + 40)
G = 1620
GX, GS = 770, .6        # Gérard debout
MX_, MSC = 330, .36      # Michel


def hand_pos():
    return GX + (640 - 790) * GS, G + (1010 - 1516) * GS


def scene_lune(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    day = 43
    c.drawImage(STARS, 0, 0)
    # Lune
    face = "angry" if key in ("j43", "dist", "calc", "hook") else "scared"
    draw_moon(c, MOON[0], MOON[1], MOON[2], t, face)
    # sol : jardin, toits
    for (x, w_, h_) in ((-60, 260, 210), (850, 300, 260)):
        art.draw_house(c, x, w_, h_, G, "#2C3550", "#1E2440")
    c.drawRect(skia.Rect.MakeLTRB(0, G, W, H), fill("#24432E"))
    c.drawLine(0, G, W, G, line(INK, 6))
    hx, hy = hand_pos()
    laser_on = key in ("hook", "j43", "dist", "calc") or (key == "doigt" and d_ < .6)
    pointing = key in ("hook", "j43", "dist", "calc", "doigt")
    # Gérard debout, bras levé
    stage = 0
    if key == "fin":
        stage = 3
    if key == "hook":
        stage = 1
    ger_debout(c, GX, G, GS, t, stage, "laser" if key != "fin2" else None)
    ang = math.atan2(SPOT[1] - hy, SPOT[0] - hx)
    if key != "fin2":
        if key == "fin":
            # le laser tombe
            u = clamp((d_ - .3) / .5)
            px, py = hx - 30 * u, lerp(hy, G - 10, u * u)
            pen(c, px, py, ang + u * 3, .5, day)
        elif key == "doigt" and d_ > .6:
            # Gérard pointe la Lune du doigt
            c.save()
            c.translate(hx, hy)
            c.rotate(math.degrees(ang))
            shape(c, rrect(0, -9, 60, 9, 9), "#F7C7A0", 5)
            c.restore()
        else:
            tip = pen(c, hx, hy, ang, .5, day)
            if laser_on:
                on = eout(clamp(d_ / .5)) if key == "j43" else 1
                ex, ey = lerp(tip[0], SPOT[0], on), lerp(tip[1], SPOT[1], on)
                beam(c, tip[0], tip[1], ex, ey, day, .9)
                if on >= 1:
                    red_dot(c, SPOT[0], SPOT[1], 14, t)
    # Michel
    if key == "fin" or key == "fin2":
        if key == "fin":
            u = clamp(d_ / .45)
            mx = lerp(MX_, hx, eout(u))
            my = lerp(G, hy + 70, eout(u)) - math.sin(u * math.pi) * 200
            draw_cat(c, mx, my, MSC * .9, t, "open" if u < 1 else "wink", 4 if u >= 1 else 0)
            if u >= 1:
                text(c, "CRONCH", hx - 120, hy - 150, 54, "#FFE14D", INK, 9, a=clamp((d_ - .45) / .1))
        else:
            # pansement sur la main, Michel ravi
            shape(c, rrect(hx - 20, hy - 12, hx + 20, hy + 12, 6), "#F2D7B5", 4)
            draw_cat(c, MX_ + 40, G, MSC, t, "bliss")
    else:
        look = key == "doigt"
        mood = "open" if look else "bliss"
        draw_cat(c, MX_, G, MSC, t, mood)
        if look and d_ > 1.0:
            text(c, "!", MX_ + 70, G - 150, 90, "#FFE14D", INK, 10, a=clamp((d_ - 1.0) / .12))
            # regard : pointillés vers le doigt, pas vers la Lune
            c.drawPath(skia.Path().moveTo(MX_ + 30, G - 80).lineTo(hx - 10, hy + 10),
                       skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5, Color=col("#FFE14D", .8),
                                  PathEffect=skia.DashPathEffect.Make([16, 12], -t * 60)))
    # panneaux (sous la Lune)
    if key == "dist":
        a = clamp((d_ - .3) / .25)
        panel(c, a, 1040, 1250)
        ex = 160
        img, x0, y0 = earth_rgba(46, cx=ex, cy=1145)
        c.drawImage(img, x0, y0)
        c.drawCircle(ex, 1145, 46, line(INK, 5))
        draw_moon(c, 920, 1145, 30, t, "scared")
        u = clamp((d_ - .5) / T_LUM)
        c.drawLine(ex + 50, 1145, lerp(ex + 50, 885, u), 1145, line("#FF4A4A", 8, a))
        text(c, "%s km" % nb(LUNE), 540, 1118, 46, "#FFFFFF", INK, 7, a=a)
        text(c, "lumière : %s s" % fr(T_LUM, 1), 540, 1222, 44, "#FFE14D", INK, 7, a=a)
    if key == "calc":
        a = clamp((d_ - .4) / .25)
        panel(c, a, 1030, 1250)
        text(c, "TACHE : %s km (air agité)" % fr(TACHE, 1), 540, 1092, 44, "#FFFFFF", INK, 7, a=a)
        text(c, "LASER : %s W/m²" % nb(round(ECL(43))), 540, 1160, 54, "#FF5A5A", INK, 9, a=a)
        text(c, "SOLEIL : %s W/m²" % nb(SOLEIL_LUNE), 540, 1226, 54, "#FFE14D", INK, 9, a=a)
    if b["ger"]:
        f = skia.Font(TF, 52)
        w = f.measureText(b["ger"])
        bx = clamp(GX + 40, w / 2 + 44, W - w / 2 - 44)
        bubble(c, bx, G - 330, b["ger"], 52, back((d_ - .4) / .16), 3)


# ---------------------------------------------------------------- HUD, légende, carton
def heat_c(d):
    u = clamp((d - 1) / 42)
    stops = [(0, "#59E36A"), (.3, "#D7F03A"), (.55, "#FFC531"), (.8, "#FF7A1F"), (.92, "#FF2E2E"), (1, "#FF2EA6")]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if a <= u <= b:
            return hexmix(ca, cb, (u - a) / (b - a))
    return "#FF2EA6"


def big_txt(d):
    p = pw(d)
    if p < .9995:
        m = round(p * 1000)
        return "%d MILLIWATT%s" % (m, "S" if m > 1 else "")
    if p < 9.995:
        return fr(p, 2) + " WATT" + ("S" if p >= 2 else "")
    if p < 99.95:
        return fr(p, 1) + " WATTS"
    if p < 999999.5:
        return nb(round(p)) + " WATTS"
    if p < 1e9:
        q = p / 1e6
        return (fr(q, 1) if q < 9.95 else "%d" % round(q)) + " MILLIONS DE W"
    q = p / 1e9
    return fr(q, 2) + (" MILLIARD DE W" if q < 2 else " MILLIARDS DE W")


assert big_txt(1) == "1 MILLIWATT" and big_txt(6) == "32 MILLIWATTS" and big_txt(10) == "512 MILLIWATTS" and big_txt(11) == "1,02 WATT"
assert big_txt(17) == "65,5 WATTS" and big_txt(21) == "1 049 WATTS" and big_txt(43) == "4,40 MILLIARDS DE W"


def low_txt(d):
    dd = round(d)
    if pw(d) <= CLASSE2 * 1.0001:
        return "Jour n° %d · classe 2" % dd
    if pw(d) >= CLASSE4:
        return "Jour n° %d · classe 4" % dd
    return "Jour n° %d" % dd


def hud(c, t, b):
    d = d_at(t)
    hook = b["key"] == "hook"
    colr = heat_c(43 if hook else d)
    d_ = t - b["start"]
    pop = 1 + .14 * (1 - eout(d_ / .22)) if b["d1"] != b["d0"] else 1.0
    c.save()
    c.translate(540, 262)
    c.scale(pop, pop)
    pan = rrect(-420, -135, 420, 135, 44)
    c.drawPath(pan, fill("#14121C", .94))
    c.drawPath(pan, line(colr, 8))
    head = "PUISSANCE DU LASER DE GÉRARD"
    big = "DE 1 mW À LA LUNE ?" if hook else big_txt(d)
    low = "×2 chaque jour" if hook else low_txt(d)
    text(c, head, 0, -88, fit(head, 38, 770), "#C9C6D8")
    text(c, big, 0, 32, fit(big, 108, 780), colr)
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


CARD_LINES = ("Très approximatif : 1 mW le jour 1, ×2 chaque jour.",
              "Classe 2 : 1 mW max (CNRS). Classe 4 : dès 500 mW (Berkeley Lab).",
              "France : au-delà de la classe 2, usages pros seulement (DGCCRF).",
              "Soleil au sol : environ 1 000 W/m². Découpe d'acier : 1 à 6 kW et +.",
              "Lune : 384 400 km. Tache : 1,9 km (Murphy, télémétrie laser).",
              "Soleil sur la Lune : 1 361 W/m². Pertes dans l'air ignorées.",
              "Ne visez jamais les yeux (ni ceux du chat), ni le ciel.")


def card(c, t):
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#000000"))
    d_ = t - CARD
    if d_ < .2:
        return
    s = back((d_ - .2) / .22)
    c.save()
    c.translate(540, 720)
    c.scale(s, s)
    text(c, "À SUIVRE :", 0, 0, 86, "#FFFFFF")
    text(c, "JOUR N° 44 : MARS.", 0, 128, 86, "#FF5A5A")
    c.restore()
    a = clamp((d_ - .5) / .25)
    for i, l in enumerate(CARD_LINES):
        text(c, l, 540, 1000 + i * 62, fit(l, 42, 980), "#A9A6BC", a=a)


def shake_amp(t):
    amp = 0
    for tk in JUMPS:
        d_ = t - tk
        if 0 <= d_ < .22:
            amp = max(amp, 9 * (1 - d_ / .22))
    tf = K["fin"] + .45
    if 0 <= t - tf < .25:
        amp = max(amp, 14 * (1 - (t - tf) / .25))
    return amp


def burst(c, t):
    for tk in JUMPS:
        d_ = t - tk
        if 0 <= d_ < .07:
            c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", .5 * (1 - d_ / .07)))


SCN = dict(salon=scene_salon, lune=scene_lune)


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
    SCN[b["dec"]](c, t, b)
    c.restore()
    burst(c, t)
    hud(c, t, b)
    caption(c, t)


_sp = [K["j10"], K["j24"], K["j43"], CARD, END]
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
