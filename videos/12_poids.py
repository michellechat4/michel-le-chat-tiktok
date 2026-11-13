"""Le poids de Michel double à chaque croquette (sa taille, non) : plancher, baleine, tours Eiffel, centre de la Terre, trou noir."""
import math, random, sys, os, subprocess
import importlib.util as _u
import numpy as np
import skia
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "moteur"))
import art
from art import (fill, line, col, hexmix, poly, rrect, oval, shape, text, jitter, clamp, lerp, eout, ein, back,
                 draw_cat, draw_gerard, draw_couch, draw_eiffel, draw_moon, earth_rgba, STARS, bubble, wrap_rich, TF, INK, W, H, FPS)

# décors et Gérard debout repris de la vidéo 08 (salon, fenêtre, ger, bulle)
_sp = _u.spec_from_file_location("saut08", os.path.join(HERE, "08_saut.py"))
V8 = _u.module_from_spec(_sp)
_sp.loader.exec_module(V8)
ger, gerbub, sky_grad, fit, nb = V8.ger, V8.gerbub, V8.sky_grad, V8.fit, V8.nb
FLOOR, MX = V8.FLOOR, V8.MX

# ---------------------------------------------------------------- chiffres (calculés, pas recopiés)
M0 = 4.5                 # kg, Michel au départ ; chat adulte : 3,5 à 5,5 kg (PetsCare)
GERARD = 70              # kg, Gérard (personnage, chiffre inventé)
PLANCHER = 150           # kg/m², charge d'exploitation courante d'un logement (1,5 kN/m², valeur usuelle, forum Futura)
BALEINE = (120e3, 170e3) # kg, baleine bleue : 120 à 170 t (Futura)
EIFFEL_T = 10100e3       # kg, tour Eiffel installations comprises (dossier de presse SETE, 2024)
NOYAU_C = 5500           # °C, noyau interne ≈ surface du Soleil (Futura, 2026)
R_TERRE = 6371           # km, rayon moyen
M_TERRE, M_LUNE = 5.972e24, 7.346e22
G_, C_ = 6.674e-11, 2.998e8
TAILLE = .50             # m, Michel en boule (estimation)


def kg(n):
    return M0 * 2 ** n


def rs(m):
    return 2 * G_ * m / C_ ** 2


def poids_gerard(n):
    """Michel au centre de la Terre : g en surface × (1 + m/M_Terre)."""
    return GERARD * (1 + kg(n) / M_TERRE)


assert kg(3) < GERARD < kg(4) == 72
assert kg(8) == 1152 and BALEINE[0] < kg(15) < BALEINE[1] and round(kg(15) / 1000) == 147
assert .9 < kg(22) / (2 * EIFFEL_T) < .95 and round(kg(22) / 1000, -2) == 18900
assert kg(73) < M_LUNE < kg(74) and round(poids_gerard(74) - GERARD) == 1
assert .9 < kg(80) / M_TERRE < 1 < kg(81) / M_TERRE and round(poids_gerard(80)) == 134
assert rs(kg(84)) < TAILLE / 2 < rs(kg(85)) and round(kg(85) / M_TERRE) == 29

