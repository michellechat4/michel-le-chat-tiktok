"""Gérard lâche une croquette de plus en plus haut (hauteur ×2 chaque jour), du haut d'une échelle de plus en plus grande.
Gag : grâce à l'air, elle arrive toujours à environ 36 km/h (vitesse limite)… jusqu'au jour 29 : 268 435 km,
presque 3 jours de chute, entrée à 39 400 km/h, elle prend feu. Une étoile filante. Michel fait un vœu : le sac."""
import math, random, sys, os, subprocess
import importlib.util as _u
import numpy as np
import skia
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "moteur"))
import art
from art import (fill, line, col, hexmix, poly, rrect, oval, shape, text, jitter, clamp, lerp, eout, ein, back,
                 draw_cat, draw_gerard, draw_eiffel, draw_moon, earth_rgba, STARS, bubble, wrap_rich, TF, INK, W, H, FPS)

# décor du salon, outils repris de la vidéo 08
_sp = _u.spec_from_file_location("saut08", os.path.join(HERE, "08_saut.py"))
V8 = _u.module_from_spec(_sp)
_sp.loader.exec_module(V8)
sky_grad, fit, nb, FLOOR, pigeon, scale_bar, plane = V8.sky_grad, V8.fit, V8.nb, V8.FLOOR, V8.pigeon, V8.scale_bar, V8.plane
SHELF_Y = V8.SHELF_Y

# ---------------------------------------------------------------- chiffres (calculés, pas recopiés)
H1 = 1.0                  # m, jour 1 : lâchée de la main de Gérard
M_CROQ = 0.25e-3          # kg, masse d'une croquette (ESTIMATION, non sourcée)
D_CROQ = 0.010            # m, diamètre (ESTIMATION) ; traitée comme une petite sphère
CD = 0.5                  # coefficient de traînée d'une sphère (valeur de manuel, environ 0,47)
GOUTTE = 10               # m/s, « about 10 meters per second » pour les plus grosses gouttes (NASA GPM, FAQ)
EIFFEL = 330              # m, avec l'antenne de 2022 (déjà utilisé vidéo 08)
EVEREST = 8848.86         # m (déjà utilisé vidéo 08)
KARMAN = 100              # km, limite conventionnelle de l'espace (OQLF, Vitrine linguistique)
LUNE = 384400             # km, distance moyenne Terre-Lune
METEORE = 30              # km/s, vitesse typique des étoiles filantes (CNES) ; les grains brûlent vers 80 km
GM, RT = 3.986004418e14, 6.371e6
A_CROQ = math.pi * (D_CROQ / 2) ** 2

# atmosphère standard (densité en kg/m³, US Standard Atmosphere 1976, interpolation log)
_HT = np.array([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 150]) * 1000.
_RH = np.log([1.225, .4135, .08891, .01841, .003996, .001027, 3.097e-4, 8.283e-5, 1.846e-5, 3.416e-6, 5.604e-7, 9.708e-8, 2.222e-8, 2.076e-9])
_LAY = [(0, 288.15, -6.5e-3), (11000, 216.65, 0), (20000, 216.65, 1e-3), (32000, 228.65, 2.8e-3), (47000, 270.65, 0),
        (51000, 270.65, -2.8e-3), (71000, 214.65, -2e-3), (86000, 186.95, 0)]


def rho(h):
    return 0.0 if h > 150000 else float(np.exp(np.interp(max(h, 0), _HT, _RH)))


def son(h):
    T = 288.15
    for hb, Tb, L in _LAY:
        if min(h, 86000) >= hb:
            T = Tb + L * (min(h, 86000) - hb)
    return math.sqrt(1.4 * 287.05 * T)


def hd(d):
    return H1 * 2 ** (d - 1)


def chute(h0):
    """Chute verticale depuis h0 (m), sans vitesse initiale, air + gravité en 1/r².
    Renvoie (durée s, vitesse d'arrivée m/s, vitesse max m/s, Mach max)."""
    from scipy.integrate import solve_ivp

    def f(t, y):
        v = y[1]
        return [v, -GM / (RT + y[0]) ** 2 + .5 * rho(y[0]) * CD * A_CROQ * v * v / M_CROQ]
    ev = lambda t, y: y[0]
    ev.terminal = True
    s = solve_ivp(f, [0, 1e6], [h0, 0.0], events=ev, rtol=1e-8, atol=1e-6, max_step=max(.01, h0 / 1500))
    v = -s.y[1]
    mach = max(v[k] / son(s.y[0][k]) for k in range(0, len(v), 5))
    return s.t_events[0][0], float(v[-1]), float(v.max()), mach


def chute_espace(h0):
    """Chute depuis très loin jusqu'à 120 km (début de l'entrée), Terre seule. Renvoie (jours, km/s)."""
    from scipy.integrate import solve_ivp
    ev = lambda t, y: y[0] - (RT + 120000)
    ev.terminal = True
    s = solve_ivp(lambda t, y: [y[1], -GM / y[0] ** 2], [0, 1e8], [RT + h0, 0], events=ev, rtol=1e-11, atol=1e-3)
    return s.t_events[0][0] / 86400, -s.y_events[0][0][1] / 1000


