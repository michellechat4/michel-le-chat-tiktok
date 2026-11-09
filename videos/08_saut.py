"""Le saut de Michel double à chaque fois : étagère, plafond, toit, tour Eiffel, Everest, ISS ratée de 29 km, Lune."""
import math, random, sys, os, subprocess
import numpy as np
import skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "moteur"))
import art
from art import (fill, line, col, hexmix, poly, rrect, oval, shape, text, jitter, clamp, lerp, eout, ein, back,
                 draw_cat, draw_gerard, draw_eiffel, draw_moon, draw_iss, earth_rgba, STARS, bubble, wrap_rich, TF, INK, W, H, FPS)

# ---------------------------------------------------------------- chiffres (calculés, pas recopiés)
H0 = 1.5                 # m, saut 0 ; un chat domestique saute environ 1,2 à 1,8 m (Catster, 2026)
PLAFOND = 2.5            # m, hauteur sous plafond courante (estimation, non sourcée)
ARC = 50                 # m, Arc de Triomphe (France.fr : « environ 50 mètres »)
EIFFEL = 330             # m, depuis l'antenne de 2022 (Archinect)
EVEREST = 8848.86        # m (RTBF, 2020)
AVIONS = (9200, 12200)   # m, croisière des avions de ligne (Futura)
KARMAN = 100             # km, limite conventionnelle de l'espace
ISS = 422                # km, altitude moyenne après la correction de février 2026 (Ground News / se7en)
LUNE = 384400            # km, distance moyenne Terre-Lune
V_LIB = 11.2             # km/s, vitesse de libération (Physics Factbook)
SON = 343                # m/s, vitesse du son dans l'air à 20 °C (valeur standard)
GM, RT = 3.986004418e14, 6.371e6


def hm(n):
    return H0 * 2 ** n


def v_dec(h):
    """Vitesse de décollage (m/s) pour monter à h, gravité en 1/r², sans air."""
    return math.sqrt(2 * GM * (1 / RT - 1 / (RT + h)))


def t_vol(h_target, v0):
    """Temps (s) pour atteindre l'altitude h_target en partant à v0 (intégration numérique, Terre seule)."""
    from scipy.integrate import solve_ivp
    ev = lambda t, y: y[0] - (RT + h_target)
    ev.terminal = True
    s = solve_ivp(lambda t, y: [y[1], -GM / y[0] ** 2], [0, 1e7], [RT, v0], events=ev, rtol=1e-10, atol=1)
    return s.t_events[0][0]


V13 = v_dec(hm(13)) * 3.6
V28 = v_dec(hm(28)) * 3.6
JOURS = t_vol(LUNE * 1000, v_dec(hm(28))) / 86400
assert PLAFOND < hm(1) and hm(5) < ARC < hm(6) and hm(7) < EIFFEL < hm(8)
assert hm(12) < EVEREST < hm(13) and hm(13) > AVIONS[1] and hm(16) / 1000 < KARMAN < hm(17) / 1000
assert hm(18) / 1000 < ISS < hm(19) / 1000 and round(ISS - hm(18) / 1000) == 29
assert hm(27) / 1000 < LUNE < hm(28) / 1000 and round(hm(28) / 1000) == 402653 and round(hm(29) / 1000) == 805306
assert round(V13, -1) == 1770 and V13 / 3.6 / SON > 1.4
assert round(V28, -3) == 40000 and .98 < V28 / 3.6 / 1000 / V_LIB < 1.0
assert 3.85 < JOURS < 3.95          # « presque 4 jours »

# ---------------------------------------------------------------- chronologie
# (clé, durée, saut, légende, Gérard dit, décor)
RAW = [
    ("hook", 3.0, 0, "CE CHAT VA SAUTER | *JUSQU'À LA LUNE.*", None, "salon"),
    ("regle", 3.2, 0, "Règle : à chaque saut, | il saute *deux fois plus haut.*", "Michel, non.", "salon"),
    ("s0", 3.2, 0, "Saut 0 : 1,50 m. Un vrai chat | saute *1,20 à 1,80 m.*", None, "salon"),
    ("s1", 3.0, 1, "Saut 1 : 3 m. | Le plafond fait *2,50 m.*", "MON PLAFOND !", "salon"),
    ("s2", 2.8, 2, "Saut 2 : 6 m. | *Par le toit.*", None, "maison"),
    ("s4", 2.6, 4, "Saut 4 : 24 m. | Les pigeons *s'écartent.*", None, "ville"),
    ("s6", 3.0, 6, "Saut 6 : 96 m. Par-dessus | l'*Arc de Triomphe* (50 m).", None, "paris"),
    ("s8", 3.0, 8, "Saut 8 : 384 m. | Plus haut que la *tour Eiffel.*", None, "paris"),
    ("veto", 3.0, 8, "Gérard appelle *le véto.*", "Il saute 384 m.", "salon"),
    ("s13", 3.4, 13, "Saut 13 : 12,3 km. Au-dessus | de l'*Everest* et des *avions.*", None, "ciel"),
    ("mach", 3.2, 13, "Il décolle à *1 770 km/h.* | Il passe *le mur du son.*", None, "mach"),
    ("s17", 3.0, 17, "Saut 17 : 197 km. | Michel est *dans l'espace.*", None, "espace"),
    ("s18", 3.4, 18, "Saut 18 : 393 km. Il rate | la *station spatiale* de 29 km.", None, "espace"),
    ("filet", 3.0, 18, "Gérard installe | *un filet.*", "Par sécurité.", "salon"),
    ("s28", 3.4, 28, "Saut 28 : 402 653 km. | La Lune est à *384 400 km.*", None, "lune_vol"),
    ("vit", 3.4, 28, "Il décolle à *40 000 km/h.* | Presque de quoi *quitter la Terre.*", None, "lune_vol"),
    ("voyage", 3.0, 28, "Trajet : *presque 4 jours.* | Il fait la sieste.", None, "lune_vol"),
    ("lune", 3.2, 28, "Premier chat *sur la Lune.* | Il plante *son drapeau.*", None, "lune"),
    ("croq", 3.2, 28, "Sur Terre, Gérard secoue | *la boîte de croquettes.*", None, "salon"),
    ("retour", 3.0, 28, "*Michel est déjà rentré.*", None, "salon"),
    ("fin", 3.8, 28, "Prochain saut : | *805 306 km.*", "NON.", "salon"),
]
CARD_DUR = 3.4
BEATS = []
_t, _n = 0.0, 0
for key, dur, n, cap, ger_, ph_ in RAW:
    BEATS.append(dict(key=key, start=_t, dur=dur, n0=_n, n1=n, cap=cap, ger=ger_, ph=ph_))
    _t += dur
    _n = n
