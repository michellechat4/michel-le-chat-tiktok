"""Et si un trou traversait la Terre ? Michel pousse Gérard dedans. Gérard tombe, très calme, jusqu'aux îles Antipodes, et revient."""
import math, random, sys, os, subprocess
import numpy as np
import skia
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "moteur"))
import art
from art import (fill, line, col, hexmix, poly, rrect, oval, shape, text, jitter, clamp, lerp, eout, ein, back,
                 draw_cat, draw_gerard, earth_rgba, STARS, bubble, wrap_rich, TF, INK, W, H, FPS)

# ---------------------------------------------------------------- physique (calculée, pas recopiée)
R_T = 6371e3            # m, rayon moyen de la Terre
R_C = 3485e3            # m, rayon du noyau (National Geographic : ~3 485 km, sommet à ~2 900 km de profondeur)
R_IC = 1220e3           # m, rayon de la graine (noyau interne)
G0 = 9.82               # m/s², pesanteur supposée constante dans le manteau (approximation de Klotz, 2015)
KOLA = 12262            # m, forage de Kola (1970-1989), le plus profond jamais creusé
SON = 343               # m/s, vitesse du son dans l'air à 20 °C
ISS_KMH = 28000         # km/h, vitesse de l'ISS (environ)
KLOTZ = 38 * 60 + 11    # s, durée de la traversée avec le modèle PREM (Klotz, 2015)


def g_of(r):
    """Modèle maison : g constant dans le manteau, puis noyau homogène (g proportionnel à r)."""
    return G0 if r >= R_C else G0 * r / R_C


def _simulate(dt=0.005):
    r, v, t = R_T, 0.0, 0.0
    ts, ds, vs = [0.0], [0.0], [0.0]
    while r > 0:
        a = g_of(r)
        v += a * dt
        r -= v * dt
        t += dt
        ts.append(t); ds.append(R_T - r); vs.append(v)
    ts, ds, vs = np.array(ts), np.array(ds), np.array(vs)
    th = ts[-1]
    # symétrie : remontée de l'autre côté
    ts2 = np.concatenate([ts, 2 * th - ts[::-1][1:]])
    ds2 = np.concatenate([ds, 2 * R_T - ds[::-1][1:]])
    vs2 = np.concatenate([vs, vs[::-1][1:]])
    return ts2, ds2, vs2, th


TS, DS, VS, T_HALF = _simulate()
T_CROSS = TS[-1]                        # traversée complète
T_RT = 2 * T_CROSS                      # aller-retour


def dist(tp):
    """Distance parcourue (m) à l'instant physique tp (s), aller-retour compris."""
    if tp <= T_CROSS:
        return float(np.interp(tp, TS, DS))
    return 2 * R_T + float(np.interp(tp - T_CROSS, TS, DS))


def speed(tp):
    if tp <= T_CROSS:
        return float(np.interp(tp, TS, VS))
    return float(np.interp(tp - T_CROSS, TS, VS))


