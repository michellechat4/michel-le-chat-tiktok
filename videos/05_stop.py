"""Et si la Terre s'arrêtait une seconde ? Michel est accroché aux rideaux, le salon de Gérard part sans lui."""
import math, random, sys, os, subprocess
import numpy as np
import skia
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "moteur"))
import art
from art import (fill, line, col, hexmix, poly, rrect, oval, shape, text, jitter, clamp, lerp, eout, ein, back,
                 draw_cat, draw_gerard, draw_couch, draw_eiffel, draw_iss, sun_face, earth_rgba, STARS, bubble, wrap_rich, TF, INK, W, H, FPS)

# ---------------------------------------------------------------- chiffres (calculés, pas recopiés)
A, E2 = 6378137.0, 0.00669438     # WGS 84
JOUR = 86164.09                   # jour sidéral, s
LAT = math.radians(48.8566)       # Paris
R_PAR = A / math.sqrt(1 - E2 * math.sin(LAT) ** 2) * math.cos(LAT)
V = 2 * math.pi * R_PAR / JOUR    # 306,6 m/s à Paris
V_EQ = 2 * math.pi * A / JOUR     # 465,1 m/s
KMH, KMH_EQ = V * 3.6, V_EQ * 3.6
CHUTE = .5 * 9.81                 # m en 1 s
OEIL = .15                        # s, pupille masquée (100-150 ms, BioNumbers)
D_OEIL = V * OEIL
TOUR = 330.0
TORNADE = 512.0                   # km/h, Greenfield 2024 (haut de la fourchette radar)
I_T, L_SOL = 8.04e37, 3.828e26    # moment d'inertie, luminosité du Soleil
E_ROT = .5 * I_T * (2 * math.pi / JOUR) ** 2
MIN_SOL = E_ROT / L_SOL / 60
MARCHE = V / (5 / 3.6)            # 5 km/h, s
assert round(KMH, -2) == 1100 and round(KMH_EQ) == 1674 and round(V) == 307 and round(D_OEIL) == 46
assert round(MIN_SOL) == 9 and round(KMH / TORNADE) == 2 and round(MARCHE / 10) == 22 and V / TOUR > .9 and round(CHUTE, 1) == 4.9

# ---------------------------------------------------------------- chronologie
# (clé, durée, T à la fin du temps fort, légende, Gérard dit, décor) ; T = instant réel pendant la seconde
RAW = [
    ("hook", 2.8, None, "LA TERRE S'ARRÊTE. | *UNE SECONDE.*", None, "salon"),
    ("vit", 3.2, None, "Paris tourne à *1 100 km/h.* | Personne ne le sent.", None, "globe"),
    ("tout", 3.0, None, "Le canapé, le frigo, Gérard : | *tout file à cette vitesse.*", None, "salon"),
    ("regarde", 1.9, None, "Michel regarde le plafond.", "Michel ?", "salon"),
    ("rideaux", 2.2, None, "*Il s'accroche aux rideaux.*", None, "salon"),
    ("cafe", 1.3, None, "Gérard boit son café.", None, "salon"),
    ("stop", 2.6, .006, "*STOP.* | La Terre s'arrête.", None, "vol"),
    ("reste", 2.6, .016, "Les murs s'arrêtent. | *Le salon, non.*", None, "vol"),
    ("flag", 2.6, .024, "Michel tient bon. | *Il flotte comme un drapeau.*", None, "vol"),
    ("mur", 2.4, .06, "Le mur du salon ? | *Il n'a pas eu le temps.*", None, "vol"),
    ("oeil", 3.2, OEIL, "En un clin d'œil, | Gérard a fait *46 m.*", None, "vol"),
    ("sent", 2.8, .23, "Il ne sent rien : | *l'air voyage avec lui.*", "Tiens.", "vol"),
    ("vent", 3.0, .31, "Pour les arbres : *1 100 km/h.* | Deux fois la pire tornade.", None, "vol"),
    ("bus", 2.8, .39, "Un bus à sa hauteur. | *Même vitesse.*", "Bonjour.", "vol"),
    ("pole", 2.6, .46, "Au pôle Nord : *0 km/h.* | Un ours n'a rien remarqué.", None, "pole"),
    ("equa", 2.8, .54, "À l'équateur : *1 674 km/h.* | Les cocos s'en vont.", None, "equa"),
    ("iss", 2.4, .60, "L'ISS ne touche pas le sol. | *Rien senti.*", None, "iss"),
    ("seine", 2.6, .67, "La Seine repart | *vers sa source.*", None, "seine"),
    ("soleil", 3.0, .75, "Cette rotation, c'est | *9 minutes de tout le Soleil.*", None, "soleil"),
    ("tombe", 2.4, .84, "Gérard tombe aussi. | *4,9 m. Très calmement.*", None, "vol"),
    ("tour", 3.0, .94, "307 m en une seconde : | *presque une tour Eiffel.*", None, "tour"),
    ("fin1", 1.6, 1.0, "*T + 1,00 s.*", None, "vol"),
    ("repart", 2.6, 1.0, "La Terre repart. | *Tout s'arrête. Pile.*", "Ah.", "vol"),
    ("intact", 2.2, 1.0, "Salon intact. Café intact. | *Au milieu de la route.*", None, "vol"),
    ("marche", 2.2, 1.0, "Retour à pied : *3 min 40.*", None, "marche"),
    ("vide", 2.2, 1.0, "Chez lui : plus rien. | *Sauf Michel.*", None, "fin"),
    ("q", 2.2, 1.0, "Gérard a une question.", "Comment tu savais ?", "fin"),
    ("bouton", 2.4, 1.0, "Derrière le rideau…", None, "fin"),
    ("patte", 2.2, 1.0, "Il regarde Gérard.", "Michel, non.", "fin"),
]
CARD_DUR = 2.6
BEATS = []
_t, _T = 0.0, 0.0
for key, dur, T_end, cap, ger, ph_ in RAW:
    T0 = _T if T_end is not None else None
    BEATS.append(dict(key=key, start=_t, dur=dur, T0=T0, T1=T_end, cap=cap, ger=ger, ph=ph_))
    _t += dur
    if T_end is not None:
        _T = T_end
CARD = _t
END = CARD + CARD_DUR
K = {b["key"]: b["start"] for b in BEATS}
PPM = 100                     # pixels par mètre


def beat_at(t):
    cur = BEATS[0]
    for b in BEATS:
        if b["start"] <= t:
            cur = b
        else:
            break
    return cur


