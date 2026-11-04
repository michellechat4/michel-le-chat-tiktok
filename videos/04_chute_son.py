"""Son de la vidéo 04 : marche pizzicato sournoise, tapotements, casse, silence d'attente."""
import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
import importlib.util as _u, os as _o
_sp = _u.spec_from_file_location("chute", _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "04_chute.py"))
ch = _u.module_from_spec(_sp); _sp.loader.exec_module(ch)
BEATS, K, IMP, OBJS, LAST, CARD, END = ch.BEATS, ch.K, ch.IMP, ch.OBJS, ch.LAST, ch.CARD, ch.END

SR = 48000
N = int(END * SR) + SR
rs = np.random.RandomState(44)
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


def pizz(f, d=.2):
    t = tv(d)
    return (np.sin(2 * np.pi * f * t) + .5 * np.sin(4 * np.pi * f * t) * np.exp(-t * 20)) * np.exp(-t * 17) * np.minimum(t / .002, 1)


def basson(f, d=.2):
    t = tv(d)
    return lp(2 * ((f * t) % 1) - 1, 560) * np.minimum(t / .008, 1) * np.exp(-t * 8)


# musique : marche sur la pointe des pieds, en mineur, qui monte d'un ton par décor
ST = 60 / 132 / 2  # croche
mel = [0, None, 3, None, 7, None, 3, None, 8, None, 7, 6, 7, None, None, None, 0, None, 3, None, 7, None, 10, None, 8, None, 7, None, 3, None, 2, None]
bas = [0, 7, 0, 7, 5, 7, 0, 7]
root = 110.0
fin_mus = K["fin1"]
i = 0
t0 = 0.0
beat_of = lambda t: [b for b in BEATS if b["start"] <= t][-1]
while t0 < fin_mus:
    b = beat_of(t0)
    n = b["n"]
    tr = {"salon": 0, "toit": 2, "mer": 4, "paris": 6, "fin": 0}[b["ph"]]
    if i % 2 == 0:
        mus(t0, basson(root * 2 ** ((bas[(i // 2) % 8] + tr) / 12), ST * 1.7), -7)
    m = mel[i % len(mel)]
    if m is not None:
        mus(t0, pizz(root * 4 * 2 ** ((m + tr) / 12), .26), -11)
    if b["ph"] in ("mer", "paris") and i % 4 == 0:
        x = tv(.2)
        mus(t0, np.sin(2 * np.pi * np.cumsum(52 + 100 * np.exp(-x * 26)) / SR) * np.exp(-x * 12), -9)
    if b["ph"] != "salon" and i % 2 == 1:
        mus(t0, hp(noise(.03), 7000) * np.exp(-tv(.03) * 120), -30)
    i += 1
    t0 += ST
# la musique se tait pendant que la tour bascule, reprend pour la chute
for a, z in ((K["chute"] + .05, K["seine"] + 1.2),):
    env = 1 - np.clip((tt - a) / .3, 0, 1) * np.clip((z - tt) / .2, 0, 1)
    MUS *= env.astype(np.float32)
MUS *= np.clip((fin_mus + .3 - tt) / .5, 0, 1).astype(np.float32)


# ---------------- bruitages
def tap(t0, g=-13):
    x = tv(.05)
    add(t0, bp(noise(.05), 500, 2600) * np.exp(-x * 90), g)


def glass(t0, g=-3, pan=.25):
    d = .9
    x = tv(d)
    v = sum(np.sin(2 * np.pi * f * x) * np.exp(-x * a) for f, a in ((2300, 9), (3517, 11), (4780, 14), (6210, 18), (7930, 24)))
    v = v / 3 + hp(noise(d), 3500) * np.exp(-x * 13) * 1.2
    add(t0, v, g, pan)
    for k in range(12):
        dt = rs.uniform(.02, .45)
        x2 = tv(.05)
        add(t0 + dt, np.sin(2 * np.pi * rs.uniform(3000, 8000) * x2) * np.exp(-x2 * 90), g - 8, rs.uniform(-.3, .6))


def ceramic(t0, g=-3):
    d = .5
    x = tv(d)
    add(t0, (bp(noise(d), 800, 5000) * np.exp(-x * 14) + np.sin(2 * np.pi * 1450 * x) * np.exp(-x * 22)) * .9, g, .2)
    for k in range(8):
        x2 = tv(.04)
        add(t0 + rs.uniform(.03, .3), bp(noise(.04), 1500, 6000) * np.exp(-x2 * 100), g - 6, rs.uniform(-.2, .5))


def thud(t0, f=55, d=.7, g=-2):
    x = tv(d)
    add(t0, np.sin(2 * np.pi * np.cumsum(f + 90 * np.exp(-x * 12)) / SR) * np.exp(-x * 5), g)
    add(t0, lp(noise(d), 1400) * np.exp(-x * 11), g - 3)


def metal(t0, g=-5, d=1.1):
    x = tv(d)
    v = sum(np.sin(2 * np.pi * f * x) * np.exp(-x * a) for f, a in ((310, 5), (523, 6), (877, 7), (1490, 9), (2230, 12)))
    add(t0, v / 2.5 + bp(noise(d), 500, 5000) * np.exp(-x * 7), g, .1)


def splash_snd(t0, g=-2, d=2.0):
    x = tv(d)
    v = lp(noise(d), 2600) * np.minimum(x / .03, 1) * np.exp(-x * 2.2) + hp(noise(d), 3000) * .35 * np.exp(-x * 1.4)
    add(t0, v, g)
    add(t0, np.sin(2 * np.pi * np.cumsum(44 + 80 * np.exp(-x * 7)) / SR) * np.exp(-x * 3), g - 2)


# tapotements avant chaque poussée
for k, o in list(OBJS.items()) + [("dernier", LAST)]:
    n_t = 2 if o["tp"] >= .5 else 1
    for j in range(n_t):
        tap(o["ts"] + o["tp"] * (j + .5) / n_t)
    # glissement
    d = o["s"]
    x = tv(d)
    add(o["ts"] + o["tp"], bp(noise(d), 300, 1800) * np.hanning(len(x)), -18 + min(o["shake"], 30) * .35)
    # petit sifflet de chute
    d = o["tf"]
    x = tv(d)
    add(o["ts"] + o["tp"] + o["s"], np.sin(2 * np.pi * np.cumsum(1500 - 900 * x / d) / SR) * np.hanning(len(x)), -19)
# tapotements du crochet (boucle)
for j in range(4):
    t_ = (j + .5) * np.pi / 2.6
    if t_ < 3:
        tap(t_, -14)
glass(IMP["verre"])
ceramic(IMP["tasse"])
ceramic(IMP["vase"], -1)
glass(IMP["vase"] + .01, -12)
# télé : verre + grésillement
glass(IMP["tele"], -6)
thud(IMP["tele"], 70, .45, -5)
x = tv(.5)
add(IMP["tele"] + .05, hp(noise(.5), 2500) * (np.sin(2 * np.pi * 60 * x) > 0) * np.exp(-x * 7), -13)
# frigo
thud(IMP["frigo"], 52, .8, -1)
metal(IMP["frigo"], -9, .7)
# piano : accord brutal + do final
x = tv(1.8)
for f in (65.4, 130.8, 196, 277, 311, 415, 622, 880, 1244):
    add(IMP["piano"], (np.sin(2 * np.pi * f * x) + .4 * np.sin(4 * np.pi * f * x)) * np.exp(-x * 2.6) / 3.2, -3, rs.uniform(-.3, .3))
thud(IMP["piano"], 50, .9, -2)
x = tv(1.0)
add(IMP["piano"] + .75, (np.sin(2 * np.pi * 261.6 * x) + .5 * np.sin(4 * np.pi * 261.6 * x)) * np.exp(-x * 4) * np.minimum(x / .004, 1), -8)
# voiture + alarme
thud(IMP["voiture"], 48, .8, -1)
metal(IMP["voiture"], -5)
glass(IMP["voiture"], -9)
x = tv(.32)
for k in range(2):
    add(IMP["voiture"] + .35 + k * .42, (np.sign(np.sin(2 * np.pi * 620 * x))) * .28 * np.minimum(x / .01, 1), -19)
# bus
thud(IMP["bus"], 42, 1.1, 0)
metal(IMP["bus"], -3, 1.5)
glass(IMP["bus"], -7)
# barque : vagues + mouette
x = tv(1.6)
add(K["barque"], lp(noise(1.6), 900) * np.sin(x * 3) ** 2, -12)
# avion, statue : eau
x = tv(1.0)
add(OBJS["avion"]["ts"] + OBJS["avion"]["tp"], np.sin(2 * np.pi * np.cumsum(200 + 90 * x) / SR) * np.hanning(len(x)), -17)
splash_snd(IMP["avion"], -1)
d = ch.STATUE_DUR
x = tv(d)
add(ch.STATUE_T0, bp(noise(d), 120, 900) * (x / d) ** 1.5, -6)
metal(ch.STATUE_T0, -14, .8)
splash_snd(IMP["statue"], 0)
# tapotement statue
for j in range(3):
    tap(K["statue0"] + .49 + j * .98, -14)
# tour Eiffel : patte, gémissement de métal, puis énorme chute
for j in range(4):
    tap(K["tour3"] + (.44 + j * .87), -11)
d = ch.TOUR_DUR
x = tv(d)
g_ = np.sin(2 * np.pi * np.cumsum(55 + 170 * (x / d) ** 2 + 6 * np.sin(x * 19)) / SR) + .5 * np.sin(2 * np.pi * np.cumsum(117 + 260 * (x / d) ** 2) / SR)
add(K["chute"], bp(g_, 60, 1600) * (x / d) ** .8 * np.minimum((d - x) / .02, 1), -6)
add(K["chute"], bp(noise(d), 200, 1500) * (x / d) ** 2.5, -8)
splash_snd(IMP["tour"], 1, 2.2)
thud(IMP["tour"], 34, 1.6, 1)
metal(IMP["tour"], -4, 1.8)

# Gérard : petites voix
def voice(t0, base=215, n=3, g=-11):
    for k in range(n):
        x = tv(.1)
        f = base * rs.uniform(.92, 1.15) * (1 + .1 * np.sin(x * 50))
        add(t0 + k * .1, bp(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)), 350, 2500) * np.hanning(len(x)), g)


for b in BEATS:
    if b["ger"]:
        voice(b["start"] + .03, 215, min(2 + len(b["ger"]) // 5, 5))


def mrrp(t0, g=-5):
    d = .55
    x = tv(d)
    f = 340 + 370 * np.minimum(x / .34, 1) ** 1.6
    v = sum(np.sin(2 * np.pi * np.cumsum(f * k) / SR) / k for k in (1, 2, 3, 4))
    v = bp(v, 300, 3200) * (.65 + .35 * np.sin(2 * np.pi * 24 * x)) * np.hanning(len(x)) ** .6
    add(t0, norm(v), g)


# fin : pointe des pieds, tic-tac, ronflette, verre
x = tv(.07)
for j in range(5):
    add(K["fin1"] + .5 + j * .4, bp(noise(.07), 300, 1200) * np.exp(-x * 60), -14, .4)
t_ = K["h1"]
while t_ < K["calme"]:
    x = tv(.03)
    add(t_, bp(noise(.03), 2000, 7000) * np.exp(-x * 160), -14)
    t_ += .12
t_ = K["calme"]
while t_ < K["oeil"] + .55:
    x = tv(.03)
    add(t_, bp(noise(.03), 2000, 7000) * np.exp(-x * 160), -17)
    t_ += .5
# ronron de sommeil
d = K["oeil"] + .55 - K["h1"]
x = tv(d)
add(K["h1"], lp(np.sign(np.sin(2 * np.pi * 26 * x)) * (1 + np.sin(2 * np.pi * .55 * x)) / 2, 300), -21)
# yeux qui s'ouvrent : petit ding
x = tv(.25)
add(K["oeil"] + .55, np.sin(2 * np.pi * 1760 * x) * np.exp(-x * 18), -15)
glass(IMP["dernier"], -2)
mrrp(K["stare"] + .1, -4)
# carton
i = int(CARD * SR)
FX[i:] = 0
MUS[i:] = 0
x = tv(.5)
add(CARD + .05, np.sin(2 * np.pi * np.cumsum(46 + 60 * np.exp(-x * 10)) / SR) * np.exp(-x * 7), -6)
glass(CARD + 1.5, -14)

L = MUS * db2(-1) + FX[:, 0]
Rr = MUS * db2(-1) + FX[:, 1]
L, Rr = np.tanh(L * 1.6), np.tanh(Rr * 1.6)
pk = max(np.abs(L).max(), np.abs(Rr).max())
st = np.stack([L, Rr], 1)[: int(END * SR)] / pk * .89
# mastering : on coupe l'extrême aigu (éclats saturés), gain, limiteur de crête vraie (suréchantillonné x4)
from scipy.ndimage import maximum_filter1d, uniform_filter1d
from scipy.signal import resample_poly
MASTER_DB, LIM_DB = -1.2, -3.0
st = sosfilt(butter(4, 14000, "low", fs=SR, output="sos"), st, axis=0) * db2(MASTER_DB)
lim = db2(LIM_DB)
for _ in range(3):
    up = np.abs(resample_poly(st, 4, 1, axis=0)).max(1)
    env = up.reshape(-1, 4)[:len(st)].max(1) if len(up) % 4 == 0 else up[:len(st) * 4].reshape(-1, 4).max(1)
    gr = np.minimum(1, lim / np.maximum(env, 1e-6))
    w = int(.004 * SR)
    gr = 1 - maximum_filter1d(1 - gr, 2 * w + 1)
    gr = uniform_filter1d(gr, 2 * w + 1)
    st = st * gr[:, None]
tp = np.abs(resample_poly(st, 4, 1, axis=0)).max()
wavfile.write("son4.wav", SR, (np.clip(st, -1, 1) * 32767).astype(np.int16))
print("pic", pk, "crête vraie dB", 20 * np.log10(tp), "durée", END)
