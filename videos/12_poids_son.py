"""Son de la vidéo 12 : marche qui descend d'un demi-ton à chaque croquette (plus lourd), crunch + boum de plus en plus grave, plancher qui casse, grondement sous terre, lave, trou noir."""
import numpy as np
from scipy.signal import butter, sosfilt, resample_poly
from scipy.io import wavfile
from scipy.ndimage import maximum_filter1d, uniform_filter1d
import importlib.util as _u, os as _o, sys
_sp = _u.spec_from_file_location("poids", _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "12_poids.py"))
ch = _u.module_from_spec(_sp); _sp.loader.exec_module(ch)
BEATS, K, CARD, END, JUMPS = ch.BEATS, ch.K, ch.CARD, ch.END, ch.JUMPS

SR = 48000
N = int(END * SR) + SR
rs = np.random.RandomState(12)
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


def boing(t0, f=180, g=-7, d=.5):
    x = tv(d)
    fr = f * (1 + 1.2 * x / d) * (1 + .25 * np.sin(2 * np.pi * 14 * x) * np.exp(-x * 4))
    add(t0, np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-x * 5) * np.minimum(x / .005, 1), g)


def thud(t0, f=55, d=.7, g=-2):
    x = tv(d)
    add(t0, np.sin(2 * np.pi * np.cumsum(f + 90 * np.exp(-x * 12)) / SR) * np.exp(-x * 5), g)
    add(t0, lp(noise(d), 1400) * np.exp(-x * 11), g - 3)


def crash(t0, d=.8, g=-9):
    x = tv(d)
    add(t0, bp(noise(d), 1500, 9000) * np.exp(-x * 6) * np.minimum(x / .003, 1), g)
    for k in range(6):
        ding(t0 + .05 + k * .07, rs.uniform(2500, 5000), g - 6, .15)


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


def ding(t0, f=1320, g=-14, d=.5):
    x = tv(d)
    add(t0, (np.sin(2 * np.pi * f * x) + .3 * np.sin(4 * np.pi * f * x)) * np.exp(-x * 9), g)



def crunch(t0, g=-8):
    for k in range(3):
        add(t0 + k * .06, bp(noise(.05), 1200, 7000) * np.exp(-tv(.05) * 60), g - k * 2)