def T_at(t):
    b = beat_at(t)
    if b["T1"] is None:
        return 0.0
    return lerp(b["T0"], b["T1"], clamp((t - b["start"]) / b["dur"]))


def x_off(t):
    return T_at(t) * V * PPM


# ---------------------------------------------------------------- géométrie
FLOOR0 = 1100                 # plancher du salon (4,9 m au-dessus de la route)
ROAD_F = FLOOR0 + CHUTE * PPM # atterrissage : 1590
SIDE = 1500                   # bas des façades
WALL_X = 1960                 # mur est, dans le repère de l'immeuble
KG = .56                      # échelle du salon
OX = 540                      # écran <- local 620
SHOP_END = WALL_X + 60


def loc(x, y, floor=FLOOR0):
    return OX + (x - 640) * KG, floor + (y - 1495) * KG


# ---------------------------------------------------------------- meubles
def d_frigo(c):
    shape(c, rrect(-95, -420, 95, 0, 22), "#F2F2F7", 7)
    c.drawLine(-95, -270, 95, -270, line(INK, 6))
    for a, b in ((-340, -292), (-240, -150)):
        c.drawLine(-68, a, -68, b, line("#8A8FA0", 11))
    shape(c, rrect(10, -240, 72, -170, 3), "#FFE14D", 4)
    c.drawLine(20, -218, 62, -218, line(INK, 3))
    c.drawLine(20, -196, 54, -196, line(INK, 3))


def d_tele(c):
    shape(c, rrect(-90, -120, 90, 0, 8), "#7B4A2B", 6)
    shape(c, rrect(-30, -160, 30, -120, 6), "#3A3A48", 6)
    shape(c, rrect(-150, -340, 150, -156, 12), "#20202B", 7)
    c.drawRect(skia.Rect.MakeLTRB(-136, -326, 136, -170), fill("#3F6FD8"))
    c.drawCircle(0, -248, 40, fill("#FFFFFF", .22))
    c.drawPath(poly([(-14, -272), (-14, -224), (24, -248)]), fill("#FFFFFF", .75))


def d_lampe(c):
    c.drawLine(0, -600, 0, -10, line(INK, 12))
    c.drawLine(0, -600, 0, -10, line("#B8BCC8", 6))
    shape(c, oval(-52, -20, 52, 8), "#3A3A48", 6)
    shape(c, poly([(-40, -700), (40, -700), (84, -570), (-84, -570)]), "#FFD98A", 7)


def d_gamelle(c):
    shape(c, poly([(-62, -46), (62, -46), (82, 0), (-82, 0)]), "#D9534F", 6)
    c.drawOval(skia.Rect.MakeLTRB(-60, -58, 60, -34), fill("#7B4A2B"))
    c.drawOval(skia.Rect.MakeLTRB(-60, -58, 60, -34), line(INK, 5))


def d_bus(c):
    shape(c, rrect(-235, -170, 235, -26, 22), "#3FA58E", 7)
    for x in range(-210, 200, 78):
        shape(c, rrect(x, -148, x + 62, -92, 6), "#CDEBFF", 4)
    c.drawRect(skia.Rect.MakeLTRB(-233, -74, 233, -60), fill("#FFFFFF"))
    for wx in (-150, 150):
        c.drawCircle(wx, -24, 26, fill(INK))
        c.drawCircle(wx, -24, 11, fill("#B8BCC8"))


def paw(c, x0, y0, x1, y1, s=1.0):
    p = skia.Path()
    p.moveTo(x0, y0)
    p.quadTo((x0 + x1) / 2, (y0 + y1) / 2 - 18 * s, x1, y1)
    c.drawPath(p, line(INK, 54 * s))
    c.drawPath(p, line("#F49A3A", 38 * s))
    shape(c, oval(x1 - 31 * s, y1 - 27 * s, x1 + 31 * s, y1 + 27 * s), "#FFE1B0", 5 * s)
    for dy in (-7, 7):
        c.drawLine(x1 + 8 * s, y1 + dy * s, x1 + 20 * s, y1 + dy * s, line(INK, 3 * s))


def group(c, t, floor, stage=0, sip=0.0, gerard=True, cat=False, cat_mood="bliss", float_=0.0):
    """Le salon en ordre : tapis, lampe, canapé, Gérard, frigo, télé, gamelle (repère de draw_couch)."""
    c.save()
    c.translate(OX, floor)
    c.scale(KG, KG)
    c.translate(-640, -1495)
    bo = lambda i: math.sin(t * 2.0 + i * 1.7) * float_
    shape(c, oval(20, 1490, 1120, 1560), "#D9534F", 6)
    c.drawOval(skia.Rect.MakeLTRB(90, 1505, 1050, 1545), line("#F7DDAE", 6))
    c.save(); c.translate(60, 1510 + bo(2)); d_lampe(c); c.restore()
    c.save(); c.translate(1200, 1500 + bo(3)); d_frigo(c); c.restore()
    c.save(); c.translate(1430, 1500 + bo(4)); c.scale(.75, .75); d_tele(c); c.restore()
    c.save(); c.translate(0, bo(0))
    draw_couch(c)
    if gerard:
        draw_gerard(c, stage, t)
        # bras + café
        hx, hy = lerp(640, 720, sip), lerp(1190, 1050, sip)
        arm = skia.Path()
        arm.moveTo(712, 1170)
        arm.quadTo(650, 1230, hx, hy)
        c.drawPath(arm, line(INK, 60))
        c.drawPath(arm, line("#3F6FD8", 46))
        h_ = skia.Path()
        h_.addOval(skia.Rect.MakeLTRB(hx - 74, hy - 40, hx - 40, hy - 4))
        c.drawPath(h_, line(INK, 12))
        c.drawPath(h_, line("#FFFFFF", 5))
        shape(c, rrect(hx - 44, hy - 62, hx + 34, hy + 18, 10), "#FFFFFF", 6)
        c.drawOval(skia.Rect.MakeLTRB(hx - 40, hy - 68, hx + 30, hy - 54), fill("#5A3A22"))
        c.drawOval(skia.Rect.MakeLTRB(hx - 40, hy - 68, hx + 30, hy - 54), line(INK, 4))
        for i in range(2):
            ph = (t * .7 + i * .5) % 1
            c.drawCircle(hx - 12 + i * 22 + math.sin(t * 3 + i) * 8, hy - 92 - ph * 80, 8 + ph * 8, fill("#FFFFFF", .5 * (1 - ph)))
    if cat:
        draw_cat(c, 340, 1312, 1.0, t, cat_mood, 0)
    c.restore()
    c.save(); c.translate(210, 1548 + bo(5)); c.scale(.9, .9); d_gamelle(c); c.restore()
    c.restore()


