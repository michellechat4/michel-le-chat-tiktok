"""Son de la vidéo 09 : marche qui accélère chaque jour, porte qui grince, pas de Gérard, bang supersonique, espace calme, pluie, « NON »."""
import numpy as np
from scipy.signal import butter, sosfilt, resample_poly
from scipy.io import wavfile
from scipy.ndimage import maximum_filter1d, uniform_filter1d
import importlib.util as _u, os as _o, sys
_sp = _u.spec_from_file_location("porte", _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "09_porte.py"))
ch = _u.module_from_spec(_sp); _sp.loader.exec_module(ch)
BEATS, K, CARD, END, DAYS = ch.BEATS, ch.K, ch.CARD, ch.END, ch.DAYS
B = {b["key"]: b for b in BEATS}

SR = 48000
N = int(END * SR) + SR
rs = np.random.RandomState(49)
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



def creak(t0, g=-14):
    d = .45
    x = tv(d)
    f = 520 + 260 * np.sin(np.pi * x / d)
    v = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * (.5 + .5 * np.sin(2 * np.pi * 37 * x))
    add(t0, bp(v, 600, 3000) * np.hanning(len(x)), g, .5)


def clack(t0, g=-8):
    thud(t0, 80, .25, g)
    add(t0, hp(noise(.03), 2000) * np.exp(-tv(.03) * 120), g - 4, .5)


def step(t0, g=-20, pan=0.0):
    x = tv(.08)
    add(t0, lp(noise(.08), 900) * np.exp(-x * 50), g, pan)


def day_at(t):
    return max([b["n1"] for b in BEATS if b["start"] <= t] + [0])