SIM = {d: chute(hd(d)) for d in (1, 4, 6, 10, 14, 17, 18)}
VLIM = math.sqrt(2 * M_CROQ * 9.81 / (1.225 * CD * A_CROQ))
JOURS29, V29 = chute_espace(hd(29))
KMH = lambda v: v * 3.6

assert hd(1) == 1 and hd(4) == 8 and hd(6) == 32 and hd(10) == 512 and hd(14) == 8192
assert hd(9) < EIFFEL < hd(10) and hd(14) < EVEREST < hd(15)
assert hd(17) / 1000 < KARMAN < hd(18) / 1000 and round(hd(17) / 1000, 1) == 65.5 and round(hd(18) / 1000) == 131
assert round(hd(29) / 1000) == 268435 and round(hd(29) / 1000 / LUNE, 2) == .70
assert round(KMH(VLIM)) == 36 and abs(VLIM - GOUTTE) < .5
assert round(KMH(SIM[1][1])) == 15 and round(KMH(SIM[4][1])) == 32
assert all(round(KMH(SIM[d][1])) == 36 for d in (6, 10, 14, 17, 18))
assert round(SIM[10][0]) == 51 and round(SIM[14][0] / 60) == 11 and round(SIM[17][0] / 60) == 25
assert SIM[17][3] > 1.1 and round(KMH(SIM[17][2]), -1) == 1430
assert round(SIM[18][3], 1) == 3.5
assert round(JOURS29, 1) == 2.9 and round(KMH(V29 * 1000), -2) == 39400


def fr(x, n=0):
    return (("%." + str(n) + "f") % x).replace(".", ",")


V17 = nb(round(KMH(SIM[17][2]), -1))
V29T = nb(round(KMH(V29 * 1000), -2))

