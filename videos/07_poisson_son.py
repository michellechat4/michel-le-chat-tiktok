"""Son de la vidéo 07 : marche aquatique qui monte à chaque doublement, « bloup » de plus en plus grave, duel en silence tendu."""
import numpy as np
from scipy.signal import butter, sosfilt, resample_poly
from scipy.io import wavfile
from scipy.ndimage import maximum_filter1d, uniform_filter1d
import importlib.util as _u, os as _o, sys
_sp = _u.spec_from_file_location("poisson", _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "07_poisson.py"))
ch = _u.module_from_spec(_sp); _sp.loader.exec_module(ch)
BEATS, K, CARD, END, JUMPS = ch.BEATS, ch.K, ch.CARD, ch.END, ch.JUMPS

SR = 48000
N = int(END * SR) + SR
rs = np.random.RandomState(47)
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


def bloup(t0, f=420, g=-8, d=.16, pan=0.0):
    x = tv(d)
    fr = f * (1 + 1.8 * x / d)
    add(t0, np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.hanning(len(x)) ** .5 * np.exp(-x * 14), g, pan)


def thud(t0, f=55, d=.7, g=-2):
    x = tv(d)
    add(t0, np.sin(2 * np.pi * np.cumsum(f + 90 * np.exp(-x * 12)) / SR) * np.exp(-x * 5), g)
    add(t0, lp(noise(d), 1400) * np.exp(-x * 11), g - 3)


def splash(t0, d=.8, g=-9):
    x = tv(d)
    add(t0, bp(noise(d), 600, 7000) * np.exp(-x * 5) * np.minimum(x / .01, 1), g)


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


