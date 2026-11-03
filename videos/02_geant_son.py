import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
from geant import BEATS, T, PH, CARD, END, Lm

SR = 48000
N = int(END * SR) + SR
rs = np.random.RandomState(11)
tt = np.arange(N) / SR
MUS = np.zeros(N, np.float32)
FX = np.zeros((N, 2), np.float32)


def db2(x):
    return 10 ** (x / 20)


def bp(x, lo, hi, o=2):
    return sosfilt(butter(o, [lo, hi], "band", fs=SR, output="sos"), x)


def lp(x, f, o=2):
    return sosfilt(butter(o, f, "low", fs=SR, output="sos"), x)


def hp(x, f, o=2):
    return sosfilt(butter(o, f, "high", fs=SR, output="sos"), x)


def tv(d):
    return np.arange(int(d * SR)) / SR


def noise(d):
    return rs.randn(int(d * SR)).astype(np.float32)


def norm(x):
    return x / (np.max(np.abs(x)) + 1e-9)


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
    return (np.sin(2 * np.pi * f * t) + .5 * np.sin(4 * np.pi * f * t) * np.exp(-t * 20) + .25 * np.sin(6 * np.pi * f * t) * np.exp(-t * 34)) * np.exp(-t * 16) * np.minimum(t / .002, 1)


def tuba(f, d=.2):
    t = tv(d)
    x = 2 * ((f * t) % 1) - 1
    return lp(x, 620) * np.minimum(t / .008, 1) * np.exp(-t * 7)


# ---------------------------------------------------------- musique : marche de cartoon
B = 60 / 132 / 2     # croche
SC = [0, 3, 5, 7, 10]
melody = [(0, 0), (2, 3), (3, 5), (4, 7), (6, 5), (7, 3), (8, 7), (10, 10), (11, 12), (12, 10), (14, 7), (15, 5),
          (16, 0), (18, 3), (19, 5), (20, 7), (22, 8), (23, 7), (24, 5), (26, 3), (28, 2), (30, -1)]
