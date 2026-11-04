"""Michel fait tomber des objets de plus en plus gros, du verre à la tour Eiffel."""
import math, random, sys, os, subprocess
import numpy as np
import skia
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "moteur"))
import art
from art import (fill, line, col, hexmix, poly, rrect, oval, shape, text, jitter, clamp, lerp, eout, ein, back,
                 draw_cat, draw_gerard, draw_eiffel, bubble, wrap_rich, TF, INK, W, H, FPS, ROWS)

# ---------------------------------------------------------------- chiffres (calculés, pas recopiés)
G = 9.81
TABLE_M = .75                 # table standard
MU = .5                       # frottement très approximatif
CHAT = 4.0                    # kg
T_CHUTE = math.sqrt(2 * TABLE_M / G)        # 0,39 s
REACTION = .25                # s, réaction visuelle moyenne
M_VERRE, M_FRIGO, M_TOUR = .25, 65, 1.01e7
FUSEE = 7.5e6 * 4.44822       # N, Saturn V au décollage
N_MICHELS = round(M_FRIGO * MU / CHAT)      # 8
N_VERRES = M_TOUR / M_VERRE                 # 40,4 millions
N_FUSEES = MU * M_TOUR * G / FUSEE          # 1,48
assert N_MICHELS == 8 and round(N_VERRES / 1e6) == 40 and round(N_FUSEES, 1) == 1.5 and round(T_CHUTE, 2) == .39

# n° : (nom, masse affichée, prix en €, None = inestimable)
OBJ = {1: ("un verre", "250 g", 3), 2: ("une tasse", "300 g", 8), 3: ("le vase de Tatie", "2 kg", 30), 4: ("la télé", "19 kg", 500),
       5: ("le frigo", "65 kg", 700), 6: ("le piano", "250 kg", 5000), 7: ("la voiture", "1,1 tonne", 15000), 8: ("un bus", "12 tonnes", 290000),
       9: ("un avion", "42 tonnes", 1e8), 10: ("la Liberté", "200 tonnes", None), 11: ("la tour Eiffel", "10 100 tonnes", None), 12: ("le dernier verre", "250 g", 3)}

# ---------------------------------------------------------------- chronologie
# (objet, durée, légende, Gérard dit, clé, décor)
RAW = [
    (1, 3.0, "CE CHAT FAIT TOUT TOMBER. | *MÊME LA TOUR EIFFEL.*", None, "hook", "salon"),
    (1, 2.6, "Un verre. *250 g.* | Il fixe Gérard dans les yeux.", "Michel...", "verre", "salon"),
    (1, 2.8, "*0,39 seconde* de chute. | Gérard réagit en 0,25. | Il est à 3 mètres.", None, "expl", "salon"),
    (2, 1.7, "Sa tasse préférée.", None, "tasse", "salon"),
    (3, 1.8, "Le vase de Tatie.", "Tatie...", "vase", "salon"),
    (4, 2.2, "La télé. *19 kg.* | Il force à peine.", "Bon.", "tele", "salon"),
    (5, 2.8, "Le frigo. *65 kg.* | Il faut la force de *8 Michel.*", None, "frigo", "salon"),
    (5, 1.2, "Il s'en fiche.", None, "frigo2", "salon"),
    (6, 2.8, "Le piano. *250 kg.* | Note finale : *un do.*", "Je n'en jouais pas.", "piano", "salon"),
    (7, 2.2, "Gérard range tout dehors. | *Michel monte sur le toit.*", "Ah non.", "toit", "toit"),
    (7, 2.9, "La voiture. *1,1 tonne.* | Personne ne sait | comment elle est montée.", None, "voiture", "toit"),
    (8, 3.0, "Un bus. *12 tonnes.* Vide : | Michel n'est pas un monstre.", "C'est pas ma ligne !", "bus", "toit"),
    (9, 1.6, "Gérard fuit en barque.", None, "barque", "mer"),
    (9, 3.1, "Un avion de ligne. *42 tonnes.* | Vide aussi. Michel insiste.", None, "avion", "mer"),
    (10, 2.6, "La statue de la Liberté. | *200 tonnes.*", None, "statue0", "mer"),
    (10, 2.4, "Un cadeau de la France. | *Michel l'a rendu.*", "Désolé, New York.", "statue", "mer"),
    (11, 2.4, "Retour à Paris. | *La tour Eiffel. 10 100 tonnes.*", "Pas encore elle...", "tour0", "paris"),
    (11, 1.8, "Autant que | *40 millions de verres.*", None, "tour1", "paris"),
    (11, 2.2, "Pour la faire glisser : | *1,5 fusée Saturn V.*", None, "tour2", "paris"),
    (11, 1.7, "Michel utilise | *une patte.*", None, "tour3", "paris"),
    (11, 3.0, "Il regarde Gérard.", None, "chute", "paris"),
    (11, 1.7, "Dans la Seine.", None, "seine", "paris"),
    (12, 2.2, "Gérard a compris. | Michel pousse *si on regarde.*", "Ah !", "fin0", "fin"),
    (12, 2.6, "Il pose son dernier verre. | Il sort sur la pointe des pieds.", None, "fin1", "fin"),
    (12, 1.4, "Une heure.", None, "h1", "fin"),
    (12, 1.4, "Quatre heures.", None, "h4", "fin"),
    (12, 1.8, "Michel ne bouge pas. | *Le verre non plus.*", None, "calme", "fin"),
    (12, 1.7, "Gérard jette un œil.", None, "oeil", "fin"),
    (12, 1.4, None, "NON !", "dernier", "fin"),
    (12, 2.2, "Il a attendu. | *Quatre heures.*", None, "stare", "fin"),
]
CARD_DUR = 2.6
BEATS = []
_t = 0.0
for n_, dur, cap, ger, key, ph_ in RAW:
    BEATS.append(dict(n=n_, start=_t, dur=dur, cap=cap, ger=ger, key=key, ph=ph_))
    _t += dur
CARD = _t
END = CARD + CARD_DUR
K = {b["key"]: b["start"] for b in BEATS}


def beat_at(t):
    cur = BEATS[0]
    for b in BEATS:
        if b["start"] <= t:
            cur = b
        else:
            break
    return cur


# ---------------------------------------------------------------- géométrie des décors
GY = 1560                     # sol du salon
TY = 1210                     # dessus de la table
TL, TE = 50, 690              # bords de la table
CAT_S = .62
ROOF, ROOF_E, ROAD = 900, 650, 1470
QUAY, QUAY_E, SEA = 1060, 650, 1400
PARIS_G = 1400
SALON_F = GY - 8


