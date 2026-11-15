"""Son de la vidéo 14 : thème sautillant, bourdonnement du laser qui monte avec la puissance, « piou » à chaque jour,
grésillement du tapis, disqueuse sur le mur, voisin, pigeon ; dehors, nappe spatiale ; « cronch » et « aïe » à la fin."""
import numpy as np
from scipy.signal import butter, sosfilt, resample_poly
from scipy.io import wavfile
from scipy.ndimage import maximum_filter1d, uniform_filter1d
import importlib.util as _u, os as _o, sys
_sp = _u.spec_from_file_location("laser", _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "14_laser.py"))
ch = _u.module_from_spec(_sp); _sp.loader.exec_module(ch)
BEATS, K, CARD, END, JUMPS, d_at = ch.BEATS, ch.K, ch.CARD, ch.END, ch.JUMPS, ch.d_at

SR = 48000
N = int(END * SR) + SR
rs = np.random.RandomState(14)
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


# ---- musique : thème sautillant dans le salon, nappe spatiale dehors
mel = [0, 4, 7, 4, 9, 7, 4, None, 2, 5, 9, 5, 7, None, None, None]
bas = [0, 5, 7, 5]
t0, i = K["regle"], 0
z1 = K["j43"]
while t0 < z1:
    root = 146.8 * (2 ** (2 / 12) if t0 >= K["j17"] else 1)
    gm = -3 if t0 >= K["j24"] else 0
    if i % 2 == 0:
        mus(t0, tuba(root * 2 ** (bas[(i // 2) % 4] / 12), .3), -7 + gm)
    m = mel[i % len(mel)]
    if m is not None:
        mus(t0, mallet(root * 4 * 2 ** (m / 12)), -12 + gm)
    if i % 4 == 2:
        mus(t0, hp(noise(.04), 6000) * np.exp(-tv(.04) * 90), -27 + gm)
    i += 1
    t0 += 60 / 124 / 2
fade = int(.1 * SR)
s1 = int(z1 * SR)
MUS[s1 - fade:s1] *= np.linspace(1, 0, fade)
MUS[s1:] = 0


def pad(t0, t1, chord, g):
    d = t1 - t0
    x = tv(d)
    v = sum(np.sin(2 * np.pi * f * x + .3 * np.sin(2 * np.pi * .2 * x)) for f in chord)
    mus(t0, lp(v, 1800) * np.minimum(x / .6, 1) * np.minimum((d - x) / .3, 1) * .3, g)


# accroche (dehors) et finale dehors : nappe + arpège de célesta
for (a, b_) in ((0, K["regle"]), (K["j43"], CARD)):
    pad(a, b_, (110, 164.8, 220, 277.2), -9)
    tt, k = a + .2, 0
    arp = (880, 1108.7, 1318.5, 1760, 1318.5, 1108.7)
    while tt < b_ - .3:
        mus(tt, mallet(arp[k % len(arp)], .6), -19)
        tt += .3
        k += 1

# ---- bourdonnement du laser : monte avec la puissance (salon)
a, b_ = K["regle"], K["j43"]
n = int((b_ - a) * SR)
tt = a + np.arange(n) / SR
step = int(.02 * SR)
days = np.array([d_at(a + j / SR) for j in range(0, n, step)])
days = np.interp(np.arange(n), np.arange(0, n, step), days)
f = 70 * 2 ** ((days - 1) / 10)
lev = db2(-36 + 20 * np.clip((days - 1) / 27, 0, 1))
ph = 2 * np.pi * np.cumsum(f) / SR
hum = (np.sin(ph) + .4 * np.sin(2 * ph) + .2 * np.sin(3 * ph)) * lev
hum *= np.minimum((tt - a) / .3, 1) * np.minimum((b_ - tt) / .1, 1)
add(a, hum.astype(np.float32), 0)

# ---- « piou » + petit pop à chaque nouveau jour
for tk in JUMPS:
    piou(tk, -11)
    ding(tk + .03, 1760, -21, .2)

# ---- grésillement du tapis (jour 17 et après, jusqu'au ciel)
a, b_ = K["j17"] + .4, K["j28"]
x = tv(b_ - a)
cr = hp(noise(b_ - a), 3000) * (rs.rand(len(x)) < .004) * 6
fz = bp(noise(b_ - a), 2000, 9000) * .25
add(a, ((cr + fz) * np.minimum(x / .5, 1) * np.minimum((x[-1] - x) / .2, 1)).astype(np.float32), -17)

# ---- disqueuse sur le mur (jour 24), étincelles
d = K["j26"] - K["j24"] - .2
x = tv(d)
saw = 2 * ((900 * x + 40 * np.sin(2 * np.pi * 3 * x)) % 1) - 1
add(K["j24"] + .2, bp(saw + .6 * noise(d), 1500, 7000) * np.minimum(x / .2, 1) * np.minimum((d - x) / .1, 1), -19)
# le bloc de mur tombe chez le voisin, puis le voisin crie
thud(K["j26"] + .15, 50, .8, -6)
voice(K["j26"] + .9, 150, 4, -9)
voice(K["michel"] + .05, 150, 3, -16)
mrrp(K["michel"] + .7, -9, 250)

# ---- le ciel : souffle, pigeon
whoosh(K["j28"] + .5, .9, -15, 300, 3000, .4)
for k in range(2):
    x = tv(.25)
    add(K["j28"] + 1.6 + k * .3, np.sin(2 * np.pi * (330 - 60 * x / .25) * x) * np.hanning(len(x)), -15)
for k in range(6):
    whoosh(K["j28"] + 1.3 + k * .09, .08, -22, 500, 3000)

# ---- petits gags du salon
# couinement du jouet (véto)
for k in range(2):
    x = tv(.18)
    add(K["veto"] + .5 + k * .35, np.sin(2 * np.pi * np.cumsum(1500 + 900 * np.sin(np.pi * x / .18)) / SR) * np.hanning(len(x)), -17)
# bâillement
x = tv(1.2)
v = sum(np.sin(2 * np.pi * np.cumsum((420 - 220 * x / 1.2) * k) / SR) / k for k in (1, 2, 3))
add(K["j6"] + 1.0, bp(v, 200, 2500) * np.hanning(len(x)), -14)
# alarme « danger » (classe 4)
for k in range(3):
    ding(K["j10"] + .5 + k * .22, 988, -20, .18)
# panneaux qui apparaissent
for key, dl in (("loi", .3), ("j10", .5), ("j21", .6), ("j24", .6), ("dist", .3), ("calc", .4)):
    whoosh(K[key] + dl - .05, .2, -22, 800, 6000)

# ---- bulles de Gérard
for b in BEATS:
    if b["ger"] and b["key"] not in ("fin",):
        voice(b["start"] + .4, 215, min(2 + len(b["ger"]) // 5, 4), -11)

# ---- dehors : allumage vers la Lune
x = tv(.6)
add(K["j43"] + .05, np.sin(2 * np.pi * np.cumsum(200 + 1600 * (x / .6) ** 2) / SR) * np.hanning(len(x)), -14)
thud(K["j43"] + .55, 45, 1.0, -5)
piou(0.15, -13)
# la lumière part : 1,3 s
x = tv(ch.T_LUM)
add(K["dist"] + .5, np.sin(2 * np.pi * np.cumsum(600 + 900 * x / x[-1]) / SR) * np.minimum(x / .05, 1) * np.minimum((x[-1] - x) / .05, 1) * .5, -18)
ding(K["dist"] + .5 + ch.T_LUM, 2093, -15, .6)
for k in range(2):
    ding(K["calc"] + .5 + k * .12, (1568, 2093)[k], -18, .4)
# « ! » de Michel, saut, cronch, aïe, laser qui tombe
ding(K["doigt"] + 1.0, 1318, -14, .3)
whoosh(K["fin"], .45, -12, 500, 5000)
crunch(K["fin"] + .45, -5)
crunch(K["fin"] + .62, -9)
x = tv(.45)
v = sum(np.sin(2 * np.pi * np.cumsum((520 + 300 * np.exp(-x * 6)) * k) / SR) / k for k in (1, 2, 3, 4))
add(K["fin"] + .5, bp(v, 300, 3500) * np.hanning(len(x)) ** .5, -9)
ding(K["fin"] + .8, 3200, -17, .25)
ding(K["fin"] + .86, 2700, -19, .25)
mrrp(K["fin2"] + 1.6, -10, 300)

i = int(CARD * SR)
FX[i:] = 0
MUS[i:] = 0
thud(CARD + .05, 40, .7, -3)
piou(CARD + 1.6, -12)

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
wavfile.write("son14.wav", SR, (np.clip(st, -1, 1) * 32767).astype(np.int16))
print("pic", pk, "crête vraie dB", 20 * np.log10(tp), "durée", END)
