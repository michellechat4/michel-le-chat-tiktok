"""Gérard est allergique à Michel, et ses éternuements doublent chaque jour : 1, 64, un par seconde, 24 par seconde (un film),
une note de musique, un sifflement, puis trop aigu pour les humains… mais pas pour Michel."""
import math, random, sys, os, subprocess
import importlib.util as _u
import numpy as np
import skia
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "moteur"))
import art
from art import (fill, line, col, hexmix, poly, rrect, oval, shape, text, jitter, clamp, lerp, eout, ein, back,
                 draw_cat, draw_gerard, draw_couch, bubble, wrap_rich, TF, INK, W, H, FPS)

# décor du salon et outils repris de la vidéo 08
_sp = _u.spec_from_file_location("saut08", os.path.join(HERE, "08_saut.py"))
V8 = _u.module_from_spec(_sp)
_sp.loader.exec_module(V8)
sky_grad, fit, nb, FLOOR = V8.sky_grad, V8.fit, V8.nb, V8.FLOOR

# ---------------------------------------------------------------- chiffres (calculés, pas recopiés)
JOUR_S = 86400           # s dans une journée (éternuements répartis sur 24 h, sommeil compris : très approximatif)
FILM = 24                # images/s, standard du cinéma 35 mm (Universalis, StudioBinder)
HUMAIN = (20, 20000)     # Hz, audition humaine (AudioNova)
CHAT = 60000             # Hz, audition du chat : 60 000 (AudioNova) à 64 000 Hz (FirstVet) → « environ 60 000 »
CHAT_MAX = 64000
SOL = 440 * 2 ** (-2 / 12)   # sol sous le la 440 Hz : 392 Hz


def par_jour(d):
    return 2 ** (d - 1)


def par_s(d):
    return par_jour(d) / JOUR_S


assert par_jour(7) == 64 and par_jour(11) == 1024 and round(JOUR_S / par_jour(11)) == 84
assert par_jour(17) == 65536 and .7 < par_s(17) < 1 < par_s(18)
assert round(par_s(22)) == FILM and par_s(21) < HUMAIN[0] < par_s(22)
assert round(par_s(26)) == 388 and abs(par_s(26) / SOL - 1) < .01 and round(SOL) == 392
assert round(par_s(27)) == 777 and round(par_s(30)) == 6214
assert par_s(31) < HUMAIN[1] < par_s(32) and round(par_s(32)) == 24855
assert par_s(33) < CHAT and round(par_s(33)) == 49710 and par_s(34) > CHAT_MAX and round(par_s(34)) == 99421