# o = dict(key, x0, y0, xE, yf, tp, s, tf, h, w, cols, rot, vx, shake)
def O(key, x0, y0, xE, yf, tp, s, tf, h, w, cols, rot=120, vx=60, shake=8, cat=(260, CAT_S)):
    return dict(key=key, x0=x0, y0=y0, xE=xE, yf=yf, tp=tp, s=s, tf=tf, h=h, w=w, cols=cols, rot=rot, vx=vx, shake=shake, cat=cat, ts=K[key])


CR = ("#FFFFFF", "#BEE8FF", "#7EC8FF")
OBJS = {
    "verre": O("verre", 545, TY, TE + 8, SALON_F, .9, .35, T_CHUTE, 118, 76, CR, 170, 40, 5),
    "tasse": O("tasse", 545, TY, TE + 8, SALON_F, .35, .25, T_CHUTE, 90, 104, ("#FFFFFF", "#F2F2F7", "#E8627A"), 200, 44, 6),
    "vase": O("vase", 540, TY, TE + 10, SALON_F, .4, .28, T_CHUTE, 210, 120, ("#3F6FD8", "#FFFFFF", "#F4C542"), 160, 50, 8),
    "tele": O("tele", 500, TY, TE + 30, SALON_F, .55, .4, .42, 240, 340, ("#20202B", "#3F6FD8", "#8A8FA0"), 110, 70, 12, (170, CAT_S)),
    "frigo": O("frigo", 530, TY, TE + 40, SALON_F, 1.0, .55, .42, 420, 190, ("#F2F2F7", "#C9CBD6", "#7EC8FF"), 100, 70, 16, (170, CAT_S)),
    "piano": O("piano", 500, TY, TE + 60, SALON_F, .7, .6, .42, 300, 350, ("#23202C", "#FFFFFF", "#5A3A22"), 100, 60, 22, (170, CAT_S)),
    "voiture": O("voiture", 440, ROOF, ROOF_E + 50, ROAD, .9, .55, .55, 110, 240, ("#3F6FD8", "#CDEBFF", "#23202C"), 150, 70, 20, (110, .36)),
    "bus": O("bus", 400, ROOF, ROOF_E + 60, ROAD, 1.0, .65, .55, 170, 470, ("#E8C24A", "#CDEBFF", "#23202C"), 110, 60, 28, (80, .36)),
    "avion": O("avion", 372, QUAY, QUAY_E + 170, SEA + 60, 1.0, .85, .6, 190, 600, ("#F2F2F7", "#D9534F", "#7EC8FF"), 40, 60, 30, (44, .18)),
}
# impacts : temps absolu
IMP = {k: o["ts"] + o["tp"] + o["s"] + o["tf"] for k, o in OBJS.items()}
STATUE_T0 = K["statue"] + .15
STATUE_DUR = 1.05
IMP["statue"] = STATUE_T0 + STATUE_DUR
TOUR_DUR = 3.0
TOUR_T0 = K["chute"]
IMP["tour"] = K["seine"]
LAST_TP, LAST_S, LAST_TF = .35, .28, T_CHUTE
LAST = O("dernier", 545, TY, TE + 8, SALON_F, LAST_TP, LAST_S, LAST_TF, 118, 76, CR, 170, 40, 7)
IMP["dernier"] = LAST["ts"] + LAST_TP + LAST_S + LAST_TF


def facture(t):
    tot = 0
    inf = False
    last = False
    for key, nn in (("verre", 1), ("tasse", 2), ("vase", 3), ("tele", 4), ("frigo", 5), ("piano", 6), ("voiture", 7), ("bus", 8), ("avion", 9), ("statue", 10), ("tour", 11), ("dernier", 12)):
        if t >= IMP[key]:
            v = OBJ[nn][2]
            if nn == 12:
                last = True
            elif v is None:
                inf = True
            else:
                tot += v
    if inf:
        return "inestimable + 3 €" if last else "inestimable"
    return euros(tot)


def grp(n):
    s = str(int(round(n)))
    o = []
    while s:
        o.append(s[-3:])
        s = s[:-3]
    return " ".join(reversed(o))


def euros(v):
    if v < 1e6:
        return grp(v) + " €"
    return "%d millions €" % round(v / 1e6)


# ---------------------------------------------------------------- objets (origine : milieu de la base)
def d_verre(c):
    p = poly([(-34, -112), (34, -112), (26, 0), (-26, 0)])
    c.drawPath(poly([(-29, -74), (29, -74), (26, 0), (-26, 0)]), fill("#7EC8FF", .75))
    c.drawPath(p, fill("#E9F6FF", .32))
    c.drawPath(p, line(INK, 6))
    c.drawLine(-18, -96, -15, -28, line("#FFFFFF", 5, .9))


def d_tasse(c):
    h_ = skia.Path()
    h_.addOval(skia.Rect.MakeLTRB(26, -70, 72, -18))
    c.drawPath(h_, line(INK, 16))
    c.drawPath(h_, line("#FFFFFF", 7))
    shape(c, rrect(-48, -88, 42, 0, 14), "#FFFFFF", 6)
    c.drawCircle(-14, -52, 11, fill("#E8627A"))
    c.drawCircle(4, -52, 11, fill("#E8627A"))
    c.drawPath(poly([(-25, -47), (15, -47), (-5, -24)]), fill("#E8627A"))


def d_vase(c):
    p = skia.Path()
    p.moveTo(-30, -206)
    p.lineTo(30, -206)
    p.cubicTo(24, -160, 66, -130, 56, -66)
    p.cubicTo(50, -24, 36, -6, 30, 0)
    p.lineTo(-30, 0)
    p.cubicTo(-36, -6, -50, -24, -56, -66)
    p.cubicTo(-66, -130, -24, -160, -30, -206)
    p.close()
    shape(c, p, "#3F6FD8", 6)
    for yy, cc in ((-110, "#F4C542"), (-70, "#FFFFFF")):
        c.drawLine(-52, yy, 52, yy, line(cc, 10))


def d_tele(c):
    shape(c, rrect(-40, -40, 40, 0, 6), "#3A3A48", 6)
    shape(c, rrect(-170, -238, 170, -34, 12), "#20202B", 7)
    c.drawRect(skia.Rect.MakeLTRB(-156, -224, 156, -48), fill("#3F6FD8"))
    c.drawCircle(0, -136, 46, fill("#FFFFFF", .22))
    c.drawPath(poly([(-16, -162), (-16, -110), (28, -136)]), fill("#FFFFFF", .75))


def d_frigo(c):
    shape(c, rrect(-95, -420, 95, 0, 22), "#F2F2F7", 7)
    c.drawLine(-95, -270, 95, -270, line(INK, 6))
    for a, b in ((-340, -292), (-240, -150)):
        c.drawLine(-68, a, -68, b, line("#8A8FA0", 11))
    # aimant et note
    shape(c, rrect(10, -240, 72, -170, 3), "#FFE14D", 4)
    c.drawLine(20, -218, 62, -218, line(INK, 3))
    c.drawLine(20, -196, 54, -196, line(INK, 3))
    c.drawCircle(41, -238, 9, fill("#E0202B"))


