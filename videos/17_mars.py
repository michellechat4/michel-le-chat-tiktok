"""Michel responsable de tout : un point rouge dans le ciel à 3 h du matin. C'était Mars.
Gérard construit une fusée en carton ; 203 jours de trajet (durée réelle d'une mission de 2020), Michel dort tout du long.
Sur Mars : -60 °C, gravité 38 % (il saute presque 4 m), Olympus Mons comme griffoir, il se proclame empereur.
MIAOU par radio : 12 min 31 s (distance moyenne). Le jour martien dure 24 h 40 : tous les 37 jours, un repas de moins.
Il pousse Phobos « de la table » (2 m par siècle). Loi n° 1 : Gérard doit venir. Prochain départ : 26 mois.
Fin : Michel voit un point bleu dans le ciel. C'est la Terre. Gérard : « NON. »"""
import math, random, sys, os, subprocess
import importlib.util as _u
import numpy as np
import skia
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "moteur"))
import art
from art import (fill, line, col, hexmix, poly, rrect, oval, shape, text, jitter, clamp, lerp, eout, ein, back,
                 draw_cat, draw_moon, earth_rgba, STARS, bubble, wrap_rich, TF, INK, W, H, FPS)

# salon, Gérard sur le canapé, réveil : repris de la vidéo 16 (qui reprend la 08)
_sp = _u.spec_from_file_location("vit16", os.path.join(HERE, "16_vitesse.py"))
V16 = _u.module_from_spec(_sp)
_sp.loader.exec_module(V16)
V8 = V16.V8
sky_grad, fit, nb, FLOOR, SHELF_Y = V8.sky_grad, V8.fit, V8.nb, V8.FLOOR, V8.SHELF_Y
salon_bg, ger_couch, clock, panel = V16.salon_bg, V16.ger_couch, V16.clock, V16.panel

# ---------------------------------------------------------------- chiffres (calculés, pas recopiés)
TRAJET = 203                 # jours : lancement 30 juil. 2020 → atterrissage 18 févr. 2021, « a 203-day journey » (JPL/NASA)
TEMP = -60                   # °C, « -60 °C en moyenne » (CNES, dossier Mars ; -63 °C à l'équateur dans son tableau ; JPL : -53 °C)
GRAV = 0.38                  # « 38 % de celle de la Terre » (CNES ; JPL « 38 percent »)
SAUT_T = 1.5                 # m, saut d'un chat sur Terre (1,2 à 1,8 m, Catster ; déjà utilisé vidéo 08)
OLYMPUS = 21.2               # km au-dessus du niveau de référence (22,5 km au-dessus des plaines) (Vikidia)
EVEREST = 8848.86            # m (déjà utilisé vidéo 08)
SOL_S = 24 * 3600 + 39 * 60 + 35   # s, « 24 hours, 39 minutes, 35 seconds » (JPL, Mars at a Glance)
D_MOY = 225e6                # km, distance moyenne Terre-Mars (CNES ; Universe Today)
C_KMS = 299792.458           # km/s, vitesse de la lumière (exacte)
PHOBOS_FT = 6.6              # pieds par siècle (Smithsonian : « roughly 6.6 feet every 100 years »)
PHOBOS_FIN = (30, 50)        # millions d'années avant sa destruction (Smithsonian, d'après T. Hurford, NASA)
AN_T, AN_M = 365.256, 686.98  # jours, périodes orbitales de la Terre et de Mars (valeurs standard)

SAUT_M = SAUT_T / GRAV                         # même vitesse d'élan, gravité 0,38 → hauteur / 0,38
X_SAUT = 1 / GRAV
X_EVEREST = OLYMPUS * 1000 / EVEREST
SOL_H = SOL_S / 3600
RECUL = (SOL_S - 86400) / 60                   # minutes de retard du petit-déj par jour terrestre
J_REPAS = (SOL_S / 86400) / (SOL_S / 86400 - 1)  # jours terrestres pour avoir un sol (donc un repas) de moins
RADIO = D_MOY / C_KMS                           # s
PHOBOS_M = PHOBOS_FT * 0.3048
SYNODIQUE = 1 / (1 / AN_T - 1 / AN_M)          # jours entre deux fenêtres de tir Terre → Mars
MOIS = SYNODIQUE / (365.25 / 12)

assert round(SAUT_M, 1) == 3.9 and round(X_SAUT, 1) == 2.6
assert round(X_EVEREST, 1) == 2.4
assert round(SOL_H, 2) == 24.66 and round(RECUL) == 40
assert round(J_REPAS) == 37
assert divmod(round(RADIO), 60) == (12, 31)
assert round(PHOBOS_M) == 2
assert round(MOIS) == 26 and round(SYNODIQUE) == 780

J_ARR = TRAJET
J_REP = J_ARR + round(J_REPAS)


def fr(x, n=0):
    return (("%." + str(n) + "f") % x).replace(".", ",")


