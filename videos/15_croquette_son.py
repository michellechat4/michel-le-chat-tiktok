"""Son de la vidéo 15 : thème sautillant, sifflement de chute qui s'allonge, « cronch » à chaque arrivée, bang supersonique,
nappe spatiale, grondement de l'entrée, carillon d'étoile filante, sac qui tombe et pluie de croquettes."""
import numpy as np
from scipy.signal import butter, sosfilt, resample_poly
from scipy.io import wavfile
from scipy.ndimage import maximum_filter1d, uniform_filter1d
import importlib.util as _u, os as _o, sys
_sp = _u.spec_from_file_location("croq", _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "15_croquette.py"))
ch = _u.module_from_spec(_sp); _sp.loader.exec_module(ch)
BEATS, K, CARD, END, JUMPS, DROP = ch.BEATS, ch.K, ch.CARD, ch.END, ch.JUMPS, ch.DROP

SR = 48000
N = int(END * SR) + SR
rs = np.random.RandomState(15)
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


def mallet(f, d=.3):
    t = tv(d)
    return (np.sin(2 * np.pi * f * t) + .25 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 30)) * np.exp(-t * 11) * np.minimum(t / .002, 1)


def tuba(f, d=.22):
    t = tv(d)
    return lp(2 * ((f * t) % 1) - 1, 420) * np.minimum(t / .01, 1) * np.exp(-t * 7)


def ding(t0, f=1320, g=-14, d=.5):
    x = tv(d)
    add(t0, (np.sin(2 * np.pi * f * x) + .3 * np.sin(4 * np.pi * f * x)) * np.exp(-x * 9), g)


def whoosh(t0, d=.4, g=-12, a_=400, b_=4000, pan=0.0):
    x = tv(d)
    add(t0, bp(noise(d), a_, b_) * np.hanning(len(x)), g, pan)


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


def piou(t0, g=-12, f0=2400, f1=350, d=.28):
    x = tv(d)
    f = f1 + (f0 - f1) * np.exp(-x * 14)
    add(t0, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 9) * np.minimum(x / .003, 1), g)


def crunch(t0, g=-8):
    for k in range(3):
        add(t0 + k * .06, bp(noise(.05), 1200, 7000) * np.exp(-tv(.05) * 60), g - k * 2)


def thud(t0, f=55, d=.7, g=-2):
    x = tv(d)
    add(t0, np.sin(2 * np.pi * np.cumsum(f + 90 * np.exp(-x * 12)) / SR) * np.exp(-x * 5), g)
    add(t0, lp(noise(d), 1400) * np.exp(-x * 11), g - 3)


# ---- musique : thème sautillant (Terre), nappe (espace, nuit)
mel = [0, 4, 7, 4, 9, 7, 4, None, 2, 5, 9, 5, 7, None, None, None]
bas = [0, 5, 7, 5]


