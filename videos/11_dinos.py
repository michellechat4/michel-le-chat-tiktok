"""Michel responsable de tout : il remonte le temps, deux fois plus loin à chaque saut, et pousse l'astéroïde des dinosaures."""
import math, random, sys, os, subprocess
import numpy as np
import skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "moteur"))
import art
from art import (fill, line, col, hexmix, poly, rrect, oval, shape, text, jitter, clamp, lerp, eout, ein, back,
                 draw_cat, draw_gerard, earth_rgba, STARS, bubble, wrap_rich, TF, INK, W, H, FPS)

# ---------------------------------------------------------------- chiffres (calculés, pas recopiés)
NOW = 2026
IMPACT = 66.0e6          # ans : impact de Chicxulub, ~66 millions d'années (NOAA, Science On a Sphere)
TREX = (68e6, 66e6)      # T. rex : 68 à 66 millions d'années (Natural History Museum, Londres)
PYRAMIDE = -2559         # grande pyramide achevée vers 2560 av. J.-C. (année astronomique -2559)
SAPIENS = 300e3          # Homo sapiens : au moins 300 000 ans (Smithsonian, Jebel Irhoud)
NEAND = (430e3, 40e3)    # Néandertaliens en Europe jusqu'à ~40 000 ans (World History Encyclopedia)


def saut(n):
    """Saut n : 2^(n-1) ans dans le passé."""
    return 2 ** (n - 1)


def annee(y_back):
    """Année calendaire (texte) atteinte en remontant de y_back ans depuis 2026."""
    a = NOW - y_back            # année astronomique
    if a >= 1:
        return "%d" % a
    return "%d av. J.-C." % (1 - a)


def nb(n):
    s = "%d" % n
    out = ""
    while len(s) > 3:
        out = " " + s[-3:] + out
        s = s[:-3]
    return s + out


def mill(y):
    return ("%.1f" % (y / 1e6)).replace(".", ",")


AVANCE = saut(27) - IMPACT
assert saut(1) == 1 and saut(7) == 64 and saut(11) == 1024 and saut(13) == 4096 and saut(15) == 16384
assert saut(17) == 65536 and saut(20) == 524288 and saut(26) == 33554432 and saut(27) == 67108864
assert annee(1) == "2025" and annee(64) == "1962" and annee(1024) == "1002" and annee(4096) == "2071 av. J.-C."
AGE_PYR = (NOW - 4096) - PYRAMIDE          # âge de la pyramide à l'arrivée
assert 480 <= AGE_PYR <= 500               # « près de 500 ans »
assert NEAND[1] < saut(17) < NEAND[0]      # 65 536 ans : Néandertaliens encore là
assert saut(20) > SAPIENS and round((saut(20) - SAPIENS) / 1e4) * 1e4 == 220000
assert mill(saut(26)) == "33,6" and mill(saut(27)) == "67,1" and mill(AVANCE) == "1,1"
assert TREX[1] <= saut(27) <= TREX[0]      # le T. rex est bien là
assert saut(26) < IMPACT < saut(27)        # 26 sauts : pas assez ; 27 : trop loin

# ---------------------------------------------------------------- chronologie
# (clé, durée, années dans le passé à atteindre, légende, Gérard dit, décor)
RAW = [
    ("hook", 3.4, 0, "C'EST MICHEL QUI A TUÉ | *LES DINOSAURES.*", "Pardon ?", "salon"),
    ("machine", 3.8, 0, "Gérard fabrique une machine | à remonter le temps. *Michel s'y assoit.*", "Non.", "salon"),
    ("regle", 3.6, 0, "Chaque saut l'envoie | *deux fois plus loin* dans le passé.", None, "salon"),
    ("an1", 3.6, saut(1), "Saut 1 : *1 an.* Il pousse | la tasse de Gérard. *Version 2025.*", "Ah.", "salon"),
    ("an64", 3.6, saut(7), "Saut 7 : *64 ans.* 1962. | Il pousse un téléphone *à cadran.*", None, "salon"),
    ("an1024", 3.6, saut(11), "Saut 11 : *l'an 1002.* | Un banquet. Une coupe. *Bing.*", None, "chateau"),
    ("egypte", 3.8, saut(13), "Saut 13 : *2071 av. J.-C.* La grande | pyramide a déjà *près de 500 ans.*", None, "egypte"),
    ("glace", 3.8, saut(15), "Saut 15 : *16 384 ans.* Âge glaciaire. | Il pousse un caillou. *Sur un mammouth.*", None, "glace"),
    ("neand", 3.6, saut(17), "Saut 17 : *65 536 ans.* Néandertal. | L'un d'eux a *une moustache.*", "Ah.", "grotte"),
    ("vide", 3.8, saut(20), "Saut 20 : *524 288 ans.* | *Aucun humain.* Aucune croquette.", None, "savane"),
    ("montage", 3.6, saut(26), "Sauts 21 à 26 : | *%s millions d'années.*" % mill(saut(26)), None, "foret"),
    ("dino", 3.8, saut(27), "Saut 27 : *%s millions d'années.* | Des dinosaures." % mill(saut(27)), None, "dino"),
    ("tot", 3.8, saut(27), "L'astéroïde, c'est il y a *66 millions.* | Michel a *%s million d'années* d'avance." % mill(AVANCE), None, "dino"),
    ("sieste", 3.6, IMPACT, "Il fait une sieste. | De *%s million d'années.*" % mill(AVANCE), None, "dino"),
    ("roche", 3.8, IMPACT, "Un rocher d'environ *10 km* | passe *à côté* de la Terre.", None, "espace"),
    ("pousse", 3.6, IMPACT, "Michel fait ce qu'il fait | avec *tous les objets.*", None, "espace"),
    ("impact", 3.6, IMPACT, "*Fin des dinosaures.* | Enfin… presque tous.", None, "impact"),
    ("retour", 3.8, 0, "Retour en 2026. Les oiseaux | *sont des dinosaures.* Michel les surveille.", None, "salon"),
    ("fin", 4.6, 0, "Gérard a une question. | Michel pousse *son verre.*", "C'était toi ?", "salon"),
]
CARD_DUR = 4.4
BEATS = []
_t, _p = 0.0, 0.0
for key, dur, yb, cap, ger_, ph_ in RAW:
    BEATS.append(dict(key=key, start=_t, dur=dur, p0=_p, p1=yb, cap=cap, ger=ger_, ph=ph_))
    _t += dur
    _p = yb