# ---- musique : marche, un demi-ton plus bas à chaque croquette ; nappe sous terre et dans l'espace
mel = [0, 4, 7, 12, 9, 7, 4, None, 5, 7, 9, None, 7, None, None, None]
bas = [0, 7, 5, 7]
ZONES = [(0, K["sol"]), (K["ficelle"], K["c85"])]
for z0, z1 in ZONES:
    t0, i = z0, 0
    while t0 < z1:
        nj = sum(1 for j in JUMPS if j <= t0)
        root = 130.8 * 2 ** (-min(nj, 9) / 12)
        if i % 2 == 0:
            mus(t0, tuba(root * 2 ** (bas[(i // 2) % 4] / 12), .3), -7)
        m = mel[i % len(mel)]
        if m is not None:
            mus(t0, mallet(root * 4 * 2 ** (m / 12)), -12)
        if i % 4 == 2:
            mus(t0, hp(noise(.04), 6000) * np.exp(-tv(.04) * 90), -27)
        i += 1
        t0 += 60 / (124 - nj * 2) / 2
    fade = int(.25 * SR)
    s1 = int(z1 * SR)
    MUS[s1 - fade:s1] *= np.linspace(1, 0, fade)
for (a, z, chord) in ((K["sol"], K["ficelle"], (110, 130.8, 164.8, 220)), (K["c85"], CARD, (55, 82.4, 110, 138.6))):
    d = z - a
    x = tv(d)
    pad = sum(np.sin(2 * np.pi * f * x) for f in chord) * (.6 + .4 * np.sin(2 * np.pi * .25 * x))
    pad *= np.minimum(x / .8, 1) * np.minimum((d - x) / .3, 1)
    mus(a, lp(pad, 1800) * .28, -8)
for k, f in enumerate((440, 554, 659, 554, 494, 659, 880, 659) * 2):
    mus(K["centre"] + .3 + k * .8, mallet(f, .6), -20)

# ---- chaque croquette : crunch + boum de plus en plus grave
for b in BEATS:
    if b["n1"] > b["n0"] and b["key"] != "ficelle":
        crunch(b["start"] - .02, -8)
        f = max(30, 90 * .985 ** b["n1"])
        thud(b["start"] + .05, f, .8, -3)
for b in BEATS:
    if b["ger"]:
        voice(b["start"] + .38, 215, min(2 + len(b["ger"]) // 5, 5))
mrrp(K["hook"] + 1.2, -8)
# règle : croquette lancée + crunch
whoosh(K["regle"] + 1.4, .5, -16, 800, 5000)
crunch(K["regle"] + 1.9, -8)
mrrp(K["c0"] + 1.2, -9, 250)
# balance qui craque
for k in range(3):
    add(K["c4"] + .3 + k * .08, bp(noise(.06), 500, 3000) * np.exp(-tv(.06) * 40), -12)
# plancher
add(K["c8"] + .3, bp(noise(.4), 200, 2500) * np.exp(-tv(.4) * 6), -10)
crash(K["c8"] + .7, 1.0, -6)
thud(K["c8"] + .75, 40, 1.2, 0)
x = tv(.5)
add(K["c8"] + .7, np.sin(2 * np.pi * np.cumsum(1800 - 1300 * x / .5) / SR) * np.minimum(x / .05, 1) * .5, -16)
for k in range(2):
    ding(K["veto"] + .15 + k * .5, 1480, -18, .25)
# baleine : chant grave
x = tv(1.6)
add(K["c15"] + .6, np.sin(2 * np.pi * np.cumsum(180 + 90 * np.sin(np.pi * x / 1.6)) / SR) * np.hanning(len(x)), -12)
# tours Eiffel : grincement métallique
x = tv(1.0)
add(K["c22"] + .3, bp(np.sin(2 * np.pi * np.cumsum(300 + 80 * np.sin(x * 9)) / SR) + .3 * noise(1.0), 300, 3000) * np.hanning(len(x)), -15)
# sous terre : grondement
d = K["centre"] + .9 - K["sol"]
x = tv(d)
add(K["sol"], lp(noise(d), 160) * np.minimum(x / .3, 1) * np.minimum((d - x) / .2, 1), -2)
thud(K["centre"] + .9, 45, .9, -2)
# lave : bulles
for k in range(26):
    tt = K["chaud"] + k * .27 + rs.uniform(0, .1)
    x = tv(.08)
    add(tt, np.sin(2 * np.pi * np.cumsum(200 + 900 * x / .08) / SR) * np.hanning(len(x)), -18, rs.uniform(-.5, .5))
d = 2.6
x = tv(d)
add(K["chaud"] + .6, lp(noise(d), 300) * (.5 + .5 * np.sin(2 * np.pi * 25 * x)) * np.hanning(len(x)), -10)
# ficelle : crunchs en rafale
for k in range(16):
    crunch(K["ficelle"] + .3 + k * .19, -14)
# Lune inquiète
mrrp(K["c74"] + 1.5, -12, 150)
# balance de Gérard : bip
ding(K["gkg"] + .9, 1760, -14, .2)
ding(K["gkg"] + 1.0, 1760, -14, .2)
add(K["c80"] + .1, bp(noise(.5), 150, 1500) * np.exp(-tv(.5) * 5), -10)
# c85 : montée grave
d = 3.4
x = tv(d)
add(K["c85"], np.sin(2 * np.pi * np.cumsum(40 + 160 * (x / d) ** 2) / SR) * (x / d), -6)
add(K["c85"], hp(noise(d), 3000) * (x / d) ** 3, -18)
# trou noir : choc puis aspiration
x = tv(2.0)
add(K["bh"], np.sin(2 * np.pi * np.cumsum(30 + 60 * np.exp(-x * 3)) / SR) * np.exp(-x * 1.5), 0)
add(K["bh"], lp(noise(2.0), 2000) * np.exp(-x * 2), -6)
d = 2.8
x = tv(d)
add(K["bh"] + .3, bp(noise(d), 300, 2500) * np.hanning(len(x)) * (.6 + .4 * np.sin(2 * np.pi * 3 * x)), -12)
mrrp(K["fin"] + 1.0, -5, 320)
i = int(CARD * SR)
FX[i:] = 0
MUS[i:] = 0
x = tv(.6)
add(CARD + .05, np.sin(2 * np.pi * np.cumsum(40 + 70 * np.exp(-x * 9)) / SR) * np.exp(-x * 6), -3)
crunch(CARD + 1.6, -10)

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
wavfile.write("son12.wav", SR, (np.clip(st, -1, 1) * 32767).astype(np.int16))
print("pic", pk, "crête vraie dB", 20 * np.log10(tp), "durée", END)