# ---------------------------------------------------------------- chronologie
# (clé, durée, jour, légende, Gérard dit, décor, sous-titre du compteur)
RAW = [
    ("hook", 3.2, 0, "CE CHAT A FONDÉ | *UN EMPIRE SUR MARS.*", None, "mars", "1 habitant"),
    ("point", 3.4, 0, "Tout a commencé par | *un point rouge* dans le ciel.", None, "salon", "sur Terre, 3 h du matin"),
    ("cetait", 3.4, 0, "C'était *Mars.* | Michel veut *l'attraper.*", "Michel… il est 3 h.", "salon", "sur Terre, 3 h du matin"),
    ("fusee", 3.4, 0, "Gérard lui construit | *une fusée en carton.*", "Bon voyage !", "salon", "sur Terre"),
    ("decol", 3.2, 0, "Décollage. | Gérard *dort enfin.*", None, "decol", "départ"),
    ("voyage", 3.8, J_ARR, "Trajet : *%d jours.* | Michel dort *tout du long.*" % TRAJET, None, "voyage", "en route"),
    ("arrive", 3.3, J_ARR, "Arrivée sur Mars : | *%d °C* en moyenne." % TEMP, None, "mars", "sur Mars"),
    ("saut", 3.5, J_ARR + 1, "Gravité : *38 %%.* | Il saute à *%s m.*" % fr(SAUT_M, 1), None, "mars", "gravité 38 %"),
    ("volcan", 3.5, J_ARR + 2, "Le plus haut volcan : *21 km.* | *%s fois* l'Everest." % fr(X_EVEREST, 1), None, "volcan", "Olympus Mons"),
    ("griffe", 3.0, J_ARR + 2, "Son nouveau | *griffoir.*", None, "griffe", "Olympus Mons"),
    ("empereur", 3.2, J_ARR + 3, "Il se proclame | *empereur de Mars.*", None, "mars", "empire : 1 habitant"),
    ("miaou", 3.6, J_ARR + 3, "Premier message : *MIAOU.* | Trajet radio : *%d min %02d s.*" % divmod(round(RADIO), 60), None, "radio", "message pour Gérard"),
    ("recu", 3.2, J_ARR + 3, "Gérard le reçoit | *à 3 h 12.*", "Même d'ici…", "salon", "sur Terre"),
    ("sol", 3.5, J_ARR + 7, "Un jour sur Mars : *24 h 40.* | Le petit-déj *recule chaque jour.*", None, "mars", "1 jour martien = 24 h 40"),
    ("repas", 3.4, J_REP, "Tous les *%d jours,* | il perd *un repas entier.*" % round(J_REPAS), None, "mars", "repas perdus : 1"),
    ("phobos", 3.4, 300, "Mars a une petite lune. | Michel *la pousse.*", None, "phobos", "lune de Mars : Phobos"),
    ("patient", 3.5, 300, "Elle s'approche de *%d m par siècle.* | Michel est *patient.*" % round(PHOBOS_M), None, "phobos", "Phobos"),
    ("loi", 3.4, 365, "Loi n° 1 de l'empire : | *Gérard doit venir.*", None, "mars", "empire : 1 habitant"),
    ("fenetre", 3.4, 365, "Prochain départ possible : | dans *%d mois.*" % round(MOIS), "Ouf.", "salon", "sur Terre"),
    ("bleu", 3.4, 400, "Un soir, Michel voit | *un point bleu* dans le ciel.", None, "mars", "sur Mars, 3 h du matin"),
    ("fin", 3.8, 400, "C'est *la Terre.* | Michel veut *l'attraper.*", "NON.", "salon", "sur Terre"),
]
CARD_DUR = 4.0
BEATS = []
_t, _d = 0.0, 0
for key, dur, d, cap, ger_, dec, low in RAW:
    BEATS.append(dict(key=key, start=_t, dur=dur, d0=_d, d1=d, cap=cap, ger=ger_, dec=dec, low=low))
    _t += dur
    _d = d
CARD = _t
END = CARD + CARD_DUR
K = {b["key"]: b["start"] for b in BEATS}
JUMPS = sorted(b["start"] for b in BEATS if b["d1"] > b["d0"] and b["key"] != "voyage")
ROLL = .7


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
    d_ = t - b["start"]
    if b["key"] == "voyage":
        f = clamp((d_ - .3) / (b["dur"] - .8))
    else:
        f = eout(d_ / ROLL)
    return lerp(b["d0"], b["d1"], f)


# ---------------------------------------------------------------- objets
MARS_PATCH = [(random.Random(i).uniform(-1, 1), random.Random(i + 40).uniform(-1, 1), random.Random(i + 80).uniform(.12, .32)) for i in range(14)]


def mars_globe(c, x, y, r, rot=0.0):
    sh = skia.GradientShader.MakeRadial((x - r * .35, y - r * .35), r * 1.5, [col("#FFA66B"), col("#D35A2E"), col("#7A2A18")], [0, .55, 1])
    circ = oval(x - r, y - r, x + r, y + r)
    c.drawPath(circ, skia.Paint(AntiAlias=True, Shader=sh))
    c.save()
    c.clipPath(circ, skia.ClipOp.kIntersect, True)
    for (px, py, rr) in MARS_PATCH:
        xx = x + ((px + rot) % 2 - 1) * r
        c.drawOval(skia.Rect.MakeLTRB(xx - rr * r, y + py * r * .8 - rr * r * .5, xx + rr * r, y + py * r * .8 + rr * r * .5), fill("#8E3420", .45))
    c.drawOval(skia.Rect.MakeLTRB(x - r * .45, y - r * 1.05, x + r * .45, y - r * .8), fill("#FFF4EC", .95))
    c.restore()
    c.drawPath(circ, line(INK, max(3, r * .05)))


def glow_dot(c, x, y, r, colr, t, a=1.0):
    pul = 1 + .15 * math.sin(t * 6)
    for k in range(4, 0, -1):
        c.drawCircle(x, y, r * (1 + k * .7) * pul, fill(colr, .12 * a))
    c.drawCircle(x, y, r, fill(colr, a))
    c.drawCircle(x, y, r * .45, fill("#FFFFFF", .7 * a))