CARD = _t
END = CARD + CARD_DUR
K = {b["key"]: b["start"] for b in BEATS}
B = {b["key"]: b for b in BEATS}
JUMPS = [b["start"] for b in BEATS if b["p1"] > b["p0"] and b["key"] != "montage"]
# le montage enchaîne 6 sauts (21 à 26)
MONTAGE_JUMPS = [K["montage"] + i * B["montage"]["dur"] * .85 / 6 for i in range(6)]
FLOOR = 1565


def beat_at(t):
    cur = BEATS[0]
    for b in BEATS:
        if b["start"] <= t:
            cur = b
        else:
            break
    return cur


def phys_at(t):
    """Nombre d'années dans le passé affiché par le compteur."""
    b = beat_at(t)
    p0, p1 = b["p0"], b["p1"]
    if p1 == p0:
        return p1
    if b["key"] == "montage":
        # 6 marches nettes : un saut à chaque fois
        k = min(6, int((t - b["start"]) / (b["dur"] * .85 / 6)) + 1)
        return float(saut(20 + k))
    f = clamp((t - b["start"]) / (b["dur"] * (.85 if b["key"] in ("sieste", "retour") else .55)))
    if b["key"] == "sieste":
        return lerp(p0, p1, f)                    # le temps passe, à l'endroit
    f = eout(f)
    a, z = max(p0, 1.0), max(p1, 1.0)
    y = math.exp(lerp(math.log(a), math.log(z), f))   # interpolation géométrique
    if p1 == 0 and f >= 1:
        return 0.0
    if p0 == 0 and f < .15:
        return 0.0
    return y


# ---------------------------------------------------------------- outils communs (repris des vidéos 09 et 10)
def ger(c, x, floor, s, t, stage=0, arms="down", walk=0.0, lean=0.0, a=1.0, fur=False):
    c.save()
    if a < 1:
        c.saveLayerAlpha(None, int(255 * a))
    bob = -abs(math.sin(t * 9)) * 16 * walk
    c.translate(x, floor + bob)
    c.rotate(lean)
    c.scale(s, s)
    c.translate(-790, -1516)
    sw = "#3F6FD8" if not fur else "#9A6A3A"
    draw_gerard(c, stage, t, False, 0, True)
    if fur:
        # tunique en peau de bête par-dessus le pull
        p = poly([(672, 1110), (908, 1100), (930, 1352), (860, 1330), (800, 1372), (740, 1330), (668, 1360)])
        shape(c, p, "#9A6A3A", 8)
        for (x_, y_) in ((720, 1170), (840, 1200), (760, 1270), (870, 1290)):
            c.drawCircle(x_, y_, 14, fill("#6E4524"))
    for sg in (-1, 1):
        arm = skia.Path()
        arm.moveTo(790 + sg * 96, 1160)
        if arms == "float":
            w_ = math.sin(t * 2 + sg) * 20
            arm.quadTo(790 + sg * 190, 1150 + w_, 790 + sg * 230, 1060 + w_)
        elif arms == "up":
            arm.quadTo(790 + sg * 170, 1100, 790 + sg * 200, 960)
        else:
            arm.quadTo(790 + sg * 130, 1250, 790 + sg * 118, 1330)
        c.drawPath(arm, line(INK, 56))
        c.drawPath(arm, line(sw, 42))
    if a < 1:
        c.restore()
    c.restore()


def gerbub(c, t, b, x, y, delay=0.0):
    if not b["ger"]:
        return
    f = skia.Font(TF, 56)
    w = f.measureText(b["ger"])
    xx = clamp(x, w / 2 + 44, W - w / 2 - 44)
    bubble(c, xx, y, b["ger"], 56, back((t - b["start"] - .35 - delay) / .16), 2)


def fit(s, size, maxw):
    f = skia.Font(TF, size)
    while f.measureText(s) > maxw and size > 20:
        size -= 2
        f = skia.Font(TF, size)
    return size


def sign(c, s, x, y, size=46, colr="#FFE14D", rot=0.0, a=1.0):
    f = skia.Font(TF, size)
    w = f.measureText(s)
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    shape(c, rrect(-w / 2 - 26, -size * .95, w / 2 + 26, size * .45, 14), colr, 6, a)
    text(c, s, 0, 0, size, INK, a=a)
    c.restore()


def paw(c, x0, y0, x1, y1):
    p = skia.Path()
    p.moveTo(x0, y0)
    p.lineTo(x1, y1)
    c.drawPath(p, line(INK, 40))
    c.drawPath(p, line("#F49A3A", 28))
    shape(c, oval(x1 - 24, y1 - 20, x1 + 24, y1 + 20), "#FFE1B0", 6)


def pop(c, t, b, x, y):
    """Arrivée de la machine : éclair et anneaux."""
    d_ = t - b["start"]
    if d_ < 0 or d_ > .5:
        return
    u = d_ / .5
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", clamp(1 - d_ / .18) * .9))
    for k in range(3):
        r = (120 + k * 90) * eout(u) + 20
        c.drawCircle(x, y, r, line("#7EF0FF", 14 * (1 - u), 1 - u))


def box(c, x, floor, s, t, glow=0.0, label=True):
    """La machine : un carton, un cadran, une antenne."""
    c.save()
    c.translate(x, floor)
    c.scale(s, s)
    if glow > 0:
        gl = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((0, -120), 320, [col("#7EF0FF", .55 * glow), col("#7EF0FF", 0)]))
        c.drawCircle(0, -120, 320, gl)
    shape(c, poly([(-170, -200), (170, -200), (150, 0), (-150, 0)]), "#C8955A", 8)
    shape(c, poly([(-170, -200), (-230, -270), (-110, -270), (-60, -200)]), "#D9A86C", 7)
    shape(c, poly([(170, -200), (230, -270), (110, -270), (60, -200)]), "#D9A86C", 7)
    if label:
        text(c, "MACHINE", 0, -110, 46, INK)
    c.drawCircle(-90, -55, 30, fill("#FFFFFF"))
    c.drawCircle(-90, -55, 30, line(INK, 6))
    a_ = t * (3 + 20 * glow)
    c.drawLine(-90, -55, -90 + 22 * math.cos(a_), -55 + 22 * math.sin(a_), line("#FF4B4B", 6))
    for k in range(3):
        on = (int(t * 6) + k) % 3 == 0
        c.drawCircle(30 + k * 44, -50, 14, fill("#59E36A" if on else "#2E6B35"))
        c.drawCircle(30 + k * 44, -50, 14, line(INK, 4))
    c.drawLine(150, -200, 200, -330, line(INK, 8))
    c.drawCircle(200, -340, 18, fill("#FF4B4B" if int(t * 4) % 2 else "#FFE14D"))
    c.drawCircle(200, -340, 18, line(INK, 5))
    c.restore()


