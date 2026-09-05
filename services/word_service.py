# Fil: services/word_service.py
"""
Ordbank-service: normalisering og sværhedsgrad for danske ord.

Baggrund
--------
LIX måler kun overfladen af en tekst - gennemsnitlig sætningslængde og
andelen af ord over 6 bogstaver. Formlen kan derfor ikke se forskel på
"hyggeligt" og "kollektivt", selvom det første er et hverdagsord for et
barn og det andet næsten aldrig optræder i børnesprog.

Dette modul supplerer LIX med to ting, der faktisk siger noget om, hvor
svært et ord er at læse:

  1. Hvor hyppigt ordet er i dansk (frekvensbånd 1-5).
  2. Om ordet er sammensat - dansk sætter ord sammen ("flod" + "hest"),
     og et sammensat ord er sværere end sine dele hver for sig.

Frekvenstabellen ligger som data i repoet og er bygget med
scripts/build_word_frequency.py. Den vej er valgt for at undgå at have
'wordfreq' med i produktion, hvor pakken ville fylde 58 MB.
"""

import json
import os
import re
import threading

import snowballstemmer

# Bånd 1 er lettest (de mest almindelige ord), bånd 5 er sværest og
# dækker alt, der ikke står i frekvenslisten.
BAAND_LETTEST = 1
BAAND_SVAEREST = 5

BAAND_NAVNE = {
    1: "meget almindeligt",
    2: "almindeligt",
    3: "kendt",
    4: "sjældnere",
    5: "svært eller ukendt",
}

_DATA_STI = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'da_ordfrekvens.json')

# Bindebogstaver i danske sammensætninger: "fødsel-s-dag", "barn-e-vogn".
_BINDEBOGSTAVER = ('', 's', 'e')

# Mindste længde på hver del i en sammensætning. Under 3 bogstaver bliver
# opdelingen for tilfældig ("kat" ville blive delt i "ka" + "t").
_MIN_DEL = 3

# Appens egen elementliste (dyr, steder, ting) er ord, vi selv tilbyder
# boernene. De hoerer til deres kerneordforraad, men flere af dem - "myre",
# "dovendyr", "enhjoerning" - er for sjaeldne til at staa i en frekvensliste
# bygget paa voksensprog. Uden dem ville appens egne forslag blive markeret
# som svaere ord i appens egne historier.
_ELEMENT_STI = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'static', 'laesehest_data.json')
_ELEMENT_BAAND = 2  # Konkrete navneord, barnet selv har valgt.

_ord_baand = None
_laas = threading.Lock()
_stemmer = snowballstemmer.stemmer('danish')

# Ord, som ikke skal tælle med i en ordbank: de bærer ikke betydning,
# og et barn afkoder dem sjældent bevidst.
STOPORD = frozenset("""
og i er af det at en et til på jeg har for ikke med den der de du kan som
han vi men om så var hun mig sig dig hvad her nu ja nej være blev bliver
denne dette disse min mit mine din dit dine hans hendes deres vores
skal vil må kunne ville skulle da når hvis fordi eller også kun bare
ind ud op ned hen over under ved fra efter før mens hele helt meget
noget nogen ingen alle andre samme sådan hvor hvem hvorfor hvordan
""".split())


def _hent_baand():
    """Indlæser frekvenstabellen ved første brug. Trådsikker og idempotent."""
    global _ord_baand
    if _ord_baand is not None:
        return _ord_baand
    with _laas:
        if _ord_baand is not None:
            return _ord_baand
        tabel = {}
        try:
            with open(_DATA_STI, encoding='utf-8') as fh:
                raa = json.load(fh)
            for baand, ord_liste in raa.items():
                b = int(baand)
                for o in ord_liste:
                    tabel[o] = b
        except (OSError, ValueError):
            # Uden tabellen fungerer resten stadig; alle ord bliver blot
            # betragtet som ukendte. Det er bedre end at vælte et kald.
            tabel = {}

        # Appens egne elementord lægges oveni og kan gøre et ord lettere,
        # men aldrig sværere. Et ord, vi selv viser barnet på et billedkort,
        # er mere kendt for det barn, end et voksenkorpus antyder:
        # "blæksprutte" er sjældent i avisdansk og hverdagsagtigt i en
        # billedbog. Omvendt skal et element, der allerede er vurderet som
        # meget almindeligt, ikke gøres sværere af at stå på listen.
        for o in _hent_elementord():
            for noegle in (o, _stemmer.stemWord(o)):
                tabel[noegle] = min(tabel.get(noegle, _ELEMENT_BAAND), _ELEMENT_BAAND)

        _ord_baand = tabel
    return _ord_baand


def _hent_elementord():
    """Ordene fra appens elementliste, ét ord ad gangen og i småt."""
    try:
        with open(_ELEMENT_STI, encoding='utf-8') as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return []
    ud = []
    for kategori in data.get('categories', []):
        for element in kategori.get('items', []):
            for felt in (element.get('name'), element.get('value')):
                for del_ in re.findall(r"[^\W\d_]+", (felt or '').lower(), flags=re.UNICODE):
                    if len(del_) >= 2:
                        ud.append(del_)
    return ud