def ger_bubble(c, t, b, floor, dx=0):
    if not b["ger"]:
        return
    s_ = back((t - b["start"]) / .16)
    hx, hy = loc(790, 900, floor)
    f = skia.Font(TF, 46)
    w = f.measureText(b["ger"])
    xx = clamp(hx + dx - 60, w / 2 + 44, W - w / 2 - 44)
    bubble(c, xx, hy - 74, b["ger"], 46, s_, 2)


# ---------------------------------------------------------------- l'immeuble de Gérard (coupe)
def curtain(c, x, f, t):
    """Rideau accroché en haut (x, 716). f=0 : pend. f=1 : à l'horizontale, vers l'est."""
    ln = 370
    p = skia.Path()
    wd = 64
    pts_a, pts_b = [], []
    for i in range(13):
        u = i / 12
        ang = lerp(math.pi / 2, .06, f)
        wob = math.sin(u * 7 + t * (3 + 40 * f)) * (5 + 18 * f) * u
        xx = x + math.cos(ang) * ln * u + wob * math.sin(ang)
        yy = 716 + math.sin(ang) * ln * u + wob * math.cos(ang)
        pts_a.append((xx - math.sin(ang) * wd / 2, yy + math.cos(ang) * wd / 2 * (1 - f) - f * wd * .0))
        pts_b.append((xx + math.sin(ang) * wd / 2, yy + f * wd * .9))
    return poly(pts_a + pts_b[::-1])


def michel_curtain(c, t, xo, f):
    """Michel suspendu. f=0 : assis contre le rideau. f=1 : drapeau."""
    x0 = 100 - xo
    p = curtain(c, x0, f, t)
    shape(c, p, "#C0443E", 6)
    # position de la prise de Michel sur le rideau
    ang = lerp(math.pi / 2, .06, f)
    gx, gy = x0 + math.cos(ang) * 300, 716 + math.sin(ang) * 300 + f * 26
    if f > .5:
        k = .42
        c.save()
        c.translate(gx + 48 + 8 * math.sin(t * 40), gy + 8 * math.sin(t * 31))
        c.rotate(-90)
        draw_cat(c, 0, 0 + 370 * k + 60 * k, k, t, "open", 0)
        c.restore()
        for dy in (-44, 42):
            paw(c, gx + 90, gy + dy, gx - 8, gy + dy * .45, .26)
    else:
        k = .38
        draw_cat(c, gx + 8, gy + 70, k, t, "bliss" if f < 0 else "open", 0)
        for sgn in (-1, 1):
            paw(c, gx + 8 + sgn * 26, gy + 20, gx + 8 + sgn * 36, gy - 92, .22)


def building(c, xo, t, broken=False, tag_button=None):
    """Tout ce qui est vissé : mur du fond, fenêtre, plancher, commerce du bas."""
    c.save()
    c.translate(-xo, 0)
    # rez-de-chaussée (commerce)
    c.drawRect(skia.Rect.MakeLTRB(-240, FLOOR0, SHOP_END, ROAD_F - 80), fill("#D0C3A5"))
    for x in range(90, SHOP_END - 200, 520):
        shape(c, rrect(x, FLOOR0 + 120, x + 400, ROAD_F - 100, 8), "#CDEBFF", 7)
        for i in range(6):
            c.drawRect(skia.Rect.MakeLTRB(x + i * 66, FLOOR0 + 60, x + i * 66 + 66, FLOOR0 + 118), fill("#3F6FD8" if i % 2 else "#FFFFFF"))
        c.drawLine(x, FLOOR0 + 118, x + 400, FLOOR0 + 118, line(INK, 6))
    # mur du salon
    c.drawRect(skia.Rect.MakeLTRB(-240, 0, WALL_X, FLOOR0), fill("#F7DDAE"))
    for x in range(-240, WALL_X, 120):
        c.drawRect(skia.Rect.MakeLTRB(x, 0, x + 60, FLOOR0), fill("#F2D29C", .55))
    c.drawRect(skia.Rect.MakeLTRB(-240, FLOOR0 - 34, WALL_X, FLOOR0), fill("#FFF5E0"))
    # fenêtre (moitié gauche, derrière le rideau)
    win = skia.Rect.MakeLTRB(60, 700, 320, 1030)
    c.drawRect(win, fill("#9BDCFA"))
    c.drawRect(win, line(INK, 24))
    c.drawRect(win, line("#FFFFFF", 16))
    c.drawLine(190, 700, 190, 1030, line("#FFFFFF", 11))
    c.drawLine(60, 860, 320, 860, line("#FFFFFF", 11))
    c.drawLine(40, 714, 340, 714, line(INK, 14))
    c.drawLine(40, 714, 340, 714, line("#B8BCC8", 7))
    # tableau + deuxième fenêtre, pour le défilement
    for wx in (760, 1280):
        win2 = skia.Rect.MakeLTRB(wx, 700, wx + 240, 1030)
        c.drawRect(win2, fill("#9BDCFA"))
        c.drawRect(win2, line(INK, 22))
        c.drawRect(win2, line("#FFFFFF", 14))
        c.drawLine(wx + 120, 700, wx + 120, 1030, line("#FFFFFF", 10))
    # plancher
    shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(-260, FLOOR0, SHOP_END, FLOOR0 + 26)), "#7B4A2B", 7)
    # mur est
    top = FLOOR0 if not broken else 650
    shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(WALL_X, 0, SHOP_END, top)), "#D0C3A5", 8)
    shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(WALL_X, FLOOR0 + 26, SHOP_END, ROAD_F - 80)), "#D0C3A5", 8)
    if broken:
        for i in range(7):
            c.drawPath(poly([(WALL_X + i * 8, 650), (WALL_X + i * 8 + 12, 650 + 28 + (i % 3) * 22), (WALL_X + i * 8 + 24, 650)]), fill("#D0C3A5"))
    c.restore()


# ---------------------------------------------------------------- la rue
_r = random.Random(11)
FAC = []
_x = 800
while _x < 19000:
    w = _r.uniform(250, 430)
    h_ = _r.uniform(690, 920)
    cc = _r.choice(("#E8D9B8", "#DCCBA6", "#EFE3C8", "#D6C39A"))
    FAC.append((_x, w, h_, cc, _r.random()))
    _x += w
