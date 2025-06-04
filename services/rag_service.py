# Fil: services/rag_service.py
"""
Service modul for Retrieval Augmented Generation (RAG).
Dette modul håndterer oprettelse, vedligeholdelse og søgning i en
narrativ-terapeutisk videnbase.
"""

from flask import current_app
import google.generativeai as genai
import traceback
import numpy as np

# Global variabel til at holde vores simple in-memory videnbase.
# Hvert element kan f.eks. være en tuple: (original_text_chunk, embedding_vector)
# Eller en dictionary: {'text': original_text_chunk, 'embedding': embedding_vector}
knowledge_base_data = []

# Eksempel på tekst-chunks til videnbasen (vi udvider denne senere)
# Kilde: Modulbeskrivelse: Narrativ Støtte 25. maj
# Disse repræsenterer centrale narrative principper
INITIAL_KNOWLEDGE_CHUNKS = [
    {
        "id": "ext001",
        "text": "Externalisering: Et af narrativ terapiens mest magtfulde redskaber. Det handler om at hjælpe børn (og voksne) med at adskille et problem fra deres identitet – f.eks. at se 'vrede' som en 'vred trold', der kommer på besøg, i stedet for at barnet er vredt. Problemet gives en ydre form. Ved at gøre problemet til en ekstern enhed, bliver det noget, barnet kan tale om, reflektere over, og potentielt arbejde med eller endda 'kæmpe imod', i stedet for en indre, uoverkommelig del af sig selv. Dette reducerer skam og skyld og øger følelsen af handlekraft.",
        # [cite: 37, 38, 39, 40, 41, 42]
        "embedding": None  # Pladsholder for embedding
    },
    {
        "id": "res001",
        "text": "Identifikation af Ressourcer og Styrker: Modulet fokuserer aktivt på at afdække og fremhæve barnets egne, ofte oversete, styrker, ressourcer og positive egenskaber. Hvert barn besidder unikke 'superkræfter' (f.eks. mod, venlighed, kreativitet, tålmodighed, nysgerrighed, humor), som kan mobiliseres i mødet med udfordringer. Historierne vil aktivt væve disse styrker ind i fortællingen som løsningsstrategier for hovedpersonen.",
        # [cite: 43, 44, 45]
        "embedding": None  # Pladsholder for embedding
    },
    {
        "id": "uniq001",
        "text": "Unikke Udfald (Unique Outcomes): Narrativ terapi søger aktivt efter 'unikke udfald' – de øjeblikke, hvor problemet ikke havde fuld magt, eller hvor barnet udviste modstand, mestring eller en alternativ, mere ønskværdig respons. Disse små sejre forstørres og væves ind i historien for at vise barnet, at problemet ikke altid vinder, og at de har evnen til at modstå det.",
        # [cite: 46, 47]
        "embedding": None  # Pladsholder for embedding
    },
    {
        "id": "ext002_techniques",
        "text": "Teknikker til externalisering involverer at give problemet et navn (f.eks. 'Vredestrolden', 'Bekymrings-Skyggen', 'Generthedsskyggen') og beskrive dets karakteristika, adfærd og indflydelse. Dette hjælper barnet med at tale om problemet som en adskilt enhed, som man kan forholde sig til, forhandle med, eller endda 'bekæmpe'. Processen reducerer skam og skyld og fremmer barnets handlekraft.", # [cite: 247, 249, 322]
        "embedding": None
    },
    {
        "id": "uniq002_identification",
        "text": "For at identificere 'unikke udfald', spørg ind til tidspunkter, hvor problemet ikke dominerede, eller hvor barnet viste uventet modstand, styrke eller alternative handlinger. Forstærk disse 'små sejre' i fortællingen for at vise barnet, at problemet ikke er almægtigt, og at barnet besidder evnen til at modstå og handle anderledes.", # [cite: 253, 254, 322]
        "embedding": None
    },
    {
        "id": "reauth001_goal",
        "text": "Re-fortælling (re-authoring) handler om at skabe en ny, foretrukken livshistorie. Ved at væve externaliserede problemer, barnets ressourcer, og unikke udfald sammen, skabes en fortælling, der er mere positiv, styrkende og håbefuld. Målet er at skifte fokus fra en 'problem-mættet' til en 'løsnings- og styrke-mættet' narrativ, der øger barnets følelse af mestring og handlekraft (agency).", # [cite: 255, 256, 257]
        "embedding": None
    },
    {
        "id": "agency001_definition",
        "text": "Agency, eller handlekraft, er centralt i narrativ terapi. Det refererer til barnets evne til at påvirke sit eget liv og sine omgivelser. Historier bør fremhæve protagonistens (barnets spejling) evne til at træffe valg, handle aktivt og påvirke historiens gang, især i mødet med udfordringer.", # [cite: 256, 319]
        "embedding": None
    },
    {
        "id": "devpsy001_metaphors",
        "text": "For yngre børn (ca. 3-7 år) er metaforer og konkretisering effektive redskaber. Komplekse følelser eller problemer kan gøres mere håndgribelige ved at blive repræsenteret som f.eks. dyr, fantasivæsener eller objekter. Dette hjælper barnet med at forstå og bearbejde oplevelser på en alderssvarende måde.", # [cite: 320]
        "embedding": None
    },
    {
        "id": "ped001_showdonttell",
        "text": "Når historier bruges pædagogisk, er princippet om 'show, don't tell' vigtigt. I stedet for direkte at belære eller moralisere, bør historien illustrere pointer og værdier gennem karakterernes handlinger, oplevelser og de konsekvenser, disse medfører. Moral og budskaber bør vokse organisk ud af fortællingen.", # [cite: 321, 322]
        "embedding": None
    },
    {
        "id": "char001_problem_character",
        "text": "Ved design af en problem-karakter (eksternalisering), overvej dens Navn/Identitet (gør den distinkt), Rolle/Funktion (hvordan optræder den?), Formål/Intention (hvad 'vil' den?), Adfærd/Handling (hvordan agerer den konkret?), og Indflydelse (hvordan påvirker den hovedpersonen?). Disse træk hjælper med at gøre problemet håndterbart og mindre overvældende for barnet.", # [cite: 323, 324]
        "embedding": None
    },
    {
        "id": "char002_protagonist_strengths",
        "text": "Fremhæv protagonistens (barnets spejling) Styrker, Værdier, Motivation/Ønsker, og Relationer. Disse positive egenskaber er ikke bare pynt, men aktive ressourcer, der kan mobiliseres i mødet med udfordringer, og som driver fortællingen mod positive unikke udfald og en styrket re-fortælling.", # [cite: 250, 251, 252, 324]
        "embedding": None
    }
]


