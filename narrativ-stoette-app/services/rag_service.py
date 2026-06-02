"""
RAG (Retrieval Augmented Generation) service.
Håndterer in-memory videnbase med narrative terapeutiske principper.
"""

import traceback
import numpy as np
from flask import current_app
import google.generativeai as genai

knowledge_base_data = []

INITIAL_KNOWLEDGE_CHUNKS = [
    {
        "id": "ext001",
        "text": "Externalisering: Et af narrativ terapiens mest magtfulde redskaber. Det handler om at hjælpe børn (og voksne) med at adskille et problem fra deres identitet – f.eks. at se 'vrede' som en 'vred trold', der kommer på besøg, i stedet for at barnet er vredt. Problemet gives en ydre form. Ved at gøre problemet til en ekstern enhed, bliver det noget, barnet kan tale om, reflektere over, og potentielt arbejde med eller endda 'kæmpe imod', i stedet for en indre, uoverkommelig del af sig selv. Dette reducerer skam og skyld og øger følelsen af handlekraft.",
        "embedding": None
    },
    {
        "id": "res001",
        "text": "Identifikation af Ressourcer og Styrker: Modulet fokuserer aktivt på at afdække og fremhæve barnets egne, ofte oversete, styrker, ressourcer og positive egenskaber. Hvert barn besidder unikke 'superkræfter' (f.eks. mod, venlighed, kreativitet, tålmodighed, nysgerrighed, humor), som kan mobiliseres i mødet med udfordringer. Historierne vil aktivt væve disse styrker ind i fortællingen som løsningsstrategier for hovedpersonen.",
        "embedding": None
    },
    {
        "id": "uniq001",
        "text": "Unikke Udfald (Unique Outcomes): Narrativ terapi søger aktivt efter 'unikke udfald' – de øjeblikke, hvor problemet ikke havde fuld magt, eller hvor barnet udviste modstand, mestring eller en alternativ, mere ønskværdig respons. Disse små sejre forstørres og væves ind i historien for at vise barnet, at problemet ikke altid vinder, og at de har evnen til at modstå det.",
        "embedding": None
    },
    {
        "id": "ext002_techniques",
        "text": "Teknikker til externalisering involverer at give problemet et navn (f.eks. 'Vredestrolden', 'Bekymrings-Skyggen', 'Generthedsskyggen') og beskrive dets karakteristika, adfærd og indflydelse. Dette hjælper barnet med at tale om problemet som en adskilt enhed, som man kan forholde sig til, forhandle med, eller endda 'bekæmpe'. Processen reducerer skam og skyld og fremmer barnets handlekraft.",
        "embedding": None
    },
    {
        "id": "uniq002_identification",
        "text": "For at identificere 'unikke udfald', spørg ind til tidspunkter, hvor problemet ikke dominerede, eller hvor barnet viste uventet modstand, styrke eller alternative handlinger. Forstærk disse 'små sejre' i fortællingen for at vise barnet, at problemet ikke er almægtigt, og at barnet besidder evnen til at modstå og handle anderledes.",
        "embedding": None
    },
    {
        "id": "reauth001_goal",
        "text": "Re-fortælling (re-authoring) handler om at skabe en ny, foretrukken livshistorie. Ved at væve externaliserede problemer, barnets ressourcer, og unikke udfald sammen, skabes en fortælling, der er mere positiv, styrkende og håbefuld. Målet er at skifte fokus fra en 'problem-mættet' til en 'løsnings- og styrke-mættet' narrativ, der øger barnets følelse af mestring og handlekraft (agency).",
        "embedding": None
    },
    {
        "id": "agency001_definition",
        "text": "Agency, eller handlekraft, er centralt i narrativ terapi. Det refererer til barnets evne til at påvirke sit eget liv og sine omgivelser. Historier bør fremhæve protagonistens (barnets spejling) evne til at træffe valg, handle aktivt og påvirke historiens gang, især i mødet med udfordringer.",
        "embedding": None
    },
    {
        "id": "devpsy001_metaphors",
        "text": "For yngre børn (ca. 3-7 år) er metaforer og konkretisering effektive redskaber. Komplekse følelser eller problemer kan gøres mere håndgribelige ved at blive repræsenteret som f.eks. dyr, fantasivæsener eller objekter. Dette hjælper barnet med at forstå og bearbejde oplevelser på en alderssvarende måde.",
        "embedding": None
    },
    {
        "id": "ped001_showdonttell",
        "text": "Når historier bruges pædagogisk, er princippet om 'show, don't tell' vigtigt. I stedet for direkte at belære eller moralisere, bør historien illustrere pointer og værdier gennem karakterernes handlinger, oplevelser og de konsekvenser, disse medfører. Moral og budskaber bør vokse organisk ud af fortællingen.",
        "embedding": None
    },
    {
        "id": "char001_problem_character",
        "text": "Ved design af en problem-karakter (eksternalisering), overvej dens Navn/Identitet (gør den distinkt), Rolle/Funktion (hvordan optræder den?), Formål/Intention (hvad 'vil' den?), Adfærd/Handling (hvordan agerer den konkret?), og Indflydelse (hvordan påvirker den hovedpersonen?). Disse træk hjælper med at gøre problemet håndterbart og mindre overvældende for barnet.",
        "embedding": None
    },
    {
        "id": "char002_protagonist_strengths",
        "text": "Fremhæv protagonistens (barnets spejling) Styrker, Værdier, Motivation/Ønsker, og Relationer. Disse positive egenskaber er ikke bare pynt, men aktive ressourcer, der kan mobiliseres i mødet med udfordringer, og som driver fortællingen mod positive unikke udfald og en styrket re-fortælling.",
        "embedding": None
    },
]