def d_piano(c):
    shape(c, rrect(-175, -300, 175, -60, 12), "#23202C", 7)
    shape(c, rrect(-175, -150, 175, -108, 4), "#F7F4EA", 6)
    for x in range(-155, 165, 24):
        c.drawLine(x, -150, x, -108, line(INK, 3))
        if (x + 155) % 72:
            c.drawRect(skia.Rect.MakeLTRB(x - 6, -150, x + 6, -127), fill(INK))
    for x in (-150, 150):
        shape(c, rrect(x - 16, -66, x + 16, 0, 5), "#23202C", 6)
    shape(c, rrect(-110, -262, 110, -202, 4), "#3A3647", 5)
    c.drawLine(-98, -246, 98, -246, line("#FFFFFF", 3, .55))
    c.drawLine(-98, -222, 98, -222, line("#FFFFFF", 3, .55))


def d_voiture(c):
    k = 1.5
    c.save()
    c.scale(k, k)
    c.translate(0, -21)
    shape(c, rrect(-80, -44, 80, 0, 16), "#3F6FD8", 5)
    shape(c, poly([(-44, -44), (-26, -78), (34, -78), (54, -44)]), "#CDEBFF", 5)
    for wx in (-48, 48):
        c.drawCircle(wx, 2, 19, fill(INK))
        c.drawCircle(wx, 2, 8, fill("#B8BCC8"))
    c.restore()


def d_bus(c):
    shape(c, rrect(-235, -170, 235, -26, 22), "#E8C24A", 7)
    for x in range(-210, 200, 78):
        shape(c, rrect(x, -148, x + 62, -92, 6), "#CDEBFF", 4)
    c.drawRect(skia.Rect.MakeLTRB(-233, -74, 233, -60), fill("#D9534F"))
    for wx in (-150, 150):
        c.drawCircle(wx, -24, 26, fill(INK))
        c.drawCircle(wx, -24, 11, fill("#B8BCC8"))


def d_avion(c):
    # dérive
    shape(c, poly([(-282, -74), (-332, -176), (-284, -176), (-200, -74)]), "#D9534F", 6)
    p = skia.Path()
    p.moveTo(-300, -60)
    p.lineTo(-180, -102)
    p.lineTo(220, -102)
    p.quadTo(308, -96, 318, -58)
    p.quadTo(306, -24, 220, -22)
    p.lineTo(-180, -22)
    p.close()
    shape(c, p, "#F2F2F7", 7)
    for x in range(-160, 210, 30):
        c.drawRoundRect(skia.Rect.MakeLTRB(x, -82, x + 16, -62), 5, 5, fill("#2C3550"))
    c.drawRect(skia.Rect.MakeLTRB(-180, -50, 240, -40), fill("#D9534F"))
    shape(c, poly([(235, -86), (292, -86), (300, -60), (244, -60)]), "#2C3550", 4)
    shape(c, poly([(-60, -44), (60, -44), (-20, 18), (-92, 18)]), "#C9CBD6", 6)
    for wx in (-130, 170):
        c.drawLine(wx, -22, wx, -6, line(INK, 7))
        c.drawCircle(wx, -5, 10, fill(INK))


D = dict(verre=d_verre, tasse=d_tasse, vase=d_vase, tele=d_tele, frigo=d_frigo, piano=d_piano, voiture=d_voiture, bus=d_bus, avion=d_avion, dernier=d_verre)


def d_statue(c, h=440):
    """Figure drapée générique, torche levée. Base en (0,0), haut de la torche en (0,-h)."""
    u = h / 440
    c.save()
    c.scale(u, u)
    V, VF = "#6FB9A2", "#4C957F"
    # robe
    p = skia.Path()
    p.moveTo(-58, -300)
    p.lineTo(52, -300)
    p.cubicTo(66, -190, 84, -80, 92, 0)
    p.lineTo(-92, 0)
    p.cubicTo(-84, -80, -72, -190, -58, -300)
    p.close()
    shape(c, p, V, 6)
    for x0, x1 in ((-36, -56), (-6, -14), (26, 34), (44, 66)):
        c.drawLine(x0, -270, x1, -6, line(VF, 7))
    # bras gauche et tablette
    shape(c, rrect(-92, -226, -40, -148, 8), VF, 5)
    # bras levé + torche
    c.drawLine(44, -290, 68, -382, line(INK, 42))
    c.drawLine(44, -290, 68, -382, line(V, 30))
    shape(c, rrect(54, -424, 84, -380, 6), VF, 5)
    fl = poly([(50, -424), (88, -424), (82, -446), (70, -472), (58, -446)])
    shape(c, fl, "#FFC531", 5)
    # tête + couronne
    for a in (-60, -35, -10, 15, 40, 65):
        r = math.radians(a - 90)
        c.drawLine(-4 + 36 * math.cos(r), -350 + 36 * math.sin(r), -4 + 70 * math.cos(r), -350 + 70 * math.sin(r), line(INK, 15))
        c.drawLine(-4 + 36 * math.cos(r), -350 + 36 * math.sin(r), -4 + 70 * math.cos(r), -350 + 70 * math.sin(r), line(V, 7))
    shape(c, oval(-42, -388, 34, -300), V, 6)
    shape(c, rrect(-48, -376, 40, -356, 6), VF, 4)
    c.drawCircle(-18, -338, 5, fill(INK))
    c.drawCircle(10, -338, 5, fill(INK))
    c.drawLine(-14, -314, 6, -314, line(INK, 4))
    c.restore()


# ---------------------------------------------------------------- mouvements
def obj_state(o, t):
    """x, y, rotation, statut ('wait', 'on', 'fall', 'gone')."""
    d_ = t - o["ts"]
    if d_ < 0:
        return o["x0"], o["y0"], 0, "wait"
    if d_ < o["tp"]:
        nudge = clamp(d_ / o["tp"]) * 8
        return o["x0"] + nudge, o["y0"], 0, "on"
    if d_ < o["tp"] + o["s"]:
        f = (d_ - o["tp"]) / o["s"]
        return lerp(o["x0"] + 8, o["xE"], f * f), o["y0"], 0, "on"
    d2 = d_ - o["tp"] - o["s"]
    if d2 < o["tf"]:
        f = d2 / o["tf"]
        return o["xE"] + o["vx"] * f, lerp(o["y0"], o["yf"], f * f), o["rot"] * f, "fall"
    return o["xE"] + o["vx"], o["yf"], o["rot"], "gone"


