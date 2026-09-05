# Fil: services/phonics_service.py
"""
Fokus på bestemte bogstaver og lyde i en tekst.

Appen kunne allerede bede AI'en om at bruge et fokus-bogstav, men bad
blot om "ord, der indeholder dette bogstav". Det er for løst på to måder:

*Positionen betyder alt.* Et barn, der er ved at lære `s`, øver forlyd:
**s**ol, **s**av, **s**ut. `s` inde i he**s**t træner ikke det samme, og
kan i praksis forvirre.

*Ingen kontrollerede resultatet.* Appen måler LIX på den færdige tekst og
viser tre kandidater, så en lærer kan vælge. Præcis samme greb mangler her:
en bestilling er ikke det samme som en leveret tekst.

Modulet her gør begge dele: det formulerer bestillingen præcist, og det
tæller bagefter, hvad teksten faktisk indeholder.
"""

import re

from services.word_service import ord_i_tekst

FORLYD = 'forlyd'
INDLYD = 'indlyd'
UDLYD = 'udlyd'
HVOR_SOM_HELST = 'hvorsomhelst'

POSITION_NAVNE = {
    FORLYD: 'forlyd (først i ordet)',
    INDLYD: 'indlyd (inde i ordet)',
    UDLYD: 'udlyd (sidst i ordet)',
    HVOR_SOM_HELST: 'hvor som helst i ordet',
}

VOKALER = set('aeiouyæøå')

# Konsonantklynger i dansk forlyd. De er en kendt forhindring: barnet skal
# holde to eller tre lyde sammen, før vokalen kommer.
KLYNGER = (
    'skr', 'spr', 'str', 'skv',
    'bl', 'br', 'dr', 'fl', 'fr', 'gl', 'gr', 'kl', 'kr', 'pl', 'pr',
    'sk', 'sl', 'sm', 'sn', 'sp', 'st', 'sv', 'tr', 'tv', 'kn', 'gn',
)

# Mønstre, hvor dansk retskrivning ikke følger lyden. Et barn, der lyderer
# sig gennem ordet, kommer galt afsted her. Listen er bevidst konservativ:
# den fanger de hyppigste faldgruber og påstår ikke at afgøre lydrethed.
SVAERE_MOENSTRE = [
    (re.compile(r'^hv'), 'stumt h i "hv"'),
    (re.compile(r'^hj'), 'stumt h i "hj"'),
    (re.compile(r'[aeiouyæøå][ln]d\b'), 'stumt d efter vokal'),
    (re.compile(r'rd\b'), 'stumt d i "rd"'),
    (re.compile(r'ds\b'), 'stumt d i "ds"'),
    (re.compile(r'eg\b'), '"eg" udtales som "ej"'),
    (re.compile(r'øj|ej|aj'), 'diftong'),
    (re.compile(r'(.)\1'), 'dobbeltkonsonant'),
]


def _rens(ord_):
    """Ordet uden tegnsætning, i småt."""
    return re.sub(r'[^\w]', '', (ord_ or '').lower(), flags=re.UNICODE)


def normaliser_fokus(fokus):
    """Læser brugerens fokus-input til en liste af lyde.

    Feltet er frit tekst - læreren skriver "s", "s, m" eller "sk br".
    Alt, der ikke er bogstaver, kasseres, og dubletter fjernes.
    """
    if not fokus:
        return []
    if isinstance(fokus, (list, tuple, set)):
        raa = ' '.join(str(f) for f in fokus)
    else:
        raa = str(fokus)
    fundne = re.findall(r'[^\W\d_]+', raa.lower(), flags=re.UNICODE)
    ud = []
    for f in fundne:
        if f not in ud:
            ud.append(f)
    return ud


def rammer(ord_, lyd, position=FORLYD):
    """Har ordet den ønskede lyd på den ønskede plads?"""
    o = _rens(ord_)
    lyd = (lyd or '').lower()
    if not o or not lyd:
        return False
    if position == FORLYD:
        return o.startswith(lyd)
    if position == UDLYD:
        return o.endswith(lyd)
    if position == INDLYD:
        # Inde i ordet vil sige hverken først eller sidst.
        return lyd in o[1:-1] if len(o) > 2 else False
    return lyd in o