def helmet(c, x, y, s):
    c.drawCircle(x, y - 270 * s, 190 * s, fill("#BEE8FF", .22))
    c.drawCircle(x, y - 270 * s, 190 * s, line("#E9F6FF", max(3, 8 * s / .42)))
    c.drawCircle(x, y - 270 * s, 190 * s, line(INK, max(2, 3 * s / .42)))


def crown(c, x, y, s, a=1.0):
    p = poly([(-70, 0), (-80, -80), (-40, -40), (0, -100), (40, -40), (80, -80), (70, 0)])
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    shape(c, p, "#FFD23F", 8, a)
    for xx, yy in ((0, -100), (-80, -80), (80, -80)):
        c.drawCircle(xx, yy, 12, fill("#FF4B6E", a))
    c.restore()


def michel(c, x, y, s, t, mood="open", vib=0.0, crowned=False, helm=True):
    draw_cat(c, x, y, s, t, mood, vib)
    if crowned:
        crown(c, x, y - 380 * s, s * 1.1)
    if helm:
        helmet(c, x, y, s)


def box_rocket(c, x, y, s, t, flame=0.0, mood="bliss", shake=0.0):
    """Fusée en carton, base en (x, y)."""
    j = jitter(t, 5)
    c.save()
    c.translate(x + j[0] * shake, y + j[1] * shake)
    c.scale(s, s)
    if flame > 0:
        fl = 1 + .25 * math.sin(t * 40)
        for k, (cc, w_, h_) in enumerate((("#FF5A1F", 90, 300), ("#FFB31F", 62, 210), ("#FFF3B0", 34, 120))):
            c.drawPath(poly([(-w_, 0), (0, h_ * fl * flame), (w_, 0)]), fill(cc, .95))
    for sg in (-1, 1):
        shape(c, poly([(sg * 110, -40), (sg * 190, 20), (sg * 190, -10), (sg * 110, -170)]), "#B9824A", 7)
    shape(c, rrect(-115, -440, 115, 0, 10), "#D9A066", 8)
    for xx in (-60, 0, 60):
        c.drawLine(xx, -430, xx + 6, -10, line("#B9824A", 4, .7))
    c.drawRect(skia.Rect.MakeLTRB(-115, -150, 115, -118), fill("#E8D9A8", .9))
    shape(c, poly([(-135, -440), (0, -640), (135, -440)]), "#C98C52", 8)
    # hublot avec Michel
    hub = oval(-78, -360, 78, -204)
    c.drawPath(hub, fill("#1B2350"))
    c.save()
    c.clipPath(hub, skia.ClipOp.kIntersect, True)
    draw_cat(c, 0, -282 + 272 * .42 + 10, .42, t, mood)
    c.restore()
    c.drawPath(hub, line(INK, 9))
    c.drawPath(hub, line("#E8D9A8", 4))
    text(c, "MARS", 0, -70, 54, "#7A3A12")
    c.restore()


