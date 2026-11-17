"""Son de la vidéo 16 : thème sautillant de nuit, « fouit » à chaque passage de Michel, ronflements de Gérard, train,
bang supersonique, lumières de l'immeuble, nappe spatiale, décollage, alunissage, oiseaux du matin, vitre cassée."""
import numpy as np
from scipy.signal import butter, sosfilt, resample_poly
from scipy.io import wavfile
from scipy.ndimage import maximum_filter1d, uniform_filter1d
import importlib.util as _u, os as _o, sys
_sp = _u.spec_from_file_location("vit", _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "16_vitesse.py"))
ch = _u.module_from_spec(_sp); _sp.loader.exec_module(ch)
BEATS, K, CARD, END, JUMPS = ch.BEATS, ch.K, ch.CARD, ch.END, ch.JUMPS

SR = 48000
N = int(END * SR) + SR
rs = np.random.RandomState(16)
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


# ---- musique : thème sautillant (salon, Terre), nappe (espace)
mel = [0, 4, 7, 4, 9, 7, 4, None, 2, 5, 9, 5, 7, None, None, None]
bas = [0, 5, 7, 5]


def theme(a, z, root, gm=0, bpm=124):
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
        t0 += 60 / bpm / 2


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


R0 = 146.8
theme(K["regle"], K["n6"], R0, -1, 124)
theme(K["immeuble"], K["n10"], R0 * 2 ** (2 / 12), -1, 132)
theme(K["calme"], K["n12"], R0 * 2 ** (4 / 12), -3, 110)
theme(K["fin"], CARD, R0 * 2 ** (5 / 12), -1, 140)
for a, z in ((0, K["regle"]), (K["n10"], K["calme"]), (K["n12"], K["fin"])):
    pad(a, z, (110, 164.8, 220, 277.2), -9)
    arp(a, z)
pad(K["n6"], K["immeuble"], (55, 82.4, 110), -8)

# ---- chaque nouvelle nuit : petit « pop »
for tk in JUMPS:
    ding(tk + .02, 1760, -18, .2)
    whoosh(tk, .25, -20, 800, 6000)


def zoom(t0, g=-12, d=.3, pan=0.0):
    """passage de Michel : souffle bref + petit sifflement descendant"""
    whoosh(t0, d, g, 600, 7000, pan)
    piou(t0 + d * .3, g - 8, 2600, 900, d)


def flutter(a, z, rate=11, g=-15):
    d = z - a
    x = tv(d)
    env = (.5 + .5 * np.sin(2 * np.pi * rate * x)) ** 3 * np.minimum(x / .1, 1) * np.minimum((d - x) / .1, 1)
    add(a, bp(noise(d), 700, 6000) * env, g)


def snore(a, z, g=-14):
    d = z - a
    x = tv(d)
    env = np.clip(np.sin(2 * np.pi * x / 1.6), 0, 1) ** 2 * np.minimum((d - x) / .2, 1)
    add(a, (lp(noise(d), 300, 4) * 4 + bp(noise(d), 80, 400) * 2) * env * (1 + .5 * np.sin(2 * np.pi * 32 * x)), g)


def clicks(a, n, span, g=-16):
    for k in range(n):
        add(a + span * k / n + rs.uniform(0, .03), hp(noise(.015), 2500) * np.exp(-tv(.015) * 300), g)


def chirp(t0, g=-20):
    for k in range(3):
        piou(t0 + k * .09, g, 4200, 3000, .07)


# hook : départ, « Bye. »
whoosh(0.1, 1.2, -12, 300, 5000)
mrrp(1.0, -10, 250)

# règle : Gérard parle, Michel « ! »
voice(K["regle"] + .4, 215, 4, -11)
ding(K["regle"] + 1.8, 2093, -14, .3)

# nuit 1 : passages toutes les 0,9 s
tt = K["n1"] + .3
while tt < K["n2"] - .2:
    zoom(tt + .3, -11, .35, .4 if int((tt - K["n1"]) / .9) % 2 == 0 else -.4)
    tt += .9
tt = K["n2"]
while tt < K["n3"] - .2:
    zoom(tt + .2, -12, .25)
    tt += .55
whoosh(K["n2"] + .5, .2, -22, 800, 6000)
flutter(K["n3"], K["bouchons"], 11, -14)
flutter(K["bouchons"], K["n4"], 11, -24)
voice(K["bouchons"] + .4, 215, 2, -11)
snore(K["bouchons"] + 1.6, K["n4"], -16)

# train : roulement, Michel double
d = K["n6"] - K["n4"]
x = tv(d)
add(K["n4"], lp(noise(d), 250, 4) * 3 * np.minimum(x / .3, 1) * np.minimum((d - x) / .2, 1) * (1 + .3 * np.sin(2 * np.pi * 6 * x)), -12)
for k in range(8):
    add(K["n4"] + .1 + k * .38, bp(noise(.04), 300, 2000) * np.exp(-tv(.04) * 60), -20)
