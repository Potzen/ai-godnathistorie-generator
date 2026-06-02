# Fil: prompts/image_prompt_generation_prompt.py

def build_image_prompt_generation_prompt(story_text, karakter_str, sted_str):
    """
    Bygger en forbedret prompt, der prioriterer brugerens originale input (karakterer og sted).
    """
    story_text_for_prompt = story_text[:2000] if story_text and story_text.strip() else "en generel eventyrscene."

    prompt = (
        f"Opgave: Skriv en specifik og detaljeret visuel prompt på **ENGELSK** til en AI billedgenerator. Prompten skal nøje følge reglerne og prioritere brugerens input.\n\n"

        f"**KRITISKE REGLER FOR DEN ENGELSKE PROMPT:**\n"
        f"1.  **PRIORITER BRUGER-INPUT:** Det absolut vigtigste er, at prompten afbilder de karakterer og det sted, som brugeren har specificeret. Brug historieteksten til at finde en passende handling eller stemning for disse elementer.\n"
        f"2.  **INGEN BØRN:** Den engelske prompt må **ALDRIG** indeholde beskrivelser af børn eller mindreårige (undgå 'child', 'kid', 'girl', 'boy' etc.). Voksne figurer er tilladt, hvis de er specificeret af brugeren.\n"
        f"3.  **STIL (Skal altid med til sidst):** Afslut altid den engelske prompt med: 'Style: a whimsical and enchanting fairytale illustration, high-quality 3D digital art, imaginative, soft lighting.'\n\n"
        f"--- **BRUGERENS SPECIFIKKE INPUT (HØJESTE PRIORITET)** ---\n"
        f"-   **Karakter(er):** {karakter_str}\n"
        f"-   **Sted:** {sted_str}\n\n"

        f"--- **HISTORIETEKST (TIL KONTEKST FOR HANDLING/STEMNING)** ---\n"
        f"{story_text_for_prompt}\n"
        f"---\n\n"

        f"GENERER NU DEN DETALJEREDE **ENGELSKE** VISUELLE PROMPT (Husk at prioritere karakter og sted):"
    )
    return prompt