TREES = [SHOP_END + 720 + i * 2150 for i in range(16)]
LAMPS = [SHOP_END + 1700 + i * 2150 for i in range(16)]


def bg_street(c, t, xo):
    sky = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 0), (0, SIDE)], [col("#5CB8F2"), col("#D3F1FF")]))
    c.drawRect(skia.Rect.MakeWH(W, H), sky)
    c.drawCircle(860, 200, 58, fill("#FFF3B5"))
    # façades (parallaxe .5)
    xf = xo * .5
    for (x, w, h_, cc, rnd) in FAC:
        l = x - xf
        if l > W + 10 or l + w < -10:
            continue
        top = SIDE - h_
        shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(l, top, l + w, SIDE)), cc, 5)
        shape(c, poly([(l - 10, top), (l + 16, top - 80), (l + w - 16, top - 80), (l + w + 10, top)]), "#6E7486", 5)
        nx = int((w - 30) // 78)
        for iy in range(int((h_ - 170) // 134)):
            yy = top + 36 + iy * 134
            for ix in range(nx):
                xx = l + 22 + ix * 78
                c.drawRect(skia.Rect.MakeLTRB(xx, yy, xx + 46, yy + 84), fill("#3A4A66"))
                c.drawRect(skia.Rect.MakeLTRB(xx, yy, xx + 46, yy + 84), line(INK, 3))
            c.drawLine(l + 12, yy + 92, l + w - 12, yy + 92, line(INK, 5))
    # trottoir + route
    c.drawRect(skia.Rect.MakeLTRB(0, SIDE, W, SIDE + 40), fill("#B9BCC8"))
    c.drawRect(skia.Rect.MakeLTRB(0, SIDE + 40, W, H), fill("#5E616F"))
    c.drawRect(skia.Rect.MakeLTRB(0, SIDE + 36, W, SIDE + 44), fill(INK))
    off = xo % 300
    for x in range(-300, W + 300, 300):
        c.drawRect(skia.Rect.MakeLTRB(x - off, ROAD_F + 74, x - off + 160, ROAD_F + 90), fill("#F4E9B8"))


def windy(t):
    T = T_at(t)
    b = beat_at(t)
    if b["T1"] is None or T <= 0:
        return 0.0
    if T >= 1:
        return math.exp(-(t - K["repart"]) * 3) * math.cos((t - K["repart"]) * 16)
    return 1.0


def near_props(c, t, xo):
    wnd = windy(t)
    for x in TREES:
        l = x - xo
        if -420 < l < W + 420:
            c.drawLine(l, SIDE + 20, l, SIDE - 240, line(INK, 42))
            c.drawLine(l, SIDE + 20, l, SIDE - 240, line("#7B4A2B", 28))
            bx = l + 160 * wnd
            by = SIDE - 330 + 90 * abs(wnd)
            for dx, dy, r in ((-74, 10, 88), (0, -44, 106), (78, 12, 86), (0, 40, 76)):
                ccx = bx + dx * (1 + .25 * wnd)
                c.drawCircle(ccx, by + dy, r, line(INK, 10))
            for dx, dy, r in ((-74, 10, 88), (0, -44, 106), (78, 12, 86), (0, 40, 76)):
                ccx = bx + dx * (1 + .25 * wnd)
                c.drawCircle(ccx, by + dy, r, fill("#4FAE68"))
    for x in LAMPS:
        l = x - xo
        if -200 < l < W + 200:
            c.drawLine(l, SIDE + 20, l + 60 * wnd, SIDE - 470, line(INK, 16))
            c.drawLine(l, SIDE + 20, l + 60 * wnd, SIDE - 470, line("#3A3A48", 8))
            shape(c, oval(l + 60 * wnd - 30, SIDE - 520, l + 60 * wnd + 30, SIDE - 460), "#FFE9A8", 6)


def rush(c, t):
    """Stries de vitesse et feuilles, qui voyagent avec Gérard."""
    r = random.Random(3)
    for i in range(22):
        y = r.uniform(620, 1480)
        sp = r.uniform(1100, 2200)
        ln = r.uniform(120, 360)
        x = W + 200 - ((t * sp + r.uniform(0, 2000)) % (W + 600))
        c.drawLine(x, y, x + ln, y, line("#FFFFFF", 5, .45))
    for i in range(16):
        x0, y0 = r.uniform(30, 1050), r.uniform(650, 1450)
        c.save()
        c.translate(x0 + math.sin(t * 1.3 + i) * 34, y0 + math.cos(t * 1.1 + i) * 24)
        c.rotate(t * 90 + i * 50)
        c.drawOval(skia.Rect.MakeLTRB(-16, -8, 16, 8), fill("#4FAE68"))
        c.drawOval(skia.Rect.MakeLTRB(-16, -8, 16, 8), line(INK, 3))
        c.restore()


def burst(c, x, y, d_, colors, n=26, spread=380, up=620, size=14, seed=1, floor=None, g=1700):
    if d_ < 0:
        return
    r = random.Random(seed)
    fl = floor if floor is not None else y
    for i in range(n):
        vx, vy = r.uniform(-spread, spread), -r.uniform(up * .25, up)
        sz = r.uniform(size * .45, size)
        rot0, w = r.uniform(0, 360), r.uniform(-500, 500)
        tl_ = (-vy + math.sqrt(max(vy * vy + 2 * g * (fl - y), 0))) / g
        tt = min(d_, tl_)
        c.save()
        c.translate(x + vx * tt, y + vy * tt + .5 * g * tt * tt)
        c.rotate(rot0 + w * tt)
        c.drawRect(skia.Rect.MakeLTRB(-sz, -sz * .6, sz, sz * .6), fill(colors[i % len(colors)]))
        c.drawRect(skia.Rect.MakeLTRB(-sz, -sz * .6, sz, sz * .6), line(INK, 3))
        c.restore()


T_BREACH = (WALL_X - 1060) / (V * PPM)
_mb = next(b for b in BEATS if b["key"] == "mur")
T_BREACH_V = _mb["start"] + _mb["dur"] * (T_BREACH - _mb["T0"]) / (_mb["T1"] - _mb["T0"])


def scene_salon(c, t, b):
    key = b["key"]
    bg_street(c, t, 0)
    building(c, 0, t)
    sip = 0
    if key in ("hook", "tout"):
        sip = clamp(math.sin((t - b["start"]) * 1.2)) * .9
    if key == "cafe":
        sip = eout((t - b["start"]) / .5)
    # rideau + Michel
    jumped = key in ("rideaux", "cafe")
    if jumped:
        d_ = t - K["rideaux"]
        f = clamp((d_ - .3) / .45)
        p = curtain(c, 100, 0, t)
        shape(c, p, "#C0443E", 6)
        group(c, t, FLOOR0, 0, sip, True, False)
        x0, y0 = loc(340, 1312)
        gx, gy = 108, 1086
        sx = lerp(x0, gx, eout(f))
        sy = lerp(y0, gy, f) - math.sin(f * math.pi) * 230
        if f < 1:
            draw_cat(c, sx, sy, lerp(.5, .38, f), t, "open", 0)
        else:
            michel_curtain(c, t, 0, 0.001)
    else:
        p = curtain(c, 100, 0, t)
        shape(c, p, "#C0443E", 6)
        group(c, t, FLOOR0, 1 if key == "regarde" else 0, sip, True, True, "open" if key == "regarde" else "bliss")
    if key == "tout":
        # étiquettes
        d_ = t - b["start"]
        for i, (lx, ly, lab) in enumerate(((560, 1120, "1 100 km/h"), (1230, 1000, "1 100 km/h"), (790, 830, "1 100 km/h"))):
            if d_ > .25 + i * .5:
                sx, sy = loc(lx, ly)
                bubble(c, sx, sy - 40 + (0 if i else 90), lab, 34, back((d_ - .25 - i * .5) / .16), (-1) ** i * 3, tail=False, color="#FFE14D")
    if key == "regarde":
        # petit point d'interrogation, Michel regarde en l'air
        d_ = t - b["start"]
        text(c, "?", 420, 760 - eout(d_ / .4) * 30, 90, "#FFFFFF", INK, 12)
    ger_bubble(c, t, b, FLOOR0)


def scene_globe(c, t, b):
    bgim = STARS
    c.drawImage(bgim, 0, 0)
    art.LON0 = math.radians(16 - (t - b["start"]) * 7)
    R = 400
    im, x0, y0 = earth_rgba(R, 0, 0, None, 1.0, 540, 1120)
    c.drawImage(im, x0, y0)
    px, py, cosc = art.project(48.85, 2.35, R)
    px, py = px - art.EX + 540, py - art.EY + 1120
    c.drawCircle(px, py, 14, fill("#FFE14D"))
    c.drawCircle(px, py, 14, line(INK, 5))
    ln = 150 * (1 + .06 * math.sin(t * 6))
    c.drawLine(px, py - 18, px + ln, py - 18, line(INK, 18))
    c.drawLine(px, py - 18, px + ln, py - 18, line("#FFE14D", 10))
    c.drawPath(poly([(px + ln - 8, py - 44), (px + ln + 40, py - 18), (px + ln - 8, py + 8)]), fill("#FFE14D"))
    c.drawPath(poly([(px + ln - 8, py - 44), (px + ln + 40, py - 18), (px + ln - 8, py + 8)]), line(INK, 5))
    text(c, "PARIS", px - 4, py - 58, 50, "#FFFFFF", INK, 10)


def flag_f(t):
    T = T_at(t)
    if t < K["stop"]:
        return 0
    if T >= 1:
        return 0
    return eout((t - K["stop"]) / .3)


def scene_vol(c, t, b):
    key = b["key"]
    T = T_at(t)
    xo = x_off(t)
    if key == "flag":
        # caméra fixée sur l'immeuble : le salon s'éloigne
        bg_street(c, t, 0)
        building(c, 0, t)
        c.drawRect(skia.Rect.MakeLTRB(0, 0, W, FLOOR0), fill("#FFFFFF", .05))
        michel_curtain(c, t, 0, flag_f(t))
        # le salon sort du cadre, à droite
        c.save()
        c.translate(xo, 0)
        group(c, t, FLOOR0, 0, .9, True, False)
        c.restore()
        # stries dans la pièce
        r = random.Random(8)
        for i in range(10):
            y = r.uniform(680, 1050)
            x = ((t * r.uniform(900, 1500) + r.uniform(0, 1200)) % (W + 300)) - 200
            c.drawLine(x, y, x + r.uniform(70, 170), y, line("#FFFFFF", 4, .6))
        return
    floor = min(FLOOR0 + CHUTE * PPM * T * T, ROAD_F)
    bg_street(c, t, xo)
    near_props(c, t, xo)
    if xo < SHOP_END + 40:
        building(c, xo, t, broken=t >= T_BREACH_V)
        if key in ("stop", "reste") and T < .02:
            michel_curtain(c, t, xo, flag_f(t))
    if 0 < T < 1 and key not in ("stop", "reste"):
        rush(c, t)
    # bus (derrière le salon)
    if t >= K["bus"]:
        e = eout((t - K["bus"]) / 1.1)
        bx = lerp(1420, 780, e)
        bob = 0
        if T >= 1:
            bob = math.exp(-(t - K["repart"]) * 5) * 18
        c.save()
        c.translate(bx, SIDE + 34 + bob)
        c.scale(.86, .86)
        d_bus(c)
        c.restore()
    sip = .9 if key in ("stop", "reste", "mur", "fin1") else clamp(math.sin((t - b["start"]) * 1.4)) * .9
    if key == "repart":
        sip = 0
    if key == "intact":
        sip = eout((t - b["start"] - .5) / .5)
    # impact final
    g_y = floor
    if T >= 1:
        d_ = t - K["repart"]
        if d_ < .25:
            g_y = ROAD_F - 22 * math.sin(d_ / .25 * math.pi)
    stage = 1 if key in ("sent", "bus", "tombe") else 0
    if key in ("repart", "intact"):
        stage = 2 if key == "repart" else 0
    group(c, t, g_y, stage, sip, True, False, float_=4.0 if 0 < T < 1 else 0)
    if key == "mur":
        burst(c, 1060, 880, t - T_BREACH_V, ("#D0C3A5", "#B79E7A", "#F7DDAE"), 48, 420, 560, 26, seed=5, floor=1100)
    ger_bubble(c, t, b, g_y)
    if key == "repart":
        for i in range(10):
            d_ = t - K["repart"]
            r = random.Random(i + 40)
            x0 = r.uniform(120, 960)
            c.drawCircle(x0 + r.uniform(-110, 110) * d_, ROAD_F + 24 - d_ * 80, r.uniform(14, 42) * (1 + d_), fill("#8E8A90", .45 * clamp(1 - d_ * 1.2)))
    if key == "stop":
        d_ = t - K["stop"]
        if d_ < .9:
            c.save()
            c.translate(540, 1000)
            s_ = back(d_ / .15) * (1 + .15 * clamp(d_ - .3))
            c.scale(s_, s_)
            text(c, "STOP", 0, 60, 220, "#FF2E2E", "#FFFFFF", 22, a=clamp((.9 - d_) / .25))
            c.restore()


def bear(c, x, y, s, t):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    W_ = "#F7F7FA"
    shape(c, oval(-170, -280, 170, 20), W_, 8)
    shape(c, oval(-90, -60, -10, 30), W_, 6)
    shape(c, oval(10, -60, 90, 30), W_, 6)
    hy = -330 + math.sin(t * 1.1) * 4
    for sg in (-1, 1):
        shape(c, oval(sg * 84 - 34, hy - 120, sg * 84 + 34, hy - 52), W_, 7)
    shape(c, oval(-124, hy - 108, 124, hy + 96), W_, 8)
    blink = (t % 2.1) < .14
    for sg in (-1, 1):
        if blink:
            c.drawLine(sg * 52 - 13, hy - 18, sg * 52 + 13, hy - 18, line(INK, 7))
        else:
            c.drawCircle(sg * 52, hy - 18, 11, fill(INK))
    c.drawOval(skia.Rect.MakeLTRB(-46, hy + 6, 46, hy + 70), fill("#E9E3D6"))
    c.drawPath(poly([(-17, hy + 16), (17, hy + 16), (0, hy + 34)]), fill(INK))
    c.drawLine(0, hy + 34, 0, hy + 50, line(INK, 5))
    c.restore()


def scene_pole(c, t, b):
    sky = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 0), (0, 1350)], [col("#7EC2EE"), col("#E8F7FF")]))
    c.drawRect(skia.Rect.MakeWH(W, H), sky)
    shape(c, poly([(-20, 1320), (200, 1090), (340, 1210), (500, 1050), (760, 1270), (900, 1140), (1100, 1320)]), "#D6ECF8", 6)
    c.drawRect(skia.Rect.MakeLTRB(0, 1300, W, H), fill("#F2FAFF"))
    c.drawLine(0, 1300, W, 1300, line(INK, 6))
    # piquet du pôle
    c.drawLine(840, 1500, 840, 1090, line(INK, 18))
    c.drawLine(840, 1500, 840, 1090, line("#E04A3A", 10))
    shape(c, oval(806, 1050, 874, 1118), "#FFFFFF", 7)
    text(c, "PÔLE NORD", 840, 1010, 44, "#FFFFFF", INK, 9)
    bear(c, 390, 1500, 1.15, t)
    r = random.Random(4)
    for i in range(50):
        x, sp, ph = r.uniform(0, W), r.uniform(50, 110), r.uniform(0, 1400)
        c.drawCircle(x + math.sin(t + i) * 14, 600 + ((t * sp + ph) % 1100), r.uniform(4, 9), fill("#FFFFFF", .9))