# ---------------------------------------------------------------- chronologie
# (clé, durée, jour, légende, Gérard dit, décor)
RAW = [
    ("hook", 3.2, 1, "GÉRARD LÂCHE UNE CROQUETTE | *DE PLUS EN PLUS HAUT.*", None, "nuit"),
    ("regle", 3.0, 1, "Chaque jour, il la lâche | *deux fois plus haut.*", "Attrape !", "salon"),
    ("j1", 3.2, 1, "Jour 1 : 1 mètre. | Elle arrive à *%d km/h.*" % round(KMH(SIM[1][1])), None, "salon"),
    ("j4", 3.2, 4, "Jour 4 : 8 mètres. | *%d km/h.*" % round(KMH(SIM[4][1])), None, "jardin"),
    ("j6", 3.2, 6, "Jour 6 : 32 mètres. | *36 km/h.*", None, "jardin"),
    ("limite", 4.0, 6, "L'air la freine : *36 km/h max.* | Comme une grosse goutte de pluie.", None, "jardin"),
    ("j10", 3.4, 10, "Jour 10 : 512 m. Plus haut | que la *tour Eiffel.*", None, "paris"),
    ("attente", 3.2, 10, "Chute : *%d secondes.* | Arrivée : *36 km/h.*" % round(SIM[10][0]), None, "paris"),
    ("j14", 3.4, 14, "Jour 14 : 8 192 m. | Chute : *%d minutes.*" % round(SIM[14][0] / 60), None, "ciel"),
    ("j17", 3.4, 17, "Jour 17 : 65,5 km. Elle passe | *le mur du son.*", None, "mach"),
    ("frein", 3.6, 17, "Puis l'air la freine. | Arrivée : *36 km/h.*", None, "jardin"),
    ("j18", 3.4, 18, "Jour 18 : 131 km. | Gérard est *dans l'espace.*", "Attrape !", "espace"),
    ("blase", 3.0, 18, "Mach %s en route. | Arrivée : *36 km/h.*" % fr(SIM[18][3], 1), None, "jardin"),
    ("j29", 3.6, 29, "Jour 29 : 268 435 km. | *70 % du chemin* vers la Lune.", None, "lune"),
    ("trajet", 3.2, 29, "Elle tombe pendant | *presque 3 jours.*", None, "lune"),
    ("entree", 3.6, 29, "Elle arrive à *%s km/h.* | Elle *prend feu.*" % V29T, None, "entree"),
    ("etoile", 3.4, 29, "*Une étoile filante.* | Michel fait un vœu.", None, "nuit"),
    ("voeu", 3.4, 29, "Son vœu : *le sac entier.* | Lâché d'*1 mètre.*", None, "salon"),
    ("fin", 3.0, 29, "Jour 30 ?", "Non.", "salon"),
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

# moments de chute (début, arrivée) par clé, en secondes après le début du temps
DROP = dict(j1=(.6, 1.15), j4=(.5, 1.5), j6=(.5, 1.7), j10=(.5, 3.6), attente=(-3.0, 2.2), j14=(.5, 3.6),
            frein=(-.1, 1.6), j18=(.9, 3.6), blase=(-.2, 1.3))


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
def croq(c, x, y, r, rot=0.0, fire=0.0, trail=0.0, t=0.0):
    """Une croquette (petit trèfle brun). fire : flammes ; trail : traits de vitesse au-dessus."""
    if trail > 0:
        for k in (-1, 0, 1):
            c.drawLine(x + k * r * .7, y - r * 1.6, x + k * r * .7, y - r * (1.6 + 4 * trail), line("#FFFFFF", max(2, r * .22), .8))
    if fire > 0:
        for k in range(5, 0, -1):
            rr = r * (1 + k * .55 * fire)
            c.drawCircle(x + k * r * .55 * fire, y - k * r * .75 * fire, rr,
                         fill(("#FFF6C2", "#FFE14D", "#FFB02E", "#FF6A1F", "#FF2E2E")[k - 1], .55 * fire))
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    p = skia.Path()
    for k in range(3):
        a = k * 2 * math.pi / 3
        p.addCircle(math.cos(a) * r * .42, math.sin(a) * r * .42, r * .62)
    c.drawPath(p, line(INK, r * .36))
    c.drawPath(p, fill(hexmix("#9B6A3C", "#FFE14D", fire * .6)))
    c.drawCircle(-r * .2, -r * .25, r * .16, fill("#C9935E"))
    c.restore()


def sparkle(c, x, y, r, a=1.0):
    p = poly([(x, y - r), (x + r * .25, y - r * .25), (x + r, y), (x + r * .25, y + r * .25), (x, y + r), (x - r * .25, y + r * .25), (x - r, y), (x - r * .25, y - r * .25)])
    shape(c, p, "#FFE14D", 4, a)


def ger_drop(c, x, floor, s, t, stage=0, suit=False, holding=True, arm="out"):
    """Gérard debout (pieds en x, floor), bras gauche tendu vers la gauche. Renvoie la position de la main."""
    c.save()
    c.translate(x, floor)
    c.scale(s, s)
    c.translate(-790, -1516)
    sw = "#F2F2F7" if suit else "#3F6FD8"
    draw_gerard(c, stage, t, suit, 0, True)
    hand = (430, 1100) if arm == "out" else (640, 1010)
    for sg in (-1, 1):
        a = skia.Path()
        a.moveTo(790 + sg * 96, 1160)
        if sg == -1:
            a.quadTo(600, 1150, hand[0], hand[1])
        else:
            a.quadTo(790 + 130, 1250, 790 + 118, 1330)
        c.drawPath(a, line(INK, 56))
        c.drawPath(a, line(sw, 42))
    art.draw_mitt(c, hand[0], hand[1], .42, suit)
    if suit:
        c.drawCircle(790, 1000, 190, fill("#BEE8FF", .22))
        c.drawCircle(790, 1000, 190, line("#E9F6FF", 10))
        c.drawCircle(790, 1000, 190, line(INK, 4))
    c.restore()
    return x + (hand[0] - 790) * s, floor + (hand[1] - 1516) * s


def ladder(c, x, y_bot, y_top, w=56, step=34, a=1.0, colr="#B5BACB"):
    for sg in (-1, 1):
        c.drawLine(x + sg * w / 2, y_bot, x + sg * w / 2, y_top, line(INK, 12, a))
        c.drawLine(x + sg * w / 2, y_bot, x + sg * w / 2, y_top, line(colr, 6, a))
    y = y_bot - step / 2
    while y > y_top + 4:
        c.drawLine(x - w / 2, y, x + w / 2, y, line(INK, 8, a))
        c.drawLine(x - w / 2, y, x + w / 2, y, line(colr, 4, a))
        y -= step


def mouth(mx, my, s):
    return mx, my - 215 * s


def drop_pos(d_, key, y0, y1):
    """Position verticale de la croquette (None avant / après)."""
    a, z = DROP[key]
    if d_ < a:
        return y0, False
    if d_ >= z:
        return None, True
    u = (d_ - a) / (z - a)
    # accélère au début puis vitesse constante (vitesse limite)
    k = .12
    f = (u * u / (2 * k)) if u < k else (k / 2 + (u - k))
    f /= (1 - k / 2)
    return lerp(y0, y1, f), False


def cronch(c, x, y, d_since, size=54):
    if 0 <= d_since < 1.2:
        s = back(d_since / .15)
        c.save()
        c.translate(x, y)
        c.rotate(-6)
        c.scale(s, s)
        text(c, "CRONCH", 0, 0, size, "#FFE14D", INK, 9)
        c.restore()


def speed_tag(c, x, y, kmh, a):
    if a <= 0:
        return
    s_ = "%d km/h" % kmh
    f = skia.Font(TF, 46)
    w = f.measureText(s_)
    p = rrect(x - w / 2 - 22, y - 46, x + w / 2 + 22, y + 16, 22)
    c.drawPath(p, fill("#14121C", .9 * a))
    c.drawPath(p, line("#FFE14D", 5, a))
    text(c, s_, x, y, 46, "#FFE14D", a=a)


def drop_scene(c, t, b, hand, ground, mx, ms, kmh, crunch_size=54):
    """Croquette qui tombe de la main jusqu'à la bouche de Michel, puis CRONCH."""
    key = b["key"]
    d_ = t - b["start"]
    mxx, myy = mouth(mx, ground, ms)
    y, done = drop_pos(d_, key, hand[1] + 10, myy)
    r = 14
    if y is not None:
        moving = d_ > DROP[key][0]
        croq(c, hand[0] if moving else hand[0], y, r, t * 5 if moving else 0, 0, .8 if moving else 0)
    mood = "open"
    since = d_ - DROP[key][1]
    if done:
        mood = "wink" if since > .5 else "bliss"
    draw_cat(c, mx, ground, ms, t, mood, 3 if 0 <= since < .3 else 0)
    if done:
        cronch(c, mx + 40, myy - 80 * ms / .3, since, crunch_size)
        speed_tag(c, mx + (200 if mx < 600 else -200), ground - 60, kmh, clamp((since - .25) / .2))


# ---------------------------------------------------------------- décors
def scene_salon(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    V8.salon(c, t, b, night=False, holed=False)
    # sac de croquettes sur l'étagère
    sx = 800
    if key in ("regle", "j1"):
        sack(c, sx, SHELF_Y, 0)
        GX, MXX = 900, None
        hand = ger_drop(c, GX, FLOOR + 14, .62, t, 0)
        mx = hand[0]
        if key == "regle":
            draw_cat(c, mx, FLOOR + 10, .36, t, "open")
            croq(c, hand[0], hand[1] + 14, 15)
            V8.gerbub(c, t, b, GX - 40, 960)
        else:
            drop_scene(c, t, b, hand, FLOOR + 10, mx, .36, round(KMH(SIM[1][1])), 64)
            if d_ > 1.6:
                c.drawLine(hand[0] + 80, hand[1], hand[0] + 80, FLOOR - 10, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5,
                                                                                    Color=col("#FFFFFF"), PathEffect=skia.DashPathEffect.Make([16, 12], 0)))
                text(c, "1 m", hand[0] + 100, (hand[1] + FLOOR) / 2, 50, "#FFE14D", INK, 9, align="left", a=clamp((d_ - 1.6) / .2))
        return
    # vœu : le sac tombe de l'étagère, Michel enseveli de croquettes
    mx = 560
    u = clamp((d_ - .5) / .45) if key == "voeu" else 1.0
    if key == "voeu" and u <= 0:
        sack(c, sx, SHELF_Y, 0)
        draw_cat(c, mx, FLOOR + 10, .4, t, "open")
        if d_ > .1:
            sparkle(c, sx, SHELF_Y - 240, 30, clamp((d_ - .1) / .2))
        return
    if u < 1:
        sack(c, lerp(sx, 640, u), lerp(SHELF_Y, FLOOR - 120, u * u), u * 110)
        draw_cat(c, mx, FLOOR + 10, .4, t, "open")
        return
    # pile de croquettes
    rr = random.Random(7)
    grow = eout(clamp((d_ - .95) / .4)) if key == "voeu" else 1
    for i in range(130):
        ang = rr.uniform(math.pi, 2 * math.pi)
        dist = rr.uniform(0, 1) ** .5
        x = mx + math.cos(ang) * 300 * dist
        y = FLOOR + 10 + math.sin(ang) * 210 * dist * grow
        croq(c, x, y, 13, rr.uniform(0, 6))
    sack(c, 820, FLOOR + 5, 80, empty=True)
    draw_cat(c, mx, FLOOR - 120 * grow, .4, t, "bliss" if key == "voeu" else "wink")
    if key == "voeu" and d_ > 1.2:
        cronch(c, mx + 150, FLOOR - 400, d_ - 1.2, 64)
    if key == "fin":
        gx = lerp(1300, 930, eout(d_ / .5))
        ger_drop(c, gx, FLOOR + 14, .62, t, 2, arm="up")
        if b["ger"]:
            bubble(c, 820, 900, b["ger"], 64, back((d_ - .5) / .16), 3)


def sack(c, x, y_bottom, rot=0.0, empty=False):
    c.save()
    c.translate(x, y_bottom)
    c.rotate(rot)
    p = skia.Path()
    p.moveTo(-70, 0)
    p.lineTo(-80, -190)
    p.lineTo(80, -190)
    p.lineTo(70, 0)
    p.close()
    shape(c, p, "#E85D3F" if not empty else "#C9503A", 7)
    shape(c, rrect(-82, -214, 82, -186, 8), "#C9503A", 6)
    shape(c, oval(-42, -150, 42, -70), "#FFFFFF", 5)
    croq(c, -10, -112, 16)
    croq(c, 14, -102, 14, 1)
    c.restore()


def house(c, x, G, PX, a=1.0):
    """Maison de 3 m de murs, faîte à 5 m (échelle PX px/m)."""
    w = 7 * PX
    shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(x, G - 3 * PX, x + w, G)), "#F2E3C6", max(3, min(7, PX / 20)), a)
    shape(c, poly([(x - .3 * PX, G - 3 * PX), (x + w + .3 * PX, G - 3 * PX), (x + w / 2, G - 5 * PX)]), "#C8553D", max(3, min(7, PX / 20)), a)
    for wx in (x + 1 * PX, x + 4.6 * PX):
        shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(wx, G - 2.4 * PX, wx + 1.3 * PX, G - 1.2 * PX)), "#9BDCFA", max(2, min(6, PX / 20)), a)


