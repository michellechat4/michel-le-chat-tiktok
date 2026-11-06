"""Michel vit un milliard d'années : les descendants de Gérard le nourrissent, jusqu'à la minute de retard."""
import math, random, sys, os, subprocess
import numpy as np
import skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "moteur"))
import art
from art import (fill, line, col, hexmix, poly, rrect, oval, shape, text, jitter, clamp, lerp, eout, back,
                 draw_cat, draw_gerard, draw_couch, draw_mitt, sun_face, STARS, bubble, wrap_rich, TF, INK, W, H, FPS)

# ---------------------------------------------------------------- chiffres (calculés, pas recopiés)
GEN = 27                       # ans : 26,9 ans en moyenne (Wang et al., Science Advances 2023), arrondi
GRAMMES = 55                   # g de croquettes par jour, chat de 4 kg (ordre de grandeur, source commerciale)
REPAS_J = 2                    # hypothèse : 2 repas par jour
PYRAMIDE = 5.3e9               # kg, grande pyramide (New World Encyclopedia)
MS_SIECLE = 1.7                # ms de plus par siècle (Scientific American), extrapolé
AN = 365.25


def gerard_no(y):
    return 1 + int(y // GEN)


def kg_croquettes(y):
    return GRAMMES / 1000 * AN * y


def jour_h(y):
    return 24 + y / 100 * MS_SIECLE / 1000 / 3600


REPAS = REPAS_J * AN * 1e9
PYR_600 = kg_croquettes(6e8) / PYRAMIDE
J_900 = jour_h(9e8)
assert gerard_no(1e9) == 37037038 and gerard_no(100) == 4 and gerard_no(1000) == 38 and gerard_no(4600) == 171
assert round(REPAS / 1e9) == 730 and 2 < PYR_600 < 3 and round(J_900) == 28 and 2026 + 12000 == 14026 and 2026 + 2560 < 4600 + 20


# ---------------------------------------------------------------- chronologie
# (clé, durée, année, légende, Gérard dit, décor)
RAW = [
    ("hook", 3.0, 0, "CE CHAT VA VIVRE | *1 MILLIARD D'ANNÉES.*", None, "salon"),
    ("regle", 2.8, 0, "Règle : Michel ne meurt jamais. | *Gérard, si.*", "Pardon ?", "salon"),
    ("repas", 2.8, 0, "Michel mange à *7 h 02.* | Pas 7 h 03.", None, "salon"),
    ("test", 3.3, 26, "An 26. Gérard est vieux. | *Il rédige son testament.*", None, "test"),
    ("fils", 3.0, 27, "Le n° 2 hérite de la gamelle. | *Et de la moustache.*", None, "fils"),
    ("nom", 3.2, 100, "Le n° 4 s'appelle Thomas. | *Trop long. Ce sera Gérard.*", "C'est Thomas.", "salon"),
    ("oort", 3.0, 300, "An 300. La sonde Voyager 1 | atteint le *nuage d'Oort.*", None, "oort"),
    ("mur", 3.0, 1000, "An 1 000. *38 Gérard.* | Le couloir des portraits déborde.", None, "mur"),
    ("pyr", 3.0, 4600, "An 4 600 : il a l'âge | de la *grande pyramide.*", "On est 171.", "pyr"),
    ("vega", 3.2, 12000, "An 12 000 : l'étoile polaire change. | *Pas l'heure du repas.*", None, "vega"),
    ("ice", 3.2, 50000, "An 50 000 : ère glaciaire. | Gérard *dégivre la gamelle.*", None, "ice"),
    ("betel", 3.2, 100000, "Bételgeuse explose. | *Visible en plein jour.* Michel dort.", None, "betel"),
    ("evo", 3.4, 1e6, "An 1 million. Les Gérard évoluent : | *4 bras pour ouvrir les boîtes.*", None, "evo"),
    ("dino", 3.4, 66e6, "An 66 millions : aussi loin | que les dinosaures, *dans l'autre sens.*", None, "dino"),
    ("gal", 3.4, 230e6, "*Un tour complet de la galaxie.* | Michel n'a pas quitté le canapé.", None, "gal"),
    ("pang", 3.4, 250e6, "Un seul continent. | *Un seul magasin de croquettes.*", None, "pang"),
    ("pile", 3.4, 600e6, "Croquettes mangées, en masse : | *plus de 2 grandes pyramides.*", None, "pile"),
    ("jour", 3.4, 900e6, "Le jour dure *28 h.* | Son estomac : toujours 24 h.", None, "jour"),
    ("sun", 3.4, 1e9, "An 1 milliard. Soleil : *+10 %.* | Les océans commencent à bouillir.", None, "sun"),
    ("ult", 3.0, 1e9, "Gérard n° 37 037 038. | 8 bras. *Même moustache.*", None, "sun"),
    ("r730", 2.6, 1e9, "Repas n° *730 milliards.*", None, "sun"),
    ("retard", 2.6, 1e9, "Il arrive à… *7 h 03.*", "Pardon !", "sun"),
    ("stare", 3.2, 1e9, "Une minute. | *En un milliard d'années.*", None, "stare"),
    ("fin", 3.6, 1e9, "Michel s'en souviendra. | *Il a le temps.*", None, "fin"),
]
CARD_DUR = 3.2
BEATS = []
_t, _y = 0.0, 0.0
for key, dur, y, cap, ger, ph_ in RAW:
    BEATS.append(dict(key=key, start=_t, dur=dur, y0=_y, y1=y, cap=cap, ger=ger, ph=ph_))
    _t += dur
    _y = y
CARD = _t
END = CARD + CARD_DUR
K = {b["key"]: b["start"] for b in BEATS}
ROLL = .45                     # le compteur défile pendant ce temps au début de chaque saut
JUMPS = [b["start"] for b in BEATS if b["y1"] != b["y0"]]
FLOOR = 1565


def beat_at(t):
    cur = BEATS[0]
    for b in BEATS:
        if b["start"] <= t:
            cur = b
        else:
            break
    return cur


def year_at(t):
    b = beat_at(t)
    f = eout((t - b["start"]) / ROLL)
    if b["y1"] == b["y0"] or f >= 1:
        return b["y1"]
    if b["y0"] <= 0:
        return b["y1"] * f
    return math.exp(lerp(math.log(b["y0"]), math.log(b["y1"]), f))


def arms_at(y):
    return 2 if y < 1e6 else 4 if y < 230e6 else 6 if y < 1e9 else 8


# ---------------------------------------------------------------- petits objets
def d_gamelle(c, x, y, s=1.0, frost=False, full=True):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    shape(c, poly([(-62, -46), (62, -46), (82, 0), (-82, 0)]), "#CDEBFF" if frost else "#D9534F", 6)
    c.drawOval(skia.Rect.MakeLTRB(-60, -58, 60, -34), fill("#FFFFFF" if frost else ("#7B4A2B" if full else "#3A2418")))
    c.drawOval(skia.Rect.MakeLTRB(-60, -58, 60, -34), line(INK, 5))
    c.restore()


def ger(c, x, floor, s, t, stage=0, arms=2, suit=False, bowl=True, frost=False, scarf=False, cane=False, cans=False, vib=0.0):
    """Gérard debout, gamelle en main ; arms = nombre de bras."""
    c.save()
    c.translate(x, floor)
    c.scale(s, s)
    c.translate(-790, -1516)
    sw = "#F2F2F7" if suit else "#3F6FD8"
    # bras supplémentaires, derrière le torse
    extra = arms - 2
    for i in range(extra):
        sg = -1 if i % 2 == 0 else 1
        lv = i // 2
        x0, y0 = 790 + sg * 96, 1160 + lv * 46
        wob = math.sin(t * 5 + i * 1.3) * 22
        hx, hy = 790 + sg * (250 + lv * 16), 1020 + lv * 150 + wob
        arm = skia.Path()
        arm.moveTo(x0, y0)
        arm.quadTo(790 + sg * 230, y0 + 50, hx, hy)
        c.drawPath(arm, line(INK, 50))
        c.drawPath(arm, line(sw, 36))
        shape(c, oval(hx - 34, hy - 34, hx + 34, hy + 34), "#F2F2F7" if suit else "#F7C7A0", 6)
        if cans:
            shape(c, rrect(hx - 30, hy - 84, hx + 30, hy - 18, 8), "#C9CED8", 5)
            c.drawRect(skia.Rect.MakeLTRB(hx - 29, hy - 66, hx + 29, hy - 36), fill("#FFE14D"))
    draw_gerard(c, stage, t, suit, vib, True)
    if scarf:
        shape(c, rrect(698, 1078, 882, 1136, 24), "#D9534F", 6)
        shape(c, rrect(800, 1110, 862, 1250, 16), "#D9534F", 6)
    if cane:
        c.drawLine(930, 1240, 950, 1510, line(INK, 18))
        c.drawLine(930, 1240, 950, 1510, line("#9B6A3C", 9))
    if bowl:
        # deux bras vers l'avant, gamelle tenue
        for sg in (-1, 1):
            arm = skia.Path()
            arm.moveTo(790 + sg * 96, 1160)
            arm.quadTo(790 + sg * 124, 1260, 790 + sg * 60, 1272)
            c.drawPath(arm, line(INK, 56))
            c.drawPath(arm, line(sw, 42))
        d_gamelle(c, 790, 1290, 1.25, frost)
    c.restore()


def couch(c, t, mood="bliss", x=540, floor=FLOOR, s=.8, cat=True):
    c.save()
    c.translate(x, floor)
    c.scale(s, s)
    c.translate(-570, -1495)
    draw_couch(c)
    if cat:
        draw_cat(c, 360, 1312, 1.0, t, mood, 0)
    c.restore()


def hello(t, b, delay=0.0, x0=1320, x1=800, d=.5):
    return lerp(x0, x1, eout((t - b["start"] - delay) / d))


def gerbub(c, t, b, x, y):
    if not b["ger"]:
        return
    f = skia.Font(TF, 50)
    w = f.measureText(b["ger"])
    xx = clamp(x - 20, w / 2 + 44, W - w / 2 - 44)
    bubble(c, xx, y, b["ger"], 50, back((t - b["start"] - .35) / .16), 2)


def digi(c, x, y, s, label, colr="#59E36A", a=1.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    shape(c, rrect(-132, -58, 132, 58, 16), "#14121C", 7, a)
    text(c, label, 0, 24, 66, colr, a=a)
    c.restore()


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


def portrait(c, x, y, s, no, t=0.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    shape(c, rrect(-92, -118, 92, 118, 8), "#C9962E", 8)
    c.drawRect(skia.Rect.MakeLTRB(-72, -98, 72, 98), fill("#E8D9B8"))
    c.drawRect(skia.Rect.MakeLTRB(-72, -98, 72, 98), line(INK, 4))
    # buste
    shape(c, rrect(-58, 44, 58, 104, 22), "#3F6FD8", 5)
    shape(c, oval(-52, -66, 52, 54), "#F7C7A0", 5)
    p = skia.Path()
    p.moveTo(-48, -22)
    p.quadTo(-38, -78, 4, -72)
    p.quadTo(46, -70, 50, -20)
    p.quadTo(14, -44, -48, -22)
    p.close()
    shape(c, p, "#8A8F9C", 4)
    for sg in (-1, 1):
        c.drawCircle(sg * 21, -10, 15, line(INK, 4))
        c.drawCircle(sg * 21, -10, 3.5, fill(INK))
    m = skia.Path()
    m.moveTo(0, 12)
    m.quadTo(-20, 8, -34, 24)
    m.quadTo(-16, 28, 0, 20)
    m.quadTo(16, 28, 34, 24)
    m.quadTo(20, 8, 0, 12)
    m.close()
    c.drawPath(m, fill("#6A6470"))
    shape(c, rrect(-52, 76, 52, 112, 6), "#FFF5E0", 3)
    text(c, "N° %d" % no, 0, 104, 28, INK)
    c.restore()


def pip(c, t, x, y, label=None, r=120, mood="bliss"):
    """Médaillon : Michel, indifférent."""
    c.drawCircle(x, y, r, fill("#F7DDAE"))
    c.save()
    pp = skia.Path()
    pp.addCircle(x, y, r)
    c.clipPath(pp, skia.ClipOp.kIntersect, True)
    draw_cat(c, x, y + r * .95, r / 215, t, mood, 0)
    c.restore()
    c.drawCircle(x, y, r, line(INK, 8))
    c.drawCircle(x, y, r - 7, line("#FFE14D", 5))
    if label:
        text(c, label, x, y + r + 58, 44, "#FFFFFF", INK, 9)


# ---------------------------------------------------------------- décors
def scene_salon(c, t, b):
    key = b["key"]
    wall(c)
    window(c, 90, 640)
    txt = "7 h 02"
    digi(c, 800, 730, 1.0 if key != "repas" else lerp(1.0, 1.35, eout((t - b["start"]) / .35)), txt)
    couch(c, t, "open" if key in ("repas", "regle") else "bliss")
    if key == "hook":
        # Gérard, l'air de rien, sur le canapé
        c.save()
        c.translate(540, FLOOR)
        c.scale(.8, .8)
        c.translate(-570, -1495)
        draw_gerard(c, 0, t)
        c.restore()
    elif key == "regle":
        c.save()
        c.translate(540, FLOOR)
        c.scale(.8, .8)
        c.translate(-570, -1495)
        draw_gerard(c, 2 if t - b["start"] > .3 else 0, t)
        c.restore()
        gerbub(c, t, b, 760, 1000)
    elif key == "repas":
        gx = hello(t, b, .15)
        ger(c, gx, FLOOR + 14, .8, t, 0)
    elif key == "nom":
        gx = hello(t, b, 0)
        ger(c, gx, FLOOR + 14, .8, t, 1)
        gerbub(c, t, b, gx, 1040)
        if t - b["start"] > 1.5:
            d_ = t - b["start"] - 1.5
            s_ = back(d_ / .15)
            c.save()
            c.translate(gx, FLOOR - 165)
            c.rotate(-6)
            c.scale(s_, s_)
            shape(c, rrect(-150, -36, 150, 36, 8), "#FFFFFF", 6)
            text(c, "GÉRARD", 0, 20, 52, "#D9534F")
            c.restore()


def scene_test(c, t, b):
    wall(c)
    window(c, 90, 640)
    couch(c, t, "open")
    d_ = t - b["start"]
    ger(c, 850, FLOOR + 14, .62, t, 1, bowl=False, cane=True)
    # le testament, déroulé
    u = eout(d_ / .5)
    c.save()
    c.translate(420, 980)
    c.rotate(-2.5)
    h_ = lerp(40, 330, u)
    shape(c, rrect(-310, -h_, 310, h_, 12), "#FFF5E0", 8)
    c.save()
    c.clipPath(skia.Path().addRect(skia.Rect.MakeLTRB(-310, -h_, 310, h_)), skia.ClipOp.kIntersect, True)
    text(c, "TESTAMENT", 0, -226, 58, "#D9534F")
    c.drawLine(-240, -196, 240, -196, line(INK, 4))
    text(c, "1. Nourrir Michel.", 0, -112, 56, INK)
    text(c, "2. À 7 h 02.", 0, -20, 56, INK)
    if d_ > 1.3:
        text(c, "3. PAS à 7 h 03.", 0, 72, 56, "#D9534F", a=clamp((d_ - 1.3) / .2))
    if d_ > 2.1:
        text(c, "Transmettre.", 0, 164, 50, INK, a=clamp((d_ - 2.1) / .2))
        text(c, "Bon courage.", 0, 240, 40, "#7B4A2B", a=clamp((d_ - 2.1) / .2))
    c.restore()
    c.restore()


def scene_fils(c, t, b):
    wall(c)
    window(c, 90, 640)
    digi(c, 800, 730, 1.0, "7 h 02")
    couch(c, t, "bliss")
    d_ = t - b["start"]
    ox = lerp(800, 1400, eout((d_ - .1) / 1.0))
    ger(c, ox, FLOOR + 14, .8, t, 0, bowl=False, cane=True)
    nx = lerp(1400, 800, eout((d_ - .7) / .7))
    ger(c, nx, FLOOR + 14, .8, t, 1)
    if d_ > 1.5:
        bubble(c, clamp(nx, 150, 860), 1040, "N° 2", 56, back((d_ - 1.5) / .16), -2, color="#FFE14D")


def scene_oort(c, t, b):
    c.drawImage(STARS, 0, 0)
    d_ = t - b["start"]
    # Soleil minuscule, nuage d'Oort en pointillé
    c.drawCircle(90, 1180, 16, fill("#FFF3B5"))
    r = random.Random(5)
    for i in range(420):
        an = r.uniform(-.75, .75)
        rad = r.uniform(830, 1300)
        x = 90 + math.cos(an) * rad
        y = 1180 + math.sin(an) * rad
        c.drawCircle(x, y, r.uniform(1.5, 4), fill("#CFE6FF", .55))
    text(c, "NUAGE D'OORT", 830, 900, 50, "#CFE6FF", INK, 9)
    # la sonde arrive
    x = lerp(300, 840, eout(d_ / 2.2))
    y = 1180 + math.sin(t) * 4
    c.save()
    c.translate(x, y)
    c.rotate(-8)
    c.drawLine(-120, 0, 70, 0, line(INK, 14))
    c.drawLine(-120, 0, 70, 0, line("#B8BCC8", 7))
    shape(c, rrect(-26, -24, 26, 24, 5), "#C9962E", 5)
    d = skia.Path()
    d.addArc(skia.Rect.MakeLTRB(-96, -96, 96, 96), 215, 110)
    d.close()
    shape(c, d, "#F2F2F7", 6)
    c.restore()
    text(c, "VOYAGER 1", x, y + 112, 44, "#FFE14D", INK, 9)
    pip(c, t, 230, 1540, None, 130, "open")
    if d_ > 1.5:
        bubble(c, 390, 1400, "mrrp ? 7 h ?", 44, back((d_ - 1.5) / .16), -3)


def scene_mur(c, t, b):
    wall(c, "#E8D9B8", "#DCCBA6")
    d_ = t - b["start"]
    sc = lerp(0, 3200, d_ / b["dur"])
    n = 38
    cols = (n + 2) // 3
    for i in range(n):
        ix = i // 3
        iy = i % 3
        x = 140 + ix * 245 + iy * 40 - sc
        y = 760 + iy * 300
        if -120 < x < W + 120:
            portrait(c, x, y, 1.05, i + 1)
    # Michel passe, sans regarder
    bob = abs(math.sin(t * 6)) * 12
    draw_cat(c, 540, FLOOR + 130 - bob, .5, t, "bliss", 0)


def scene_pyr(c, t, b):
    sky = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 0), (0, 1400)], [col("#3FA9F0"), col("#FFE9B8")]))
    c.drawRect(skia.Rect.MakeWH(W, H), sky)
    d_ = t - b["start"]
    c.drawCircle(860, 720, 70, fill("#FFF3B5"))
    shape(c, poly([(60, 1380), (400, 780), (760, 1380)]), "#D9B46A", 7)
    c.drawPath(poly([(400, 780), (760, 1380), (500, 1380)]), fill("#B8904F"))
    for k in range(1, 10):
        yy = 780 + k * 60
        half = (yy - 780) * .585
        c.drawLine(400 - half, yy, 400 + half, yy, line(INK, 3, .3))
    c.drawRect(skia.Rect.MakeLTRB(0, 1370, W, H), fill("#EBCB84"))
    c.drawLine(0, 1370, W, 1370, line(INK, 6))
    couch(c, t, "bliss", 500, FLOOR, .68)
    gx = hello(t, b, 0, 1300, 860)
    ger(c, gx, FLOOR + 14, .68, t, 1)
    gerbub(c, t, b, gx - 60, 1090)