COCOS = [(120, 1640), (250, 1560), (390, 1660), (520, 1570), (660, 1650), (800, 1560), (70, 1540), (950, 1640)]


def scene_equa(c, t, b):
    sky = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 0), (0, 1300)], [col("#2FA8EC"), col("#BFF0FF")]))
    c.drawRect(skia.Rect.MakeWH(W, H), sky)
    c.drawCircle(850, 720, 80, fill("#FFF3B5"))
    c.drawRect(skia.Rect.MakeLTRB(0, 1230, W, 1420), fill("#2B86DE"))
    d_ = t - b["start"]
    for yy in (1275, 1335, 1390):
        for x in range(-200 + int(d_ * 500) % 200, W, 200):
            c.drawLine(x, yy, x + 90, yy, line("#7EC8FF", 6))
    c.drawRect(skia.Rect.MakeLTRB(0, 1420, W, H), fill("#F3D88F"))
    c.drawLine(0, 1420, W, 1420, line(INK, 6))
    # cocotier, vissé au sol, qui se couche
    bend = 170 * eout(d_ / .4)
    p = skia.Path()
    p.moveTo(250, 1530)
    p.quadTo(230, 1200, 250 + bend, 930)
    c.drawPath(p, line(INK, 50))
    c.drawPath(p, line("#9B6A3C", 36))
    for an in (-20, 10, 40, 70, 105, 150):
        r_ = math.radians(an + bend * .12)
        ex, ey = 250 + bend + math.cos(r_) * 240, 930 + math.sin(r_) * 120 - 30
        q = skia.Path()
        q.moveTo(250 + bend, 930)
        q.quadTo((250 + bend + ex) / 2, 900, ex, ey)
        c.drawPath(q, line(INK, 30))
        c.drawPath(q, line("#3E9E5A", 20))
    # cocos : à l'équateur, ça part fort
    r = random.Random(6)
    for i, (x, y) in enumerate(COCOS):
        sp = 250 + i * 25
        xx = x + max(0, d_ - .08 * i) * sp
        spin = d_ * 400
        c.save()
        c.translate(xx, y)
        c.rotate(spin)
        shape(c, oval(-38, -38, 38, 38), "#6B4324", 6)
        c.drawCircle(-10, -10, 5, fill(INK))
        c.drawCircle(10, -10, 5, fill(INK))
        c.restore()
    for i in range(24):
        y = r.uniform(1450, 1880)
        x = ((d_ * r.uniform(900, 1500) + r.uniform(0, 1100)) % (W + 300)) - 150
        c.drawLine(x, y, x + r.uniform(30, 90), y, line("#D8B86C", 5))