def initialize_knowledge_base(chunks=None):
    """
    Initialiserer (eller genindlæser) videnbasen.
    I denne simple version "embedder" vi tekst-chunks og gemmer dem.
    Senere vil dette involvere opsætning af en rigtig vector database.
    """
    global knowledge_base_data
    knowledge_base_data = [] # Nulstil for hver initialisering

    if chunks is None:
        chunks_to_process = INITIAL_KNOWLEDGE_CHUNKS
    else:
        chunks_to_process = chunks

    current_app.logger.info(f"RAG Service: Initialiserer videnbase med {len(chunks_to_process)} chunks...") # Denne log-linje er fin

    for chunk_dict in chunks_to_process:
        try:
            text_to_embed = chunk_dict.get("text")
            chunk_id = chunk_dict.get("id", "unknown_id")
            if not text_to_embed:
                current_app.logger.warning(f"RAG Service: Manglende tekst for chunk ID: {chunk_id}. Skipper.")
                continue

            embedding_vector = get_text_embedding(text_to_embed)

            if embedding_vector:
                knowledge_base_data.append({
                    "id": chunk_id,
                    "text": text_to_embed,
                    "embedding": embedding_vector
                })
                current_app.logger.debug(f"RAG Service: 'Embedded' og tilføjet chunk ID: {chunk_id}")
            else:
                current_app.logger.warning(f"RAG Service: Kunne ikke embedde tekst for chunk ID: {chunk_id}. Ikke tilføjet.")

        except Exception as e:
            current_app.logger.error(f"RAG Service: Fejl under initialisering af chunk: {chunk_dict.get('id', 'Ukendt ID')}: {e}\n{traceback.format_exc()}")

    current_app.logger.info(f"RAG Service: Videnbase initialiseret. Antal elementer: {len(knowledge_base_data)}")
    if not knowledge_base_data and chunks_to_process:
        current_app.logger.warning("RAG Service: Videnbasen er tom efter initialisering, selvom der var chunks at processere. Tjek embedding-logikken.")
    # DER SKAL IKKE VÆRE NOGEN REFERENCER TIL query_text ELLER find_relevant_chunks HER


def get_text_embedding(text_content: str, task_type="RETRIEVAL_DOCUMENT"):
    """
    Genererer et embedding for den givne tekst ved hjælp af Google's embedding model.

    Args:
        text_content (str): Teksten der skal embeddes.
        task_type (str): Typen af opgave for embedding.
                         Mulige værdier: "RETRIEVAL_QUERY", "RETRIEVAL_DOCUMENT",
                         "SEMANTIC_SIMILARITY", "CLASSIFICATION", "CLUSTERING".

    Returns:
        list: En liste af floats (embedding vector), eller None ved fejl.
    """
    if not text_content or not text_content.strip():
        current_app.logger.warning("RAG Service: get_text_embedding kaldt med tom tekst.")
        return None

    # Tjek om GOOGLE_API_KEY er sat, da genai.configure() afhænger af det.
    # genai skulle være konfigureret i create_app()
    if not current_app.config.get('GOOGLE_API_KEY'):
        current_app.logger.error("RAG Service: GOOGLE_API_KEY ikke konfigureret. Kan ikke generere embeddings.")
        # I en virkelig applikation vil vi måske kaste en fejl her eller have en fallback.
        # For nu returnerer vi None, så initialize_knowledge_base logger en advarsel.
        return None

    try:
        current_app.logger.debug(
            f"RAG Service: Anmoder om embedding for tekst (første 50 tegn): '{text_content[:50]}...'")
        # Modelnavn for text-embedding-004 (som specificeret i Vertex AI dokumentation)
        # Ifølge din requirements.txt (google-generativeai==0.8.4), kan vi bruge 'models/embedding-001'
        # eller 'models/text-embedding-004' hvis understøttet af API key'en og versionen.
        # Vi prøver med 'models/embedding-001' som er en mere generel model.
        # Hvis du specifikt vil have 'text-embedding-004', kan det kræve en opdatering
        # eller bekræftelse af, at din API-nøgle understøtter den direkte via genai.
        # Lad os bruge en simpel model først for at sikre flowet.
        result = genai.embed_content(
            model="models/embedding-001",  # Standard embedding model
            content=text_content,
            task_type=task_type
        )
        current_app.logger.info(
            f"RAG Service: Embedding genereret succesfuldt for tekst (første 50 tegn): '{text_content[:50]}...'")
        return result['embedding']
    except Exception as e:
        current_app.logger.error(
            f"RAG Service: Fejl under generering af embedding for tekst '{text_content[:50]}...': {e}\n{traceback.format_exc()}")
        return None