def scene_vega(c, t, b):
    c.drawImage(STARS, 0, 0)
    d_ = t - b["start"]
    # toit
    c.drawRect(skia.Rect.MakeLTRB(0, FLOOR - 10, W, H), fill("#2B2A3B"))
    c.drawLine(0, FLOOR - 10, W, FLOOR - 10, line(INK, 7))
    couch(c, t, "open", 430, FLOOR, .62)
    ger(c, 860, FLOOR + 14, .62, t, 1)
    # étoiles
    u = eout((d_ - .5) / .6)
    px, py = 280, 760
    vx, vy = 780, 900
    c.drawCircle(px, py, 12, fill("#CFE6FF", lerp(1, .35, u)))
    text(c, "ÉTOILE POLAIRE", px, py + 66, 38, "#CFE6FF", INK, 7, a=lerp(1, .5, u))
    for k in range(6):
        an = k * math.pi / 3 + t * .4
        rr = 24 + 20 * u + math.sin(t * 5) * 4
        c.drawLine(vx, vy, vx + math.cos(an) * rr, vy + math.sin(an) * rr, line("#FFE14D", 5))
    c.drawCircle(vx, vy, 16 + 4 * u, fill("#FFF3B5"))
    if d_ > .5:
        text(c, "VÉGA", vx, vy + 76, 56, "#FFE14D", INK, 9, a=u)
        if u > .4:
            # flèche Nord qui change d'étoile
            mid = skia.Path()
            mid.moveTo(px + 60, py - 10)
            mid.quadTo(530, 640, vx - 40, vy - 30)
            c.drawPath(mid, line("#FFFFFF", 6, .7))
            text(c, "NORD", 530, 640, 44, "#FFFFFF", INK, 8)