CARD = _t
END = CARD + CARD_DUR
K = {b["key"]: b["start"] for b in BEATS}
JUMPS = [b["start"] for b in BEATS if b["n1"] > b["n0"]] + [K["s0"]]
JUMPS.sort()
ROLL = .7
FLOOR = 1565
RISE = .9                   # durée de la montée


def beat_at(t):
    cur = BEATS[0]
    for b in BEATS:
        if b["start"] <= t:
            cur = b
        else:
            break
    return cur


def jump_at(t):
    b = beat_at(t)
    f = eout((t - b["start"]) / ROLL)
    if b["n1"] <= b["n0"] or f >= 1:
        return b["n1"]
    return lerp(b["n0"], b["n1"], f)


def rise(d_):
    """0 → 1 pendant la montée, puis petit flottement au sommet."""
    return eout(d_ / RISE)


# ---------------------------------------------------------------- Michel en vol
def fly_cat(c, x, y, s, t, mood="open", speed=1.0, trail=True, a_trail=1.0):
    """Michel étiré vers le haut, pieds en (x, y)."""
    if trail and speed > 0:
        r = random.Random(int(t * 12))
        for i in range(7):
            dx = (i - 3) * 34 * s / .4
            ln = r.uniform(120, 260) * s / .4 * speed
            c.drawLine(x + dx, y + 20 * s / .4, x + dx, y + 20 * s / .4 + ln, line("#FFFFFF", max(2, 7 * s / .4), .75 * a_trail))
    c.save()
    c.translate(x, y)
    c.scale(1 - .08 * speed, 1 + .14 * speed)
    draw_cat(c, 0, 0, s, t, mood, 0)
    c.restore()


# ---------------------------------------------------------------- Gérard et décors (repris de la vidéo 07)
def ger(c, x, floor, s, t, stage=0, hold=None, shake=0.0):
    c.save()
    c.translate(x, floor)
    c.scale(s, s)
    c.translate(-790, -1516)
    sw = "#3F6FD8"
    draw_gerard(c, stage, t, False, 0, True)
    for sg in (-1, 1):
        arm = skia.Path()
        arm.moveTo(790 + sg * 96, 1160)
        if hold and sg == -1:
            arm.quadTo(790 - 150, 1120, 790 - 150, 1010)
        else:
            arm.quadTo(790 + sg * 130, 1250, 790 + sg * 118, 1330)
        c.drawPath(arm, line(INK, 56))
        c.drawPath(arm, line(sw, 42))
    if hold == "phone":
        shape(c, rrect(640 - 10, 940, 640 + 30, 1010, 10), "#2B2B36", 5)
    if hold == "box":
        jx = math.sin(t * 40) * 22 * shake
        c.save()
        c.translate(640 + jx, 960)
        c.rotate(math.sin(t * 40) * 8 * shake)
        shape(c, rrect(-60, -90, 60, 70, 12), "#F2C14E", 7)
        shape(c, oval(-34, -40, 34, 20), "#FFFFFF", 5)
        c.drawCircle(-10, -14, 8, fill("#9B6A3C"))
        c.drawCircle(12, -6, 8, fill("#9B6A3C"))
        c.restore()
        if shake > .5:
            for k in range(3):
                c.drawLine(560 - k * 24, 880 + k * 40, 520 - k * 24, 860 + k * 40, line(INK, 8))
                c.drawLine(720 + k * 24, 880 + k * 40, 760 + k * 24, 860 + k * 40, line(INK, 8))
    c.restore()


def gerbub(c, t, b, x, y):
    if not b["ger"]:
        return
    f = skia.Font(TF, 52)
    w = f.measureText(b["ger"])
    xx = clamp(x, w / 2 + 44, W - w / 2 - 44)
    bubble(c, xx, y, b["ger"], 52, back((t - b["start"] - .35) / .16), 2)


PXS = 290                       # px par mètre dans le salon
CEIL = FLOOR - PLAFOND * PXS    # 840
MX = 470                        # x de Michel dans le salon
SHELF_Y = FLOOR - H0 * PXS


def window(c, x, y, w=240, h=300, night=False):
    win = skia.Rect.MakeLTRB(x, y, x + w, y + h)
    c.drawRect(win, fill("#1B2350" if night else "#9BDCFA"))
    if night:
        draw_moon(c, x + w * .68, y + h * .3, 34, 0, "scared")
        for (sx, sy) in ((.2, .2), (.35, .6), (.8, .75), (.15, .8)):
            c.drawCircle(x + w * sx, y + h * sy, 3, fill("#FFFFFF"))
    c.drawRect(win, line(INK, 22))
    c.drawRect(win, line("#FFFFFF", 14))
    c.drawLine(x + w / 2, y, x + w / 2, y + h, line("#FFFFFF", 10))
    c.drawLine(x, y + h / 2, x + w, y + h / 2, line("#FFFFFF", 10))