# ---------------------------------------------------------------- objets qu'on pousse
def obj(c, kind, x, y, rot=0.0, broken=False):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    if kind == "tasse":
        shape(c, rrect(-40, -86, 40, 0, 12), "#FF6B8A", 6)
        c.drawCircle(46, -44, 22, line(INK, 18))
        c.drawCircle(46, -44, 22, line("#FF6B8A", 8))
    elif kind == "tel":
        shape(c, poly([(-70, 0), (70, 0), (56, -70), (-56, -70)]), "#2F2A3A", 6)
        c.drawCircle(0, -40, 30, fill("#E9E4D8"))
        c.drawCircle(0, -40, 30, line(INK, 5))
        for k in range(8):
            a_ = k * .7
            c.drawCircle(18 * math.cos(a_), -40 + 18 * math.sin(a_), 4, fill(INK))
        shape(c, rrect(-80, -104, 80, -76, 14), "#2F2A3A", 6)
    elif kind == "coupe":
        shape(c, poly([(-40, -110), (40, -110), (12, -50), (12, -16), (34, 0), (-34, 0), (-12, -16), (-12, -50)]), "#E8B83A", 6)
        c.drawOval(skia.Rect.MakeLTRB(-34, -112, 34, -96), fill("#8E1F3A"))
    elif kind == "vase":
        shape(c, poly([(-30, -110), (30, -110), (22, -92), (52, -50), (30, 0), (-30, 0), (-52, -50), (-22, -92)]), "#3A8FB7", 6)
        c.drawLine(-46, -52, 46, -52, line("#FFE14D", 6))
    elif kind == "caillou":
        shape(c, poly([(-50, 0), (-56, -40), (-20, -72), (30, -66), (58, -30), (44, 0)]), "#8C8A94", 6)
    elif kind == "os":
        shape(c, rrect(-60, -28, 60, -12, 8), "#F2ECD8", 5)
        for sx in (-60, 60):
            for dy in (-34, -8):
                shape(c, oval(sx - 13, dy - 13, sx + 13, dy + 13), "#F2ECD8", 5)
    elif kind == "verre":
        shape(c, poly([(-36, -120), (36, -120), (28, 0), (-28, 0)]), "#DDF3FF", 6)
        c.drawRect(skia.Rect.MakeLTRB(-31, -70, 31, -4), fill("#7EC8FF", .7))
    if broken:
        for k in range(5):
            r = random.Random(k)
            c.drawLine(r.uniform(-50, 50), r.uniform(-60, 0), r.uniform(-50, 50), r.uniform(-60, 0), line(INK, 4))
    c.restore()


def push_seq(c, t, d_, kind, x_edge, y_top, y_floor, cat_x, t0=1.0, dir_=1):
    """L'objet est au bord ; Michel tapote 3 fois, il glisse, il tombe, il casse.
    Renvoie (patte tendue 0..1, objet tombé)."""
    taps = d_ - t0
    slide = clamp((taps - .75) / .25)
    x = x_edge - dir_ * 50 + dir_ * 70 * eout(slide)
    fall = taps - 1.0
    if fall < 0:
        obj(c, kind, x, y_top)
        ext = 0.0
        if 0 <= taps < .9:
            ext = abs(math.sin(taps / .3 * math.pi))
        return ext, False
    g = 5200
    y = y_top + .5 * g * fall * fall
    if y >= y_floor:
        obj(c, kind, x + dir_ * 60, y_floor, dir_ * 100, broken=kind in ("tasse", "coupe", "vase", "verre", "tel"))
        return 0.0, True
    obj(c, kind, x + dir_ * 60 * clamp(fall / .3), y, dir_ * 220 * fall)
    return 0.0, False


# ---------------------------------------------------------------- salon (2026, 2025, 1962)
TX0, TX1, TY = 500, 900, FLOOR - 250       # table


def table(c, x0=TX0, x1=TX1, y=TY, colr="#A86A3C"):
    shape(c, rrect(x0, y, x1, y + 34, 10), colr, 7)
    for lx in (x0 + 30, x1 - 64):
        shape(c, rrect(lx, y + 30, lx + 34, FLOOR + 6, 6), hexmix(colr, "#000000", .2), 6)


def calendar(c, s, x=380, y=760):
    shape(c, rrect(x - 90, y - 70, x + 90, y + 110, 10), "#FFFFFF", 6)
    c.drawRect(skia.Rect.MakeLTRB(x - 88, y - 68, x + 88, y - 20), fill("#FF4B4B"))
    text(c, s, x, y + 70, 64, INK)


def dino_toy(c, x, y, s=1.0, colr="#59B36A"):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    trex(c, 0, 0, .22, 0.0, colr)
    c.restore()


def salon_bg(c, t, era):
    wall, stripe = ("#F7DDAE", "#F2D29C") if era != "1962" else ("#E9A85C", "#C9783A")
    c.drawRect(skia.Rect.MakeWH(W, H), fill(wall))
    for x in range(0, W, 120):
        c.drawRect(skia.Rect.MakeLTRB(x, 640, x + 60, FLOOR), fill(stripe, .55))
    c.drawRect(skia.Rect.MakeLTRB(0, FLOOR - 34, W, FLOOR), fill("#FFF5E0"))
    shape(c, rrect(620, 760, 960, 1080, 14), "#9AD4F5", 8)
    c.drawLine(790, 760, 790, 1080, line(INK, 6))
    c.drawLine(620, 920, 960, 920, line(INK, 6))
    calendar(c, {"2026": "2026", "2025": "2025", "1962": "1962"}[era])
    c.drawRect(skia.Rect.MakeLTRB(0, FLOOR, W, H), fill("#7B4A2B" if era != "1962" else "#5E7A3A"))
    c.drawLine(0, FLOOR, W, FLOOR, line(INK, 7))
    for i in range(5):
        c.drawLine(i * 240 + 60, FLOOR + 2, i * 300 - 180, H, line(INK, 4, .35))


def bird(c, x, y, s, t):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    shape(c, oval(-50, -40, 50, 30), "#6E8FD8", 6)
    shape(c, oval(20, -80, 80, -20), "#6E8FD8", 6)
    c.drawCircle(58, -56, 8, fill(INK))
    shape(c, poly([(78, -54), (110, -46), (78, -38)]), "#FFB02E", 4)
    w_ = math.sin(t * 14) * 18
    shape(c, poly([(-20, -20), (-70, -60 + w_), (10, -30)]), "#4E6FB8", 5)
    c.drawLine(-10, 30, -14, 54, line(INK, 5))
    c.drawLine(10, 30, 14, 54, line(INK, 5))
    c.restore()