def snow(c, t, seed=9, n=70, wind=-35):
    r = random.Random(seed)
    for i in range(n):
        x0, sp, ph, rad = r.uniform(0, W + 200), r.uniform(70, 160), r.uniform(0, 1500), r.uniform(4, 10)
        y = 560 + ((t * sp + ph) % 1200)
        c.drawCircle((x0 + t * wind + math.sin(t + i) * 14) % W, y, rad, fill("#FFFFFF", .92))


def scene_ice(c, t, b):
    sky = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 500), (0, 1400)], [col("#8FC4E8"), col("#EAF8FF")]))
    c.drawRect(skia.Rect.MakeWH(W, H), sky)
    shape(c, poly([(-20, 1240), (150, 860), (300, 1100), (460, 760), (680, 1160), (850, 900), (1100, 1240)]), "#D6ECF8", 6)
    c.drawRect(skia.Rect.MakeLTRB(0, 1230, W, H), fill("#F2FAFF"))
    c.drawLine(0, 1230, W, 1230, line(INK, 6))
    couch(c, t, "bliss", 440, FLOOR, .64)
    # glaçons au bord du canapé
    for x in range(120, 760, 44):
        c.drawPath(poly([(x, FLOOR - 160), (x + 30, FLOOR - 160), (x + 15, FLOOR - 112 - (x % 3) * 12)]), fill("#CDEBFF"))
    d_ = t - b["start"]
    gx = hello(t, b, 0, 1300, 830)
    ger(c, gx, FLOOR + 14, .7, t, 3 if d_ > 1.0 else 1, frost=True, scarf=True, vib=2.0)
    # raclette
    if d_ > .7:
        hx, hy = gx - 60 + math.sin(t * 22) * 28, FLOOR - 190
        c.drawLine(hx, hy - 60, hx + 60, hy - 130, line(INK, 18))
        c.drawLine(hx, hy - 60, hx + 60, hy - 130, line("#FFE14D", 9))
        shape(c, rrect(hx - 44, hy - 66, hx + 26, hy - 46, 4), "#3A3A48", 4)
    snow(c, t)


