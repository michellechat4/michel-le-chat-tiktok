"""Son de la vidéo 17 : thème sautillant (salon), nappe spatiale (voyage, Mars), fusée en carton, décollage,
grelottement, rebonds en basse gravité, griffures, fanfare impériale, radio, horloge, buzzer, « tap » sur Phobos, « NON. »"""
import numpy as np
from scipy.signal import butter, sosfilt, resample_poly
from scipy.io import wavfile
from scipy.ndimage import maximum_filter1d, uniform_filter1d
import importlib.util as _u, os as _o, sys
_sp = _u.spec_from_file_location("mars", _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "17_mars.py"))
ch = _u.module_from_spec(_sp); _sp.loader.exec_module(ch)
BEATS, K, CARD, END, JUMPS = ch.BEATS, ch.K, ch.CARD, ch.END, ch.JUMPS
ch = _u.module_from_spec(_sp); _sp.loader.exec_module(ch)
BEATS, K, CARD, END, JUMPS = ch.BEATS, ch.K, ch.CARD, ch.END, ch.JUMPS

SR = 48000
N = int(END * SR) + SR
rs = np.random.RandomState(17)
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


def pad(t0, t1, chord, g):
    d = t1 - t0
    x = tv(d)
    v = sum(np.sin(2 * np.pi * f * x + .3 * np.sin(2 * np.pi * .2 * x)) for f in chord)
    mus(t0, lp(v, 1800) * np.minimum(x / .6, 1) * np.minimum((d - x) / .3, 1) * .3, g)



def arp(a, z, g=-19, notes=(880, 1108.7, 1318.5, 1760, 1318.5, 1108.7), step=.3):
    tt, k = a + .2, 0
    while tt < z - .3:
        mus(tt, mallet(notes[k % len(notes)], .6), g)
        tt += step
        k += 1


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


def tick(t0, g=-19):
    add(t0, bp(noise(.03), 2000, 5000) * np.exp(-tv(.03) * 150), g)


def static(a, d, g=-24):
    x = tv(d)
    add(a, bp(noise(d), 1500, 6000) * (0.6 + .4 * np.sin(2 * np.pi * 7 * x)) * np.minimum(x / .05, 1) * np.minimum((d - x) / .05, 1), g)


def bleep(t0, f=1500, g=-18, d=.09):
    x = tv(d)
    add(t0, np.sign(np.sin(2 * np.pi * f * x)) * np.minimum(x / .005, 1) * np.minimum((d - x) / .005, 1) * .4, g)


def fanfare(t0, root=523.25, g=-12):
    for k, (st, du) in enumerate(((0, .15), (0, .15), (7, .15), (12, .5))):
        x = tv(du + .2)
        f = root * 2 ** (st / 12)
        v = sum(np.sin(2 * np.pi * f * h * x) / h for h in (1, 2, 3, 4, 5)) * np.exp(-np.maximum(x - du, 0) * 12) * np.minimum(x / .01, 1)
        mus(t0 + (0, .17, .34, .51)[k], lp(v, 3500) * .5, g)


def scratch(t0, g=-14):
    d = .12
    x = tv(d)
    add(t0, bp(noise(d), 1800, 7000) * np.sin(np.pi * x / d) * (1 + .6 * np.sin(2 * np.pi * 60 * x)), g)


def boing(t0, g=-14, up=True):
    d = .35
    x = tv(d)
    f = (220 + 500 * x / d) if up else (720 - 500 * x / d)
    add(t0, np.sin(2 * np.pi * np.cumsum(f * (1 + .05 * np.sin(2 * np.pi * 18 * x))) / SR) * np.exp(-x * 5), g)


def rumble(a, d, g=-8, rise=False):
    x = tv(d)
    env = np.minimum(x / .3, 1) * np.minimum((d - x) / .3, 1)
    if rise:
        env = env * (x / d) ** .7
    add(a, (lp(noise(d), 260, 4) * 3 + bp(noise(d), 500, 3000) * .4) * env, g)


def buzzer(t0, g=-12):
    d = .6
    x = tv(d)
    add(t0, lp(np.sign(np.sin(2 * np.pi * 110 * x)), 1500) * np.minimum((d - x) / .05, 1) * .5, g)


# ---- musique
R0 = 146.8
SPACE = (110, 164.8, 220, 277.2)
pad(0, K["point"], SPACE, -10)
arp(0, K["point"], -20)
theme(K["point"], K["decol"], R0, -1, 118)
pad(K["decol"], K["arrive"], SPACE, -9)
arp(K["voyage"], K["arrive"], -20)
theme(K["arrive"], K["miaou"], R0 * 2 ** (2 / 12), -2, 112)
pad(K["miaou"], K["recu"], (98, 146.8, 196, 246.9), -10)
theme(K["recu"], K["phobos"], R0 * 2 ** (3 / 12), -2, 120)
pad(K["phobos"], K["loi"], (82.4, 123.5, 164.8, 207.7), -9)
arp(K["phobos"], K["loi"], -21, (659.3, 830.6, 987.8, 1318.5), .45)
theme(K["loi"], K["bleu"], R0 * 2 ** (5 / 12), -2, 124)
pad(K["bleu"], K["fin"], SPACE, -10)
theme(K["fin"], CARD, R0 * 2 ** (7 / 12), -1, 136)

for tk in JUMPS:
    ding(tk + .02, 1760, -19, .2)
    whoosh(tk, .25, -21, 800, 6000)