def draw_obj(c, o, t):
    x, y, r, st = obj_state(o, t)
    if st in ("wait", "gone"):
        return
    pop = back((t - o["ts"]) / .18) if o["key"] not in ("verre", "dernier", "voiture") else 1
    c.save()
    c.translate(x, y - o["h"] / 2)
    c.rotate(r)
    c.translate(0, o["h"] / 2)
    c.scale(pop, pop)
    D[o["key"]](c)
    c.restore()


def paw(c, x0, y0, x1, y1, s=1.0):
    """Une patte orange, très extensible."""
    p = skia.Path()
    p.moveTo(x0, y0)
    p.quadTo((x0 + x1) / 2, (y0 + y1) / 2 - 18 * s, x1, y1)
    c.drawPath(p, line(INK, 54 * s))
    c.drawPath(p, line("#F49A3A", 38 * s))
    shape(c, oval(x1 - 31 * s, y1 - 27 * s, x1 + 31 * s, y1 + 27 * s), "#FFE1B0", 5 * s)
    for dy in (-7, 7):
        c.drawLine(x1 + 8 * s, y1 + dy * s, x1 + 20 * s, y1 + dy * s, line(INK, 3 * s))


def tap_ext(d_, tp):
    """Extension de la patte : deux petits tapotements avant la vraie poussée."""
    if d_ < 0:
        return 0
    if d_ >= tp:
        return 1
    return abs(math.sin(d_ / tp * math.pi * 2)) ** 1.5 * .96


def pushing(c, o, t, cat):
    d_ = t - o["ts"]
    x, y, r, st = obj_state(o, t)
    cx, s = cat
    y0 = o["y0"] - 130 * s
    x0 = cx + 95 * s
    yy = o["y0"] - min(o["h"] * .3, 150)
    if st == "on":
        tip = x - o["w"] / 2 - 18 * s
        e = tap_ext(d_, o["tp"])
        paw(c, x0, y0, lerp(x0 + 10, tip, e), lerp(y0, yy, e), s)
    elif st == "fall":
        d2 = d_ - o["tp"] - o["s"]
        f = clamp(1 - d2 / .3)
        if f > 0:
            tip = o["xE"] - o["w"] / 2 - 18 * s
            paw(c, x0, y0, lerp(x0 + 10, tip, f), lerp(y0, yy, f), s)


def burst(c, x, y, d_, colors, n=26, spread=380, up=620, size=14, seed=1, floor=None, g=1700, keep=True):
    """Éclats ballistiques qui restent au sol."""
    if d_ < 0:
        return
    r = random.Random(seed)
    fl = floor if floor is not None else y
    for i in range(n):
        vx, vy = r.uniform(-spread, spread), -r.uniform(up * .25, up)
        sz = r.uniform(size * .45, size)
        rot0, w = r.uniform(0, 360), r.uniform(-500, 500)
        cc = colors[i % len(colors)]
        # temps d'atterrissage
        tl_ = (-vy + math.sqrt(max(vy * vy + 2 * g * (fl - y), 0))) / g
        tt = min(d_, tl_)
        xx = x + vx * tt
        yy = y + vy * tt + .5 * g * tt * tt
        if d_ > tl_ and not keep:
            continue
        c.save()
        c.translate(xx, yy)
        c.rotate(rot0 + w * tt)
        c.drawPath(poly([(-sz, sz * .55), (sz * .2, -sz * .8), (sz, sz * .4)]), fill(cc))
        c.drawPath(poly([(-sz, sz * .55), (sz * .2, -sz * .8), (sz, sz * .4)]), line(INK, 2.5))
        c.restore()


def splash(c, x, y, d_, k=1.0, seed=2):
    """Gerbe d'eau."""
    if d_ < 0 or d_ > 2.6:
        return
    r = random.Random(seed)
    a = clamp(2.6 - d_)
    # colonne
    hh = 620 * k * math.sin(clamp(d_ / 1.6) * math.pi)
    if hh > 2:
        wd = 150 * k * (1 + d_ * .3)
        p = skia.Path()
        p.moveTo(x - wd, y + 30)
        p.cubicTo(x - wd * .35, y - hh * .5, x - wd * .3, y - hh, x, y - hh)
        p.cubicTo(x + wd * .3, y - hh, x + wd * .35, y - hh * .5, x + wd, y + 30)
        p.close()
        c.drawPath(p, fill("#BEE8FF", .92 * a))
        c.drawPath(p, line("#FFFFFF", 8, a))
    for i in range(60):
        an = r.uniform(-2.7, -.45)
        sp = r.uniform(300, 1300) * k
        rd = r.uniform(6, 20) * max(k, .7)
        xx = x + math.cos(an) * sp * d_
        yy = y + math.sin(an) * sp * d_ + .5 * 1500 * d_ * d_
        if yy < y + 80:
            c.drawCircle(xx, yy, rd, fill("#FFFFFF" if i % 3 else "#7EC8FF", a))
            c.drawCircle(xx, yy, rd, line(INK, 2, a * .6))


def gerard(c, x, gy, k, t, stage=0, vib=0):
    c.save()
    c.translate(x - 790 * k, gy - 1498 * k)
    c.scale(k, k)
    draw_gerard(c, stage, t, False, vib, True)
    c.restore()


def ger_bubble(c, t, b, x, gy, k, rot=2, minx=None):
    if not b["ger"]:
        return
    s_ = back((t - b["start"]) / .16)
    f = skia.Font(TF, 46)
    w = f.measureText(b["ger"])
    xx = clamp(x - 70 * max(k, .5), w / 2 + 44, W - w / 2 - 44)
    bubble(c, xx, gy - 594 * k - 80, b["ger"], 46, s_, rot)


def arrow_label(c, x, y, label="MICHEL", ln=120):
    text(c, label, clamp(x, 110, W - 110), y - ln - 18, 44, "#FFE14D", INK, 10)
    c.drawLine(x, y - ln, x, y, line(INK, 13))
    c.drawLine(x, y - ln, x, y, line("#FFE14D", 7))
    c.drawPath(poly([(x - 22, y - 24), (x + 22, y - 24), (x, y + 4)]), fill("#FFE14D"))
    c.drawPath(poly([(x - 22, y - 24), (x + 22, y - 24), (x, y + 4)]), line(INK, 4))


