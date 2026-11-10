"""Michel veut sortir, puis rentrer. Chaque jour, il demande deux fois plus. Gérard finit par marcher plus loin que la Lune."""
import math, random, sys, os, subprocess
import numpy as np
import skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "moteur"))
import art
from art import (fill, line, col, hexmix, poly, rrect, oval, shape, text, jitter, clamp, lerp, eout, ein, back,
                 draw_cat, draw_gerard, draw_moon, earth_rgba, STARS, bubble, wrap_rich, TF, INK, W, H, FPS)

# ---------------------------------------------------------------- chiffres (calculés, pas recopiés)
R0 = 20                  # demandes le jour 1 (estimation, non sourcée)
AR = 12                  # m par aller-retour canapé-porte (6 m + 6 m, estimation)
MARATHON = 42.195        # km (distance officielle)
TDF = 3333               # km, Tour de France 2026 (BikeRadar, Domestique)
TGV = 320                # km/h, vitesse commerciale maximale (Kombo, Euronews 2026)
TERRE = 40075            # km, circonférence à l'équateur
LUNE = 384400            # km, distance moyenne Terre-Lune
SON = 1235               # km/h, vitesse du son dans l'air à 20 °C (343 m/s)
JOUR_S = 86400


def dem(n):
    """Demandes le jour n."""
    return R0 * 2 ** (n - 1) if n >= 1 else 0


def dist_m(n):
    """Distance cumulée (m) à la fin du jour n (n continu pour l'animation)."""
    return AR * R0 * (2 ** n - 1)


def vit_kmh(n):
    """Vitesse moyenne (km/h) s'il marche 24 h sur 24 le jour n."""
    return dem(n) * AR / JOUR_S * 3.6


assert dem(1) == 20 and dem(5) == 320 and round(dist_m(5) / 1000, 1) == 7.4
assert dist_m(7) / 1000 < MARATHON < dist_m(8) / 1000 and round(dist_m(8) / 1000, 1) == 61.2
assert 5.0 < vit_kmh(10) < 5.2                       # « il marche 24 h sur 24 » à ~5 km/h
assert 1.0 < JOUR_S / dem(13) < 1.1                  # « presque une demande par seconde »
assert dist_m(13) / 1000 < TDF < dist_m(14) / 1000 and round(dist_m(14) / 1000) == 3932
assert vit_kmh(15) < TGV < vit_kmh(16) and round(vit_kmh(16)) == 328
assert dist_m(17) / 1000 < TERRE < dist_m(18) / 1000 and round(dist_m(18) / 1000) == 62914
assert 1.5 < dist_m(18) / 1000 / TERRE < 1.6         # « une fois et demie »
assert vit_kmh(17) < SON < vit_kmh(18) and round(vit_kmh(18)) == 1311
assert dist_m(20) / 1000 < LUNE < dist_m(21) / 1000 and round(dist_m(21) / 1000) == 503316