def hole(c, x, a=1.0):
    p = skia.Path()
    r = random.Random(5)
    pts = []
    for i in range(14):
        ang = math.pi * i / 13
        rr = r.uniform(.8, 1.15)
        pts.append((x + math.cos(ang) * 130 * rr, CEIL + math.sin(ang) * 46 * rr))
    p.moveTo(x - 140, CEIL)
    for q in pts[::-1]:
        p.lineTo(*q)
    p.lineTo(x + 140, CEIL)
    p.close()
    c.drawPath(p, fill("#9BDCFA", a))
    c.drawPath(p, line(INK, 7, a))


def salon(c, t, b, night=False, holed=True):
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#F7DDAE"))
    for x in range(0, W, 120):
        c.drawRect(skia.Rect.MakeLTRB(x, CEIL, x + 60, FLOOR), fill("#F2D29C", .55))
    c.drawRect(skia.Rect.MakeLTRB(0, 0, W, CEIL), fill("#EFE6D2"))
    c.drawRect(skia.Rect.MakeLTRB(0, CEIL, W, CEIL + 26), fill("#FFF5E0"))
    c.drawLine(0, CEIL, W, CEIL, line(INK, 7))
    c.drawLine(0, CEIL + 26, W, CEIL + 26, line(INK, 4))
    # lustre
    c.drawLine(800, CEIL + 26, 800, CEIL + 110, line(INK, 5))
    shape(c, poly([(760, CEIL + 150), (840, CEIL + 150), (815, CEIL + 106), (785, CEIL + 106)]), "#FFE14D", 5)
    c.drawRect(skia.Rect.MakeLTRB(0, FLOOR - 34, W, FLOOR), fill("#FFF5E0"))
    c.drawRect(skia.Rect.MakeLTRB(0, FLOOR, W, H), fill("#7B4A2B"))
    c.drawLine(0, FLOOR, W, FLOOR, line(INK, 7))
    for i in range(5):
        c.drawLine(i * 240 + 60, FLOOR + 2, i * 300 - 180, H, line(INK, 4, .35))
    window(c, 70, 980, night=night)
    # étagère à 1,50 m
    shape(c, rrect(640, SHELF_Y, 960, SHELF_Y + 26, 6), "#9B6A3C", 6)
    for bx in (680, 920):
        shape(c, poly([(bx - 14, SHELF_Y + 26), (bx + 14, SHELF_Y + 26), (bx, SHELF_Y + 80)]), "#7B4A2B", 5)
    for i, (bx, bh, cc) in enumerate(((870, 120, "#D9534F"), (905, 100, "#3F6FD8"), (935, 130, "#59B36A"))):
        shape(c, rrect(bx - 14, SHELF_Y - bh, bx + 14, SHELF_Y, 4), cc, 5)
    if holed:
        hole(c, MX)
    # gamelle
    shape(c, poly([(160, FLOOR + 40), (300, FLOOR + 40), (280, FLOOR - 4), (180, FLOOR - 4)]), "#D9534F", 6)


def vase(c, x, y, rot=0.0):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    p = skia.Path()
    p.moveTo(-22, 0)
    p.quadTo(-48, -60, -16, -110)
    p.lineTo(16, -110)
    p.quadTo(48, -60, 22, 0)
    p.close()
    shape(c, p, "#7EC8FF", 6)
    c.drawLine(-30, -56, 30, -56, line("#FFFFFF", 6))
    c.restore()