def tree(c, x, G, PX):
    shape(c, rrect(x - .25 * PX, G - 3 * PX, x + .25 * PX, G, 4), "#8A5A3B", max(3, min(6, PX / 20)))
    shape(c, oval(x - 1.6 * PX, G - 6.5 * PX, x + 1.6 * PX, G - 2.6 * PX), "#59B36A", max(3, min(6, PX / 20)))


TOP = 760          # hauteur (px) de la main de Gérard dans les décors verticaux
LX = 640           # x de l'échelle


def scene_jardin(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    sky_grad(c, "#5CB8F2", "#D3F1FF")
    G = 1640
    day = {"j4": 4, "j6": 6, "limite": 6}.get(key, None)
    if day:
        h = hd(day)
        gs = .3
        foot = TOP + (1516 - 1100) * gs
        PX = (G - TOP) / h
        house(c, 60 if day == 4 else 120, G, PX)
        tree(c, 900, G, PX)
        c.drawRect(skia.Rect.MakeLTRB(0, G, W, H), fill("#7CC46E"))
        c.drawLine(0, G, W, G, line(INK, 6))
        ladder(c, LX, G + 10, foot, step=max(14, .3 * PX))
        hand = ger_drop(c, LX + 30, foot, gs, t, 1 if day == 6 else 0)
        mx = hand[0]
        if key == "limite":
            draw_cat(c, mx, G + 10, .3, t, "wink")
            speed_tag(c, mx + 210, G - 60, 36, 1)
            panel_limite(c, t, d_)
        else:
            drop_scene(c, t, b, hand, G + 10, mx, .3, round(KMH(SIM[day][1])))
        scale_bar(c, 1000, G, hand[1], "%d m" % h, "#FFE14D", -1, clamp((d_ - .8) / .2) if key != "limite" else 1)
        return
    # frein / blase : l'échelle monte hors champ, la croquette arrive d'en haut
    PX = 60
    house(c, 60, G, PX)
    tree(c, 900, G, PX)
    c.drawRect(skia.Rect.MakeLTRB(0, G, W, H), fill("#7CC46E"))
    c.drawLine(0, G, W, G, line(INK, 6))
    ladder(c, LX, G + 10, -50, step=18)
    mx = 520
    drop_scene(c, t, b, (mx, -40), G + 10, mx, .3, 36)
    if key == "frein":
        # chrono de chute
        a = clamp((d_ - .2) / .2)
        text(c, "chute : %d min" % round(SIM[17][0] / 60), 300, 1000, 62, "#FFFFFF", INK, 9, a=a)
    if key == "blase" and d_ > 1.9:
        text(c, "Mrrp.", mx - 160, G - 230, 52, "#FFFFFF", INK, 9, a=clamp((d_ - 1.9) / .15))


PY0, PY1 = 640, 900


def panel(c, a=1.0, y0=PY0, y1=PY1):
    p = rrect(60, y0, 1020, y1, 34)
    c.drawPath(p, fill("#14121C", .92 * a))
    c.drawPath(p, line("#FFFFFF", 6, a))


def drop_icon(c, x, y, r, a):
    p = skia.Path()
    p.moveTo(x, y - r * 1.6)
    p.quadTo(x + r * 1.1, y - r * .2, x + r, y + r * .2)
    p.arcTo(skia.Rect.MakeLTRB(x - r, y - r * .8, x + r, y + r * 1.2), 0, 180, False)
    p.quadTo(x - r * 1.1, y - r * .2, x, y - r * 1.6)
    shape(c, p, "#7EC8FF", 5, a)


def panel_limite(c, t, d_):
    a = clamp((d_ - .5) / .25)
    if a <= 0:
        return
    panel(c, a)
    text(c, "VITESSE LIMITE (AIR)", 540, 702, 44, "#FFFFFF", INK, 7, a=a)
    drop_icon(c, 150, 780, 26, a)
    text(c, "grosse goutte : env. 10 m/s", 210, 796, 42, "#9BDCFA", align="left", a=a)
    croq(c, 150, 852, 20)
    text(c, "croquette : env. 10 m/s (estimé)", 210, 868, 40, "#FFE14D", align="left", a=a)


def scene_paris(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    sky_grad(c, "#F7B267", "#FFE9B8")
    G = 1660
    h = hd(10)
    PX = (G - TOP) / h
    r = random.Random(3)
    x = -20
    while x < W:
        w_ = r.uniform(60, 110)
        shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(x, G - 20 * PX, x + w_, G)), "#B58FA0", 3)
        x += w_ + 4
    c.save()
    c.translate(860, G)
    draw_eiffel(c, EIFFEL * PX)
    c.restore()
    text(c, "330 m", 860, G - EIFFEL * PX - 26, 46, "#FFFFFF", INK, 9)
    c.drawRect(skia.Rect.MakeLTRB(0, G, W, H), fill("#8A8F9C"))
    c.drawLine(0, G, W, G, line(INK, 6))
    gs = .3
    foot = TOP + (1516 - 1100) * gs
    ladder(c, 500, G + 10, foot, w=44, step=10)
    hand = ger_drop(c, 530, foot, gs, t, 0 if key == "j10" else 2)
    mx = hand[0]
    if key == "attente":
        # vue rapprochée : chrono, Michel tape du pied
        a = clamp(d_ / .2)
        tt = clamp((d_ + 3.0 - .5) / 5.2) * SIM[10][0]
        text(c, "%d s" % min(round(SIM[10][0]), int(tt)), 230, 1000, 70, "#FFFFFF", INK, 10, a=a)
    drop_scene(c, t, b, hand, G + 10, mx, .2, 36, 46)
    scale_bar(c, 1010, G, hand[1], "512 m", "#FFE14D", -1, clamp((d_ - .8) / .2) if key == "j10" else 1)
    for i in range(3):
        pigeon(c, 180 + i * 120 + 30 * math.sin(t + i), 900 + 40 * i, .7, t, i)