# ---- musique : marche sautillante, un demi-ton plus haut à chaque doublement, jusqu'au duel
mel = [0, 4, 7, None, 9, 7, 4, None, 5, None, 4, 2, 0, None, None, None]
bas = [0, 7, 5, 7]
STOP = K["duel"]
t0, i = 0.0, 0
while t0 < STOP:
    nj = sum(1 for j in JUMPS if j <= t0)
    root = 110.0 * 2 ** (min(nj, 12) / 12)
    if i % 2 == 0:
        mus(t0, tuba(root * 2 ** (bas[(i // 2) % 4] / 12), .3), -7)
    m = mel[i % len(mel)]
    if m is not None:
        mus(t0, mallet(root * 4 * 2 ** (m / 12)), -12)
    if i % 4 == 2:
        mus(t0, hp(noise(.04), 6000) * np.exp(-tv(.04) * 90), -27)
    i += 1
    t0 += 60 / (122 + nj * 1.5) / 2
fade = int(.15 * SR)
s0 = int(STOP * SR)
MUS[s0 - fade:s0] *= np.linspace(1, 0, fade)
MUS[s0:] = 0

# ---- chaque doublement : « bloup » de plus en plus grave + souffle
for n, j in enumerate(JUMPS):
    f = 900 * 0.86 ** n
    bloup(j, f, -6)
    bloup(j + .09, f * 1.3, -12)
    whoosh(j - .06, .35, -16, 300, 3000)
    thud(j, 60 - n * 1.5, .5, -10 - max(0, 6 - n))

# ---- temps forts
for b in BEATS:
    if b["ger"]:
        voice(b["start"] + .38, 215, min(2 + len(b["ger"]) // 5, 5))
for k in range(3):
    bloup(K["hook"] + .6 + k * .7, 1400, -16, .1, .3)
mrrp(K["j1"] + 1.2, -9)
for k in range(3):
    add(K["j1"] + .3 + k * .25, bp(noise(.06), 1500, 5000) * np.exp(-tv(.06) * 50), -20)   # coup de langue
# bocal qui craque
for k in range(3):
    add(K["j3"] + .5 + k * .18, hp(noise(.03), 3000) * np.exp(-tv(.03) * 120), -12)
ding(K["j3"] + 1.4, 1760, -18, .3)
splash(K["j4"] + .05, 1.0, -7)
# Michel recule
whoosh(K["recul"] + .6, .3, -12, 800, 5000, -.4)
add(K["recul"] + 1.3, np.sin(2 * np.pi * np.cumsum(300 - 120 * tv(.3)) / SR) * np.hanning(int(.3 * SR)), -20)
splash(K["j5"] + .1, 1.2, -8)
# mémoire : souvenir (réverbération de carillons)
for k, f in enumerate((1047, 1319, 1568, 1319)):
    ding(K["memo"] + .3 + k * .14, f, -17, 1.0)
thud(K["memo"] + 1.6, 90, .3, -7)   # tampon N'OUBLIE PAS
splash(K["j7"] + .05, 1.0, -8)
# mer : vagues
for key in ("j9", "j10"):
    d = 3.0
    x = tv(d)
    add(K[key], lp(noise(d), 900) * (0.6 + .4 * np.sin(2 * np.pi * .6 * x)) * np.hanning(len(x)), -17)
# Paris : il se dresse, cloche lointaine
add(K["j13"] + .1, np.sin(2 * np.pi * np.cumsum(120 + 200 * tv(.8)) / SR) * np.hanning(int(.8 * SR)), -16)
ding(K["j13"] + 1.0, 523, -16, 1.2)
# fosse : grondement grave
d = 3.0
x = tv(d)
add(K["j18"], lp(noise(d), 160) * np.hanning(len(x)), -8)
# espace : sonar
for k in range(3):
    ding(K["j21"] + .9 + k * .6, 1200, -20, .4)
# entraînement : griffes
for k in range(4):
    add(K["entr"] + .1 + k * .55, bp(noise(.18), 2500, 9000) * np.hanning(int(.18 * SR)), -13, -.3)
mrrp(K["entr"] + 2.4, -10, 250)
# Terre et Lune : montée
for key in ("j28", "j33"):
    d = 1.0
    x = tv(d)
    add(K[key] + .1, np.sin(2 * np.pi * np.cumsum(200 + 400 * x / d) / SR) * np.hanning(len(x)), -18)

# ---- duel : drone grave, battement de cœur, puis fuite
d = K["fuite"] - K["duel"]
x = tv(d)
add(K["duel"], (np.sin(2 * np.pi * 55 * x) + .5 * np.sin(2 * np.pi * 58.3 * x)) * np.minimum(x / 1.2, 1) * np.minimum((d - x) / .05, 1), -9)
add(K["duel"], bp(noise(d), 700, 2200) * x / d, -30)
for k in range(8):
    tb = K["duel"] + .4 + k * .72
    thud(tb, 48, .25, -10)
    thud(tb + .18, 44, .25, -14)
add(K["regard"] + .4, np.sin(2 * np.pi * np.cumsum(260 + 70 * tv(.4)) / SR) * np.exp(-tv(.4) * 7), -18)  # gorgée
whoosh(K["fuite"], 1.4, -4, 200, 6000, .3)
for k in range(5):
    bloup(K["fuite"] + .2 + k * .2, 600 + k * 180, -14, .12, .4)
mrrp(K["fuite"] + 1.9, -4, 180)
# ---- fin : petite reprise de la marche
for k, (f, dt) in enumerate(((440, .4), (554, .65), (659, .9), (880, 2.0))):
    mus(K["fin"] + dt, mallet(f, .4), -10)
bloup(K["fin"] + 1.2, 1500, -14, .1)
mrrp(K["fin"] + 2.6, -7, 220)
for k, (f, dt) in enumerate(((220, 3.0), (277.2, 3.25), (329.6, 3.5))):
    mus(K["fin"] + dt, tuba(f, .3), -8)
i = int(CARD * SR)
FX[i:] = 0
MUS[i:] = 0
x = tv(.6)
add(CARD + .05, np.sin(2 * np.pi * np.cumsum(40 + 70 * np.exp(-x * 9)) / SR) * np.exp(-x * 6), -3)
bloup(CARD + 1.6, 700, -12)

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
wavfile.write("son7.wav", SR, (np.clip(st, -1, 1) * 32767).astype(np.int16))
print("pic", pk, "crête vraie dB", 20 * np.log10(tp), "durée", END)