def scene_iss(c, t, b):
    c.drawImage(STARS, 0, 0)
    art.LON0 = math.radians(2.35)
    im, x0, y0 = earth_rgba(1100, 0, 0, None, 1.0, 540, 2300)
    c.drawImage(im, x0, y0)
    d_ = t - b["start"]
    draw_iss(c, 540, 930 + math.sin(t) * 8, 2.5, -8 + d_ * 1.2)
    bubble(c, 790, 780, "Tiens ?", 50, back((d_ - .9) / .16), 3)


def scene_seine(c, t, b):
    sky = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 0), (0, 1400)], [col("#6FC6F5"), col("#EAF8FF")]))
    c.drawRect(skia.Rect.MakeWH(W, H), sky)
    d_ = t - b["start"]
    # quais et immeubles au loin
    c.drawRect(skia.Rect.MakeLTRB(0, 1000, W, 1200), fill("#C9BDA3"))
    r = random.Random(7)
    x = -30
    while x < W:
        w, h_ = r.uniform(120, 200), r.uniform(220, 360)
        shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(x, 1000 - h_, x + w, 1000)), r.choice(("#E8D9B8", "#DCCBA6", "#EFE3C8")), 5)
        x += w
    # pont de pierre
    shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(620, 1040, 1100, 1120)), "#B9AE9A", 7)
    for ax in (700, 890):
        shape(c, oval(ax - 90, 1120, ax + 90, 1500), "#8F8676", 6)
    # l'eau : elle monte contre le pont
    wall_x = 620
    rise = 260 * eout(d_ / 1.2)
    p = skia.Path()
    p.moveTo(-10, H + 10)
    p.lineTo(-10, 1380)
    for xx in range(-10, W + 20, 30):
        ys = 1380 - rise * clamp(xx / wall_x) ** 2 + math.sin(xx * .03 + t * 7) * 12
        if xx > wall_x:
            ys = 1380 - rise * .45 + math.sin(xx * .03 + t * 7) * 12
        p.lineTo(xx, ys)
    p.lineTo(W + 20, H + 10)
    p.close()
    c.drawPath(p, fill("#2B86DE", .95))
    c.drawPath(p, line(INK, 6))
    # péniche emportée
    bx = lerp(140, 520, eout(d_ / 2.0))
    by = 1380 - rise * clamp(bx / wall_x) ** 2
    c.save()
    c.translate(bx, by - 8)
    c.rotate(-6 * eout(d_ / 2.0))
    shape(c, poly([(-160, -46), (160, -46), (130, 30), (-130, 30)]), "#5A3A22", 6)
    shape(c, rrect(-60, -102, 70, -46, 8), "#E9E3D6", 6)
    c.restore()
    # flèche du courant
    c.drawLine(120, 1640, 840, 1640, line(INK, 26))
    c.drawLine(120, 1640, 840, 1640, line("#FFE14D", 16))
    c.drawPath(poly([(830, 1600), (920, 1640), (830, 1680)]), fill("#FFE14D"))
    c.drawPath(poly([(830, 1600), (920, 1640), (830, 1680)]), line(INK, 5))


