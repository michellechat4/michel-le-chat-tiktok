"""Son de la vidéo 11 : marche au salon, ding et sifflet à chaque saut dans le temps, ambiances par époque, grondement de l'impact, objets qui tombent."""
import numpy as np
from scipy.signal import butter, sosfilt, resample_poly
from scipy.io import wavfile
from scipy.ndimage import maximum_filter1d, uniform_filter1d
import importlib.util as _u, os as _o, sys
_sp = _u.spec_from_file_location("dinos", _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "11_dinos.py"))
ch = _u.module_from_spec(_sp); _sp.loader.exec_module(ch)
BEATS, K, CARD, END, JUMPS = ch.BEATS, ch.K, ch.CARD, ch.END, ch.JUMPS
B = {b["key"]: b for b in BEATS}

SR = 48000
N = int(END * SR) + SR
rs = np.random.RandomState(51)
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


def epiano(f, d=.6):
    t = tv(d)
    return (np.sin(2 * np.pi * f * t + .8 * np.sin(2 * np.pi * f * t) * np.exp(-t * 6))) * np.exp(-t * 3.5) * np.minimum(t / .004, 1)


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


def slide(t0, f0, f1, d=.8, g=-12):
    """Sifflet à coulisse."""
    x = tv(d)
    f = f0 * (f1 / f0) ** (x / d) * (1 + .02 * np.sin(2 * np.pi * 6 * x))
    v = np.sin(2 * np.pi * np.cumsum(f) / SR) + .15 * bp(noise(d), 1000, 6000)
    add(t0, v * np.minimum(x / .02, 1) * np.minimum((d - x) / .08, 1), g)


def tap(t0, g=-10):
    x = tv(.06)
    add(t0, lp(noise(.06), 2500) * np.exp(-x * 60), g, .3)


def thud(t0, f=55, d=.7, g=-2):
    x = tv(d)
    add(t0, np.sin(2 * np.pi * np.cumsum(f + 90 * np.exp(-x * 12)) / SR) * np.exp(-x * 5), g)
    add(t0, lp(noise(d), 1400) * np.exp(-x * 11), g - 3)


# ---- musique
# salon : petite marche (tuba + mallet)
mel = [0, 4, 7, 4, 9, 7, 4, None, 2, 5, 9, 5, 7, None, 4, None]
bas = [0, 5, 7, 5]