GX = 300


def scene_salon(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    era = {"an1": "2025", "an64": "1962"}.get(key, "2026")
    salon_bg(c, t, era)
    if key == "hook":
        dino_toy(c, 560, FLOOR + 10, 1.0)
        box(c, 800, FLOOR + 6, .9, t)
        ger(c, GX, FLOOR + 30, .62, t, 1)
        draw_cat(c, 800, FLOOR - 170, .3, t, "wink" if d_ > 2.0 else "open", 0)
        gerbub(c, t, b, GX + 40, 960, .9)
        return
    if key == "machine":
        s = back((d_ - .2) / .3)
        if s > 0:
            box(c, 780, FLOOR + 6, .9 * s, t)
        # Michel saute dedans
        j = clamp((d_ - 1.0) / .6)
        mx = lerp(1000, 780, j)
        my = FLOOR + 30 - math.sin(j * math.pi) * 300 - (FLOOR + 30 - (FLOOR - 170)) * eout(j)
        draw_cat(c, mx, my, .3, t, "open" if j < 1 else "bliss", 0)
        ger(c, GX, FLOOR + 30, .62, t, 2 if d_ > 1.8 else 0, arms="up" if d_ > 1.8 else "down")
        gerbub(c, t, b, GX + 40, 960, 1.6)
        return
    if key == "regle":
        g = .5 + .5 * math.sin(t * 10)
        box(c, 780, FLOOR + 6, .9, t, glow=.4 + .6 * g * clamp(d_ / .5))
        draw_cat(c, 780, FLOOR - 170, .3, t, "bliss", 2 * clamp(d_ / .5))
        ger(c, GX, FLOOR + 30, .62, t, 1)
        sign(c, "×2 À CHAQUE SAUT", 540, 1150, 58, "#7EF0FF", -3, clamp((d_ - .4) / .2))
        return
    if key in ("an1", "an64"):
        table(c, colr="#A86A3C" if key == "an1" else "#7A4E2A")
        if key == "an1":
            ger(c, GX, FLOOR + 30, .62, t, 0 if d_ < 2.2 else 2)
        draw_cat(c, 680, TY + 4, .3, t, "open" if d_ < 2.4 else "bliss", 0)
        ext, done = push_seq(c, t, d_, "tasse" if key == "an1" else "tel", TX1 - 40, TY, FLOOR + 6, 780)
        if ext > 0:
            paw(c, 720, TY - 50, 720 + 100 * ext, TY - 40)
        if key == "an1" and d_ > 2.3:
            gerbub(c, t, b, GX + 40, 960, 1.95)
        if key == "an64" and d_ > 2.3:
            bubble(c, 680, TY - 200, "mrrp.", 52, back((d_ - 2.3) / .16), 3)
        pop(c, t, b, 680, TY - 80)
        return
    if key == "retour":
        ger(c, GX, FLOOR + 30, .62, t, 0)
        box(c, 300 + 560, FLOOR + 6, .7, t, label=False)
        # Michel sur le rebord, devant la fenêtre ; un oiseau dehors
        shape(c, rrect(600, 1080, 980, 1110, 6), "#FFFFFF", 6)
        bx = lerp(1150, 860, eout(clamp((d_ - .5) / .8)))
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(620, 760, 960, 1080))
        bird(c, bx, 1000, .9, t)
        c.restore()
        draw_cat(c, 720, 1084, .3, t, "open", 3 if d_ > 1.4 else 0)
        if d_ > 1.6:
            bubble(c, 640, 860, "ek ek ek", 46, back((d_ - 1.6) / .16), -3)
        pop(c, t, b, 860, FLOOR - 120)
        return
    if key == "fin":
        table(c)
        ger(c, GX, FLOOR + 30, .62, t, 0 if d_ < 2.4 else 3)
        draw_cat(c, 680, TY + 4, .3, t, "wink" if d_ > 3.0 else "open", 0)
        ext, done = push_seq(c, t, d_, "verre", TX1 - 40, TY, FLOOR + 6, 780, t0=1.4)
        if ext > 0:
            paw(c, 720, TY - 50, 720 + 100 * ext, TY - 40)
        if d_ < 1.4:
            gerbub(c, t, b, GX + 40, 960)
        if d_ > 3.0:
            bubble(c, 680, TY - 200, "mrrp ?", 52, back((d_ - 3.0) / .16), 3)
        return


# ---------------------------------------------------------------- château, an 1002
def scene_chateau(c, t, b):
    d_ = t - b["start"]
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#8A8698"))
    for row in range(16):
        off = 70 if row % 2 else 0
        for x in range(-140, W + 140, 140):
            c.drawRect(skia.Rect.MakeLTRB(x + off + 4, 600 + row * 64 + 4, x + off + 136, 600 + row * 64 + 60), fill("#9C98AA"))
    # bannière
    shape(c, poly([(160, 640), (360, 640), (360, 1040), (260, 980), (160, 1040)]), "#C2283A", 7)
    shape(c, oval(220, 760, 300, 840), "#FFE14D", 5)
    # torche
    c.drawLine(820, 900, 860, 760, line(INK, 18))
    c.drawLine(820, 900, 860, 760, line("#7A4E2A", 10))
    fl = 1 + .15 * math.sin(t * 23)
    shape(c, oval(830, 690 - 30 * fl, 890, 770), "#FF8A1F", 5)
    c.drawOval(skia.Rect.MakeLTRB(845, 720, 875, 765), fill("#FFE14D"))
    c.drawRect(skia.Rect.MakeLTRB(0, FLOOR, W, H), fill("#5E4634"))
    c.drawLine(0, FLOOR, W, FLOOR, line(INK, 7))
    table(c, 120, TX1, TY, "#7A4E2A")
    # pain, pomme
    shape(c, oval(220, TY - 70, 380, TY + 4), "#D9A050", 6)
    c.drawCircle(470, TY - 30, 32, fill("#D33A3A"))
    c.drawCircle(470, TY - 30, 32, line(INK, 5))
    draw_cat(c, 680, TY + 4, .3, t, "open" if d_ < 2.4 else "bliss", 0)
    ext, done = push_seq(c, t, d_, "coupe", TX1 - 40, TY, FLOOR + 6, 680)
    if ext > 0:
        paw(c, 720, TY - 50, 720 + 100 * ext, TY - 40)
    if d_ > 2.4:
        text(c, "BING.", 960, FLOOR - 60, 64, "#FFE14D", INK, 10, a=clamp((d_ - 2.4) / .15))
    pop(c, t, b, 680, TY - 80)