def scene_salon(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    salon(c, t, b, night=key in ("hook", "regle"), holed=key not in ("hook", "regle", "s0", "s1"))
    if key in ("hook", "regle"):
        vase(c, 760, SHELF_Y)
        sc = 1 + .02 * math.sin(t * 9) if key == "hook" else 1
        draw_cat(c, MX, FLOOR + 10, .42 * sc, t, "open", 0)
        if key == "hook":
            # flèche pointillée vers la Lune de la fenêtre
            u = clamp((d_ - .6) / .8)
            p = skia.Path()
            p.moveTo(MX, FLOOR - 200)
            p.quadTo(MX - 60, 1000, 70 + 240 * .68, 980 + 300 * .3 + 40)
            pm = skia.PathMeasure(p, False)
            seg = skia.Path()
            pm.getSegment(0, pm.getLength() * u, seg, True)
            c.drawPath(seg, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=8, Color=col("#FFE14D"),
                                       PathEffect=skia.DashPathEffect.Make([22, 14], 0)))
        if key == "regle":
            gx = lerp(1320, 900, eout((d_ - .1) / .5))
            ger(c, gx, FLOOR + 14, .7, t, 0)
            gerbub(c, t, b, gx - 60, 1010)
    elif key == "s0":
        # saut sur l'étagère : courbe de (MX, sol) à (780, étagère)
        u = clamp((d_ - .1) / .8)
        x = lerp(MX, 780, u)
        y = lerp(FLOOR + 10, SHELF_Y + 4, u) - math.sin(u * math.pi) * 90
        fall = clamp((d_ - 1.5) / .5)
        if d_ < 1.5:
            vase(c, 760 if u < 1 else 760 + 10 * clamp((d_ - 1.1) / .4), SHELF_Y, 0)
        elif fall < 1:
            vase(c, 770 + 60 * fall, SHELF_Y + (FLOOR - SHELF_Y) * fall ** 2, fall * 80)
        else:
            r = random.Random(3)
            for k in range(7):
                dx = r.uniform(-80, 80)
                shape(c, poly([(830 + dx, FLOOR), (850 + dx, FLOOR - 24), (866 + dx, FLOOR)]), "#7EC8FF", 4)
        if u < 1:
            fly_cat(c, x, y, .42, t, "open", .5 * (1 - u))
        else:
            draw_cat(c, 780, SHELF_Y + 4, .42, t, "wink" if d_ > 2.0 else "open", 0)
        if d_ > 1.1:
            c.drawLine(785, SHELF_Y + 50, 785, FLOOR - 40, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5,
                                                                       Color=col("#FFFFFF"), PathEffect=skia.DashPathEffect.Make([16, 12], 0)))
            text(c, "1,50 m", 900, (SHELF_Y + FLOOR) / 2 + 40, 50, "#FFE14D", INK, 9, a=clamp((d_ - 1.1) / .2))
    elif key == "s1":
        # il monte, la tête dans le plafond
        u = rise(d_ * 2.2)
        top_target = CEIL + 70     # base du chat quand il est coincé
        y = lerp(FLOOR + 10, top_target + 405 * .42 - 120, u)
        stuck = u >= 1
        c.save()
        c.clipPath(skia.Path().addRect(skia.Rect.MakeLTRB(0, CEIL + 2, W, H)), skia.ClipOp.kIntersect, True)
        fly_cat(c, MX, y + (math.sin(t * 30) * 4 if stuck else 0), .42, t, "open", 0 if stuck else 1)
        c.restore()
        if stuck:
            k = clamp((d_ - .45) / .15)
            for ang in (-160, -120, -70, -30, 10):
                a_ = math.radians(ang)
                c.drawLine(MX + 80 * math.cos(a_), CEIL + 6, MX + 220 * math.cos(a_) * k, CEIL + 6 + 30 * k * abs(math.sin(a_)), line(INK, 6))
            r = random.Random(11)
            for i in range(12):
                ph = clamp((d_ - .5 - i * .05) / 1.2)
                if ph > 0:
                    c.drawRect(skia.Rect.MakeXYWH(MX + r.uniform(-180, 180), CEIL + ph ** 2 * (FLOOR - CEIL), 22, 16), fill("#FFFFFF"))
            for i in range(3):
                ang = t * 5 + i * 2.1
                cx_, cy_ = MX + math.cos(ang) * 130, CEIL + 60 + math.sin(ang) * 30
                text(c, "★", cx_, cy_, 40, "#FFE14D", INK, 6)
        gx = lerp(1320, 900, eout((d_ - .6) / .5))
        ger(c, gx, FLOOR + 14, .7, t, 2)
        if d_ > .6:
            gerbub(c, t, b, gx - 60, 1010)
    elif key == "veto":
        draw_cat(c, MX, FLOOR + 10, .42, t, "open", 0)
        gx = lerp(1320, 880, eout((d_ - .1) / .5))
        ger(c, gx, FLOOR + 14, .7, t, 1, hold="phone")
        gerbub(c, t, b, gx - 60, 1010)
    elif key == "filet":
        # filet tendu sous le trou
        u = eout((d_ - .2) / .6)
        y0 = CEIL + 220
        for px in (MX - 230, MX + 230):
            shape(c, rrect(px - 10, y0 - 10, px + 10, FLOOR, 5), "#9B9FB0", 5)
        net = skia.Path()
        net.moveTo(MX - 230, y0)
        net.quadTo(MX, y0 + 120 * u, MX + 230, y0)
        c.drawPath(net, line(INK, 6))
        for i in range(1, 10):
            fx = MX - 230 + 46 * i
            sag = 120 * u * (1 - ((fx - MX) / 230) ** 2)
            c.drawLine(fx, y0 + sag * .5, fx - 20, y0 + sag, line("#FFFFFF", 3, .9))
            c.drawLine(fx, y0 + sag * .5, fx + 20, y0 + sag, line("#FFFFFF", 3, .9))
        draw_cat(c, MX + 230 + 90, FLOOR + 10, .42, t, "open", 0)
        gx = lerp(1320, 900, eout((d_ - .1) / .5))
        ger(c, gx, FLOOR + 14, .7, t, 1)
        gerbub(c, t, b, gx - 60, 1010)
    elif key == "croq":
        shake = clamp((d_ - .4) / .2)
        ger(c, 820, FLOOR + 14, .7, t, 0, hold="box", shake=shake)
        if d_ > .7:
            for i, s_ in enumerate(("tchk", "tchk", "tchk")):
                a_ = clamp((d_ - .7 - i * .4) / .15)
                text(c, s_, 430 + i * 110, 1180 - i * 60, 56, "#FFFFFF", INK, 9, a=a_)
    elif key in ("retour", "fin"):
        ger(c, 820, FLOOR + 14, .7, t, 2 if key == "retour" else 3, hold="box" if key == "retour" else None)
        # croquettes dans la gamelle
        for k in range(5):
            c.drawCircle(200 + k * 16, FLOOR - 6 - (k % 2) * 8, 9, fill("#9B6A3C"))
        if key == "retour":
            u = clamp((d_ - .2) / .3)
            if u < 1:
                y = lerp(-300, FLOOR + 10, ein(u))
                c.save()
                c.translate(MX - 120, y)
                c.rotate(180)
                c.translate(-(MX - 120), -y)
                fly_cat(c, MX - 120, y - 160, .42, t, "open", 1.6)
                c.restore()
            else:
                k = d_ - .5
                if k < .6:
                    for i in range(10):
                        a_ = math.pi + math.pi * i / 9
                        rr = 60 + 300 * eout(k / .6)
                        c.drawCircle(MX - 120 + math.cos(a_) * rr, FLOOR - 20 + math.sin(a_) * rr * .4, 46 * (1 - k / .6) + 8, fill("#E8D9B8", .9))
                draw_cat(c, MX - 120, FLOOR + 10, .42, t, "bliss", 0)
            if 1.4 < d_:
                bubble(c, MX - 60, 1180, "mrrp ?", 52, back((d_ - 1.4) / .16), -3)
        else:
            draw_cat(c, MX - 120, FLOOR + 10, .42, t, "wink" if d_ > 2.4 else "bliss", 0)
            gerbub(c, t, b, 780, 1010)


def sky_grad(c, a, b_, y0=400, y1=1400):
    p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, y0), (0, y1)], [col(a), col(b_)]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)


def scale_bar(c, x, y_bottom, y_top, label, colr="#FFFFFF", side=1, a=1.0):
    c.drawLine(x, y_bottom, x, y_top, line(colr, 5, a))
    c.drawLine(x - 18, y_top, x + 18, y_top, line(colr, 5, a))
    text(c, label, x + side * 24, y_top + 16, 46, colr, INK, 9, align="left" if side > 0 else "right", a=a)