def cloud(c, x, y, s, a=1.0):
    for dx, dy, r in ((-60, 10, 50), (0, -20, 70), (70, 5, 55), (20, 20, 50)):
        c.drawCircle(x + dx * s, y + dy * s, r * s, fill("#FFFFFF", .92 * a))


def scene_ciel(c, t, b):
    d_ = t - b["start"]
    sky_grad(c, "#2E6FD0", "#BFE6FF", 300, 1700)
    G = 1720
    h = hd(14)
    PX = (G - TOP) / h
    pk = G - EVEREST * PX
    m = poly([(380, G), (700, pk + 200), (850, pk), (960, pk + 160), (1100, pk + 300), (1300, G)])
    shape(c, m, "#8C8FA3", 7)
    shape(c, poly([(790, pk + 90), (850, pk), (920, pk + 90), (880, pk + 70), (850, pk + 110), (820, pk + 80)]), "#FFFFFF", 5)
    text(c, "EVEREST : 8 849 m", 830, pk - 26, 42, "#FFFFFF", INK, 8)
    for i, (x, y) in enumerate(((150, 1200), (900, 1350), (420, 1480), (750, 1050))):
        cloud(c, x + 20 * math.sin(t * .4 + i), y, .9)
    c.drawRect(skia.Rect.MakeLTRB(0, G, W, H), fill("#7CC46E"))
    gs = .3
    foot = TOP + (1516 - 1100) * gs
    ladder(c, 440, G + 10, foot, w=40, step=8)
    hand = ger_drop(c, 470, foot, gs, t, 1)
    drop_scene(c, t, b, hand, G + 10, hand[0], .16, 36, 40)
    scale_bar(c, 120, G, hand[1], "8 192 m", "#FFE14D", 1, clamp((d_ - .8) / .2))