# ---------------------------------------------------------------- chronologie
# (clé, durée, jour, légende, Gérard dit, décor)
RAW = [
    ("hook", 3.4, 0, "CE CHAT VA ENVOYER GÉRARD | *SUR LA LUNE.* À PIED.", None, "entree"),
    ("regle", 3.6, 0, "Michel veut sortir. | Puis *rentrer.* Puis sortir.", None, "entree"),
    ("regle2", 3.2, 0, "Règle : chaque jour, | il demande *deux fois plus.*", "Encore ?!", "entree"),
    ("j1", 3.6, 1, "Jour 1 : 20 demandes. | *6 m* aller, *6 m* retour.", None, "entree"),
    ("hesite", 3.4, 1, "Michel ne sort pas. | Il *réfléchit.*", None, "entree"),
    ("j5", 3.2, 5, "Jour 5 : 320 demandes. | Gérard a marché *7,4 km.*", None, "entree"),
    ("j8", 3.6, 8, "Jour 8 : 61,2 km. Plus | qu'*un marathon* (42,195 km).", None, "route"),
    ("j10", 3.4, 10, "Jour 10 : il marche *24 h sur 24.* | Il ne dort plus.", None, "entree"),
    ("j13", 3.4, 13, "Jour 13 : *presque une | demande par seconde.*", None, "entree"),
    ("chat", 3.2, 13, "Gérard installe | *une chatière.*", "Voilà !", "entree"),
    ("chat2", 3.6, 13, "Michel s'assoit devant. | Il *attend qu'on ouvre.*", None, "entree"),
    ("j14", 3.6, 14, "Jour 14 : 3 932 km. Plus que | le *Tour de France* (3 333 km).", None, "route"),
    ("j16", 3.6, 16, "Jour 16 : il court à *328 km/h.* | Un TGV : *320 km/h.*", None, "train"),
    ("j18", 3.8, 18, "Jour 18 : 62 914 km. | *1,5 fois* le tour de la Terre.", None, "terre"),
    ("mach", 3.4, 18, "Il ouvre la porte à *1 311 km/h.* | *Mur du son.*", None, "entree"),
    ("j21", 3.8, 21, "Jour 21 : 503 316 km. | Plus loin que *la Lune.*", None, "lune"),
    ("pluie", 3.4, 22, "Jour 22 : Gérard ouvre. | *Il pleut.*", None, "entree"),
    ("fin", 4.2, 22, "Michel veut essayer | *l'autre porte.*", "NON.", "entree"),
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
DAYS = [b["start"] for b in BEATS if b["n1"] > b["n0"]]
ROLL = .8
FLOOR = 1565


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
    if b["n1"] <= b["n0"] or f >= 1:
        return b["n1"]
    return lerp(b["n0"], b["n1"], f)


# ---------------------------------------------------------------- Gérard debout (repris de la vidéo 08)
def ger(c, x, floor, s, t, stage=0, hold=None, walk=0.0, lean=0.0, a=1.0):
    c.save()
    if a < 1:
        c.saveLayerAlpha(None, int(255 * a))
    bob = -abs(math.sin(t * 9)) * 16 * walk
    c.translate(x, floor + bob)
    c.rotate(lean)
    c.scale(s, s)
    c.translate(-790, -1516)
    sw = "#3F6FD8"
    draw_gerard(c, stage, t, False, 0, True)
    for sg in (-1, 1):
        arm = skia.Path()
        arm.moveTo(790 + sg * 96, 1160)
        if hold == "up" and sg == -1:
            arm.quadTo(790 - 150, 1120, 790 - 150, 1010)
        elif hold == "knob" and sg == -1:
            arm.quadTo(790 - 170, 1200, 790 - 230, 1240)
        else:
            sw_ = math.sin(t * 9 + (0 if sg < 0 else math.pi)) * 40 * walk
            arm.quadTo(790 + sg * 130 + sw_, 1250, 790 + sg * 118 + sw_, 1330)
        c.drawPath(arm, line(INK, 56))
        c.drawPath(arm, line(sw, 42))
    if hold == "tool":
        c.save()
        c.translate(640, 990)
        c.rotate(-30 + math.sin(t * 25) * 15)
        shape(c, rrect(-12, -10, 12, 90, 6), "#9B6A3C", 5)
        shape(c, rrect(-40, -36, 40, -6, 6), "#9B9FB0", 5)
        c.restore()
    if a < 1:
        c.restore()
    c.restore()


def gerbub(c, t, b, x, y):
    if not b["ger"]:
        return
    f = skia.Font(TF, 56)
    w = f.measureText(b["ger"])
    xx = clamp(x, w / 2 + 44, W - w / 2 - 44)
    bubble(c, xx, y, b["ger"], 56, back((t - b["start"] - .35) / .16), 2)


# ---------------------------------------------------------------- l'entrée
DL, DR, DT = 110, 430, 790          # porte du jardin
D2L, D2R = 800, 1040                # « l'autre porte »
GX_REST, GX_DOOR = 690, 520         # Gérard : fauteuil / porte
MX_IN = 290                         # Michel devant la porte


def outside(c, mode, t):
    r_ = skia.Rect.MakeLTRB(DL, DT, DR, FLOOR)
    c.save()
    c.clipRect(r_, skia.ClipOp.kIntersect, True)
    sky = {"jour": ("#5CB8F2", "#D3F1FF"), "nuit": ("#0E1440", "#2B3A7A"), "pluie": ("#6C7486", "#A9B0BE")}[mode]
    p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, DT), (0, FLOOR)], [col(sky[0]), col(sky[1])]))
    c.drawRect(r_, p)
    g = {"jour": "#7CC46E", "nuit": "#2E5A3A", "pluie": "#5E8A5A"}[mode]
    c.drawRect(skia.Rect.MakeLTRB(DL, 1300, DR, FLOOR), fill(g))
    shape(c, oval(300, 1080, 470, 1240), hexmix(g, "#1F5A2A", .4), 6)
    c.drawRect(skia.Rect.MakeLTRB(372, 1220, 398, 1310), fill("#7B4A2B"))
    if mode == "nuit":
        draw_moon(c, 200, 900, 40, t, "scared")
        for (sx, sy) in ((330, 860), (380, 960), (150, 1010)):
            c.drawCircle(sx, sy, 3, fill("#FFFFFF"))
    if mode == "pluie":
        for (cx_, cy_, rx) in ((180, 860, 110), (360, 880, 120)):
            shape(c, oval(cx_ - rx, cy_ - 50, cx_ + rx, cy_ + 50), "#8B92A3", 0)
        r = random.Random(1)
        for i in range(46):
            x0 = r.uniform(DL - 40, DR)
            y0 = (r.uniform(0, 900) + t * 1500) % 900 + DT
            c.drawLine(x0, y0, x0 + 12, y0 + 46, line("#DDE8FF", 4, .85))
    c.restore()