# ---------------------------------------------------------------- chronologie
# (clé, durée, jour, légende, Gérard dit, mode)
RAW = [
    ("hook", 3.0, 1, "GÉRARD VA ÉTERNUER | *SI VITE QU'IL CHANTE.*", None, "hook"),
    ("regle", 3.4, 1, "Gérard est allergique à Michel. | Chaque jour, ça *double.*", "Atchoum.", "snz"),
    ("dix", 3.4, 1, "1 Français sur 10 serait | allergique *aux chats.*", None, "dix"),
    ("salive", 3.6, 1, "Pas à cause des poils : d'une | protéine, *dans sa salive.*", None, "salive"),
    ("j1", 2.8, 1, "Jour 1 : *1 éternuement.*", "Atchoum.", "snz"),
    ("j7", 3.2, 7, "Jour 7 : 64. | Gérard achète *des mouchoirs.*", None, "snz"),
    ("j11", 3.4, 11, "Jour 11 : 1 024. | *Un toutes les 84 secondes.*", None, "clock"),
    ("j17", 3.6, 17, "Jour 17 : 65 536. | *Presque un par seconde.*", "Je dors quand ?", "snz"),
    ("medecin", 3.4, 17, "Le médecin conseille | *d'éloigner le chat.*", "Jamais.", "snz"),
    ("j22", 3.6, 22, "Jour 22 : 24 par seconde. | Autant que les images *d'un film.*", None, "film"),
    ("son", 3.4, 22, "Plus de 20 par seconde : | ça devient *un son grave.*", None, "freq"),
    ("j26", 3.6, 26, "Jour 26 : 388 par seconde. | Gérard chante *presque un sol.*", None, "freq"),
    ("voisin", 3.0, 27, "Jour 27 : une octave plus haut. | *Le voisin applaudit.*", None, "freq"),
    ("j30", 3.4, 30, "Jour 30 : 6 214 par seconde. | *Un sifflement.*", None, "freq"),
    ("j32", 3.6, 32, "Jour 32 : 24 855 par seconde. | Trop aigu : *on n'entend plus rien.*", None, "freq"),
    ("calme", 3.0, 32, "Gérard éternue | *en silence.*", "...", "freq"),
    ("j33", 3.6, 33, "Jour 33 : 49 710 par seconde. | Michel, lui, *entend tout.*", None, "freq"),
    ("j34", 3.4, 34, "Jour 34 : 99 421 par seconde. | Même Michel *n'entend plus.*", None, "freq"),
    ("fin", 3.8, 34, "Michel se rendort | *sur la tête de Gérard.*", None, "fin"),
    ("fin2", 3.0, 34, "Jour 35 ?", "Atch…", "fin"),
]
CARD_DUR = 3.8
BEATS = []
_t, _d = 0.0, 1
for key, dur, d, cap, ger_, mode in RAW:
    BEATS.append(dict(key=key, start=_t, dur=dur, d0=_d, d1=d, cap=cap, ger=ger_, mode=mode))
    _t += dur
    _d = d
CARD = _t
END = CARD + CARD_DUR
K = {b["key"]: b["start"] for b in BEATS}
JUMPS = sorted(b["start"] for b in BEATS if b["d1"] > b["d0"])
ROLL = .7
SILENT = ("j32", "calme", "j33", "j34")

# éternuements « un par un » (même liste pour l'image et le son)
SNZ = [K["hook"] + 1.0, K["regle"] + 1.2, K["j1"] + .9, K["j7"] + .5, K["j7"] + 1.7, K["j11"] + 1.6]
for key in ("j17", "medecin"):
    tt = K[key] + .25
    while tt < K[key] + 3.4 - .3:
        SNZ.append(tt)
        tt += 1 / par_s(17)          # le vrai rythme du jour 17 : un toutes les 1,3 s
SNZ.sort()
PRE = .45                            # « Ah… » avant le « tchoum »


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


def snz_state(t):
    """(pré, coup) : pré 0..1 pendant le « Ah », coup 1→0 après le « tchoum »."""
    pre, hit = 0.0, 0.0
    for s in SNZ:
        if s - PRE <= t < s:
            pre = max(pre, ein((t - s + PRE) / PRE))
        if s <= t < s + .6:
            hit = max(hit, 1 - (t - s) / .6)
    return pre, hit


def buzz_level(t):
    """Vibration continue de Gérard quand les éternuements fusionnent."""
    b = beat_at(t)
    if b["mode"] in ("film", "freq"):
        return 1.0
    return 0.0


# ---------------------------------------------------------------- personnages
HX, HY = 790, 1000          # tête de Gérard (coordonnées du canapé)
MCX, MCY, MS = 330, 1318, .55


def tissue(c, x, y, s, r=0):
    c.save()
    c.translate(x, y)
    c.rotate(r)
    c.scale(s, s)
    p = skia.Path()
    rr = random.Random(int(x * 7 + y))
    for k in range(9):
        a = k / 9 * 6.283
        rad = 30 + rr.uniform(-8, 8)
        (p.moveTo if k == 0 else p.lineTo)(math.cos(a) * rad, math.sin(a) * rad * .8)
    p.close()
    shape(c, p, "#FFFFFF", 5)
    c.drawLine(-10, -6, 8, 4, line("#C9CBD6", 3))
    c.restore()


