# Fil: tests/test_laeseunivers.py
"""Test af fokus-lyd, ugens fokus, ordbanken og hjemmelæsningsloggen.

Køres med:  python -m pytest tests/ -q
"""
import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('FLASK_SECRET_KEY', 'test')
os.environ.setdefault('GOOGLE_API_KEY', 'test')
os.environ.setdefault('GOOGLE_CLIENT_ID', 'test')
os.environ.setdefault('GOOGLE_CLIENT_SECRET', 'test')

from services.phonics_service import (  # noqa: E402
    FORLYD, UDLYD, find_fokusord, forlydsklynge, maal_fokus, normaliser_fokus,
    prompt_instruktion, rammer, svaere_moenstre,
)


# =====================================================================
# Fokus-lyd
# =====================================================================

def test_positionen_er_det_der_afgoer_det():
    """Hele pointen: 'hest' indeholder s, men træner det ikke som forlyd."""
    assert rammer("sol", "s", FORLYD)
    assert not rammer("hest", "s", FORLYD)
    assert rammer("hus", "s", UDLYD)
    assert not rammer("sol", "s", UDLYD)


def test_fokus_input_ryddes_op():
    """Lærere skriver forskelligt. Alle former skal give det samme."""
    for skrivemaade in ["s, m", "s m", "S; M", "  s , m  "]:
        assert normaliser_fokus(skrivemaade) == ["s", "m"]


def test_dubletter_fjernes():
    assert normaliser_fokus("s, s, m") == ["s", "m"]


def test_tomt_fokus_giver_tom_liste():
    assert normaliser_fokus("") == []
    assert normaliser_fokus(None) == []
    assert normaliser_fokus("123 !!") == []


def test_fokus_accepterer_liste():
    assert normaliser_fokus(["sk", "br"]) == ["sk", "br"]


def test_maalt_fokus_skelner_god_fra_daarlig_tekst():
    """En bestilling er ikke en leveret tekst. Derfor måles der efter."""
    maalrettet = "Sol skinner på sandet. Sara sidder ved sin sæl og synger en sang."
    tilfaeldig = "Hesten løb over marken, og fuglene fløj hen over træerne."
    assert maal_fokus(maalrettet, "s", FORLYD)['andel'] > \
           maal_fokus(tilfaeldig, "s", FORLYD)['andel'] * 3


def test_daekning_viser_hvilke_lyde_der_mangler():
    """Bestiller man tre lyde og får to, skal det kunne ses."""
    m = maal_fokus("Sara sidder ved sin sæl. Bien brummer.", "s, b, m", FORLYD)
    assert m['pr_lyd']['s'] > 0
    assert m['pr_lyd']['b'] > 0
    assert m['pr_lyd']['m'] == 0
    assert m['daekning'] == pytest.approx(2 / 3, abs=0.01)


def test_samme_ord_taelles_kun_en_gang():
    m = maal_fokus("Sol sol sol sol.", "s", FORLYD)
    assert m['pr_lyd']['s'] == 1


def test_fokusord_returneres_saa_de_kan_vises():
    fundet = find_fokusord("Sara ser solen.", "s", FORLYD)
    assert set(fundet['s']) == {"sara", "ser", "solen"}


def test_tom_tekst_giver_nuller():
    m = maal_fokus("", "s", FORLYD)
    assert m['antal_ord'] == 0 and m['andel'] == 0.0


def test_uden_fokus_maales_der_ikke():
    m = maal_fokus("En helt almindelig tekst.", "", FORLYD)
    assert m['pr_lyd'] == {}


# =====================================================================
# Danske mønstre, et lyderende barn snubler over
# =====================================================================

@pytest.mark.parametrize("ord_", ["sol", "kat", "bil", "hus"])
def test_ligefremme_ord_flages_ikke(ord_):
    assert svaere_moenstre(ord_) == []


@pytest.mark.parametrize("ord_", ["hjul", "hvem", "mand", "bord", "øje", "sommer"])
def test_kendte_faldgruber_flages(ord_):
    assert svaere_moenstre(ord_)


def test_forlydsklynge_findes_og_er_laengst_mulig():
    """'str' skal vinde over 'st', ellers rammer øvelsen ved siden af."""
    assert forlydsklynge("strand") == "str"
    assert forlydsklynge("stol") == "st"
    assert forlydsklynge("sol") is None


# =====================================================================
# Prompt-instruktionen
# =====================================================================

def test_instruktionen_naevner_positionen():
    tekst = prompt_instruktion("s", FORLYD)
    assert "forlyd" in tekst
    assert "hest" in tekst      # eksemplet på hvad der IKKE tæller