def phobos_shape(c, x, y, s, rot=0.0):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    p = skia.Path()
    pts = [(-200, -20), (-150, -110), (-40, -130), (90, -105), (190, -60), (215, 30), (150, 110), (20, 125), (-120, 105), (-205, 55)]
    p.moveTo(*pts[0])
    for i in range(len(pts)):
        a_, b_ = pts[i], pts[(i + 1) % len(pts)]
        p.quadTo(a_[0] * 1.08, a_[1] * 1.08, (a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2)
    p.close()
    shape(c, p, "#8C7B6B", 8)
    for (cx_, cy_, r_) in ((-110, -10, 34), (60, 30, 46), (130, -40, 20), (-30, 70, 18), (-40, -70, 16)):
        c.drawCircle(cx_, cy_, r_, fill("#6B5C4F"))
        c.drawCircle(cx_ + 4, cy_ + 4, r_ * .7, fill("#7C6C5D"))
    c.restore()


def radio_box(c, x, y, a=1.0):
    shape(c, rrect(x - 80, y - 110, x + 80, y, 16), "#6B4A33", 6, a)
    c.drawCircle(x - 30, y - 55, 32, fill("#2B2230", a))
    for k in range(3):
        c.drawCircle(x - 30, y - 55, 10 + k * 8, line("#5A4A60", 3, a))
    c.drawCircle(x + 40, y - 70, 14, fill("#FFD23F", a))
    c.drawLine(x + 50, y - 110, x + 100, y - 230, line(INK, 6, a))
    c.drawCircle(x + 100, y - 230, 9, fill("#FF4B3A", a))


def bowl(c, x, y, full=False):
    shape(c, poly([(x - 80, y), (x + 80, y), (x + 62, y - 46), (x - 62, y - 46)]), "#D9534F", 6)
    if full:
        for k in range(7):
            c.drawCircle(x - 48 + k * 16, y - 52 - (k % 2) * 8, 11, fill("#9B5A2C"))


# ---------------------------------------------------------------- Mars, en surface
G_M = 1500
ROCKS = [(random.Random(i).uniform(0, W), random.Random(i + 9).uniform(G_M + 30, 1880), random.Random(i + 19).uniform(14, 46)) for i in range(16)]


def mars_bg(c, t, night=False):
    if night:
        sky_grad(c, "#07051A", "#3A1E30", 300, G_M)
        rr = random.Random(21)
        for i in range(120):
            c.drawCircle(rr.uniform(0, W), rr.uniform(0, G_M - 200), rr.uniform(1, 3.2), fill("#FFFFFF", rr.uniform(.4, 1)))
    else:
        sky_grad(c, "#E9B987", "#C98457", 300, G_M)
        c.drawCircle(860, 820, 34, fill("#F4F6FF", .9))
        c.drawCircle(860, 820, 60, fill("#DCE8FF", .18))
    hill = skia.Path()
    hill.moveTo(0, G_M - 60)
    for k in range(9):
        hill.quadTo(k * 135 + 67, G_M - 60 - (90 if k % 2 else 40), (k + 1) * 135, G_M - 60)
    hill.lineTo(W, G_M + 10)
    hill.lineTo(0, G_M + 10)
    hill.close()
    shape(c, hill, "#9C3F25" if not night else "#4A2026", 6)
    c.drawRect(skia.Rect.MakeLTRB(0, G_M, W, H), fill("#B9532F" if not night else "#5E2A25"))
    c.drawLine(0, G_M, W, G_M, line(INK, 7))
    for (x, y, r) in ROCKS:
        c.drawOval(skia.Rect.MakeLTRB(x - r, y - r * .55, x + r, y + r * .3), fill("#8E3A22" if not night else "#43201F"))


def flag(c, x, y, h, a=1.0, wave=0.0):
    c.drawLine(x, y, x, y - h, line(INK, 9, a))
    p = skia.Path()
    p.moveTo(x, y - h)
    p.quadTo(x + 90, y - h - 20 + wave * 14, x + 180, y - h + 6)
    p.lineTo(x + 180, y - h + 116)
    p.quadTo(x + 90, y - h + 90 + wave * 14, x, y - h + 110)
    p.close()
    shape(c, p, "#FFFFFF", 7, a)
    # empreinte de patte
    cx_, cy_ = x + 92, y - h + 62
    c.drawOval(skia.Rect.MakeLTRB(cx_ - 26, cy_ - 8, cx_ + 26, cy_ + 30), fill("#F49A3A", a))
    for dx, dy in ((-30, -20), (-10, -36), (12, -36), (32, -20)):
        c.drawCircle(cx_ + dx, cy_ + dy, 11, fill("#F49A3A", a))


def throne(c, x, y):
    shape(c, poly([(x - 170, y), (x - 140, y - 160), (x - 30, y - 200), (x + 120, y - 170), (x + 170, y)]), "#8E3A22", 7)
    c.drawLine(x - 120, y - 120, x + 110, y - 110, line("#6E2A18", 5, .7))


def scroll(c, x, y, s_, a=1.0, w=520):
    p = rrect(x - w / 2, y - 70, x + w / 2, y + 70, 16)
    c.drawPath(p, fill("#FFF3D6", a))
    c.drawPath(p, line(INK, 6, a))
    for sg in (-1, 1):
        shape(c, rrect(x + sg * w / 2 - 22, y - 86, x + sg * w / 2 + 22, y + 86, 20), "#E8D2A0", 6, a)
    text(c, s_, x, y + 18, fit(s_, 50, w - 70), "#7A3A12", a=a)


def scene_mars(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    night = key == "bleu"
    mars_bg(c, t, night)
    G = G_M + 20
    if key == "hook":
        throne(c, 540, G)
        flag(c, 790, G - 10, 420, wave=math.sin(t * 3))
        michel(c, 520, G - 190, .4, t, "open" if d_ < 2 else "wink", crowned=True)
        return
    if key == "arrive":
        c.save()
        c.translate(800, G + 10)
        c.rotate(14)
        box_rocket(c, 0, 0, .6, t, 0, "open")
        c.restore()
        u = eout(clamp((d_ - .2) / .5))
        mx = lerp(760, 360, u)
        michel(c, mx, G, .4, t, "open", vib=6 if d_ > .8 else 0)
        a = clamp((d_ - .9) / .2)
        if a > 0:
            # thermomètre
            tx, ty = 140, 820
            shape(c, rrect(tx - 30, ty, tx + 30, ty + 380, 30), "#FFFFFF", 6, a)
            c.drawCircle(tx, ty + 400, 50, fill("#3FA9FF", a))
            c.drawCircle(tx, ty + 400, 50, line(INK, 6, a))
            c.drawRect(skia.Rect.MakeLTRB(tx - 14, ty + 300, tx + 14, ty + 380), fill("#3FA9FF", a))
            text(c, "%d °C" % TEMP, tx + 60, ty + 120, 58, "#3FA9FF", INK, 9, align="left", a=a)
        if d_ > 1.7:
            bubble(c, 470, 1050, "Un plaid. Vite.", 48, back((d_ - 1.7) / .16), -3)
        return
    if key == "saut":
        PX = 175          # px par mètre
        for h_, lab, cc in ((SAUT_T, "Terre : %s m" % fr(SAUT_T, 1), "#FFFFFF"), (SAUT_M, "Mars : %s m" % fr(SAUT_M, 1), "#FFE14D")):
            yy = G - h_ * PX
            c.drawPath(skia.Path().moveTo(80, yy).lineTo(1000, yy),
                       skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6, Color=col(cc, .9), PathEffect=skia.DashPathEffect.Make([24, 16], 0)))
            text(c, lab, 90, yy - 18, 46, cc, INK, 8, align="left")
        per = 2.4
        ph = ((d_ - .2) % per) / per if d_ > .2 else 0
        hgt = math.sin(ph * math.pi) * SAUT_M * PX
        michel(c, 640, G - hgt, .36, t, "bliss" if hgt > 300 else "open")
        if hgt < 30 and d_ > .3:
            for k in range(6):
                c.drawCircle(640 + (k - 2.5) * 50, G - 10 - (k % 2) * 12, 16, fill("#D98A5A", .7))
        return
    if key == "empereur":
        throne(c, 540, G)
        u = clamp((d_ - .4) / .5)
        flag(c, 790, G - 10, 420 * eout(clamp(d_ / .4)), wave=math.sin(t * 3))
        michel(c, 520, G - 190, .4, t, "open" if d_ < 1.6 else "bliss")
        if u < 1:
            crown(c, 520, lerp(400, G - 190 - 380 * .4, ein(u)), .44)
        else:
            crown(c, 520, G - 190 - 380 * .4, .44)
            r = random.Random(4)
            for i in range(10):
                ph = clamp((d_ - .9) / .8)
                a_ = r.uniform(0, 6.28)
                c.drawCircle(520 + math.cos(a_) * 200 * ph, G - 340 + math.sin(a_) * 200 * ph, 9 * (1 - ph) + 1, fill("#FFE14D", 1 - ph))
        return
    if key == "sol":
        # le Soleil traverse le ciel, le petit-déj recule
        u = clamp((d_ - .1) / 3.2)
        michel(c, 330, G, .4, t, "open")
        bowl(c, 600, G + 40)
        a = clamp((d_ - .3) / .2)
        panel(c, a, 640, 1000)
        text(c, "PETIT-DÉJ DE MICHEL", 540, 712, 44, "#FFFFFF", INK, 7, a=a)
        text(c, "(heure de Gérard)", 540, 762, 36, "#C9C6D8", a=a)
        n = min(3, int(clamp((d_ - .5) / 2.4) * 4))
        for k in range(n + 1):
            m = 7 * 60 + round(k * RECUL)
            text(c, "jour %d : %d h %02d" % (k + 1, m // 60, m % 60), 540, 830 + k * 48, 44, "#FFE14D" if k == n else "#A9A6BC", a=a)
        return
    if key == "repas":
        michel(c, 330, G, .4, t, "open", vib=4 + 4 * (d_ > 1.0))
        bowl(c, 640, G + 40)
        a = clamp((d_ - .4) / .2)
        if a > 0:
            c.drawLine(560, G - 90, 720, G + 50, line("#FF2E2E", 22, a))
            c.drawLine(720, G - 90, 560, G + 50, line("#FF2E2E", 22, a))
        if d_ > 1.3:
            bubble(c, 400, 1080, "Je porte plainte.", 50, back((d_ - 1.3) / .16), -3)
        return
    if key == "loi":
        throne(c, 540, G)
        flag(c, 790, G - 10, 420, wave=math.sin(t * 3))
        michel(c, 520, G - 190, .4, t, "open")
        crown(c, 520, G - 190 - 380 * .4, .44)
        s_ = back((d_ - .5) / .2)
        if d_ > .5:
            c.save()
            c.translate(540, 1000)
            c.scale(s_, s_)
            scroll(c, 0, 0, "LOI N° 1 : GÉRARD VIENT.", 1.0, 760)
            c.restore()
        return
    if key == "bleu":
        ex, ey = 780, 760
        glow_dot(c, ex, ey, 14, "#4FA3FF", t)
        wig = math.sin(t * 22) * 10 * clamp((d_ - 1.0) / .3)
        michel(c, 380 + wig, G, .42, t, "open")
        if d_ > .8:
            text(c, "!", 380, G - 470, 110, "#FFE14D", INK, 12, a=clamp((d_ - .8) / .15))
        if d_ > 1.6:
            c.drawPath(skia.Path().moveTo(470, G - 330).quadTo(640, 900, ex - 30, ey + 30),
                       skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6, Color=col("#FFFFFF", .7),
                                  PathEffect=skia.DashPathEffect.Make([20, 14], -t * 60)))
        return


# ---------------------------------------------------------------- Olympus Mons
def scene_volcan(c, t, b):
    d_ = t - b["start"]
    sky_grad(c, "#E9B987", "#C98457", 300, 1600)
    G = 1560
    PXK = 33            # px par km (échelle verticale ; largeur non à l'échelle)
    u = eout(clamp((d_ - .2) / 1.0))
    hO = OLYMPUS * PXK * u
    dome = skia.Path()
    dome.moveTo(-200, G)
    dome.cubicTo(150, G - hO * .25, 280, G - hO, 560, G - hO)
    dome.cubicTo(840, G - hO, 980, G - hO * .25, W + 200, G)
    dome.close()
    shape(c, dome, "#B5502E", 8)
    # caldeira
    if u > .5:
        c.drawOval(skia.Rect.MakeLTRB(470, G - hO - 12, 650, G - hO + 18), fill("#7A2E1C"))
    c.drawRect(skia.Rect.MakeLTRB(0, G, W, H), fill("#9C3F25"))
    c.drawLine(0, G, W, G, line(INK, 7))
    # Everest à la même échelle
    a = clamp((d_ - 1.1) / .3)
    if a > 0:
        hE = EVEREST / 1000 * PXK
        ev = poly([(80, G), (230, G - hE), (380, G)])
        shape(c, ev, "#8A8F9C", 7, a)
        c.drawPath(poly([(230, G - hE), (196, G - hE + 70), (215, G - hE + 58), (232, G - hE + 76), (262, G - hE + 72)]), fill("#FFFFFF", a))
        text(c, "Everest", 230, G - hE - 30, 46, "#FFFFFF", INK, 8, a=a)
        text(c, "8,8 km", 230, G - hE + 140, 40, "#FFFFFF", INK, 7, a=a)
    if u > .9:
        text(c, "Olympus Mons : 21 km", 600, G - hO - 60, 54, "#FFE14D", INK, 9)
        draw_cat(c, 560, G - hO, .07, t, "open")
    if d_ > 2.2:
        text(c, "(largeur pas à l'échelle : 600 km)", 540, G + 120, 36, "#FFE1C8", a=clamp((d_ - 2.2) / .2))


SCRATCH = [(-90 + k * 70, k * .11) for k in range(5)]


def scene_griffe(c, t, b):
    d_ = t - b["start"]
    sky_grad(c, "#E9B987", "#C98457", 300, 1600)
    wall = poly([(380, 1700), (1180, 600), (1180, 1900), (380, 1900)])
    shape(c, wall, "#B5502E", 8)
    c.drawRect(skia.Rect.MakeLTRB(0, 1600, W, H), fill("#9C3F25"))
    c.drawLine(0, 1600, 470, 1600, line(INK, 7))
    # griffures qui s'accumulent
    n = int(clamp((d_ - .2) / 2.2) * 5) + (1 if d_ > .2 else 0)
    for i in range(min(n, 5)):
        x0 = 640 + i * 90
        y0 = 1280 - i * 80
        for k in range(4):
            c.drawLine(x0 + k * 22, y0, x0 + k * 22 + 40, y0 + 200, line("#5E1F12", 9))
    paw = math.sin(t * 18) * 40
    draw_cat(c, 420, 1610, .42, t, "bliss", 3)
    helmet(c, 420, 1610, .42)
    c.drawOval(skia.Rect.MakeLTRB(540, 1280 + paw - 30, 620, 1280 + paw + 30), fill("#FFE1B0"))
    c.drawOval(skia.Rect.MakeLTRB(540, 1280 + paw - 30, 620, 1280 + paw + 30), line(INK, 6))
    rr = random.Random(int(t * 12))
    for k in range(6):
        c.drawCircle(600 + rr.uniform(-40, 120), 1300 + rr.uniform(-60, 200), rr.uniform(6, 16), fill("#E3A07A", .7))
    if d_ > .4:
        text(c, "scritch", 820, 940 + 20 * math.sin(t * 9), 64, "#FFFFFF", INK, 9, a=clamp((d_ - .4) / .2))


# ---------------------------------------------------------------- salon (Terre)
def scene_salon(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    night = key not in ("fenetre",)
    salon_bg(c, t, b, night)
    G = FLOOR + 10
    wx, wy = 70 + 70, 980 + 210        # point rouge dans la fenêtre
    if key == "point":
        clock(c, "03:00")
        ger_couch(c, t, 0, asleep=True)
        glow_dot(c, wx, wy, 10, "#FF4B3A", t)
        draw_cat(c, 260, G, .34, t, "open")
        if d_ > 1.0:
            text(c, "!", 260, G - 170, 90, "#FFE14D", INK, 10, a=clamp((d_ - 1.0) / .15))
        return
    if key == "cetait":
        clock(c, "03:00")
        ger_couch(c, t, 1)
        glow_dot(c, wx, wy, 10, "#FF4B3A", t)
        if d_ > .3:
            a = clamp((d_ - .3) / .2)
            mars_globe(c, 380, 820, 70 * a + 1)
            c.drawPath(skia.Path().moveTo(wx + 20, wy - 20).lineTo(330, 870), line("#FFFFFF", 4, .6 * a))
            text(c, "MARS", 380, 730, 46, "#FFFFFF", INK, 8, a=a)
        ph = (d_ * 1.6) % 1
        hop = math.sin(ph * math.pi) * 160
        draw_cat(c, 250, G - hop, .34, t, "open")
        V8.gerbub(c, t, b, 700, 1110)
        return
    if key == "fusee":
        clock(c, "03:20")
        ger_couch(c, t, 0)
        box_rocket(c, 280, G + 6, .62, t, 0, "open" if d_ < 1.8 else "wink")
        V8.gerbub(c, t, b, 700, 1110)
        return
    if key == "recu":
        clock(c, "03:12")
        ger_couch(c, t, 2 if d_ > .6 else 0, asleep=d_ < .6, zz=d_ < .6)
        radio_box(c, 300, G + 10)
        if d_ > .3:
            bubble(c, 300, G - 300, "MIAOU.", 58, back((d_ - .3) / .16), -4)
        V8.gerbub(c, t, dict(b, start=b["start"] + .9), 700, 1110)
        return
    if key == "fenetre":
        ger_couch(c, t, 0)
        # calendrier
        x0, y0 = 360, 860
        shape(c, rrect(x0, y0, x0 + 230, y0 + 250, 10), "#FFFFFF", 6)
        c.drawRect(skia.Rect.MakeLTRB(x0 + 4, y0 + 4, x0 + 226, y0 + 60), fill("#D9534F"))
        text(c, "DÉPART", x0 + 115, y0 + 48, 36, "#FFFFFF")
        text(c, "+%d" % round(MOIS), x0 + 115, y0 + 160, 84, INK)
        text(c, "MOIS", x0 + 115, y0 + 220, 40, INK)
        draw_cat_absent(c)
        V8.gerbub(c, t, b, 700, 1110)
        return
    if key == "fin":
        clock(c, "03:00")
        ger_couch(c, t, 0 if d_ < .5 else 2, asleep=d_ < .5, zz=d_ < .5)
        radio_box(c, 300, G + 10)
        if d_ > .2:
            bubble(c, 300, G - 300, "J'ARRIVE.", 58, back((d_ - .2) / .16), -4)
        glow_dot(c, wx, wy, 10, "#FF4B3A", t, .8)
        V8.gerbub(c, t, dict(b, start=b["start"] + 1.0), 700, 1110)
        return


def draw_cat_absent(c):
    text(c, "(pas de Michel)", 230, FLOOR - 60, 40, "#7B4A2B", "#FFF5E0", 6)


# ---------------------------------------------------------------- décollage
def scene_decol(c, t, b):
    d_ = t - b["start"]
    sky_grad(c, "#06061A", "#22305E", 300, 1500)
    rr = random.Random(5)
    for i in range(90):
        c.drawCircle(rr.uniform(0, W), rr.uniform(0, 1400), rr.uniform(1, 3), fill("#FFFFFF", rr.uniform(.3, 1)))
    glow_dot(c, 860, 700, 9, "#FF4B3A", t)
    G = 1600
    # maison de Gérard
    shape(c, rrect(560, G - 380, 960, G, 4), "#E8C79A", 7)
    shape(c, poly([(530, G - 380), (760, G - 560), (990, G - 380)]), "#A0463A", 7)
    c.drawRect(skia.Rect.MakeLTRB(620, G - 300, 760, G - 180), fill("#1B2350"))
    c.drawRect(skia.Rect.MakeLTRB(620, G - 300, 760, G - 180), line(INK, 8))
    for k in range(3):
        ph = (t * .6 + k / 3) % 1
        text(c, "z", 700 + ph * 60, G - 320 - ph * 100, 34 + 22 * ph, "#FFFFFF", INK, 6, a=1 - ph)
    c.drawRect(skia.Rect.MakeLTRB(0, G, W, H), fill("#24432E"))
    c.drawLine(0, G, W, G, line(INK, 6))
    u = ein(clamp((d_ - .5) / 2.2))
    y = lerp(G + 4, -500, u)
    # fumée
    rs_ = random.Random(7)
    for i in range(14):
        ph = clamp((d_ - .3 - i * .05) / 1.5)
        if ph <= 0:
            continue
        c.drawCircle(260 + rs_.uniform(-140, 140) * ph, G - 10 - rs_.uniform(0, 80), 30 + 70 * ph, fill("#D8D8E2", .6 * (1 - ph * .6)))
    box_rocket(c, 260, y, .55, t, 1.0 if d_ > .3 else 0, "open", shake=6 if d_ < .8 else 0)


# ---------------------------------------------------------------- voyage Terre → Mars
def bez(p0, p1, p2, u):
    return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0], (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1])


def scene_voyage(c, t, b):
    d_ = t - b["start"]
    c.drawImage(STARS, 0, 0)
    E, M = (230, 1500, 105), (850, 780, 115)
    img, x0, y0 = earth_rgba(E[2], cx=E[0], cy=E[1])
    c.drawImage(img, x0, y0)
    c.drawCircle(E[0], E[1], E[2], line(INK, 6))
    mars_globe(c, M[0], M[1], M[2], t * .05)
    p0, p1, p2 = (E[0] + 80, E[1] - 110), (200, 700), (M[0] - 130, M[1] - 20)
    path = skia.Path().moveTo(*p0).quadTo(*p1, *p2)
    c.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5, Color=col("#FFFFFF", .55), PathEffect=skia.DashPathEffect.Make([18, 12], 0)))
    u = clamp((d_ - .3) / (b["dur"] - .8))
    x, y = bez(p0, p1, p2, u)
    x2, y2 = bez(p0, p1, p2, min(1, u + .01))
    ang = math.degrees(math.atan2(y2 - y, x2 - x)) + 90
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    box_rocket(c, 0, 120, .3, t, .6, "bliss")
    c.restore()
    for k in range(3):
        ph = (t * .7 + k / 3) % 1
        text(c, "z", x + 80 + ph * 60, y - 60 - ph * 90, 36 + 22 * ph, "#FFFFFF", INK, 6, a=1 - ph)
    text(c, "jour %d" % round(u * TRAJET), 540, 1720, 72, "#FFFFFF", INK, 11)


