"""Son de la vidéo 10 : petite marche au salon, musique d'ascenseur pendant la chute, vent, grondement du noyau, mer et manchot, sifflet à coulisse."""
import numpy as np
from scipy.signal import butter, sosfilt, resample_poly
from scipy.io import wavfile
from scipy.ndimage import maximum_filter1d, uniform_filter1d
import importlib.util as _u, os as _o, sys
_sp = _u.spec_from_file_location("trou", _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "10_trou.py"))
ch = _u.module_from_spec(_sp); _sp.loader.exec_module(ch)
BEATS, K, CARD, END, JUMPS = ch.BEATS, ch.K, ch.CARD, ch.END, ch.JUMPS
B = {b["key"]: b for b in BEATS}

SR = 48000
N = int(END * SR) + SR
rs = np.random.RandomState(50)
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


marche(0, K["chute"])
fade_zone(0, K["chute"])
ascenseur(K["chute"], K["arrive"])
fade_zone(K["chute"], K["arrive"])
ascenseur(K["arrive"], K["retour"], root=146.83, bpm=88)
marche(K["retour"], CARD, 110.0, 108)
# « sans bruit » : la musique se coupe une seconde au mur du son
i0, i1 = int((K["son"] + .4) * SR), int((K["son"] + 1.4) * SR)
MUS[i0:i1] *= .08
# ---- chaque saut de chronomètre : ding
for n, j in enumerate(JUMPS):
    ding(j, 880 * 1.05 ** n, -15, .4)

# ---- salon
mrrp(K["hook"] + 1.0, -6)
voice(K["regle"] + 1.25, 205, 2, -10)
for k in range(3):
    tap(K["pousse"] + .9 + k * .12, -8)
voice(K["pousse"] + 1.15, 230, 1, -9)
whoosh(K["pousse"] + 1.3, .7, -14, 300, 2500)
slide(K["pousse"] + 2.0, 1400, 300, 1.2, -12)
mrrp(K["pousse"] + 2.9, -8, 150)
# ---- chute : vent qui monte avec la vitesse
d = K["arrive"] - K["chute"]
x = tv(d)
v = np.array([ch.speed(ch.phys_at(K["chute"] + xx)) for xx in x[::480]])
env = np.interp(x, x[::480], np.clip(v / 9500, 0, 1)) * .8 + .2
wind = bp(noise(d), 200, 1800) * env * np.minimum(x / .5, 1) * np.minimum((d - x) / .5, 1)
add(K["chute"], wind, -19)
voice(K["chute"] + 1.05, 200, 2, -10)
ding(K["son"] + 1.4, 1760, -14, .6)
whoosh(K["kola"] + .5, 1.2, -13, 600, 5000, .4)
for k in range(6):
    ding(K["apes"] + .4 + k * .35, 1568 * 1.12 ** (k % 3), -22, .4)
# noyau : grondement
d = B["noyau"]["dur"] + B["centre"]["dur"] + B["press"]["dur"]
x = tv(d)
add(K["noyau"], lp(noise(d), 120, 4) * 6 * np.minimum(x / .6, 1) * np.minimum((d - x) / .5, 1), -12)
whoosh(K["centre"] + .4, .8, -11, 300, 3000)
for k in range(3):
    add(K["press"] + .3 + k * .25, bp(np.sign(np.sin(2 * np.pi * np.cumsum(90 + 30 * tv(.2)) / SR)), 200, 900) * np.hanning(int(.2 * SR)), -18)
voice(K["press"] + 1.55, 190, 1, -10)
# coupes : petit « ping » radar
for key in ("trou", "manteau", "remonte"):
    for k in range(3):
        ding(K[key] + .3 + k * 1.1, 2093, -22, .3)
# forage du trou
d = 2.0
x = tv(d)
add(K["trou"] + .4, bp(np.sign(np.sin(2 * np.pi * 70 * x)), 100, 2000) * np.minimum(x / .1, 1) * np.minimum((d - x) / .2, 1), -20)
# ---- océan
d = K["retour"] - K["arrive"]
x = tv(d)
waves = lp(noise(d), 900) * (.6 + .4 * np.sin(2 * np.pi * .35 * x)) * np.minimum(x / .5, 1) * np.minimum((d - x) / .4, 1)
add(K["arrive"], waves, -15)
slide(K["arrive"] + .8, 300, 1300, .9, -13)
add(K["arrive"] + 1.75, bp(noise(.5), 500, 4000) * np.exp(-tv(.5) * 8), -12)
voice(K["arrive"] + 1.85, 215, 2, -10)
for t0 in (K["zero"] + .5, K["zero"] + 1.0):
    x = tv(.25)
    f = 600 + 300 * np.sin(np.pi * x / .25)
    add(t0, bp(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)), 500, 3000) * np.hanning(len(x)), -15, -.3)
ding(K["zero"] + 2.3, 1046, -13, .6)
slide(K["zero"] + 2.6, 1300, 300, .9, -13)
# ---- retour, fin
slide(K["retour"] + 1.0, 300, 1300, .9, -13)
voice(K["retour"] + 2.6, 260, 1, -16)
mrrp(K["fin"] + 1.2, -6, 380)
for k in range(3):
    tap(K["fin"] + 1.9 + k * .1, -8)
slide(K["fin"] + 2.2, 1300, 300, .9, -12)
voice(K["fin"] + 2.75, 200, 2, -10)
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
wavfile.write("son10.wav", SR, (np.clip(st, -1, 1) * 32767).astype(np.int16))
print("pic", pk, "crête vraie dB", 20 * np.log10(tp), "durée", END)
