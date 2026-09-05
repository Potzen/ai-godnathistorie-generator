# Fil: services/level_service.py
"""
Foreslår det næste læseniveau (LIX) ud fra barnets egen historik.

I dag vælger brugeren selv LIX-tallet på en slider. Det virker, når en
lærer sidder ved siden af, men det betyder også, at appen ikke lærer noget
af, hvordan det gik sidst.

Modulet her tager de data, appen allerede gemmer - historiernes målte
LIX-score og resultaterne fra læse-quizzen - og foreslår et niveau til
næste gang.

To principper styrer designet:

*Gennemsigtighed.* En lærer skal kunne se, hvorfor niveauet ændrede sig.
Derfor er det almindelige regler og ikke en model, og hvert forslag
kommer med en begrundelse i klar tekst.

*Træghed.* Et barn kan have en dårlig dag. Niveauet flytter sig derfor
først, når to målinger i træk peger samme vej, så det ikke svinger frem
og tilbage efter en enkelt quiz.
"""

from datetime import datetime

# Slideren i Læsehesten går fra 5 til 55, og forslaget skal holde sig der.
MIN_NIVEAU = 5
MAKS_NIVEAU = 55

# Startniveau, når vi intet ved om barnet endnu.
STANDARD_NIVEAU = 25

# Omtrentlige startniveauer efter alder. Kun et udgangspunkt - efter de
# første par historier er det barnets egne resultater, der bestemmer.
NIVEAU_EFTER_ALDER = [
    (6, 12), (7, 16), (8, 20), (9, 25), (10, 30), (11, 34), (12, 38),
]

# Hvor mange målinger der skal pege samme vej, før niveauet flytter sig.
KRAEVEDE_ENIGE = 2

# Grænser for, hvad en quiz-score betyder.
SIKKER_GRAENSE = 80      # Barnet forstod teksten uden besvær.
MEGET_SIKKER_GRAENSE = 90
USIKKER_GRAENSE = 50     # Teksten var for svær.
MEGET_USIKKER_GRAENSE = 35

# Ligger to på hinanden følgende quizzer længere fra hinanden end dette,
# siger de ikke noget entydigt om niveauet - og så skal begrundelsen sige
# netop det, i stedet for at kalde spredningen "en passende udfordring".
STOR_SPREDNING = 30


def _klem(niveau):
    return max(MIN_NIVEAU, min(MAKS_NIVEAU, int(round(niveau))))


def startniveau(alder=None):
    """Et rimeligt udgangspunkt, før barnet har læst noget i appen."""
    if alder is None:
        return STANDARD_NIVEAU
    try:
        alder = int(alder)
    except (TypeError, ValueError):
        return STANDARD_NIVEAU
    for grænse, niveau in NIVEAU_EFTER_ALDER:
        if alder <= grænse:
            return niveau
    return NIVEAU_EFTER_ALDER[-1][1]


def _sorter(historik):
    """Ældst først. Poster uden brugbart LIX-tal kasseres."""
    rene = []
    for post in historik or ():
        lix = post.get('lix')
        if lix is None:
            continue
        rene.append({
            'lix': int(lix),
            'quiz_pct': post.get('quiz_pct'),
            'dato': post.get('dato'),
        })

    def noegle(p):
        d = p.get('dato')
        if isinstance(d, datetime):
            return d
        if isinstance(d, str):
            try:
                return datetime.fromisoformat(d)
            except ValueError:
                return datetime.min
        return datetime.min

    return sorted(rene, key=noegle)


def foreslaa_niveau(historik, alder=None):
    """Foreslår næste LIX-niveau ud fra barnets læsehistorik.

    'historik' er en liste af poster med mindst 'lix', og gerne 'quiz_pct'
    (0-100) og 'dato'. Rækkefølgen er ligegyldig; der sorteres efter dato.

    Returnerer en dict med:
        niveau      - det foreslåede LIX-tal
        forrige     - niveauet på den seneste læste historie
        aendring    - forskellen, positiv hvis der rykkes op
        begrundelse - én sætning i klar tekst til læreren
        grundlag    - hvor mange quizresultater forslaget hviler på
    """
    poster = _sorter(historik)

    if not poster:
        niveau = startniveau(alder)
        return {
            'niveau': niveau,
            'forrige': None,
            'aendring': 0,
            'begrundelse': ("Der er endnu ingen historier at regne på. "
                            f"Forslaget er et udgangspunkt{' for alderen' if alder else ''}."),
            'grundlag': 0,
        }

    forrige = poster[-1]['lix']

    # Kun målinger med quizresultat siger noget om forståelsen.
    med_quiz = [p for p in poster if p.get('quiz_pct') is not None]
    seneste = med_quiz[-KRAEVEDE_ENIGE:]

    if len(seneste) < KRAEVEDE_ENIGE:
        return {
            'niveau': _klem(forrige),
            'forrige': forrige,
            'aendring': 0,
            'begrundelse': (f"Niveauet holdes på {forrige}. Der skal to quizresultater til, "
                            f"før det flytter sig, og der er indtil videre {len(med_quiz)}."),
            'grundlag': len(med_quiz),
        }

    scorer = [p['quiz_pct'] for p in seneste]
    laveste, hoejeste = min(scorer), max(scorer)
    vist = ' og '.join(f"{int(s)}%" for s in scorer)

    if laveste >= MEGET_SIKKER_GRAENSE:
        trin, tekst = 3, "Historierne er tydeligvis for lette"
    elif laveste >= SIKKER_GRAENSE:
        trin, tekst = 2, "Forståelsen sidder godt"
    elif hoejeste <= MEGET_USIKKER_GRAENSE:
        trin, tekst = -3, "Teksterne er for svære lige nu"
    elif hoejeste <= USIKKER_GRAENSE:
        trin, tekst = -2, "Forståelsen halter"
    elif hoejeste - laveste > STOR_SPREDNING:
        # Resultaterne peger hver sin vej. At kalde det en passende
        # udfordring ville være at læse mere ud af tallene, end de siger.
        return {
            'niveau': _klem(forrige),
            'forrige': forrige,
            'aendring': 0,
            'begrundelse': (f"Niveauet holdes på {forrige}. De seneste quizzer ({vist}) "
                            "svinger for meget til at sige noget entydigt endnu."),
            'grundlag': len(med_quiz),
        }
    else:
        return {
            'niveau': _klem(forrige),
            'forrige': forrige,
            'aendring': 0,
            'begrundelse': (f"Niveauet holdes på {forrige}. De seneste quizzer ({vist}) "
                            "viser en passende udfordring."),
            'grundlag': len(med_quiz),
        }

    nyt = _klem(forrige + trin)
    faktisk = nyt - forrige

    if faktisk == 0:
        kant = "laveste" if trin < 0 else "højeste"
        return {
            'niveau': nyt,
            'forrige': forrige,
            'aendring': 0,
            'begrundelse': (f"{tekst} ({vist}), men {forrige} er allerede det {kant} "
                            "niveau, appen tilbyder."),
            'grundlag': len(med_quiz),
        }

    retning = "op" if faktisk > 0 else "ned"
    return {
        'niveau': nyt,
        'forrige': forrige,
        'aendring': faktisk,
        'begrundelse': (f"{tekst} ({vist}), så niveauet rykkes {retning} "
                        f"fra {forrige} til {nyt}."),
        'grundlag': len(med_quiz),
    }