# ---------------------------------------------------------------- Égypte, 2071 av. J.-C.
def scene_egypte(c, t, b):
    d_ = t - b["start"]
    p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 600), (0, 1300)], [col("#FFB55E"), col("#FFE7A8")]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    c.drawCircle(860, 760, 90, fill("#FFF3B0"))
    for (x, w_, h_) in ((330, 560, 440), (760, 380, 300), (960, 220, 170)):
        shape(c, poly([(x - w_ / 2, 1300), (x, 1300 - h_), (x + w_ / 2, 1300)]), "#E0B060", 7)
        c.drawPath(poly([(x, 1300 - h_), (x + w_ / 2, 1300), (x + w_ * .12, 1300)]), fill("#C79440", .7))
    text(c, "~500 ANS", 330, 1250, 50, "#FFFFFF", INK, 8, a=clamp((d_ - 1.0) / .2))
    c.drawRect(skia.Rect.MakeLTRB(0, 1300, W, H), fill("#F2CC7A"))
    c.drawLine(0, 1300, W, 1300, line(INK, 6))
    # bloc de pierre + vase
    shape(c, rrect(460, TY, 900, FLOOR + 40, 6), "#D9B070", 7)
    draw_cat(c, 660, TY + 4, .3, t, "open" if d_ < 2.4 else "bliss", 0)
    ext, done = push_seq(c, t, d_, "vase", 880, TY, FLOOR + 140, 660)
    if ext > 0:
        paw(c, 700, TY - 50, 700 + 100 * ext, TY - 40)
    pop(c, t, b, 660, TY - 80)


# ---------------------------------------------------------------- âge glaciaire, 16 384 ans
def mammoth(c, x, y, s, t, hit=0.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    for lx in (-110, -40, 50, 120):
        shape(c, rrect(lx - 30, -60, lx + 30, 80, 14), "#7A4A2A", 6)
    shape(c, oval(-190, -260, 190, 20), "#8E5A32", 8)
    for k in range(9):
        c.drawLine(-170 + k * 40, -10, -176 + k * 40, 30, line("#6E4524", 8))
    shape(c, oval(110, -330, 290, -130), "#8E5A32", 8)
    tr = skia.Path()
    tr.moveTo(260, -170)
    tr.cubicTo(320, -80, 300, 10, 250 + 20 * math.sin(t * 3), 40)
    c.drawPath(tr, line(INK, 46))
    c.drawPath(tr, line("#8E5A32", 32))
    tk = skia.Path()
    tk.moveTo(230, -150)
    tk.cubicTo(300, -60, 360, -80, 360, -170)
    c.drawPath(tk, line(INK, 26))
    c.drawPath(tk, line("#F7F1DF", 16))
    if hit > 0:
        c.drawCircle(220, -260, 16, fill(INK))
        c.drawCircle(220, -260, 26, line(INK, 4))
    else:
        c.drawCircle(220, -260, 10, fill(INK))
    c.restore()


def scene_glace(c, t, b):
    d_ = t - b["start"]
    p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 600), (0, 1400)], [col("#A9D4F2"), col("#EAF6FF")]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    shape(c, poly([(-40, 1350), (200, 1000), (380, 1350)]), "#FFFFFF", 6)
    shape(c, poly([(260, 1350), (520, 900), (760, 1350)]), "#F2FAFF", 6)
    for k in range(30):
        r = random.Random(k)
        x = (r.uniform(0, W) + t * 40) % W
        y = (r.uniform(0, H) + t * 120 * r.uniform(.6, 1.2)) % H
        c.drawCircle(x, y, r.uniform(4, 9), fill("#FFFFFF", .85))
    c.drawRect(skia.Rect.MakeLTRB(0, FLOOR, W, H), fill("#F7FBFF"))
    c.drawLine(0, FLOOR, W, FLOOR, line(INK, 7))
    # falaise à droite
    shape(c, poly([(640, TY - 200), (W + 20, TY - 200), (W + 20, FLOOR + 10), (700, FLOOR + 10)]), "#B9C6D8", 7)
    yt = TY - 200
    # mammouth en bas à gauche
    hit_t = None
    draw_cat(c, 860, yt + 4, .3, t, "open" if d_ < 2.4 else "bliss", 0)
    taps = d_ - 1.0
    fall = taps - 1.0
    hit = clamp((fall - .42) / .1) if fall > 0 else 0
    mammoth(c, 330 + 10 * math.sin(t * 30) * hit * clamp(1 - (fall - .5) / .6), FLOOR + 20, .85, t, hit)
    # caillou : tombe en arc sur le mammouth
    if taps < 1.0:
        x = 690 - 60 * eout(clamp((taps - .75) / .25))
        obj(c, "caillou", x, yt)
        if 0 <= taps < .9:
            e = abs(math.sin(taps / .3 * math.pi))
            paw(c, 820, yt - 50, 820 - 90 * e, yt - 40)
    else:
        f = clamp(fall / .45)
        x = lerp(630, 470, f)
        y = lerp(yt, FLOOR - 260, f * f)
        if f >= 1:
            x, y = 470 + 120 * clamp((fall - .45) / .4), FLOOR - 260 + 260 * clamp((fall - .45) / .4) ** 2
        obj(c, "caillou", x, y, -200 * fall)
    if hit > 0 and fall < 1.6:
        bubble(c, 520, FLOOR - 420, "!", 70, back((fall - .45) / .16), 4)
    pop(c, t, b, 860, yt - 80)


# ---------------------------------------------------------------- grotte, Néandertaliens
def fire(c, x, y, t):
    for lx in (-50, 50):
        c.drawLine(x + lx, y + 10, x - lx, y - 20, line("#5E3A1E", 22))
    for k, (s_, colr) in enumerate(((1.0, "#FF6A1F"), (.66, "#FFB02E"), (.36, "#FFF3B0"))):
        h_ = 170 * s_ * (1 + .12 * math.sin(t * 17 + k))
        w_ = 70 * s_
        c.drawPath(poly([(x - w_, y), (x - w_ * .4, y - h_ * .6), (x, y - h_), (x + w_ * .5, y - h_ * .55), (x + w_, y)]), fill(colr))