# ---------------------------------------------------------------- décors
def clock(c, x, y, r, t):
    wait = clamp((t - K["h1"]) / .2) * (1 - clamp((t - K["calme"]) / .2))
    speed = lerp(.04, 8, wait)
    tt = (t - K["h1"]) if t >= K["h1"] else 0
    a = K["h1"] * .04 + (tt * 8 if t < K["calme"] else (K["calme"] - K["h1"]) * 8)
    shape(c, oval(x - r, y - r, x + r, y + r), "#FFFFFF", 7)
    for i in range(12):
        an = i * math.pi / 6
        c.drawLine(x + (r - 12) * math.cos(an), y + (r - 12) * math.sin(an), x + (r - 5) * math.cos(an), y + (r - 5) * math.sin(an), line(INK, 3))
    c.drawLine(x, y, x + (r - 16) * math.sin(a), y - (r - 16) * math.cos(a), line(INK, 6))
    c.drawLine(x, y, x + (r - 30) * math.sin(a / 12), y - (r - 30) * math.cos(a / 12), line(INK, 9))
    c.drawCircle(x, y, 7, fill(INK))


def draw_table(c):
    for lx in (TL + 28, TE - 58):
        shape(c, rrect(lx, TY + 18, lx + 30, GY - 6, 6), "#7B4A2B", 6)
    shape(c, rrect(TL, TY, TE, TY + 26, 8), "#A9683B", 7)


def bg_salon(c, t, b):
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#F7DDAE"))
    for x in range(-40, W + 80, 120):
        c.drawRect(skia.Rect.MakeLTRB(x, 0, x + 60, 1490), fill("#F2D29C", .55))
    c.drawRect(skia.Rect.MakeLTRB(0, 1466, W, 1495), fill("#FFF5E0"))
    c.drawRect(skia.Rect.MakeLTRB(0, 1495, W, H), fill("#B47B4C"))
    for y in range(1540, H, 90):
        c.drawLine(0, y, W, y, line("#94613A", 5))
    win = skia.Rect.MakeLTRB(90, 680, 400, 900)
    c.drawRect(win, fill("#9BDCFA"))
    c.drawRect(win, line(INK, 24))
    c.drawRect(win, line("#FFFFFF", 16))
    c.drawLine(245, 680, 245, 900, line("#FFFFFF", 11))
    c.drawLine(90, 790, 400, 790, line("#FFFFFF", 11))
    clock(c, 830, 790, 84, t)
    draw_table(c)


SALON_SEQ = ("verre", "tasse", "vase", "tele", "frigo", "piano")


def scene_salon(c, t, b):
    bg_salon(c, t, b)
    key = b["key"]
    # éclats accumulés sur le sol
    for i, k_ in enumerate(SALON_SEQ):
        o = OBJS[k_]
        if t >= IMP[k_]:
            n = {"verre": 30, "tasse": 26, "vase": 32, "tele": 40, "frigo": 46, "piano": 56}[k_]
            sp = {"verre": 330, "tasse": 300, "vase": 330, "tele": 420, "frigo": 520, "piano": 620}[k_]
            sz = {"verre": 11, "tasse": 12, "vase": 14, "tele": 18, "frigo": 22, "piano": 26}[k_]
            burst(c, o["xE"] + o["vx"], SALON_F, t - IMP[k_], o["cols"], n, sp, 620 + sp * .6, sz, seed=20 + i, floor=SALON_F + 18)
    # Gérard
    stage = 0
    if key in ("verre",):
        stage = 2 if t > K["verre"] + o_start("verre") else 1
    if key in ("expl",):
        stage = 2
    if key in ("tasse", "vase", "tele"):
        stage = 2
    if key in ("frigo", "frigo2", "piano"):
        stage = 3
    gerard(c, 880, GY - 2, .62, t, stage)
    # objet courant + Michel
    cat = (260, CAT_S)
    cur = None
    for k_ in SALON_SEQ:
        if K[k_] <= t < K[k_] + {"verre": 4.9}.get(k_, 2.8):
            cur = OBJS[k_]
    if key == "hook":
        # verre déjà là, tapotements en boucle
        o = OBJS["verre"]
        c.save()
        c.translate(o["x0"], o["y0"])
        d_verre(c)
        c.restore()
    if key in ("frigo2",):
        cur = None
    if cur:
        cat = cur["cat"]
        if key not in ("frigo2",) and b["key"] == cur["key"]:
            draw_obj(c, cur, t)
    if key == "frigo2":
        cat = OBJS["frigo"]["cat"]
    open_ = key in ("verre", "tasse", "vase", "tele", "frigo", "piano", "hook", "frigo2")
    draw_cat(c, cat[0], TY, cat[1], t, "open" if open_ else "bliss", 0)
    if key == "hook":
        o = OBJS["verre"]
        x0, y0 = cat[0] + 95 * cat[1], TY - 130 * cat[1]
        e = abs(math.sin(t * 2.6)) ** 1.4 * .96
        paw(c, x0, y0, lerp(x0 + 10, o["x0"] - 58, e), lerp(y0, TY - 40, e), cat[1])
    elif cur and b["key"] == cur["key"]:
        pushing(c, cur, t, cat)
    ger_bubble(c, t, b, 880, GY - 2, .62)
    if key == "piano" and t >= IMP["piano"]:
        # la note
        d_ = t - IMP["piano"]
        s_ = back(d_ / .2)
        text(c, "♪", OBJS["piano"]["xE"] + 100, SALON_F - 260 - d_ * 90, 150 * s_, "#FFE14D", INK, 12, a=clamp(2 - d_ * 1.4))


def o_start(k_):
    o = OBJS[k_]
    return o["tp"] + o["s"]


def bg_rue(c, t, b):
    sky = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 0), (0, 1400)], [col("#5CB8F2"), col("#D3F1FF")]))
    c.drawRect(skia.Rect.MakeWH(W, H), sky)
    c.drawCircle(860, 760, 58, fill("#FFF3B5"))
    for cx_, cy_, k in ((760, 880, 1.0), (980, 1040, .75)):
        for dx, r_ in ((-46, 32), (0, 44), (44, 30)):
            c.drawCircle(cx_ + dx * k, cy_, r_ * k, fill("#FFFFFF", .85))
    c.drawRect(skia.Rect.MakeLTRB(0, ROAD - 40, W, H), fill("#6B6E7E"))
    c.drawRect(skia.Rect.MakeLTRB(0, ROAD - 40, W, ROAD - 14), fill("#9EA1AE"))
    for x in range(-40, W, 180):
        c.drawRect(skia.Rect.MakeLTRB(x, ROAD + 58, x + 100, ROAD + 70), fill("#F4E9B8"))
    # immeuble de Gérard
    shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(-30, ROOF, ROOF_E, ROAD - 14)), "#E58B7B", 8)
    shape(c, rrect(-40, ROOF - 16, ROOF_E + 12, ROOF + 14, 6), "#7A3B3B", 7)
    for fy in range(ROOF + 56, ROAD - 130, 142):
        for fx in range(40, ROOF_E - 110, 170):
            rc = skia.Rect.MakeLTRB(fx, fy, fx + 98, fy + 96)
            c.drawRect(rc, fill("#CDEBFF"))
            c.drawRect(rc, line(INK, 5))
            c.drawLine(fx + 49, fy, fx + 49, fy + 96, line(INK, 3))


