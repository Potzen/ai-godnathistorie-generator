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
        f"Denne engelske prompt skal bruges af AI billedgeneratoren Vertex AI Imagen og skal følge nedenstående regler NØJAGTIGT.\n\n"

        f"VIGTIGE REGLER FOR DEN **ENGELSKE** VISUELLE PROMPT, DU SKAL GENERERE:\n\n"

        f"1.  **HÅNDTERING AF MENNESKELIGE FIGURER (KRITISK REGEL):**\n"
        f"    - **FORBUD MOD BØRN:** Den engelske prompt må **ABSOLUT IKKE** indeholde beskrivelser af børn eller mindreårige. Undgå ALTID termer som 'child', 'children', 'kid', 'little girl', 'young boy', 'teenager', eller specifikke børnenavne. Dette er for at overholde sikkerhedsfiltre.\n"
        f"    - **TILLADELSE TIL VOKSNE:** Du må gerne inkludere voksne figurer (f.eks. 'a king', 'a mother', 'an old wizard', 'a baker'), HVIS en voksen er tydeligt beskrevet og central for den scene i historien, du vælger at illustrere. Beskriv den voksnes handling, ikke kun udseende.\n"
        f"    - **FOKUS:** Selvom en voksen kan inkluderes, skal hovedfokus i prompten ofte være på et dyr, et magisk objekt eller et stemningsfuldt landskab for at skabe et rigt og interessant billede.\n\n"

        f"2.  **HOVEDMOTIV OG STRUKTUR:** Start den engelske prompt med det mest centrale visuelle element. Følg generelt strukturen: Hovedmotiv (kan være en voksen, et dyr eller et objekt) -> Handling -> Omgivelser/Detaljer -> Billedstil.\n\n"

        f"3.  **BILLEDSTIL (Skal altid med til sidst):** Den engelske prompt skal ALTID afsluttes med en præcis stilbeskrivelse. Brug følgende: "
        f"'Style: a whimsical and enchanting fairytale illustration, high-quality 3D digital art, imaginative, soft lighting.'\n\n"

        f"DANSK HISTORIE (Læs denne for at skabe den engelske prompt. Husk reglerne for menneskelige figurer):\n"
        f"---\n{story_text_for_prompt}\n---\n\n"

        f"GENERER NU DEN DETALJEREDE OG SPECIFIKKE **ENGELSKE** VISUELLE PROMPT (følg alle regler, især den nuancerede håndtering af voksne vs. børn):"
    )
    return prompt