def scene_grotte(c, t, b):
    d_ = t - b["start"]
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#3A2A22"))
    gl = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((640, 1400), 700 + 30 * math.sin(t * 9), [col("#FF9A3A", .55), col("#FF9A3A", 0)]))
    c.drawRect(skia.Rect.MakeWH(W, H), gl)
    # parois
    shape(c, poly([(-20, 560), (260, 600), (180, 900), (-20, 1000)]), "#2A1E18", 0)
    shape(c, poly([(W + 20, 560), (820, 620), (900, 900), (W + 20, 1050)]), "#2A1E18", 0)
    # peinture rupestre générique (cheval + mains)
    pc = "#C2552E"
    c.drawPath(poly([(380, 760), (520, 740), (560, 780), (540, 830), (400, 840), (360, 800)]), fill(pc, .8))
    for lx in (400, 430, 500, 530):
        c.drawLine(lx, 830, lx, 880, line(pc, 10, .8))
    c.drawLine(540, 770, 600, 730, line(pc, 14, .8))
    c.drawRect(skia.Rect.MakeLTRB(0, FLOOR, W, H), fill("#4A3A30"))
    c.drawLine(0, FLOOR, W, FLOOR, line(INK, 7))
    fire(c, 600, FLOOR + 10, t)
    ger(c, GX, FLOOR + 30, .62, t, 0 if d_ < 2.2 else 2, fur=True)
    # rocher + os
    shape(c, rrect(760, TY + 40, 1060, FLOOR + 20, 30), "#6C6070", 7)
    draw_cat(c, 900, TY + 44, .3, t, "open" if d_ < 2.4 else "bliss", 0)
    ext, done = push_seq(c, t, d_, "os", 790, TY + 40, FLOOR + 6, 900, dir_=-1)
    if ext > 0:
        paw(c, 860, TY - 10, 860 - 100 * ext, TY)
    if d_ > 2.2:
        gerbub(c, t, b, GX + 40, 960, 1.85)
    pop(c, t, b, 900, TY - 40)


# ---------------------------------------------------------------- savane vide, 524 288 ans
def scene_savane(c, t, b):
    d_ = t - b["start"]
    p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 600), (0, 1300)], [col("#FFC46B"), col("#FFE9B8")]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    c.drawCircle(300, 820, 110, fill("#FFF3B0"))
    c.drawRect(skia.Rect.MakeLTRB(0, 1320, W, H), fill("#D9B254"))
    c.drawLine(0, 1320, W, 1320, line(INK, 6))
    # acacia
    c.drawLine(820, 1330, 800, 1030, line(INK, 34))
    c.drawLine(820, 1330, 800, 1030, line("#7A4E2A", 22))
    shape(c, oval(600, 940, 1020, 1060), "#5E8A3A", 7)
    for k in range(14):
        r = random.Random(k)
        x = r.uniform(20, W - 20)
        y = r.uniform(1350, FLOOR + 200)
        for dx in (-12, 0, 12):
            c.drawLine(x, y, x + dx * 1.4 + 6 * math.sin(t * 2 + k), y - 40, line("#A88A2E", 6))
    box(c, 420, FLOOR + 6, .7, t, label=False)
    draw_cat(c, 420, FLOOR - 140, .26, t, "open", 0)
    if d_ > 1.2:
        bubble(c, 480, FLOOR - 330, "?", 60, back((d_ - 1.2) / .16), -3)
    u = clamp((d_ - 1.8) / .2)
    sign(c, "HOMO SAPIENS : DANS ~220 000 ANS", 540, 1240, 42, "#FFFFFF", -2, u)
    pop(c, t, b, 420, FLOOR - 120)


# ---------------------------------------------------------------- montage, sauts 21 à 26
MONT_COLS = [("#B8D86A", "#5E8A3A"), ("#8FD0A8", "#3E7A5A"), ("#D8C86A", "#7A6A2E"), ("#6AC8B8", "#2E6A6A"), ("#A8D85E", "#4E7A2E"), ("#7AC86A", "#2E6A3A")]


def scene_foret(c, t, b):
    d_ = t - b["start"]
    step = b["dur"] * .85 / 6
    k = min(5, int(d_ / step))
    sky, ground = MONT_COLS[k]
    c.drawRect(skia.Rect.MakeWH(W, H), fill(sky))
    r = random.Random(k * 13)
    for i in range(7):
        x = r.uniform(0, W)
        hh = r.uniform(300, 700)
        c.drawLine(x, FLOOR, x, FLOOR - hh, line(INK, 30))
        c.drawLine(x, FLOOR, x, FLOOR - hh, line("#7A4E2A", 18))
        for j in range(5):
            a_ = -math.pi / 2 + (j - 2) * .55
            c.drawLine(x, FLOOR - hh, x + 170 * math.cos(a_), FLOOR - hh + 170 * math.sin(a_) + 60, line(ground, 30))
    c.drawRect(skia.Rect.MakeLTRB(0, FLOOR, W, H), fill(ground))
    c.drawLine(0, FLOOR, W, FLOOR, line(INK, 7))
    # traits de vitesse
    rr = random.Random(int(t * 20))
    for i in range(16):
        y = rr.uniform(600, FLOOR)
        x = rr.uniform(-200, W)
        c.drawLine(x, y, x + rr.uniform(200, 500), y, line("#FFFFFF", 6, .6))
    box(c, 540, FLOOR + 6, .8, t, glow=.8)
    draw_cat(c, 540, FLOOR - 154, .3, t, "open", 4)
    lt = d_ - k * step
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", clamp(1 - lt / .14) * .85))