def theme(a, z, root, gm=0):
    t0, i = a, 0
    while t0 < z - .05:
        if i % 2 == 0:
            mus(t0, tuba(root * 2 ** (bas[(i // 2) % 4] / 12), .3), -7 + gm)
        m = mel[i % len(mel)]
        if m is not None:
            mus(t0, mallet(root * 4 * 2 ** (m / 12)), -12 + gm)
        if i % 4 == 2:
            mus(t0, hp(noise(.04), 6000) * np.exp(-tv(.04) * 90), -27 + gm)
        i += 1
        t0 += 60 / 124 / 2


def pad(t0, t1, chord, g):
    d = t1 - t0
    x = tv(d)
    v = sum(np.sin(2 * np.pi * f * x + .3 * np.sin(2 * np.pi * .2 * x)) for f in chord)
    mus(t0, lp(v, 1800) * np.minimum(x / .6, 1) * np.minimum((d - x) / .3, 1) * .3, g)


def arp(a, z, g=-19):
    tt, k = a + .2, 0
    notes = (880, 1108.7, 1318.5, 1760, 1318.5, 1108.7)
    while tt < z - .3:
        mus(tt, mallet(notes[k % len(notes)], .6), g)
        tt += .3
        k += 1


theme(K["regle"], K["j17"], 146.8)
theme(K["frein"], K["j18"], 146.8 * 2 ** (2 / 12), -2)
theme(K["blase"], K["j29"], 146.8 * 2 ** (2 / 12), -2)
theme(K["voeu"], CARD, 146.8 * 2 ** (4 / 12), -1)
for a, z in ((0, K["regle"]), (K["j18"], K["blase"]), (K["j29"], K["entree"]), (K["etoile"], K["voeu"])):
    pad(a, z, (110, 164.8, 220, 277.2), -9)
    arp(a, z)
# mach : grosse tenue grave
pad(K["j17"], K["frein"], (55, 82.4, 110), -8)
pad(K["entree"], K["etoile"], (61.7, 92.5, 123.5), -8)
arp(0, K["regle"])

# ---- chaque nouveau jour : petit « pop »
for tk in JUMPS:
    ding(tk + .02, 1760, -18, .2)
    whoosh(tk, .25, -20, 800, 6000)

# ---- chutes : sifflement descendant, cronch à l'arrivée, petit miaou content
for key, (a, z) in DROP.items():
    t0 = K[key] + max(a, 0)
    d = K[key] + z - t0
    if d > .15:
        x = tv(d)
        f = 1800 - 900 * x / d
        add(t0, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(x / .1, 1) * np.minimum((d - x) / .05, 1) * .5, -22)
        add(t0, bp(noise(d), 1500, 6000) * np.minimum(x / .3, 1) * np.minimum((d - x) / .05, 1), -28)
    crunch(K[key] + z, -6)
    crunch(K[key] + z + .17, -9)
    ding(K[key] + z + .3, 2093, -20, .25)
    if key in ("j1", "j6", "frein"):
        mrrp(K[key] + z + .55, -11, 300)
mrrp(K["blase"] + 1.9, -12, 120)

# ---- bulles de Gérard
for b in BEATS:
    if b["ger"]:
        voice(b["start"] + .4 if b["key"] != "fin" else b["start"] + .5, 215, min(2 + len(b["ger"]) // 5, 4), -11)
voice(K["j29"] + 1.2, 215, 3, -14)

# ---- pigeons (Paris)
for k in range(4):
    whoosh(K["j10"] + .4 + k * .1, .08, -24, 500, 3000)

# ---- panneau vitesse limite, chronos
whoosh(K["limite"] + .45, .2, -22, 800, 6000)
for k in range(5):
    add(K["attente"] + .2 + k * .4, hp(noise(.02), 3000) * np.exp(-tv(.02) * 200), -20)

# ---- mur du son : souffle qui monte, BANG
d = .75
x = tv(d)
add(K["j17"], bp(noise(d), 300, 4000) * (x / d) ** 2, -10)
thud(K["j17"] + .75, 40, 1.2, -1)
add(K["j17"] + .75, lp(noise(.4), 3000) * np.exp(-tv(.4) * 10), -4)
whoosh(K["j17"] + .9, 2.4, -16, 200, 2500)

# ---- espace : lâcher feutré
ding(K["j18"] + .9, 660, -18, .5)

# ---- trajet : tic-tac
for k in range(7):
    add(K["trajet"] + .2 + k * .42, bp(noise(.03), 2000, 5000) * np.exp(-tv(.03) * 150), -21 if k % 2 else -18)

# ---- entrée atmosphérique : grondement qui enfle, crépitements
a, z = K["entree"] + .1, K["etoile"]
d = z - a
x = tv(d)
env = np.clip((x - .5) / 1.2, 0, 1) * np.minimum((d - x) / .3, 1)
add(a, (lp(noise(d), 400, 4) * 3 + bp(noise(d), 800, 5000) * .4) * env, -9)
add(a, (hp(noise(d), 3000) * (rs.rand(len(x)) < .003) * 6 * env).astype(np.float32), -18)

# ---- étoile filante : carillon montant, vœu
for k, f in enumerate((1318.5, 1568, 1760, 2093, 2637)):
    ding(K["etoile"] + .3 + k * .1, f, -16, .7)
for k in range(3):
    ding(K["etoile"] + 1.9 + k * .15, 2637 + k * 300, -20, .5)

# ---- vœu : étincelle, sac qui tombe, pluie de croquettes
ding(K["voeu"] + .1, 3136, -16, .6)
whoosh(K["voeu"] + .5, .45, -14, 400, 3000)
thud(K["voeu"] + .95, 60, .6, -3)
for k in range(60):
    tt = K["voeu"] + .95 + rs.uniform(0, .9) ** 1.5
    add(tt, bp(noise(.02), 2000, 8000) * np.exp(-tv(.02) * 200), rs.uniform(-24, -16), rs.uniform(-.5, .5))
crunch(K["voeu"] + 1.2, -6)
crunch(K["voeu"] + 1.4, -8)
crunch(K["voeu"] + 1.6, -10)
# Gérard arrive
for k in range(3):
    thud(K["fin"] + k * .16, 90, .15, -16)
mrrp(K["fin"] + 1.6, -10, 300)

i = int(CARD * SR)
FX[i:] = 0
MUS[i:] = 0
thud(CARD + .05, 40, .7, -3)
crunch(CARD + 1.6, -9)

L = MUS * db2(-1) + FX[:, 0]
Rr = MUS * db2(-1) + FX[:, 1]
L, Rr = np.tanh(L * 1.6), np.tanh(Rr * 1.6)
pk = max(np.abs(L).max(), np.abs(Rr).max())
st = np.stack([L, Rr], 1)[: int(END * SR)] / pk * .89
MASTER_DB = float(sys.argv[1]) if len(sys.argv) > 1 else -1.0
LIM_DB = -4.5
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
wavfile.write("son15.wav", SR, (np.clip(st, -1, 1) * 32767).astype(np.int16))
print("pic", pk, "crête vraie dB", 20 * np.log10(tp), "durée", END)