def door_leaf(c, x0, x1, a, colr="#3F8F6F", flap=False, flap_a=0.0, flap_k=1.0):
    """Battant articulé à gauche, a = 0 fermé … 1 ouvert (vu de biais)."""
    w = (x1 - x0) * (1 - .86 * a)
    sk = 46 * a
    p = poly([(x0, DT), (x0 + w, DT - sk), (x0 + w, FLOOR + sk), (x0, FLOOR)])
    shape(c, p, colr, 7)
    if a < .6:
        k = 1 - a / .6
        for (yy0, yy1) in ((DT + 60, DT + 330), (DT + 400, FLOOR - 60)):
            c.drawRect(skia.Rect.MakeLTRB(x0 + 40 * (1 - a), yy0, x0 + w - 40 * (1 - a), yy1), line(INK, 4, .35 * k))
        c.drawCircle(x0 + w - 36 * (1 - a), (DT + FLOOR) / 2, 15, fill("#F2C14E", k))
        c.drawCircle(x0 + w - 36 * (1 - a), (DT + FLOOR) / 2, 15, line(INK, 4, k))
        if flap:
            fx = x0 + w / 2
            fr = rrect(fx - 70 * (1 - a), FLOOR - 170, fx + 70 * (1 - a), FLOOR - 30, 16)
            shape(c, fr, "#2B2B36", 6, k * flap_k)
            c.save()
            c.translate(fx, FLOOR - 160)
            c.scale(1, math.cos(flap_a))
            shape(c, rrect(-58 * (1 - a), 0, 58 * (1 - a), 120, 10), "#BFD7E8", 4, k * flap_k)
            c.restore()


def cycle(p):
    """Un aller-retour : (x de Gérard, ouverture de porte, Michel dehors 0..1, marche)."""
    if p < .22:
        return lerp(GX_REST, GX_DOOR, eout(p / .22)), 0, 0, 1
    if p < .32:
        return GX_DOOR, eout((p - .22) / .1), 0, 0
    if p < .5:
        return GX_DOOR, 1, eout((p - .32) / .18), 0
    if p < .68:
        return GX_DOOR, 1, 1 - eout((p - .5) / .18), 0
    if p < .78:
        return GX_DOOR, 1 - eout((p - .68) / .1), 0, 0
    return lerp(GX_DOOR, GX_REST, eout((p - .78) / .22)), 0, 0, 1


def door_times():
    """Instants d'ouverture et de fermeture de la porte (pour le son)."""
    ev = []
    for key, per, t0 in (("regle", 3.2, .2), ("j1", 3.2, .2), ("j5", 1.5, .1)):
        b = BEATS[[x["key"] for x in BEATS].index(key)]
        k = 0
        while t0 + k * per + per * .78 < b["dur"]:
            s = b["start"] + t0 + k * per
            ev.append(("open", s + per * .22))
            ev.append(("close", s + per * .68))
            k += 1
    return ev


def footprints(c, n, a=1.0):
    r = random.Random(7)
    for i in range(n):
        x = r.uniform(DR + 20, D2L - 40)
        y = r.uniform(FLOOR + 30, FLOOR + 140)
        c.drawOval(skia.Rect.MakeLTRB(x - 14, y - 7, x + 14, y + 7), fill("#5A3520", .5 * a))


def wall_clock(c, t, speed, x=620, y=900):
    shape(c, oval(x - 66, y - 66, x + 66, y + 66), "#FFFFFF", 7)
    for k in range(12):
        a_ = k * math.pi / 6
        c.drawLine(x + math.cos(a_) * 52, y + math.sin(a_) * 52, x + math.cos(a_) * 60, y + math.sin(a_) * 60, line(INK, 4))
    a1 = t * speed - math.pi / 2
    a2 = t * speed / 12 - math.pi / 2
    c.drawLine(x, y, x + math.cos(a1) * 50, y + math.sin(a1) * 50, line(INK, 6))
    c.drawLine(x, y, x + math.cos(a2) * 34, y + math.sin(a2) * 34, line(INK, 9))