zoom(K["n4"] + 1.0, -9, .6)
piou(K["n4"] + 2.0, -14, 1600, 2400, .18)

# mur du son
d = .65
x = tv(d)
add(K["n6"], bp(noise(d), 300, 4000) * (x / d) ** 2, -10)
thud(K["n6"] + .65, 40, 1.2, -1)
add(K["n6"] + .65, lp(noise(.4), 3000) * np.exp(-tv(.4) * 10), -4)
whoosh(K["n6"] + .8, 2.2, -16, 200, 2500)

# immeuble : lumières, voisins, ronflement
clicks(K["immeuble"] + .25, 17, 1.3, -15)
for k, tt in enumerate((.9, 1.25, 1.6)):
    voice(K["immeuble"] + tt, (300, 260, 340)[k], 2, -13)
snore(K["immeuble"] + 1.6, K["n7"], -15)

# Paris–Marseille : tic-tac et passage
whoosh(K["n7"] + .4, 2.2, -16, 500, 5000)
for k in range(7):
    add(K["n7"] + .3 + k * .42, bp(noise(.03), 2000, 5000) * np.exp(-tv(.03) * 150), -21 if k % 2 else -18)
zoom(K["sardine"], -10, .35)
thud(K["sardine"] + .35, 90, .2, -14)
mrrp(K["sardine"] + .8, -10, 300)
snore(K["sardine"] + 1.2, K["n9"], -17)

# tour de la Terre
whoosh(K["n9"] + .3, 2.6, -15, 400, 4000)
for k in range(7):
    add(K["n9"] + .3 + k * .42, bp(noise(.03), 2000, 5000) * np.exp(-tv(.03) * 150), -21 if k % 2 else -18)
zoom(K["retour9"], -10, .35)
thud(K["retour9"] + .35, 90, .2, -14)
snore(K["retour9"] + .6, K["n10"], -15)

# orbite : passage qui monte et redescend
x = tv(3.2)
f = 500 + 900 * np.sin(np.pi * x / 3.2)
add(K["n10"] + .1, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * x / 3.2) * .4, -20)
whoosh(K["n10"] + .1, 3.2, -15, 300, 4000)
mrrp(K["n10"] + 2.3, -12, 120)

# libération : décollage
d = 2.6
x = tv(d)
add(K["n11"] + .3, (lp(noise(d), 300, 4) * 3 + bp(noise(d), 600, 4000) * .5) * np.minimum(x / .3, 1) * np.exp(-np.maximum(x - 1.2, 0) * 1.5), -8)
for k in range(4):
    ding(K["n11"] + 1.3 + k * .18, 1318.5 * 2 ** (k * 4 / 12), -18, .4)

# voyage : tic-tac
for k in range(7):
    add(K["quitte"] + .2 + k * .44, bp(noise(.03), 2000, 5000) * np.exp(-tv(.03) * 150), -21 if k % 2 else -18)

# Lune : alunissage feutré, sieste
thud(K["lune"] + .45, 70, .5, -8)
for k in range(3):
    ding(K["lune"] + 1.1 + k * .5, 660 * (1, 1.25, 1.5)[k], -22, .8)

# matin : oiseaux, Gérard
for tt in (.3, 1.0, 1.8, 2.5):
    chirp(K["calme"] + tt, -20)
snore(K["calme"], K["calme"] + 1.0, -16)
voice(K["calme"] + 1.3, 215, 3, -11)

# retour de la Lune
whoosh(K["n12"] + .2, 3.0, -14, 300, 5000)
for k in range(7):
    add(K["n12"] + .2 + k * .44, bp(noise(.03), 2000, 5000) * np.exp(-tv(.03) * 150), -21 if k % 2 else -18)

# fin : vitre, atterrissage, « Miaou. », « NON. »
whoosh(K["fin"], .3, -10, 600, 7000)
add(K["fin"] + .25, hp(noise(.5), 2500) * np.exp(-tv(.5) * 8), -6)
for k in range(10):
    ding(K["fin"] + .28 + rs.uniform(0, .6), rs.uniform(2500, 5000), rs.uniform(-24, -16), .25)
thud(K["fin"] + .45, 70, .4, -6)
mrrp(K["fin"] + 1.0, -8, 370)
voice(K["fin"] + 1.9, 215, 2, -9)

i = int(CARD * SR)
FX[i:] = 0
MUS[i:] = 0
thud(CARD + .05, 40, .7, -3)
mrrp(CARD + 1.6, -12, 300)

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
wavfile.write("son16.wav", SR, (np.clip(st, -1, 1) * 32767).astype(np.int16))
print("pic", pk, "crête vraie dB", 20 * np.log10(tp), "durée", END)