def tissue_box(c, x, y):
    shape(c, rrect(x - 62, y - 54, x + 62, y, 10), "#7EC8FF", 6)
    c.drawLine(x - 62, y - 30, x + 62, y - 30, line("#FFFFFF", 6, .6))
    p = skia.Path()
    p.moveTo(x - 20, y - 54)
    p.quadTo(x - 30, y - 100, x + 4, y - 96)
    p.quadTo(x + 26, y - 84, x + 18, y - 54)
    p.close()
    shape(c, p, "#FFFFFF", 5)


def tissue_pile(c, day):
    n = 0 if day < 6.5 else int(min(44, (day - 5) * 2.6))
    rr = random.Random(5)
    for k in range(n):
        row = int(math.sqrt(k))
        x = 1000 + rr.uniform(-80, 70) - row * 6
        y = FLOOR + 30 - row * 34 + rr.uniform(-10, 10)
        tissue(c, x, y, .9, rr.uniform(0, 360))


def ger_full(c, t, stage, lean=0.0, vib=0.0, nose=0.0, mouth_o=False):
    c.save()
    c.translate(HX, 1340)
    c.rotate(lean)
    c.translate(-HX, -1340)
    draw_gerard(c, stage, t, False, vib, True)
    jx, jy = jitter(t, 9)
    # nez rouge (dessiné par-dessus, au milieu du visage)
    if nose > 0:
        c.drawOval(skia.Rect.MakeLTRB(HX - 15 + jx * vib, HY + 4 + jy * vib, HX + 15 + jx * vib, HY + 30 + jy * vib),
                   fill(hexmix("#F2A98A", "#E8343A", nose)))
        c.drawOval(skia.Rect.MakeLTRB(HX - 15 + jx * vib, HY + 4 + jy * vib, HX + 15 + jx * vib, HY + 30 + jy * vib), line(INK, 4))
    c.restore()


def spray(c, t, s):
    """Gouttelettes du dernier « tchoum » (s = instant)."""
    d_ = t - s
    if not (0 <= d_ < .55):
        return
    rr = random.Random(int(s * 100))
    u = eout(d_ / .55)
    for k in range(26):
        a = rr.uniform(.35, 2.8)
        dist = rr.uniform(60, 340) * u
        x = HX + math.cos(a) * dist * 1.3 - 10
        y = HY + 60 + math.sin(a) * dist * .55 + 60 * u * u
        c.drawCircle(x, y, rr.uniform(5, 11) * (1 - .5 * u), fill("#BFE7FF", 1 - u))
    if d_ < .4:
        bw = back(d_ / .15)
        text(c, "TCHOUM !", HX - 230, HY - 150, 64 * bw, "#FFFFFF", INK, 11, a=clamp(1 - (d_ - .25) / .15))


def rings(c, t, x, y, freq_vis, a=1.0, colr="#FFFFFF"):
    for k in range(5):
        ph = (t * freq_vis + k / 5) % 1
        r_ = 110 + ph * 420
        p = skia.Path()
        p.addArc(skia.Rect.MakeLTRB(x - r_, y - r_ * .8, x + r_, y + r_ * .8), 200, 140)
        c.drawPath(p, line(colr, 10 * (1 - ph) + 2, a * (1 - ph)))


def note(c, x, y, s, a=1.0, colr="#FFE14D"):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.drawOval(skia.Rect.MakeLTRB(-26, -14, 18, 18), fill(colr, a))
    c.drawOval(skia.Rect.MakeLTRB(-26, -14, 18, 18), line(INK, 5, a))
    c.drawLine(15, 0, 15, -90, line(INK, 8, a))
    p = skia.Path()
    p.moveTo(15, -90)
    p.quadTo(45, -70, 40, -40)
    c.drawPath(p, line(INK, 8, a))
    c.restore()


def eyebrows(c, x, y, s):
    for sg in (-1, 1):
        c.drawLine(x + sg * 100 * s, y - 340 * s, x + sg * 30 * s, y - 318 * s, line(INK, 18 * s))


