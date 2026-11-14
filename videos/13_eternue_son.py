"""Son de la vidéo 13 : thème sautillant, « Ah… TCHOUM ! » synthétisés, puis les éternuements fusionnent en bourdonnement (24 Hz),
en note (388 Hz, puis 777 Hz), en sifflement (6 214 Hz, discret), puis silence total quand ça dépasse l'oreille humaine. Berceuse à la fin."""
import numpy as np
from scipy.signal import butter, sosfilt, resample_poly
from scipy.io import wavfile
from scipy.ndimage import maximum_filter1d, uniform_filter1d
import importlib.util as _u, os as _o, sys
_sp = _u.spec_from_file_location("eternue", _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "13_eternue.py"))
ch = _u.module_from_spec(_sp); _sp.loader.exec_module(ch)
BEATS, K, CARD, END, JUMPS, SNZ, PRE, par_s = ch.BEATS, ch.K, ch.CARD, ch.END, ch.JUMPS, ch.SNZ, ch.PRE, ch.par_s

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



def ah(t0, g=-9):
    d = PRE
    x = tv(d)
    f = 170 + 90 * (x / d)
    v = sum(np.sin(2 * np.pi * np.cumsum(f * k) / SR) / k for k in range(1, 7))
    v = bp(v, 300, 2600) * np.minimum(x / .05, 1) * (x / d) ** .5
    add(t0 - d, norm(v), g)


def tchoum(t0, g=-3):
    d = .5
    x = tv(d)
    add(t0, bp(noise(d), 1800, 7500) * np.exp(-x * 9) * np.minimum(x / .004, 1), g)
    x2 = tv(.35)
    f = 200 - 70 * x2 / .35
    v = sum(np.sin(2 * np.pi * np.cumsum(f * k) / SR) / k for k in range(1, 5))
    add(t0 + .12, lp(v, 900) * np.hanning(len(x2)), g - 4)


def train(t0, d, f, g, lo=100, hi=4000, click=.004):
    """Train d'impulsions de bruit à f par seconde (les éternuements fusionnés)."""
    x = tv(d)
    ph = (x * f) % 1
    env = np.exp(-ph / (click * f)) if click * f < 1 else np.ones_like(x)
    sig = bp(noise(d) * env, lo, hi)
    sig = sig * np.minimum(x / .15, 1) * np.minimum((d - x) / .1, 1)
    add(t0, norm(sig), g)


def tone(t0, d, f, g):
    x = tv(d)
    v = (np.sin(2 * np.pi * f * x) + .3 * np.sin(4 * np.pi * f * x) + .15 * np.sin(6 * np.pi * f * x)) * (1 + .05 * np.sin(2 * np.pi * 5 * x))
    add(t0, norm(v) * np.minimum(x / .12, 1) * np.minimum((d - x) / .1, 1), g)


