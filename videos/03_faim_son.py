import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
import importlib.util as _u, os as _o
_sp = _u.spec_from_file_location("faim", _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "03_faim.py"))
faim = _u.module_from_spec(_sp); _sp.loader.exec_module(faim)
BEATS, T, K, CARD, END = faim.BEATS, faim.T, faim.K, faim.CARD, faim.END

SR = 48000
N = int(END * SR) + SR
rs = np.random.RandomState(21)
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


def pizz(f, d=.22):
    t = tv(d)
    return (np.sin(2 * np.pi * f * t) + .5 * np.sin(4 * np.pi * f * t) * np.exp(-t * 20)) * np.exp(-t * 16) * np.minimum(t / .002, 1)


def tuba(f, d=.2):
    t = tv(d)
    return lp(2 * ((f * t) % 1) - 1, 620) * np.minimum(t / .008, 1) * np.exp(-t * 7)


# musique : petite valse de cartoon qui s'énerve
B = 60 / 150
gulp = K["gulp"]
mel = [(0, 0), (1, 4), (2, 7), (3, 9), (4, 7), (5, 4), (6, 5), (7, 9), (8, 12), (9, 9), (10, 7), (11, 5)]
chords = [0, 0, 5, 7]
root = 130.8
i_b = 0
t0 = 0.0
beat_d = lambda t: [b["d"] for b in BEATS if b["start"] <= t][-1]
while t0 < gulp + 1.0:
    d = beat_d(t0)
    tr = min(d // 9, 9)
    rt = root * 2 ** ((tr + chords[(i_b // 3) % 4]) / 12)
    if i_b % 3 == 0:
        mus(t0, tuba(rt / 2, B * .9), -8)
    else:
        for k in (0, 4, 7):
            mus(t0, pizz(rt * 2 * 2 ** (k / 12)), -18)
    for p_, n in mel:
        if p_ == i_b % 12 and d >= 2:
            mus(t0, pizz(root * 2 * 2 ** ((n + tr) / 12), .3), -11)
    if d >= 24 and i_b % 3 == 0:
        x = tv(.2)
        mus(t0, np.sin(2 * np.pi * np.cumsum(50 + 110 * np.exp(-x * 26)) / SR) * np.exp(-x * 12), -9)
    if d >= 24:
        mus(t0, hp(noise(.03), 7000) * np.exp(-tv(.03) * 120), -30)
    i_b += 1
    t0 += B if d < 47 else B * .84
wet = np.clip((tt - T[47]) / .4, 0, 1)
MUS = MUS * (1 - wet * .75) + lp(MUS, 800) * wet * .95
MUS *= np.clip((gulp + 1.0 - tt) / .4, 0, 1)
MUS[int(K["burp"] * SR):] = 0


def crunch(t0, g=-20):
    d = .05
    add(t0, bp(noise(d), 900, 6000) * np.exp(-tv(d) * 80), g + rs.uniform(-3, 2), rs.uniform(-.2, .2))


# mastication : plus rapide et plus lourde avec les jours
t0 = 0.5
while t0 < K["burp"] - .3:
    d = beat_d(t0)
    if d <= 2 or d >= 5:
        crunch(t0, -24 + min(d, 45) * .18)
        if d >= 30:
            x = tv(.1)
            add(t0, np.sin(2 * np.pi * 80 * x) * np.exp(-x * 34), -18)
    t0 += max(.33 - min(d, 60) * .0045, .075)
# un tic à chaque nouveau jour, de plus en plus aigu
seen = set()
for b in BEATS:
    d = b["d"]
    if d in seen or d == 1:
        continue
    seen.add(d)
    k = len(seen)
    x = tv(.26)
    f = 200 * 2 ** (k / 12)
    add(b["start"], (np.sin(2 * np.pi * f * x) + .4 * np.sin(2 * np.pi * f * 3.98 * x) * np.exp(-x * 26)) * np.exp(-x * 13), -13)


def stamp(t0, g=-2):
    x = tv(.16)
    add(t0, (np.sin(2 * np.pi * np.cumsum(90 + 150 * np.exp(-x * 40)) / SR) + bp(noise(.16), 300, 2500) * 2) * np.exp(-x * 28), g)


def ching(t0, g=-9):
    x = tv(.5)
    add(t0 + .13, sum(np.sin(2 * np.pi * f * x) * np.exp(-x * a) for f, a in ((2093, 8), (2637, 8), (3136, 10), (4186, 13))) / 2, g)


for k_ in ("s_console", "s_tv", "s_couch", "s_car", "s_house", "s_eiffel", "s_france"):
    big = {"s_house": -1, "s_eiffel": -1, "s_france": 0}.get(k_, -3)
    stamp(K[k_], big)
    ching(K[k_])
    x = tv(.3)
    add(K[k_] + .62, norm(bp(noise(.36), 300, 3400)) * np.hanning(int(.36 * SR)), -14)
stamp(K["s_bank"] + .1, -2)
ching(K["s_must"] + .4, -9)
# gros coup pour la France
x = tv(1.1)
add(K["s_france"], np.sin(2 * np.pi * np.cumsum(38 + 120 * np.exp(-x * 9)) / SR) * np.exp(-x * 4), -3)
# pins
for dt in (.2, .65, 1.1):
    stamp(K["pins"] + dt, -9)
    ching(K["pins"] + dt, -16)
# ventre qui gargouille
for d_ in (10, 29):
    x = tv(1.1)
    f = 70 + 34 * np.sin(x * 14) + 22 * np.sin(x * 37)
    add(T[d_] + .15, lp(2 * (np.cumsum(f) / SR % 1) - 1, 500) * np.hanning(len(x)), -9)
# klaxon du camion
x = tv(.32)
for k in (0, .4):
    add(K["truck"] + .1 + k, (np.sign(np.sin(2 * np.pi * 330 * x)) + np.sign(np.sin(2 * np.pi * 415 * x))) * .3 * np.minimum(x / .01, 1), -14)
add(K["truck"] + .55, lp(noise(.8), 1500) * np.hanning(int(.8 * SR)), -10)


def voice(t0, base=215, n=3, g=-11):
    for k in range(n):
        x = tv(.1)
        f = base * rs.uniform(.92, 1.15) * (1 + .1 * np.sin(x * 50))
        add(t0 + k * .1, bp(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)), 350, 2500) * np.hanning(len(x)), g)


for b in BEATS:
    if b["ger"]:
        voice(b["start"] + .03, 215, min(2 + len(b["ger"]) // 5, 5))
# moustache : petit zip
x = tv(.3)
add(K["s_must"] + .55, bp(noise(.3), 2000, 8000) * (np.sin(2 * np.pi * 44 * x) > 0) * np.hanning(len(x)), -9)
# éléments avalés
x = tv(1.4)
add(T[68], norm(bp(noise(1.4), 400, 5000)) * np.hanning(len(x)), -9)
x = tv(1.6)
add(T[76], norm(lp(noise(1.6), 900)) * np.sin(x * 3) ** 2, -7)
for k in range(9):
    x = tv(.13)
    add(T[76] + .1 + k * .16, np.sin(2 * np.pi * np.cumsum(300 + 1300 * x) / SR) * np.exp(-x * 20), -15)
x = tv(1.4)
add(T[82], np.sin(2 * np.pi * np.cumsum(900 - 500 * x) / SR) * (x / 1.4), -18)
x = tv(.2)
add(T[82] + 1.45, np.sin(2 * np.pi * np.cumsum(180 + 600 * x) / SR) * np.exp(-x * 14), -6)
# la Terre : aspiration puis GLOUP
d = 2.5
x = tv(d)
add(gulp + .3, norm(bp(noise(d), 200, 3800)) * (x / d) ** 2 * np.minimum((d - x) / .03, 1), -3)
f = 90 * 2 ** (x / d * 3.2)
add(gulp + .3, np.sin(2 * np.pi * np.cumsum(f) / SR) * (x / d) ** 1.6 * np.minimum((d - x) / .03, 1), -10)
x = tv(.55)
fg = 110 + 500 * np.exp(-((x - .22) / .08) ** 2)
add(gulp + 2.72, np.tanh(2 * np.sin(2 * np.pi * np.cumsum(fg) / SR)) * np.exp(-x * 4), 0)
# rot
x = tv(.75)
f = 92 + 26 * np.sin(x * 11) - 34 * x
v = bp(2 * (np.cumsum(f) / SR % 1) - 1, 80, 1500) * (.6 + .4 * np.sin(2 * np.pi * 26 * x)) * np.minimum(x / .05, 1) * np.minimum((.75 - x) / .25, 1)
add(K["burp"] + .1, norm(v), -3)


def mrrp(t0, g=-5):
    d = .55
    x = tv(d)
    f = 340 + 370 * np.minimum(x / .34, 1) ** 1.6
    v = sum(np.sin(2 * np.pi * np.cumsum(f * k) / SR) / k for k in (1, 2, 3, 4))
    v = bp(v, 300, 3200) * (.65 + .35 * np.sin(2 * np.pi * 24 * x)) * np.hanning(len(x)) ** .6
    add(t0, norm(v), g)


mrrp(K["mrrp"] + .05)
# le regard : grave qui monte, coupe nette
d = CARD - K["stare"]
x = tv(d)
add(K["stare"], (np.sin(2 * np.pi * 55 * x) * .7 + np.sin(2 * np.pi * 110.5 * x) * .3) * (x / d) ** 1.3, -9)
i = int(CARD * SR)
FX[i:] = 0
x = tv(.5)
add(CARD + .05, np.sin(2 * np.pi * np.cumsum(46 + 60 * np.exp(-x * 10)) / SR) * np.exp(-x * 7), -6)
mrrp(CARD + 1.5, -10)

L = MUS * db2(-1) + FX[:, 0]
Rr = MUS * db2(-1) + FX[:, 1]
L, Rr = np.tanh(L * 1.6), np.tanh(Rr * 1.6)
pk = max(np.abs(L).max(), np.abs(Rr).max())
st = np.stack([L, Rr], 1)[: int(END * SR)] / pk * .89
wavfile.write("son3.wav", SR, (st * 32767).astype(np.int16))
print("pic", pk)