# ---------------------------------------------------------------- panneaux (zone du mur)
PY0, PY1 = 640, 880


def panel(c, a=1.0):
    p = rrect(60, PY0, 1020, PY1, 34)
    c.drawPath(p, fill("#14121C", .92 * a))
    c.drawPath(p, line("#FFFFFF", 6, a))


def person(c, x, y, s, colr):
    c.drawCircle(x, y - 70 * s, 22 * s, fill(colr))
    c.drawPath(rrect(x - 26 * s, y - 44 * s, x + 26 * s, y + 20 * s, 18 * s), fill(colr))


def panel_dix(c, t, b):
    d_ = t - b["start"]
    a = clamp(d_ / .25)
    panel(c, a)
    for k in range(10):
        u = back(clamp((d_ - .1 - k * .06) / .2))
        x = 130 + k * 91
        red = k == 6
        c.save()
        c.translate(x, 798)
        c.scale(u, u)
        person(c, 0, 0, 1.5, "#FF5A5A" if red else "#8FA0C8")
        c.restore()
        if red and d_ > 1.0:
            text(c, "ATCHOUM", x, 676, 30, "#FFE14D", INK, 6, a=clamp((d_ - 1.0) / .15))
    text(c, "≈ 1 SUR 10 (ESTIMATION)", 540, 866, 28, "#C9C6D8", a=a)


def scale_x(f):
    lo, hi = math.log10(10), math.log10(200000)
    return 110 + (math.log10(max(f, 10)) - lo) / (hi - lo) * 860


def panel_freq(c, t, b):
    d_ = t - b["start"]
    a = clamp(d_ / .25) if b["key"] == "son" else 1.0
    panel(c, a)
    y1, y2 = 770, 830
    for (f0, f1, yy, colr, lab) in ((HUMAIN[0], HUMAIN[1], y1, "#5AA9FF", "HUMAIN"), (20, CHAT, y2, "#F49A3A", "CHAT")):
        c.drawPath(rrect(scale_x(f0), yy - 16, scale_x(f1), yy + 16, 16), fill(colr, a))
        c.drawPath(rrect(scale_x(f0), yy - 16, scale_x(f1), yy + 16, 16), line(INK, 4, a))
        text(c, lab, scale_x(f0) + 16, yy + 12, 30, "#FFFFFF", INK, 6, align="left", a=a)
    text(c, "20 000", scale_x(HUMAIN[1]), y1 + 12, 26, "#FFFFFF", INK, 5, a=a)
    text(c, "≈ 60 000 Hz", scale_x(CHAT) - 4, y2 + 12, 26, "#FFFFFF", INK, 5, align="right", a=a)
    # curseur : fréquence des éternuements
    f = par_s(d_at(t))
    x = scale_x(f)
    off = f > CHAT_MAX
    colr = "#FFE14D" if f < HUMAIN[1] else ("#FF8A1F" if f < CHAT_MAX else "#B44CFF")
    c.drawLine(x, 708, x, 846, line(colr, 6, a))
    shape(c, poly([(x - 18, 680), (x + 18, 680), (x, 706)]), colr, 4, a)
    lab = "GÉRARD : %s Hz" % nb(round(f))
    xl = clamp(x, 110 + fit(lab, 36, 500) * 4.5, 970 - fit(lab, 36, 500) * 4.5)
    text(c, lab, xl, 672, 36, colr, INK, 7, a=a)
    if off:
        text(c, "HORS LIMITES", 760, 862, 28, "#B44CFF", INK, 5, a=a)