# ---------------------------------------------------------------- chronologie
# (clé, durée, croquette, légende, Gérard dit, décor)
RAW = [
    ("hook", 3.0, 0, "CE CHAT VA DEVENIR | *UN TROU NOIR.*", None, "salon"),
    ("regle", 3.4, 0, "À chaque croquette, son poids | *double.* Sa taille, non.", "Michel, non.", "salon"),
    ("c0", 3.2, 0, "Croquette 0 : 4,5 kg. Un chat | adulte : *3,5 à 5,5 kg.*", None, "salon"),
    ("c4", 3.2, 4, "Croquette 4 : 72 kg. | *Plus lourd que Gérard.*", "J'en fais 70 !", "salon"),
    ("c8", 3.6, 8, "Croquette 8 : 1,15 tonne. | Un plancher : *150 kg par m².*", "MON PLANCHER !", "salon"),
    ("veto", 3.0, 8, "Gérard appelle *le véto.*", "Il pèse une tonne.", "salon"),
    ("c15", 3.4, 15, "Croquette 15 : 147 tonnes. | Autant qu'*une baleine bleue.*", None, "balance"),
    ("c22", 3.6, 22, "Croquette 22 : 18 900 tonnes. | *Presque deux tours Eiffel.*", None, "balance"),
    ("sol", 3.2, 23, "Le sol ne tient plus. | Michel *s'enfonce.*", "Michel ?", "sol"),
    ("centre", 3.2, 23, "Il s'arrête | *au centre de la Terre.*", None, "coupe"),
    ("chaud", 3.4, 23, "Il y fait *5 500 °C.* Comme | la surface du Soleil. *Il adore.*", None, "coupe"),
    ("ficelle", 3.6, 73, "Gérard descend les croquettes. | Ficelle : *6 371 km.*", None, "coupe"),
    ("c74", 3.4, 74, "Croquette 74 : Michel est | *plus lourd que la Lune.*", None, "espace"),
    ("gkg", 3.4, 74, "En haut, Gérard prend *1 kg.* | Il accuse le fromage.", "C'est le brie.", "salon"),
    ("c80", 3.6, 80, "Croquette 80 : *presque une Terre.* | Gérard pèse 134 kg.", "Je reste assis.", "salon"),
    ("c85", 3.4, 85, "Croquette 85 : 29 Terres | dans *50 cm de chat.*", None, "espace"),
    ("bh", 3.4, 85, "Michel devient | *un trou noir.*", None, "trou"),
    ("calme", 3.2, 85, "Gérard tourne autour. | *Très calme.*", None, "trou"),
    ("fin", 3.8, 85, "Croquette 86 ?", "NON.", "trou"),
]
CARD_DUR = 3.6
BEATS = []
_t, _n = 0.0, 0
for key, dur, n, cap, ger_, ph_ in RAW:
    BEATS.append(dict(key=key, start=_t, dur=dur, n0=_n, n1=n, cap=cap, ger=ger_, ph=ph_))
    _t += dur
    _n = n
CARD = _t
END = CARD + CARD_DUR
K = {b["key"]: b["start"] for b in BEATS}
JUMPS = sorted(b["start"] for b in BEATS if b["n1"] > b["n0"] and b["key"] != "ficelle")
ROLL = .7


def beat_at(t):
    cur = BEATS[0]
    for b in BEATS:
        if b["start"] <= t:
            cur = b
        else:
            break
    return cur


def n_at(t):
    b = beat_at(t)
    if b["key"] == "ficelle":
        f = clamp((t - b["start"] - .3) / (b["dur"] - .6))
        return lerp(b["n0"], b["n1"], f)
    f = eout((t - b["start"]) / ROLL)
    if b["n1"] <= b["n0"] or f >= 1:
        return b["n1"]
    return lerp(b["n0"], b["n1"], f)