def scene_maison(c, t, b):
    d_ = t - b["start"]
    sky_grad(c, "#5CB8F2", "#D3F1FF")
    G = 1640
    PX = 150
    c.drawRect(skia.Rect.MakeLTRB(0, G, W, H), fill("#7CC46E"))
    c.drawLine(0, G, W, G, line(INK, 6))
    # maison (faîte à 5 m)
    shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(200, G - 3 * PX, 860, G)), "#F2E3C6", 7)
    roof = poly([(160, G - 3 * PX), (900, G - 3 * PX), (530, G - 5 * PX)])
    shape(c, roof, "#C8553D", 7)
    shape(c, rrect(470, G - 260, 590, G, 8), "#7B4A2B", 6)
    for wx in (260, 680):
        shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(wx, G - 360, wx + 120, G - 240)), "#9BDCFA", 6)
    u = rise(d_)
    apex = G - hm(2) * PX
    roof_y = G - 4.2 * PX
    y = lerp(roof_y + 160, apex, u)
    if u > .05:
        # trou dans le toit
        c.drawOval(skia.Rect.MakeLTRB(400, roof_y - 40, 560, roof_y + 30), fill("#3A2420"))
        r = random.Random(2)
        for i in range(10):
            ph = clamp((d_ - .05) / 1.4)
            vx, vy = r.uniform(-500, 500), r.uniform(-700, -300)
            tx, ty = 480 + vx * ph, roof_y + vy * ph + 900 * ph * ph
            c.save()
            c.translate(tx, ty)
            c.rotate(ph * 500 + i * 40)
            shape(c, rrect(-26, -12, 26, 12, 4), "#C8553D", 4)
            c.restore()
    c.save()
    c.clipPath(skia.Path().addRect(skia.Rect.MakeLTRB(0, 0, W, roof_y - 10)), skia.ClipOp.kIntersect, True)
    fly_cat(c, 480, y, .32, t, "open", 1 - u * .7)
    c.restore()
    scale_bar(c, 960, G, apex, "6 m", "#FFE14D", -1, clamp((d_ - .8) / .2))


def pigeon(c, x, y, s, t, ph=0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    w = math.sin(t * 22 + ph) * 30
    shape(c, oval(-34, -18, 34, 18), "#9AA0B5", 5)
    shape(c, poly([(-10, -6), (-50, -50 - w), (14, -10)]), "#B5BACB", 5)
    c.drawCircle(30, -14, 14, fill("#9AA0B5"))
    c.drawCircle(30, -14, 14, line(INK, 4))
    c.drawCircle(34, -17, 3, fill(INK))
    c.drawPath(poly([(42, -12), (54, -8), (42, -4)]), fill("#F2A93B"))
    c.restore()


def scene_ville(c, t, b):
    d_ = t - b["start"]
    sky_grad(c, "#5CB8F2", "#D3F1FF")
    G = 1660
    PX = 38
    r = random.Random(4)
    x = -30
    while x < W:
        w_ = r.uniform(170, 240)
        h_ = r.uniform(17, 21) * PX
        shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(x, G - h_, x + w_, G)), r.choice(("#EDE0C8", "#E6D3B3", "#F2E8D5")), 6)
        shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(x - 6, G - h_ - 40, x + w_ + 6, G - h_)), "#6F7B91", 5)
        for fy in range(int(G - h_ + 60), G - 80, 110):
            for fx in range(int(x + 30), int(x + w_ - 40), 64):
                c.drawRect(skia.Rect.MakeLTRB(fx, fy, fx + 34, fy + 60), fill("#4D6A8A"))
        x += w_ + 10
    c.drawRect(skia.Rect.MakeLTRB(0, G, W, H), fill("#8A8F9C"))
    u = rise(d_)
    apex = G - hm(4) * PX
    fly_cat(c, 520, lerp(G - 6 * PX, apex, u), .24, t, "open", 1 - u * .7)
    for i in range(5):
        k = clamp((d_ - .4) / 1.2)
        px0, py0 = 380 + i * 70, apex + 40 + (i % 2) * 60
        pigeon(c, px0 + (i - 2) * 260 * k, py0 - 200 * k + 40 * i * k, .9, t, i)
    scale_bar(c, 960, G, apex, "24 m", "#FFE14D", -1, clamp((d_ - .8) / .2))


def arc(c, x, G, h):
    w = h * .9
    s = skia.Path()
    s.addRect(skia.Rect.MakeLTRB(x - w / 2, G - h, x + w / 2, G))
    shape(c, s, "#E8D7B0", 6)
    c.drawRect(skia.Rect.MakeLTRB(x - w / 2 - 6, G - h, x + w / 2 + 6, G - h * .86), fill("#D8C49A"))
    c.drawRect(skia.Rect.MakeLTRB(x - w / 2 - 6, G - h, x + w / 2 + 6, G - h * .86), line(INK, 5))
    a = skia.Path()
    aw = w * .34
    a.moveTo(x - aw / 2, G)
    a.lineTo(x - aw / 2, G - h * .42)
    a.arcTo(skia.Rect.MakeLTRB(x - aw / 2, G - h * .42 - aw / 2, x + aw / 2, G - h * .42 + aw / 2), 180, 180, False)
    a.lineTo(x + aw / 2, G)
    a.close()
    shape(c, a, "#5E7FA8", 5)