def panel_film(c, t, b):
    d_ = t - b["start"]
    a = clamp(d_ / .25)
    panel(c, a)
    c.save()
    c.clipPath(rrect(70, PY0 + 10, 1010, PY1 - 10, 28), skia.ClipOp.kIntersect, True)
    off = (t * 220) % 140
    c.drawRect(skia.Rect.MakeLTRB(60, 680, 1020, 830), fill("#2B2833", a))
    for k in range(-1, 9):
        x = 80 + k * 140 - off
        for yy in (690, 808):
            c.drawRect(skia.Rect.MakeLTRB(x + 10, yy, x + 34, yy + 14), fill("#EDEAF5", a))
            c.drawRect(skia.Rect.MakeLTRB(x + 70, yy, x + 94, yy + 14), fill("#EDEAF5", a))
        c.drawRect(skia.Rect.MakeLTRB(x + 8, 712, x + 128, 800), fill("#F7DDAE", a))
        c.drawCircle(x + 68, 756, 26, fill("#F7C7A0", a))
        c.drawCircle(x + 68, 756, 26, line(INK, 4, a))
        for j in range(5):
            aa = .8 + j * .35
            c.drawCircle(x + 68 + math.cos(aa) * 40, 760 + math.sin(aa) * 26, 5, fill("#5AA9FF", a))
    c.restore()
    text(c, "FILM : 24 IMAGES / S", 300, 870, 32, "#FFFFFF", INK, 6, a=a)
    text(c, "GÉRARD : 24 TCHOUMS / S", 770, 870, 32, "#FFE14D", INK, 6, a=a)


def panel_clock(c, t, b):
    d_ = t - b["start"]
    a = clamp(d_ / .25)
    panel(c, a)
    x, y, r = 260, 760, 92
    shape(c, oval(x - r, y - r, x + r, y + r), "#FFFFFF", 7, a)
    for k in range(12):
        an = k / 12 * 6.283
        c.drawLine(x + math.cos(an) * r * .8, y + math.sin(an) * r * .8, x + math.cos(an) * r * .92, y + math.sin(an) * r * .92, line(INK, 5, a))
    an = -math.pi / 2 + clamp(d_ / 1.6) * 6.283 * (84 / 60)
    c.drawLine(x, y, x + math.cos(an) * r * .78, y + math.sin(an) * r * .78, line("#E8343A", 7, a))
    c.drawCircle(x, y, 9, fill(INK, a))
    text(c, "84 s", 640, 790, 110, "#FFE14D", INK, 12, a=a)
    text(c, "entre deux tchoums", 640, 852, 36, "#C9C6D8", a=a)


def panel_salive(c, t, b):
    d_ = t - b["start"]
    a = clamp((d_ - .6) / .25)
    if a <= 0:
        return
    panel(c, a)
    text(c, "PROTÉINE « Fel d 1 »", 540, 735, 60, "#FFE14D", INK, 10, a=a)
    text(c, "salive, peau, glandes du chat", 540, 800, 40, "#FFFFFF", a=a)
    text(c, "puis sur les poils, puis dans l'air", 540, 852, 36, "#C9C6D8", a=a)