# ---------------------------------------------------------------- message radio
def scene_radio(c, t, b):
    d_ = t - b["start"]
    c.drawImage(STARS, 0, 0)
    M, E = (250, 820, 130), (840, 1420, 105)
    mars_globe(c, M[0], M[1], M[2], .3)
    img, x0, y0 = earth_rgba(E[2], cx=E[0], cy=E[1])
    c.drawImage(img, x0, y0)
    c.drawCircle(E[0], E[1], E[2], line(INK, 6))
    draw_cat(c, M[0] + 20, M[1] - M[2] + 30, .16, t, "open")
    a0, a1 = (M[0] + 110, M[1] + 90), (E[0] - 90, E[1] - 80)
    c.drawPath(skia.Path().moveTo(*a0).lineTo(*a1),
               skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=4, Color=col("#FFFFFF", .4), PathEffect=skia.DashPathEffect.Make([14, 12], 0)))
    u = clamp((d_ - .3) / 2.6)
    x, y = lerp(a0[0], a1[0], u), lerp(a0[1], a1[1], u)
    ang = math.degrees(math.atan2(a1[1] - a0[1], a1[0] - a0[0]))
    for k in range(3):
        r_ = 40 + k * 26
        p = skia.Path()
        p.addArc(skia.Rect.MakeLTRB(x - r_ - k * 30, y - r_, x + r_ - k * 30, y + r_), -50, 100)
        c.save()
        c.translate(x, y)
        c.rotate(ang)
        c.translate(-x, -y)
        c.drawPath(p, line("#FFE14D", 7, (1 - k * .25) * (1 if 0 < u < 1 else 0)))
        c.restore()
    if 0 < u < 1:
        text(c, "MIAOU.", x - 40, y - 70, 54, "#FFFFFF", INK, 8)
    tot = round(RADIO * u)
    text(c, "%d min %02d s" % divmod(tot, 60), 540, 1720, 72, "#FFFFFF", INK, 11)
    text(c, "225 millions de km", 300, 1300, 42, "#C9C6D8")
    text(c, "(en moyenne)", 300, 1350, 38, "#C9C6D8")


