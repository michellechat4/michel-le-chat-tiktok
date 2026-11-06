"""Son de la vidéo 06 : marche pizzicato qui monte d'un ton à chaque ère, coupée net à 7 h 03."""
import numpy as np
from scipy.signal import butter, sosfilt, resample_poly
from scipy.io import wavfile
from scipy.ndimage import maximum_filter1d, uniform_filter1d
import importlib.util as _u, os as _o, sys
_sp = _u.spec_from_file_location("milliard", _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "06_milliard.py"))
ch = _u.module_from_spec(_sp); _sp.loader.exec_module(ch)
BEATS, K, CARD, END, JUMPS = ch.BEATS, ch.K, ch.CARD, ch.END, ch.JUMPS

SR = 48000
N = int(END * SR) + SR
rs = np.random.RandomState(46)
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


def thud(t0, f=55, d=.7, g=-2):
    x = tv(d)
    add(t0, np.sin(2 * np.pi * np.cumsum(f + 90 * np.exp(-x * 12)) / SR) * np.exp(-x * 5), g)
    add(t0, lp(noise(d), 1400) * np.exp(-x * 11), g - 3)


def whoosh(t0, d=.4, g=-12, a_=400, b_=4000, pan=0.0):
    x = tv(d)
    add(t0, bp(noise(d), a_, b_) * np.hanning(len(x)), g, pan)


def tick(t0, g=-15):
    x = tv(.03)
    add(t0, bp(noise(.03), 2000, 7000) * np.exp(-x * 160), g)


def voice(t0, base=215, n=3, g=-11):
    for k in range(n):
        x = tv(.1)
        f = base * rs.uniform(.92, 1.15) * (1 + .1 * np.sin(x * 50))
        add(t0 + k * .1, bp(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)), 350, 2500) * np.hanning(len(x)), g)


def mrrp(t0, g=-5, up=370):
    d = .55
    x = tv(d)
    f = 340 + up * np.minimum(x / .34, 1) ** 1.6
    v = sum(np.sin(2 * np.pi * np.cumsum(f * k) / SR) / k for k in (1, 2, 3, 4))
    v = bp(v, 300, 3200) * (.65 + .35 * np.sin(2 * np.pi * 24 * x)) * np.hanning(len(x)) ** .6
    add(t0, norm(v), g)


def ding(t0, f=1320, g=-14, d=.5):
    x = tv(d)
    add(t0, (np.sin(2 * np.pi * f * x) + .3 * np.sin(4 * np.pi * f * x)) * np.exp(-x * 9), g)