# ---------------------------------------------------------------- les dinosaures
def trex(c, x, y, s, t, colr="#59B36A", sleep=False, look=0.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    dk = hexmix(colr, "#000000", .3)
    tail = poly([(-120, -260), (-470, -180 + 10 * math.sin(t * 2)), (-110, -170)])
    shape(c, tail, colr, 8)
    for lx in (-60, 60):
        shape(c, rrect(lx - 40, -170, lx + 40, -10, 20), dk, 7)
        shape(c, rrect(lx - 50, -30, lx + 70, 6, 12), dk, 6)
    shape(c, oval(-170, -380, 150, -130), colr, 8)
    c.drawOval(skia.Rect.MakeLTRB(-60, -330, 120, -150), fill(hexmix(colr, "#FFFFFF", .35)))
    # tête
    c.save()
    c.translate(110, -380)
    c.rotate(look)
    shape(c, rrect(-60, -150, 220, 10, 50), colr, 8)
    c.drawLine(10, -30, 210, -30, line(INK, 6))
    for k in range(6):
        c.drawPath(poly([(30 + k * 30, -30), (44 + k * 30, -30), (37 + k * 30, -12)]), fill("#FFFFFF"))
    if sleep:
        p = skia.Path()
        p.moveTo(40, -96)
        p.quadTo(66, -76, 92, -96)
        c.drawPath(p, line(INK, 8))
    else:
        c.drawCircle(66, -96, 24, fill("#FFFFFF"))
        c.drawCircle(66, -96, 24, line(INK, 6))
        c.drawCircle(72, -94, 11, fill(INK))
    c.drawCircle(196, -116, 6, fill(INK))
    c.restore()
    # petits bras
    for k in (0, 1):
        a = poly([(110 + k * 14, -240), (190 + k * 14, -220), (186 + k * 14, -196)], close=False)
        c.drawPath(a, line(INK, 26))
        c.drawPath(a, line(colr, 14))
    c.restore()


def volcano(c, x, y, t):
    shape(c, poly([(x - 300, y), (x - 60, y - 380), (x + 60, y - 380), (x + 300, y)]), "#6E5A6A", 7)
    for k in range(3):
        ph = (t * .4 + k / 3) % 1
        c.drawCircle(x + math.sin(t + k) * 30, y - 420 - ph * 260, 50 + ph * 70, fill("#9E96A8", .7 * (1 - ph)))


def fern(c, x, y, s, t):
    for k in range(5):
        a_ = -math.pi / 2 + (k - 2) * .45 + .05 * math.sin(t * 2 + k)
        p = skia.Path()
        p.moveTo(x, y)
        p.quadTo(x + 120 * s * math.cos(a_) * 1.4, y + 120 * s * math.sin(a_), x + 220 * s * math.cos(a_ + .3), y + 200 * s * math.sin(a_) + 40 * s)
        c.drawPath(p, line(INK, 26 * s))
        c.drawPath(p, line("#3E9A4E", 16 * s))


def scene_dino(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    night = 0.0
    if key == "sieste":
        night = .5 + .5 * math.sin(t * 14) if d_ > .3 else 0.0
    sky1 = hexmix("#FFB86B", "#1A1440", night)
    sky2 = hexmix("#FFE3B0", "#3A2A60", night)
    p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 600), (0, 1350)], [col(sky1), col(sky2)]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    volcano(c, 820, 1350, t)
    c.drawRect(skia.Rect.MakeLTRB(0, 1340, W, H), fill(hexmix("#8AA64A", "#2E3A2A", night)))
    c.drawLine(0, 1340, W, 1340, line(INK, 6))
    fern(c, 80, 1360, 1.0, t)
    fern(c, 1000, 1400, 1.2, t)
    trex(c, 330, FLOOR + 20, .78, t, sleep=(key == "sieste" and d_ > 1.0), look=-8 if key == "dino" and d_ > 1.0 else 0)
    box(c, 840, FLOOR + 6, .7, t, label=False)
    mood = "bliss" if key == "sieste" else "open"
    draw_cat(c, 840, FLOOR - 140, .26, t, mood, 0)
    if key == "dino":
        if d_ > 1.2:
            bubble(c, 520, 1020, "?", 60, back((d_ - 1.2) / .16), -3)
        if d_ > 2.0:
            bubble(c, 840, FLOOR - 330, "mrrp.", 50, back((d_ - 2.0) / .16), 3)
        pop(c, t, b, 840, FLOOR - 120)
    if key == "tot":
        u = clamp((d_ - .3) / .2)
        sign(c, "ASTÉROÏDE : DANS %s MILLION D'ANNÉES" % mill(AVANCE), 540, 1240, 38, "#FFFFFF", -2, u)
    if key == "sieste":
        for k in range(3):
            ph = (t * .7 + k / 3) % 1
            text(c, "z", 900 + ph * 80, FLOOR - 300 - ph * 200, 50 + 30 * ph, "#FFFFFF", INK, 7, a=clamp(d_ / .3) * (1 - ph))


# ---------------------------------------------------------------- l'espace
art.LAT0, art.LON0 = math.radians(21.3), math.radians(-89.5)   # Terre vue au-dessus du Yucatán (continents actuels)
EC_X, EC_Y, EC_R = 540, 1500, 330
AST_R = 105


def asteroid(c, x, y, r, rot):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    pts = []
    rr = random.Random(5)
    for k in range(14):
        a_ = k / 14 * 2 * math.pi
        q = r * rr.uniform(.82, 1.1)
        pts.append((q * math.cos(a_), q * math.sin(a_)))
    shape(c, poly(pts), "#7E7686", 7)
    for (dx, dy, cr) in ((-.3, -.2, .22), (.35, .25, .16), (.1, -.45, .12), (-.2, .45, .1)):
        c.drawCircle(dx * r, dy * r, cr * r, fill("#625A6C"))
    c.restore()


_EIMG = {}


def earth_img(R, cx, cy):
    k = (R, cx, cy)
    if k not in _EIMG:
        _EIMG[k] = earth_rgba(R, cx=cx, cy=cy)
    return _EIMG[k]


def scene_espace(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    c.drawImage(STARS, 0, 0)
    im, x0, y0 = earth_img(EC_R, EC_X, EC_Y)
    c.drawImage(im, x0, y0)
    bx, by = 330, 1000 + 20 * math.sin(t * 1.5)
    ax0, ay0 = 760, 900
    if key == "roche":
        ax = ax0 + 60 * (1 - eout(clamp(d_ / 2.0)))
        ay = ay0
        asteroid(c, ax, ay, AST_R, t * 8)
        u = clamp((d_ - .8) / .2)
        text(c, "~10 km", ax, ay + 170, 56, "#FFFFFF", INK, 8, a=u)
        box(c, bx, by + 150, .6, t, label=False)
        draw_cat(c, bx, by - 20, .24, t, "open", 0)
        # trajectoire qui passe à côté
        if d_ > 1.6:
            pth = skia.Path()
            pth.moveTo(ax, ay)
            pth.quadTo(900, 1200, 1100, 1300)
            pe = skia.DashPathEffect.Make([24, 18], 0)
            pp = line("#FFFFFF", 6, .7)
            pp.setPathEffect(pe)
            c.drawPath(pth, pp)
            text(c, "RATÉ", 1000, 1180, 46, "#59E36A", INK, 7, a=clamp((d_ - 1.8) / .2))
        return
    # pousse : 3 tapes, puis le rocher file vers le Yucatán
    taps = d_ - .6
    go = clamp((taps - 1.0) / 1.6)
    ex, ey = EC_X, EC_Y - EC_R * .05
    ax = lerp(ax0, ex, ein(go))
    ay = lerp(ay0, ey, ein(go))
    if go < 1:
        asteroid(c, ax, ay, AST_R * (1 - .8 * go), t * 8 + 300 * go)
        if go > 0:
            for k in range(4):
                c.drawLine(ax - (ex - ax0) * .05 * k, ay - (ey - ay0) * .05 * k, ax - (ex - ax0) * .08 * (k + 1), ay - (ey - ay0) * .08 * (k + 1), line("#FFB02E", 10 - 2 * k, .7))
    box(c, bx + 200 * clamp(taps / .3) * (1 - go), by + 150, .6, t, label=False)
    mx = bx + 200 * clamp(taps / .3) * (1 - go)
    draw_cat(c, mx, by - 20, .24, t, "open" if go < .5 else "wink", 0)
    if 0 <= taps < 1.0:
        e = abs(math.sin(taps / .33 * math.pi))
        paw(c, mx + 30, by - 70, mx + 30 + (ax0 - AST_R - mx - 30) * e, ay0)
    if go >= 1:
        c.drawCircle(ex, ey, 30 + 40 * clamp((taps - 2.6) / .2), fill("#FFF3B0"))


def scene_impact(c, t, b):
    d_ = t - b["start"]
    c.drawImage(STARS, 0, 0)
    R = 430
    cx, cy = 540, 1150
    im, x0, y0 = earth_img(R, cx, cy)
    c.drawImage(im, x0, y0)
    # nuage de poussière qui s'étale
    u = clamp(d_ / 2.6)
    c.save()
    c.clipPath(oval(cx - R, cy - R, cx + R, cy + R), skia.ClipOp.kIntersect, True)
    dust = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((cx, cy), max(1, R * 1.4 * eout(u)), [col("#3A2E2A", .85), col("#5A4A40", .6), col("#5A4A40", 0)], [0, .7, 1]))
    c.drawRect(skia.Rect.MakeWH(W, H), dust)
    c.restore()
    for k in range(3):
        r = (R * 1.2) * eout(clamp((d_ - k * .25) / 1.4))
        c.drawCircle(cx, cy, r, line("#FFE14D", 16 * (1 - clamp((d_ - k * .25) / 1.4)), .9))
    fl = clamp(1 - d_ / .45)
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", fl))
    text(c, "YUCATÁN", cx, cy + R + 90, 56, "#FFFFFF", INK, 8, a=clamp((d_ - .6) / .2))
    if d_ > 1.6:
        # le seul survivant visible : un petit oiseau
        bird(c, 860, 900 - 20 * math.sin(t * 3), .8, t)
        if d_ > 2.2:
            bubble(c, 860, 760, "cui.", 46, back((d_ - 2.2) / .16), 3)