def scene_toit(c, t, b):
    bg_rue(c, t, b)
    key = b["key"]
    cat = OBJS["voiture"]["cat"]
    if key == "toit":
        o = OBJS["voiture"]
        c.save()
        c.translate(o["x0"], o["y0"])
        d_voiture(c)
        c.restore()
    if key == "voiture":
        draw_obj(c, OBJS["voiture"], t)
    if t >= IMP["voiture"]:
        o = OBJS["voiture"]
        x = o["xE"] + o["vx"]
        # carcasse
        c.save()
        c.translate(x, ROAD - 14)
        c.scale(1.5, .55)
        c.rotate(-4)
        shape(c, rrect(-80, -44, 80, 0, 14), "#2E55B4", 6)
        shape(c, poly([(-40, -44), (-16, -66), (24, -66), (44, -44)]), "#6E90A8", 5)
        c.restore()
        burst(c, x, ROAD - 14, t - IMP["voiture"], o["cols"], 40, 420, 760, 20, seed=31, floor=ROAD + 6)
    if key == "bus":
        cat = OBJS["bus"]["cat"]
        draw_obj(c, OBJS["bus"], t)
    if t >= IMP["bus"]:
        o = OBJS["bus"]
        x = o["xE"] + o["vx"]
        c.save()
        c.translate(x, ROAD - 22)
        c.rotate(-13)
        c.scale(.8, .7)
        d_bus(c)
        c.restore()
        burst(c, x, ROAD - 14, t - IMP["bus"], o["cols"], 60, 620, 1000, 26, seed=32, floor=ROAD + 30)
        dd = t - IMP["bus"]
        for i in range(10):
            ph = (dd * .7 + i * .1) % 1
            c.drawCircle(x - 160 + i * 36 + math.sin(i + t) * 12, ROAD - 40 - ph * 240, 18 + ph * 42, fill("#8E8A90", .55 * (1 - ph)))
    # Gérard (dans la rue, à droite)
    gerard(c, 1000, ROAD + 2, .42, t, 3)
    # Michel sur le toit
    draw_cat(c, cat[0], ROOF, cat[1], t, "open", 0)
    if key == "voiture":
        pushing(c, OBJS["voiture"], t, cat)
    elif key == "bus":
        pushing(c, OBJS["bus"], t, cat)
    ger_bubble(c, t, b, 1000, ROAD + 2, .42)


def boat(c, x, y, t, bob, k=.3):
    gerard(c, x, y + 8 + bob, k, t, 3)
    c.save()
    c.translate(x, y + bob)
    c.rotate(math.sin(t * 2.1) * 3)
    p = poly([(-130, -30), (130, -30), (96, 42), (-96, 42)])
    shape(c, p, "#B26A3A", 6)
    c.drawLine(-120, -14, 120, -14, line("#7B4A2B", 7))
    c.restore()


def bg_mer(c, t):
    sky = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 0), (0, SEA)], [col("#4FA8E8"), col("#FFE9C9")]))
    c.drawRect(skia.Rect.MakeWH(W, H), sky)
    c.drawCircle(830, 820, 66, fill("#FFF3B5"))
    # horizon lointain
    r = random.Random(4)
    x = -20
    while x < W:
        w, h_ = r.uniform(40, 90), r.uniform(26, 110)
        c.drawRect(skia.Rect.MakeLTRB(x, SEA - h_, x + w, SEA), fill("#A9B8CC"))
        x += w


def sea_front(c, t):
    p = skia.Path()
    p.moveTo(-10, H + 10)
    p.lineTo(-10, SEA)
    for x in range(-10, W + 40, 40):
        p.lineTo(x, SEA + math.sin(x * .02 + t * 2) * 10)
    p.lineTo(W + 20, H + 10)
    p.close()
    c.drawPath(p, fill("#2B86DE", .92))
    for yy, ph_ in ((SEA + 60, 0), (SEA + 130, 2), (SEA + 210, 4)):
        for x in range(-40 + int((t * 40 + ph_ * 30) % 160), W, 160):
            c.drawLine(x, yy, x + 70, yy, line("#7EC8FF", 6))


def scene_mer(c, t, b):
    bg_mer(c, t)
    key = b["key"]
    is_st = key in ("statue0", "statue")
    if not is_st:
        # quai
        shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(-30, QUAY, QUAY_E, SEA + 40)), "#8E91A0", 7)
        c.drawRect(skia.Rect.MakeLTRB(-30, QUAY, QUAY_E, QUAY + 20), fill("#B9BCC8"))
        for yy in range(QUAY + 80, SEA, 90):
            c.drawLine(-30, yy, QUAY_E, yy, line("#7A7D8C", 4))
        cat = OBJS["avion"]["cat"]
        if key == "avion":
            draw_obj(c, OBJS["avion"], t)
        else:
            # avion déjà garé, pas encore poussé
            o = OBJS["avion"]
            c.save()
            c.translate(o["x0"], o["y0"])
            d_avion(c)
            c.restore()
        draw_cat(c, cat[0], QUAY, cat[1], t, "open", 0)
        if key == "avion":
            pushing(c, OBJS["avion"], t, cat)
    else:
        # socle de pierre
        shape(c, poly([(120, SEA + 40), (150, 1200), (500, 1200), (530, SEA + 40)]), "#B9AE9A", 8)
        shape(c, poly([(190, 1200), (214, 1130), (436, 1130), (460, 1200)]), "#CFC5B2", 7)
        for yy in (1250, 1310, 1370):
            c.drawLine(140, yy, 512, yy, line("#8F8676", 5))
        px, py = 395, 1130
        d_ = t - STATUE_T0
        rot = 62 * ein(d_ / STATUE_DUR) if key == "statue" else 0
        drop = 430 * ein((d_ - .45) / (STATUE_DUR - .45)) if key == "statue" else 0
        dx = 60 * clamp((d_ - .45) / .6) if key == "statue" else 0
        c.save()
        c.translate(px + dx, py + drop)
        c.rotate(rot)
        c.translate(-70, 0)
        s_ = back((t - K["statue0"]) / .22) if key == "statue0" else 1
        c.scale(s_, s_)
        d_statue(c, 440)
        c.restore()
        draw_cat(c, 234, 1130, .13, t, "open", 0)
        if key == "statue0":
            e = abs(math.sin((t - K["statue0"]) * 3.2)) ** 2
            paw(c, 244, 1115, lerp(254, 306, e), 1105, .22)
        elif d_ < .4:
            paw(c, 244, 1115, 310, 1100, .22)
        arrow_label(c, 234, 1072, "MICHEL", 80)
    # mer + impacts
    sea_front(c, t)
    if key == "avion" and t >= IMP["avion"]:
        o = OBJS["avion"]
        splash(c, o["xE"] + o["vx"], SEA + 10, t - IMP["avion"], 1.0, 41)
    if key == "statue0":
        d0 = t - K["statue0"]
        o = OBJS["avion"]
        # dernières bulles de l'avion
        for i in range(6):
            ph = (d0 * .8 + i / 6) % 1
            c.drawCircle(o["xE"] + o["vx"] - 100 + i * 42, SEA + 110 - ph * 90, 7 + ph * 6, line("#FFFFFF", 3, 1 - ph))
    if key == "statue" and t >= IMP["statue"]:
        splash(c, 740, SEA + 10, t - IMP["statue"], .9, 43)
    # barque
    bob = 0
    for k_ in ("avion", "statue"):
        if t >= IMP[k_]:
            bob += -70 * math.exp(-(t - IMP[k_]) * 2.2) * abs(math.sin((t - IMP[k_]) * 6))
    bx = 930 if key in ("barque", "avion") else 985
    enter = 1 - eout((t - K["barque"]) / .5)
    boat(c, bx + 340 * enter, SEA + 26, t, bob + math.sin(t * 2.4) * 8)
    ger_bubble(c, t, b, bx - 60, SEA + 26, .3, 2)
    if key not in ("statue0", "statue") and key != "avion":
        arrow_label(c, OBJS["avion"]["cat"][0] + 12, QUAY - 96, "MICHEL", 76)
    if key == "avion" and t < K["avion"] + 1.2:
        arrow_label(c, OBJS["avion"]["cat"][0] + 12, QUAY - 96, "MICHEL", 76)