# ---- musique : petite marche, plus rapide et plus haute chaque jour ; pause dans l'espace et au mur du son
mel = [0, 4, 7, 4, 9, 7, 4, None, 2, 5, 9, 5, 7, None, 4, None]
bas = [0, 5, 7, 5]
SPACE0, SPACE1 = K["j18"], K["pluie"]
ZONES = [(0, K["j18"]), (K["pluie"], CARD)]
for z0, z1 in ZONES:
    t0, i = z0, 0
    while t0 < z1:
        n = day_at(t0)
        root = 110.0 * 2 ** (min(n, 16) / 2 / 12)
        if z0 == K["pluie"]:
            root = 98.0
        if i % 2 == 0:
            mus(t0, tuba(root * 2 ** (bas[(i // 2) % 4] / 12), .28), -7)
        m = mel[i % len(mel)]
        if m is not None:
            mus(t0, mallet(root * 4 * 2 ** (m / 12)), -12)
        if i % 4 == 2:
            mus(t0, hp(noise(.04), 6000) * np.exp(-tv(.04) * 90), -27)
        i += 1
        bpm = 112 + 4 * min(n, 16) if z0 == 0 else 96
        t0 += 60 / bpm / 2
    fade = int(.25 * SR)
    s1 = int(z1 * SR)
    MUS[s1 - fade:s1] *= np.linspace(1, 0, fade)
    MUS[s1:int((ZONES[1][0] if z0 == 0 else END) * SR)] = 0
# espace et mur du son : nappe douce
d = SPACE1 - SPACE0
x = tv(d)
pad = sum(np.sin(2 * np.pi * f * x) for f in (220, 277.2, 329.6, 440)) * (.6 + .4 * np.sin(2 * np.pi * .25 * x))
pad *= np.minimum(x / .8, 1) * np.minimum((d - x) / .4, 1)
mus(SPACE0, lp(pad, 2000) * .25, -8)
for k, f in enumerate((880, 1109, 1319, 1109, 988, 1319, 1760, 1319) * 3):
    tk = SPACE0 + .3 + k * .9
    if tk < SPACE1 - .3 and not (K["mach"] <= tk < K["j21"]):
        mus(tk, mallet(f, .6), -20)
i0, i1 = int(K["mach"] * SR), int(K["j21"] * SR)
MUS[i0:i1] *= .35

# ---- chaque nouveau jour : petit « ding » qui monte
for n, j in enumerate(DAYS):
    ding(j, 880 * 1.06 ** n, -13, .4)
    whoosh(j, .35, -20, 800, 6000)

# ---- porte : cycles (mêmes formules que l'image)
def cycles(key, per, off, single=False, g_door=0.0):
    b = B[key]
    k = 0
    while True:
        s = b["start"] + off + k * per
        if s + per * .78 > b["start"] + b["dur"]:
            break
        creak(s + per * .22, -14 + g_door)
        clack(s + per * .78, -10 + g_door)
        nst = max(2, int(per * .22 / .16))
        for j in range(nst):
            step(s + j * per * .22 / nst, -21, -.2)
            step(s + per * .78 + j * per * .22 / nst, -21, -.2)
        if single:
            break
        k += 1


cycles("regle", 3.2, .2, True)
cycles("j1", 3.2, .2, True)
cycles("j5", 1.5, .1)
cycles("j10", 1.4, 0)
b = B["j13"]
x = tv(b["dur"])
add(b["start"], bp(noise(b["dur"]), 300, 2500) * (.5 + .5 * np.sign(np.sin(2 * np.pi * x / .42))) * np.minimum(x / .2, 1), -20)
for k in range(int(b["dur"] / .21)):
    clack(b["start"] + k * .21, -16)

# ---- voix
for b in BEATS:
    if b["ger"]:
        t0 = b["start"] + .38 + (1.4 if b["key"] == "chat" else 1.2 if b["key"] == "fin" else 0)
        voice(t0, 215, min(2 + len(b["ger"]) // 5, 5), -10)
mrrp(K["hook"] + .9, -6)
mrrp(K["regle2"] + 1.2, -9, 200)
mrrp(K["chat2"] + 1.0, -7, 300)
mrrp(K["fin"] + 1.2, -6, 380)
mrrp(K["pluie"] + 1.8, -9, -120)
# hésitation : pied qui tape
for k in range(9):
    add(K["hesite"] + .6 + k * .3, lp(noise(.05), 1200) * np.exp(-tv(.05) * 60), -14, -.3)
# marathon : foule
d = 2.4
x = tv(d)
add(K["j8"] + 1.6, bp(noise(d), 400, 3000) * np.hanning(len(x)) * (.7 + .3 * np.sin(2 * np.pi * 3 * x)), -14)
for k in range(4):
    ding(K["j8"] + 1.8 + k * .14, 1047 * 2 ** (k * 4 / 12), -16, .4)
# Tour : sonnette de vélo
for k in range(2):
    ding(K["j14"] + 1.5 + k * .18, 2300, -15, .3)
    ding(K["j14"] + 1.5 + k * .18, 2900, -18, .3)
# TGV : grondement + klaxon
d = B["j16"]["dur"]
x = tv(d)
add(K["j16"], lp(noise(d), 500) * np.minimum(x / .6, 1) * np.minimum((d - x) / .3, 1), -9)
for f in (440, 554):
    xx = tv(.7)
    add(K["j16"] + 1.3, lp(np.sign(np.sin(2 * np.pi * f * xx)), 2000) * np.minimum(xx / .03, 1) * np.minimum((.7 - xx) / .1, 1), -22)
# tour de la Terre : petits pas + fanfare
for k in range(20):
    step(K["j18"] + .25 + k * .13, -24)
for k, f in enumerate((523, 659, 784, 1047)):
    ding(K["j18"] + 2.0 + k * .1, f, -13, .6)
# mur du son
b = B["mach"]
x = tv(b["dur"])
add(b["start"], bp(noise(b["dur"]), 200, 3000) * np.minimum(x / .4, 1) * np.minimum((b["dur"] - x) / .3, 1), -16)
x = tv(1.2)
add(K["mach"] + .55, np.sin(2 * np.pi * np.cumsum(38 + 80 * np.exp(-x * 7)) / SR) * np.exp(-x * 4), 0)
add(K["mach"] + .55, lp(noise(1.2), 2500) * np.exp(-x * 6), -4)
add(K["mach"] + .62, lp(noise(.8), 1800) * np.exp(-tv(.8) * 7), -8)
# Lune : pas lointains + « ?! »
for k in range(14):
    step(K["j21"] + .3 + k * .17, -26)
ding(K["j21"] + 2.7, 1568, -14, .3)
ding(K["j21"] + 2.82, 1976, -14, .4)
# pluie
d = K["fin"] + B["fin"]["dur"] - K["pluie"]
x = tv(d)
rain = hp(noise(d), 1500) * .5 + lp(noise(d), 600) * .3
env = np.where(x < 3.4, np.minimum(x / .8, 1), .35)
add(K["pluie"], rain * env, -17)
creak(K["pluie"] + .2, -12)
clack(K["fin"] + .1, -8)
# chatière : marteau + étincelles
for k in range(4):
    add(K["chat"] + .2 + k * .28, lp(noise(.06), 2500) * np.exp(-tv(.06) * 50), -8, .4)
for k in range(5):
    ding(K["chat"] + 1.25 + k * .08, 1760 + k * 220, -18, .3)
add(K["chat2"] + 1.6, np.sin(2 * np.pi * 300 * tv(.3)) * np.exp(-tv(.3) * 12), -16)
# carton
i = int(CARD * SR)
FX[i:] = 0
MUS[i:] = 0
x = tv(.6)
add(CARD + .05, np.sin(2 * np.pi * np.cumsum(40 + 70 * np.exp(-x * 9)) / SR) * np.exp(-x * 6), -3)
creak(CARD + 1.4, -14)

L = MUS * db2(-1) + FX[:, 0]
Rr = MUS * db2(-1) + FX[:, 1]
L, Rr = np.tanh(L * 1.6), np.tanh(Rr * 1.6)
pk = max(np.abs(L).max(), np.abs(Rr).max())
st = np.stack([L, Rr], 1)[: int(END * SR)] / pk * .89
MASTER_DB = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
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
wavfile.write("son9.wav", SR, (np.clip(st, -1, 1) * 32767).astype(np.int16))
print("pic", pk, "crête vraie dB", 20 * np.log10(tp), "durée", END)