# ---- musique : même marche du début à 7 h 03, un demi-ton plus haut à chaque saut, tempo qui presse un peu
mel = [0, None, 3, None, 7, None, 3, None, 8, None, 7, 6, 7, None, None, None]
bas = [0, 7, 0, 7, 5, 7, 0, 7]
STOP = K["retard"] + .25
t0, i = 0.0, 0
while t0 < STOP:
    nj = sum(1 for j in JUMPS if j <= t0)
    root = 98.0 * 2 ** (min(nj, 14) * .5 / 12 * 2)
    if i % 2 == 0:
        mus(t0, basson(root * 2 ** (bas[(i // 2) % 8] / 12), .32), -7)
    m = mel[i % len(mel)]
    if m is not None:
        mus(t0, pizz(root * 4 * 2 ** (m / 12)), -11)
    if i % 4 == 2:
        x = tv(.05)
        mus(t0, hp(noise(.05), 6000) * np.exp(-x * 80), -27)
    i += 1
    t0 += 60 / (118 + nj * 1.6) / 2
MUS[int(STOP * SR):] = 0

# ---- sauts dans le temps : souffle, roulement du compteur, plus grave et plus large avec les années
for n, j in enumerate(JUMPS):
    whoosh(j - .08, .5, -10, 300 + n * 30, 3500 + n * 150)
    for k in range(9):
        tick(j + k * .045, -17)
    ding(j + .42, 1760, -21, .25)

# ---- temps forts
x = tv(.5)
add(.05, np.sin(2 * np.pi * np.cumsum(46 + 60 * np.exp(-x * 10)) / SR) * np.exp(-x * 7), -6)
for b in BEATS:
    if b["ger"]:
        voice(b["start"] + .38, 215, min(2 + len(b["ger"]) // 5, 5))
# pas de Gérard qui arrive
for key in ("repas", "nom", "pyr", "ice", "evo", "sun"):
    for k in range(3):
        x = tv(.07)
        add(K[key] + .05 + k * .16, bp(noise(.07), 250, 1000) * np.exp(-x * 60), -13, .3)
# bip du réveil
for k in range(2):
    ding(K["repas"] + .2 + k * .28, 2100, -20, .12)
mrrp(K["repas"] + 1.2, -9)
# testament : plume
x = tv(.5)
for k, dt in enumerate((.5, 1.3, 2.1)):
    add(K["test"] + dt, bp(noise(.5), 2500, 7000) * np.hanning(len(x)) * (1 + .6 * np.sin(x * 90)), -22)
# tampon GÉRARD
thud(K["nom"] + 1.5, 90, .25, -7)
# Voyager : bip lointain
for k in (0, .3, .6):
    ding(K["oort"] + .9 + k, 880, -24, .15)
mrrp(K["oort"] + 1.5, -10)
# portraits : petits cadres
for k in range(8):
    tick(K["mur"] + .4 + k * .3, -18)
# pyramide : vent de sable
d = 3.0
x = tv(d)
add(K["pyr"], bp(noise(d), 800, 3000) * np.hanning(len(x)), -24)
# Véga : carillon
for k, f in enumerate((1047, 1319, 1568)):
    ding(K["vega"] + .9 + k * .13, f, -17, .9)
# ère glaciaire : vent + raclette
d = 3.2
x = tv(d)
add(K["ice"], lp(noise(d), 1300) * np.hanning(len(x)), -15)
t_ = K["ice"] + .75
while t_ < K["ice"] + 3.0:
    x = tv(.06)
    add(t_, bp(noise(.06), 1800, 6000) * np.exp(-x * 30), -15, .25)
    t_ += .142
# Bételgeuse : souffle très doux, puis ronflement de Michel
thud(K["betel"] + .1, 34, 1.6, -7)
x = tv(2.0)
add(K["betel"] + .1, hp(noise(2.0), 2500) * np.exp(-x * 2.5), -24)
for k in range(2):
    x = tv(.8)
    add(K["betel"] + 1.3 + k * 1.0, lp(noise(.8), 300) * np.hanning(len(x)), -12)
# boîtes ouvertes
for k in range(4):
    add(K["evo"] + .7 + k * .28, bp(noise(.05), 2500, 8000) * np.exp(-tv(.05) * 70), -13, -.4 + k * .27)
# astéroïde
d = 2.6
x = tv(d)
add(K["dino"], np.sin(2 * np.pi * np.cumsum(1500 - 900 * x / d) / SR) * np.hanning(len(x)), -24)
thud(K["dino"] + 2.6, 34, .9, -3)
# galaxie : montée
d = 3.0
x = tv(d)
add(K["gal"], np.sin(2 * np.pi * np.cumsum(180 + 300 * x / d) / SR) * np.hanning(len(x)), -23)
ding(K["gal"] + 3.0, 1568, -15, .5)
# longue marche
t_ = K["pang"] + .2
while t_ < K["pang"] + 3.0:
    x = tv(.06)
    add(t_, bp(noise(.06), 300, 1200) * np.exp(-x * 60), -16, .15)
    t_ += .24
ding(K["pang"] + 3.0, 2093, -17, .3)
# croquettes qui tombent
d = 1.5
for k in range(170):
    x = tv(.03)
    add(K["pile"] + rs.uniform(0, d), bp(noise(.03), 1500, 7000) * np.exp(-x * 170), rs.uniform(-29, -19), rs.uniform(-.5, .5))
mrrp(K["pile"] + 2.0, -10)
# horloge de 28 h, miaou à 24
b = next(q for q in BEATS if q["key"] == "jour")
t_ = K["jour"]
while t_ < K["jour"] + b["dur"]:
    tick(t_, -15)
    t_ += .25
mrrp(K["jour"] + (24 - 14) / (26.5 - 14) * (b["dur"] - .3), -4)
# Soleil : grésillement
d = K["retard"] - K["sun"]
x = tv(d)
add(K["sun"], hp(noise(d), 3500) * np.minimum(x / .8, 1) * np.minimum((d - x) / .2, 1), -29)
add(K["sun"], lp(noise(d), 240) * np.minimum(x / .5, 1) * np.minimum((d - x) / .2, 1), -18)
# réveil final, 7 h 02
ding(K["r730"] + .4, 2100, -18, .15)

# 7 h 03 : disque rayé, silence, alarme
ts = STOP
d = .3
x = tv(d)
add(ts - .2, bp(np.sign(np.sin(2 * np.pi * np.cumsum(1600 - 5000 * x + 700 * np.sin(x * 90)) / SR)) + .4 * noise(d), 300, 5000) * np.hanning(len(x)), -9)
thud(ts, 40, 1.2, -1)
for k in range(5):
    x = tv(.12)
    add(ts + .3 + k * .28, np.sign(np.sin(2 * np.pi * 1000 * x)) * np.hanning(len(x)), -24)
# regard : drone grave qui monte
d = K["fin"] - K["stare"]
x = tv(d)
add(K["stare"], (np.sin(2 * np.pi * 55 * x) + .5 * np.sin(2 * np.pi * 58.3 * x)) * np.minimum(x / 1.6, 1) * np.minimum((d - x) / .05, 1), -9)
add(K["stare"], bp(noise(d), 700, 2200) * x / d, -30)
x = tv(.4)
add(K["stare"] + .25, np.sin(2 * np.pi * np.cumsum(260 + 70 * x) / SR) * np.exp(-x * 7), -20)  # gorgée d'angoisse
# tablette
thud(K["fin"] + .35, 70, .45, -6)
for k in range(5):
    x = tv(.05)
    add(K["fin"] + .9 + k * .06, bp(noise(.05), 2200, 8000) * np.exp(-x * 80), -12)  # griffe
mrrp(K["fin"] + 2.2, -4, 180)
for k, (f, dt) in enumerate(((220, 2.8), (207.65, 3.05), (196, 3.3))):
    mus(K["fin"] + dt, pizz(f, .4), -7)
i = int(CARD * SR)
FX[i:] = 0
MUS[i:] = 0
x = tv(.6)
add(CARD + .05, np.sin(2 * np.pi * np.cumsum(40 + 70 * np.exp(-x * 9)) / SR) * np.exp(-x * 6), -3)
add(CARD + 1.6, np.sin(2 * np.pi * 110 * tv(.2)) * np.exp(-tv(.2) * 16), -14)

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
wavfile.write("son6.wav", SR, (np.clip(st, -1, 1) * 32767).astype(np.int16))
print("pic", pk, "crête vraie dB", 20 * np.log10(tp), "durée", END)