def scene_mach(c, t, b):
    d_ = t - b["start"]
    sky_grad(c, "#0E1E4A", "#3F7FD8", 300, 1700)
    r = random.Random(9)
    for i in range(10):
        y = (r.uniform(0, H) - (t * 2600)) % (H + 400) - 200
        x = r.uniform(-60, W)
        shape(c, oval(x, y, x + 220, y + 70), "#FFFFFF", 0, .6)
    cx, cy = 540, 1150
    u = clamp((d_ - .7) / .3)
    if u > 0:
        cone = skia.Path()
        cone.moveTo(cx, cy + 120)
        cone.quadTo(cx - 330, cy - 60, cx - 380, cy - 300)
        cone.quadTo(cx, cy - 200, cx + 380, cy - 300)
        cone.quadTo(cx + 330, cy - 60, cx, cy + 120)
        c.drawPath(cone, fill("#FFFFFF", .5 * u))
        c.drawPath(cone, line("#FFFFFF", 8, .9 * u))
    j = jitter(t, 4)
    croq(c, cx + j[0] * 5, cy + 60 + j[1] * 5, 70, t * 9, 0, 1.4)
    if d_ > .75:
        s_ = back((d_ - .75) / .18)
        c.save()
        c.translate(cx + 220, cy + 330)
        c.rotate(-8)
        c.scale(s_, s_)
        text(c, "BANG !", 0, 0, 120, "#FFE14D", INK, 14)
        c.restore()
        text(c, "%s km/h · Mach %s" % (V17, fr(SIM[17][3], 1)), 540, 1660, 52, "#FFFFFF", INK, 9, a=clamp((d_ - 1.2) / .2))


