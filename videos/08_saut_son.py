"""Son de la vidéo 08 : marche sautillante qui monte à chaque saut, « boing » de plus en plus aigu, bang supersonique, espace calme, retour fracassant."""
import numpy as np
from scipy.signal import butter, sosfilt, resample_poly
from scipy.io import wavfile
from scipy.ndimage import maximum_filter1d, uniform_filter1d
import importlib.util as _u, os as _o, sys
_sp = _u.spec_from_file_location("saut", _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "08_saut.py"))
ch = _u.module_from_spec(_sp); _sp.loader.exec_module(ch)
BEATS, K, CARD, END, JUMPS = ch.BEATS, ch.K, ch.CARD, ch.END, ch.JUMPS

SR = 48000
N = int(END * SR) + SR
rs = np.random.RandomState(48)
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


# ---- musique : marche sautillante, un demi-ton plus haut à chaque saut ; pause dans l'espace
mel = [0, 4, 7, 12, 9, 7, 4, None, 5, 7, 9, None, 7, None, None, None]
bas = [0, 7, 5, 7]
ZONES = [(0, K["s17"]), (K["croq"], K["fin"] + 3.4)]
for z0, z1 in ZONES:
    t0, i = z0, 0
    while t0 < z1:
        nj = sum(1 for j in JUMPS if j <= t0)
        root = 110.0 * 2 ** (min(nj, 10) / 12)
        if i % 2 == 0:
            mus(t0, tuba(root * 2 ** (bas[(i // 2) % 4] / 12), .3), -7)
        m = mel[i % len(mel)]
        if m is not None:
            mus(t0, mallet(root * 4 * 2 ** (m / 12)), -12)
        if i % 4 == 2:
            mus(t0, hp(noise(.04), 6000) * np.exp(-tv(.04) * 90), -27)
        i += 1
        t0 += 60 / (124 + nj * 2) / 2
    fade = int(.2 * SR)
    s1 = int(z1 * SR)
    MUS[s1 - fade:s1] *= np.linspace(1, 0, fade)
    MUS[s1:int((ZONES[1][0] if z0 == 0 else END) * SR)] = 0
# espace : nappe douce (s17 → croq)
d = K["croq"] - K["s17"]
x = tv(d)
pad = sum(np.sin(2 * np.pi * f * x) for f in (220, 277.2, 329.6, 440)) * (.6 + .4 * np.sin(2 * np.pi * .25 * x))
pad *= np.minimum(x / 1.0, 1) * np.minimum((d - x) / .4, 1)
mus(K["s17"], lp(pad, 2000) * .25, -8)
for k, f in enumerate((880, 1109, 1319, 1109, 988, 1319, 1760, 1319) * 3):
    mus(K["s17"] + .3 + k * .9, mallet(f, .6), -20)

# ---- chaque saut : « boing » de plus en plus aigu + souffle
for n, j in enumerate(JUMPS):
    boing(j, 160 * 1.09 ** n, -7)
    whoosh(j + .02, .6, -14, 500, 6000)

# ---- temps forts
for b in BEATS:
    if b["ger"]:
        voice(b["start"] + .38, 215, min(2 + len(b["ger"]) // 5, 5))
# accroche : petit miaulement
mrrp(K["hook"] + 1.4, -8)
# étagère : vase qui tombe et casse
whoosh(K["s0"] + 1.5, .5, -18, 1500, 6000)
crash(K["s0"] + 2.0, .6, -9)
# plafond : bonk + plâtre
thud(K["s1"] + .45, 90, .5, -3)
add(K["s1"] + .45, np.sin(2 * np.pi * 620 * tv(.4)) * np.exp(-tv(.4) * 10), -14)
for k in range(8):
    add(K["s1"] + .9 + k * .12, hp(noise(.03), 2500) * np.exp(-tv(.03) * 120), -18)
# toit : tuiles
crash(K["s2"] + .1, 1.0, -8)
for k in range(5):
    add(K["s2"] + 1.2 + k * .17, bp(noise(.05), 800, 4000) * np.exp(-tv(.05) * 60), -16)
# pigeons : battements d'ailes
for k in range(14):
    add(K["s4"] + .4 + k * .07, bp(noise(.05), 300, 2500) * np.hanning(int(.05 * SR)), -15, (k % 3 - 1) * .5)
# Paris : cloche lointaine
ding(K["s8"] + 1.0, 523, -16, 1.2)
# téléphone
for k in range(2):
    ding(K["veto"] + .15 + k * .5, 1480, -18, .25)
# avion : moteur qui passe
d = 3.2
x = tv(d)
add(K["s13"], lp(noise(d), 700) * np.hanning(len(x)), -18, .4)
# mur du son : BANG
x = tv(1.2)
add(K["mach"] + .55, np.sin(2 * np.pi * np.cumsum(38 + 80 * np.exp(-x * 7)) / SR) * np.exp(-x * 4), 0)
add(K["mach"] + .55, lp(noise(1.2), 2500) * np.exp(-x * 6), -4)
add(K["mach"] + .62, lp(noise(.8), 1800) * np.exp(-tv(.8) * 7), -8)
whoosh(K["mach"], 3.0, -16, 300, 3000)
# ISS : bips
for k in range(3):
    ding(K["s18"] + .9 + k * .3, 1500, -20, .2)
mrrp(K["s18"] + 1.8, -10, 200)
# filet : clic
for k in range(2):
    add(K["filet"] + .3 + k * .25, hp(noise(.02), 2000) * np.exp(-tv(.02) * 150), -14)
# décollage vers la Lune : grand souffle grave
x = tv(2.0)
add(K["s28"], lp(noise(2.0), 300) * np.exp(-x * 1.5), -4)
add(K["vit"] + .2, np.sin(2 * np.pi * np.cumsum(200 + 600 * np.minimum(tv(1.2) / 1.2, 1)) / SR) * np.hanning(int(1.2 * SR)), -18)
# sieste : ronron
d = 2.8
x = tv(d)
add(K["voyage"] + .1, lp(noise(d), 300) * (.5 + .5 * np.sin(2 * np.pi * 25 * x)) * (.5 + .5 * np.sin(2 * np.pi * .7 * x)) ** 2 * np.hanning(len(x)), -10)
# Lune : atterrissage feutré + fanfare
thud(K["lune"] + .45, 70, .4, -10)
for k, f in enumerate((523, 659, 784, 1047)):
    ding(K["lune"] + 1.1 + k * .12, f, -14, .6)
mrrp(K["lune"] + 2.2, -8, 260)
# croquettes : tchk tchk
for k in range(9):
    add(K["croq"] + .5 + k * .2, bp(noise(.07), 1500, 8000) * np.exp(-tv(.07) * 40), -9, .3)
# retour : sifflement de chute + crash
x = tv(.5)
add(K["retour"], np.sin(2 * np.pi * np.cumsum(2200 - 1600 * x / .5) / SR) * np.minimum(x / .05, 1), -16)
thud(K["retour"] + .5, 45, .9, 0)
crash(K["retour"] + .5, .9, -8)
mrrp(K["retour"] + 1.4, -6, 300)
# fin : croque, puis NON
for k in range(6):
    add(K["fin"] + .3 + k * .3, bp(noise(.04), 1000, 5000) * np.exp(-tv(.04) * 70), -16)
i = int(CARD * SR)
FX[i:] = 0
MUS[i:] = 0
x = tv(.6)
add(CARD + .05, np.sin(2 * np.pi * np.cumsum(40 + 70 * np.exp(-x * 9)) / SR) * np.exp(-x * 6), -3)
boing(CARD + 1.6, 300, -12)

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
wavfile.write("son8.wav", SR, (np.clip(st, -1, 1) * 32767).astype(np.int16))
print("pic", pk, "crête vraie dB", 20 * np.log10(tp), "durée", END)
