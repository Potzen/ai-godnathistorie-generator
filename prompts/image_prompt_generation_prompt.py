# Fil: prompts/image_prompt_generation_prompt.py

def build_image_prompt_generation_prompt(story_text):
    """
    Bygger den komplette prompt-streng, der sendes til Gemini
    for at generere en billedprompt til Vertex AI Imagen.
    INSTRUKTION OPDATERET: Tillader relevante voksne, forbyder strengt børn.
    Balancerer fokus mellem figurer og andre elementer.

    Args:
        story_text (str): Historieteksten, som billedprompten skal baseres på.

    Returns:
        str: Den færdigbyggede prompt-streng.
    """
    if not story_text or not story_text.strip():
        story_text_for_prompt = "en generel eventyrscene, med fokus på stemningsfulde omgivelser eller et karakteristisk dyr/objekt."
    else:
        story_text_for_prompt = story_text[:2000]

    prompt = (
        f"Opgave: Baseret på følgende danske historie, skal du skrive en **meget specifik og detaljeret visuel prompt på ENGELSK** (ca. 30-60 ord). "
        f"Denne engelske prompt skal bruges af AI billedgeneratoren Vertex AI Imagen og skal følge Googles bedste praksis for Imagen-prompts.\n\n"

        f"VIGTIGE INSTRUKTIONER TIL DEN **ENGELSKE** VISUELLE PROMPT, DU (GEMINI) SKAL GENERERE:\n\n"

        f"1.  **HOVEDMOTIV (Subject First & Clear):** Start den engelske prompt med en klar beskrivelse af det **mest centrale visuelle element** i den scene fra historien, du vælger at illustrere. "
        f"Hvis en **relevant VOKSEN figur** (se punkt 2) er det absolutte omdrejningspunkt for scenen, kan denne beskrives her. Ellers, eller som et vigtigt supplement, fokuser på dyr, magiske objekter, fantasi-væsener, eller stemningsfulde landskaber, der er centrale for historien. Vær bogstavelig.\n\n"

        f"2.  **HÅNDTERING AF MENNESKELIGE FIGURER (KRITISK!):**\n"
        f"    - **FORBUD MOD BØRN/MINDREÅRIGE:** Den engelske prompt må **ABSOLUT IKKE** indeholde beskrivelser af børn eller nogen form for mindreårige (undgå ALTID termer som 'child', 'children', 'kid', 'little girl', 'young boy', 'teenager', specifikke børnenavne osv.). Dette er for at sikre, at billedgeneratoren ikke blokerer outputtet.\n"
        f"    - **VOKSNE FIGURER (HVIS TYDELIGT CENTRALE OG BESKREVET I HISTORIEN):** Hvis en **VOKSEN** figur (f.eks. 'a mother', 'a king', 'an old wizard', 'a woman', 'a man') er *tydeligt beskrevet i den danske historie og er afgørende for den specifikke scene*, du ønsker at afbilde, KAN du inkludere en kortfattet, generisk beskrivelse af denne voksne figur og dens handlinger. Undgå unødvendige detaljer om den voksne, medmindre de er essentielle for scenen og tydeligt fremgår af historieteksten.\n"
        f"    - **BALANCE OG FOKUS:** Stræb efter en god balance. Selvom en relevant voksen kan inkluderes, skal du også give plads til beskrivelser af de vigtigste omgivelser, objekter, dyr eller den generelle stemning i scenen for at skabe et komplet og rigt billede. Hvis en scene fra historien effektivt kan illustreres *uden* at vise en voksen, men i stedet gennem symbolske elementer, karakteristiske objekter eller stemningsfulde omgivelser, er det ofte en foretrukken tilgang.\n\n"

        f"3.  **Handling og Interaktion:** Hvis relevant, beskriv tydeligt på engelsk, hvad de centrale subjekter (f.eks. voksne, dyr, objekter) gør, eller hvordan de interagerer med omgivelserne.\n\n"

        f"4.  **Omgivelser og Baggrund (Setting & Background):** Beskriv detaljeret stedet/baggrunden på engelsk. Inkluder vigtige elementer fra historien, der definerer scenen (f.eks. en månebelyst skov, en funklende sø, et hyggeligt rum).\n\n"

        f"5.  **Billedstil (Image Style - MEGET VIGTIGT):\n"
        f"    - Den engelske prompt skal ALTID afsluttes med en præcis stilbeskrivelse. Brug følgende kerneelementer i din engelske stilbeskrivelse: "
        f"'Style: Child-friendly high-quality 3D digital illustration, fairytale-like and imaginative.'\n\n"

        f"6.  **Klarhed og Orden (Clarity & Order):** Strukturen i den engelske prompt bør generelt være: Hovedmotiv(er) -> Handling (hvis relevant) -> Omgivelser/Detaljer -> Style.\n\n"

        f"7.  **Undgå (Avoid):** Ingen tekst i billedet. Ingen børn.\n\n"

        f"DANSK HISTORIE (læs denne for at forstå indholdet, som du så skal basere den engelske billedprompt på - husk de strenge regler for børn, men tillad relevante voksne, i din engelske prompt):\n{story_text_for_prompt}\n\n"

        f"GENERER NU DEN DETALJEREDE OG SPECIFIKKE **ENGELSKE** VISUELLE PROMPT TIL VERTEX AI IMAGEN (følg alle ovenstående instruktioner nøje, især punkt 2 om at undgå børn, men tillade relevante og centralt beskrevne voksne, samt vigtigheden af at inkludere andre visuelle elementer):"
    )
    return prompt