# hook : fanfare impériale, « miaou » satisfait
fanfare(.3, 523.25, -11)
mrrp(1.6, -9, 250)

# point rouge : ronflement, « ! »
snore(K["point"], K["cetait"], -16)
ding(K["point"] + 1.0, 2093, -13, .3)

# c'était Mars : sauts contre la fenêtre, Gérard
for k in range(6):
    tt = K["cetait"] + k / 1.6
    boing(tt + .05, -17)
    thud(tt + 1 / 1.6 - .02, 160, .15, -16)
voice(K["cetait"] + .4, 215, 4, -11)

# fusée en carton : scotch, Gérard
for k in range(3):
    d = .35
    x = tv(d)
    add(K["fusee"] + .1 + k * .45, bp(noise(d), 1500, 6000) * np.minimum(x / .02, 1) * np.exp(-x * 4) * (1 + .5 * np.sin(2 * np.pi * 80 * x)), -17)
voice(K["fusee"] + .5, 230, 3, -11)
mrrp(K["fusee"] + 1.8, -10, 300)

# décollage
rumble(K["decol"] + .3, 2.8, -6)
whoosh(K["decol"] + .6, 2.4, -14, 300, 4000)
snore(K["decol"] + .2, K["voyage"], -20)

# voyage : tic-tac + ronron de Michel
for k in range(8):
    tick(K["voyage"] + .3 + k * .42, -21 if k % 2 else -18)
d = K["arrive"] - K["voyage"]
x = tv(d)
add(K["voyage"], lp(noise(d), 120, 4) * 3 * (.5 + .5 * np.sin(2 * np.pi * 25 * x)) * np.minimum(x / .3, 1) * np.minimum((d - x) / .3, 1), -18)

# arrivée : atterrissage, grelottement, « Un plaid. »
thud(K["arrive"] + .05, 60, .5, -8)
flutter(K["arrive"] + .8, K["arrive"] + 2.6, 16, -19)
mrrp(K["arrive"] + 1.7, -8, 120)

# sauts en basse gravité (atterrissage à .2 + k·2,4 s)
for k in range(2):
    t0 = K["saut"] + .2 + k * 2.4
    boing(t0, -13, True)
    boing(t0 + 1.0, -16, False)
    thud(t0 + 2.4, 70, .3, -12)
thud(K["saut"] + .2, 70, .3, -12)

# volcan : grondement qui monte, Everest
rumble(K["volcan"] + .2, 1.2, -10, True)
ding(K["volcan"] + 1.1, 1046.5, -16, .4)

# griffoir
tt = K["griffe"] + .2
while tt < K["empereur"] - .2:
    scratch(tt, -13 + rs.uniform(-2, 2))
    tt += 60 / 18 / 2 * 2 * .17
mrrp(K["griffe"] + 2.0, -12, 200)

# empereur : couronne, fanfare
whoosh(K["empereur"] + .4, .5, -15, 1000, 6000)
ding(K["empereur"] + .9, 2637, -12, .8)
fanfare(K["empereur"] + 1.0, 587.3, -10)

# message radio
mrrp(K["miaou"] + .1, -7, 370)
for k in range(5):
    bleep(K["miaou"] + .4 + k * .5, 1500 if k % 2 else 1200)
static(K["miaou"] + .3, 2.7, -27)

# Gérard reçoit
static(K["recu"] + .2, .9, -22)
mrrp(K["recu"] + .3, -9, 370)
voice(K["recu"] + 1.25, 205, 3, -11)

# jour martien : horloge
for k in range(8):
    tick(K["sol"] + .2 + k * .42, -20 if k % 2 else -17)
for k in range(4):
    ding(K["sol"] + .5 + k * .6, 1318.5 * 2 ** (-k / 12), -17, .3)

# repas perdu
buzzer(K["repas"] + .4, -13)
mrrp(K["repas"] + 1.3, -8, 80)

# Phobos : « tap »
for tk in (.8, 1.6, 2.4):
    thud(K["phobos"] + tk, 220, .12, -14)
    ding(K["phobos"] + tk, 3200, -24, .08)
for k in range(3):
    thud(K["patient"] + .2 + k * .8, 220, .12, -16)
ding(K["patient"] + 1.6, 523.25, -16, 1.2)

# loi : parchemin, fanfare
whoosh(K["loi"] + .45, .4, -14, 1500, 7000)
fanfare(K["loi"] + .7, 523.25, -10)

# fenêtre de tir : « Ouf. »
voice(K["fenetre"] + .4, 200, 2, -11)
for tt in (1.0, 1.8, 2.5):
    for k in range(3):
        piou(K["fenetre"] + tt + k * .09, -21, 4200, 3000, .07)

# point bleu
ding(K["bleu"] + .8, 2093, -13, .3)
flutter(K["bleu"] + 1.0, K["fin"], 22, -22)

# fin : radio « J'arrive. », « NON. »
static(K["fin"] + .1, .8, -22)
mrrp(K["fin"] + .2, -7, 370)
voice(K["fin"] + 1.4, 215, 2, -8)
thud(K["fin"] + 1.4, 50, .5, -8)

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
MASTER_DB = float(sys.argv[1]) if len(sys.argv) > 1 else -0.5
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
wavfile.write("son17.wav", SR, (np.clip(st, -1, 1) * 32767).astype(np.int16))
print("pic", pk, "crête vraie dB", 20 * np.log10(tp), "durée", END)