def initialize_knowledge_base(chunks=None):
    global knowledge_base_data
    knowledge_base_data = []

    chunks_to_process = chunks if chunks is not None else INITIAL_KNOWLEDGE_CHUNKS
    current_app.logger.info(f"RAG: Initialiserer videnbase med {len(chunks_to_process)} chunks...")

    for chunk in chunks_to_process:
        text = chunk.get("text")
        chunk_id = chunk.get("id", "unknown")
        if not text:
            continue
        embedding = get_text_embedding(text)
        if embedding:
            knowledge_base_data.append({"id": chunk_id, "text": text, "embedding": embedding})

    current_app.logger.info(f"RAG: Videnbase initialiseret med {len(knowledge_base_data)} elementer.")


def get_text_embedding(text_content: str, task_type="RETRIEVAL_DOCUMENT"):
    if not text_content or not text_content.strip():
        return None
    if not current_app.config.get('GOOGLE_API_KEY'):
        return None
    try:
        result = genai.embed_content(
            model="models/embedding-001",
            content=text_content,
            task_type=task_type,
        )
        return result['embedding']
    except Exception as e:
        current_app.logger.error(f"RAG: Embedding fejl: {e}\n{traceback.format_exc()}")
        return None


def cosine_similarity(vec1, vec2):
    if vec1 is None or vec2 is None:
        return 0.0
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (n1 * n2))


def find_relevant_chunks_v2(query_text: str, top_k: int = 3):
    if not knowledge_base_data or not query_text or not query_text.strip():
        return []

    query_embedding = get_text_embedding(query_text, task_type="RETRIEVAL_QUERY")
    if query_embedding is None:
        return []

    scored = []
    for item in knowledge_base_data:
        doc_emb = item.get('embedding')
        if doc_emb is None:
            continue
        score = cosine_similarity(query_embedding, doc_emb)
        scored.append({'text': item['text'], 'score': score})

    scored.sort(key=lambda x: x['score'], reverse=True)
    return [c['text'] for c in scored[:top_k] if c['score'] > 0.0]
