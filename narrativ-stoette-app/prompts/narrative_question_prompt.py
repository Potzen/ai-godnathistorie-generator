# Fil: prompts/narrative_question_prompt.py

def build_narrative_question_prompt(
    final_story_title: str,
    final_story_content: str,
    narrative_brief: str,
    original_user_inputs: dict  # Indeholder f.eks. barnets alder
):
    """
    Bygger prompten for Trin 4 AI (Spørgsmåls-AI), der skal generere
    refleksionsspørgsmål baseret på den endelige historie og det narrative brief.

    Args:
        final_story_title (str): Titlen på den færdigredigerede historie.
        final_story_content (str): Indholdet af den færdigredigerede historie.
        narrative_brief (str): Det oprindelige narrative brief fra Trin 1.
        original_user_inputs (dict): De oprindelige brugerinput for kontekst.

    Returns:
        str: Den færdigbyggede prompt-streng til Spørgsmåls-AI'en.
    """
    prompt_parts = [
        "SYSTEM INSTRUKTION: Du er en empatisk og pædagogisk AI-assistent med speciale i narrativ terapi og børns udvikling. Din opgave er at formulere 3-4 åbne, ikke-ledende refleksionsspørgsmål, der kan hjælpe en forælder med at starte en samtale med et barn efter at have læst den medfølgende historie. Spørgsmålene skal være alderssvarende og relateret til historiens temaer og protagonistens oplevelser, som beskrevet i det narrative brief og selve historien.",
        "Outputtet skal KUN være de genererede spørgsmål. Start hvert spørgsmål på en ny linje. Hvis du genererer to spørgsmål, skal de også være på separate linjer. Undgå nummerering eller punkttegn foran spørgsmålene i dit output.",
        "---"
    ]

    prompt_parts.append("DEL 1: DET NARRATIVE BRIEF (KONTEKST OM HISTORIENS FORMÅL OG BARNET):")
    prompt_parts.append("Dette brief beskriver det oprindelige fokus for historien og information om barnet:")
    prompt_parts.append(narrative_brief)
    prompt_parts.append("---")

    prompt_parts.append("DEL 2: DEN FÆRDIGE HISTORIE:")
    prompt_parts.append(f"TITEL: \"{final_story_title}\"")
    prompt_parts.append("HISTORIETEKST:")
    prompt_parts.append(final_story_content)
    prompt_parts.append("---")

    prompt_parts.append("DEL 3: DIN OPGAVE - GENERER REFLEKSIONSSPØRGSMÅL:")
    child_age_info = original_user_inputs.get('child_age', 'en ukendt alder')
    prompt_parts.append(f"Baseret på ovenstående brief (DEL 1) og den færdige historie (DEL 2), formuler nu 1 ELLER 2 (maksimalt to) åbne refleksionsspørgsmål. Husk at barnet er omkring {child_age_info}.")
    prompt_parts.append("Karakteristika for gode spørgsmål:")
    prompt_parts.append("   - **Åbne:** De skal ikke kunne besvares med et simpelt 'ja' eller 'nej'. Start gerne med 'Hvad tænker du om...', 'Hvordan tror du...', 'Hvad ville du gøre hvis...', 'Hvad følte [hovedpersonens navn] mon da...'.")
    prompt_parts.append("   - **Ikke-ledende:** Undgå at lægge ord i munden på barnet eller antyde et 'rigtigt' svar.")
    prompt_parts.append("   - **Relateret til historien og briefet:** Spørgsmålene skal tage udgangspunkt i historiens temaer, konflikter, løsninger eller hovedpersonens følelser og udvikling, som skitseret i briefet og udfoldet i historien.")
    prompt_parts.append("   - **Fremmer dialog:** Målet er at starte en nysgerrig og tryg samtale mellem forælder og barn.")
    prompt_parts.append("   - **Alderssvarende:** Brug et sprog, der er let at forstå for et barn i den angivne alder.")
    prompt_parts.append("   - **Fokuser på unikke udfald og re-authoring:** Hvis relevant, overvej spørgsmål der kan belyse øjeblikke hvor problemet ikke havde magt, eller hvordan hovedpersonen fandt nye måder at se sig selv eller situationen på.")

    prompt_parts.append("\nReturner KUN de 3-4 spørgsmål, hvert på en ny linje. INGEN ekstra tekst, INGEN nummerering eller punkttegn før spørgsmålene.")

    return "\n\n".join(prompt_parts)

# Eksempel på hvordan funktionen kan kaldes (til test)
if __name__ == '__main__':
    example_title = "Den Modige Mus Miko"
    example_content = "Miko var en lille mus, der var bange for mørke. En nat hjalp en venlig ugle ham med at se, at mørket også kunne være hyggeligt. Miko lærte at være modig."
    example_brief_text = """
STRUKTURERET OPSUMMERING AF BRUGERINPUT:
========================================
1. NARRATIVT FOKUS (TEMA/UDFORDRING):
   - Barn er bange for mørke.
2. ØNSKET UDVIKLING/MÅL FOR HISTORIEN:
   - At barnet føler sig mere tryg i mørke.
3. INFORMATION OM BARNET (PROTAGONISTENS UDGANGSPUNKT):
   - Navn: Leo
   - Alder: 5
   # ... (andre brief detaljer) ...
========================================
    """
    example_original_inputs_for_prompt = {
        'child_age': "5 år"
        # ... andre oprindelige input hvis nødvendigt for prompten ...
    }

    question_prompt = build_narrative_question_prompt(
        final_story_title=example_title,
        final_story_content=example_content,
        narrative_brief=example_brief_text,
        original_user_inputs=example_original_inputs_for_prompt
    )
    print(question_prompt)