# ---------------------------------------------------------------- Phobos
def scene_phobos(c, t, b):
    key = b["key"]
    d_ = t - b["start"]
    c.drawImage(STARS, 0, 0)
    mars_globe(c, 540, 2350, 1050, .4)
    px, py = 560, 1030
    bob = 0
    if key == "phobos":
        taps = [.8, 1.6, 2.4]
        for tk in taps:
            if 0 <= d_ - tk < .3:
                bob = 6 * math.sin((d_ - tk) / .3 * math.pi)
    phobos_shape(c, px, py + bob, 1.0, -8)
    asleep = key == "patient" and d_ > 1.6
    draw_cat(c, px - 30, py - 95, .3, t, "bliss" if asleep else "open")
    helmet(c, px - 30, py - 95, .3)
    # la patte qui pousse
    if not asleep:
        ph = (d_ * 1.25) % 1
        ext = math.sin(ph * math.pi) * 50
        c.drawOval(skia.Rect.MakeLTRB(px + 40 + ext, py - 130, px + 100 + ext, py - 96), fill("#FFE1B0"))
        c.drawOval(skia.Rect.MakeLTRB(px + 40 + ext, py - 130, px + 100 + ext, py - 96), line(INK, 5))
    else:
        for k in range(3):
            ph = (t * .7 + k / 3) % 1
            text(c, "z", px + 60 + ph * 60, py - 220 - ph * 90, 36 + 22 * ph, "#FFFFFF", INK, 6, a=1 - ph)
    text(c, "PHOBOS", px, py + 200, 54, "#FFFFFF", INK, 8)
    if key == "patient":
        a = clamp((d_ - .3) / .2)
        c.drawLine(px + 260, py - 40, px + 260, py + 140, line("#FFE14D", 10, a))
        c.drawPath(poly([(px + 230, py + 120), (px + 290, py + 120), (px + 260, py + 170)]), fill("#FFE14D", a))
        text(c, "2 m / siècle", px + 260, py - 70, 44, "#FFE14D", INK, 7, a=a)
        a2 = clamp((d_ - 1.6) / .2)
        text(c, "Fin de Phobos : dans 30 à 50", 540, 1560, 58, "#FFFFFF", INK, 9, a=a2)
        text(c, "millions d'années.", 540, 1630, 58, "#FFFFFF", INK, 9, a=a2)
    else:
        if d_ > 1.2:
            text(c, "tap", px + 160, py - 160, 52, "#FFFFFF", INK, 8, a=clamp((d_ - 1.2) / .2))