def scene_betel(c, t, b):
    d_ = t - b["start"]
    sky = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 400), (0, 1400)], [col("#5CB8F2"), col("#D3F1FF")]))
    c.drawRect(skia.Rect.MakeWH(W, H), sky)
    c.drawRect(skia.Rect.MakeLTRB(0, 1370, W, H), fill("#7CC46E"))
    c.drawLine(0, 1370, W, 1370, line(INK, 6))
    bx, by = 780, 800
    u = eout((d_ - .2) / .5)
    for k in range(8):
        an = k * math.pi / 4 + t * .2
        rr = lerp(10, 150 + (k % 2) * 90, u)
        c.drawLine(bx, by, bx + math.cos(an) * rr, by + math.sin(an) * rr, line("#FFFFFF", 10, .9))
    c.drawCircle(bx, by, lerp(6, 44, u), fill("#FFFFFF"))
    c.drawCircle(bx, by, lerp(10, 84, u), fill("#FFE14D", .4))
    if u > .3:
        text(c, "BÉTELGEUSE", bx, by + 180, 48, "#FFFFFF", INK, 9, a=u)
    couch(c, t, "bliss", 500, FLOOR, .68)
    gx = 860
    ger(c, gx, FLOOR + 14, .66, t, 2 if d_ > .4 else 0)
    # Zzz
    for i in range(3):
        ph = (t * .6 + i / 3) % 1
        text(c, "z", 340 + ph * 90 + i * 12, 1150 - ph * 170, 42 + i * 8, "#FFFFFF", INK, 7, a=1 - ph)
    if d_ < .3:
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", (.3 - d_) / .3 * .85))