def marche(z0, z1, root=110.0, bpm=116):
    t0, i = z0, 0
    while t0 < z1 - .05:
        if i % 2 == 0:
            mus(t0, tuba(root * 2 ** (bas[(i // 2) % 4] / 12), .28), -7)
        m = mel[i % len(mel)]
        if m is not None:
            mus(t0, mallet(root * 4 * 2 ** (m / 12)), -12)
        if i % 4 == 2:
            mus(t0, hp(noise(.04), 6000) * np.exp(-tv(.04) * 90), -27)
        i += 1
        t0 += 60 / bpm / 2


# chute : « musique d'ascenseur » (accords doux, contrebasse, balais)
CHORDS = [(0, 4, 7, 11), (5, 9, 12, 16), (2, 5, 9, 12), (7, 11, 14, 17)]


def ascenseur(z0, z1, root=130.81, bpm=92):
    beat = 60 / bpm
    t0, i = z0, 0
    while t0 < z1 - .05:
        chd = CHORDS[(i // 4) % 4]
        if i % 4 in (0, 2):
            for n in chd:
                mus(t0 + .01 * n, epiano(root * 2 * 2 ** (n / 12), .9), -21)
        if i % 2 == 0:
            mus(t0, tuba(root / 2 * 2 ** (chd[0] / 12), .35), -9)
        else:
            mus(t0, tuba(root / 2 * 2 ** (chd[2] / 12), .3), -12)
        mus(t0, bp(noise(.12), 3000, 9000) * np.exp(-tv(.12) * 25), -30)
        if i % 8 in (1, 5):
            mus(t0 + beat / 2, mallet(root * 8 * 2 ** (chd[(i // 2) % 4] / 12), .5), -21)
        i += 1
        t0 += beat


def fade_zone(z0, z1, f=.25):
    a, b = int(z0 * SR), int(z1 * SR)
    n = int(f * SR)
    MUS[b - n:b] *= np.linspace(1, 0, n)



def crash(t0, g=-9):
    """Objet qui casse : choc + éclats."""
    thud(t0, 90, .35, g)
    x = tv(.5)
    add(t0, hp(noise(.5), 3000) * np.exp(-x * 9), g - 2, .2)
    for k in range(4):
        ding(t0 + .02 + k * .05, 2600 + 700 * k, g - 8, .25)


def saut_fx(t0, n=0):
    """Départ dans le temps : sifflet montant + ding + souffle."""
    slide(t0, 500, 1800, .35, -15)
    ding(t0 + .05, 880 * 1.03 ** n, -13, .5)
    whoosh(t0, .45, -16, 800, 6000)


def tapotis(t0, n=3, step=.3):
    for k in range(n):
        tap(t0 + k * step, -8)


# ---- musique : marche au salon, ascenseur dans le passé, marche au retour
marche(0, K["an64"])
fade_zone(0, K["an64"])
ascenseur(K["an64"], K["roche"])
fade_zone(K["an64"], K["roche"])
# espace : nappe grave
d = K["retour"] - K["roche"]
x = tv(d)
pad = sum(np.sin(2 * np.pi * f * x) for f in (55, 82.4, 110)) / 3
mus(K["roche"], pad * np.minimum(x / 1.0, 1) * np.minimum((d - x) / .3, 1), -12)
marche(K["retour"], CARD, 110.0, 112)
fade_zone(K["retour"], CARD)
# la sieste : musique au ralenti -> on l'étouffe
i0, i1 = int((K["sieste"] + .3) * SR), int((K["sieste"] + B["sieste"]["dur"]) * SR)
MUS[i0:i1] *= .35

# ---- sauts
for n, j in enumerate(JUMPS):
    saut_fx(j, n)
for n, j in enumerate(ch.MONTAGE_JUMPS):
    saut_fx(j, 10 + n)

# ---- salon, début
mrrp(K["hook"] + 1.0, -6)
voice(K["hook"] + 1.25, 215, 2, -10)
thud(K["machine"] + .2, 70, .3, -10)
whoosh(K["machine"] + 1.0, .5, -14, 400, 3000)
tap(K["machine"] + 1.6, -6)
voice(K["machine"] + 1.95, 240, 1, -9)
d = B["regle"]["dur"]
x = tv(d)
add(K["regle"], bp(np.sign(np.sin(2 * np.pi * (220 + 120 * x) * x)), 300, 3000) * np.minimum(x / .3, 1) * np.minimum((d - x) / .2, 1), -24)

# ---- objets poussés (t0 = 1.0, chute à +2.0, sol ~ +2.3)
for key, kind in (("an1", 1), ("an64", 1), ("an1024", 1), ("egypte", 1), ("neand", 0)):
    tapotis(K[key] + 1.0)
    whoosh(K[key] + 1.9, .35, -16, 500, 4000)
    if kind:
        crash(K[key] + 2.3)
    else:
        thud(K[key] + 2.3, 120, .25, -12)
voice(K["an1"] + 2.3, 205, 1, -10)
# téléphone qui sonne en tombant
x = tv(.5)
add(K["an64"] + 2.0, (np.sin(2 * np.pi * 1800 * x) * (np.sin(2 * np.pi * 20 * x) > 0)) * np.exp(-x * 3), -20)
mrrp(K["an64"] + 2.3, -8, 150)
ding(K["an1024"] + 2.4, 1320, -11, 1.2)
voice(K["neand"] + 2.2, 180, 1, -10)
# glace : vent, caillou, mammouth
d = B["glace"]["dur"]
x = tv(d)
add(K["glace"], bp(noise(d), 300, 2000) * (.6 + .4 * np.sin(2 * np.pi * .4 * x)) * np.minimum(x / .4, 1) * np.minimum((d - x) / .3, 1), -22)
tapotis(K["glace"] + 1.0)
whoosh(K["glace"] + 2.0, .45, -14, 400, 3000)
thud(K["glace"] + 2.45, 60, .4, -6)
x = tv(.7)
f = 300 + 500 * np.sin(np.pi * x / .7)
add(K["glace"] + 2.55, lp(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)), 2500) * np.hanning(len(x)), -15)
# grotte : feu qui crépite
d = B["neand"]["dur"]
x = tv(d)
crk = (rs.rand(len(x)) > .9993).astype(np.float32)
add(K["neand"], hp(np.convolve(crk, np.exp(-np.arange(200) / 30), "same"), 1500) * 3 + lp(noise(d), 400) * .3, -18)
# savane : grillons
d = B["vide"]["dur"]
x = tv(d)
add(K["vide"], np.sin(2 * np.pi * 4200 * x) * (np.sin(2 * np.pi * 9 * x) > .6) * .4, -26)
ding(K["vide"] + 1.2, 660, -16, .4)
# dinos : rugissement grave, mrrp
x = tv(1.0)
roar = lp(noise(1.0), 500) * (1 + np.sin(2 * np.pi * 70 * x)) * np.minimum(x / .1, 1) * np.exp(-x * 2.5)
add(K["dino"] + .9, roar, -6)
mrrp(K["dino"] + 2.0, -8, 200)
ding(K["tot"] + .3, 1046, -14, .6)
# sieste : ronron
d = B["sieste"]["dur"]
x = tv(d)
add(K["sieste"], lp(noise(d), 300) * (.5 + .5 * np.sin(2 * np.pi * 1.4 * x)) ** 2 * np.minimum(x / .4, 1) * np.minimum((d - x) / .3, 1), -9)
# espace
tapotis(K["pousse"] + .6, 3, .33)
slide(K["pousse"] + 1.6, 1500, 250, 1.0, -12)
whoosh(K["pousse"] + 1.6, 1.0, -12, 200, 2500)
# impact
thud(K["impact"], 35, 1.6, 0)
d = 3.0
x = tv(d)
add(K["impact"], lp(noise(d), 200, 4) * 5 * np.exp(-x * 1.2), -8)
x = tv(.3)
add(K["impact"] + 2.2, np.sin(2 * np.pi * np.cumsum(3000 + 800 * np.sin(np.pi * x / .3)) / SR) * np.hanning(len(x)), -18)
# retour : oiseau, claquement de mâchoire du chat
saut_fx(K["retour"], 14)
for k in range(3):
    x = tv(.18)
    add(K["retour"] + 1.0 + k * .45, np.sin(2 * np.pi * np.cumsum(2800 + 1200 * np.sin(np.pi * x / .18)) / SR) * np.hanning(len(x)), -18, .3)
for k in range(6):
    tap(K["retour"] + 1.6 + k * .09, -12)
# fin
voice(K["fin"] + .35, 230, 3, -9)
tapotis(K["fin"] + 1.4)
whoosh(K["fin"] + 2.3, .35, -16, 500, 4000)
crash(K["fin"] + 2.7, -7)
mrrp(K["fin"] + 3.0, -6, 380)
# ---- carton
i = int(CARD * SR)
FX[i:] = 0
MUS[i:] = 0
thud(CARD + .05, 40, .7, -3)
slide(CARD + 1.2, 1300, 300, .9, -16)

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
wavfile.write("son11.wav", SR, (np.clip(st, -1, 1) * 32767).astype(np.int16))
print("pic", pk, "crête vraie dB", 20 * np.log10(tp), "durée", END)