def scene_paris(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    sky_grad(c, "#F7B267", "#FFE9B8")
    G = 1660
    if key == "s6":
        PX = 8.0
    else:
        PX = lerp(8.0, 2.4, eout(d_ / .6))
    # immeubles bas
    r = random.Random(3)
    x = -20
    while x < W:
        w_ = r.uniform(90, 160)
        h_ = 20 * PX
        shape(c, skia.Path().addRect(skia.Rect.MakeLTRB(x, G - h_, x + w_, G)), "#B58FA0", 4)
        x += w_ + 6
    if key == "s8":
        c.save()
        c.translate(800, G)
        draw_eiffel(c, EIFFEL * PX)
        c.restore()
    if key == "s8" and EIFFEL * PX < 1400:
        text(c, "330 m", 800, G - EIFFEL * PX - 26, 46, "#FFFFFF", INK, 9)
    arc(c, 330, G, ARC * PX)
    text(c, "50 m", 330, G - ARC * PX - 22, 44, "#FFFFFF", INK, 9)
    c.drawRect(skia.Rect.MakeLTRB(0, G, W, H), fill("#8A8F9C"))
    c.drawLine(0, G, W, G, line(INK, 6))
    u = rise(d_)
    h = hm(6) if key == "s6" else hm(8)
    apex = G - h * PX
    s_ = .2 if key == "s6" else .14
    fly_cat(c, 330 if key == "s6" else 560, lerp(G - 10, apex, u), s_, t, "open", 1 - u * .7)
    lab = "96 m" if key == "s6" else "384 m"
    text(c, lab, 330 if key == "s6" else 560, apex - 405 * s_ - 24, 48, "#FFE14D", INK, 9, a=clamp((d_ - .9) / .2))


def plane(c, x, y, s, t):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    shape(c, rrect(-160, -24, 160, 24, 24), "#F2F2F7", 6)
    shape(c, poly([(-20, 0), (40, 0), (-40, 90), (-80, 90)]), "#D4D7E0", 5)
    shape(c, poly([(-130, -10), (-100, -10), (-150, -80), (-175, -80)]), "#D9534F", 5)
    for k in range(6):
        c.drawCircle(-60 + k * 30, -6, 7, fill("#4D6A8A"))
    c.restore()


def scene_ciel(c, t, b):
    d_ = t - b["start"]
    sky_grad(c, "#2E6FD0", "#BFE6FF", 300, 1700)
    G = 1720
    PX = .08
    # Everest
    pk = G - EVEREST * PX
    m = poly([(-100, G), (300, pk + 200), (420, pk), (560, pk + 160), (760, pk + 340), (1180, G)])
    shape(c, m, "#8C8FA3", 7)
    shape(c, poly([(355, pk + 100), (420, pk), (500, pk + 90), (460, pk + 70), (420, pk + 110), (390, pk + 80)]), "#FFFFFF", 5)
    text(c, "EVEREST : 8 849 m", 420, pk - 26, 44, "#FFFFFF", INK, 9)
    # bande des avions
    a0, a1 = G - AVIONS[0] * PX, G - AVIONS[1] * PX
    c.drawRect(skia.Rect.MakeLTRB(0, a1, W, a0), fill("#FFFFFF", .16))
    plane(c, 860 + math.sin(t) * 6 - (t - b["start"]) * 40, (a0 + a1) / 2, .5, t)
    text(c, "AVIONS : 9 À 12 km", W - 30, a1 - 16, 40, "#FFFFFF", INK, 8, align="right")
    u = rise(d_)
    apex = G - hm(13) * PX
    fly_cat(c, 420, lerp(G - 300, apex, u), .16, t, "open", 1 - u * .7)
    if d_ > 1.6:
        bubble(c, 820, (a0 + a1) / 2 - 60, "?!", 46, back((d_ - 1.6) / .16), 4)


def scene_mach(c, t, b):
    d_ = t - b["start"]
    sky_grad(c, "#2E6FD0", "#BFE6FF", 300, 1700)
    r = random.Random(9)
    for i in range(10):
        y = (r.uniform(0, H) + (t * 2400)) % (H + 400) - 200
        x = r.uniform(-60, W)
        shape(c, oval(x, y, x + 220, y + 70), "#FFFFFF", 0, .85)
    # cône de vapeur
    cx, cy = 540, 1150
    u = clamp((d_ - .5) / .3)
    if u > 0:
        cone = skia.Path()
        cone.moveTo(cx, cy - 330)
        cone.quadTo(cx - 330, cy - 120, cx - 380, cy + 120)
        cone.quadTo(cx, cy + 40, cx + 380, cy + 120)
        cone.quadTo(cx + 330, cy - 120, cx, cy - 330)
        c.drawPath(cone, fill("#FFFFFF", .55 * u))
        c.drawPath(cone, line("#FFFFFF", 8, .9 * u))
    vib = 6
    fly_cat(c, cx + jitter(t, 4)[0] * vib, cy + 120, .55, t, "open", 1.6)
    if d_ > .55:
        s_ = back((d_ - .55) / .18)
        c.save()
        c.translate(cx + 250, cy + 300)
        c.rotate(-8)
        c.scale(s_, s_)
        text(c, "BANG !", 0, 0, 120, "#FFE14D", INK, 14)
        c.restore()
        text(c, "Son : 1 235 km/h", 540, 1620, 46, "#FFFFFF", INK, 9, a=clamp((d_ - 1.2) / .2))


def scene_espace(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 1000), (0, 1640)], [col("#06061A"), col("#4FA3E8")]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    rr = random.Random(8)
    for i in range(140):
        y = rr.uniform(0, 1300)
        c.drawCircle(rr.uniform(0, W), y, rr.choice((1.2, 2, 2.6)), fill("#FFFFFF", clamp((1350 - y) / 500)))
    G = 1660
    PXK = 2.2
    shape(c, oval(-900, G - 30, W + 900, G + 2400), "#2B86DE", 7)
    c.drawPath(oval(-900, G - 30, W + 900, G + 2400), line("#9BDCFA", 18, .5))
    for (x0, w0) in ((80, 260), (600, 320)):
        shape(c, oval(x0, G - 10, x0 + w0, G + 60), "#59B36A", 0)
    ky = G - KARMAN * PXK
    c.drawPath(skia.Path().moveTo(0, ky).lineTo(W, ky),
               skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6, Color=col("#FFE14D"), PathEffect=skia.DashPathEffect.Make([26, 16], 0)))
    text(c, "ESPACE : 100 km", 820, ky - 22, 42, "#FFE14D", INK, 8)
    iy = G - ISS * PXK
    ix = 560 + (t - K["s17"]) * 70 - 220
    draw_iss(c, ix, iy, .55, 6)
    text(c, "ISS : 422 km", ix + 40, iy - 60, 42, "#FFFFFF", INK, 8)
    h = hm(17) if key == "s17" else hm(18)
    u = rise(d_)
    apex = G - h / 1000 * PXK
    mx = 470
    y = lerp(G + 40, apex, u)
    # casque
    fly_cat(c, mx, y, .16, t, "open", 1 - u * .7)
    c.drawCircle(mx, y - 270 * .16, 190 * .16, fill("#BEE8FF", .22))
    c.drawCircle(mx, y - 270 * .16, 190 * .16, line("#E9F6FF", 3))
    if key == "s18" and d_ > 1.1:
        a_ = clamp((d_ - 1.1) / .2)
        top = apex - 405 * .16
        c.drawLine(mx + 70, top, mx + 70, iy + 10, line("#FFE14D", 5, a_))
        text(c, "29 km", mx + 90, (top + iy) / 2 + 16, 44, "#FFE14D", INK, 8, align="left", a=a_)
        if d_ > 1.8:
            bubble(c, mx - 30, top - 70, "mrrp…", 44, back((d_ - 1.8) / .16), -3)


