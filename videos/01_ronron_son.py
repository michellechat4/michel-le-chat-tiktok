import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
from tl import *

SR = 48000
N = int(END * SR) + SR
rs = np.random.RandomState(7)
tt = np.arange(N) / SR
L = np.zeros(N, np.float32)
R = np.zeros(N, np.float32)


def db2(x):
    return 10 ** (x / 20)


def bp(x, lo, hi, o=2):
    return sosfilt(butter(o, [lo, hi], "band", fs=SR, output="sos"), x)


def lp(x, f, o=2):
    return sosfilt(butter(o, f, "low", fs=SR, output="sos"), x)


def hp(x, f, o=2):
    return sosfilt(butter(o, f, "high", fs=SR, output="sos"), x)


def add(t0, x, gain=0.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N or i < 0:
        return
    x = x[: N - i] * db2(gain)
    L[i:i + len(x)] += x * (1 - max(pan, 0))
    R[i:i + len(x)] += x * (1 + min(pan, 0))


def noise(d):
    return rs.randn(int(d * SR)).astype(np.float32)


def tvec(d):
    return np.arange(int(d * SR)) / SR


def env(d, a=.005, r=.1):
    t = tvec(d)
    e = np.minimum(t / a, 1) * np.minimum((d - t) / r, 1)
    return np.clip(e, 0, 1)


def saw(f, t):
    ph = np.cumsum(np.full_like(t, 1) * f) / SR if np.isscalar(f) else np.cumsum(f) / SR
    return 2 * (ph % 1) - 1


def norm(x):
    return x / (np.max(np.abs(x)) + 1e-9)


# ------------------------------------------------------------ ronron
def purr():
    breath = 0.5 + 0.5 * np.sin(2 * np.pi * tt / 2.3)
    rate = 25 + 2.2 * breath
    ph = np.cumsum(rate) / SR
    pulse = np.clip(np.sin(2 * np.pi * ph), 0, 1) ** 3
    nz = rs.randn(N).astype(np.float32)
    grit = bp(nz, 120, 1500) * pulse
    body = bp(((ph % 1) * 2 - 1) * pulse, 50, 700)
    x = norm(grit) * .75 + norm(body) * .9
    return x * (0.72 + .28 * breath)


pur = purr()
# niveaux par temps fort
g = np.zeros(N)
drive = np.ones(N)
space = np.zeros(N)
for b in BEATS:
    i0, i1 = int(b["start"] * SR), int((b["start"] + b["dur"]) * SR)
    n = b["n"]
    g[i0:i1] = -18 + min(n, 14) * 1.05 + max(n - 14, 0) * .1
    drive[i0:i1] = 1 + n * .22
i_sil = int((T41 - .55) * SR)
g[i_sil:int(E0 * SR)] = -120
g[int(E0 * SR):] = -18
drive[int(E0 * SR):] = 1
g = lp(g, 30, 1)
drive = lp(drive, 20, 1)
sig = np.tanh(pur * drive * 1.6) / np.tanh(drive * 1.6)
# étouffé dans l'espace
sp_lp = lp(sig, 520, 2)
sw = np.clip((tt - T[28]) / .3, 0, 1) * (tt < E0)
sig = sig * (1 - sw) + sp_lp * 1.6 * sw
out = sig * 10 ** (g / 20)
# sub qui monte (téléphones : surtout harmonique)
sub = lp(rs.randn(N).astype(np.float32), 90, 2)
sub = norm(sub) * np.clip((tt - T[14]) / (T41 - T[14]), 0, 1) ** 1.2 * (tt < T41 - .55) * db2(-16)
L += out + sub
R += out + sub

# ------------------------------------------------------------ note à chaque caresse
for n in range(1, 42):
    if n == 41:
        continue
    f = 220 * 2 ** ((n - 1) / 12)
    t = tvec(.3)
    x = (np.sin(2 * np.pi * f * t) + .45 * np.sin(2 * np.pi * f * 3.98 * t) * np.exp(-t * 28)) * np.exp(-t * 12)
    add(T[n], x, -13 + min(n, 20) * .18)
    sw_ = bp(noise(.22), 1500, 6000) * np.hanning(int(.22 * SR))
    add(T[n] - .18, sw_, -30 + min(n, 14) * .8)
    if n >= 9:
        d = .28
        t = tvec(d)
        fr = 130 * np.exp(-t * 11) + 40
        th = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 11)
        add(T[n], th, -14 + min(n, 30) * .3)


def boom(t0, d=2.0, gain=-3, low=45, bright=2500):
    t = tvec(d)
    fr = low * 3 * np.exp(-t * 9) + low
    a = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 3.2 / d)
    b = lp(noise(d), bright) * np.exp(-t * 7 / d)
    add(t0, np.tanh(norm(a) * 1.3 + norm(b) * 1.2), gain)