# ---------------------------------------------------------------- scène
def scene(c, t, b):
    key, mode = b["key"], b["mode"]
    d_ = t - b["start"]
    day = d_at(t)
    V8.salon(c, t, b, night=key in ("fin", "fin2"), holed=False)
    if key in ("fin", "fin2"):
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#1A2350", .35))
    tissue_pile(c, day)
    draw_couch(c)
    tissue_box(c, 1010, 1180)
    # Michel sur le canapé (sauf fin : sur la tête de Gérard)
    pre, hit = snz_state(t)
    buzz = buzz_level(t)
    on_head = key in ("fin", "fin2") and (key == "fin2" or d_ > 1.2)
    if not on_head:
        mood = "bliss"
        mx, my = MCX, MCY
        if key == "fin":
            u = clamp((d_ - .2) / 1.0)
            mx, my = lerp(MCX, HX, eout(u)), lerp(MCY, HY - 85, eout(u)) - math.sin(u * math.pi) * 260
            mood = "open"
        elif key in ("j33",):
            mood = "open"
        elif hit > .3:
            mood = "open"
        vib = 6 if key == "j33" else 0
        draw_cat(c, mx, my, MS if key != "fin" else lerp(MS, .32, clamp((d_ - .2) / 1.0)), t, mood, vib)
        if key == "j33":
            jx, jy = jitter(t, 3)
            eyebrows(c, mx + jx * 6, my + jy * 6, MS)
            text(c, "GRRR", mx + 150, my - 260, 54, "#FF5A3B", INK, 9, a=clamp((d_ - .5) / .15))
            for sg in (-1, 1):
                for k in range(3):
                    ph = (t * 3 + k / 3) % 1
                    c.drawCircle(mx + sg * (80 + 60 * ph), my - 230 - 30 * ph, 7, fill("#FF5A3B", 1 - ph))
        if key == "salive":
            # Michel se lèche la patte
            c.save()
            c.translate(mx, my)
            c.scale(MS, MS)
            lk = abs(math.sin(t * 7))
            shape(c, oval(-12, -214, 12, -184 + 14 * lk), "#FF8FA3", 4)
            c.restore()
            for k in range(6):
                ph = (t * .7 + k / 6) % 1
                c.drawCircle(mx - 80 + k * 32 + 20 * math.sin(t * 2 + k), my - 180 - ph * 380, 8, fill("#FFE14D", .9 * (1 - ph)))
    # Gérard
    nose = clamp((day - 1) / 16)
    lean = -7 * pre + 15 * hit
    stage = 0
    if pre > 0:
        stage = 2
    if hit > 0:
        stage = 3
    vib = 0.0
    if buzz:
        stage = 2
        vib = {"film": 5, "son": 5}.get(key, 9)
        lean = 6 + 2 * math.sin(t * 50)
    if key in ("fin", "fin2"):
        stage, vib, lean = 0, 0.0, 0.0
        if key == "fin2":
            dd = d_ - 1.2
            if dd > 0:
                stage, lean = 2, -6 * clamp(dd / .4)
    if key in ("medecin", "j17") and hit == 0 and pre == 0:
        stage = 1
    ger_full(c, t, stage, lean, vib, nose)
    if on_head:
        jx = 0
        draw_cat(c, HX, HY - 82 + (0 if key == "fin" else -6 * clamp((d_ - 1.2) / .4)), .32, t,
                 "bliss" if key == "fin" or d_ < 1.4 else "open")
        if key == "fin":
            for k in range(3):
                ph = (t * .8 + k / 3) % 1
                text(c, "z", HX + 70 + ph * 60, HY - 220 - ph * 100, 30 + 20 * ph, "#FFFFFF", INK, 5, a=1 - ph)
    for s in SNZ:
        spray(c, t, s)
    # bruit visible
    if buzz and key not in SILENT:
        fv = {"film": 1.6, "son": 1.2, "j26": 2.2, "voisin": 2.8, "j30": 4}.get(key, 2)
        rings(c, t, HX, HY + 50, fv, .85, "#FFFFFF" if key in ("film", "son") else "#FFE14D")
    if key in ("j26", "voisin", "hook"):
        for k in range(4):
            ph = (t * .6 + k / 4) % 1
            x = HX + (-260 if k % 2 else 230) + 40 * math.sin(t * 3 + k)
            note(c, x, HY + 40 - ph * 300, .9, 1 - ph)
    if key in ("j32", "calme"):
        text(c, "( silence )", 560, 1010, 52, "#FFFFFF", INK, 8, a=clamp((d_ - .5) / .2))
    if key == "voisin" and d_ > .9:
        bubble(c, 220, 1060, "BRAVO !", 54, back((d_ - .9) / .16), -6)
        for k in range(3):
            ph = (t * 4 + k / 3) % 1
            c.drawLine(80, 1150 + k * 30, 40 - 30 * ph, 1150 + k * 30, line(INK, 6, 1 - ph))
    # panneaux
    if mode == "dix":
        panel_dix(c, t, b)
    elif mode == "salive":
        panel_salive(c, t, b)
    elif mode == "clock":
        panel_clock(c, t, b)
    elif mode == "film":
        panel_film(c, t, b)
    elif mode == "freq":
        panel_freq(c, t, b)
    # bulle de Gérard
    if b["ger"]:
        delay = .35 if key not in ("regle", "j1") else 1.0
        if key == "fin2":
            delay = 1.5
        f = skia.Font(TF, 52)
        w = f.measureText(b["ger"])
        bx = clamp(HX - 60, w / 2 + 44, W - w / 2 - 44)
        if key == "calme":
            bx, by = 600, 1130
        else:
            by = HY - 200 if key != "fin2" else HY - 330
        bubble(c, bx, by, b["ger"], 52, back((d_ - delay) / .16), 2)