def scene_lune_vol(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    c.drawImage(STARS, 0, 0)
    ex, mx, y = 130, 130 + 800, 1250
    img, x0, y0 = earth_rgba(52, cx=ex, cy=y)
    c.drawImage(img, x0, y0)
    c.drawCircle(ex, y, 52, line(INK, 5))
    draw_moon(c, mx, y, 32, t, "scared")
    c.drawPath(skia.Path().moveTo(ex, y + 120).lineTo(mx, y + 120),
               skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5, Color=col("#FFFFFF"), PathEffect=skia.DashPathEffect.Make([18, 12], 0)))
    text(c, "384 400 km", (ex + mx) / 2, y + 190, 50, "#FFFFFF", INK, 9)
    # progression sur les trois temps
    T0, T1 = K["s28"] + .3, K["lune"] - .2
    p = clamp((t - T0) / (T1 - T0))
    # vitesse décroissante : départ rapide
    q = 1 - (1 - p) ** 1.6
    path_x = lerp(ex + 60, mx - 40, q)
    path_y = y - 40 - math.sin(q * math.pi) * 220
    c.drawPath(skia.Path().moveTo(ex + 50, y - 40).quadTo((ex + mx) / 2, y - 480, mx - 40, y - 40),
               skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=4, Color=col("#FFE14D", .6), PathEffect=skia.DashPathEffect.Make([10, 10], 0)))
    path_y = (1 - q) ** 2 * (y - 40) + 2 * (1 - q) * q * (y - 480) + q * q * (y - 40)
    path_x = (1 - q) ** 2 * (ex + 50) + 2 * (1 - q) * q * ((ex + mx) / 2) + q * q * (mx - 40)
    sl = key == "voyage"
    draw_cat(c, path_x, path_y + 30, .14, t, "bliss" if sl else "open", 0)
    c.drawCircle(path_x, path_y + 30 - 270 * .14, 190 * .14, fill("#BEE8FF", .22))
    c.drawCircle(path_x, path_y + 30 - 270 * .14, 190 * .14, line("#E9F6FF", 3))
    if sl:
        for k in range(3):
            ph = (t * .8 + k / 3) % 1
            text(c, "z", path_x + 40 + ph * 60, path_y - 60 - ph * 90, 30 + 20 * ph, "#FFFFFF", INK, 5, a=1 - ph)
        # compteur de jours
        dd = JOURS * clamp((t - b["start"]) / (b["dur"] - .4))
        text(c, ("Jour %.1f" % dd).replace(".", ","), 540, 1560, 60, "#FFE14D", INK, 10)
    if key == "vit":
        # compteur de vitesse
        cx, cy, R = 540, 1640, 150
        u = eout(d_ / 1.2)
        arcp = skia.Path()
        arcp.addArc(skia.Rect.MakeLTRB(cx - R, cy - R, cx + R, cy + R), 180, 180)
        c.drawPath(arcp, line("#FFFFFF", 14, .3))
        arc2 = skia.Path()
        arc2.addArc(skia.Rect.MakeLTRB(cx - R, cy - R, cx + R, cy + R), 180, 180 * .992 * u)
        c.drawPath(arc2, line("#FF5A3B", 14))
        ang = math.radians(180 + 180 * .992 * u)
        c.drawLine(cx, cy, cx + math.cos(ang) * (R - 20), cy + math.sin(ang) * (R - 20), line("#FFFFFF", 8))
        text(c, "99 % DE LA VITESSE", cx, cy + 60, 40, "#FFFFFF", INK, 8)
        text(c, "DE LIBÉRATION", cx, cy + 104, 40, "#FFFFFF", INK, 8)
    if key == "s28" and d_ < .5:
        c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", .5 * (1 - d_ / .5)))