def room(c, t, mode="jour", a=0.0, flap=False, flap_a=0.0, clock=0.0, prints=0, flap_k=1.0):
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#F7DDAE"))
    for x in range(0, W, 120):
        c.drawRect(skia.Rect.MakeLTRB(x, 640, x + 60, FLOOR), fill("#F2D29C", .55))
    c.drawRect(skia.Rect.MakeLTRB(0, FLOOR - 34, W, FLOOR), fill("#FFF5E0"))
    c.drawRect(skia.Rect.MakeLTRB(0, FLOOR, W, H), fill("#7B4A2B"))
    c.drawLine(0, FLOOR, W, FLOOR, line(INK, 7))
    for i in range(5):
        c.drawLine(i * 240 + 60, FLOOR + 2, i * 300 - 180, H, line(INK, 4, .35))
    footprints(c, prints)
    # porte du jardin
    c.drawRect(skia.Rect.MakeLTRB(DL - 22, DT - 22, DR + 22, FLOOR), fill("#FFF5E0"))
    c.drawRect(skia.Rect.MakeLTRB(DL - 22, DT - 22, DR + 22, FLOOR), line(INK, 7))
    outside(c, mode, t)
    c.drawRect(skia.Rect.MakeLTRB(DL, DT, DR, FLOOR), line(INK, 6))
    # paillasson
    shape(c, rrect(DL + 10, FLOOR + 12, DR - 10, FLOOR + 56, 10), "#C8553D", 5)
    if clock:
        wall_clock(c, t, clock)
    # l'autre porte
    c.drawRect(skia.Rect.MakeLTRB(D2L - 18, DT + 40, D2R + 18, FLOOR), fill("#FFF5E0"))
    c.drawRect(skia.Rect.MakeLTRB(D2L - 18, DT + 40, D2R + 18, FLOOR), line(INK, 7))
    shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(D2L, DT + 58, D2R, FLOOR)), "#B5876A", 6)
    c.drawCircle(D2L + 34, (DT + FLOOR) / 2 + 20, 14, fill("#F2C14E"))
    c.drawCircle(D2L + 34, (DT + FLOOR) / 2 + 20, 14, line(INK, 4))
    return lambda: door_leaf(c, DL, DR, a, flap=flap, flap_a=flap_a, flap_k=flap_k)


def cat_at_door(c, t, out, mood="open"):
    """Michel : 0 = devant la porte, 1 = dehors (plus petit, sur l'herbe)."""
    x = lerp(MX_IN, 300, out)
    y = lerp(FLOOR + 30, 1330, out)
    s = lerp(.34, .2, out)
    draw_cat(c, x, y, s, t, mood, 0)


