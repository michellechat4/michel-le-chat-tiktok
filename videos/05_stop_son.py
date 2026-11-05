"""Son de la vidéo 05 : pizzicato sournois, STOP, musique de salon très calme pendant la catastrophe."""
import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
from scipy.ndimage import maximum_filter1d, uniform_filter1d
from scipy.signal import resample_poly
import importlib.util as _u, os as _o, sys
_sp = _u.spec_from_file_location("stop", _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "05_stop.py"))
ch = _u.module_from_spec(_sp); _sp.loader.exec_module(ch)
BEATS, K, CARD, END = ch.BEATS, ch.K, ch.CARD, ch.END

SR = 48000
N = int(END * SR) + SR
rs = np.random.RandomState(45)
tt = np.arange(N) / SR
MUS = np.zeros(N, np.float32)
FX = np.zeros((N, 2), np.float32)
db2 = lambda x: 10 ** (x / 20)
bp = lambda x, a, b, o=2: sosfilt(butter(o, [a, b], "band", fs=SR, output="sos"), x)
lp = lambda x, f, o=2: sosfilt(butter(o, f, "low", fs=SR, output="sos"), x)
hp = lambda x, f, o=2: sosfilt(butter(o, f, "high", fs=SR, output="sos"), x)
tv = lambda d: np.arange(int(d * SR)) / SR
noise = lambda d: rs.randn(int(d * SR)).astype(np.float32)
norm = lambda x: x / (np.max(np.abs(x)) + 1e-9)


def add(t0, x, g=0.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N or i < 0:
        return
    x = x[: N - i] * db2(g)
    FX[i:i + len(x), 0] += x * (1 - max(pan, 0))
    FX[i:i + len(x), 1] += x * (1 + min(pan, 0))


def mus(t0, x, g=0.0):
    i = int(t0 * SR)
    if i >= N or i < 0:
        return
    x = x[: N - i] * db2(g)
    MUS[i:i + len(x)] += x


def pizz(f, d=.26):
    t = tv(d)
    return (np.sin(2 * np.pi * f * t) + .5 * np.sin(4 * np.pi * f * t) * np.exp(-t * 20)) * np.exp(-t * 17) * np.minimum(t / .002, 1)


def basson(f, d=.2):
    t = tv(d)
    return lp(2 * ((f * t) % 1) - 1, 560) * np.minimum(t / .008, 1) * np.exp(-t * 8)


def vibra(f, d=1.3):
    t = tv(d)
    return (np.sin(2 * np.pi * f * t) + .25 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 7)) * np.exp(-t * 2.6) * (1 + .18 * np.sin(2 * np.pi * 5.2 * t)) * np.minimum(t / .004, 1)


def contrebasse(f, d=.5):
    t = tv(d)
    return (np.sin(2 * np.pi * f * t) + .3 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 5) * np.minimum(t / .006, 1)