def scene_evo(c, t, b):
    wall(c, "#D7F0E4", "#C5E6D6", "#5E616F")
    window(c, 90, 640, sky="#BCE9D2")
    couch(c, t, "open")
    d_ = t - b["start"]
    gx = hello(t, b, 0, 1320, 790)
    ger(c, gx, FLOOR + 14, .8, t, 1, arms=4, cans=True)
    if d_ > 1.2:
        bubble(c, clamp(gx, 180, 860), 1000, "2 × plus vite", 48, back((d_ - 1.2) / .16), -2, color="#FFE14D")


def dinosaure(c, x, y, s, t):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    G, D = "#6BB36E", "#4E8E58"
    tail = poly([(-30, -180), (-230, -130), (-280, -110), (-30, -110)])
    shape(c, tail, G, 7)
    for lx in (-30, 50):
        shape(c, rrect(lx, -110, lx + 54, 0, 16), D, 6)
        shape(c, rrect(lx - 10, -22, lx + 70, 4, 10), D, 5)
    shape(c, oval(-110, -270, 120, -80), G, 8)
    shape(c, rrect(50, -390, 120, -220, 26), G, 7)
    shape(c, rrect(40, -450, 200, -350, 34), G, 8)
    c.drawLine(120, -393, 196, -393, line(INK, 6))
    # petits bras
    c.drawLine(100, -210, 150, -180, line(INK, 18))
    c.drawLine(100, -210, 150, -180, line(D, 10))
    # œil en X (très bien, dans l'autre sens)
    c.drawLine(92, -430, 118, -404, line(INK, 7))
    c.drawLine(118, -430, 92, -404, line(INK, 7))
    c.restore()