PARIS_X = 800
TOUR_H = 700


def bg_paris(c, t):
    sky = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 0), (0, 1400)], [col("#141A44"), col("#39356E"), col("#E8785A")], [0, .62, 1]))
    c.drawRect(skia.Rect.MakeWH(W, H), sky)
    c.drawCircle(150, 700, 52, fill("#F6F1D0"))
    yb, colr, bl = ROWS[0]
    for (x, w, h_, wins, rnd) in bl:
        off = PARIS_G - yb
        c.drawRect(skia.Rect.MakeLTRB(x, yb + off - h_ * .7, x + w, PARIS_G), fill(colr))
        c.drawRect(skia.Rect.MakeLTRB(x, yb + off - h_ * .7, x + w, PARIS_G), line(INK, 3))


def seine(c, t, a=1.0):
    p = skia.Path()
    p.moveTo(-10, PARIS_G + 30)
    p.lineTo(440, PARIS_G + 30)
    p.cubicTo(540, PARIS_G + 120, 620, PARIS_G + 250, 650, H + 10)
    p.lineTo(-10, H + 10)
    p.close()
    c.drawPath(p, fill("#2B86DE", a))
    c.drawPath(p, line(INK, 6, a))
    for yy, xe in ((PARIS_G + 70, 420), (PARIS_G + 130, 480), (PARIS_G + 200, 520)):
        for x in range(10 + int((t * 30) % 110), xe, 110):
            c.drawLine(x, yy, x + 54, yy, line("#7EC8FF", 5, a))


def scene_paris(c, t, b):
    bg_paris(c, t)
    key = b["key"]
    # sol
    c.drawRect(skia.Rect.MakeLTRB(0, PARIS_G, W, H), fill("#8E91A0"))
    c.drawRect(skia.Rect.MakeLTRB(0, PARIS_G, W, PARIS_G + 14), fill("#B9BCC8"))
    for x in range(-20, W, 150):
        c.drawLine(x, PARIS_G + 14, x - 60, H, line("#7A7D8C", 4))
    seine(c, t)
    # tour : pivot sur le pied gauche
    pivot = (PARIS_X - 238, PARIS_G)
    th = 0
    if key == "chute":
        th = 88 * ein((t - TOUR_T0) / TOUR_DUR)
    elif key == "seine":
        th = 88
    c.save()
    sink = 150 * eout((t - K["seine"]) / .4) if key == "seine" else 0
    c.translate(pivot[0], pivot[1] + sink)
    c.rotate(-th)
    c.translate(PARIS_X - pivot[0], PARIS_G - pivot[1])
    draw_eiffel(c, TOUR_H)
    c.restore()
    if key == "seine":
        d_ = t - K["seine"]
        splash(c, 220, PARIS_G + 90, d_, 1.25, 51)
        splash(c, 440, PARIS_G + 60, d_ - .08, .7, 52)
        seine(c, t, .55)
    # Gérard, entre les pieds de la tour
    gerard(c, 830, PARIS_G + 80, .34, t, 3 if key in ("chute", "seine") else 2)
    # Michel
    mx = 1010
    draw_cat(c, mx, PARIS_G + 76, .2, t, "open", 0)
    if key in ("tour3", "chute"):
        d_ = t - K["tour3"]
        e = abs(math.sin(d_ * 3.6)) ** 1.5 if key == "tour3" else clamp(1 - (t - TOUR_T0) * 2.2)
        paw(c, mx - 16, PARIS_G + 44, lerp(mx - 22, mx - 60, e), PARIS_G + 6, .3)
    if key not in ("seine",):
        arrow_label(c, mx, PARIS_G + 8, "MICHEL", 96)
    ger_bubble(c, t, b, 830, PARIS_G + 80, .34, 2)


FIN_GX = 880


def fin_gx(t, b):
    key = b["key"]
    if key == "fin0":
        return FIN_GX
    if key == "fin1":
        d_ = (t - K["fin1"] - .4) / 2.0
        return lerp(FIN_GX, 1330, ein(d_) if d_ > 0 else 0)
    if key == "oeil":
        return lerp(1330, 1035, eout((t - K["oeil"] - .15) / .5))
    if key in ("dernier", "stare"):
        return 1035
    return 1330


