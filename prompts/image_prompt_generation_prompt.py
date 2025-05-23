# Fil: prompts/image_prompt_generation_prompt.py

def build_image_prompt_generation_prompt(story_text):
    """
    Bygger den komplette prompt-streng, der sendes til Gemini
    for at generere en billedprompt til Vertex AI Imagen.

    Args:
        story_text (str): Historieteksten, som billedprompten skal baseres på.

    Returns:
        str: Den færdigbyggede prompt-streng.
    """
    if not story_text or not story_text.strip():
        # Håndter tom story_text, måske returner en generisk prompt-bygger-prompt
        # eller lad den kaldende funktion håndtere det. For nu, lad os bygge som før.
        story_text_for_prompt = "en generel eventyrscene for børn."
    else:
        story_text_for_prompt = story_text[:2000] # Begræns længden for at spare tokens

    prompt = (
        f"Opgave: Baseret på følgende danske historie, skal du skrive en **meget specifik og detaljeret visuel prompt på ENGELSK** (ca. 40-70 ord). "
        f"Denne engelske prompt skal bruges af AI billedgeneratoren Vertex AI Imagen og skal følge Googles bedste praksis for Imagen-prompts.\n\n"
        f"VIGTIGE INSTRUKTIONER TIL DEN **ENGELSKE** VISUELLE PROMPT, DU (GEMINI) SKAL GENERERE:\n"
        f"1.  **Hovedmotiv Først (Subject First & Clear):** Start ALTID med en klar **engelsk** beskrivelse af hovedperson(er), dyr eller centrale objekter. Vær bogstavelig for at undgå fejlfortolkning.\n"
        f"2.  **Handling og Interaktion (Action & Interaction):** Beskriv tydeligt på **engelsk**, hvad subjekt(erne) gør, og hvordan de interagerer.\n"
        f"3.  **Omgivelser og Baggrund (Setting & Background):** Beskriv Detaljer stedet/baggrunden på **engelsk**. Inkluder vigtige elementer fra historien, der definerer scenen.\n"
        f"4.  **Billedstil (Image Style - MEGET VIGTIGT - skal ligne en poleret 3D animationsfilm scene):\n"
        f"    - Den **engelske** prompt skal ALTID afsluttes med en præcis stilbeskrivelse. Oversæt og brug følgende kerneelementer i din **engelske** stilbeskrivelse: "
        f"'Style: Child-friendly high-quality 3D digital illustration, fairytale-like and imaginative.'\n"
        # Punkt 5 mangler i din originale prompt-tekst.
        f"6.  **Klarhed og Orden (Clarity & Order):** Strukturen i den **engelske** prompt du genererer bør generelt være: Subject(s) -> Action -> Setting/Details -> Style.\n"
        f"7.  **Undgå (Avoid):** Ingen tekst i billedet.\n\n"
        f"DANSK HISTORIE (læs denne for at forstå indholdet, som du så skal basere den engelske billedprompt på):\n{story_text_for_prompt}\n\n"
        f"GENERER DEN DETALJEREDE OG SPECIFIKKE **ENGELSKE** VISUELLE PROMPT TIL VERTEX AI IMAGEN NU (følg alle ovenstående instruktioner nøje):"
    )
    return prompt