# ---------------------------------------------------------------- HUD, légende, carton
HUD_COL = "#FF6A3D"


def hud(c, t, b):
    d = day_at(t)
    hook = b["key"] == "hook"
    d_ = t - b["start"]
    pop = 1 + .14 * (1 - eout(d_ / .22)) if b["d1"] != b["d0"] and b["key"] != "voyage" else 1.0
    c.save()
    c.translate(540, 262)
    c.scale(pop, pop)
    pan = rrect(-420, -135, 420, 135, 44)
    c.drawPath(pan, fill("#14121C", .94))
    c.drawPath(pan, line(HUD_COL, 8))
    head = "MICHEL, EMPEREUR DE MARS"
    big = "EMPIRE DE MARS" if hook else "JOUR %d" % round(d)
    low = b["low"]
    text(c, head, 0, -88, fit(head, 38, 770), "#C9C6D8")
    text(c, big, 0, 32, fit(big, 108, 780), HUD_COL)
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


CARD_LINES = ("Très approximatif. Trajet : %d jours (mission de 2020)." % TRAJET,
              "Mars : environ -60 °C en moyenne (CNES ; JPL : -53 °C).",
              "Gravité : 38 % de la Terre. Saut d'un chat : 1,5 m.",
              "Olympus Mons : 21,2 km (22,5 depuis les plaines).",
              "Jour martien : 24 h 39 min 35 s (NASA/JPL).",
              "Radio : 225 millions de km en moyenne (3 à 22 min).",
              "Phobos : ~2 m par siècle, détruite dans 30-50 Ma.",
              "Fenêtre de tir tous les ~26 mois (calcul). Fusée : inventée.",
              "Gérard va bien. Michel aussi.")


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
    text(c, "L'EMPIRE DE LA TERRE.", 0, 128, 80, "#4FA3FF")
    c.restore()
    a = clamp((d_ - .5) / .25)
    for i, l in enumerate(CARD_LINES):
        text(c, l, 540, 1000 + i * 62, fit(l, 42, 980), "#A9A6BC", a=a)


def shake_amp(t):
    amp = 0
    for tk in JUMPS + [K["decol"] + .5, K["fin"] + 1.0]:
        d_ = t - tk
        if 0 <= d_ < .22:
            amp = max(amp, 9 * (1 - d_ / .22))
    return amp


def burst(c, t):
    for tk in JUMPS:
        d_ = t - tk
        if 0 <= d_ < .07:
            c.drawRect(skia.Rect.MakeWH(W, H), fill("#FFFFFF", .5 * (1 - d_ / .07)))


SCN = dict(salon=scene_salon, mars=scene_mars, volcan=scene_volcan, griffe=scene_griffe, decol=scene_decol, voyage=scene_voyage,
           radio=scene_radio, phobos=scene_phobos)


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


_spl = [K["decol"], K["volcan"], K["recu"], K["phobos"], K["bleu"], CARD, END]
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
    print("saut", SAUT_M, "everest x", X_EVEREST, "recul", RECUL, "repas", J_REPAS, "radio", RADIO, "phobos", PHOBOS_M, "mois", MOIS)
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