def normaliser(ord_):
    """Reducerer et ord til sin stamme, så bøjninger grupperes.

    "hesten", "heste" og "hest" bliver alle til samme nøgle, hvilket er
    det, en ordbank skal bruge for at vide, at barnet har mødt ordet før.
    """
    if not ord_:
        return ''
    return _stemmer.stemWord(ord_.strip().lower())


def ord_i_tekst(tekst, medtag_stopord=False):
    """Trækker ordene ud af en tekst i den rækkefølge, de står.

    Bindestreger og apostroffer bevares inde i ord ("far-far", "barnets"),
    mens al anden tegnsætning fjernes.
    """
    if not tekst:
        return []
    fundne = re.findall(r"[^\W\d_]+(?:[-'][^\W\d_]+)*", tekst.lower(), flags=re.UNICODE)
    if medtag_stopord:
        return fundne
    return [o for o in fundne if o not in STOPORD]


def _slaa_op(ord_):
    """Bånd for et ord, som det står, eller for dets stamme. None hvis ukendt."""
    tabel = _hent_baand()
    if ord_ in tabel:
        return tabel[ord_]
    stamme = normaliser(ord_)
    if stamme in tabel:
        return tabel[stamme]
    return None


def del_sammensat(ord_):
    """Forsøger at dele et sammensat ord i to kendte dele.

    Dansk sætter ord sammen uden mellemrum, så "flodhest" står ikke i nogen
    frekvensliste, selvom både "flod" og "hest" gør. Returnerer (venstre,
    højre) hvis begge dele er kendte ord, ellers None.

    Der deles ved det snit, hvor den sværeste af de to dele er lettest -
    det giver den mest sandsynlige opdeling frem for den første, der passer.
    """
    ord_ = (ord_ or '').lower()
    if len(ord_) < _MIN_DEL * 2:
        return None

    bedste = None
    bedste_score = None
    for i in range(_MIN_DEL, len(ord_) - _MIN_DEL + 1):
        venstre = ord_[:i]
        v_baand = _slaa_op(venstre)
        if v_baand is None:
            continue
        for binde in _BINDEBOGSTAVER:
            if binde and not venstre.endswith(binde):
                continue
            # Med bindebogstav hører det til venstre del og skal ikke med i højre.
            hoejre = ord_[i:]
            if len(hoejre) < _MIN_DEL:
                continue
            h_baand = _slaa_op(hoejre)
            if h_baand is None:
                continue
            score = max(v_baand, h_baand)
            if bedste_score is None or score < bedste_score:
                bedste_score = score
                bedste = (venstre, hoejre)
    return bedste


def svaerhedsgrad(ord_):
    """Sværhedsbånd 1-5 for ét ord. 1 er lettest.

    Rækkefølgen er: direkte opslag, opslag på stammen, opdeling af
    sammensætning, og ellers bånd 5. Lange ord løftes et bånd, fordi
    længden i sig selv koster for en læser, der stadig lyder ordene.
    """
    ord_ = (ord_ or '').strip().lower()
    if not ord_:
        return BAAND_SVAEREST

    baand = _slaa_op(ord_)

    if baand is None:
        dele = del_sammensat(ord_)
        if dele:
            # Et sammensat ord er sværere end sine dele: barnet skal både
            # afkode delene og se, at de hører sammen.
            baand = min(BAAND_SVAEREST, max(svaerhedsgrad(d) for d in dele) + 1)
        else:
            baand = BAAND_SVAEREST

    # Længden lægger oveni, uafhængigt af hvor hyppigt ordet er.
    if len(ord_) >= 12:
        baand = min(BAAND_SVAEREST, baand + 1)

    return baand


def analyser_tekst(tekst):
    """Fordeler en teksts ord på sværhedsbånd.

    Returnerer en dict med det samlede antal ord, fordelingen på bånd, og
    de ord der ligger i de to sværeste bånd - det er dem, der er værd at
    forberede et barn på, eller at følge op på bagefter.
    """
    ord_ = ord_i_tekst(tekst)
    if not ord_:
        return {'antal_ord': 0, 'fordeling': {}, 'svaere_ord': [], 'gennemsnit': 0.0}

    fordeling = {}
    svaere = {}
    sum_baand = 0
    for o in ord_:
        b = svaerhedsgrad(o)
        sum_baand += b
        fordeling[b] = fordeling.get(b, 0) + 1
        if b >= 4:
            svaere.setdefault(normaliser(o), o)

    return {
        'antal_ord': len(ord_),
        'fordeling': fordeling,
        'svaere_ord': sorted(svaere.values()),
        'gennemsnit': round(sum_baand / len(ord_), 2),
    }


def nye_ord(tekst, kendte_stammer):
    """De ord i teksten, barnet ikke har mødt før.

    'kendte_stammer' er de normaliserede ord fra barnets ordbank. Bruges
    til at vise en lærer, hvad en ny tekst faktisk introducerer.
    """
    kendte = set(kendte_stammer or ())
    set_ord = {}
    for o in ord_i_tekst(tekst):
        stamme = normaliser(o)
        if stamme and stamme not in kendte and stamme not in set_ord:
            set_ord[stamme] = o
    return sorted(set_ord.values())
