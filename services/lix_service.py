# Fil: services/lix_service.py
import re

def calculate_lix(text: str) -> int:
    """
    Beregner LIX-tallet (Læsbarhedsindeks) for en given tekst.

    LIX-tallet er et mål for en teksts læsbarhed og beregnes ud fra den
    gennemsnitlige sætningslængde og procentdelen af lange ord.

    Formel: LIX = (antal ord / antal sætninger) + (antal lange ord * 100 / antal ord)

    Args:
        text: Den tekststreng, der skal analyseres.

    Returns:
        Et afrundet heltal, der repræsenterer LIX-tallet.
        Returnerer 0, hvis teksten er tom, eller hvis en beregning ikke er mulig.
    """
    if not text or not text.strip():
        return 0

    # 1. Tæl ord
    # Splitter på alle whitespace-karakterer (mellemrum, tab, linjeskift)
    words = text.split()
    num_words = len(words)

    if num_words == 0:
        return 0

    # 2. Tæl sætninger
    # En sætning defineres som en tekststreng, der afsluttes med '.', '!' eller '?'.
    # Vi bruger re.split til at splitte på et eller flere af disse tegn.
    sentences = re.split(r'[.!?]+', text)
    # Fjerner tomme strenge, som kan opstå, hvis teksten f.eks. slutter med et punktum.
    num_sentences = len([s for s in sentences if s.strip()])

    # Edge case: Hvis der ingen sætningsafsluttende tegn er, betragtes hele teksten som én sætning.
    if num_sentences == 0:
        num_sentences = 1

    # 3. Tæl lange ord
    # Et "langt ord" defineres typisk som et ord med mere end 6 bogstaver.
    # Vi fjerner tegnsætning fra ordet for en mere præcis længde-tælling.
    long_words = [word for word in words if len(re.sub(r'[\W_]+', '', word)) > 6]
    num_long_words = len(long_words)

    # 4. Beregn LIX-scoren
    try:
        # LIX = (gennemsnitlig sætningslængde) + (procentdel af lange ord)
        lix_score = (num_words / num_sentences) + (num_long_words * 100 / num_words)
        return round(lix_score)
    except ZeroDivisionError:
        # Dette burde ikke ske pga. vores tjek ovenfor, men er en god sikkerhedsforanstaltning.
        return 0