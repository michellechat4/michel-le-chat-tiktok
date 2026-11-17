"""La folie de 3 h du matin : chaque nuit, Michel court deux fois plus vite (50 km/h la nuit 1).
Guépard, train à grande vitesse, mur du son (l'immeuble se réveille, sauf Gérard et ses bouchons), Paris–Marseille en 12 min,
tour de la Terre en 3 h 08, presque l'orbite, vitesse de libération : il part sur la Lune (11 h 36 de trajet).
Gérard dort enfin jusqu'à 7 h. Nuit 12 : retour en 3 h 44, il arrive à 6 h 44, pile pour le petit-déj."""
import math, random, sys, os, subprocess
import importlib.util as _u
import numpy as np
import skia
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "moteur"))
import art
from art import (fill, line, col, hexmix, poly, rrect, oval, shape, text, jitter, clamp, lerp, eout, ein, back,
                 draw_cat, draw_gerard, draw_couch, draw_moon, earth_rgba, project, STARS, bubble, wrap_rich, TF, INK, W, H, FPS)

# décor du salon et outils repris de la vidéo 08
_sp = _u.spec_from_file_location("saut08", os.path.join(HERE, "08_saut.py"))
V8 = _u.module_from_spec(_sp)
_sp.loader.exec_module(V8)
sky_grad, fit, nb, FLOOR, scale_bar = V8.sky_grad, V8.fit, V8.nb, V8.FLOOR, V8.scale_bar
SHELF_Y = V8.SHELF_Y

# ---------------------------------------------------------------- chiffres (calculés, pas recopiés)
V1 = 50                   # km/h, nuit 1 : un chat domestique court vers 50 km/h (Vikidia, « Vitesse des animaux » ; les sources varient)
GUEPARD = (90, 110)       # km/h, vitesse de pointe estimée (Futura-Sciences, 2026)
TRAIN = 320               # km/h, vitesse commerciale des trains à grande vitesse français (Vikidia, « TGV »)
SON = 343                 # m/s, vitesse du son dans l'air à 20 °C (valeur standard, déjà utilisée vidéo 08)
COULOIR = 5               # m, couloir de Gérard (INVENTÉ)
PARIS_MARSEILLE = 661     # km à vol d'oiseau (Bonnes Routes, centre à centre)
TOUR = 40075              # km, circonférence à l'équateur (notre-planete.info)
ORBITE = 28000            # km/h, orbite basse (ESA Kids)
LIBERATION = 40300        # km/h, 11,2 km/s (ESA Kids, Techno-Science)
LUNE = 384400             # km, distance moyenne Terre-Lune (déjà utilisée vidéos 08 et 15)
GM, RT = 3.986004418e14, 6.371e6


def v(n):
    return V1 * 2 ** (n - 1)


def hmin(h):
    """heures décimales → (h, min)"""
    m = round(h * 60)
    return m // 60, m % 60


def vol_lune(v0):
    """Durée (h) pour monter de la surface à 384 400 km en partant à v0 (m/s), gravité de la Terre seule, sans air."""
    from scipy.integrate import solve_ivp
    ev = lambda t, y: y[0] - (RT + LUNE * 1000)
    ev.terminal = True
    s = solve_ivp(lambda t, y: [y[1], -GM / y[0] ** 2], [0, 1e7], [RT, v0], events=ev, rtol=1e-10, atol=1)
    return s.t_events[0][0] / 3600


def retour(v0):
    """Durée (h) pour revenir de 384 400 km jusqu'à la surface en partant à v0 (m/s) vers la Terre."""
    from scipy.integrate import solve_ivp
    ev = lambda t, y: y[0] - RT
    ev.terminal = True
    s = solve_ivp(lambda t, y: [y[1], -GM / y[0] ** 2], [0, 1e7], [RT + LUNE * 1000, -v0], events=ev, rtol=1e-10, atol=1)
    return s.t_events[0][0] / 3600


PAR_S = v(3) / 3.6 / COULOIR
MACH6 = v(6) / 3.6 / SON
PM_MIN = PARIS_MARSEILLE / v(7) * 60
TOUR_H = TOUR / v(9)
H_LUNE = vol_lune(v(11) / 3.6)
H_RET = retour(v(12) / 3.6)
TL = hmin(TOUR_H)
LL = hmin(H_LUNE)
RR = hmin(H_RET)

assert [v(n) for n in (1, 2, 3, 4, 6, 7, 9, 10, 11, 12)] == [50, 100, 200, 400, 1600, 3200, 12800, 25600, 51200, 102400]
assert GUEPARD[0] <= v(2) <= GUEPARD[1] and v(3) > GUEPARD[1] and v(3) < TRAIN < v(4)
assert round(PAR_S) == 11
assert v(5) < SON * 3.6 < v(6) and round(SON * 3.6) == 1235 and round(MACH6, 1) == 1.3
assert round(PM_MIN) == 12 and round(2 * PM_MIN) == 25
assert TL == (3, 8)
assert v(10) < ORBITE < v(11) and LIBERATION < v(11) and round(v(11) / LIBERATION * 100) == 127
assert LL == (11, 36) and RR == (3, 44)
ARR_LUNE = "%d h %02d" % hmin(3 + H_LUNE)
ARR_RET = "%d h %02d" % hmin(3 + H_RET)
assert ARR_LUNE == "14 h 36" and ARR_RET == "6 h 44"


def fr(x, n=0):
    return (("%." + str(n) + "f") % x).replace(".", ",")