def t_at_depth(d):
    return float(np.interp(d, DS[:len(DS) // 2 + 1], TS[:len(TS) // 2 + 1]))


T_SON = float(np.interp(SON, VS[:len(VS) // 2 + 1], TS[:len(TS) // 2 + 1]))
T_KOLA = t_at_depth(KOLA)
T_CMB = t_at_depth(R_T - R_C)
V_MAX_KMH = speed(T_HALF) * 3.6

assert round(T_SON) == 35 and round(T_KOLA) == 50
assert round((R_T - R_C) / 1000) == 2886 and round(T_CMB / 60) == 13
assert round(T_HALF / 60) == 19 and 34000 <= V_MAX_KMH < 34500 and V_MAX_KMH > ISS_KMH
assert round(T_CROSS / 60) == 39 and abs(T_CROSS - KLOTZ) / KLOTZ < .02      # à 2 % de l'étude PREM
assert round(T_RT / 60) == 77
assert abs(dist(T_CROSS) - 2 * R_T) < 50 and abs(dist(T_RT) - 4 * R_T) < 100

# ---------------------------------------------------------------- chronologie
# (clé, durée, temps physique à atteindre, légende, Gérard dit, décor)
RAW = [
    ("hook", 3.6, 0, "MICHEL VA POUSSER GÉRARD | *À TRAVERS LA TERRE.*", None, "salon"),
    ("trou", 3.8, 0, "Et si un trou traversait | la Terre, *de part en part ?*", None, "coupe"),
    ("regle", 3.6, 0, "Un tube *sans air.* Gérard | *ne cuit pas.* On a dit.", "Ah bon.", "salon"),
    ("pousse", 3.8, 0, "Michel pousse les objets. | Gérard est *un objet.*", "Ah.", "salon"),
    ("chute", 3.6, 12, "Gérard tombe. | *Très calmement.*", "D'accord.", "tube"),
    ("son", 3.6, T_SON, "35 s : il passe | *la vitesse du son.* Sans bruit.", None, "tube"),
    ("kola", 4.0, T_KOLA, "50 s : 12,3 km. Le trou le plus | profond du monde : *19 ans* de forage.", None, "tube"),
    ("apes", 3.6, 150, "En chute libre, Gérard | ne pèse *rien.* Son journal non plus.", None, "tube"),
    ("manteau", 3.8, 560, "Il traverse le *manteau* : | 2 900 km de roche.", None, "coupe"),
    ("noyau", 3.6, T_CMB, "13 min : *le noyau.* | Du fer liquide, à *4 000 °C* et plus.", None, "tube"),
    ("centre", 4.0, T_HALF, "19 min : le centre. *34 000 km/h.* | L'ISS : *28 000.*", None, "tube"),
    ("press", 3.6, T_HALF, "Pression : *3,6 millions* | d'atmosphères.", "Bien.", "tube"),
    ("remonte", 3.6, 1900, "Il ralentit. Il remonte | *de l'autre côté.*", None, "coupe"),
    ("arrive", 3.8, T_CROSS, "39 min : plein Pacifique, | près des *îles Antipodes.*", "Bonjour.", "ocean"),
    ("zero", 3.6, T_CROSS, "Vitesse : *zéro.* | Un manchot le regarde.", None, "ocean"),
    ("retour", 3.8, T_RT, "Il retombe. Retour à Paris | *77 min* plus tard.", None, "salon"),
    ("fin", 4.6, T_RT, "Michel l'attendait. | Il le pousse. *Encore.*", "D'accord.", "salon"),
]
CARD_DUR = 4.4
BEATS = []
_t, _p = 0.0, 0.0
for key, dur, tp, cap, ger_, ph_ in RAW:
    BEATS.append(dict(key=key, start=_t, dur=dur, p0=_p, p1=tp, cap=cap, ger=ger_, ph=ph_))
    _t += dur
    _p = tp
CARD = _t
END = CARD + CARD_DUR
K = {b["key"]: b["start"] for b in BEATS}
B = {b["key"]: b for b in BEATS}
JUMPS = [b["start"] for b in BEATS if b["p1"] > b["p0"]]
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
    b = beat_at(t)
    if b["p1"] <= b["p0"]:
        return b["p1"]
    f = clamp((t - b["start"]) / (b["dur"] * .85))
    if b["key"] in ("chute",):
        f = f * f
    else:
        f = eout(f)
    return lerp(b["p0"], b["p1"], f)


# ---------------------------------------------------------------- Gérard (repris de la vidéo 09)
def ger(c, x, floor, s, t, stage=0, arms="down", walk=0.0, lean=0.0, a=1.0):
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
        if arms == "float":
            w_ = math.sin(t * 2 + sg) * 20
            arm.quadTo(790 + sg * 190, 1150 + w_, 790 + sg * 230, 1060 + w_)
        elif arms == "wave" and sg == 1:
            w_ = math.sin(t * 12) * 30
            arm.quadTo(790 + 170, 1120, 790 + 170 + w_, 1000)
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


# ---------------------------------------------------------------- salon avec le trou
HX, HY, HRX, HRY = 380, FLOOR + 70, 220, 54      # trou dans le plancher
GX0 = 700                                         # Gérard debout
MX0 = 930                                         # Michel


def hole_path():
    return oval(HX - HRX, HY - HRY, HX + HRX, HY + HRY)


def salon_bg(c, t):
    c.drawRect(skia.Rect.MakeWH(W, H), fill("#F7DDAE"))
    for x in range(0, W, 120):
        c.drawRect(skia.Rect.MakeLTRB(x, 640, x + 60, FLOOR), fill("#F2D29C", .55))
    c.drawRect(skia.Rect.MakeLTRB(0, FLOOR - 34, W, FLOOR), fill("#FFF5E0"))
    # fenêtre et cadre
    shape(c, rrect(620, 800, 960, 1120, 14), "#9AD4F5", 8)
    c.drawLine(790, 800, 790, 1120, line(INK, 6))
    c.drawLine(620, 960, 960, 960, line(INK, 6))
    shape(c, rrect(120, 820, 380, 1010, 10), "#FFFFFF", 7)
    shape(c, rrect(140, 840, 360, 990, 6), "#7CC46E", 4)
    c.drawCircle(300, 880, 26, fill("#FFE14D"))
    c.drawRect(skia.Rect.MakeLTRB(0, FLOOR, W, H), fill("#7B4A2B"))
    c.drawLine(0, FLOOR, W, FLOOR, line(INK, 7))
    for i in range(5):
        c.drawLine(i * 240 + 60, FLOOR + 2, i * 300 - 180, H, line(INK, 4, .35))
    # le trou
    hp = hole_path()
    p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((HX, HY + 20), HRX, [col("#000000"), col("#2A1A12")]))
    c.drawPath(hp, p)
    c.drawPath(hp, line(INK, 8))
    c.drawPath(hp, line("#A8744C", 4))


def hole_clip(c):
    """Tout ce qui est au-dessus du bord arrière du trou, ou dans le trou."""
    p = skia.Path()
    p.addRect(skia.Rect.MakeLTRB(0, 0, W, HY))
    p.addPath(hole_path())
    c.clipPath(p, skia.ClipOp.kIntersect, True)


def paw(c, x0, y0, x1, y1):
    p = skia.Path()
    p.moveTo(x0, y0)
    p.lineTo(x1, y1)
    c.drawPath(p, line(INK, 40))
    c.drawPath(p, line("#F49A3A", 28))
    shape(c, oval(x1 - 24, y1 - 20, x1 + 24, y1 + 20), "#FFE1B0", 6)


def sign(c, s, x, y, size=46, colr="#FFE14D", rot=0.0, a=1.0):
    f = skia.Font(TF, size)
    w = f.measureText(s)
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    shape(c, rrect(-w / 2 - 26, -size * .95, w / 2 + 26, size * .45, 14), colr, 6, a)
    text(c, s, 0, 0, size, INK, a=a)
    c.restore()


def scene_salon(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    salon_bg(c, t)
    if key == "hook":
        ger(c, GX0, FLOOR + 30, .62, t, 0)
        draw_cat(c, MX0, FLOOR + 30, .34, t, "wink" if d_ > 2.2 else "open", 0)
        if 1.0 < d_:
            bubble(c, MX0 - 20, 1240, "mrrraa !", 52, back((d_ - 1.0) / .16), -3)
        # flèche vers le trou
        a = clamp((d_ - .4) / .3)
        y = HY - 150 + math.sin(t * 8) * 14
        shape(c, poly([(HX - 40, y - 60), (HX + 40, y - 60), (HX + 40, y), (HX + 80, y), (HX, y + 70), (HX - 80, y), (HX - 40, y)]), "#FF4B4B", 6, a)
        return
    if key == "regle":
        ger(c, GX0 - 40, FLOOR + 30, .62, t, 1, lean=-6)
        draw_cat(c, MX0, FLOOR + 30, .34, t, "bliss", 0)
        a = clamp((d_ - .3) / .2)
        sign(c, "TUBE SANS AIR", HX, HY - 230, 48, "#FFFFFF", -3, a)
        gerbub(c, t, b, GX0 - 40, 960, .9)
        return
    if key == "pousse":
        # Michel s'approche, tend la patte ; Gérard bascule et tombe
        mx = lerp(MX0, GX0 + 150, eout(clamp(d_ / .7)))
        push = clamp((d_ - .9) / .3)
        tip = ein(clamp((d_ - 1.3) / .7))
        fall = ein(clamp((d_ - 2.0) / .7))
        gx = lerp(GX0, HX + 60, tip)
        lean = -80 * tip
        c.save()
        hole_clip(c)
        ger(c, gx, FLOOR + 30 + 900 * fall, .62, t, 2 if tip > .2 else 0, arms="float" if tip > .3 else "down", lean=lean)
        c.restore()
        draw_cat(c, mx, FLOOR + 30, .34, t, "open" if push < 1 else "bliss", 0)
        if 0 < push and tip < 1:
            paw(c, mx - 30, FLOOR - 50, mx - 30 - 90 * push, FLOOR - 70)
        if d_ > 1.0 and fall < .5:
            gerbub(c, t, b, gx + 40, 900, .8)
        if d_ > 2.9:
            bubble(c, mx - 10, 1240, "mrrp.", 52, back((d_ - 2.9) / .16), 3)
        return
    if key in ("retour", "fin"):
        # Gérard remonte du trou ; Michel l'attend au bord
        if key == "retour":
            up = eout(clamp((d_ - 1.0) / .9))
            down = 0
        else:
            up = 1
            down = ein(clamp((d_ - 2.2) / .6))
        rise = up - down
        c.save()
        hole_clip(c)
        ger(c, HX, FLOOR + 30 + lerp(700, 240, rise), .62, t, 0, arms="wave" if key == "retour" and d_ > 2.0 else "float" if down > 0 else "down")
        c.restore()
        mx = HX + 330 if key == "retour" else lerp(HX + 330, HX + 260, eout(clamp((d_ - 1.4) / .4)))
        draw_cat(c, mx, FLOOR + 30, .34, t, "wink" if (key == "fin" and d_ > 3.0) else "open", 0)
        if key == "fin":
            push = clamp((d_ - 1.8) / .3) * (1 - clamp((d_ - 2.9) / .3))
            if push > 0:
                paw(c, mx - 30, FLOOR - 60, mx - 30 - 120 * push, FLOOR - 140 + 60 * down)
            if 1.2 < d_ < 2.2:
                bubble(c, mx - 10, 1240, "mrrp !", 52, back((d_ - 1.2) / .16), 3)
            if d_ > 2.4:
                gerbub(c, t, b, HX + 80, 1000, 2.05)
        else:
            if d_ > 2.6:
                bubble(c, mx - 10, 1240, "...", 56, back((d_ - 2.6) / .16), 3)
        return


# ---------------------------------------------------------------- dans le tube
LAYERS = [(0, "#8A6A50", "#5E4634"), (35e3, "#A8502E", "#6E2E18"), (R_T - R_C, "#FF7A1F", "#C2410F"),
          (R_T - R_IC, "#FFD23F", "#E8A21A")]


def layer_cols(d):
    dd = d if d <= R_T else 2 * R_T - d
    cur = LAYERS[0]
    for L in LAYERS:
        if dd >= L[0]:
            cur = L
    return cur[1], cur[2]


def scene_tube(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    tp = phys_at(t)
    v = speed(tp)
    dd = dist(tp)
    c1, c2 = layer_cols(dd)
    p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 0), (W, 0)], [col(c2), col(c1), col(c2)]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    # parois qui défilent
    vis = min(4000, 60 + v * 1.4)
    off = (t * vis) % 260
    for k in range(-1, 10):
        y = k * 260 - off if dd <= R_T else k * 260 + off - 260
        for (x0, x1) in ((0, 210), (870, W)):
            c.drawRect(skia.Rect.MakeLTRB(x0, y, x1, y + 120), fill(c2, .5))
            r = random.Random(k * 7 + x0)
            for _ in range(3):
                cx = r.uniform(x0 + 20, x1 - 20)
                c.drawCircle(cx, y + r.uniform(140, 240), r.uniform(10, 26), fill(hexmix(c1, "#000000", .25)))
    c.drawLine(210, 0, 210, H, line(INK, 8))
    c.drawLine(870, 0, 870, H, line(INK, 8))
    # tube de verre
    c.drawRect(skia.Rect.MakeLTRB(210, 0, 870, H), fill("#0E1030", .55))
    # traits de vitesse
    r = random.Random(int(t * 20))
    n = int(clamp(v / 1500) * 14)
    for k in range(n):
        x = r.uniform(240, 840)
        y = r.uniform(0, H)
        c.drawLine(x, y, x, y + r.uniform(120, 360), line("#FFFFFF", 5, .5))
    # glow du noyau
    if key in ("noyau", "centre", "press"):
        gl = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial((540, 1100), 900, [col("#FFE9A0", .45), col("#FFE9A0", 0)]))
        c.drawRect(skia.Rect.MakeWH(W, H), gl)
    # Gérard, en apesanteur
    sway = math.sin(t * 1.3) * 8
    gy = 1300 + math.sin(t * 1.9) * 18
    stage = 0 if key != "press" else 1
    ger(c, 540, gy, .7, t, stage, arms="float" if key != "chute" or d_ > .6 else "down", lean=sway)
    if key == "chute":
        gerbub(c, t, b, 560, 860, .7)
    if key == "son":
        u = clamp((d_ - .4) / .2)
        sign(c, "MACH 1", 540, 1640, 64, "#FFE14D", -4, u)
        text(c, "(pas d'air, pas de « bang »)", 540, 1730, 44, "#FFFFFF", INK, 8, a=clamp((d_ - 1.2) / .2))
    if key == "kola":
        # panneau sur la paroi qui passe vers le haut
        y = lerp(1950, 1000, eout(clamp((d_ - .3) / 1.6)))
        shape(c, rrect(670, y - 110, 1070, y + 110, 18), "#FFFFFF", 7)
        text(c, "FORAGE DE KOLA", 870, y - 40, 40, INK)
        text(c, "12 262 m · 1970-1989", 870, y + 30, 36, "#C2410F")
        text(c, "RECORD DU MONDE", 870, y + 86, 30, "#6C7390")
    if key == "apes":
        # journal et chaussette qui flottent
        for k, (ox, oy, w_, h_, cc) in enumerate(((330, 1020, 150, 110, "#F2F2F7"), (760, 1180, 70, 110, "#D9534F"))):
            c.save()
            c.translate(ox + math.sin(t * 1.4 + k) * 30, oy + math.cos(t * 1.1 + k) * 30)
            c.rotate(t * 40 * (1 if k else -1))
            shape(c, rrect(-w_ / 2, -h_ / 2, w_ / 2, h_ / 2, 8), cc, 6)
            if k == 0:
                for j in range(4):
                    c.drawLine(-w_ / 2 + 14, -h_ / 2 + 22 + j * 22, w_ / 2 - 14, -h_ / 2 + 22 + j * 22, line(INK, 4, .5))
            c.restore()
        text(c, "0 kg", 540, 1720, 70, "#FFE14D", INK, 10, a=clamp((d_ - .8) / .2))
    if key == "noyau":
        text(c, "FER LIQUIDE", 540, 1700, 64, "#FFFFFF", INK, 10, a=clamp((d_ - .5) / .2))
    if key == "centre":
        u = clamp((d_ - .5) / .2)
        text(c, "Gérard : 34 000 km/h", 540, 1650, 56, "#FFE14D", INK, 10, a=u)
        text(c, "ISS : 28 000 km/h", 540, 1730, 46, "#FFFFFF", INK, 8, a=clamp((d_ - 1.2) / .2))
        if d_ > 1.6:
            bubble(c, 300, 980, "!", 50, back((d_ - 1.6) / .16), -4)
    if key == "press":
        u = clamp((d_ - .2) / .3)
        sign(c, "3 600 000 atm", 540, 1700, 60, "#FFFFFF", 3, u)
        gerbub(c, t, b, 560, 880, 1.2)


# ---------------------------------------------------------------- coupe de la Terre
CX, CY, CR = 540, 1100, 440


def scene_coupe(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    c.drawImage(STARS, 0, 0)
    # couches (à l'échelle des rayons)
    for rr, colr in ((1.0, "#8A6A50"), ((R_T - 35e3) / R_T, "#C2552E"), (R_C / R_T, "#FF8A1F"), (R_IC / R_T, "#FFD23F")):
        shape(c, oval(CX - CR * rr, CY - CR * rr, CX + CR * rr, CY + CR * rr), colr, 6)
    c.drawCircle(CX, CY, CR, line("#2B86DE", 10))
    c.drawCircle(CX, CY, CR + 6, line(INK, 5))
    # le tube
    if key == "trou":
        prog = eout(clamp((d_ - .4) / 2.0))
    else:
        prog = 1
    y0, y1 = CY - CR - 20, CY - CR - 20 + (2 * CR + 40) * prog
    c.drawLine(CX, y0, CX, y1, line(INK, 26))
    c.drawLine(CX, y0, CX, y1, line("#0E1030", 14))
    if key == "trou" and prog < 1:
        # foreuse générique
        shape(c, poly([(CX - 30, y1 - 40), (CX + 30, y1 - 40), (CX, y1 + 30)]), "#C9CBD6", 5)
    text(c, "PARIS", CX + 40, CY - CR - 40, 46, "#FFFFFF", INK, 8, align="left")
    text(c, "ÎLES ANTIPODES", CX, CY + CR + 90, 46, "#FFFFFF", INK, 8, a=clamp((d_ - 2.0) / .3) if key == "trou" else 1)
    if key == "trou":
        text(c, "12 742 km", CX - 60, CY + 10, 46, "#FFFFFF", INK, 8, align="right", a=clamp((d_ - 2.4) / .3))
    if key == "manteau":
        u = clamp((d_ - .3) / .3)
        for s_, x_, y_, colr in (("CROÛTE", 860, CY - CR + 10, "#FFFFFF"), ("MANTEAU", 860, CY - CR + 170, "#FFFFFF"),
                                 ("NOYAU", 860, CY - 60, "#FFE14D")):
            text(c, s_, x_, y_, 40, colr, INK, 7, a=u)
    # Gérard (point)
    if key != "trou":
        dd = dist(phys_at(t))
        y = CY - CR + 2 * CR * clamp(dd / (2 * R_T))
        ger(c, CX, y + 40, .14, t, 0, arms="float")
        c.drawCircle(CX, y, 60, line("#FFE14D", 5, .6 + .4 * math.sin(t * 8)))


# ---------------------------------------------------------------- l'arrivée, en plein Pacifique
OX, OY = 540, 1330      # bouche du tube sur une petite plateforme


def penguin(c, x, y, s, t, look=0.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    shape(c, oval(-70, -220, 70, 0), "#23202C", 7)
    c.drawOval(skia.Rect.MakeLTRB(-46, -170, 46, -10), fill("#FFFFFF"))
    shape(c, oval(-50, -290, 50, -190), "#23202C", 7)
    for sg in (-1, 1):
        c.drawCircle(sg * 20 + look * 10, -250, 13, fill("#FFFFFF"))
        c.drawCircle(sg * 20 + look * 14, -250, 6, fill(INK))
        c.drawLine(sg * 10, -280, sg * 60, -300, line("#FFD23F", 7))
    shape(c, poly([(-14 + look * 8, -232), (14 + look * 8, -232), (look * 30, -205)]), "#FF8A1F", 4)
    for sg in (-1, 1):
        shape(c, oval(sg * 30 - 24, -14, sg * 30 + 24, 10), "#FF8A1F", 4)
    c.restore()


def scene_ocean(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    p = skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 400), (0, 1150)], [col("#7FB8E8"), col("#DDEFFF")]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    # îles au loin (rochers génériques)
    shape(c, poly([(-40, 1160), (90, 1060), (180, 1100), (300, 1030), (420, 1160)]), "#5E7A5A", 6)
    # mer
    c.drawRect(skia.Rect.MakeLTRB(0, 1150, W, H), fill("#1F6FBF"))
    for k in range(8):
        y = 1190 + k * 90
        off = (t * 60 * (1 + k * .2)) % 200
        for x in range(-200, W + 200, 200):
            c.drawLine(x + off, y, x + off + 80, y, line("#BFE3FF", 5, .6))
    # plateforme + bouche du tube
    shape(c, rrect(OX - 300, OY - 10, OX + 300, OY + 60, 20), "#C9CBD6", 7)
    c.drawOval(skia.Rect.MakeLTRB(OX - 150, OY - 40, OX + 150, OY + 30), fill("#0E1030"))
    c.drawOval(skia.Rect.MakeLTRB(OX - 150, OY - 40, OX + 150, OY + 30), line(INK, 7))
    # Gérard sort jusqu'à la taille
    if key == "arrive":
        rise = eout(clamp((d_ - .8) / 1.0))
    else:
        rise = 1 - ein(clamp((d_ - 2.6) / .6))
    if rise > 0:
        c.save()
        cp = skia.Path()
        cp.addRect(skia.Rect.MakeLTRB(0, 0, W, OY - 5))
        cp.addOval(skia.Rect.MakeLTRB(OX - 150, OY - 40, OX + 150, OY + 30))
        c.clipPath(cp, skia.ClipOp.kIntersect, True)
        ger(c, OX, OY + lerp(520, 190, rise), .62, t, 0 if key == "arrive" else 1, arms="wave" if key == "arrive" and d_ > 1.8 else "down")
        c.restore()
    c.drawOval(skia.Rect.MakeLTRB(OX - 150, OY - 40, OX + 150, OY + 30), line("#9B9FB0", 4))
    # manchot
    look = -1 if (key == "zero" and d_ > 1.0) or key == "arrive" else 0
    penguin(c, OX + 230, OY + 20, .9, t, look)
    if key == "arrive" and d_ > 1.8:
        gerbub(c, t, b, OX, 920, 1.45)
    if key == "zero":
        if d_ > .5:
            bubble(c, OX + 260, 1020, "?", 56, back((d_ - .5) / .16), 4)
        if d_ > 2.3:
            text(c, "0 km/h", OX - 280, 1080, 64, "#FFE14D", INK, 10, a=clamp((d_ - 2.3) / .2))


# ---------------------------------------------------------------- HUD, légende, carton
def heat_c(u):
    stops = [(0, "#59E36A"), (.3, "#D7F03A"), (.55, "#FFC531"), (.8, "#FF7A1F"), (.97, "#FF2E2E"), (1, "#FF2EA6")]
    u = clamp(u)
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if a <= u <= b:
            return hexmix(ca, cb, (u - a) / (b - a))
    return "#FF2EA6"


def nb(n):
    s = "%d" % n
    out = ""
    while len(s) > 3:
        out = " " + s[-3:] + out
        s = s[:-3]
    return s + out


def dist_txt(m):
    if m < 999.5:
        return "%d M" % round(m)
    k = m / 1000
    if k < 99.95:
        return ("%.1f KM" % k).replace(".", ",")
    return "%s KM" % nb(round(k))


def time_txt(s):
    s = int(round(s))
    if s < 60:
        return "%d s" % s
    return "%d min %02d s" % (s // 60, s % 60)


assert dist_txt(KOLA) == "12,3 KM" and dist_txt(dist(T_CROSS)) == "12 742 KM" and dist_txt(dist(T_RT)) == "25 484 KM"


def hud(c, t, b):
    tp = phys_at(t)
    v = speed(tp) * 3.6
    colr = heat_c(v / 34000)
    d_ = t - b["start"]
    pop = 1 + .14 * (1 - eout(d_ / .22)) if b["p1"] != b["p0"] else 1.0
    c.save()
    c.translate(540, 262)
    c.scale(pop, pop)
    pan = rrect(-420, -135, 420, 135, 44)
    c.drawPath(pan, fill("#14121C", .94))
    c.drawPath(pan, line(colr, 8))
    head = "GÉRARD A PARCOURU"
    big = dist_txt(dist(tp))
    low = "T + %s · %s km/h" % (time_txt(tp), nb(round(v / 100) * 100 if v >= 1000 else round(v)))
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


CARD_LINES = ("Très approximatif : tube sans air ni frottement,",
              "Terre immobile, Gérard qui ne cuit pas.",
              "Gravité simplifiée : 9,82 m/s² jusqu'au noyau,",
              "puis décroissante : 38 min 40 s la traversée.",
              "Étude de A. Klotz (2015) : 38 min 11 s.",
              "Kola : 12 262 m (1970-1989). ISS : ~28 000 km/h.",
              "Gérard va bien. Il est calme.")
assert abs(T_CROSS - (38 * 60 + 40)) < 1


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
    text(c, "ALLER-RETOUR N° 2.", 0, 128, 86, "#FFD93B")
    c.restore()
    a = clamp((d_ - .5) / .25)
    for i, l in enumerate(CARD_LINES):
        text(c, l, 540, 1000 + i * 62, fit(l, 44, 960), "#A9A6BC", a=a)


SCN = dict(salon=scene_salon, tube=scene_tube, coupe=scene_coupe, ocean=scene_ocean)


def shake_amp(t):
    amp = 0
    for key, a0, dur, A in (("pousse", 2.0, .4, 10), ("chute", 0, .3, 8), ("fin", 2.5, .4, 10)):
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


_sp = [K["chute"], K["manteau"], K["noyau"], K["arrive"], K["retour"], CARD, END]
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
    print("son %.1f s, Kola %.1f s, noyau %.0f s, centre %.0f s (%.0f km/h), traversée %.0f s, aller-retour %.0f s"
          % (T_SON, T_KOLA, T_CMB, T_HALF, V_MAX_KMH, T_CROSS, T_RT))
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