def whoosh(t0, d=.5, gain=-10, lo=300, hi=5000):
    x = bp(noise(d), lo, hi) * np.hanning(int(d * SR))
    add(t0, norm(x), gain)


def knock(t0, gain=-5, f=190):
    t = tvec(.14)
    x = (np.sin(2 * np.pi * f * t) * .9 + bp(noise(.14), 500, 2600) * 3) * np.exp(-t * 42)
    add(t0, x, gain)


def layer(t0, x, gain, fade=.06):
    n_ = len(x)
    e = np.minimum(np.arange(n_) / (fade * SR), 1) * np.minimum((n_ - np.arange(n_)) / (fade * SR), 1)
    add(t0, x * e, gain)


# ------------------------------------------------------------ objets comparés
d = BEATS[[i for i, b in enumerate(BEATS) if b["n"] == 2][0]]["dur"]
t = tvec(d)
layer(T[2], sum(np.sin(2 * np.pi * f * t) / (k + 1) for k, f in enumerate((100, 200, 300, 400))), -24)
d = 0.9
layer(T[5], norm(bp(noise(d), 700, 5500)) + .25 * np.sin(2 * np.pi * 880 * tvec(d)), -17)
for dt in (.1, .45, .8):
    knock(T[6] + dt, -4)
d = 1.1
t = tvec(d)
f = 55 + 35 * np.minimum(t / .4, 1) + 15 * np.sin(t * 16)
layer(T[7], np.tanh(saw(f, t) * 3) * (.65 + .35 * np.sign(np.sin(2 * np.pi * f * t / 2))), -15)
d = 0.95
beat = 60 / 128
for k in range(3):
    tk = tvec(.2)
    add(T[8] + k * beat * .92, np.sin(2 * np.pi * np.cumsum(55 + 170 * np.exp(-tk * 30)) / SR) * np.exp(-tk * 13), -5)
    add(T[8] + k * beat * .92 + beat * .46, hp(noise(.05), 7000) * np.exp(-tvec(.05) * 70), -19)
d = .95
t = tvec(d)
f = 115 + 45 * np.sin(t * 7) ** 2
layer(T[9], np.tanh(saw(f, t) * 5) * .75 + .3 * norm(bp(noise(d), 1500, 7000)), -13)
t = tvec(1.2)
layer(T[10], np.sin(2 * np.pi * 6200 * t), -32)
d = 1.1
t = tvec(d)
x = np.zeros(int(d * SR))
nz = noise(d)
layer(T[12], norm(lp(nz, 900)) * (t / d) + norm(bp(noise(d), 1200, 5500)) * .55 * (t / d), -5)

# ------------------------------------------------------------ verre
for k in range(150):
    t0 = T[13] + rs.exponential(.17)
    f = rs.uniform(2200, 9500)
    d_ = rs.uniform(.03, .25)
    t = tvec(d_)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * rs.uniform(25, 60))
    add(t0, x, rs.uniform(-23, -11), rs.uniform(-.7, .7))
crash = hp(noise(.9), 2500) * np.exp(-tvec(.9) * 6)
add(T[13], crash, -5)
boom(T[13], 1.0, -7, 60, 3000)

# ------------------------------------------------------------ rue
whoosh(T[14] - .15, .35, -7)
for k, (f1, f2, r_, p_) in enumerate(((900, 1250, 5.5, -.6), (760, 1100, 7.1, .6), (1050, 620, 3.9, 0))):
    d = 1.2
    t = tvec(d)
    fq = np.where(np.sin(2 * np.pi * r_ * t) > 0, f1, f2)
    layer(T[14], np.sign(np.sin(2 * np.pi * np.cumsum(fq) / SR)) * .5, -23, )
boom(T[15], 1.2, -4, 38, 1500)
whoosh(T[16], 1.2, -7, 150, 2500)
for k in range(4):
    knock(T[16] + .1 + k * .22, -7, 120)
boom(T[17], 1.9, -1, 34, 4000)
whoosh(T[17] - .1, .6, -5, 400, 8000)

# ------------------------------------------------------------ Paris
whoosh(T[18] - .15, .35, -7)
for k in range(4):   # râleurs : petits « blabla » qui grognent
    t0 = T[19] + k * .16
    d = .28
    t = tvec(d)
    f = rs.uniform(170, 260) * (1 + .12 * np.sin(t * 60))
    v = bp(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)), 300, 2400) * np.hanning(len(t))
    add(t0, v, -7, rs.uniform(-.5, .5))
d = 1.1
t = tvec(d)
f = 150 + 60 * np.sin(t * 5) + 18 * np.sin(t * 90)
layer(T[20], bp(saw(f, t), 300, 3000), -9)
d = 1.2
t = tvec(d)
layer(T[21], norm(bp(noise(d), 200, 3500)) * (1 - t / d * .3), -5)
t = tvec(d)
f = 200 + 1400 * (t / d) ** 2
layer(T[21], np.sin(2 * np.pi * np.cumsum(f) / SR), -15)
boom(T[22], 2.2, 0, 32, 3000)