def find_fokusord(tekst, fokus, position=FORLYD):
    """De ord i teksten, der rammer mindst én af fokus-lydene.

    Returnerer en dict fra lyd til de ord, der rammer den. Rækkefølgen er
    som i teksten, og hvert ord tælles kun én gang pr. lyd.
    """
    lyde = normaliser_fokus(fokus)
    if not lyde:
        return {}
    fundet = {lyd: [] for lyd in lyde}
    set_ord = {lyd: set() for lyd in lyde}
    for o in ord_i_tekst(tekst, medtag_stopord=True):
        ren = _rens(o)
        for lyd in lyde:
            if ren not in set_ord[lyd] and rammer(ren, lyd, position):
                set_ord[lyd].add(ren)
                fundet[lyd].append(ren)
    return fundet


def maal_fokus(tekst, fokus, position=FORLYD):
    """Måler, hvor godt en færdig tekst rammer det bestilte fokus.

    Det er dette tal, der gør fokus til andet end en hensigtserklæring:
    en lærer kan se, om teksten faktisk øver det, den skulle.

    Returnerer:
        lyde        - de efterspurgte lyde
        position    - hvor lyden skulle sidde
        pr_lyd      - antal forskellige ord pr. lyd
        ord_pr_lyd  - selve ordene, så de kan vises eller printes
        antal_ord   - tekstens længde i ord
        andel       - fokusord som andel af alle ord, afrundet
        daekning    - hvor stor en del af de bestilte lyde der optræder
    """
    lyde = normaliser_fokus(fokus)
    alle_ord = ord_i_tekst(tekst, medtag_stopord=True)
    if not lyde or not alle_ord:
        return {
            'lyde': lyde, 'position': position, 'pr_lyd': {}, 'ord_pr_lyd': {},
            'antal_ord': len(alle_ord), 'andel': 0.0, 'daekning': 0.0,
        }

    fundet = find_fokusord(tekst, lyde, position)
    pr_lyd = {lyd: len(ord_) for lyd, ord_ in fundet.items()}
    ramte = sum(1 for antal in pr_lyd.values() if antal)
    samlet = sum(pr_lyd.values())

    return {
        'lyde': lyde,
        'position': position,
        'pr_lyd': pr_lyd,
        'ord_pr_lyd': fundet,
        'antal_ord': len(alle_ord),
        'andel': round(samlet / len(alle_ord), 3),
        'daekning': round(ramte / len(lyde), 2),
    }


def svaere_moenstre(ord_):
    """Navngiver de danske skrivemønstre i ordet, som bryder med lyden.

    Bruges til at advare en lærer om ord, et lyderende barn vil snuble
    over - ikke til at afgøre om et ord er lydret. Dansk retskrivning har
    flere undtagelser, end en regelliste kan fange, så listen er
    konservativ og melder hellere for lidt end for meget.
    """
    o = _rens(ord_)
    if not o:
        return []
    fundne = []
    for moenster, navn in SVAERE_MOENSTRE:
        if moenster.search(o) and navn not in fundne:
            fundne.append(navn)
    return fundne


def forlydsklynge(ord_):
    """Konsonantklyngen i ordets forlyd, hvis der er en. Ellers None.

    "strand" giver "str", "blomst" giver "bl", "sol" giver None.
    """
    o = _rens(ord_)
    for klynge in sorted(KLYNGER, key=len, reverse=True):
        if o.startswith(klynge):
            return klynge
    return None


def prompt_instruktion(fokus, position=FORLYD, mindst=6):
    """Formulerer fokus-kravet til AI'en.

    Den gamle formulering bad om "ord, der indeholder dette bogstav" og
    forklarede det med at "øve udtalen". Begge dele er forkerte for
    målgruppen: barnet øver afkodning, ikke udtale, og placeringen af
    lyden er det, der afgør om øvelsen rammer.
    """
    lyde = normaliser_fokus(fokus)
    if not lyde:
        return None

    vist = ', '.join(f"'{l}'" for l in lyde)
    hvor = POSITION_NAVNE.get(position, POSITION_NAVNE[FORLYD])

    linjer = [
        f"- **FOKUSLYD:** Historien skal træne {vist} som {hvor}.",
        f"  Brug mindst {mindst} forskellige ord, hvor lyden sidder netop dér, "
        f"og fordel dem jævnt gennem teksten frem for at samle dem i én sætning.",
        "  Ordene skal falde naturligt i handlingen. En opremsning af ord med "
        "samme lyd er ikke en historie, og barnet gennemskuer det.",
    ]
    if position == FORLYD:
        linjer.append("  Det er lyden i begyndelsen af ordet, der tæller - "
                      "et ord som 'hest' træner ikke 's' som forlyd.")
    return '\n'.join(linjer)