# ---------------------------------------------------------------- objets
def scale_pad(c, x, y, s, val, a=1.0, broken=0.0):
    """Pèse-personne posé au sol (y = sol), affichage val."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    if broken > 0:
        c.rotate(-6 * broken)
    shape(c, rrect(-150, -46, 150, 0, 22), "#E9ECF4", 7)
    shape(c, rrect(-70, -40, 70, -10, 8), "#1C2B24", 5)
    f = skia.Font(TF, 30)
    w = f.measureText(val)
    c.drawString(val, -w / 2, -14, f, fill("#7CFF9B"))
    if broken > 0:
        for k in range(4):
            c.drawLine(-120 + k * 70, -46, -100 + k * 70, -4, line(INK, 4))
    c.restore()


def floor_hole(c, a=1.0):
    p = oval(MX - 190, FLOOR - 26, MX + 190, FLOOR + 52)
    c.drawPath(p, fill("#1A0F0C", a))
    c.drawPath(p, line(INK, 7, a))
    r = random.Random(4)
    for k in range(9):
        ang = math.pi * 2 * k / 9 + r.uniform(-.2, .2)
        x0, y0 = MX + math.cos(ang) * 190, FLOOR + 13 + math.sin(ang) * 39
        c.drawLine(x0, y0, x0 + math.cos(ang) * r.uniform(60, 140), y0 + math.sin(ang) * r.uniform(15, 40), line(INK, 6, a))


def ger_sq(c, x, floor, s, t, stage, sx=1.0, sy=1.0):
    c.save()
    c.translate(x, floor)
    c.scale(sx, sy)
    c.translate(-x, -floor)
    ger(c, x, floor, s, t, stage)
    c.restore()


def scene_salon(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    V8.salon(c, t, b, night=key in ("hook",), holed=False)
    if key in ("veto", "gkg", "c80"):
        floor_hole(c)
    if key == "hook":
        # spirale violette derrière Michel
        for i in range(5):
            r_ = 120 + i * 70 + 20 * math.sin(t * 3 + i)
            p = skia.Path()
            p.addArc(skia.Rect.MakeLTRB(MX - r_, FLOOR - 200 - r_ * .5, MX + r_, FLOOR - 200 + r_ * .5), t * 120 + i * 50, 220)
            c.drawPath(p, line("#7A3CFF", 10, .5 - i * .08))
        scale_pad(c, MX, FLOOR + 6, 1, "4,5 kg")
        draw_cat(c, MX, FLOOR - 36, .42 * (1 + .02 * math.sin(t * 9)), t, "open", 0)
    elif key == "regle":
        scale_pad(c, MX, FLOOR + 6, 1, "4,5 kg")
        draw_cat(c, MX, FLOOR - 36, .42, t, "open", 0)
        gx = lerp(1320, 900, eout((d_ - .1) / .5))
        ger(c, gx, FLOOR + 14, .7, t, 0, hold="box")
        gerbub(c, t, b, gx - 60, 1010)
        u = clamp((d_ - 1.4) / .5)
        if 0 < u < 1:
            c.drawCircle(lerp(gx - 150, MX + 20, u), lerp(1200, FLOOR - 180, u) - math.sin(u * math.pi) * 160, 14, fill("#9B6A3C"))
        if d_ > 1.9:
            text(c, "crunch", MX + 170, FLOOR - 260, 52, "#FFFFFF", INK, 9, a=clamp((d_ - 1.9) / .15))
    elif key == "c0":
        scale_pad(c, MX, FLOOR + 6, 1, "4,5 kg")
        draw_cat(c, MX, FLOOR - 36, .42, t, "bliss", 0)
    elif key == "c4":
        val = "72 kg" if d_ > .3 else "4,5 kg"
        scale_pad(c, MX, FLOOR + 6, 1, val, broken=clamp((d_ - .3) / .2) * .3)
        draw_cat(c, MX, FLOOR - 36 + 8 * clamp((d_ - .3) / .2), .42, t, "open", 0)
        gx = lerp(1320, 880, eout((d_ - .4) / .5))
        ger(c, gx, FLOOR + 14, .7, t, 2)
        if d_ > .7:
            gerbub(c, t, b, gx - 60, 1010)
        if d_ > .9:
            text(c, "72 > 70", MX, FLOOR - 300, 60, "#FFE14D", INK, 10, a=clamp((d_ - .9) / .2))
    elif key == "c8":
        brk = clamp((d_ - .3) / .2)
        fall = clamp((d_ - .7) / .5)
        if d_ > .7:
            floor_hole(c, clamp((d_ - .7) / .1))
        if fall < 1:
            if d_ < .7:
                scale_pad(c, MX, FLOOR + 6 + 20 * brk, 1, "ERR", broken=brk)
            c.save()
            clip = skia.Path().addRect(skia.Rect.MakeLTRB(0, 0, W, FLOOR + 10))
            c.clipPath(clip, skia.ClipOp.kIntersect, True)
            draw_cat(c, MX, FLOOR - 36 + 20 * brk + ein(fall) * 500, .42, t, "open", 4 * brk)
            c.restore()
        else:
            # poussière
            k = d_ - 1.2
            if k < .8:
                for i in range(10):
                    a_ = math.pi + math.pi * i / 9
                    rr = 80 + 320 * eout(k / .8)
                    c.drawCircle(MX + math.cos(a_) * rr, FLOOR + math.sin(a_) * rr * .4, 50 * (1 - k / .8) + 8, fill("#E8D9B8", .9))
        gx = lerp(1320, 880, eout((d_ - .9) / .5))
        ger(c, gx, FLOOR + 14, .7, t, 3)
        if d_ > 1.2:
            gerbub(c, t, b, gx - 60, 1010)
    elif key == "veto":
        c.save()
        c.clipPath(skia.Path().addRect(skia.Rect.MakeLTRB(0, 0, W, FLOOR + 14)), skia.ClipOp.kIntersect, True)
        draw_cat(c, MX, FLOOR + 130, .42, t, "open" if d_ < 2.2 else "wink", 0)
        c.restore()
        gx = lerp(1320, 880, eout((d_ - .1) / .5))
        ger(c, gx, FLOOR + 14, .7, t, 1, hold="phone")
        gerbub(c, t, b, gx - 60, 1010)
    elif key == "gkg":
        val = "71 kg" if d_ > .9 else "70 kg"
        scale_pad(c, 820, FLOOR + 20, 1.2, val)
        ger(c, 820, FLOOR - 30, .7, t, 1)
        if d_ > .9:
            text(c, "+1 kg", 1000, FLOOR - 160, 56, "#FF5A3B", INK, 9, a=clamp((d_ - .9) / .15))
        if d_ > 1.4:
            gerbub(c, t, b, 760, 1000)
        # rond lumineux sous le trou : Michel loin dessous
        c.drawCircle(MX, FLOOR + 14, 30 + 6 * math.sin(t * 6), fill("#FF8A1F", .7))
    elif key == "c80":
        sq = eout(d_ / .4)
        scale_pad(c, 820, FLOOR + 20, 1.2, "134 kg", broken=.2 * sq)
        ger_sq(c, 820, FLOOR - 30, .7, t, 3, 1 + .25 * sq, 1 - .3 * sq)
        for k in range(3):
            ph = (t * 1.5 + k * .33) % 1
            c.drawCircle(700 + k * 120, FLOOR - 400 + ph * 200, 10, fill("#7EC8FF", 1 - ph))
        if d_ > .9:
            gerbub(c, t, b, 780, 1010)
        c.drawCircle(MX, FLOOR + 14, 34 + 8 * math.sin(t * 6), fill("#FF5A1F", .85))
        # objets du salon tirés vers le trou
        r = random.Random(7)
        for k in range(6):
            u = clamp((d_ - .3 - k * .25) / .6)
            if 0 < u < 1:
                x0, y0 = r.uniform(80, 1000), r.uniform(900, 1400)
                shape(c, rrect(-1, -1, 1, 1, 1).makeOffset(0, 0) if False else oval(lerp(x0, MX, ein(u)) - 22, lerp(y0, FLOOR, ein(u)) - 22,
                                                                                   lerp(x0, MX, ein(u)) + 22, lerp(y0, FLOOR, ein(u)) + 22),
                      r.choice(("#D9534F", "#3F6FD8", "#59B36A", "#FFE14D")), 5)


# ---------------------------------------------------------------- balance géante
def whale(c, x, y, s):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    p = skia.Path()
    p.moveTo(-200, -10)
    p.cubicTo(-180, -110, 120, -120, 190, -40)
    p.lineTo(260, -90)
    p.lineTo(250, -10)
    p.lineTo(270, 50)
    p.lineTo(190, 0)
    p.cubicTo(100, 40, -160, 50, -200, -10)
    p.close()
    shape(c, p, "#5C8FD6", 7)
    c.drawLine(-180, 10, 60, 22, line("#3D6CB0", 6))
    c.drawCircle(-130, -40, 9, fill(INK))
    c.restore()


def scene_balance(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    sky_grad(c, "#5CB8F2", "#D3F1FF")
    G = 1660
    c.drawRect(skia.Rect.MakeLTRB(0, G, W, H), fill("#7CC46E"))
    c.drawLine(0, G, W, G, line(INK, 6))
    px, py = 540, G - 300
    shape(c, poly([(px - 110, G), (px + 110, G), (px, py)]), "#8C8FA3", 7)
    if key == "c15":
        ang = 14 * math.exp(-d_ * 2.5) * math.cos(d_ * 9)
    else:
        ang = -4 - 10 * math.exp(-d_ * 2.5) * math.cos(d_ * 9)
    a = math.radians(ang)
    L = 340
    ends = [(px - L * math.cos(a), py - L * math.sin(a)), (px + L * math.cos(a), py + L * math.sin(a))]
    c.drawLine(ends[0][0], ends[0][1], ends[1][0], ends[1][1], line(INK, 30))
    c.drawLine(ends[0][0], ends[0][1], ends[1][0], ends[1][1], line("#C9A24E", 18))
    c.drawCircle(px, py, 18, fill(INK))
    for i, (ex, ey) in enumerate(ends):
        ty = ey + 160
        c.drawLine(ex, ey, ex - 110, ty, line(INK, 4))
        c.drawLine(ex, ey, ex + 110, ty, line(INK, 4))
        shape(c, rrect(ex - 140, ty, ex + 140, ty + 24, 10), "#C9A24E", 6)
        if i == 0:
            if key == "c15":
                whale(c, ex, ty - 50, .5)
                text(c, "BALEINE BLEUE", ex, ty + 90, 40, "#FFFFFF", INK, 8)
                text(c, "120 À 170 t", ex, ty + 136, 40, "#FFE14D", INK, 8)
            else:
                for dx in (-60, 60):
                    c.save()
                    c.translate(ex + dx, ty)
                    draw_eiffel(c, 300)
                    c.restore()
                text(c, "2 TOURS EIFFEL", ex, ty + 90, 40, "#FFFFFF", INK, 8)
                text(c, "20 200 t", ex, ty + 136, 40, "#FFE14D", INK, 8)
        else:
            draw_cat(c, ex, ty + 2, .2, t, "bliss" if key == "c22" and d_ > 2 else "open", 0)
            text(c, "MICHEL", ex, ty + 90, 40, "#FFFFFF", INK, 8)
            text(c, "147 t" if key == "c15" else "18 900 t", ex, ty + 136, 40, "#FFE14D", INK, 8)


# ---------------------------------------------------------------- sous terre
def scene_sol(c, t, b):
    d_ = t - b["start"]
    sky_grad(c, "#5CB8F2", "#D3F1FF", 0, 900)
    S = 900
    layers = [(S, "#7CC46E"), (S + 40, "#8A5A3B"), (S + 300, "#6E6A78"), (S + 700, "#8C4A3A"), (S + 1000, "#B5482F")]
    for i, (y0, cc) in enumerate(layers):
        y1 = layers[i + 1][0] if i + 1 < len(layers) else H
        c.drawRect(skia.Rect.MakeLTRB(0, y0, W, y1), fill(cc))
        c.drawLine(0, y0, W, y0, line(INK, 5))
    r = random.Random(3)
    for k in range(40):
        x, y = r.uniform(0, W), r.uniform(S + 60, H)
        c.drawOval(skia.Rect.MakeXYWH(x, y, r.uniform(20, 50), r.uniform(10, 26)), fill("#000000", .15))
    # tunnel
    u = clamp((d_ - .2) / 2.6)
    my = lerp(S + 30, H + 260, ein(u))
    c.drawRect(skia.Rect.MakeLTRB(MX - 80, S, MX + 80, my - 60), fill("#1A0F0C"))
    c.drawLine(MX - 80, S, MX - 80, my - 60, line(INK, 6))
    c.drawLine(MX + 80, S, MX + 80, my - 60, line(INK, 6))
    for k in range(6):
        ph = (t * 2.2 + k / 6) % 1
        c.drawCircle(MX + (k - 2.5) * 30, my - 140 - ph * 300, 14 * (1 - ph), fill("#C9B08A", .8))
    draw_cat(c, MX, my, .3, t, "open", 3)
    # Gérard au bord
    ger(c, 860, S + 10, .45, t, 2)
    if d_ > .6:
        gerbub(c, t, b, 620, S - 150)


EC = (540, 1180)
ER = 500


def coupe(c, t):
    c.drawImage(STARS, 0, 0)
    x, y = EC
    shape(c, oval(x - ER, y - ER, x + ER, y + ER), "#2B86DE", 8)
    c.drawPath(oval(x - ER + 10, y - ER + 10, x + ER - 10, y + ER - 10), fill("#4FA34F"))
    for rr, cc in ((ER - 28, "#D9662F"), (ER * .55, "#F2A03A"), (ER * .2, "#FFE14D")):
        shape(c, oval(x - rr, y - rr, x + rr, y + rr), cc, 5)
    c.drawCircle(x, y, ER * .2 + 14 + 5 * math.sin(t * 5), line("#FFF2A8", 6, .6))


def scene_coupe(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    coupe(c, t)
    x, y = EC
    if key == "centre":
        u = clamp(d_ / .9)
        my = lerp(y - ER, y + 40, ein(u))
        c.drawPath(skia.Path().moveTo(x, y - ER).lineTo(x, my - 70), skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6,
                   Color=col("#FFFFFF"), PathEffect=skia.DashPathEffect.Make([18, 12], 0)))
        draw_cat(c, x, my, .2, t, "open", 0)
        if d_ > 1.0:
            a_ = clamp((d_ - 1.0) / .2)
            c.drawLine(x + 150, y - ER, x + 150, y, line("#FFFFFF", 5, a_))
            text(c, "6 371 km", x + 170, y - ER / 2, 48, "#FFFFFF", INK, 9, align="left", a=a_)
    else:
        draw_cat(c, x, y + 40, .2, t, "bliss", 0)
        for k in range(3):
            ph = (t * .8 + k / 3) % 1
            text(c, "z", x + 50 + ph * 50, y - 60 - ph * 80, 26 + 18 * ph, "#FFFFFF", INK, 5, a=1 - ph)
    if key == "chaud":
        # thermomètre
        tx, ty = 930, 760
        u = eout((d_ - .2) / 1.0)
        shape(c, rrect(tx - 26, ty, tx + 26, ty + 420, 26), "#FFFFFF", 6)
        c.drawRect(skia.Rect.MakeLTRB(tx - 14, ty + 410 - 390 * u, tx + 14, ty + 410), fill("#FF3B2E"))
        shape(c, oval(tx - 46, ty + 390, tx + 46, ty + 482), "#FF3B2E", 6)
        text(c, "5 500 °C", tx - 40, ty - 24, 50, "#FFE14D", INK, 9, align="right", a=u)
        # petit soleil comparé
        sx, sy = 170, 760
        shape(c, oval(sx - 60, sy - 60, sx + 60, sy + 60), "#FFC531", 6, clamp((d_ - 1.0) / .3))
        text(c, "= SOLEIL", sx, sy + 110, 40, "#FFFFFF", INK, 8, a=clamp((d_ - 1.0) / .3))
        text(c, "(surface)", sx, sy + 150, 34, "#FFFFFF", INK, 7, a=clamp((d_ - 1.0) / .3))
        if d_ > 2.2:
            bubble(c, x - 60, y - 140, "prrr", 44, back((d_ - 2.2) / .16), -3)
    if key == "ficelle":
        gy = y - ER
        ger(c, x + 30, gy + 4, .22, t, 0)
        hx, hy = x + 30 - 150 * .22, gy - 140 * .22 * 3
        c.drawLine(x - 4, gy - 120, x, y - 50, line("#FFFFFF", 4))
        for k in range(5):
            ph = (t * 1.4 + k / 5) % 1
            c.drawCircle(x, lerp(gy - 110, y - 60, ph), 10, fill("#9B6A3C"))
            c.drawCircle(x, lerp(gy - 110, y - 60, ph), 10, line(INK, 3))
        text(c, "crunch", x - 150, y + 110, 44, "#FFFFFF", INK, 8, a=.5 + .5 * math.sin(t * 9))


def glow(c, x, y, r, colr, a=1.0):
    p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((x, y), r, [col(colr, a), col(colr, 0)]))
    c.drawCircle(x, y, r, p)


def scene_espace(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    c.drawImage(STARS, 0, 0)
    ex, ey, R = 540, 1200, 300
    if key == "c74":
        mx = lerp(900, 840, eout(d_ / 3))
        draw_moon(c, mx, 740, 74, t, "scared")
        text(c, "LUNE", mx, 860, 40, "#FFFFFF", INK, 8)
    img, x0, y0 = earth_rgba(R, cx=ex, cy=ey)
    vib = 0 if key == "c74" else 8 * clamp(d_ / 2.4)
    jx, jy = jitter(t, 6)
    c.drawImage(img, x0 + jx * vib, y0 + jy * vib)
    c.drawCircle(ex + jx * vib, ey + jy * vib, R, line(INK, 7))
    if key == "c74":
        glow(c, ex, ey, 80, "#FF8A1F", .9)
        c.drawCircle(ex, ey, 10, fill("#FFE14D"))
        c.drawLine(ex + 30, ey + 30, ex + 210, ey + 220, line("#FFE14D", 6))
        text(c, "MICHEL (ICI)", ex + 220, ey + 270, 42, "#FFE14D", INK, 8)
    else:
        g = clamp(d_ / 2.6)
        glow(c, ex, ey, 60 + 260 * g, "#B44CFF", .5 + .4 * g)
        c.drawCircle(ex, ey, 6 + 30 * g, fill("#000000"))
        if d_ > 2.9:
            c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", clamp((d_ - 2.9) / .4)))


def black_hole(c, x, y, t, r=110, eyes=0.0):
    for k in range(3):
        glow(c, x, y, r * (3.4 - k * .6), ("#FF7A1F", "#FFB347", "#FFE9A8")[k], .35)
    # disque d'accrétion
    c.save()
    c.translate(x, y)
    c.scale(1, .32)
    for i in range(36):
        a0 = t * 140 + i * 10
        rr = r * (1.6 + (i % 4) * .28)
        p = skia.Path()
        p.addArc(skia.Rect.MakeLTRB(-rr, -rr, rr, rr), a0, 16)
        c.drawPath(p, line(("#FFE14D", "#FFB347", "#FF7A1F", "#FFF4C9")[i % 4], 18))
    c.restore()
    c.drawCircle(x, y, r, fill("#000000"))
    c.drawCircle(x, y, r + 5, line("#FFF4C9", 5))
    # moitié avant du disque
    c.save()
    c.clipPath(skia.Path().addRect(skia.Rect.MakeLTRB(0, y, W, H)), skia.ClipOp.kIntersect, True)
    c.translate(x, y)
    c.scale(1, .32)
    for i in range(36):
        a0 = t * 140 + i * 10
        rr = r * (1.6 + (i % 4) * .28)
        p = skia.Path()
        p.addArc(skia.Rect.MakeLTRB(-rr, -rr, rr, rr), a0, 16)
        c.drawPath(p, line(("#FFE14D", "#FFB347", "#FF7A1F", "#FFF4C9")[i % 4], 18))
    c.restore()
    if eyes > 0:
        for sg in (-1, 1):
            e = skia.Path()
            ex_ = x + sg * 38
            e.moveTo(ex_ - 26, y - 10)
            e.quadTo(ex_, y - 34 * eyes, ex_ + 26, y - 10)
            e.quadTo(ex_, y + 14 * eyes, ex_ - 26, y - 10)
            c.drawPath(e, fill("#FFE14D"))
            c.drawOval(skia.Rect.MakeLTRB(ex_ - 5, y - 26 * eyes, ex_ + 5, y + 6 * eyes), fill("#000000"))


def ger_canape(c, x, y, s, t, stage=0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.translate(-570, -1300)
    draw_couch(c)
    draw_gerard(c, stage, t, True, 0, True)
    c.restore()


def scene_trou(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    c.drawImage(STARS, 0, 0)
    x, y = 540, 1150
    if key == "bh":
        # la Terre est aspirée en spirale
        u = clamp(d_ / 2.6)
        R = 300 * (1 - ein(u))
        if R > 4:
            img, x0, y0 = earth_rgba(R, cx=x, cy=y)
            c.save()
            c.translate(x, y)
            c.rotate(u * 400)
            c.scale(1 + u * .8, 1 - u * .5)
            c.translate(-x, -y)
            c.drawImage(img, x0, y0)
            c.restore()
        for k in range(40):
            ang = k * .7 + t * (2 + k % 3) + u * 6
            rr = (360 - (t * 160 + k * 37) % 360) * (.4 + u)
            c.drawCircle(x + math.cos(ang) * rr, y + math.sin(ang) * rr * .5, 6, fill(("#5BBF6B", "#2B86DE", "#FFFFFF")[k % 3], .9))
        black_hole(c, x, y, t, 110 * eout(clamp((d_ - .2) / 1.2)) + 1)
    else:
        black_hole(c, x, y, t, 110, eyes=clamp((d_ - .4) / .3) if key == "fin" else 0)
        ang = (t - K["calme"]) * .9 + 2.2
        gx, gy = x + math.cos(ang) * 400, y + math.sin(ang) * 260
        front = math.sin(ang) > 0
        if True:
            ger_canape(c, gx, gy, .34, t, 0 if key == "calme" else 2)
        if key == "calme" and d_ > 1.0:
            bubble(c, gx + 70, gy - 200, "...", 46, back((d_ - 1.0) / .16), 3)
        if key == "fin":
            if d_ > 1.0:
                bubble(c, x, y - 200, "mrrp ?", 52, back((d_ - 1.0) / .16), -3)
            if d_ > 2.0:
                gerbub(c, t, b, gx + 70, gy - 200)


# ---------------------------------------------------------------- HUD, légende, carton
def heat_c(n):
    u = clamp(n / 85)
    stops = [(0, "#59E36A"), (.3, "#D7F03A"), (.55, "#FFC531"), (.8, "#FF7A1F"), (.95, "#FF2E2E"), (1, "#B44CFF")]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if a <= u <= b:
            return hexmix(ca, cb, (u - a) / (b - a))
    return "#B44CFF"


MOTS = [(1e24, "QUADRILLIONS"), (1e21, "TRILLIARDS"), (1e18, "TRILLIONS"), (1e15, "BILLIARDS"), (1e12, "BILLIONS"), (1e9, "MILLIARDS"), (1e6, "MILLIONS")]


def poids_txt(m):
    if m < 10:
        return ("%.1f KG" % m).replace(".", ",")
    if m < 999.5:
        return "%d KG" % round(m)
    t_ = m / 1000
    if t_ < 9.995:
        return ("%.2f T" % t_).replace(".", ",")
    if t_ < 999999.5:
        return "%s T" % nb(round(t_))
    for v, w in MOTS:
        if t_ >= v:
            q = t_ / v
            if q >= 999.5 and v == 1e24:
                return "%s %s DE T" % (nb(round(q)), w)
            s = "%d" % round(q) if q >= 10 else ("%.1f" % q).replace(".", ",")
            return "%s %s DE T" % (s, w)


assert poids_txt(kg(0)) == "4,5 KG" and poids_txt(kg(4)) == "72 KG" and poids_txt(kg(8)) == "1,15 T"
assert poids_txt(kg(15)) == "147 T" and poids_txt(kg(22)) == "18 874 T" and poids_txt(kg(74)) == "85 TRILLIONS DE T"
assert poids_txt(kg(85)) == "174 TRILLIARDS DE T"


def hud(c, t, b):
    n = n_at(t)
    colr = heat_c(n)
    d_ = t - b["start"]
    pop = 1 + .14 * (1 - eout(d_ / .22)) if (b["n1"] != b["n0"] and b["key"] != "ficelle") else 1.0
    c.save()
    c.translate(540, 262)
    c.scale(pop, pop)
    pan = rrect(-420, -135, 420, 135, 44)
    c.drawPath(pan, fill("#14121C", .94))
    c.drawPath(pan, line(colr, 8))
    head = "POIDS DE MICHEL"
    big = poids_txt(kg(n))
    low = "Croquette n° %d" % round(n)
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
    c.translate(540, 720)
    c.scale(s, s)
    text(c, "À SUIVRE :", 0, 0, 86, "#FFFFFF")
    text(c, "CROQUETTE N° 86.", 0, 128, 86, "#FFD93B")
    c.restore()
    a = clamp((d_ - .5) / .25)
    for i, l in enumerate(("Très approximatif : départ à 4,5 kg, ×2 par croquette,",
                           "taille fixe (50 cm en boule), physique très simplifiée.",
                           "Chat adulte : 3,5 à 5,5 kg. Baleine bleue : 120 à 170 t.",
                           "Tour Eiffel : 10 100 t. Noyau : environ 5 500 °C.",
                           "Plancher de logement : environ 150 kg/m².",
                           "Trou noir : rayon = 2GM/c² (plus de 25 cm ici).",
                           "Ne nourrissez pas votre chat comme ça. Michel va bien.")):
        text(c, l, 540, 1000 + i * 62, fit(l, 42, 980), "#A9A6BC", a=a)


SCN = dict(salon=scene_salon, balance=scene_balance, sol=scene_sol, coupe=scene_coupe, espace=scene_espace, trou=scene_trou)


def shake_amp(t):
    amp = 0
    for tk in JUMPS:
        d_ = t - tk
        if 0 <= d_ < .22:
            amp = max(amp, 9 * (1 - d_ / .22))
    for key, a0, dur, g in (("c8", .7, .6, 26), ("c15", 0, .5, 16), ("c22", 0, .5, 18), ("sol", 0, 3.2, 6), ("c85", 1.0, 2.4, 10), ("bh", 0, 1.0, 22)):
        d_ = t - K[key] - a0
        if 0 <= d_ < dur:
            amp = max(amp, g * (1 - d_ / dur) if key not in ("sol", "c85") else g)
    return amp


def burst(c, t):
    for tk in JUMPS:
        d_ = t - tk
        if 0 <= d_ < .07:
            c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", .5 * (1 - d_ / .07)))
    d_ = t - K["bh"]
    if 0 <= d_ < .4:
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", 1 - d_ / .4))


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


_sp = [K["c15"], K["sol"], K["c74"], K["gkg"], K["c85"], K["bh"], CARD, END]
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