# ------------------------------------------------------------ Terre
for n_ in (23, 24, 25):
    whoosh(T[n_] - .1, .4, -6, 200, 4000)
boom(T[26], 1.5, -3, 36, 1200)
d = 1.6
t = tvec(d)
layer(T[28], np.sin(2 * np.pi * 90 * t) * .2, -20)
for dt in (.25, .65):
    knock(T[29] + dt, -2, 95)
d = 1.5
t = tvec(d)
layer(T[30], norm(lp(noise(d), 600)) * (.65 + .35 * np.sin(t * 9)), -8)
for ti in np.linspace(T[32], T[32] + 1.55, 14):
    boom(ti, .45, -9, 45, 1000)
d = 1.2
t = tvec(d)
layer(T[34], norm(bp(noise(d), 500, 6500)) * (.4 + .6 * t / d), -6)
d = 1.5
t = tvec(d)
ch = sum(np.sin(2 * np.pi * f * (1 + .002 * np.sin(t * 5 + f)) * t) for f in (220, 277.2, 329.6, 440, 554.4, 659.3))
layer(T[35], norm(ch) * np.minimum(t / .25, 1), -8, .1)
d = 1.3
layer(T[36], norm(hp(noise(d), 2500)) * np.hanning(int(d * SR)), -8)

# montée finale
d = T41 - .55 - T[37]
t = tvec(d)
f = 90 * 2 ** (t / d * 4.5)
rise = np.sin(2 * np.pi * np.cumsum(f) / SR) + np.tanh(saw(f * 1.5, t) * 2) * .35
nz = norm(bp(noise(d), 300, 7000))
add(T[37], (rise * .6 + nz * .6) * (t / d) ** 1.4 * np.minimum((d - t) / .01, 1), -3)

# ------------------------------------------------------------ BOUM
d = 5.0
t = tvec(d)
fr = 26 + 110 * np.exp(-t * 3.2)
a = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * .9)
nzl = noise(d)
cut = lp(nzl, 5000) * np.exp(-t * 3.5) + lp(noise(d), 700) * np.exp(-t * .8) * 1.1
x = np.tanh((norm(a) * 1.3 + norm(cut) * 1.3) * 1.8)
add(T41, x, 0)
for k in range(90):   # débris
    t0 = T41 + rs.uniform(.15, 3.6)
    add(t0, hp(noise(.03), 1500) * np.exp(-tvec(.03) * 120), rs.uniform(-30, -15), rs.uniform(-.8, .8))

# ------------------------------------------------------------ fin
def mrrp(t0, gain=-5):
    d = .55
    t = tvec(d)
    f = 340 + 370 * np.minimum(t / .34, 1) ** 1.6
    trem = .65 + .35 * np.sin(2 * np.pi * 24 * t)
    v = sum(np.sin(2 * np.pi * np.cumsum(f * k) / SR) / k for k in (1, 2, 3, 4))
    v = bp(v, 300, 3200) * trem * np.hanning(len(t)) ** .6
    add(t0, norm(v), gain)


mrrp(E0 + 1.95)
d = .32
t = tvec(d)
v = bp(np.sign(np.sin(2 * np.pi * np.cumsum(330 - 90 * t / d) / SR)), 300, 2200) * np.hanning(len(t))
add(E0 + 3.92, v, -8)              # « Non. » du Soleil
whoosh(E0 + 3.5, .4, -14, 400, 3000)
whoosh(E0 + 5.15, .33, -10, 400, 5000)
# coupe nette au noir
i = int(CARD * SR)
L[i:] = 0
R[i:] = 0
knock(CARD + .08, -2, 70)
boom(CARD + .1, .8, -9, 40, 500)

# ------------------------------------------------------------ master
ge = np.interp(tt, [0, T[13], T[15], T41 - .6, T41 - .01, T41, E0, E0 + .2], [.72, .72, .42, .42, .42, .85, .85, .72])
L = np.tanh(L * ge)
R = np.tanh(R * ge)
pk = max(np.abs(L).max(), np.abs(R).max())
L, R = L / pk * .74, R / pk * .74
n_end = int(END * SR)
st = np.stack([L[:n_end], R[:n_end]], 1)
wavfile.write("son.wav", SR, (st * 32767).astype(np.int16))
print("ok", st.shape, "pic", pk)
for b_ in BEATS[::3]:
    i0, i1 = int(b_["start"] * SR), int((b_["start"] + b_["dur"]) * SR)
    rms = np.sqrt(np.mean(st[i0:i1] ** 2))
    print("%5.1fs n=%2d rms %.1f dBFS" % (b_["start"], b_["n"], 20 * np.log10(rms + 1e-9)))