def scene_dino(c, t, b):
    sky = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 500), (0, 1250)], [col("#F7B267"), col("#FFE9B8")]))
    c.drawRect(skia.Rect.MakeWH(W, H), sky)
    c.drawRect(skia.Rect.MakeLTRB(0, 1320, W, H), fill("#C9A66B"))
    c.drawLine(0, 1320, W, 1320, line(INK, 6))
    d_ = t - b["start"]
    dinosaure(c, 225, 1320, .86, t)
    # l'astéroïde tombe sur lui
    if d_ < 2.6:
        ax, ay = lerp(560, 300, d_ / 2.6), lerp(620, 860, d_ / 2.6)
        c.drawLine(ax, ay, ax + 120, ay - 110, line("#FF8A1F", 22, .75))
        shape(c, oval(ax - 34, ay - 34, ax + 34, ay + 34), "#6E7486", 6)
    couch(c, t, "bliss", 800, 1320, .34)
    ger(c, 945, 1326, .34, t, 1, arms=4)
    # la frise
    yb = 1460
    c.drawLine(120, yb, 960, yb, line(INK, 24))
    c.drawLine(120, yb, 960, yb, line("#FFE14D", 12))
    for x, lab, top in ((120, "- 66 M", False), (540, "AUJOURD'HUI", True), (960, "+ 66 M", False)):
        c.drawLine(x, yb - 34, x, yb + 34, line(INK, 14))
        c.drawLine(x, yb - 34, x, yb + 34, line("#FFFFFF", 6))
        text(c, lab, clamp(x, 130, 950), yb + 88, 46, "#FFFFFF", INK, 9)


_GAL = None


def galaxy_img():
    global _GAL
    if _GAL is None:
        s = skia.Surface(1000, 1000)
        with s as cv:
            cv.clear(skia.ColorSetARGB(0, 0, 0, 0))
            r = random.Random(3)
            for i in range(9000):
                arm = i % 4
                rr = r.random() ** .7 * 470 + 22
                an = rr / 95 + arm * math.pi / 2 + r.gauss(0, .24)
                x, y = 500 + rr * math.cos(an), 500 + rr * math.sin(an)
                hot = 1 - rr / 500
                cc = hexmix("#9CC4FF", "#FFE9B8", hot)
                cv.drawCircle(x, y, r.uniform(.8, 3.2), fill(cc, r.uniform(.35, .95)))
            cv.drawCircle(500, 500, 70, fill("#FFF3B5", .85))
            cv.drawCircle(500, 500, 110, fill("#FFE9B8", .25))
        _GAL = s.makeImageSnapshot()
    return _GAL


def couch_mini(c, x, y, s, t):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.translate(-570, -1300)
    draw_couch(c)
    draw_cat(c, 360, 1312, 1.0, t, "bliss", 0)
    c.restore()


def scene_gal(c, t, b):
    c.drawImage(STARS, 0, 0)
    d_ = t - b["start"]
    cx, cy = 540, 1160
    c.save()
    c.translate(cx, cy)
    c.rotate(-math.degrees(d_ * .07))
    c.drawImage(galaxy_img(), -500, -500)
    c.restore()
    R = 345
    pr = clamp(d_ / (b["dur"] - .4))
    a0 = -math.pi * .7
    an = a0 + pr * 2 * math.pi
    tr = skia.Path()
    tr.addArc(skia.Rect.MakeLTRB(cx - R, cy - R, cx + R, cy + R), math.degrees(a0), pr * 359.9)
    c.drawPath(tr, line("#FFE14D", 8))
    x, y = cx + R * math.cos(an), cy + R * math.sin(an)
    couch_mini(c, x, y, .17, t)
    text(c, "MICHEL", x, y - 90, 46, "#FFE14D", INK, 9)
    text(c, "230 millions d'années", cx, 1730, 54, "#FFFFFF", INK, 10)


def scene_pang(c, t, b):
    c.drawImage(STARS, 0, 0)
    d_ = t - b["start"]
    cx, cy, R = 540, 1140, 450
    c.drawCircle(cx, cy, R, fill("#2B86DE"))
    # continent unique
    r = random.Random(12)
    amp = [(r.uniform(.04, .1), k, r.uniform(0, 6.28)) for k in (2, 3, 5, 7, 11)]
    pts = []
    for i in range(120):
        th = i / 120 * 2 * math.pi
        rr = 300 * (1 + sum(a * math.sin(k * th + p) for a, k, p in amp))
        pts.append((cx + rr * 1.16 * math.cos(th), cy + rr * .72 * math.sin(th)))
    shape(c, poly(pts), "#D9A85A", 7)
    shape(c, oval(cx - 220, cy - 100, cx + 220, cy + 120), "#EBC070", 0)
    text(c, "PANGÉE ULTIMA", cx, cy + 16, 54, "#FFFFFF", INK, 10)
    c.drawCircle(cx, cy, R, line(INK, 8))
    # chemin de Gérard
    x0, x1 = cx - 275, cx + 275
    yy = cy + 170
    for i in range(14):
        xx = lerp(x0 + 50, x1 - 80, i / 13)
        if i % 2 == 0:
            c.drawLine(xx, yy, xx + 18, yy, line("#FFFFFF", 7))
    u = clamp((d_ - .2) / (b["dur"] - .6))
    ger(c, lerp(x0 + 60, x1 - 100, u), yy + 22, .2, t, 1, arms=6, bowl=False)
    couch_mini(c, x0, yy - 45, .15, t)
    shape(c, rrect(x1 - 85, yy - 85, x1 + 85, yy + 20, 6), "#FFFFFF", 5)
    shape(c, rrect(x1 - 95, yy - 120, x1 + 95, yy - 82, 6), "#D9534F", 5)
    text(c, "CROQUETTES", x1, yy - 90, 28, "#FFFFFF")
    # chaleur
    text(c, "Intérieur : 50 à 65 °C", cx, cy - 170, 44, "#FFE14D", INK, 9)


_KIB = None