# ---------------------------------------------------------------- HUD, légende, carton
def heat_c(d):
    u = clamp((d - 1) / 33)
    stops = [(0, "#59E36A"), (.3, "#D7F03A"), (.55, "#FFC531"), (.8, "#FF7A1F"), (.92, "#FF2E2E"), (1, "#B44CFF")]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if a <= u <= b:
            return hexmix(ca, cb, (u - a) / (b - a))
    return "#B44CFF"


def big_txt(n):
    if n < 999999.5:
        return nb(round(n))
    if n < 1e9:
        q = n / 1e6
        s = ("%.1f" % q).replace(".", ",") if q < 9.95 else "%d" % round(q)
        return s + " MILLIONS"
    q = n / 1e9
    s = ("%.2f" % q).replace(".", ",") if q < 9.995 else "%d" % round(q)
    return s + (" MILLIARD" if q < 2 else " MILLIARDS")


assert big_txt(par_jour(17)) == "65 536" and big_txt(par_jour(22)) == "2,1 MILLIONS" and big_txt(par_jour(30)) == "537 MILLIONS"
assert big_txt(par_jour(31)) == "1,07 MILLIARD" and big_txt(par_jour(34)) == "8,59 MILLIARDS"


def low_txt(d):
    s = par_s(d)
    dd = round(d)
    if s < .995:
        return "Jour n° %d" % dd
    return "Jour n° %d · %s par seconde" % (dd, nb(round(s)))


def hud(c, t, b):
    d = d_at(t)
    colr = heat_c(d)
    d_ = t - b["start"]
    pop = 1 + .14 * (1 - eout(d_ / .22)) if b["d1"] != b["d0"] else 1.0
    c.save()
    c.translate(540, 262)
    c.scale(pop, pop)
    pan = rrect(-420, -135, 420, 135, 44)
    c.drawPath(pan, fill("#14121C", .94))
    c.drawPath(pan, line(colr, 8))
    head = "ÉTERNUEMENTS DE GÉRARD / JOUR"
    big = big_txt(par_jour(d))
    low = low_txt(d)
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


CARD_LINES = ("Très approximatif : 1 éternuement le jour 1, ×2 par jour,",
              "étalés sur 24 h. Personne ne peut éternuer comme ça.",
              "Environ 1 Français sur 10 serait allergique aux chats (estimation).",
              "Allergène principal : Fel d 1 (salive, peau, glandes sébacées).",
              "Cinéma : 24 images/s. Oreille humaine : 20 à 20 000 Hz.",
              "Chat : jusqu'à 60 000 à 64 000 Hz environ. Sol : 392 Hz.",
              "Allergique ? Parlez-en à un médecin. Michel va bien.")


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
    text(c, "JOUR N° 35.", 0, 128, 86, "#FFD93B")
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
    for s in SNZ:
        d_ = t - s
        if 0 <= d_ < .2:
            amp = max(amp, 12 * (1 - d_ / .2))
    return amp


def burst(c, t):
    for tk in JUMPS:
        d_ = t - tk
        if 0 <= d_ < .07:
            c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", .5 * (1 - d_ / .07)))


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
    scene(c, t, b)
    c.restore()
    burst(c, t)
    hud(c, t, b)
    caption(c, t)


_sp = [K["j11"], K["j22"], K["j30"], K["fin"], CARD, END]
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