def scene_soleil(c, t, b):
    c.drawImage(STARS, 0, 0)
    d_ = t - b["start"]
    sun_face(c, 300, 1100, 250, t, True)
    art.LON0 = math.radians(2.35)
    im, x0, y0 = earth_rgba(120, 0, 0, None, 1.0, 830, 1100)
    c.drawImage(im, x0, y0)
    text(c, "la Terre", 830, 1270, 42, "#FFFFFF", INK, 8)
    text(c, "le Soleil", 300, 1420, 42, "#FFFFFF", INK, 8)
    # chrono : 9 minutes
    x0, wd = 170, 740
    shape(c, rrect(x0, 1510, x0 + wd, 1560, 18), "#14121C", 6)
    pr = eout(d_ / 1.8)
    if pr > .01:
        c.drawPath(rrect(x0 + 8, 1518, x0 + 8 + (wd - 16) * pr, 1552, 12), fill("#FFC531"))
    text(c, "%d min" % round(pr * 9), 540, 1630, 70, "#FFE14D", INK, 11)


def scene_tour(c, t, b):
    sky = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 0), (0, 1400)], [col("#5CB8F2"), col("#D3F1FF")]))
    c.drawRect(skia.Rect.MakeWH(W, H), sky)
    c.drawRect(skia.Rect.MakeLTRB(0, 1350, W, H), fill("#5E616F"))
    c.drawLine(0, 1350, W, 1350, line(INK, 7))
    PX = 2.75
    x0 = 70
    c.save()
    c.translate(x0, 1040)
    c.rotate(90)
    draw_eiffel(c, TOUR * PX)
    c.restore()
    # règle au sol
    T = T_at(t)
    xg = x0 + V * T * PX
    c.drawLine(x0, 1430, x0 + TOUR * PX, 1430, line("#FFFFFF", 7))
    for xx, lab in ((x0, "0"), (x0 + TOUR * PX, "330 m")):
        c.drawLine(xx, 1410, xx, 1450, line("#FFFFFF", 7))
        text(c, lab, clamp(xx, 70, 930), 1505, 46, "#FFFFFF", INK, 8)
    c.drawLine(x0, 1430, xg, 1430, line("#FFE14D", 13))
    # le salon, tout petit
    c.save()
    c.translate(xg, 1400)
    c.scale(.14, .14)
    c.translate(-620, -1495)
    draw_couch(c)
    draw_gerard(c, 0, t)
    c.restore()
    text(c, "GÉRARD", clamp(xg, 130, 940), 1305, 44, "#FFE14D", INK, 9)
    c.drawLine(clamp(xg, 130, 940), 1312, xg, 1330, line(INK, 8))


def scene_marche(c, t, b):
    d_ = t - b["start"]
    xo = x_off(t) * (1 - d_ / b["dur"] * .22)
    bg_street(c, t, xo)
    near_props(c, t, xo)
    bob = abs(math.sin(t * 7)) * 18
    c.save()
    c.translate(600, ROAD_F - 2 - bob)
    c.scale(.62, .62)
    c.translate(-790, -1498)
    draw_gerard(c, 1, t, False, 0, True)
    c.restore()
    # gamelle sous le bras
    c.save()
    c.translate(535, ROAD_F - 175 - bob)
    c.scale(.7, .7)
    d_gamelle(c)
    c.restore()
    # Horloge qui file
    shape(c, oval(880, 640, 1040, 800), "#FFFFFF", 7)
    a = d_ * 12
    c.drawLine(960, 720, 960 + 62 * math.sin(a), 720 - 62 * math.cos(a), line(INK, 7))
    c.drawCircle(960, 720, 8, fill(INK))