# ---- musique 1 : avant l'arrêt et à la fin : marche pizzicato
ST = 60 / 126 / 2
mel = [0, None, 3, None, 7, None, 3, None, 8, None, 7, 6, 7, None, None, None]
bas = [0, 7, 0, 7, 5, 7, 0, 7]
root = 110.0
for a, z in ((0, K["stop"]), (K["vide"], K["patte"] + 1.5)):
    t0, i = a, 0
    while t0 < z - .05:
        if i % 2 == 0:
            mus(t0, basson(root * 2 ** (bas[(i // 2) % 8] / 12), ST * 1.7), -7)
        m = mel[i % len(mel)]
        if m is not None:
            mus(t0, pizz(root * 4 * 2 ** (m / 12)), -11)
        i += 1
        t0 += ST

# ---- musique 2 : pendant la seconde, ambiance d'ascenseur en majeur, imperturbable
BPM = 84
Q = 60 / BPM
CH = [(261.63, 329.63, 392.0, 493.88), (293.66, 349.23, 440.0, 523.25), (246.94, 293.66, 349.23, 440.0), (261.63, 329.63, 392.0, 440.0)]
BS = [65.41, 73.42, 98.0, 65.41]
MEL = [(0, 659.25), (1.5, 587.33), (2, 523.25), (4, 587.33), (5.5, 659.25), (6, 698.46), (8, 587.33), (9, 493.88), (10, 440.0), (12, 523.25), (14, 392.0)]
a, z = K["stop"] + 1.1, K["repart"]
t0, n = a, 0
while t0 < z:
    c_ = CH[n % 4]
    for j, f in enumerate(c_):
        mus(t0 + j * .018, vibra(f, 1.8), -19)
    for j, f in enumerate(c_):
        mus(t0 + 2 * Q + j * .018, vibra(f, 1.2), -22)
    mus(t0, contrebasse(BS[n % 4], Q * 1.6), -10)
    mus(t0 + 2 * Q, contrebasse(BS[n % 4] * 1.5, Q * 1.2), -12)
    # charley balais
    for b_ in range(4):
        x = tv(.08)
        mus(t0 + b_ * Q, hp(noise(.08), 5000) * np.exp(-x * 50), -30)
        mus(t0 + (b_ + .66) * Q, hp(noise(.05), 6000) * np.exp(-tv(.05) * 80), -33)
    t0 += 4 * Q
    n += 1
t0 = a
while t0 < z:
    for bt, f in MEL:
        mus(t0 + bt * Q, vibra(f, 1.1), -15)
    t0 += 16 * Q
i0, i1 = int(z * SR), int((z + .12) * SR)
MUS[i1:int(K["vide"] * SR)] = 0
MUS[i0:i1] *= np.linspace(1, 0, i1 - i0).astype(np.float32)
MUS[int((K["patte"] + 1.6) * SR):] = 0


# ---- bruitages
def tick(t0, g=-15):
    x = tv(.03)
    add(t0, bp(noise(.03), 2000, 7000) * np.exp(-x * 160), g)


def thud(t0, f=55, d=.7, g=-2):
    x = tv(d)
    add(t0, np.sin(2 * np.pi * np.cumsum(f + 90 * np.exp(-x * 12)) / SR) * np.exp(-x * 5), g)
    add(t0, lp(noise(d), 1400) * np.exp(-x * 11), g - 3)


def metal(t0, g=-5, d=1.1):
    x = tv(d)
    v = sum(np.sin(2 * np.pi * f * x) * np.exp(-x * a_) for f, a_ in ((310, 5), (523, 6), (877, 7), (1490, 9), (2230, 12)))
    add(t0, v / 2.5 + bp(noise(d), 500, 5000) * np.exp(-x * 7), g, .1)


def whoosh(t0, d=.5, g=-14, a_=500, b_=2800, pan=0.0):
    x = tv(d)
    add(t0, bp(noise(d), a_, b_) * np.hanning(len(x)), g, pan)


def voice(t0, base=215, n=3, g=-11):
    for k in range(n):
        x = tv(.1)
        f = base * rs.uniform(.92, 1.15) * (1 + .1 * np.sin(x * 50))
        add(t0 + k * .1, bp(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)), 350, 2500) * np.hanning(len(x)), g)


def mrrp(t0, g=-5):
    d = .55
    x = tv(d)
    f = 340 + 370 * np.minimum(x / .34, 1) ** 1.6
    v = sum(np.sin(2 * np.pi * np.cumsum(f * k) / SR) / k for k in (1, 2, 3, 4))
    v = bp(v, 300, 3200) * (.65 + .35 * np.sin(2 * np.pi * 24 * x)) * np.hanning(len(x)) ** .6
    add(t0, norm(v), g)


# accroche : petit roulement
x = tv(.5)
add(.05, np.sin(2 * np.pi * np.cumsum(46 + 60 * np.exp(-x * 10)) / SR) * np.exp(-x * 7), -7)
# globe : souffle
d = BEATS[1]["dur"]
x = tv(d)
add(K["vit"], lp(noise(d), 500) * np.hanning(len(x)), -18)
# étiquettes 1 100 km/h : petits pops
for i in range(3):
    x = tv(.08)
    add(K["tout"] + .25 + i * .5, np.sin(2 * np.pi * (800 + i * 200) * x) * np.exp(-x * 40), -14)
# Michel saute
d_j = .45
x = tv(d_j)
add(K["rideaux"] + .3, np.sin(2 * np.pi * np.cumsum(420 + 900 * x / d_j) / SR) * np.hanning(len(x)), -16)
add(K["rideaux"] + .75, bp(noise(.12), 900, 5000) * np.exp(-tv(.12) * 30), -10)  # griffes
add(K["rideaux"] + .82, bp(noise(.09), 2000, 7000) * np.exp(-tv(.09) * 40), -12)
# gorgée
add(K["cafe"] + .35, bp(noise(.28), 300, 1100) * np.hanning(int(.28 * SR)), -16)

# STOP : scratch + énorme coup, puis le ralenti
ts = K["stop"]
d = .28
x = tv(d)
add(ts - .22, bp(np.sign(np.sin(2 * np.pi * np.cumsum(1600 - 5000 * x + 700 * np.sin(x * 90)) / SR)) + .4 * noise(d), 300, 5000) * np.hanning(len(x)), -9)
thud(ts, 36, 1.8, 1)
metal(ts, -9, 1.2)
d = 2.0
x = tv(d)
add(ts + .02, np.sin(2 * np.pi * np.cumsum(180 * np.exp(-x * 1.4) + 26) / SR) * np.exp(-x * 1.2), -9)

# drapeau : tissu qui claque en boucle
t_ = K["stop"] + .25
while t_ < K["reste"] + .4:
    add(t_, bp(noise(.06), 700, 4000) * np.exp(-tv(.06) * 50), -17)
    t_ += .19
t_ = K["flag"]
while t_ < K["mur"]:
    add(t_, bp(noise(.07), 800, 4500) * np.exp(-tv(.07) * 40), -12, -.3)
    t_ += .13
mrrp(K["flag"] + .5, -12)

# mur : briques au ralenti
tb = ch.T_BREACH_V
thud(tb, 44, 1.2, -1)
x = tv(1.1)
add(tb, lp(noise(1.1), 1800) * np.exp(-x * 3), -6, .2)
for k in range(14):
    x2 = tv(.09)
    add(tb + rs.uniform(.1, 1.2), bp(noise(.09), 300, 1800) * np.exp(-x2 * 50), -13, rs.uniform(-.4, .6))

# le vent : continu, assourdi tant qu'on est dans le salon, plus fort dehors, coupé hors de Paris
ev = np.zeros(N, np.float32)
vent = lp(rs.randn(N).astype(np.float32), 1300)
for b in BEATS:
    if b["T1"] is None or b["key"] == "repart" or b["ph"] == "marche" or b["ph"] == "fin" or b["key"] == "intact":
        continue
    if b["ph"] != "vol":
        continue
    lvl = .32 if b["key"] in ("stop", "reste", "flag") else 1.0
    if b["key"] == "vent":
        lvl = 1.5
    i, j = int(b["start"] * SR), int((b["start"] + b["dur"]) * SR)
    ev[i:j] = lvl
ev = uniform_filter1d(ev, int(.06 * SR))
wnd = vent * ev * (1 + .25 * np.sin(2 * np.pi * .45 * tt)) * db2(-18)
FX[:, 0] += wnd
FX[:, 1] += wnd
# lampadaires et arbres qui passent
for x0 in sorted(ch.TREES + ch.LAMPS):
    # temps vidéo où l'objet passe au centre de l'écran : x_off = x0 - 540
    for b in BEATS:
        if b["T1"] is None or b["ph"] != "vol" or b["T1"] == b["T0"]:
            continue
        a0, a1 = b["T0"] * ch.V * ch.PPM, b["T1"] * ch.V * ch.PPM
        if a0 <= x0 - 540 < a1:
            whoosh(b["start"] + b["dur"] * (x0 - 540 - a0) / (a1 - a0) - .1, .32, -17, 400, 2200, rs.uniform(-.2, .2))
# bus : klaxon poli
x = tv(.3)
for k in (0, .36):
    add(K["bus"] + 1.1 + k, bp(np.sign(np.sin(2 * np.pi * 349 * x)) + np.sign(np.sin(2 * np.pi * 440 * x)), 200, 2500) * np.minimum(x / .01, 1) * np.minimum((.3 - x) / .02, 1), -17, .4)
# ours : grognement, tout petit
d = .7
x = tv(d)
add(K["pole"] + 1.2, lp(np.sign(np.sin(2 * np.pi * np.cumsum(62 + 14 * np.sin(x * 8)) / SR)), 500) * np.hanning(len(x)), -14)
t_ = K["pole"]
x = tv(2.6)
add(t_, hp(noise(2.6), 3000) * np.hanning(len(x)) * .5, -24)
# équateur : cocos
d = 2.8
x = tv(d)
add(K["equa"], bp(noise(d), 1500, 7000) * (1 - x / d), -20)
for i in range(8):
    x2 = tv(.14)
    add(K["equa"] + .08 * i + .05, np.sin(2 * np.pi * (240 + i * 18) * x2) * np.exp(-x2 * 28), -9, -.4 + i * .1)
# ISS : petit bip
x = tv(.12)
for k in (0, .24):
    add(K["iss"] + .9 + k, np.sin(2 * np.pi * 1320 * x) * np.exp(-x * 20), -18)
# Seine
d = 2.6
x = tv(d)
add(K["seine"], lp(noise(d), 1800) * np.minimum(x / .2, 1) * np.minimum((d - x) / .3, 1), -9, .15)
thud(K["seine"] + 1.0, 60, .5, -9)
# Soleil : montée du compteur
d = 1.8
x = tv(d)
add(K["soleil"], (np.sin(2 * np.pi * np.cumsum(220 + 340 * x / d) / SR)) * np.hanning(len(x)), -20)
x = tv(.3)
add(K["soleil"] + 1.8, np.sin(2 * np.pi * 880 * x) * np.exp(-x * 14), -14)
# chute de Gérard : sifflet descendant, très doux
d = 2.4
x = tv(d)
add(K["tombe"], np.sin(2 * np.pi * np.cumsum(1300 - 650 * x / d) / SR) * np.hanning(len(x)), -24)
# T + 1 : tic, tac, retour de la Terre
for k in range(3):
    tick(K["fin1"] + .2 + k * .45, -11)

tr = K["repart"]
thud(tr, 32, 2.0, 2)
metal(tr, -6, 1.6)
x = tv(.5)
add(tr, hp(noise(.5), 1200) * np.exp(-x * 10), -7)
for k in range(10):
    x2 = tv(.07)
    add(tr + rs.uniform(.05, .5), bp(noise(.07), 500, 3200) * np.exp(-x2 * 60), -12, rs.uniform(-.5, .5))
# gorgée de fin, tasse posée
add(K["intact"] + .6, bp(noise(.28), 300, 1100) * np.hanning(int(.28 * SR)), -15)
x = tv(.09)
add(K["intact"] + 1.5, np.sin(2 * np.pi * 1900 * x) * np.exp(-x * 60), -16)
# marche : pas pressés + tic-tac rapide
t_ = K["marche"] + .05
while t_ < K["vide"]:
    x = tv(.07)
    add(t_, bp(noise(.07), 250, 1000) * np.exp(-x * 60), -12, .2)
    tick(t_ + .1, -18)
    t_ += .224

for b in BEATS:
    if b["ger"]:
        voice(b["start"] + .03, 215, min(2 + len(b["ger"]) // 5, 5))

# fin : rideau, bouton
add(K["bouton"] + .1, bp(noise(.4), 700, 4500) * np.hanning(int(.4 * SR)), -14)
x = tv(.18)
add(K["bouton"] + .55, np.sin(2 * np.pi * 1320 * x) * np.exp(-x * 14), -15)
mrrp(K["patte"] + 1.02, -5)
# le clic, puis noir
xc = K["patte"] + 1.75
x = tv(.03)
add(xc, bp(noise(.03), 2000, 8000) * np.exp(-x * 120), -5)
i = int(CARD * SR)
FX[i:] = 0
MUS[i:] = 0
x = tv(.6)
add(CARD + .05, np.sin(2 * np.pi * np.cumsum(40 + 70 * np.exp(-x * 9)) / SR) * np.exp(-x * 6), -3)
add(CARD + 1.5, np.sin(2 * np.pi * 110 * tv(.2)) * np.exp(-tv(.2) * 16), -14)

# après l'atterrissage : rue tranquille, oiseaux, l'accord de salon revient
d = K["vide"] - K["repart"]
x = tv(d)
add(K["repart"], lp(noise(d), 700) * np.minimum(x / .4, 1) * np.minimum((d - x) / .2, 1), -19)
for t_ in (K["repart"] + 1.3, K["intact"] + .4, K["intact"] + 1.4, K["marche"] + .4, K["marche"] + 1.4):
    x = tv(.16)
    add(t_, np.sin(2 * np.pi * np.cumsum(3100 + 900 * np.sin(x * 60)) / SR) * np.hanning(len(x)), -21, .3)
for j, f in enumerate(CH[0]):
    mus(K["intact"] + .2 + j * .02, vibra(f, 2.0), -14)
    mus(K["marche"] + j * .02, vibra(f * 1.122, 1.8), -15)

L = MUS * db2(-1) + FX[:, 0]
Rr = MUS * db2(-1) + FX[:, 1]
L, Rr = np.tanh(L * 1.6), np.tanh(Rr * 1.6)
pk = max(np.abs(L).max(), np.abs(Rr).max())
st = np.stack([L, Rr], 1)[: int(END * SR)] / pk * .89
MASTER_DB = float(sys.argv[1]) if len(sys.argv) > 1 else 1.3
LIM_DB = -3.2
st = sosfilt(butter(4, 14000, "low", fs=SR, output="sos"), st, axis=0) * db2(MASTER_DB)
lim = db2(LIM_DB)
for _ in range(3):
    up = np.abs(resample_poly(st, 4, 1, axis=0)).max(1)
    env = up[:len(st) * 4].reshape(-1, 4).max(1)
    gr = np.minimum(1, lim / np.maximum(env, 1e-6))
    w = int(.004 * SR)
    gr = 1 - maximum_filter1d(1 - gr, 2 * w + 1)
    gr = uniform_filter1d(gr, 2 * w + 1)
    st = st * gr[:, None]
tp = np.abs(resample_poly(st, 4, 1, axis=0)).max()
wavfile.write("son5.wav", SR, (np.clip(st, -1, 1) * 32767).astype(np.int16))
print("pic", pk, "crête vraie dB", 20 * np.log10(tp), "durée", END)