# ---------------------------------------------------------------- HUD, légende, carton
def heat_c(u):
    stops = [(0, "#59E36A"), (.3, "#D7F03A"), (.55, "#FFC531"), (.8, "#FF7A1F"), (.97, "#FF2E2E"), (1, "#FF2EA6")]
    u = clamp(u)
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if a <= u <= b:
            return hexmix(ca, cb, (u - a) / (b - a))
    return "#FF2EA6"


def ans_txt(y):
    if y < .5:
        return "0 AN"
    if y < 1.5:
        return "1 AN"
    if y < 999999.5:
        return "%s ANS" % nb(round(y))
    return "%s MILLIONS D'ANNÉES" % mill(y)


assert ans_txt(saut(17)) == "65 536 ANS" and ans_txt(saut(27)) == "67,1 MILLIONS D'ANNÉES" and ans_txt(IMPACT) == "66,0 MILLIONS D'ANNÉES"


def hud(c, t, b):
    y = phys_at(t)
    key = b["key"]
    colr = heat_c(math.log10(max(y, 1)) / 7.83)
    d_ = t - b["start"]
    pop_ = 1 + .14 * (1 - eout(d_ / .22)) if b["p1"] != b["p0"] and key not in ("sieste",) else 1.0
    c.save()
    c.translate(540, 262)
    c.scale(pop_, pop_)
    pan = rrect(-420, -135, 420, 135, 44)
    c.drawPath(pan, fill("#14121C", .94))
    c.drawPath(pan, line(colr, 8))
    head = "MICHEL EST REMONTÉ DE"
    big = ans_txt(y)
    if key == "sieste":
        low = "SIESTE EN COURS…"
    elif key in ("retour", "fin") or y < .5:
        low = "ANNÉE 2026" if (y < .5) else "RETOUR VERS 2026…"
    elif key in ("roche", "pousse", "impact"):
        low = "IMPACT : IL Y A ~66 MILLIONS D'ANS"
    else:
        n = int(math.floor(math.log2(max(y, 1)) + 1e-9)) + 1
        if b["p1"] > b["p0"] and key != "montage":
            n = int(round(math.log2(b["p1"]))) + 1      # le saut en cours
        low = "SAUT N° %d" % n
        if y < 1e5 and y >= .5:
            low += " · " + annee(round(y)).upper()
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


CARD_LINES = ("Très approximatif : le voyage dans le temps n'existe pas.",
              "Saut n : 2^(n-1) ans. Saut 27 : 67 108 864 ans.",
              "Astéroïde : il y a ~66 millions d'années (environ 10 km).",
              "T. rex : de 68 à 66 millions d'années (NHM, Londres).",
              "Grande pyramide : achevée vers 2560 av. J.-C.",
              "Néandertal : jusqu'à ~40 000 ans. Homo sapiens : ~300 000 ans.",
              "Les oiseaux sont des dinosaures (AMNH).",
              "Michel nie tout.")


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
    text(c, "GÉRARD CACHE LES VERRES.", 0, 128, fit("GÉRARD CACHE LES VERRES.", 86, 1000), "#FFD93B")
    c.restore()
    a = clamp((d_ - .5) / .25)
    for i, l in enumerate(CARD_LINES):
        text(c, l, 540, 1000 + i * 62, fit(l, 44, 960), "#A9A6BC", a=a)


SCN = dict(salon=scene_salon, chateau=scene_chateau, egypte=scene_egypte, glace=scene_glace, grotte=scene_grotte,
           savane=scene_savane, foret=scene_foret, dino=scene_dino, espace=scene_espace, impact=scene_impact)


def shake_amp(t):
    amp = 0
    for key, a0, dur, A in (("impact", 0, .9, 22), ("glace", 2.45, .4, 10), ("fin", 2.5, .3, 6), ("an1", 2.1, .3, 6)):
        d_ = t - K[key] - a0
        if 0 <= d_ < dur:
            amp = max(amp, A * (1 - d_ / dur))
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


_sp = [K["an1024"], K["neand"], K["dino"], K["roche"], K["retour"], CARD, END]
SPL = [("s_%d" % i, a, z) for i, (a, z) in enumerate(zip([0] + _sp, _sp))]


def png(t, path):
    from PIL import Image
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    s = skia.Surface(arr)
    with s as c:
        frame(c, t)
    Image.fromarray(arr[..., :3]).save(path)


if __name__ == "__main__":
    print("durée %.1f s, carton %.1f, avance %.0f ans, âge pyramide %d ans" % (END, CARD, AVANCE, AGE_PYR))
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