def scene_fin(c, t, b):
    key = b["key"]
    bg_street(c, t, 0)
    building(c, 0, t, True)
    # traces sur le mur : là où étaient les meubles
    c.drawPath(rrect(*loc(1105, 1075)[:2], *loc(1295, 1495)[:2], 10), line("#D9B98A", 5))
    c.drawPath(rrect(*loc(1320, 1240)[:2], *loc(1545, 1495)[:2], 10), line("#D9B98A", 5))
    c.drawPath(rrect(*loc(100, 1085)[:2], *loc(1040, 1440)[:2], 40), line("#D9B98A", 5))
    bout = key in ("bouton", "patte")
    # le bouton, caché derrière le rideau
    bx, by = 104, 870
    press = eout((t - K["patte"] - 1.6) / .3) if key == "patte" else 0
    shape(c, rrect(bx - 70, by - 86, bx + 70, by + 64, 14), "#E9E3D6", 6)
    shape(c, oval(bx - 42, by - 60 + press * 8, bx + 42, by + 24 + press * 8), "#E0202B", 7)
    text(c, "TERRE", bx, by + 52, 34, INK)
    # rideau + Michel
    d_ = t - b["start"]
    if bout:
        slide = -210 * eout((t - K["bouton"]) / .45)
    else:
        slide = 0
    c.save()
    c.translate(slide, 0)
    shape(c, curtain(c, 100, 0, t), "#C0443E", 6)
    c.restore()
    # Michel descendu du rideau, sur le rebord
    mx, my = 320, FLOOR0 - 4
    draw_cat(c, mx, my, .5, t, "bliss" if key == "vide" else "open", 0)
    if key == "patte":
        e = eout((t - K["patte"] - .25) / 1.3)
        paw(c, mx - 60, my - 120, lerp(mx - 60, bx + 26, e), lerp(my - 120, by - 18 + press * 8, e), .42)
        if t - K["patte"] > 1.0:
            bubble(c, mx + 80, my - 260, "mrrp ?", 54, back((t - K["patte"] - 1.0) / .16), -3)
    # Gérard revient
    if key in ("q", "bouton", "patte"):
        gx = lerp(1300, 820, eout((t - K["q"]) / .7))
        st = {"q": 1, "bouton": 2, "patte": 3}[key]
        c.save()
        c.translate(gx, FLOOR0 + 8)
        c.scale(.62, .62)
        c.translate(-790, -1498)
        draw_gerard(c, st, t, False, 0, True)
        c.restore()
        c.save()
        c.translate(gx - 90, FLOOR0 - 140)
        c.scale(.7, .7)
        d_gamelle(c)
        c.restore()
        if b["ger"]:
            f = skia.Font(TF, 46)
            w = f.measureText(b["ger"])
            xx = clamp(gx - 40, w / 2 + 44, W - w / 2 - 44)
            bubble(c, xx, FLOOR0 - 420, b["ger"], 46, back((t - b["start"]) / .16), 2)


# ---------------------------------------------------------------- HUD, légende, carton
def heat_c(T):
    stops = [(0, "#59E36A"), (.25, "#D7F03A"), (.5, "#FFC531"), (.75, "#FF7A1F"), (.95, "#FF2E2E"), (1, "#FF2EA6")]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if a <= T <= b:
            return hexmix(ca, cb, (T - a) / (b - a))
    return "#FF2EA6"


def fit(s, size, maxw):
    f = skia.Font(TF, size)
    while f.measureText(s) > maxw and size > 20:
        size -= 2
        f = skia.Font(TF, size)
    return size


def virg(x, n):
    return ("%.*f" % (n, x)).replace(".", ",")


def hud(c, t, b):
    T = T_at(t)
    if t < K["stop"]:
        colr, head, big, low = "#59E36A", "LA TERRE TOURNE", "1 100 km/h", "Vitesse de Paris. Personne ne le sent."
        pop = 1.0
    elif t < K["repart"]:
        colr = heat_c(T)
        n = 3 if T < .05 else 2
        head = "TERRE À L'ARRÊT · T + %s s" % virg(T, n)
        d = V * T
        big = "%d m" % round(d) if d >= 10 else "%s m" % virg(d, 1)
        low = "Gérard : encore 1 100 km/h"
        pop = 1 + .15 * (1 - eout((t - K["stop"]) / .22))
    else:
        colr, head, big, low = "#59E36A", "LA TERRE REPART", "307 m", "de chez lui"
        pop = 1 + .15 * (1 - eout((t - K["repart"]) / .22))
    if b["key"] in ("vide", "q", "bouton", "patte"):
        colr, head, big, low = "#59E36A", "LA TERRE TOURNE", "1 100 km/h", "Pour l'instant."
        pop = 1.0
    c.save()
    c.translate(540, 262)
    c.scale(pop, pop)
    pan = rrect(-420, -135, 420, 135, 44)
    c.drawPath(pan, fill("#14121C", .94))
    c.drawPath(pan, line(colr, 8))
    text(c, head, 0, -88, fit(head, 38, 770), "#C9C6D8")
    text(c, big, 0, 32, fit(big, 118, 780), colr)
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
    text(c, "DEUX SECONDES.", 0, 132, 100, "#FFD93B")
    c.restore()
    a = clamp((d_ - .5) / .25)
    text(c, "Très approximatif : arrêt instantané, murs en carton,", 540, 1140, 36, "#A9A6BC", a=a)
    text(c, "frottements oubliés. En vrai, ce serait bien pire.", 540, 1192, 36, "#A9A6BC", a=a)
    text(c, "Gérard va bien. Personne ne sait pourquoi.", 540, 1244, 36, "#A9A6BC", a=a)


SCN = dict(salon=scene_salon, globe=scene_globe, vol=scene_vol, pole=scene_pole, equa=scene_equa, iss=scene_iss, seine=scene_seine, soleil=scene_soleil, tour=scene_tour, marche=scene_marche, fin=scene_fin)


def shake_amp(t):
    amp = 0
    for tk, big in ((K["stop"], 26), (T_BREACH_V, 22), (K["repart"], 34), (K["patte"] + 1.9, 18)):
        d_ = t - tk
        if 0 <= d_ < .35:
            amp = max(amp, big * (1 - d_ / .35))
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
    # flash aux coupures de la seconde
    for tk in (K["stop"], K["repart"], K["marche"]):
        d_ = t - tk
        if 0 <= d_ < .14:
            c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", 1 - d_ / .14))
    hud(c, t, b)
    caption(c, t)


SPL = [("s_a", 0, K["stop"]), ("s_b", K["stop"], K["oeil"]), ("s_c", K["oeil"], K["pole"]), ("s_d", K["pole"], K["seine"]), ("s_e", K["seine"], K["tombe"]),
       ("s_f", K["tombe"], K["marche"]), ("s_g", K["marche"], CARD), ("s_h", CARD, END)]


def png(t, path):
    from PIL import Image
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    s = skia.Surface(arr)
    with s as c:
        frame(c, t)
    Image.fromarray(arr[..., :3]).save(path)


if __name__ == "__main__":
    print("durée %.1f s, carton %.1f, stop %.1f" % (END, CARD, K["stop"]))
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
