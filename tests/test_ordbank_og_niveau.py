# Fil: tests/test_ordbank_og_niveau.py
"""Test af ordbank-servicen og den adaptive niveau-algoritme.

Køres med:  python -m pytest tests/ -q
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.word_service import (  # noqa: E402
    analyser_tekst, del_sammensat, normaliser, nye_ord, ord_i_tekst, svaerhedsgrad,
    BAAND_SVAEREST,
)
from services.level_service import (  # noqa: E402
    MAKS_NIVEAU, MIN_NIVEAU, STANDARD_NIVEAU, STOR_SPREDNING,
    foreslaa_niveau, startniveau,
)


# --------------------------------------------------------------------
# Ordnormalisering
# --------------------------------------------------------------------

@pytest.mark.parametrize("boejninger", [
    ["hest", "hesten", "heste", "hestene"],
    ["løb", "løber", "løbende"],
    ["myre", "myren", "myrer", "myrerne"],
    ["blad", "bladet", "blade"],
])
def test_boejninger_samles_til_én_stamme(boejninger):
    """En ordbank skal vide, at 'hesten' og 'heste' er samme ord."""
    assert len({normaliser(o) for o in boejninger}) == 1


def test_normaliser_taaler_tomt_input():
    assert normaliser("") == ""
    assert normaliser(None) == ""


# --------------------------------------------------------------------
# Ordudtræk
# --------------------------------------------------------------------

def test_tegnsaetning_fjernes_men_bindestreg_bevares():
    ord_ = ord_i_tekst("Far-far sagde: \"Kom nu!\" (klokken 8).", medtag_stopord=True)
    assert "far-far" in ord_
    assert "kom" in ord_
    assert not any(char.isdigit() for o in ord_ for char in o)


def test_stopord_udelades_som_standard():
    ord_ = ord_i_tekst("Det er en kat i haven")
    assert "kat" in ord_ and "haven" in ord_
    for stop in ("det", "er", "en", "i"):
        assert stop not in ord_


# --------------------------------------------------------------------
# Sværhedsgrad
# --------------------------------------------------------------------

def test_almindelige_ord_er_lettere_end_sjaeldne():
    assert svaerhedsgrad("hund") < svaerhedsgrad("besætningen")


def test_lix_blindhed_afdaekkes():
    """LIX ser kun ordlængde. Begge er lange; kun det ene er svært."""
    assert len("hyggeligt") == 9 and len("kollektivt") == 10
    assert svaerhedsgrad("hyggeligt") < svaerhedsgrad("kollektivt")


def test_ukendt_ord_faar_svaereste_baand():
    assert svaerhedsgrad("qwertyuiopasdf") == BAAND_SVAEREST


def test_tomt_ord_haandteres():
    assert svaerhedsgrad("") == BAAND_SVAEREST
    assert svaerhedsgrad(None) == BAAND_SVAEREST


def test_meget_langt_ord_loeftes_et_baand():
    """Længden koster i sig selv for en læser, der stadig lyder ordene."""
    assert svaerhedsgrad("undersøgelsesskibet") >= 4


# --------------------------------------------------------------------
# Sammensatte ord - dansk sætter ord sammen uden mellemrum
# --------------------------------------------------------------------

@pytest.mark.parametrize("ord_, dele", [
    ("flodhest", ("flod", "hest")),
    ("sommerfugl", ("sommer", "fugl")),
    ("regnbue", ("regn", "bue")),
])
def test_sammensatte_ord_deles_korrekt(ord_, dele):
    assert del_sammensat(ord_) == dele


def test_bindebogstav_haandteres():
    """'fødselsdag' = fødsel + s + dag."""
    dele = del_sammensat("fødselsdag")
    assert dele is not None
    assert dele[1] == "dag"


def test_korte_ord_deles_ikke():
    assert del_sammensat("kat") is None
    assert del_sammensat("hus") is None


def test_ukendt_sammensaetning_er_svaerere_end_sine_dele():
    """Et sammensat ord koster ekstra: barnet skal både afkode delene og
    se, at de hører sammen.

    Reglen gælder kun ord, der ikke allerede er kendte i sig selv.
    "fødselsdag" står i frekvenslisten og "flodhest" på appens egen
    elementliste, så begge slås direkte op. "skovsti" gør ingen af delene
    og går derfor den vej, testen her handler om.
    """
    dele = del_sammensat("skovsti")
    assert dele == ("skov", "sti")
    assert svaerhedsgrad("skovsti") > max(svaerhedsgrad(d) for d in dele)


def test_sammensaetning_af_ukendte_dele_giver_svaereste_baand():
    """Kan ingen af delene genkendes, er der intet at bygge på."""
    assert svaerhedsgrad("zxcvbnmasdfgh") == BAAND_SVAEREST


def test_appens_egne_sammensaetninger_straffes_ikke():
    assert svaerhedsgrad("flodhest") <= 3


# --------------------------------------------------------------------
# Appens eget ordforråd
# --------------------------------------------------------------------

@pytest.mark.parametrize("ord_", ["myre", "dovendyr", "enhjørning", "blæksprutte", "flodhest"])
def test_appens_egne_elementord_er_ikke_svaere(ord_):
    """Appen må ikke markere sine egne forslag som svære ord."""
    assert svaerhedsgrad(ord_) <= 3


# --------------------------------------------------------------------
# Tekstanalyse
# --------------------------------------------------------------------

def test_svaer_tekst_scorer_hoejere_end_let():
    let = "Myren er lille. Den går på en sti. Katten sover i solen ved huset."
    svaer = ("Undersøgelsesskibet forlod havnen ledsaget af en usædvanlig mild vind, "
             "som besætningen fortolkede som et gunstigt varsel for ekspeditionen.")
    assert analyser_tekst(svaer)['gennemsnit'] > analyser_tekst(let)['gennemsnit']


def test_svaere_ord_udpeges():
    a = analyser_tekst("Besætningen fortolkede vinden som et gunstigt varsel.")
    assert "fortolkede" in a['svaere_ord']


def test_tom_tekst_giver_nuller():
    a = analyser_tekst("")
    assert a['antal_ord'] == 0 and a['svaere_ord'] == []


def test_nye_ord_udelader_kendte():
    kendte = {normaliser(o) for o in ["kat", "hus"]}
    nye = nye_ord("Katten sad ved huset og så på fuglen.", kendte)
    assert "fuglen" in nye
    assert not any(normaliser(o) in kendte for o in nye)


# --------------------------------------------------------------------
# Startniveau
# --------------------------------------------------------------------

def test_startniveau_stiger_med_alderen():
    assert startniveau(6) < startniveau(9) < startniveau(12)


def test_startniveau_uden_alder():
    assert startniveau(None) == STANDARD_NIVEAU
    assert startniveau("ikke et tal") == STANDARD_NIVEAU


# --------------------------------------------------------------------
# Adaptivt niveau
# --------------------------------------------------------------------

def _laesning(lix, quiz=None, dag=1):
    return {'lix': lix, 'quiz_pct': quiz, 'dato': f'2026-01-{dag:02d}'}


def test_uden_historik_gives_et_udgangspunkt():
    r = foreslaa_niveau([], alder=7)
    assert r['niveau'] == startniveau(7)
    assert r['grundlag'] == 0
    assert r['begrundelse']


def test_én_god_quiz_flytter_ikke_niveauet():
    """Træghed: et barn kan have en god eller dårlig dag."""
    r = foreslaa_niveau([_laesning(20, 100, 1)])
    assert r['aendring'] == 0
    assert r['niveau'] == 20


def test_to_gode_quizzer_i_traek_rykker_op():
    r = foreslaa_niveau([_laesning(20, 85, 1), _laesning(20, 85, 2)])
    assert r['aendring'] > 0
    assert r['niveau'] > 20


def test_to_daarlige_quizzer_i_traek_rykker_ned():
    r = foreslaa_niveau([_laesning(30, 40, 1), _laesning(30, 45, 2)])
    assert r['aendring'] < 0
    assert r['niveau'] < 30


def test_perfekte_scorer_rykker_mere_end_gode():
    god = foreslaa_niveau([_laesning(20, 82, 1), _laesning(20, 84, 2)])
    perfekt = foreslaa_niveau([_laesning(20, 95, 1), _laesning(20, 100, 2)])
    assert perfekt['aendring'] > god['aendring']


def test_blandet_resultat_holder_niveauet():
    """En passende udfordring skal ikke flytte noget."""
    r = foreslaa_niveau([_laesning(25, 90, 1), _laesning(25, 55, 2)])
    assert r['aendring'] == 0


def test_stor_spredning_forklares_aerligt():
    """90% efterfulgt af 30% er ikke "en passende udfordring" - det er
    to resultater, der peger hver sin vej. Begrundelsen skal sige det,
    ellers holder en lærer op med at stole på tallet."""
    r = foreslaa_niveau([_laesning(22, 90, 1), _laesning(22, 30, 2)])
    assert r['aendring'] == 0
    assert "svinger" in r['begrundelse']
    assert "passende udfordring" not in r['begrundelse']


def test_én_daarlig_dag_efter_gode_resultater_rykker_ikke_ned():
    r = foreslaa_niveau([_laesning(25, 90, 1), _laesning(25, 95, 2), _laesning(25, 30, 3)])
    assert r['aendring'] == 0


def test_niveauet_holder_sig_inden_for_sliderens_graenser():
    op = foreslaa_niveau([_laesning(MAKS_NIVEAU, 100, 1), _laesning(MAKS_NIVEAU, 100, 2)])
    ned = foreslaa_niveau([_laesning(MIN_NIVEAU, 10, 1), _laesning(MIN_NIVEAU, 15, 2)])
    assert op['niveau'] <= MAKS_NIVEAU
    assert ned['niveau'] >= MIN_NIVEAU


def test_graensen_forklares_naar_der_ikke_kan_rykkes_laengere():
    r = foreslaa_niveau([_laesning(MAKS_NIVEAU, 100, 1), _laesning(MAKS_NIVEAU, 100, 2)])
    assert r['aendring'] == 0
    assert "højeste" in r['begrundelse']


def test_historik_sorteres_efter_dato_ikke_raekkefoelge():
    rod = [_laesning(30, 45, 3), _laesning(20, 90, 1), _laesning(20, 95, 2)]
    r = foreslaa_niveau(rod)
    assert r['forrige'] == 30   # den nyeste efter dato


def test_laesninger_uden_quiz_taeller_ikke_med():
    r = foreslaa_niveau([_laesning(20, None, 1), _laesning(20, None, 2), _laesning(20, 90, 3)])
    assert r['aendring'] == 0
    assert r['grundlag'] == 1


def test_hvert_forslag_har_en_begrundelse():
    for historik in ([], [_laesning(20, 90, 1)],
                     [_laesning(20, 90, 1), _laesning(20, 95, 2)],
                     [_laesning(30, 20, 1), _laesning(30, 25, 2)]):
        r = foreslaa_niveau(historik)
        assert r['begrundelse'] and r['begrundelse'][0].isupper()