def scene_pile(c, t, b):
    global _KIB
    sky = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 500), (0, 1400)], [col("#F7B267"), col("#FFE9B8")]))
    c.drawRect(skia.Rect.MakeWH(W, H), sky)
    c.drawRect(skia.Rect.MakeLTRB(0, 1480, W, H), fill("#D9B46A"))
    c.drawLine(0, 1480, W, 1480, line(INK, 6))
    d_ = t - b["start"]
    # à l'échelle, même densité supposée : la pile fait 2,27 pyramides en volume, soit 1,31 fois leur taille
    PH, PW = 300, 142
    for x in (150, 435):
        shape(c, poly([(x - PW, 1480), (x, 1480 - PH), (x + PW, 1480)]), "#D9B46A", 6)
    text(c, "2 PYRAMIDES", 292, 1560, 46, "#FFFFFF", INK, 9)
    u = eout(d_ / 1.4)
    px, base = 838, 1480
    kk = PYR_600 ** (1 / 3)
    hh, ww = PH * kk * u, PW * kk * u
    if _KIB is None:
        r = random.Random(4)
        _KIB = [(r.uniform(-1, 1), r.uniform(0, 1), r.uniform(9, 15), r.uniform(0, 180), r.choice(("#7B4A2B", "#8A5A36", "#6B4324"))) for _ in range(700)]
    pile = poly([(px - ww, base), (px, base - hh), (px + ww, base)])
    shape(c, pile, "#6B4324", 7)
    c.save()
    c.clipPath(pile, skia.ClipOp.kIntersect, True)
    for ux, uy, rs, rot, cc in _KIB:
        xx = px + ux * ww
        yy = base - uy * hh
        c.drawCircle(xx, yy, rs, fill(cc))
        c.drawCircle(xx, yy, rs, line(INK, 2.5))
    c.restore()
    text(c, "1 CHAT", px, 1560, 46, "#FFE14D", INK, 9)
    if u > .1:
        draw_cat(c, px, base - hh + 10, .44, t, "open", 0)


def scene_jour(c, t, b):
    c.drawImage(STARS, 0, 0)
    d_ = t - b["start"]
    cx, cy, R = 540, 1110, 400
    shape(c, oval(cx - R, cy - R, cx + R, cy + R), "#FFF5E0", 12)
    for h_ in range(28):
        an = -math.pi / 2 + h_ / 28 * 2 * math.pi
        c.drawLine(cx + (R - 26) * math.cos(an), cy + (R - 26) * math.sin(an), cx + (R - 8) * math.cos(an), cy + (R - 8) * math.sin(an), line(INK, 6))
        if h_ % 2 == 0:
            lab = "28" if h_ == 0 else str(h_)
            hot = h_ == 24
            text(c, lab, cx + (R - 74) * math.cos(an), cy + (R - 74) * math.sin(an) + 18, 56 if hot else 46, "#D9534F" if hot else INK)
    hour = lerp(14, 26.5, clamp(d_ / (b["dur"] - .3)))
    an = -math.pi / 2 + hour / 28 * 2 * math.pi
    c.drawLine(cx, cy, cx + (R - 130) * math.cos(an), cy + (R - 130) * math.sin(an), line(INK, 16))
    c.drawCircle(cx, cy, 22, fill(INK))
    draw_cat(c, 215, 1650, .55, t, "open" if hour > 23 else "bliss", 0)
    if hour > 24:
        bubble(c, 340, 1420, "MIAOU", 62, back((hour - 24) / .3), -4, color="#FFE14D")
    ger(c, 880, 1720, .46, t, 3 if hour > 24 else 0, arms=6, bowl=False)


def sun_bg(c, t):
    sky = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 400), (0, 1330)], [col("#F2542D"), col("#FFC531")]))
    c.drawRect(skia.Rect.MakeWH(W, H), sky)
    sun_face(c, 770, 840, 200, t, True)
    # mer qui fume, au loin
    c.drawRect(skia.Rect.MakeLTRB(0, 1230, W, 1330), fill("#2B86DE"))
    r = random.Random(7)
    for i in range(16):
        x0 = r.uniform(0, W)
        ph = (t * r.uniform(.35, .7) + r.random()) % 1
        c.drawCircle(x0 + math.sin(t + i) * 12, 1250 - ph * 210, 12 + ph * 32, fill("#FFFFFF", .55 * (1 - ph)))
    c.drawRect(skia.Rect.MakeLTRB(0, 1330, W, H), fill("#C97E3A"))
    c.drawLine(0, 1330, W, 1330, line(INK, 6))
    r = random.Random(2)
    for i in range(16):
        x0, y0 = r.uniform(0, W), r.uniform(1350, H)
        pts = [(x0, y0)]
        for k in range(3):
            pts.append((pts[-1][0] + r.uniform(40, 110), pts[-1][1] + r.uniform(-24, 24)))
        c.drawPath(poly(pts, False), line(INK, 4, .5))


