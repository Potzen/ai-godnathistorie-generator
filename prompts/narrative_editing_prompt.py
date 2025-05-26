# Fil: prompts/narrative_editing_prompt.py

def build_narrative_editing_prompt(
    story_draft_title: str,
    story_draft_content: str,
    original_user_inputs: dict, # Indeholder f.eks. barnets alder, ønsket stemning, længde
    # Trin 2 genererer nu også refleksionsspørgsmål, men redaktøren fokuserer på historien.
):
    """
    Bygger prompten for Trin 3 AI (Redaktør-AI), der skal finpudse
    et eksisterende historieudkast.

    Args:
        story_draft_title (str): Titlen på historieudkastet fra Trin 2.
        story_draft_content (str): Selve historieudkastet fra Trin 2.
        original_user_inputs (dict): De oprindelige brugerinput, som kan give
                                     kontekst om f.eks. barnets alder, ønsket
                                     stemning og længde.
    Returns:
        str: Den færdigbyggede prompt-streng til Redaktør-AI'en.
    """
    prompt_parts = [
        "SYSTEM INSTRUKTION: Du er en yderst dygtig og kreativ AI-redaktør med speciale i børnelitteratur. Din opgave er at tage et eksisterende historieudkast og finpudse det sprogligt og stilistisk, så det bliver en endnu bedre læseoplevelse. Du skal IKKE ændre de grundlæggende narrative eller terapeutiske intentioner fra udkastet, men forbedre flow, sprog, og engagement.",
        "Outputtet skal starte med den (potentielt reviderede) TITEL på den allerførste linje. Efter titlen, indsæt ET ENKELT LINJESKIFT, og start derefter selve den reviderede historietekst. Returner KUN titel og historietekst.",
        "---"
    ]

    prompt_parts.append("DEL 1: HISTORIEUDKAST TIL REDIGERING (FRA FORRIGE AI TRIN):")
    prompt_parts.append(f"TITEL PÅ UDKAST: \"{story_draft_title}\"")
    prompt_parts.append("HISTORIEUDKAST:")
    prompt_parts.append(story_draft_content)
    prompt_parts.append("---")

    prompt_parts.append("DEL 2: KONTEKST FRA OPRINDELIGE BRUGERINPUT (Respekter disse rammer):")
    child_age_info = original_user_inputs.get('child_age', 'ukendt alder')
    story_length_info = original_user_inputs.get('length', 'mellem') # Matcher story_routes.py og modulbeskrivelse
    story_mood_info = original_user_inputs.get('mood', 'neutral') # Matcher story_routes.py og modulbeskrivelse
    negative_prompt_info = original_user_inputs.get('negative_prompt', '')

    prompt_parts.append(f"- Målgruppe: Børn omkring {child_age_info}.")
    prompt_parts.append(f"- Ønsket Længde: Cirka '{story_length_info}'. Dit output skal matche denne længde.")
    prompt_parts.append(f"- Ønsket Stemning: '{story_mood_info}'. Bevar denne stemning.")
    if negative_prompt_info:
        prompt_parts.append(f"- Må IKKE indeholde: {negative_prompt_info}")
    prompt_parts.append("---")

    prompt_parts.append("DEL 3: DIN OPGAVE SOM REDAKTØR-AI:")
    prompt_parts.append(
        "1.  **Sproglig Finpudsning:** Forbedr sproget, så det er flydende, levende og alderssvarende. Ret eventuelle grammatiske fejl, klodsede formuleringer eller gentagelser i udkastet.")
    prompt_parts.append(
        "2.  **Stilistisk Forbedring:** Gør historien mere engagerende. Overvej rytme, ordvalg, og brug af sanselige detaljer. Styrk metaforer eller billedsprog, hvis det er passende, uden at ændre kernen.")
    prompt_parts.append(
        "3.  **Bevare Intentioner:** Meget vigtigt: Du skal FORHOLDE DIG TÆT til historieudkastets narrative og pædagogiske/terapeutiske intentioner. Din rolle er at implementere disse intentioner trofast og forbedre præsentationen, IKKE at fortolke, tilføje nye plot-elementer eller afvige markant fra det leverede udkast. Kernen af historien, dens budskaber og de narrative teknikker (som eksternalisering, brug af styrker osv.) der allerede er i udkastet, skal bevares.")
    prompt_parts.append(
        "4.  **Sammenhæng og Flow:** Sikr, at historien er sammenhængende og har et godt flow fra start til slut.")
    prompt_parts.append(
        "5.  **Variation (Vigtigt over tid):** Selvom du redigerer ET specifikt udkast nu, så stræb efter at bruge varieret sprogbrug, forskellige måder at beskrive følelser/scener på, og undgå klichéer. Dette hjælper med at forhindre, at historier med lignende temaer lyder ens over tid. Brug din kreativitet til at finde friske måder at udtrykke tingene på inden for rammerne af udkastet.")
    prompt_parts.append(
        "6.  **Titel:** Gennemgå den oprindelige titel. Hvis du kan forbedre den, så den er mere fængende og passer bedre til den redigerede historie, må du gerne justere den. Ellers behold den oprindelige.")
    prompt_parts.append(
        "7.  **Format:** Returner KUN den endelige, redigerede titel og historietekst, formateret som specificeret i systeminstruktionen (titel på første linje, enkelt linjeskift, derefter historietekst).")

    return "\n\n".join(prompt_parts)

# Eksempel på hvordan funktionen kan kaldes (til test)
if __name__ == '__main__':
    example_draft_title = "Den Lille Sky, Der Fandt Solen"
    example_draft_content = (
        "Der var engang en lille sky ved navn Pjuske. Pjuske var ofte lidt trist, fordi de store skyer drillede ham.\n"
        "De sagde, han var for lille til at lave regn. 'Du er bare en tågedot,' fnisede Tordenskyen Thor.\n"
        "En dag besluttede Pjuske, at han ville finde solen. Han havde hørt, den kunne gøre alle glade. "
        "Han brugte sin lille vind-pust-styrke og svævede afsted. Det var en lang tur. "
        "Undervejs så han en UgleUlla, som så klog ud. 'Hvor er solen?' spurgte Pjuske. UgleUlla pegede med sin vinge. "
        "Til sidst fandt Pjuske solen, og den varmede ham, og han blev glad. De store skyer drillede ikke mere."
    )
    example_user_inputs = {
        'child_age': "5 år",
        'length': "kort",
        'mood': "håbefuld",
        'negative_prompt': "ingen farlige dyr"
    }

    editing_prompt = build_narrative_editing_prompt(
        story_draft_title=example_draft_title,
        story_draft_content=example_draft_content,
        original_user_inputs=example_user_inputs
    )
    print(editing_prompt)