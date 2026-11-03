# Chronologie partagée entre l'image et le son.
# (n, durée, légende, sous-titre) — légende None = rien, "=" = garde la précédente
RAW = [
    (0, 2.5, "CE CHAT VA | *DÉTRUIRE LA TERRE.*", "(en ronronnant)"),
    (0, 2.1, "Voici *Michel.* 25 dB : | moins qu'un chuchotement.", None),
    (0, 2.4, "Règle : à chaque caresse, | le volume *double.*", "+10 dB = 2× plus fort à l'oreille"),
    (1, 1.2, "Une bibliothèque.", None),
    (2, 0.9, "Un frigo.", None),
    (3, 1.2, "Le poisson s'inquiète.", None),
    (4, 1.3, "Gérard n'entend | plus la télé.", None),
    (5, 0.9, "Un aspirateur.", None),
    (6, 1.3, "Le voisin tape au mur.", None),
    (7, 1.1, "Une moto. Dans le salon.", None),
    (8, 0.95, "Une boîte de nuit.", None),
    (9, 0.95, "Une tronçonneuse.", None),
    (10, 1.2, "Seuil de la douleur.", None),
    (11, 1.7, "Gérard continue. | Personne ne sait pourquoi.", None),
    (12, 1.1, "Un avion de chasse.", None),
    (13, 1.8, "*LES VITRES EXPLOSENT.*", None),
    # rue
    (14, 1.2, "Toutes les alarmes | du quartier.", None),
    (15, 1.3, "Le Krakatoa, à 160 km.", None),
    (16, 1.4, "Les maisons *s'envolent.*", None),
    (17, 1.9, "Ce n'est plus un son. | *C'est une onde de choc.*", None),
    # Paris
    (18, 1.0, "Tout Paris se réveille.", None),
    (19, 1.3, "Les Parisiens râlent.", None),
    (20, 1.1, "La tour Eiffel penche.", None),
    (21, 1.2, "La tour Eiffel *s'en va.*", None),
    (22, 1.7, "Une bombe atomique | toutes les 1,6 s.", None),
    # Terre
    (23, 0.95, "On l'entend à Marseille.", None),
    (24, 0.9, "À Moscou.", None),
    (25, 1.5, "À New York. | Les USA portent plainte.", None),
    (26, 1.6, "Presque 2 Tsar Bomba. | *Par seconde.*", None),
    (27, 0.55, None, None),
    (28, 1.7, "Dans l'espace : silence. | *Sauf Michel.*", None),
    (29, 1.4, "La Lune tape au mur.", None),
    (30, 1.0, "Tsunamis. Partout.", None),
    (31, 0.5, None, None),
    (32, 1.7, "1 astéroïde des dinosaures. | *Par seconde.*", None),
    (33, 0.5, None, None),
    (34, 1.1, "L'atmosphère se barre.", None),
    (35, 1.5, "Michel développe | la puissance *du Soleil.*", None),
    (36, 1.3, "Océans évaporés | en 1 seconde.", None),
    (37, 0.75, "Gérard continue.", None),
    (38, 0.55, "=", None),
    (39, 0.5, "=", None),
    (40, 1.25, "Dernière caresse.", None),
    (41, 3.6, None, None),
    # fin (encore n=41)
    (41, 1.9, "Michel, lui, va très bien.", None),
    (41, 1.2, None, None),
    (41, 2.4, "Caresse *n° 42 ?*", None),
]
END_CARD_DUR = 2.2

BEATS = []
_t = 0.0
_last = None
for n, d, cap, sub in RAW:
    if cap == "=":
        cap_show, cap_start = _last
    else:
        cap_show, cap_start = cap, _t
        _last = (cap, _t)
    BEATS.append(dict(n=n, start=_t, dur=d, cap=cap_show, sub=sub, cap_start=cap_start))
    _t += d

T = {}
for b in BEATS:
    T.setdefault(b["n"], b["start"])
T41 = T[41]
E0 = T41 + 3.6            # début de la fin
CARD = _t                 # carton final
END = CARD + END_CARD_DUR
FPS = 30
W, H = 1080, 1920


def beat_at(t):
    cur = BEATS[0]
    for b in BEATS:
        if b["start"] <= t:
            cur = b
        else:
            break
    return cur


def level(t):
    return beat_at(t)["n"]


def db(n):
    return 25 + 10 * n


def stroke_phase(t):
    """Nombre de caresses écoulées (continu) : une caresse complète par temps fort."""
    p = 0.0
    for b in BEATS:
        if t >= b["start"] + b["dur"]:
            p += 1
        elif t >= b["start"]:
            p += (t - b["start"]) / b["dur"]
            break
    return p


SCENES = [
    ("salon", 0.0, T[14]),
    ("rue", T[14], T[18]),
    ("paris", T[18], T[23]),
    ("terre", T[23], T41),
    ("boum", T41, CARD),
    ("carton", CARD, END),
]

if __name__ == "__main__":
    print("durée totale %.1f s, T41=%.1f, E0=%.1f, carton=%.1f" % (END, T41, E0, CARD))