def scene_sun(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    sun_bg(c, t)
    couch(c, t, "open" if key in ("retard", "r730") else "bliss", 450, FLOOR, .68)
    if key == "sun":
        ger(c, hello(t, b, 0, 1300, 840), FLOOR + 14, .7, t, 2, arms=8, suit=True)
    elif key == "ult":
        c.save()
        s_ = lerp(1, 1.25, eout(d_ / 2.5))
        c.translate(780, FLOOR)
        c.scale(s_, s_)
        c.translate(-780, -FLOOR)
        ger(c, 780, FLOOR + 14, .74, t, 0, arms=8, suit=True)
        c.restore()
    elif key == "r730":
        ger(c, 800, FLOOR + 14, .7, t, 1, arms=8, suit=True)
        digi(c, 270, 720, 1.2, "7 h 02")
    elif key == "retard":
        ger(c, 800, FLOOR + 14, .7, t, 2 if d_ < .5 else 3, arms=8, suit=True, vib=2.0)
        lab = "7 h 02" if d_ < .25 else "7 h 03"
        s_ = 1.2 if d_ < .25 else 1.6 + .08 * math.sin(t * 16)
        digi(c, 270, 720, s_, lab, "#59E36A" if d_ < .25 else "#FF2E2E")
        if d_ >= .25:
            gerbub(c, t, b, 820, 1000)


def scene_stare(c, t, b):
    d_ = t - b["start"]
    sun_bg(c, t)
    z = lerp(1.2, 2.0, eout(d_ / 2.4))
    ger(c, 880, FLOOR + 14, .56, t, 3, arms=8, suit=True, vib=2.5)
    couch(c, t, "open", 480, FLOOR + 40, .9, cat=False)
    draw_cat(c, 430, FLOOR - 30, z, t, "open", 0)


def scene_fin(c, t, b):
    d_ = t - b["start"]
    sun_bg(c, t)
    couch(c, t, "wink" if d_ > 1.8 else "open", 400, FLOOR, .68)
    ger(c, 905, FLOOR + 14, .6, t, 3, arms=8, suit=True, vib=1.5)
    # la tablette des griefs
    u = eout((d_ - .3) / .35)
    c.save()
    c.translate(610, 1000)
    c.rotate(-3)
    c.scale(u * .86, u * .86)
    shape(c, rrect(-180, -160, 180, 160, 26), "#8E8A90", 8)
    text(c, "RETARDS", 0, -92, 54, "#FFFFFF", INK, 7)
    c.drawLine(-120, -70, 120, -70, line(INK, 5))
    if d_ > .9:
        n = 1
        text(c, str(n), 0, 72, 130, "#FFE14D", INK, 9, a=clamp((d_ - .9) / .15))
    c.restore()
    if d_ > 2.2:
        bubble(c, 220, 1100, "mrrp.", 56, back((d_ - 2.2) / .16), -3)


# ---------------------------------------------------------------- HUD, légende, carton
def heat_c(y):
    u = 0 if y < 1 else clamp(math.log10(y) / 9)
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


def age_txt(y):
    if y >= 1e9 - 1:
        return "1 MILLIARD D'ANNÉES"
    if y >= 1e6:
        v = y / 1e6
        return "%s MILLIONS D'ANNÉES" % nb(round(v)) if v >= 1.5 else "1 MILLION D'ANNÉES"
    if y < 2:
        return "%d AN" % y
    return "%s ANS" % nb(int(y))


def hud(c, t, b):
    y = year_at(t)
    colr = heat_c(y)
    d_ = t - b["start"]
    pop = 1 + .14 * (1 - eout(d_ / .22)) if b["y1"] != b["y0"] else 1.0
    c.save()
    c.translate(540, 262)
    c.scale(pop, pop)
    pan = rrect(-420, -135, 420, 135, 44)
    c.drawPath(pan, fill("#14121C", .94))
    c.drawPath(pan, line(colr, 8))
    head = "ÂGE DE MICHEL"
    big = age_txt(y)
    low = "Gérard n° %s" % nb(gerard_no(y))
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
    text(c, "LE MILLIARD SUIVANT.", 0, 128, 86, "#FFD93B")
    c.restore()
    a = clamp((d_ - .5) / .25)
    for i, l in enumerate(("Très approximatif : un Gérard tous les 27 ans, 2 repas par jour.",
                           "Soleil, durée du jour, glaciation, Bételgeuse : estimations.",
                           "Les bras supplémentaires : non sourcés.",
                           "Thomas va bien.")):
        s_ = fit(l, 36, 960)
        text(c, l, 540, 1080 + i * 54, s_, "#A9A6BC", a=a)


SCN = dict(salon=scene_salon, test=scene_test, fils=scene_fils, oort=scene_oort, mur=scene_mur, pyr=scene_pyr, vega=scene_vega, ice=scene_ice,
           betel=scene_betel, evo=scene_evo, dino=scene_dino, gal=scene_gal, pang=scene_pang, pile=scene_pile, jour=scene_jour, sun=scene_sun, stare=scene_stare, fin=scene_fin)


def shake_amp(t):
    amp = 0
    for tk in JUMPS[1:]:
        d_ = t - tk
        if 0 <= d_ < .22:
            amp = max(amp, 10 * (1 - d_ / .22))
    d_ = t - K["retard"] - .25
    if 0 <= d_ < .4:
        amp = max(amp, 26 * (1 - d_ / .4))
    return amp


def warp(c, t):
    """Stries du temps qui passe, au début de chaque saut."""
    for tk in JUMPS:
        d_ = t - tk
        if 0 <= d_ < .34:
            a = 1 - d_ / .34
            r = random.Random(int(tk * 10))
            for i in range(44):
                an = r.uniform(0, 6.283)
                r0 = r.uniform(260, 620) + d_ * 2300
                r1 = r0 + r.uniform(120, 460)
                c.drawLine(540 + math.cos(an) * r0, 1040 + math.sin(an) * r0, 540 + math.cos(an) * r1, 1040 + math.sin(an) * r1, line("#FFFFFF", r.uniform(3, 9), .75 * a))
            if d_ < .1:
                c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", .75 * (1 - d_ / .1)))


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
    warp(c, t)
    hud(c, t, b)
    caption(c, t)


_sp = [K["test"], K["oort"], K["pyr"], K["evo"], K["pang"], K["sun"], K["stare"], CARD, END]
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
    print("repas %.3g, pyramides à 600 M %.2f, jour à 900 M %.2f h" % (REPAS, PYR_600, J_900))
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