def scene_espace(c, t, b):
    d_ = t - b["start"]
    p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 1000), (0, 1640)], [col("#06061A"), col("#4FA3E8")]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    rr = random.Random(8)
    for i in range(140):
        y = rr.uniform(0, 1300)
        c.drawCircle(rr.uniform(0, W), y, rr.choice((1.2, 2, 2.6)), fill("#FFFFFF", clamp((1350 - y) / 500)))
    G = 1660
    gs = .28
    foot = TOP + (1516 - 1100) * gs
    PXK = (G - TOP) / (hd(18) / 1000)
    shape(c, oval(-900, G - 30, W + 900, G + 2400), "#2B86DE", 7)
    c.drawPath(oval(-900, G - 30, W + 900, G + 2400), line("#9BDCFA", 18, .5))
    for (x0, w0) in ((80, 260), (600, 320)):
        shape(c, oval(x0, G - 10, x0 + w0, G + 60), "#59B36A", 0)
    ky = G - KARMAN * PXK
    c.drawPath(skia.Path().moveTo(0, ky).lineTo(W, ky),
               skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6, Color=col("#FFE14D"), PathEffect=skia.DashPathEffect.Make([26, 16], 0)))
    text(c, "ESPACE : 100 km", 830, ky - 22, 42, "#FFE14D", INK, 8)
    ladder(c, 600, G + 10, foot, w=40, step=7)
    hand = ger_drop(c, 630, foot, gs, t, 0, suit=True)
    a, z = DROP["j18"]
    if d_ < a:
        croq(c, hand[0], hand[1] + 12, 14)
    else:
        u = clamp((d_ - a) / (z - a))
        y = lerp(hand[1] + 12, G - 20, u * u)
        if u < 1:
            croq(c, hand[0], y, 14, t * 5, 0, .8)
    if b["ger"]:
        bubble(c, 820, foot - 260, b["ger"], 50, back((d_ - .3) / .16), 3)
    scale_bar(c, 120, G - 20, hand[1], "131 km", "#FFE14D", 1, clamp((d_ - .8) / .2))


EARTH = (540, 1640, 70)
MOONP = (540, 700, 42)


def scene_lune(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    c.drawImage(STARS, 0, 0)
    ex, ey, er = EARTH
    img, x0, y0 = earth_rgba(er, cx=ex, cy=ey)
    c.drawImage(img, x0, y0)
    c.drawCircle(ex, ey, er, line(INK, 5))
    draw_moon(c, MOONP[0], MOONP[1], MOONP[2], t, "scared")
    text(c, "LUNE : 384 400 km", MOONP[0] + 70, MOONP[1] + 14, 40, "#FFFFFF", INK, 7, align="left")
    frac = hd(29) / 1000 / LUNE
    y_top = (ey - er) - frac * ((ey - er) - (MOONP[1] + MOONP[2]))
    gs = .1
    foot = y_top
    ladder(c, ex, ey - er + 4, foot, w=22, step=6, colr="#D4D7E0")
    hand = ger_drop(c, ex + 10, foot, gs, t, 0, suit=True)
    text(c, "268 435 km", ex - 70, (foot + ey) / 2, 46, "#FFE14D", INK, 8, align="right")
    if key == "j29":
        croq(c, hand[0], hand[1] + 8, 9)
        if d_ > 1.2:
            bubble(c, ex + 200, foot - 80, "Attrape !", 46, back((d_ - 1.2) / .16), 3)
    else:
        u = clamp((d_ - .2) / (b["dur"] - .4))
        q = u ** 2.2
        y = lerp(hand[1] + 8, ey - er - 10, q)
        croq(c, hand[0], y, 9, t * 3, 0, .5 * u)
        text(c, "chute : jour %s" % fr(JOURS29 * u, 1), 540, 1460, 58, "#FFFFFF", INK, 10)


def scene_entree(c, t, b):
    d_ = t - b["start"]
    p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 600), (0, 1700)], [col("#04040F"), col("#10264F")]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    rr = random.Random(4)
    for i in range(120):
        c.drawCircle(rr.uniform(0, W), rr.uniform(0, 1500), rr.choice((1.2, 2, 2.6)), fill("#FFFFFF", .8))
    # limbe de la Terre
    c.drawCircle(540, 3900, 2400, fill("#1C5FB0"))
    c.drawCircle(540, 3900, 2420, line("#7EC8FF", 30, .45))
    c.drawCircle(540, 3900, 2470, line("#7EC8FF", 40, .15))
    u = clamp((d_ - .1) / 2.6)
    x = lerp(1000, 260, u)
    y = lerp(700, 1450, u)
    fire = clamp((u - .25) / .3)
    # traînée
    for k in range(30):
        f = k / 30
        tx, ty = lerp(x, 1100, f * .8 * u), lerp(y, 600, f * .8 * u)
        c.drawCircle(tx, ty, (26 * (1 - f) + 4) * fire, fill(hexmix("#FFE14D", "#FF4B10", f), .7 * (1 - f) * fire))
    croq(c, x, y, 22, t * 12, fire)
    a = clamp((d_ - .4) / .2)
    text(c, "%s km/h" % V29T, 540, 1700, 72, "#FFE14D", INK, 11, a=a)


