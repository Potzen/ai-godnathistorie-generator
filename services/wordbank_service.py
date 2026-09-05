# Fil: services/wordbank_service.py
"""
Vedligeholder barnets ordbank ud fra de historier, det læser.

Ordbanken er det, der gør appen bedre, jo mere den bliver brugt. Uden den
starter hver historie forfra: appen ved ikke, om barnet har set "skov" én
gang eller tyve, og kan derfor hverken fortælle læreren, hvad en ny tekst
introducerer, eller senere genbruge de ord, der stadig vakler.

Nøglen er ordstammen, ikke ordet som det stod. Se word_service.normaliser.
"""

from datetime import datetime

from extensions import db
from models import WordBankEntry
from services.word_service import normaliser, ord_i_tekst, svaerhedsgrad

# Hvor mange gange et ord skal være mødt, før vi regner det for kendt.
# Tallet er et skøn, ikke en måling: barnet kan sagtens kunne et ord fra
# første færd, og omvendt. Det bruges kun til at sortere en liste, aldrig
# til at afgøre noget om barnet.
MOEDER_FOR_KENDT = 3


def registrer_tekst(user_id, tekst, commit=True):
    """Tæller tekstens ord med i brugerens ordbank.

    Ord, der allerede står i banken, får tælleren og datoen opdateret;
    resten oprettes. Returnerer et resumé med de nye ord, så kaldet kan
    vise "denne historie introducerede 7 nye ord".
    """
    if not user_id or not tekst:
        return {'nye': [], 'gensete': 0, 'i_alt': 0}

    # Tæl forekomster pr. stamme i denne ene tekst, så et ord der optræder
    # fem gange i samme historie ikke tæller som fem møder.
    set_i_teksten = {}
    for o in ord_i_tekst(tekst):
        stamme = normaliser(o)
        if stamme and stamme not in set_i_teksten:
            set_i_teksten[stamme] = o

    if not set_i_teksten:
        return {'nye': [], 'gensete': 0, 'i_alt': 0}

    eksisterende = {
        e.stamme: e for e in WordBankEntry.query.filter(
            WordBankEntry.user_id == user_id,
            WordBankEntry.stamme.in_(list(set_i_teksten)),
        ).all()
    }

    nu = datetime.utcnow()
    nye = []
    for stamme, visningsform in set_i_teksten.items():
        post = eksisterende.get(stamme)
        if post:
            post.antal_moeder += 1
            post.sidst_set = nu
        else:
            db.session.add(WordBankEntry(
                user_id=user_id,
                stamme=stamme,
                visningsform=visningsform,
                baand=svaerhedsgrad(visningsform),
                antal_moeder=1,
                foerst_set=nu,
                sidst_set=nu,
            ))
            nye.append(visningsform)

    if commit:
        db.session.commit()

    return {
        'nye': sorted(nye),
        'gensete': len(set_i_teksten) - len(nye),
        'i_alt': len(set_i_teksten),
    }


def kendte_stammer(user_id):
    """Alle ordstammer, brugeren har mødt. Til opslag mod en ny tekst."""
    if not user_id:
        return set()
    rækker = db.session.query(WordBankEntry.stamme).filter_by(user_id=user_id).all()
    return {r[0] for r in rækker}


def vaklende_ord(user_id, antal=12):
    """Ord, barnet har mødt få gange, og som er værd at gense.

    Sorteret efter sværhed først og derefter efter, hvor sjældent ordet er
    mødt: de svære, sjældent sete ord er dem, en ny historie med fordel
    kan bringe tilbage.
    """
    if not user_id:
        return []
    poster = (WordBankEntry.query
              .filter(WordBankEntry.user_id == user_id,
                      WordBankEntry.antal_moeder < MOEDER_FOR_KENDT)
              .order_by(WordBankEntry.baand.desc().nullslast(),
                        WordBankEntry.antal_moeder.asc(),
                        WordBankEntry.sidst_set.asc())
              .limit(antal).all())
    return [p.visningsform for p in poster]


def statistik(user_id):
    """Kort overblik til en lærer eller forælder."""
    if not user_id:
        return {'ord_i_alt': 0, 'kendte': 0, 'vaklende': 0}
    i_alt = WordBankEntry.query.filter_by(user_id=user_id).count()
    kendte = WordBankEntry.query.filter(
        WordBankEntry.user_id == user_id,
        WordBankEntry.antal_moeder >= MOEDER_FOR_KENDT,
    ).count()
    return {'ord_i_alt': i_alt, 'kendte': kendte, 'vaklende': i_alt - kendte}