def cosine_similarity(vec1, vec2):
    """
    Beregner kosinus-ligheden mellem to vektorer.

    Args:
        vec1 (list or np.array): Den første vektor.
        vec2 (list or np.array): Den anden vektor.

    Returns:
        float: Kosinus-lighedsscoren, eller 0.0 hvis en fejl opstår (f.eks. nul-vektor).
    """
    if vec1 is None or vec2 is None:
        return 0.0

    # Konverter til numpy arrays, hvis de ikke allerede er det
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)

    # Tjek for nul-vektorer for at undgå division med nul
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)

    if norm_vec1 == 0 or norm_vec2 == 0:
        # Hvis en af vektorerne er en nul-vektor, er ligheden udefineret eller 0.
        # Vi returnerer 0 for at undgå fejl og for at indikere ingen lighed.
        return 0.0

    dot_product = np.dot(vec1, vec2)
    similarity = dot_product / (norm_vec1 * norm_vec2)
    return similarity


def find_relevant_chunks_v2(query_text: str, top_k: int = 3):
    """
    Finder de mest relevante tekst-chunks fra videnbasen baseret på en query
    ved hjælp af kosinus-lighed på embeddings.

    Args:
        query_text (str): Søgestrengen.
        top_k (int): Antallet af mest relevante chunks der skal returneres.

    Returns:
        list: En liste af de `top_k` mest relevante tekst-chunks (som strenge),
              sorteret efter relevans (højeste score først).
              Returnerer en tom liste, hvis ingen relevante chunks findes,
              eller hvis der opstår en fejl.
    """
    current_app.logger.info(f"RAG Service: Finder relevante chunks for query: '{query_text[:50]}...'") # UDEN (placeholder funktion)

    if not knowledge_base_data:
        current_app.logger.warning("RAG Service: Videnbasen er tom. Kan ikke finde relevante chunks.")
        return []

    if not query_text or not query_text.strip():
        current_app.logger.warning("RAG Service: find_relevant_chunks kaldt med tom query_text.")
        return []

    query_embedding = get_text_embedding(query_text, task_type="RETRIEVAL_QUERY")
    current_app.logger.debug(f"RAG Service: Query embedding for '{query_text[:20]}...': {query_embedding}")


    if query_embedding is None:
        current_app.logger.error("RAG Service: Kunne ikke generere embedding for query_text. Kan ikke finde chunks.")
        return []

    # Beregn lighedsscores for alle dokumenter i videnbasen
    scored_chunks = []
    for item in knowledge_base_data:
        doc_embedding = item.get('embedding')
        if doc_embedding is None:
            current_app.logger.warning(f"RAG Service: Manglende embedding for chunk ID: {item.get('id')}. Skipper.")
            continue

        score = cosine_similarity(query_embedding, doc_embedding)
        scored_chunks.append({
            'id': item.get('id'),
            'text': item.get('text'),
            'score': score
        })
        current_app.logger.debug(f"RAG Service: Score for chunk {item.get('id')}: {score:.4f}")

    # Sorter chunks efter score (højeste først)
    sorted_chunks = sorted(scored_chunks, key=lambda x: x['score'], reverse=True)

    # Returner teksten fra de top_k chunks
    relevant_texts = [chunk['text'] for chunk in sorted_chunks[:top_k] if chunk['score'] > 0.0]

    if not relevant_texts:
        current_app.logger.info(f"RAG Service: Ingen relevante chunks fundet (eller alle scores var 0) for query: '{query_text[:50]}...'")
    else:
        current_app.logger.info(f"RAG Service: Returnerer {len(relevant_texts)} relevante chunks.")

    return relevant_texts

# Eksempel på, hvordan man kan kalde initialize_knowledge_base ved app start.
# Dette bør dog nok ske fra create_app() i app.py for at sikre, at det sker i app context.
# def on_app_startup(app_instance):
#     with app_instance.app_context():
#          initialize_knowledge_base()