def scene_fin(c, t, b):
    bg_salon(c, t, b)
    key = b["key"]
    # éclats conservés
    for i, k_ in enumerate(SALON_SEQ):
        o = OBJS[k_]
        burst(c, o["xE"] + o["vx"], SALON_F, 99, o["cols"], 14, 300, 700, 14, seed=20 + i, floor=SALON_F + 18)
    gx = fin_gx(t, b)
    bob = abs(math.sin(t * 7)) * 16 if key == "fin1" else 0
    stage = 0 if key == "fin0" else 1
    if key == "oeil":
        stage = 1
    if key == "dernier":
        stage = 2
    if key == "stare":
        stage = 3
    gerard(c, gx, GY - 2 - bob, .62, t, stage)
    # verre
    if key in ("h1", "h4", "calme", "oeil", "fin1", "fin0"):
        pose = back((t - K["fin0"] - .35) / .3)
        c.save()
        c.translate(LAST["x0"], LAST["y0"] - (1 - pose) * 60)
        d_verre(c)
        c.restore()
    if key == "dernier":
        draw_obj(c, LAST, t)
    if key in ("dernier", "stare") and t >= IMP["dernier"]:
        burst(c, LAST["xE"] + LAST["vx"], SALON_F, t - IMP["dernier"], CR, 32, 340, 720, 11, seed=61, floor=SALON_F + 18)
    # Michel
    mood = "bliss" if key in ("h1", "h4", "calme") else "open"
    if key == "oeil" and t < K["oeil"] + .55:
        mood = "bliss"
    draw_cat(c, 260, TY, CAT_S, t, mood, 0)
    if key == "calme":
        for i, off in enumerate((0, .33, .66)):
            ph = ((t - K["calme"]) * .6 + off) % 1
            text(c, "z", 340 + ph * 70 + i * 6, 930 - ph * 110, 34 + ph * 30, "#FFFFFF", INK, 8, a=1 - ph)
    if key == "dernier":
        pushing(c, LAST, t, (260, CAT_S))
    ger_bubble(c, t, b, min(gx, 960), GY - 2, .62)
    if key == "stare":
        s_ = back((t - K["stare"] - .1) / .18)
        bubble(c, 410, TY - 330, "mrrp ?", 58, s_, -4)


# ---------------------------------------------------------------- image
SHAKE_KEYS = None


def shake_amp(t):
    amp = 0
    for k_, big in (("verre", 5), ("tasse", 6), ("vase", 8), ("tele", 12), ("frigo", 16), ("piano", 22), ("voiture", 20), ("bus", 28), ("avion", 26), ("statue", 30), ("tour", 40), ("dernier", 9)):
        d_ = t - IMP[k_]
        if 0 <= d_ < .3:
            amp = max(amp, big * (1 - d_ / .3))
    return amp


def scene(c, t):
    b = beat_at(t)
    amp = shake_amp(t)
    jx, jy = jitter(t, 2)
    zz = 1 + 2.2 * amp / W
    cy = 960
    key = b["key"]
    if key == "stare":
        zz *= 1 + .18 * eout((t - K["stare"]) / 2.0)
        cy = 1120
    if key == "chute":
        # lente tension de caméra
        zz *= 1 + .03 * ((t - K["chute"]) / 3.0)
    c.save()
    c.translate(540, cy)
    c.scale(zz, zz)
    c.translate(-540 + jx * amp, -cy + jy * amp)
    ph = b["ph"]
    if ph == "salon":
        scene_salon(c, t, b)
    elif ph == "toit":
        scene_toit(c, t, b)
    elif ph == "mer":
        scene_mer(c, t, b)
    elif ph == "paris":
        scene_paris(c, t, b)
    else:
        scene_fin(c, t, b)
    c.restore()
    # flash au changement de décor
    for k_ in ("toit", "barque", "tour0", "fin0"):
        d_ = t - K[k_]
        if 0 <= d_ < .14:
            c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", 1 - d_ / .14))


def heat_c(n):
    stops = [(1, "#59E36A"), (4, "#D7F03A"), (6, "#FFC531"), (8, "#FF7A1F"), (10, "#FF2E2E"), (11, "#FF2EA6"), (12, "#59E36A")]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if a <= n <= b:
            return hexmix(ca, cb, (n - a) / (b - a))
    return "#FFFFFF"


def fit(s, size, maxw):
    f = skia.Font(TF, size)
    while f.measureText(s) > maxw and size > 20:
        size -= 2
        f = skia.Font(TF, size)
    return size


def hud(c, t, b):
    n = b["n"]
    first = next(x["start"] for x in BEATS if x["n"] == n)
    pop = 1 + .13 * (1 - eout((t - first) / .22)) if n > 1 else 1.0
    colr = heat_c(n)
    c.save()
    c.translate(540, 262)
    c.scale(pop, pop)
    pan = rrect(-420, -135, 420, 135, 44)
    c.drawPath(pan, fill("#14121C", .94))
    c.drawPath(pan, line(colr, 8))
    nom, masse, _ = OBJ[n]
    head = "OBJET N° %d · %s" % (n, nom)
    text(c, head, 0, -88, fit(head, 38, 770), "#C9C6D8")
    text(c, masse, 0, 32, fit(masse, 118, 780), colr)
    low = "Facture de Gérard : " + facture(t)
    text(c, low, 0, 106, fit(low, 44, 780), "#FFFFFF")
    c.restore()


def caption(c, t):
    b = beat_at(t)
    if not b["cap"]:
        return
    d_ = t - b["start"]
    s = back(d_ / .17)
    size = 72
    f = skia.Font(TF, size)
    while True:
        lines = wrap_rich(b["cap"], f, 980)
        sp = f.measureText(" ") * 1.6
        wmax = max(sum(f.measureText(w) for w, _ in ln) + sp * (len(ln) - 1) for ln in lines)
        if wmax <= 1000 or size <= 44:
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
    c.translate(540, 780)
    c.scale(s, s)
    text(c, "À SUIVRE :", 0, 0, 86, "#FFFFFF")
    text(c, "POSE TON VERRE.", 0, 132, 100, "#FFD93B")
    text(c, "POUR VOIR.", 0, 250, 100, "#FFD93B")
    c.restore()
    a = clamp((d_ - .5) / .25)
    text(c, "Forces et factures très approximatives (frottement : 0,5).", 540, 1160, 36, "#A9A6BC", a=a)
    text(c, "Gérard va bien. La Seine, ça dépend.", 540, 1212, 36, "#A9A6BC", a=a)


def frame(c, t):
    if t >= CARD:
        card(c, t)
        return
    scene(c, t)
    hud(c, t, beat_at(t))
    caption(c, t)


SPL = [("c_a", 0, K["toit"]), ("c_b", K["toit"], K["barque"]), ("c_c", K["barque"], K["tour0"]), ("c_d", K["tour0"], K["fin0"]), ("c_e", K["fin0"], CARD), ("c_f", CARD, END)]


def png(t, path):
    from PIL import Image
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    s = skia.Surface(arr)
    with s as c:
        frame(c, t)
    Image.fromarray(arr[..., :3]).save(path)


if __name__ == "__main__":
    print("durée %.1f s, carton %.1f" % (END, CARD))
    if sys.argv[1:2] == ["png"]:
        os.makedirs("pc", exist_ok=True)
        for ts in sys.argv[2:]:
            png(float(ts), "pc/t%06.2f.png" % float(ts))
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