# ---------------------------------------------------------------- chronologie
# (clé, durée, nuit, légende, Gérard dit, décor)
RAW = [
    ("hook", 3.2, 1, "À 3 H DU MATIN, CE CHAT | *VA QUITTER LA TERRE.*", None, "voyage"),
    ("regle", 3.4, 1, "Chaque nuit à 3 h, sa folie | va *deux fois plus vite.*", "Michel… il est 3 h.", "salon"),
    ("n1", 3.2, 1, "Nuit 1 : 50 km/h. Un vrai chat | court *vers 50 km/h.*", None, "salon"),
    ("n2", 3.4, 2, "Nuit 2 : 100 km/h. | La vitesse d'un *guépard.*", None, "salon"),
    ("n3", 3.4, 3, "Nuit 3 : 200 km/h. Le couloir : | *%d fois par seconde.*" % round(PAR_S), None, "salon"),
    ("bouchons", 3.2, 3, "Gérard achète | *des bouchons d'oreilles.*", "Enfin.", "salon"),
    ("n4", 3.4, 4, "Nuit 4 : 400 km/h. Il double | un *train à grande vitesse.*", None, "train"),
    ("n6", 3.2, 6, "Nuit 6 : 1 600 km/h. | *Le mur du son.*", None, "mach"),
    ("immeuble", 3.4, 6, "Tout l'immeuble se réveille. | *Sauf Gérard.*", None, "immeuble"),
    ("n7", 3.4, 7, "Nuit 7 : 3 200 km/h. | Paris–Marseille : *12 minutes.*", None, "carte"),
    ("sardine", 3.2, 7, "Aller-retour : 25 minutes. | Il rapporte *une sardine.*", None, "salon"),
    ("n9", 3.4, 9, "Nuit 9 : 12 800 km/h. | Le tour de la Terre : *3 h 08.*", None, "terre"),
    ("retour9", 3.2, 9, "Rentré à *6 h 08.* | Gérard n'a *rien vu.*", None, "salon"),
    ("n10", 3.4, 10, "Nuit 10 : 25 600 km/h. | *Presque* en orbite (28 000).", None, "orbite"),
    ("n11", 3.4, 11, "Nuit 11 : 51 200 km/h. Plus que | la vitesse de *libération.*", None, "orbite"),
    ("quitte", 3.4, 11, "*Il quitte la Terre.* | Trajet jusqu'à la Lune : *11 h 36.*", None, "voyage"),
    ("lune", 3.2, 11, "Arrivée : 14 h 36. | Il fait *la sieste.*", None, "lune"),
    ("calme", 3.2, 11, "Sur Terre, Gérard dort | *jusqu'à 7 h.* Une première.", "Quel silence…", "salon"),
    ("n12", 3.4, 12, "Nuit 12 : 102 400 km/h. | Retour : *3 h 44.*", None, "voyage"),
    ("fin", 3.8, 12, "Il arrive à *6 h 44.* | Pile pour *le petit-déj.*", "NON.", "salon"),
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
JUMPS = sorted(b["start"] for b in BEATS if b["d1"] > b["d0"]) + [K["n1"]]
JUMPS.sort()
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


# ---------------------------------------------------------------- Michel qui court
def run_cat(c, x, y, s, t, sp=1.0, dirn=1, ghosts=3, mood="open", helmet=False):
    """Michel penché en avant, étiré dans le sens de la course (dirn = 1 vers la droite), traînées derrière."""
    r = random.Random(int(t * 15))
    for i in range(7):
        yy = y - r.uniform(30, 360) * s
        ln = r.uniform(160, 420) * s / .3 * min(sp, 2.5)
        x0 = x - dirn * 120 * s
        c.drawLine(x0, yy, x0 - dirn * ln, yy, line("#FFFFFF", max(2, 9 * s / .3), .7))
    for g in range(ghosts, 0, -1):
        c.saveLayerAlpha(None, int(70 / g))
        gx = x - dirn * g * 150 * s * min(sp, 2)
        c.save()
        c.translate(gx, y)
        c.scale(1 + .2 * min(sp, 2), 1 - .08 * min(sp, 2))
        c.skew(.3 * dirn * min(sp, 2) * .5, 0)
        draw_cat(c, 0, 0, s, t, mood, 0)
        c.restore()
        c.restore()
    c.save()
    c.translate(x, y)
    c.scale(1 + .2 * min(sp, 2), 1 - .08 * min(sp, 2))
    c.skew(-.3 * dirn * min(sp, 2) * .5, 0)
    draw_cat(c, 0, 0, s, t, mood, 2 * sp)
    if helmet:
        c.drawCircle(0, -270 * s, 190 * s, fill("#BEE8FF", .22))
        c.drawCircle(0, -270 * s, 190 * s, line("#E9F6FF", max(2, 8 * s / .4)))
    c.restore()


def speed_tag(c, x, y, s_, a, colr="#FFE14D", size=46):
    if a <= 0:
        return
    f = skia.Font(TF, size)
    w = f.measureText(s_)
    p = rrect(x - w / 2 - 22, y - size, x + w / 2 + 22, y + size * .35, 22)
    c.drawPath(p, fill("#14121C", .9 * a))
    c.drawPath(p, line(colr, 5, a))
    text(c, s_, x, y, size, colr, a=a)


def sardine(c, x, y, s, rot=0.0):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    body = skia.Path()
    body.moveTo(-90, 0)
    body.quadTo(-20, -40, 70, -6)
    body.lineTo(70, 6)
    body.quadTo(-20, 40, -90, 0)
    body.close()
    shape(c, body, "#AFC3D6", 6)
    shape(c, poly([(66, 0), (110, -30), (100, 0), (110, 30)]), "#8EA6BD", 5)
    c.drawLine(-40, -6, 50, -4, line("#6E89A6", 5))
    c.drawCircle(-66, -6, 7, fill(INK))
    c.restore()


# ---------------------------------------------------------------- salon
CS = .62                               # échelle du canapé
CX, CY = 540, FLOOR - (1490 - 1300) * CS


def ger_couch(c, t, stage=0, asleep=False, plugs=False, zz=True):
    c.save()
    c.translate(CX, CY)
    c.scale(CS, CS)
    c.translate(-570, -1300)
    draw_couch(c)
    draw_gerard(c, stage, t, False, 0, True)
    hx, hy = 790, 1000
    if asleep:
        for sg in (-1, 1):
            ex = hx + sg * 38
            c.drawCircle(ex, hy - 12, 24, fill("#F7C7A0"))
            p = skia.Path()
            p.moveTo(ex - 18, hy - 14)
            p.quadTo(ex, hy + 2, ex + 18, hy - 14)
            c.drawPath(p, line(INK, 7))
    if plugs:
        for sg in (-1, 1):
            shape(c, oval(hx + sg * 96 - 16, hy + 2, hx + sg * 96 + 16, hy + 34), "#FFC531", 5)
    c.restore()
    if asleep and zz:
        gx, gy = CX + (790 - 570) * CS, CY + (1000 - 1300) * CS
        for k in range(3):
            ph = (t * .6 + k / 3) % 1
            text(c, "z", gx - 90 - ph * 70, gy - 60 - ph * 110, 34 + 26 * ph, "#FFFFFF", INK, 6, a=1 - ph)


def clock(c, hm, a=1.0):
    """Réveil numérique sur l'étagère."""
    x0, x1 = 668, 852
    p = rrect(x0, SHELF_Y - 78, x1, SHELF_Y, 14)
    c.drawPath(p, fill("#14121C", a))
    c.drawPath(p, line(INK, 6, a))
    text(c, hm, (x0 + x1) / 2, SHELF_Y - 20, 54, "#FF4B3A", a=a)


def salon_bg(c, t, b, night=True):
    V8.salon(c, t, b, night=night, holed=False)
    if night:
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#0B1030", .48))
        # lumière de la lune par la fenêtre
        p = poly([(70, 980), (310, 980), (520, FLOOR + 40), (120, FLOOR + 40)])
        c.drawPath(p, fill("#BFD8FF", .08))


def scene_salon(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    night = key not in ("calme", "fin")
    salon_bg(c, t, b, night)
    G = FLOOR + 10
    if key == "regle":
        clock(c, "03:00")
        ger_couch(c, t, 0 if d_ < .3 else 1)
        draw_cat(c, 200, G, .34, t, "open", 0)
        # les yeux de Michel brillent
        V8.gerbub(c, t, b, 700, 1110)
        if d_ > 1.8:
            text(c, "!", 200, G - 170, 90, "#FFE14D", INK, 10, a=clamp((d_ - 1.8) / .15))
        return
    if key == "n1":
        clock(c, "03:00")
        ger_couch(c, t, 1)
        u = ((d_ - .3) / .9) % 1 if d_ > .3 else -1
        if 0 <= u:
            k = int((d_ - .3) / .9) % 2
            dirn = 1 if k == 0 else -1
            x = lerp(-200, W + 200, u) if dirn > 0 else lerp(W + 200, -200, u)
            run_cat(c, x, G, .3, t, 1.0, dirn, 2)
        speed_tag(c, 540, 1760, "50 km/h", clamp((d_ - .6) / .2))
        return
    if key == "n2":
        clock(c, "03:00")
        ger_couch(c, t, 2)
        u = (d_ / .55) % 1
        dirn = 1 if int(d_ / .55) % 2 == 0 else -1
        x = lerp(-200, W + 200, u) if dirn > 0 else lerp(W + 200, -200, u)
        run_cat(c, x, G, .3, t, 1.4, dirn, 3)
        panel_guepard(c, t, d_)
        return
    if key == "n3":
        clock(c, "03:00")
        ger_couch(c, t, 3)
        # va-et-vient : une nuée de Michel
        rr = random.Random(int(t * FPS))
        for i in range(9):
            x = rr.uniform(-60, W + 60)
            c.saveLayerAlpha(None, 110)
            run_cat(c, x, G, .3, t, 2.0, rr.choice((-1, 1)), 0)
            c.restore()
        a = clamp((d_ - .5) / .2)
        if a > 0:
            panel(c, a, 640, 860)
            text(c, "COULOIR : %d m (inventé)" % COULOIR, 540, 720, 48, "#FFFFFF", INK, 7, a=a)
            text(c, "%d traversées par seconde" % round(PAR_S), 540, 810, 52, "#FFE14D", a=a)
        return
    if key == "bouchons":
        clock(c, "03:00")
        ger_couch(c, t, 0, asleep=d_ > 1.5, plugs=d_ > .5)
        if d_ <= .5:
            pass
        rr = random.Random(int(t * FPS))
        c.saveLayerAlpha(None, 90)
        run_cat(c, rr.uniform(0, W), G, .3, t, 2.0, rr.choice((-1, 1)), 0)
        c.restore()
        if d_ < 1.5:
            V8.gerbub(c, t, b, 700, 1110)
        return
    if key == "sardine":
        clock(c, "03:25")
        ger_couch(c, t, 0, asleep=True, plugs=True)
        u = eout(clamp(d_ / .35))
        mx = lerp(-200, 260, u)
        if u < 1:
            run_cat(c, mx, G, .34, t, 2.0, 1, 2)
        else:
            draw_cat(c, mx, G, .34, t, "wink" if d_ > 1.6 else "open")
            sardine(c, mx, G - 74, .7, -8)
        return
    if key == "retour9":
        clock(c, "06:08")
        ger_couch(c, t, 0, asleep=True, plugs=True)
        u = eout(clamp(d_ / .35))
        mx = lerp(-200, 260, u)
        if u < 1:
            run_cat(c, mx, G, .34, t, 2.0, 1, 2)
        else:
            draw_cat(c, mx, G, .34, t, "bliss" if d_ > 1.4 else "open")
        if d_ > 1.8:
            text(c, "(innocent)", 260, G - 190, 44, "#FFFFFF", INK, 8, a=clamp((d_ - 1.8) / .2))
        return
    if key == "calme":
        clock(c, "07:00")
        # rayons du matin
        for k in range(4):
            p = poly([(90 + k * 60, 990), (140 + k * 60, 990), (520 + k * 120, FLOOR + 40), (420 + k * 120, FLOOR + 40)])
            c.drawPath(p, fill("#FFF3B0", .18))
        ger_couch(c, t, 0, asleep=d_ < 1.0, plugs=True, zz=d_ < 1.0)
        if d_ > 1.2:
            V8.gerbub(c, t, dict(b, start=b["start"] + .9), 500, 1150)
        return
    if key == "fin":
        clock(c, "06:44")
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#2A2050", .25))
        ger_couch(c, t, 0 if d_ < .5 else 2, asleep=d_ < .5, plugs=True, zz=False)
        if d_ > .25:
            r = random.Random(3)
            pts = []
            for i in range(16):
                a_ = i / 16 * 2 * math.pi
                rr_ = 95 if i % 2 == 0 else 45
                pts.append((190 + math.cos(a_) * rr_ * r.uniform(.8, 1.1), 1130 + math.sin(a_) * rr_ * r.uniform(.8, 1.1)))
            shape(c, poly(pts), "#0B1030", 5)
        # Michel entre par la fenêtre
        u = clamp(d_ / .45)
        if u < 1:
            x = lerp(-150, 230, u)
            y = lerp(1100, FLOOR + 10, u * u)
            run_cat(c, x, y, .34, t, 2.5, 1, 2, helmet=True)
        else:
            draw_cat(c, 230, FLOOR + 10, .34, t, "open" if d_ < 1.8 else "wink")
            c.drawCircle(230, FLOOR + 10 - 270 * .34, 190 * .34, fill("#BEE8FF", .22))
            c.drawCircle(230, FLOOR + 10 - 270 * .34, 190 * .34, line("#E9F6FF", 6))
            if d_ > 1.0:
                bubble(c, 330, FLOOR - 230, "Miaou.", 50, back((d_ - 1.0) / .16), -3)
        if d_ > .3:
            r = random.Random(12)
            for i in range(10):
                ph = clamp((d_ - .3) / 1.0)
                sx, sy = 190 + r.uniform(-60, 60), 1130 + r.uniform(-120, 120)
                c.save()
                c.translate(sx + r.uniform(40, 260) * ph, sy + 500 * ph * ph)
                c.rotate(ph * 400 + i * 30)
                shape(c, poly([(-14, -10), (16, -6), (0, 14)]), "#CDEBFF", 3, 1 - ph * .5)
                c.restore()
        if d_ > 1.9:
            V8.gerbub(c, t, dict(b, start=b["start"] + 1.6), 500, 1150)
        return


def draw_cat_bowl(c):
    text(c, "(pas de Michel)", 230, FLOOR - 60, 40, "#7B4A2B", "#FFF5E0", 6)


PY0, PY1 = 640, 900


def panel(c, a=1.0, y0=PY0, y1=PY1):
    p = rrect(60, y0, 1020, y1, 34)
    c.drawPath(p, fill("#14121C", .92 * a))
    c.drawPath(p, line("#FFFFFF", 6, a))


def panel_guepard(c, t, d_):
    a = clamp((d_ - .5) / .25)
    if a <= 0:
        return
    panel(c, a, 630, 920)
    text(c, "VITESSE DE POINTE", 540, 694, 44, "#FFFFFF", INK, 7, a=a)
    mx = 980
    rows = (("Guépard", GUEPARD[0], GUEPARD[1], "#FFC531", "90 à 110 km/h"), ("Michel", v(2), v(2), "#F49A3A", "100 km/h"))
    for i, (nm, lo, hi, cc, lab) in enumerate(rows):
        y = 770 + i * 84
        text(c, nm, 100, y + 14, 42, cc, align="left", a=a)
        x0 = 320
        u = eout(clamp((d_ - .6 - i * .25) / .5))
        x1 = lerp(x0, x0 + (mx - x0 - 220) * hi / 120, u)
        c.drawPath(rrect(x0, y - 22, max(x0 + 1, x1), y + 18, 14), fill(cc, a))
        text(c, lab, x1 + 14, y + 14, 38, "#FFFFFF", align="left", a=a * u)


# ---------------------------------------------------------------- train
def train(c, x, y, s):
    """Train à grande vitesse générique (sans logo), nez à droite, x = nez."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    for k in range(3):
        x0 = -260 - k * 520
        shape(c, rrect(x0 - 500, -120, x0, 0, 20), "#F2F2F7", 6)
        c.drawRect(skia.Rect.MakeLTRB(x0 - 500, -50, x0, -32), fill("#3F6FD8"))
        for wx in range(int(x0 - 470), int(x0 - 30), 70):
            c.drawRect(skia.Rect.MakeLTRB(wx, -98, wx + 46, -66), fill("#FFE9A8"))
    nose = skia.Path()
    nose.moveTo(-260, -120)
    nose.lineTo(-120, -120)
    nose.quadTo(60, -100, 120, -10)
    nose.lineTo(120, 0)
    nose.lineTo(-260, 0)
    nose.close()
    shape(c, nose, "#F2F2F7", 6)
    c.drawRect(skia.Rect.MakeLTRB(-260, -50, 90, -32), fill("#3F6FD8"))
    shape(c, poly([(-110, -110), (-30, -104), (40, -64), (-110, -64)]), "#2C3550", 5)
    c.drawCircle(100, -22, 9, fill("#FFF3B0"))
    c.restore()


def scene_train(c, t, b):
    d_ = t - b["start"]
    sky_grad(c, "#06061A", "#22305E", 500, 1500)
    rr = random.Random(5)
    for i in range(90):
        c.drawCircle(rr.uniform(0, W), rr.uniform(560, 1200), rr.choice((1.4, 2.2)), fill("#FFFFFF", .7))
    draw_moon(c, 880, 760, 60, t, "scared")
    G = 1380
    # collines qui défilent
    off = (t * 300) % 600
    for k in range(-1, 4):
        hx = k * 600 - off
        shape(c, oval(hx - 100, G - 380, hx + 500, G + 300), "#1E3A2E", 0)
    c.drawRect(skia.Rect.MakeLTRB(0, G, W, H), fill("#24432E"))
    # poteaux
    for k in range(6):
        px = (k * 260 - t * 900) % (W + 260) - 130
        c.drawLine(px, G, px, G - 420, line("#141a24", 10))
    c.drawLine(0, G + 6, W, G + 6, line("#8A8F9C", 8))
    tx = 760 + d_ * 30
    train(c, tx, G, .95)
    # Michel arrive de la gauche, double le train
    u = clamp((d_ - .3) / 1.8)
    mx = lerp(-200, 940, eout(u))
    run_cat(c, mx, G + 4, .3, t, 2.0, 1, 3)
    speed_tag(c, 300, 1560, "Train : 320 km/h", clamp((d_ - .3) / .2), "#FFFFFF", 44)
    speed_tag(c, 780, 1560, "Michel : 400 km/h", clamp((d_ - 1.2) / .2), "#FFE14D", 44)
    if d_ > 2.0:
        bubble(c, 300, G - 300, "?!", 56, back((d_ - 2.0) / .16), 3)


# ---------------------------------------------------------------- mur du son
def scene_mach(c, t, b):
    d_ = t - b["start"]
    sky_grad(c, "#06061A", "#1B2A5E", 300, 1700)
    r = random.Random(9)
    for i in range(10):
        x = (r.uniform(0, W) - t * 2800) % (W + 600) - 300
        y = r.uniform(600, 1700)
        shape(c, oval(x, y, x + 260, y + 70), "#9AA6C8", 0, .45)
    cx, cy = 560, 1200
    u = clamp((d_ - .6) / .3)
    if u > 0:
        cone = skia.Path()
        cone.moveTo(cx + 170, cy - 60)
        cone.quadTo(cx - 40, cy - 350, cx - 320, cy - 400)
        cone.quadTo(cx - 200, cy - 60, cx - 320, cy + 280)
        cone.quadTo(cx - 40, cy + 230, cx + 170, cy - 60)
        c.drawPath(cone, fill("#FFFFFF", .45 * u))
        c.drawPath(cone, line("#FFFFFF", 8, .9 * u))
    j = jitter(t, 4)
    run_cat(c, cx + j[0] * 6, cy + 80 + j[1] * 6, .5, t, 2.5, 1, 3)
    if d_ > .65:
        s_ = back((d_ - .65) / .18)
        c.save()
        c.translate(cx + 120, cy + 330)
        c.rotate(-8)
        c.scale(s_, s_)
        text(c, "BANG !", 0, 0, 130, "#FFE14D", INK, 14)
        c.restore()
        text(c, "Son : 1 235 km/h · Mach %s" % fr(MACH6, 1), 540, 1650, 50, "#FFFFFF", INK, 9, a=clamp((d_ - 1.2) / .2))


# ---------------------------------------------------------------- immeuble
WIN_ORDER = list(range(18))
random.Random(21).shuffle(WIN_ORDER)
GERARD_WIN = 13
NEIGH = [(2, "QUOI ?!"), (9, "ON DORT !"), (17, "MICHEL ?!")]


def scene_immeuble(c, t, b):
    d_ = t - b["start"]
    sky_grad(c, "#06061A", "#1B2350", 300, 1600)
    rr = random.Random(11)
    for i in range(80):
        c.drawCircle(rr.uniform(0, W), rr.uniform(560, 900), rr.choice((1.4, 2.2)), fill("#FFFFFF", .7))
    G = 1680
    x0, x1, top = 170, 910, 700
    shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(x0, top, x1, G)), "#3A3F5C", 7)
    shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(x0 - 20, top - 40, x1 + 20, top)), "#2C3048", 6)
    j = jitter(t, 7)
    amp = 8 * clamp(1 - d_ / .4)
    lit_n = int(clamp((d_ - .25) / 1.3) * 18)
    order = [w for w in WIN_ORDER if w != GERARD_WIN]
    lit = set(order[:lit_n])
    for i in range(18):
        cx_ = i % 3
        ry = i // 3
        wx = x0 + 70 + cx_ * 230 + j[0] * amp
        wy = top + 50 + ry * 155 + j[1] * amp
        rc = skia.Rect.MakeLTRB(wx, wy, wx + 140, wy + 105)
        on = i in lit
        c.drawRect(rc, fill("#FFE9A8" if on else "#141A30"))
        c.drawRect(rc, line(INK, 6))
        c.drawLine(wx + 70, wy, wx + 70, wy + 105, line(INK, 4))
        if i == GERARD_WIN and d_ > 1.6:
            for k in range(3):
                ph = (t * .6 + k / 3) % 1
                text(c, "z", wx + 90 + ph * 50, wy + 40 - ph * 70, 30 + 18 * ph, "#FFFFFF", INK, 5, a=1 - ph)
    for k, (i, s_) in enumerate(NEIGH):
        tt = .9 + k * .35
        if d_ > tt and i in lit:
            wx = x0 + 70 + (i % 3) * 230
            wy = top + 50 + (i // 3) * 155
            bubble(c, clamp(wx + 70, 220, 860), wy - 30, s_, 40, back((d_ - tt) / .16), (-3, 3, -2)[k])
    if d_ > 1.6:
        wx = x0 + 70 + (GERARD_WIN % 3) * 230
        wy = top + 50 + (GERARD_WIN // 3) * 155
        c.drawLine(wx + 70, wy + 105, wx + 70, wy + 150, line("#FFE14D", 5, clamp((d_ - 1.6) / .2)))
        text(c, "GÉRARD", wx + 70, wy + 190, 40, "#FFE14D", INK, 7, a=clamp((d_ - 1.6) / .2))
    c.drawRect(skia.Rect.MakeLTRB(0, G, W, H), fill("#24283A"))
    c.drawLine(0, G, W, G, line(INK, 6))


# ---------------------------------------------------------------- carte Paris–Marseille
CARTE_R, CARTE_C = 9000, (430, 690)
_CARTE = None


def carte_img():
    global _CARTE
    if _CARTE is None:
        _CARTE = earth_rgba(CARTE_R, clouds=0.0, cx=CARTE_C[0], cy=CARTE_C[1])
    return _CARTE


def proj(lat, lon):
    x, y, _ = project(lat, lon, CARTE_R)
    return x - art.EX + CARTE_C[0], y - art.EY + CARTE_C[1]


PARIS = (48.857, 2.352)
MARSEILLE = (43.296, 5.370)


def scene_carte(c, t, b):
    d_ = t - b["start"]
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#2B86DE"))
    img, x0, y0 = carte_img()
    c.drawImage(img, x0, y0)
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#06061A", .35))
    px, py = proj(*PARIS)
    mx_, my_ = proj(*MARSEILLE)
    c.drawPath(skia.Path().moveTo(px, py).lineTo(mx_, my_),
               skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6, Color=col("#FFFFFF"), PathEffect=skia.DashPathEffect.Make([20, 14], 0)))
    for (x, y, nm, al) in ((px, py, "PARIS", "left"), (mx_, my_, "MARSEILLE", "right")):
        c.drawCircle(x, y, 16, fill("#FFE14D"))
        c.drawCircle(x, y, 16, line(INK, 5))
        text(c, nm, x + (30 if al == "left" else -30), y + 16, 50, "#FFFFFF", INK, 9, align=al)
    text(c, "661 km", (px + mx_) / 2 + 30, (py + my_) / 2, 50, "#FFE14D", INK, 9, align="left")
    u = clamp((d_ - .4) / 2.2)
    x, y = lerp(px, mx_, u), lerp(py, my_, u)
    c.save()
    c.translate(x, y)
    c.rotate(math.degrees(math.atan2(my_ - py, mx_ - px)) - 0)
    run_cat(c, 0, 20, .16, t, 2.0, 1, 2)
    c.restore()
    mins = round(u * PM_MIN)
    text(c, "3 h %02d" % mins, 540, 1700, 72, "#FFFFFF", INK, 11)


# ---------------------------------------------------------------- tour de la Terre
TERRE_R, TERRE_C = 300, (540, 1170)
_TERRE = None


def terre_img():
    global _TERRE
    if _TERRE is None:
        _TERRE = earth_rgba(TERRE_R, cx=TERRE_C[0], cy=TERRE_C[1])
    return _TERRE


def scene_terre(c, t, b):
    d_ = t - b["start"]
    c.drawImage(STARS, 0, 0)
    ex, ey = TERRE_C
    u = clamp((d_ - .3) / 2.6)
    ang = -math.pi / 2 + u * 2 * math.pi
    rx, ry = 380, 130
    back_half = math.sin(ang) < 0

    def mich():
        x, y = ex + math.cos(ang) * rx, ey + math.sin(ang) * ry * -1 + 0
        run_cat(c, x, y, .18, t, 1.6, 1 if math.sin(ang) < 0 or True else -1, 1, "open")

    c.drawPath(skia.Path().addOval(skia.Rect.MakeLTRB(ex - rx, ey - ry, ex + rx, ey + ry)),
               skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5, Color=col("#FFE14D", .7), PathEffect=skia.DashPathEffect.Make([16, 12], 0)))
    y_m = ey - math.sin(ang) * ry
    behind = y_m < ey   # moitié arrière de l'orbite : derrière la Terre
    if behind:
        mich()
    img, x0, y0 = terre_img()
    c.drawImage(img, x0, y0)
    c.drawCircle(ex, ey, TERRE_R, line(INK, 6))
    if not behind:
        mich()
    text(c, "40 075 km", ex, ey + TERRE_R + 120, 54, "#FFE14D", INK, 9)
    mins = round(u * TOUR_H * 60)
    text(c, "%d h %02d" % (3 + mins // 60, mins % 60), 540, 1700, 72, "#FFFFFF", INK, 11)


# ---------------------------------------------------------------- orbite / libération
def space_bg(c, G=1500):
    p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 900), (0, G)], [col("#06061A"), col("#3F7FD8")]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    rr = random.Random(8)
    for i in range(140):
        y = rr.uniform(0, G - 200)
        c.drawCircle(rr.uniform(0, W), y, rr.choice((1.2, 2, 2.6)), fill("#FFFFFF", clamp((G - 150 - y) / 500)))
    shape(c, oval(-1400, G - 30, W + 1400, G + 3400), "#2B86DE", 7)
    c.drawPath(oval(-1400, G - 30, W + 1400, G + 3400), line("#9BDCFA", 18, .5))
    for (x0, w0) in ((60, 300), (620, 360)):
        shape(c, oval(x0, G - 14, x0 + w0, G + 70), "#59B36A", 0)


def scene_orbite(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    G = 1560
    space_bg(c, G)
    oy = G - 260
    c.drawPath(skia.Path().addOval(skia.Rect.MakeLTRB(-1400 - 230, oy - 30, W + 1400 + 230, oy + 3400 + 2 * 230)),
               skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6, Color=col("#FFE14D", .8), PathEffect=skia.DashPathEffect.Make([26, 16], 0)))
    text(c, "ORBITE : 28 000 km/h", 540, oy - 60, 48, "#FFE14D", INK, 8)
    if key == "n10":
        # il monte vers l'orbite puis retombe
        u = clamp((d_ - .1) / 3.2)
        x = lerp(-150, W + 150, u)
        hgt = math.sin(u * math.pi) * 215
        run_cat(c, x, G - 20 - hgt, .26, t, 2.0, 1, 3)
        if d_ > 2.2:
            text(c, "Presque.", 540, 1130, 70, "#FFFFFF", INK, 10, a=clamp((d_ - 2.2) / .2))
        speed_tag(c, 540, 1760, "Michel : 25 600 km/h", clamp((d_ - .5) / .2), size=44)
    else:
        # décollage vertical
        u = ein(clamp((d_ - .4) / 1.0))
        x = 540
        y = lerp(G - 10, -300, u)
        c.save()
        c.translate(x, y)
        c.rotate(-90)
        run_cat(c, 0, 0, .24, t, 2.5, 1, 3, helmet=True)
        c.restore()
        # cadran
        cx, cy, R = 540, 1000, 170
        a = clamp((d_ - 1.2) / .25)
        if a > 0:
            panel(c, a, 760, 1140)
            k = eout(clamp((d_ - 1.3) / .8))
            arcp = skia.Path()
            arcp.addArc(skia.Rect.MakeLTRB(cx - R, cy - R, cx + R, cy + R), 180, 180)
            c.drawPath(arcp, line("#FFFFFF", 14, .3 * a))
            arc2 = skia.Path()
            arc2.addArc(skia.Rect.MakeLTRB(cx - R, cy - R, cx + R, cy + R), 180, 180 * k)
            c.drawPath(arc2, line("#FF5A3B", 14, a))
            text(c, "%d %%" % round(k * v(11) / LIBERATION * 100), cx, cy - 30, 80, "#FFE14D", INK, 10, a=a)
            text(c, "DE LA VITESSE DE LIBÉRATION", cx, cy + 60, 40, "#FFFFFF", INK, 7, a=a)
            text(c, "(40 300 km/h)", cx, cy + 108, 38, "#C9C6D8", a=a)


# ---------------------------------------------------------------- voyage Terre ↔ Lune
def scene_voyage(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    c.drawImage(STARS, 0, 0)
    E = (220, 1450, 120)
    M = (860, 760, 70)
    img, x0, y0 = earth_rgba(E[2], cx=E[0], cy=E[1])
    c.drawImage(img, x0, y0)
    c.drawCircle(E[0], E[1], E[2], line(INK, 6))
    draw_moon(c, M[0], M[1], M[2], t, "scared")
    c.drawPath(skia.Path().moveTo(E[0] + 90, E[1] - 90).lineTo(M[0] - 50, M[1] + 50),
               skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5, Color=col("#FFFFFF", .6), PathEffect=skia.DashPathEffect.Make([18, 12], 0)))
    text(c, "384 400 km", (E[0] + M[0]) / 2 + 60, (E[1] + M[1]) / 2 + 80, 50, "#FFFFFF", INK, 9, align="left")
    ang = math.degrees(math.atan2(M[1] - E[1], M[0] - E[0]))
    if key in ("hook", "quitte"):
        u = clamp((d_ - .2) / (b["dur"] - .5))
        q = 1 - (1 - u) ** 1.5 if key == "quitte" else eout(u) * .55
        x, y = lerp(E[0] + 90, M[0] - 60, q), lerp(E[1] - 90, M[1] + 60, q)
        c.save()
        c.translate(x, y)
        c.rotate(ang)
        run_cat(c, 0, 40, .2 if key == "quitte" else .3, t, 2.5, 1, 3, helmet=True)
        c.restore()
        if key == "quitte":
            mins = round(u * H_LUNE * 60)
            text(c, "trajet : %d h %02d" % (mins // 60, mins % 60), 540, 1720, 66, "#FFE14D", INK, 10)
        else:
            bubble(c, 300, 1150, "Bye.", 52, back((d_ - 1.0) / .16), -3)
    else:  # n12 : retour vers la Terre
        u = clamp((d_ - .2) / (b["dur"] - .5))
        q = u ** 1.3
        x, y = lerp(M[0] - 60, E[0] + 90, q), lerp(M[1] + 60, E[1] - 90, q)
        c.save()
        c.translate(x, y)
        c.rotate(ang)
        run_cat(c, 0, 40, .2, t, 2.5, -1, 3, helmet=True)
        c.restore()
        mins = round(u * H_RET * 60)
        text(c, "%d h %02d" % (3 + mins // 60, mins % 60), 540, 1720, 72, "#FFFFFF", INK, 11)


def scene_lune(c, t, b):
    d_ = t - b["start"]
    c.drawImage(STARS, 0, 0)
    img, x0, y0 = earth_rgba(110, cx=820, cy=860)
    c.drawImage(img, x0, y0)
    c.drawCircle(820, 860, 110, line(INK, 6))
    shape(c, oval(-500, 1360, W + 500, 2700), "#C9CBD6", 8)
    for (x, y, r) in ((180, 1480, 50), (760, 1450, 34), (560, 1640, 70), (950, 1600, 30)):
        c.drawOval(skia.Rect.MakeLTRB(x - r, y - r * .4, x + r, y + r * .4), fill("#A7A9B8"))
    u = eout(d_ / .5)
    mx, my = 400, lerp(1000, 1500, u)
    if d_ < .9:
        k = clamp((d_ - .45) / .45)
        for i in range(8):
            a_ = math.pi + math.pi * i / 7
            c.drawCircle(mx + math.cos(a_) * 200 * k, 1500 + math.sin(a_) * 60 * k, 22 * (1 - k) + 2, fill("#E3E4EC", .9))
    asleep = d_ > 1.0
    draw_cat(c, mx, my, .42, t, "bliss" if asleep else "open", 0)
    c.drawCircle(mx, my - 270 * .42, 190 * .42, fill("#BEE8FF", .22))
    c.drawCircle(mx, my - 270 * .42, 190 * .42, line("#E9F6FF", 8))
    c.drawCircle(mx, my - 270 * .42, 190 * .42, line(INK, 3))
    if asleep:
        for k in range(3):
            ph = (t * .7 + k / 3) % 1
            text(c, "z", mx + 110 + ph * 70, my - 300 - ph * 110, 40 + 26 * ph, "#FFFFFF", INK, 6, a=1 - ph)
    text(c, "14 h 36", 540, 1760, 64, "#FFFFFF", INK, 10)


# ---------------------------------------------------------------- HUD, légende, carton
def heat_c(d):
    u = clamp((d - 1) / 11)
    stops = [(0, "#59E36A"), (.3, "#D7F03A"), (.5, "#FFC531"), (.7, "#FF7A1F"), (.88, "#FF2E2E"), (1, "#FF2EA6")]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if a <= u <= b:
            return hexmix(ca, cb, (u - a) / (b - a))
    return "#FF2EA6"


def big_txt(d):
    return nb(round(V1 * 2 ** (d - 1))) + " KM/H"


assert big_txt(1) == "50 KM/H" and big_txt(6) == "1 600 KM/H" and big_txt(12) == "102 400 KM/H"

NOTE = {2: "comme un guépard", 4: "plus qu'un train à grande vitesse", 6: "Mach %s" % fr(MACH6, 1), 7: "Paris–Marseille : 12 min",
        9: "tour de la Terre : 3 h 08", 10: "presque l'orbite", 11: "il quitte la Terre", 12: "retour : 3 h 44"}


def low_txt(d):
    dd = round(d)
    if dd in NOTE:
        return "Nuit n° %d · %s" % (dd, NOTE[dd])
    return "Nuit n° %d" % dd


def hud(c, t, b):
    d = d_at(t)
    hook = b["key"] == "hook"
    colr = heat_c(12 if hook else d)
    d_ = t - b["start"]
    pop = 1 + .14 * (1 - eout(d_ / .22)) if b["d1"] != b["d0"] else 1.0
    c.save()
    c.translate(540, 262)
    c.scale(pop, pop)
    pan = rrect(-420, -135, 420, 135, 44)
    c.drawPath(pan, fill("#14121C", .94))
    c.drawPath(pan, line(colr, 8))
    head = "VITESSE DE MICHEL À 3 H DU MATIN"
    big = "DE 50 À 102 400 KM/H" if hook else big_txt(d)
    low = "×2 chaque nuit" if hook else low_txt(d)
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


CARD_LINES = ("Très approximatif : 50 km/h la nuit 1, ×2 chaque nuit.",
              "Chat : vers 50 km/h (Vikidia ; varie selon les sources).",
              "Guépard : 90 à 110 km/h. Train à grande vitesse : 320 km/h.",
              "Son : 1 235 km/h (20 °C). Orbite basse : 28 000 km/h.",
              "Libération : 40 300 km/h (ESA). Lune : 384 400 km.",
              "Paris–Marseille : 661 km à vol d'oiseau.",
              "Tour de la Terre (équateur) : 40 075 km.",
              "Air ignoré, gravité de la Terre seule. Couloir de 5 m : inventé.",
              "Ne réveillez pas Gérard. Michel va bien.")


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
    text(c, "NUIT N° 13.", 0, 128, 86, "#FF2EA6")
    c.restore()
    a = clamp((d_ - .5) / .25)
    for i, l in enumerate(CARD_LINES):
        text(c, l, 540, 1000 + i * 62, fit(l, 42, 980), "#A9A6BC", a=a)


def shake_amp(t):
    amp = 0
    for tk in JUMPS + [K["n6"] + .65, K["immeuble"], K["fin"]]:
        d_ = t - tk
        if 0 <= d_ < .22:
            amp = max(amp, 9 * (1 - d_ / .22))
    return amp


def burst(c, t):
    for tk in JUMPS:
        d_ = t - tk
        if 0 <= d_ < .07:
            c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", .5 * (1 - d_ / .07)))


SCN = dict(salon=scene_salon, train=scene_train, mach=scene_mach, immeuble=scene_immeuble, carte=scene_carte, terre=scene_terre,
           orbite=scene_orbite, voyage=scene_voyage, lune=scene_lune)


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


_spl = [K["n4"], K["n7"], K["n10"], K["calme"], CARD, END]
SPL = [("s_%d" % i, a, z) for i, (a, z) in enumerate(zip([0] + _spl, _spl))]


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
    print("par s", PAR_S, "mach", MACH6, "PM", PM_MIN, "tour", TOUR_H, "lune", H_LUNE, "retour", H_RET)
    if sys.argv[1:2] == ["png"]:
        os.makedirs("pc", exist_ok=True)
        for ts in sys.argv[2:]:
            png(float(ts), "pc/t%06.2f.png" % float(ts))
    if sys.argv[1:2] == ["keys"]:
        os.makedirs("pc", exist_ok=True)
        for b in BEATS:
            png(b["start"] + b["dur"] * .75, "pc/%05.1f_%s.png" % (b["start"], b["key"]))
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