def scene_entree(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    mode = "nuit" if key in ("j10",) else "pluie" if key in ("pluie",) else "jour"
    if key in ("regle", "j1"):
        p = clamp((d_ - .2) / 3.2)
        gx, a, out, wk = cycle(p)
        leaf = room(c, t, mode, a, prints=0 if key == "regle" else 6)
        if out > 0:
            cat_at_door(c, t, out)
        leaf()
        if out <= 0:
            cat_at_door(c, t, 0)
        ger(c, gx, FLOOR + 30, .62, t, 1 if key == "j1" else 0, hold="knob" if a > 0 and gx == GX_DOOR else None, walk=wk)
        if key == "j1":
            u = clamp((d_ - .1) / .4)
            y = FLOOR + 110
            pe = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6, Color=col("#FFFFFF", u),
                            PathEffect=skia.DashPathEffect.Make([18, 12], 0))
            c.drawLine(DR - 40, y, GX_REST + 40, y, pe)
            text(c, "6 m", (DR + GX_REST) / 2, y + 70, 58, "#FFE14D", INK, 10, a=u)
        return
    if key == "j5":
        p = (clamp(d_ - .1) * 0 + (d_ - .1) / 1.5) % 1 if d_ > .1 else 0
        gx, a, out, wk = cycle(p)
        leaf = room(c, t, mode, a, prints=40)
        if out > 0:
            cat_at_door(c, t, out)
        leaf()
        if out <= 0:
            cat_at_door(c, t, 0)
        ger(c, gx, FLOOR + 30, .62, t, 2, hold="knob" if a > 0 and gx == GX_DOOR else None, walk=wk)
        return
    if key in ("j10", "j13", "mach"):
        per = {"j10": 1.4, "j13": .42, "mach": .14}[key]
        p = (d_ / per) % 1
        gx, a, out, wk = cycle(p)
        leaf = room(c, t, mode, a, clock={"j10": 6, "j13": 40, "mach": 120}[key], prints=90)
        if key == "mach":
            cat_at_door(c, t, 0, "open")
            leaf()
            # plusieurs Gérard flous
            for k in range(5):
                gx_k = lerp(GX_DOOR, GX_REST, (math.sin(t * 40 + k) + 1) / 2)
                ger(c, gx_k, FLOOR + 30, .62, t, 4 if False else 2, walk=1, lean=-8, a=.25 + .15 * (k == 0))
            cx, cy = 560, 1200
            u = clamp((d_ - .5) / .3)
            if u > 0:
                cone = skia.Path()
                cone.moveTo(cx - 300, cy)
                cone.quadTo(cx - 60, cy - 330, cx + 260, cy - 380)
                cone.quadTo(cx + 120, cy, cx + 260, cy + 380)
                cone.quadTo(cx - 60, cy + 330, cx - 300, cy)
                c.drawPath(cone, fill("#FFFFFF", .5 * u))
                c.drawPath(cone, line("#FFFFFF", 8, .9 * u))
            if d_ > .55:
                s_ = back((d_ - .55) / .18)
                c.save()
                c.translate(760, 1000)
                c.rotate(-8)
                c.scale(s_, s_)
                text(c, "BANG !", 0, 0, 130, "#FFE14D", INK, 14)
                c.restore()
                text(c, "Son : 1 235 km/h", 540, 1720, 50, "#FFFFFF", INK, 9, a=clamp((d_ - 1.2) / .2))
            return
        if out > 0:
            cat_at_door(c, t, out)
        leaf()
        if out <= 0:
            cat_at_door(c, t, 0)
        if key == "j13":
            for k in range(4, 0, -1):
                gx_k, _, _, _ = cycle(((d_ - k * .03) / per) % 1)
                ger(c, gx_k, FLOOR + 30, .62, t, 2, walk=1, a=.18)
        ger(c, gx, FLOOR + 30, .62, t, 3 if key == "j10" else 2, walk=wk if key == "j10" else 1,
            hold="knob" if a > 0 and gx == GX_DOOR else None)
        if key == "j10":
            for k in range(3):
                ph = (t * .8 + k / 3) % 1
                text(c, "z", gx + 90 + ph * 60, 900 - ph * 90, 40 + 20 * ph, "#FFFFFF", INK, 6, a=1 - ph)
        return
    if key == "hesite":
        leaf = room(c, t, mode, 1, prints=6)
        leaf()
        # Michel assis sur le seuil, tête vers dehors puis vers nous
        cat_at_door(c, t, .12, "open" if d_ < 2.2 else "bliss")
        tap = math.sin(t * 14) > 0
        ger(c, GX_DOOR, FLOOR + 30, .62, t, 1, hold="knob")
        # pied qui tape
        if d_ > .6:
            text(c, "tap", GX_DOOR + 140, FLOOR - 30 - (12 if tap else 0), 44, "#FFFFFF", INK, 8)
        if d_ > 1.2:
            text(c, "...", MX_IN + 40, 1150, 90, "#FFFFFF", INK, 10, a=clamp((d_ - 1.2) / .2))
        return
    if key in ("hook", "regle2"):
        leaf = room(c, t, mode, 0)
        leaf()
        sc = 1 + .02 * math.sin(t * 9) if key == "hook" else 1
        draw_cat(c, MX_IN, FLOOR + 30, .34 * sc, t, "open", 0)
        if key == "hook":
            if d_ > .9:
                bubble(c, MX_IN + 40, 1150, "mrrraa !", 52, back((d_ - .9) / .16), -3)
            ger(c, GX_REST, FLOOR + 30, .62, t, 0)
        else:
            gx = lerp(GX_REST, GX_DOOR, eout((d_ - .1) / .5))
            ger(c, gx, FLOOR + 30, .62, t, 2, walk=1 if d_ < .6 else 0)
            gerbub(c, t, b, gx - 20, 980)
        return
    if key == "chat":
        fl = clamp((d_ - 1.3) / .3)
        leaf = room(c, t, mode, 0, flap=fl > 0, flap_a=0, flap_k=fl)
        leaf()
        if 1.2 < d_ < 1.8:
            for k in range(6):
                a_ = k * math.pi / 3 + t
                rr = 60 + 140 * clamp((d_ - 1.2) / .5)
                text(c, "★", (DL + DR) / 2 + math.cos(a_) * rr, FLOOR - 100 + math.sin(a_) * rr * .5, 40, "#FFE14D", INK, 6)
        ger(c, GX_DOOR, FLOOR + 30, .62, t, 0, hold="tool" if d_ < 1.3 else "up")
        draw_cat(c, 640 + 220, FLOOR + 30, .3, t, "open", 0)
        if d_ > 1.4:
            gerbub(c, t, b, GX_DOOR + 30, 960)
        return
    if key == "chat2":
        leaf = room(c, t, mode, 0, flap=True, flap_a=0)
        leaf()
        cx = lerp(860, MX_IN, eout(d_ / .7))
        draw_cat(c, cx, FLOOR + 30, .34, t, "open", 0)
        if d_ > 1.0:
            bubble(c, MX_IN + 40, 1150, "mrrp ?", 52, back((d_ - 1.0) / .16), -3)
        ger(c, GX_REST + 40, FLOOR + 30, .62, t, 3)
        return
    if key == "pluie":
        p = clamp(d_ / 1.0)
        a = eout(p)
        leaf = room(c, t, mode, a)
        leaf()
        cat_at_door(c, t, 0, "open" if d_ < 1.8 else "bliss")
        ger(c, GX_DOOR, FLOOR + 30, .62, t, 1, hold="knob")
        if d_ > 1.8:
            bubble(c, MX_IN + 40, 1150, "non.", 52, back((d_ - 1.8) / .16), -3)
        return
    if key == "fin":
        leaf = room(c, t, "pluie", 0)
        leaf()
        cx = lerp(MX_IN, (D2L + D2R) / 2, eout((d_ - .2) / .9))
        draw_cat(c, cx, FLOOR + 30, .34, t, "wink" if d_ > 2.8 else "open", 0)
        if 1.2 < d_ < 2.6:
            bubble(c, cx - 20, 1150, "mrrraa !", 52, back((d_ - 1.2) / .16), 3)
        ger(c, GX_DOOR - 60, FLOOR + 30, .62, t, 3 if d_ > 1.5 else 2)
        if d_ > 1.5:
            gerbub(c, t, dict(b, start=b["start"] + 1.2), GX_DOOR - 60, 960)
        return