def scene_lune(c, t, b):
    d_ = t - b["start"]
    c.drawImage(STARS, 0, 0)
    img, x0, y0 = earth_rgba(110, cx=820, cy=860)
    c.drawImage(img, x0, y0)
    c.drawCircle(820, 860, 110, line(INK, 6))
    shape(c, oval(-500, 1360, W + 500, 2700), "#C9CBD6", 8)
    for (x, y, r) in ((180, 1480, 50), (760, 1450, 34), (560, 1640, 70), (950, 1600, 30)):
        c.drawOval(skia.Rect.MakeLTRB(x - r, y - r * .4, x + r, y + r * .4), fill("#A7A9B8"))
    # atterrissage au début
    u = eout(d_ / .5)
    mx, my = 360, lerp(1100, 1500, u)
    if d_ < .9:
        k = clamp((d_ - .5) / .4)
        for i in range(8):
            a_ = math.pi + math.pi * i / 7
            c.drawCircle(mx + math.cos(a_) * 200 * k, 1500 + math.sin(a_) * 60 * k, 22 * (1 - k) + 2, fill("#E3E4EC", .9))
    # drapeau
    f = eout((d_ - 1.0) / .4)
    if f > 0:
        fx = 560
        top = 1500 - 360 * f
        c.drawLine(fx, 1510, fx, top, line(INK, 10))
        c.drawLine(fx, 1510, fx, top, line("#E9E9EF", 6))
        wv = math.sin(t * 6) * 6 * 0  # pas de vent sur la Lune
        flag = rrect(fx, top, fx + 220, top + 140, 6)
        shape(c, flag, "#FF6A2B", 6, f)
        # arête de poisson
        c.drawLine(fx + 40, top + 70, fx + 170, top + 70, line("#FFFFFF", 7, f))
        for k in range(3):
            xx = fx + 70 + k * 30
            c.drawLine(xx, top + 70, xx - 16, top + 40, line("#FFFFFF", 6, f))
            c.drawLine(xx, top + 70, xx - 16, top + 100, line("#FFFFFF", 6, f))
        c.drawPath(poly([(fx + 170, top + 70), (fx + 196, top + 48), (fx + 196, top + 92)]), fill("#FFFFFF", f))
        c.drawCircle(fx + 50, top + 70, 10, fill("#FFFFFF", f))
    draw_cat(c, mx, my, .42, t, "wink" if d_ > 2.2 else "open", 0)
    c.drawCircle(mx, my - 270 * .42, 190 * .42, fill("#BEE8FF", .22))
    c.drawCircle(mx, my - 270 * .42, 190 * .42, line("#E9F6FF", 8))
    c.drawCircle(mx, my - 270 * .42, 190 * .42, line(INK, 3))


# ---------------------------------------------------------------- HUD, légende, carton
def heat_c(n):
    u = clamp(n / 28)
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
    if m < 10:
        return ("%.2f M" % m).replace(".", ",")
    if m < 999.5:
        return "%d M" % round(m)
    k = m / 1000
    if k < 99.95:
        return ("%.1f KM" % k).replace(".", ",")
    return "%s KM" % nb(round(k))


assert size_txt(hm(0)) == "1,50 M" and size_txt(hm(1)) == "3,00 M" and size_txt(hm(13)) == "12,3 KM"
assert size_txt(hm(17)) == "197 KM" and size_txt(hm(18)) == "393 KM" and size_txt(hm(28)) == "402 653 KM" and size_txt(hm(8)) == "384 M"


def hud(c, t, b):
    n = jump_at(t)
    colr = heat_c(n)
    d_ = t - b["start"]
    pop = 1 + .14 * (1 - eout(d_ / .22)) if (b["n1"] != b["n0"]) else 1.0
    c.save()
    c.translate(540, 262)
    c.scale(pop, pop)
    pan = rrect(-420, -135, 420, 135, 44)
    c.drawPath(pan, fill("#14121C", .94))
    c.drawPath(pan, line(colr, 8))
    head = "HAUTEUR DU SAUT"
    big = size_txt(hm(n))
    low = "Saut n° %d" % round(n)
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
    text(c, "SAUT N° 29.", 0, 128, 86, "#FFD93B")
    c.restore()
    a = clamp((d_ - .5) / .25)
    for i, l in enumerate(("Très approximatif : départ à 1,50 m,",
                           "×2 à chaque saut, sans air, échelles à peu près.",
                           "Vrai chat : 1,2 à 1,8 m. Arc : 50 m. Eiffel : 330 m.",
                           "ISS : environ 422 km. Lune : 384 400 km.",
                           "Vitesse de libération : 11,2 km/s.",
                           "Ne faites pas sauter votre chat.",
                           "Michel va bien.")):
        s_ = fit(l, 44, 960)
        text(c, l, 540, 1000 + i * 62, s_, "#A9A6BC", a=a)


SCN = dict(salon=scene_salon, maison=scene_maison, ville=scene_ville, paris=scene_paris, ciel=scene_ciel, mach=scene_mach,
           espace=scene_espace, lune_vol=scene_lune_vol, lune=scene_lune)


def shake_amp(t):
    amp = 0
    for tk in JUMPS:
        d_ = t - tk
        if 0 <= d_ < .22:
            amp = max(amp, 9 * (1 - d_ / .22))
    for key, a0, dur in (("mach", .55, .5), ("retour", .5, .5), ("s1", .45, .3)):
        d_ = t - K[key] - a0
        if 0 <= d_ < dur:
            amp = max(amp, 24 * (1 - d_ / dur))
    return amp


def burst(c, t):
    for tk in JUMPS:
        d_ = t - tk
        if 0 <= d_ < .25:
            if d_ < .07:
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
    SCN[b["ph"]](c, t, b)
    c.restore()
    burst(c, t)
    hud(c, t, b)
    caption(c, t)


_sp = [K["s2"], K["s6"], K["s13"], K["s17"], K["s28"], K["lune"], K["croq"], CARD, END]
SPL = [("s_%d" % i, a, z) for i, (a, z) in enumerate(zip([0] + _sp, _sp))]


def png(t, path):
    from PIL import Image
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    s = skia.Surface(arr)
    with s as c:
        frame(c, t)
    Image.fromarray(arr[..., :3]).save(path)


if __name__ == "__main__":
    print("durée %.1f s, carton %.1f, V13 %.0f km/h, V28 %.0f km/h, %.2f jours" % (END, CARD, V13, V28, JOURS))
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