def test_instruktionen_taler_ikke_om_udtale():
    """Den gamle formulering sagde 'øve udtalen'. Barnet øver afkodning."""
    assert "udtale" not in prompt_instruktion("s", FORLYD).lower()


def test_ingen_instruktion_uden_fokus():
    assert prompt_instruktion("", FORLYD) is None


# =====================================================================
# Endpoints
# =====================================================================

@pytest.fixture
def app(tmp_path):
    """En frisk app med sin egen database pr. test.

    Databasestien gives via en konfigurationsklasse og ikke via
    miljøvariabler: config.py læser miljøet, når klassen defineres, altså
    ved import. En ændring bagefter ville derfor ikke have nogen virkning,
    og alle tests ville dele den første tests database.
    """
    import logging
    logging.disable(logging.CRITICAL)
    from config import Config
    from app import create_app
    from extensions import db

    class TestConfig(Config):
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{tmp_path}/test.db'
        TESTING = True
        WTF_CSRF_ENABLED = False

    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
    return app


@pytest.fixture
def data(app):
    """En lærer, en klasse og to elever - den ene tilmeldt, den anden ikke."""
    from extensions import db
    from models import Classroom, ClassroomStudent, User
    with app.app_context():
        laerer = User(google_id='t', name='Lærer', email='l@x.dk', role='teacher')
        elev = User(google_id='e1', name='Emma', email='e@x.dk', role='basic')
        udenfor = User(google_id='e2', name='Noah', email='n@x.dk', role='basic')
        db.session.add_all([laerer, elev, udenfor])
        db.session.commit()
        klasse = Classroom(teacher_id=laerer.id, name='2.A', invite_code='ABC12345')
        db.session.add(klasse)
        db.session.commit()
        db.session.add(ClassroomStudent(classroom_id=klasse.id, student_user_id=elev.id))
        db.session.commit()
        return {'laerer': laerer.id, 'elev': elev.id, 'udenfor': udenfor.id, 'klasse': klasse.id}


def _log_ind(client, user_id):
    with client.session_transaction() as s:
        s['_user_id'] = str(user_id)
        s['_fresh'] = True


def test_laerer_kan_saette_ugens_fokus(app, data):
    c = app.test_client()
    _log_ind(c, data['laerer'])
    r = c.post(f"/focus/{data['klasse']}", json={
        'lyde': 's, m', 'position': 'forlyd',
        'besked_hjem': 'Vi øver s og m i denne uge.',
    })
    assert r.status_code == 200
    assert r.get_json()['fokus']['lyde'] == ['s', 'm']


def test_elev_ser_laererens_fokus_uden_at_kende_klassen(app, data):
    """Barnet skal bare vide, hvad der øves - ikke hvor det kommer fra."""
    c = app.test_client()
    _log_ind(c, data['laerer'])
    c.post(f"/focus/{data['klasse']}", json={'lyde': 'sk'})

    c2 = app.test_client()
    _log_ind(c2, data['elev'])
    svar = c2.get('/focus/mit').get_json()
    assert svar['fokus']['lyde'] == ['sk']


def test_elev_uden_klasse_faar_intet_fokus(app, data):
    """En familie, der bruger appen privat, skal ikke se en tom skole-boks."""
    c = app.test_client()
    _log_ind(c, data['udenfor'])
    assert c.get('/focus/mit').get_json()['fokus'] is None


def test_elev_kan_ikke_saette_fokus(app, data):
    c = app.test_client()
    _log_ind(c, data['elev'])
    assert c.post(f"/focus/{data['klasse']}", json={'lyde': 's'}).status_code == 403


def test_fremmed_klasse_er_lukket(app, data):
    from extensions import db
    from models import Classroom, User
    with app.app_context():
        anden = User(google_id='t2', name='Anden', email='a@x.dk', role='teacher')
        db.session.add(anden)
        db.session.commit()
        fremmed = Classroom(teacher_id=anden.id, name='3.B', invite_code='ZZZ99999')
        db.session.add(fremmed)
        db.session.commit()
        fremmed_id = fremmed.id
    c = app.test_client()
    _log_ind(c, data['laerer'])
    assert c.get(f'/focus/{fremmed_id}').status_code == 403


def test_fokus_kraever_indhold(app, data):
    c = app.test_client()
    _log_ind(c, data['laerer'])
    assert c.post(f"/focus/{data['klasse']}", json={'lyde': '', 'fokusord': []}).status_code == 400


def test_ugyldig_position_afvises(app, data):
    c = app.test_client()
    _log_ind(c, data['laerer'])
    r = c.post(f"/focus/{data['klasse']}", json={'lyde': 's', 'position': 'bagvendt'})
    assert r.status_code == 400