harm = [0, 0, 0, 0, 5, 5, 7, 7]  # par demi-mesure de 4 croches
root = 110.0
end_music = PH["table"]
i_step = 0
t0 = 0.0
day_of = lambda t: max([b["d"] for b in BEATS if b["start"] <= t] or [1])
while t0 < end_music - .02:
    d = day_of(t0)
    tr = (d - 1) // 5          # monte d'un demi-ton tous les 5 jours
    st = i_step % 32
    rt = root * 2 ** ((tr + harm[(st // 4) % 8]) / 12)
    if st % 2 == 0:
        if st % 4 == 0:
            mus(t0, tuba(rt / 2, B * 1.8), -8)
        else:
            mus(t0, tuba(rt / 2 * 1.5, B * 1.8), -10)
    if st % 4 == 2:
        for k in (0, 3, 7):
            mus(t0, pizz(rt * 2 * 2 ** (k / 12)), -17)
    for pos, nt in melody:
        if pos == st and d >= 2:
            mus(t0, pizz(root * 2 * 2 ** ((nt + tr) / 12), .3), -11)
    if d >= 13 and st % 2 == 1:  # charleston
        mus(t0, hp(noise(.03), 7000) * np.exp(-tv(.03) * 120), -28)
    if d >= 19 and st % 8 == 0:
        tk = tv(.22)
        mus(t0, np.sin(2 * np.pi * np.cumsum(55 + 120 * np.exp(-tk * 28)) / SR) * np.exp(-tk * 12), -10)
    i_step += 1
    t0 += B
# fin nette de la musique, étouffée dans l'espace
wet = np.clip((tt - T[19]) / .4, 0, 1)
MUS = MUS * (1 - wet * .75) + lp(MUS, 700) * wet * .95
MUS[int(end_music * SR):] = 0

# ---------------------------------------------------------- à chaque jour : le chat grandit
for d in range(2, 32):
    tb = T[d]
    x = tv(.24)
    f = 170 * 2 ** ((d - 1) / 14) * (1 + 1.0 * np.minimum(x / .12, 1))
    bo = np.sin(2 * np.pi * np.cumsum(f * (1 + .03 * np.sin(x * 70))) / SR) * np.exp(-x * 9) * np.minimum(x / .004, 1)
    add(tb, bo, -11)
    if d >= 4:
        wh = bp(noise(.3), 300, 4200) * np.hanning(int(.3 * SR))
        add(tb - .05, norm(wh), -19)
    if d >= 3:
        x = tv(.3)
        th = np.sin(2 * np.pi * np.cumsum(40 + 110 * np.exp(-x * 14)) / SR) * np.exp(-x * 10)
        add(tb, th, -11 + min(d, 25) * .12)


def knock(t0, g=-6, f=190):
    t = tv(.14)
    add(t0, (np.sin(2 * np.pi * f * t) * .9 + bp(noise(.14), 500, 2600) * 3) * np.exp(-t * 42), g)


def voice(t0, base=210, n=3, g=-11):
    for k in range(n):
        d_ = .1
        t = tv(d_)
        f = base * rs.uniform(.92, 1.15) * (1 + .1 * np.sin(t * 50))
        v = bp(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)), 350, 2500) * np.hanning(len(t))
        add(t0 + k * .1, v, g)


for b in BEATS:
    if b["ger"]:
        n_ = 2 + len(b["ger"]) // 5
        voice(b["start"] + .03, 215, min(n_, 5))

# plâtre, toit
add(T[4], hp(noise(.7), 800) * np.exp(-tv(.7) * 7), -10)
for k in range(30):
    add(T[4] + rs.uniform(0, .7), bp(noise(.05), 800, 5000) * np.exp(-tv(.05) * 60), rs.uniform(-24, -13), rs.uniform(-.6, .6))
x = tv(.45)
add(T[5], bp(2 * ((70 * x + 40 * x * x * 20) % 1) - 1, 200, 2000) * np.exp(-x * 5), -7)
add(T[5] + .05, norm(bp(noise(.8), 300, 3000)) * np.hanning(int(.8 * SR)), -11)
# téléphone
for tb, nb in ((T[6] + .2, 2), (T[9] + .15, 3)):
    for k in range(nb):
        x = tv(.22)
        add(tb + k * .33, (np.sin(2 * np.pi * 950 * x) + np.sin(2 * np.pi * 1200 * x)) * .5 * (np.sin(2 * np.pi * 24 * x) > 0), -19)
# plouf gamelle
x = tv(.35)
add(T[8] + .15, np.sin(2 * np.pi * np.cumsum(300 + 900 * x) / SR) * np.exp(-x * 11), -14)
add(T[8] + .15, hp(noise(.35), 1500) * np.exp(-x * 9), -15)
# pelleteuse
x = tv(1.2)
add(T[10] + .1, np.tanh(3 * (2 * ((58 * x) % 1) - 1)) * lp(np.abs(np.sin(x * 40)), 300) * np.minimum((1.2 - x) / .1, 1), -19)
for k in range(44):
    add(T[10] + .55 + rs.uniform(0, .7), bp(noise(.02), 1200, 6000), rs.uniform(-26, -15))
# griffes
x = tv(1.55)
sc = bp(noise(1.55), 1200, 7500) * (np.sin(2 * np.pi * 7.6 * x) > 0)
add(T[11] + .15, sc, -8)
x = tv(1.4)
f = 90 + 70 * np.sin(x * 4) + 12 * np.sin(x * 55)
add(T[11] + .3, bp(2 * (np.cumsum(f) / SR % 1) - 1, 200, 2500) * np.hanning(len(x)), -15)
# vent
add(T[13], norm(bp(noise(1.1), 200, 1600)) * np.hanning(int(1.1 * SR)), -13)
# avion + bonk
x = tv(.62)
add(T[16], norm(bp(noise(.62), 500, 4500)) * (x / .62), -9)
tb = T[16] + .62
x = tv(.35)
add(tb, np.sin(2 * np.pi * np.cumsum(620 - 900 * x) / SR) * np.exp(-x * 9), -3)
knock(tb, -5, 140)
x = tv(.7)
add(tb + .05, np.sin(2 * np.pi * np.cumsum(1400 - 1500 * x) / SR) * np.minimum((.7 - x) / .1, 1), -21)
# ISS : coups de patte
for k in (.5, .85, 1.2):
    add(T[21] + k, norm(bp(noise(.16), 700, 5000)) * np.hanning(int(.16 * SR)), -11)
# coussin, litière
x = tv(.3)
add(T[23] + .05, lp(noise(.3), 500) * np.exp(-x * 12), -6)
add(T[24] + .2, hp(noise(1.0), 3000) * np.hanning(int(1.0 * SR)), -15)
# taille de la Terre : coup de cloche grave
x = tv(1.7)
add(T[26], sum(np.sin(2 * np.pi * f * x) * np.exp(-x * a) for f, a in ((110, 2), (221, 3), (331, 4), (523, 6))) / 2, -7)
# masse : grave qui gonfle
x = tv(2.0)
add(T[28], np.sin(2 * np.pi * 52 * x) * np.hanning(len(x)), -7)
add(T[28], np.sin(2 * np.pi * np.cumsum(180 + 160 * x) / SR) * np.hanning(len(x)), -18)
# pelote
for k in range(4):
    x = tv(.2)
    add(T[29] + .08 + k * .33, np.sin(2 * np.pi * np.cumsum(220 + 700 * x) / SR) * np.exp(-x * 14), -12)
# croquettes
for k in range(55):
    add(T[30] + rs.uniform(.05, 1.5), bp(noise(.015), 1500, 7000), rs.uniform(-29, -17), rs.uniform(-.5, .5))

# ---------------------------------------------------------- final
tb = PH["table"]
knock(tb + .62, 0, 75)
knock(tb + .72, -12, 75)
# ronron très doux pendant le regard
x = tv(CARD - PH["stare"])
ph = np.cumsum(26 + 1.5 * np.sin(2 * np.pi * x / 2.3)) / SR
pulse = np.clip(np.sin(2 * np.pi * ph), 0, 1) ** 3
pur = norm(bp(rs.randn(len(x)).astype(np.float32), 120, 1400) * pulse + bp((ph % 1) * pulse, 50, 700) * .8)
add(PH["stare"], pur * np.minimum(x / .4, 1), -21)
# bois qui frotte
def scrape(t0, d, g=-11):
    x = tv(d)
    s = bp(noise(d), 180, 1500) * (.6 + .4 * np.sin(2 * np.pi * 18 * x)) * np.minimum(x / .05, 1) * np.minimum((d - x) / .05, 1)
    add(t0, norm(s), g)
pm, pf = PH["pushm"], PH["fall"]
scrape(pm + .5, pf - pm - .5)
# la Lune tombe : sifflet puis... tac.
x = tv(.72)
add(pf, np.sin(2 * np.pi * np.cumsum(1500 - 1500 * x) / SR) * np.minimum(x / .02, 1) * np.minimum((.72 - x) / .02, 1), -18)
knock(pf + .74, -11, 310)
pe = PH["pushe"]
scrape(pe + .35, CARD - pe - .35)
# coupe nette au noir
i = int(CARD * SR)
FX[i:] = 0
# dans le noir : sifflet long, puis un tout petit « tac », puis Michel
x = tv(.9)
add(CARD + .2, np.sin(2 * np.pi * np.cumsum(1300 - 1100 * x) / SR) * np.minimum(x / .02, 1) * np.minimum((.9 - x) / .02, 1), -20)
knock(CARD + 1.14, -7, 240)
d = .55
x = tv(d)
f = 340 + 370 * np.minimum(x / .34, 1) ** 1.6
v = sum(np.sin(2 * np.pi * np.cumsum(f * k) / SR) / k for k in (1, 2, 3, 4))
v = bp(v, 300, 3200) * (.65 + .35 * np.sin(2 * np.pi * 24 * x)) * np.hanning(len(x)) ** .6
add(CARD + 1.65, norm(v), -9)

# ---------------------------------------------------------- master
L = MUS * db2(-1) + FX[:, 0]
Rr = MUS * db2(-1) + FX[:, 1]
L, Rr = np.tanh(L * 1.7), np.tanh(Rr * 1.7)
pk = max(np.abs(L).max(), np.abs(Rr).max())
SCALE = 0.75
st = np.stack([L, Rr], 1)[: int(END * SR)] / pk * SCALE
wavfile.write("son2.wav", SR, (st * 32767).astype(np.int16))
print("pic", pk)
for b in BEATS[::4]:
    a, e = int(b["start"] * SR), int((b["start"] + b["dur"]) * SR)
    print("%5.1fs J%-2d rms %.1f" % (b["start"], b["d"], 20 * np.log10(np.sqrt(np.mean(st[a:e] ** 2)) + 1e-9)))