# ---------------------------------------------------------------- dehors : route, train, Terre, Lune
def sky_grad(c, a, b_, y0=400, y1=1500):
    p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, y0), (0, y1)], [col(a), col(b_)]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)


def scene_route(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    sky_grad(c, "#5CB8F2", "#E3F5FF")
    if key == "j14":
        for (x0, w0, h0) in ((-120, 600, 560), (300, 700, 700), (720, 600, 520)):
            shape(c, poly([(x0, FLOOR - 120), (x0 + w0 / 2, FLOOR - 120 - h0), (x0 + w0, FLOOR - 120)]), "#8C8FA3", 7)
            shape(c, poly([(x0 + w0 / 2 - 70, FLOOR - 120 - h0 + 90), (x0 + w0 / 2, FLOOR - 120 - h0),
                           (x0 + w0 / 2 + 70, FLOOR - 120 - h0 + 90)]), "#FFFFFF", 5)
    else:
        for (x0, w0) in ((-200, 800), (500, 900)):
            shape(c, oval(x0, FLOOR - 330, x0 + w0, FLOOR + 200), "#8FD07F", 7)
    c.drawRect(skia.Rect.MakeLTRB(0, FLOOR - 130, W, FLOOR), fill("#7CC46E"))
    c.drawRect(skia.Rect.MakeLTRB(0, FLOOR - 40, W, H), fill("#6F7480"))
    c.drawLine(0, FLOOR - 40, W, FLOOR - 40, line(INK, 6))
    for k in range(0, 6):
        x = k * 200
        c.drawRect(skia.Rect.MakeLTRB(x, FLOOR + 110, x + 110, FLOOR + 126), fill("#FFFFFF"))
    # arche fixe ; Gérard passe dessous
    ax = 640
    lab = "MARATHON : 42,195 km" if key == "j8" else "TOUR DE FRANCE : 3 333 km"
    colr = "#FFFFFF" if key == "j8" else "#FFD93B"
    for px in (ax - 330, ax + 330):
        shape(c, rrect(px - 16, 760, px + 16, FLOOR - 20, 8), "#D4D7E0", 5)
    shape(c, rrect(ax - 380, 720, ax + 380, 860, 18), colr, 7)
    sz = fit(lab, 56, 700)
    text(c, lab, ax, 812, sz, INK)
    gx = lerp(120, 1000, clamp((d_ - .1) / 3.1))
    if key == "j14":
        # un cycliste générique, dépassé
        bx = lerp(420, 640, clamp(d_ / 3.2))
        bike(c, bx, FLOOR - 10, t)
        if 1.6 < d_:
            bubble(c, bx + 40, 1080, "?!", 50, back((d_ - 1.6) / .16), 4)
    ger(c, gx, FLOOR + 20, .6, t, 2 if key == "j8" else 3, walk=1.4, lean=-4)
    if gx > ax and key == "j8":
        for k in range(8):
            r = random.Random(k)
            ph = clamp((t - b["start"] - 1.9) / 1.2)
            c.drawRect(skia.Rect.MakeXYWH(ax + r.uniform(-300, 300), 860 + ph * r.uniform(200, 600), 18, 12),
                       fill(r.choice(("#FFE14D", "#FF6A2B", "#59B36A", "#3F6FD8"))))


def bike(c, x, y, t):
    for wx in (x - 90, x + 90):
        c.drawCircle(wx, y - 70, 70, line(INK, 9))
        c.drawCircle(wx, y - 70, 70, line("#D4D7E0", 5))
    c.drawPath(poly([(x - 90, y - 70), (x - 10, y - 70), (x + 40, y - 170), (x - 50, y - 170)]), line("#D9534F", 12))
    c.drawLine(x + 40, y - 170, x + 90, y - 70, line("#D9534F", 12))
    # cycliste générique
    shape(c, rrect(x - 70, y - 300, x + 40, y - 190, 40), "#FFD93B", 6)
    shape(c, oval(x + 10, y - 380, x + 90, y - 300), "#F7C7A0", 6)
    shape(c, oval(x + 4, y - 396, x + 96, y - 340), "#3F6FD8", 5)


def scene_train(c, t, b):
    d_ = t - b["start"]
    sky_grad(c, "#F7B267", "#FFE9B8")
    c.drawRect(skia.Rect.MakeLTRB(0, FLOOR - 200, W, FLOOR), fill("#9BCB7F"))
    c.drawRect(skia.Rect.MakeLTRB(0, FLOOR - 20, W, H), fill("#8A8F9C"))
    c.drawLine(0, FLOOR - 20, W, FLOOR - 20, line(INK, 6))
    off = (t * 3000) % 300
    for k in range(-1, 6):
        x = k * 300 - off
        c.drawRect(skia.Rect.MakeLTRB(x, 760, x + 14, FLOOR - 20), fill("#5A5F6E"))
    c.drawLine(0, 790, W, 790, line("#3A3F55", 4))
    # train : arrive par la gauche et reste derrière
    tx = lerp(-300, 560, eout(d_ / 1.4)) + d_ * 10
    body = skia.Path()
    body.moveTo(tx - 1800, 1180)
    body.lineTo(tx - 120, 1180)
    body.quadTo(tx + 120, 1200, tx + 160, 1440)
    body.lineTo(tx - 1800, 1440)
    body.close()
    shape(c, body, "#F2F2F7", 8)
    c.drawRect(skia.Rect.MakeLTRB(tx - 1800, 1350, tx + 140, 1380), fill("#3F6FD8"))
    for k in range(8):
        wx = tx - 300 - k * 190
        shape(c, rrect(wx - 70, 1220, wx + 40, 1300, 14), "#4D6A8A", 5)
    shape(c, poly([(tx - 90, 1210), (tx + 40, 1220), (tx + 90, 1300), (tx - 90, 1300)]), "#4D6A8A", 5)
    text(c, "TGV : 320 km/h", max(tx - 300, 220), 1150, 50, "#FFFFFF", INK, 9)
    gx = 840 + 20 * math.sin(t * 3)
    ger(c, gx, FLOOR, .5, t, 3, walk=2.2, lean=-14)
    r = random.Random(int(t * 15))
    for k in range(7):
        y = r.uniform(1000, 1500)
        c.drawLine(gx - 160, y, gx - 160 - r.uniform(120, 300), y, line("#FFFFFF", 6, .8))
    text(c, "Gérard : 328 km/h", 640, 940, 54, "#FFE14D", INK, 10, a=clamp((d_ - .8) / .2))


def tiny_ger(c, x, y, s, t, rot=0.0):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    ger(c, 0, 0, s, t, 2, walk=1.5)
    c.restore()


def scene_terre(c, t, b):
    d_ = t - b["start"]
    c.drawImage(STARS, 0, 0)
    cx, cy, R = 540, 1120, 300
    img, x0, y0 = earth_rgba(R, cx=cx, cy=cy)
    c.drawImage(img, x0, y0)
    c.drawCircle(cx, cy, R, line(INK, 7))
    RR = R + 40
    turns = dist_m(18) / 1000 / TERRE
    u = eout(clamp((d_ - .2) / 2.6)) * turns
    a0 = -math.pi / 2
    # trace des pas
    p = skia.Path()
    steps = int(u * 120)
    for i in range(steps):
        a = a0 + 2 * math.pi * i / 120
        rr = RR + 14 * (i // 120)
        c.drawCircle(cx + math.cos(a) * rr, cy + math.sin(a) * rr, 5, fill("#FFE14D", .9))
    a = a0 + 2 * math.pi * u
    rr = RR + 14 * int(u) + 20
    tiny_ger(c, cx + math.cos(a) * rr, cy + math.sin(a) * rr, .16, t, math.degrees(a) + 90)
    text(c, "TOUR DE LA TERRE : 40 075 km", 540, 1600, 52, "#FFFFFF", INK, 9)
    if u >= 1:
        text(c, "1 TOUR !", 540, 700, 80, "#FFE14D", INK, 12, a=clamp((u - 1) / .1))
        text(c, "ET DEMI.", 540, 790, 70, "#FFFFFF", INK, 11, a=clamp((u - 1.45) / .08))


def scene_lune(c, t, b):
    d_ = t - b["start"]
    c.drawImage(STARS, 0, 0)
    ex, mx, y = 120, 120 + 640, 1100
    img, x0, y0 = earth_rgba(70, cx=ex, cy=y)
    c.drawImage(img, x0, y0)
    c.drawCircle(ex, y, 70, line(INK, 5))
    draw_moon(c, mx, y, 50, t, "scared")
    c.drawPath(skia.Path().moveTo(ex, y + 130).lineTo(mx, y + 130),
               skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5, Color=col("#FFFFFF"), PathEffect=skia.DashPathEffect.Make([18, 12], 0)))
    text(c, "LUNE : 384 400 km", (ex + mx) / 2, y + 200, 50, "#FFFFFF", INK, 9)
    full = ex + (mx - ex) * dist_m(21) / 1000 / LUNE
    q = eout(clamp((d_ - .2) / 2.4))
    gx = lerp(ex + 60, full, q)
    c.drawLine(ex + 60, y - 10, gx, y - 10, line("#FFE14D", 6, .8))
    tiny_ger(c, gx, y - 14, .3, t)
    if q > .98:
        text(c, "503 316 km", min(full - 20, 900), y - 260, 50, "#FFE14D", INK, 9, a=clamp((d_ - 2.6) / .2))
        bubble(c, mx, y - 120, "?!", 40, back((d_ - 2.7) / .16), -4)


# ---------------------------------------------------------------- HUD, légende, carton
def heat_c(n):
    u = clamp(n / 21)
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


def size_txt(m):
    if m < 999.5:
        return "%d M" % round(m)
    k = m / 1000
    if k < 99.95:
        return ("%.1f KM" % k).replace(".", ",")
    return "%s KM" % nb(round(k))


assert size_txt(dist_m(1)) == "240 M" and size_txt(dist_m(5)) == "7,4 KM" and size_txt(dist_m(8)) == "61,2 KM"
assert size_txt(dist_m(14)) == "3 932 KM" and size_txt(dist_m(18)) == "62 914 KM" and size_txt(dist_m(21)) == "503 316 KM"


def hud(c, t, b):
    n = day_at(t)
    colr = heat_c(n)
    d_ = t - b["start"]
    pop = 1 + .14 * (1 - eout(d_ / .22)) if (b["n1"] != b["n0"]) else 1.0
    c.save()
    c.translate(540, 262)
    c.scale(pop, pop)
    pan = rrect(-420, -135, 420, 135, 44)
    c.drawPath(pan, fill("#14121C", .94))
    c.drawPath(pan, line(colr, 8))
    head = "GÉRARD A MARCHÉ"
    big = size_txt(dist_m(n))
    nd = round(n)
    low = "Jour %d · %s demandes" % (nd, nb(dem(nd))) if nd >= 1 else "Jour 0"
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
    c.translate(540, 700)
    c.scale(s, s)
    text(c, "À SUIVRE :", 0, 0, 86, "#FFFFFF")
    text(c, "L'AUTRE PORTE.", 0, 128, 86, "#FFD93B")
    c.restore()
    a = clamp((d_ - .5) / .25)
    for i, l in enumerate(("Très approximatif : 20 demandes le jour 1",
                           "et 12 m par aller-retour (estimations),",
                           "×2 chaque jour, sans pause ni sommeil.",
                           "Marathon : 42,195 km. Tour de France 2026 : 3 333 km.",
                           "TGV : 320 km/h. Son : 1 235 km/h.",
                           "Terre : 40 075 km. Lune : 384 400 km.",
                           "Gérard va bien. Il est assis.")):
        s_ = fit(l, 44, 960)
        text(c, l, 540, 1000 + i * 62, s_, "#A9A6BC", a=a)


SCN = dict(entree=scene_entree, route=scene_route, train=scene_train, terre=scene_terre, lune=scene_lune)


def shake_amp(t):
    amp = 0
    for tk in DAYS:
        d_ = t - tk
        if 0 <= d_ < .22:
            amp = max(amp, 8 * (1 - d_ / .22))
    for key, a0, dur in (("mach", .55, .6),):
        d_ = t - K[key] - a0
        if 0 <= d_ < dur:
            amp = max(amp, 26 * (1 - d_ / dur))
    return amp


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
    hud(c, t, b)
    caption(c, t)


_sp = [K["j1"], K["j8"], K["j10"], K["j14"], K["mach"], K["pluie"], CARD, END]
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