def test_fokus_overskrives_i_stedet_for_at_blive_dubleret(app, data):
    c = app.test_client()
    _log_ind(c, data['laerer'])
    c.post(f"/focus/{data['klasse']}", json={'lyde': 's'})
    c.post(f"/focus/{data['klasse']}", json={'lyde': 'm'})
    assert c.get(f"/focus/{data['klasse']}").get_json()['fokus']['lyde'] == ['m']


# =====================================================================
# Ordbanken
# =====================================================================

def test_ordbanken_fyldes_og_taeller_gensyn(app, data):
    from services import wordbank_service
    with app.app_context():
        f = wordbank_service.registrer_tekst(data['elev'], "Katten sad på måtten.")
        assert f['antal_nye' if 'antal_nye' in f else 'i_alt'] or f['nye']
        assert 'katten' in f['nye']

        # Samme ord igen tæller som gensyn, ikke som nyt
        igen = wordbank_service.registrer_tekst(data['elev'], "Katten sov videre.")
        assert 'katten' not in igen['nye']
        assert igen['gensete'] >= 1


def test_samme_ord_flere_gange_i_en_tekst_taeller_som_et_moede(app, data):
    from models import WordBankEntry
    from services import wordbank_service
    from services.word_service import normaliser
    with app.app_context():
        wordbank_service.registrer_tekst(data['elev'], "Kat kat kat kat kat.")
        post = WordBankEntry.query.filter_by(
            user_id=data['elev'], stamme=normaliser('kat')).first()
        assert post.antal_moeder == 1


def test_boejninger_samles_i_ordbanken(app, data):
    from services import wordbank_service
    with app.app_context():
        wordbank_service.registrer_tekst(data['elev'], "Hesten løb.")
        igen = wordbank_service.registrer_tekst(data['elev'], "Hestene løb.")
        assert not any('hest' in o for o in igen['nye'])


def test_ordbank_endpoint_svarer(app, data):
    from services import wordbank_service
    with app.app_context():
        wordbank_service.registrer_tekst(data['elev'], "Solen skinner over skoven.")
    c = app.test_client()
    _log_ind(c, data['elev'])
    svar = c.get('/ordbank/mit').get_json()
    assert svar['statistik']['ord_i_alt'] > 0


def test_tom_tekst_roerer_ikke_ordbanken(app, data):
    from services import wordbank_service
    with app.app_context():
        assert wordbank_service.registrer_tekst(data['elev'], "")['i_alt'] == 0
        assert wordbank_service.registrer_tekst(None, "Noget tekst")['i_alt'] == 0


# =====================================================================
# Hjemmelæsning
# =====================================================================

def test_foraelder_kan_kvittere_for_laesning(app, data):
    c = app.test_client()
    _log_ind(c, data['elev'])
    r = c.post('/hjemmelaesning/log', json={'laest_af': 'sammen', 'minutter': 20})
    assert r.status_code == 201
    assert c.get('/hjemmelaesning/log').get_json()['log'][0]['minutter'] == 20


def test_kvittering_uden_detaljer_er_nok(app, data):
    """Ét tryk skal være nok. Alt andet er frivilligt."""
    c = app.test_client()
    _log_ind(c, data['elev'])
    assert c.post('/hjemmelaesning/log', json={}).status_code == 201


def test_urimelige_vaerdier_afvises(app, data):
    c = app.test_client()
    _log_ind(c, data['elev'])
    assert c.post('/hjemmelaesning/log', json={'minutter': 5000}).status_code == 400
    assert c.post('/hjemmelaesning/log', json={'minutter': 'længe'}).status_code == 400
    assert c.post('/hjemmelaesning/log', json={'laest_af': 'naboen'}).status_code == 400


def test_man_kan_ikke_kvittere_paa_en_andens_historie(app, data):
    from extensions import db
    from models import Story
    with app.app_context():
        fremmed = Story(title='Andens', content='x', user_id=data['udenfor'])
        db.session.add(fremmed)
        db.session.commit()
        fremmed_id = fremmed.id
    c = app.test_client()
    _log_ind(c, data['elev'])
    assert c.post('/hjemmelaesning/log', json={'story_id': fremmed_id}).status_code == 404


def test_alt_kraever_login(app, data):
    c = app.test_client()
    for sti in ['/focus/mit', '/ordbank/mit', '/hjemmelaesning/log']:
        assert c.get(sti, headers={'Accept': 'application/json'}).status_code in (302, 401)


# =====================================================================
# Ruter
# =====================================================================

def test_hjemmelaesning_svarer(app):
    assert app.test_client().get('/hjemmelaesning').status_code == 200


def test_gammelt_hygge_link_virker_stadig(app):
    """Bogmærker og delte links må ikke knække ved en omdøbning."""
    r = app.test_client().get('/hygge')
    assert r.status_code == 301
    assert '/hjemmelaesning' in r.headers['Location']