# ---- musique : thème sautillant jusqu'au jour 32, puis silence ; berceuse à la fin
mel = [0, 4, 7, 4, 9, 7, 4, None, 2, 5, 9, 5, 7, None, None, None]
bas = [0, 5, 7, 5]
t0, i = 0.0, 0
z1 = K["j32"]
while t0 < z1:
    root = 146.8
    gm = -4 if t0 >= K["j22"] else 0
    if i % 2 == 0:
        mus(t0, tuba(root * 2 ** (bas[(i // 2) % 4] / 12), .3), -7 + gm)
    m = mel[i % len(mel)]
    if m is not None:
        mus(t0, mallet(root * 4 * 2 ** (m / 12)), -12 + gm)
    if i % 4 == 2:
        mus(t0, hp(noise(.04), 6000) * np.exp(-tv(.04) * 90), -27 + gm)
    i += 1
    t0 += 60 / 120 / 2
fade = int(.08 * SR)
s1 = int(z1 * SR)
MUS[s1 - fade:s1] *= np.linspace(1, 0, fade)
MUS[s1:] = 0
for k, f in enumerate((523, 659, 784, 659, 587, 698, 880, 698, 523, 659, 784, 1047)):
    mus(K["fin"] + .3 + k * .55, mallet(f, .9), -16)
d = CARD - K["fin"]
x = tv(d)
pad = sum(np.sin(2 * np.pi * f * x) for f in (130.8, 164.8, 196)) * np.minimum(x / .8, 1) * np.minimum((d - x) / .2, 1)
mus(K["fin"], lp(pad, 1500) * .25, -10)

# ---- sauts de jour : petit « pop »
for tk in JUMPS:
    boing(tk, 300, -15, .25)
    ding(tk + .02, 1760, -20, .2)

# ---- éternuements un par un
for s in SNZ:
    ah(s, -10)
    tchoum(s, -3)

# ---- bulles de Gérard
for b in BEATS:
    if b["ger"] and b["key"] not in ("regle", "j1", "calme", "fin2"):
        voice(b["start"] + .38, 215, min(2 + len(b["ger"]) // 5, 5), -10)

# ---- 1 sur 10 : petits « pop » des silhouettes
for k in range(10):
    ding(K["dix"] + .1 + k * .06, 900 + k * 60, -22, .12)
# salive : léchouilles
for k in range(8):
    add(K["salive"] + .3 + k * .45, bp(noise(.07), 1500, 5000) * np.hanning(int(.07 * SR)), -20)
# horloge
for k in range(6):
    add(K["j11"] + .3 + k * .5, bp(noise(.02), 2000, 6000) * np.exp(-tv(.02) * 200), -16)

# ---- fusion : bourdonnement (24/s), notes, sifflement
train(K["j22"] + .1, K["j26"] - K["j22"] - .1, par_s(22), -4, 120, 5000, .012)
tone(K["j26"] + .05, K["voisin"] - K["j26"] - .05, par_s(26), -11)
train(K["j26"] + .05, K["voisin"] - K["j26"] - .05, par_s(26), -18, 300, 6000)
tone(K["voisin"] + .05, K["j30"] - K["voisin"] - .05, par_s(27), -13)
for k in range(60):
    tt = K["voisin"] + .9 + rs.uniform(0, 1.9)
    add(tt, bp(noise(.03), 800, 5000) * np.exp(-tv(.03) * 120), -17, rs.uniform(-.8, .8))
voice(K["voisin"] + .95, 160, 2, -16)
x = tv(K["j32"] - K["j30"] - .1)
add(K["j30"] + .05, np.sin(2 * np.pi * par_s(30) * x) * np.minimum(x / .2, 1) * np.minimum((x[-1] - x) / .05, 1), -28)
# coupure nette au jour 32 : plus rien (au-dessus de 20 000 Hz)
i0 = int(K["j32"] * SR)
FX[i0:int(K["fin"] * SR)] = 0

# silence « audible » : une horloge discrète, pour qu'on comprenne que c'est voulu
tt = K["j32"] + .4
while tt < K["fin"] - .2:
    add(tt, bp(noise(.02), 2000, 6000) * np.exp(-tv(.02) * 200), -24)
    tt += .5

# ---- jour 33 : Michel grogne (lui entend)
d = 1.6
x = tv(d)
add(K["j33"] + .5, lp(noise(d), 500) * (.6 + .4 * np.sin(2 * np.pi * 28 * x)) * np.hanning(len(x)), -10)
mrrp(K["j34"] + 1.6, -12, 200)

# ---- fin : saut sur la tête, ronflements, « Ah… » coupé
whoosh(K["fin"] + .2, .9, -16, 500, 4000)
mrrp(K["fin"] + 1.25, -9, 300)
for k in range(2):
    x = tv(.9)
    add(K["fin"] + 2.0 + k * 1.0, lp(noise(.9), 700) * np.hanning(len(x)) * .7, -20)
d = 1.5
x = tv(d)
f = 170 + 120 * (x / d)
v = sum(np.sin(2 * np.pi * np.cumsum(f * k) / SR) / k for k in range(1, 7))
add(K["fin2"] + 1.2, norm(bp(v, 300, 2600)) * np.minimum(x / .1, 1), -10)

i = int(CARD * SR)
FX[i:] = 0
MUS[i:] = 0
x = tv(.6)
add(CARD + .05, np.sin(2 * np.pi * np.cumsum(40 + 70 * np.exp(-x * 9)) / SR) * np.exp(-x * 6), -3)
tchoum(CARD + 1.8, -6)

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
wavfile.write("son13.wav", SR, (np.clip(st, -1, 1) * 32767).astype(np.int16))
print("pic", pk, "crête vraie dB", 20 * np.log10(tp), "durée", END)