def scene_nuit(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    sky_grad(c, "#06061A", "#1B2350", 300, 1600)
    rr = random.Random(11)
    for i in range(110):
        c.drawCircle(rr.uniform(0, W), rr.uniform(560, 1500), rr.choice((1.4, 2.2, 3)), fill("#FFFFFF", .5 + .5 * math.sin(t * 3 + i)))
    G = 1640
    # étoile filante
    u = clamp((d_ + .2) / 1.6) if key == "hook" else clamp((d_ - .3) / 1.4)
    if 0 < u < 1:
        x, y = lerp(1050, 150, u), lerp(620, 1150, u)
        for k in range(24):
            f = k / 24
            c.drawCircle(lerp(x, 1050, f * .6), lerp(y, 620, f * .6), (12 * (1 - f) + 2), fill(hexmix("#FFFFFF", "#FFB02E", f), .8 * (1 - f)))
        croq(c, x, y, 12, t * 10, 1)
    for (x, w_, h_) in ((-60, 300, 230), (820, 320, 280)):
        art.draw_house(c, x, w_, h_, G, "#2C3550", "#1E2440")
    c.drawRect(skia.Rect.MakeLTRB(0, G, W, H), fill("#24432E"))
    c.drawLine(0, G, W, G, line(INK, 6))
    draw_cat(c, 540, G + 10, .42, t, "open" if key == "hook" or d_ < 1.8 else "bliss")
    if key == "etoile" and d_ > 1.8:
        a = clamp((d_ - 1.8) / .2)
        for k in range(3):
            ph = (t * .7 + k / 3) % 1
            sparkle(c, 540 + (k - 1) * 110, G - 330 - ph * 80, 24, a * (1 - ph))


# ---------------------------------------------------------------- HUD, légende, carton
def heat_c(d):
    u = clamp((d - 1) / 28)
    stops = [(0, "#59E36A"), (.3, "#D7F03A"), (.55, "#FFC531"), (.8, "#FF7A1F"), (.92, "#FF2E2E"), (1, "#FF2EA6")]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if a <= u <= b:
            return hexmix(ca, cb, (u - a) / (b - a))
    return "#FF2EA6"


def big_txt(d):
    m = hd(d)
    if m < 1.995:
        return "1 MÈTRE" if m < 1.05 else fr(m, 1) + " MÈTRE"
    if m < 999.5:
        return "%d MÈTRES" % round(m)
    if m < 9999.5:
        return nb(round(m)) + " MÈTRES"
    k = m / 1000
    if k < 99.95:
        return fr(k, 1) + " KM"
    return nb(round(k)) + " KM"


assert big_txt(1) == "1 MÈTRE" and big_txt(4) == "8 MÈTRES" and big_txt(10) == "512 MÈTRES" and big_txt(14) == "8 192 MÈTRES"
assert big_txt(17) == "65,5 KM" and big_txt(18) == "131 KM" and big_txt(29) == "268 435 KM"

ARR = {d: round(KMH(v[1])) for d, v in SIM.items()}


def low_txt(d):
    dd = round(d)
    if dd >= 29:
        return "Jour n° 29 · arrivée : elle brûle"
    if dd in ARR:
        return "Jour n° %d · arrivée : %d km/h" % (dd, ARR[dd])
    return "Jour n° %d" % dd


def hud(c, t, b):
    d = d_at(t)
    hook = b["key"] == "hook"
    colr = heat_c(29 if hook else d)
    d_ = t - b["start"]
    pop = 1 + .14 * (1 - eout(d_ / .22)) if b["d1"] != b["d0"] else 1.0
    c.save()
    c.translate(540, 262)
    c.scale(pop, pop)
    pan = rrect(-420, -135, 420, 135, 44)
    c.drawPath(pan, fill("#14121C", .94))
    c.drawPath(pan, line(colr, 8))
    head = "HAUTEUR DE CHUTE DE LA CROQUETTE"
    big = "DE 1 m À 268 435 km" if hook else big_txt(d)
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


CARD_LINES = ("Très approximatif : 1 m le jour 1, ×2 chaque jour, lâchée sans élan.",
              "Croquette estimée : 0,25 g, 1 cm (non sourcé). Atmosphère standard.",
              "Grosse goutte de pluie : environ 10 m/s (NASA).",
              "Eiffel : 330 m. Everest : 8 849 m. Espace : 100 km (convention).",
              "Lune : 384 400 km. Gravité de la Lune et du Soleil ignorée.",
              "Étoiles filantes : vers 30 km/s, brûlent vers 80 km (CNES).",
              "Ne lancez rien d'une échelle. Michel va bien.")


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
    text(c, "JOUR N° 30.", 0, 128, 86, "#FFB02E")
    c.restore()
    a = clamp((d_ - .5) / .25)
    for i, l in enumerate(CARD_LINES):
        text(c, l, 540, 1000 + i * 62, fit(l, 42, 980), "#A9A6BC", a=a)


def shake_amp(t):
    amp = 0
    for tk in JUMPS + [K["j17"] + .75, K["voeu"] + .95]:
        d_ = t - tk
        if 0 <= d_ < .22:
            amp = max(amp, 9 * (1 - d_ / .22))
    return amp


def burst(c, t):
    for tk in JUMPS:
        d_ = t - tk
        if 0 <= d_ < .07:
            c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", .5 * (1 - d_ / .07)))


SCN = dict(salon=scene_salon, jardin=scene_jardin, paris=scene_paris, ciel=scene_ciel, mach=scene_mach, espace=scene_espace,
           lune=scene_lune, entree=scene_entree, nuit=scene_nuit)


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


_sp = [K["j10"], K["j18"], K["etoile"], CARD, END]
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
    print({d: (round(v[0], 1), round(KMH(v[1]), 1), round(KMH(v[2])), round(v[3], 2)) for d, v in SIM.items()}, JOURS29, V29)
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
