# Fil: prompts/story_generation_prompt.py
from flask import current_app


def build_story_prompt(
        karakter_str,
        sted_str,
        plot_str,
        length_instruction,
        mood_prompt_part,
        listener_context_instruction,
        ending_instruction,
        negative_prompt_text,
        is_interactive=False,
        is_bedtime_story=False
):
    """
    Bygger den komplette prompt-streng til generering af en historie i Højtlæsnings-sektionen.
    """
    # Log de modtagne flag til debugging
    current_app.logger.info(
        f"--- build_story_prompt funktionen: Modtog is_interactive = {is_interactive}, is_bedtime_story = {is_bedtime_story} ---")

    prompt_parts = []
    prompt_parts.append(
        "SYSTEM INSTRUKTION: Du er en kreativ AI, der er ekspert i at skrive højtlæsningshistorier og godnathistorier for børn.")
    prompt_parts.append(
        "OPGAVE: Skriv en historie baseret på følgende input. Historien skal være engagerende, passende for målgruppen og have en klar begyndelse, midte og slutning.")
    prompt_parts.append(
        "FØRST, generer en kort og fængende titel til historien. Skriv KUN titlen på den allerførste linje af dit output. Efter titlen, indsæt ET ENKELT LINJESKIFT (ikke dobbelt), og start derefter selve historien.")
    prompt_parts.append("---")

    if listener_context_instruction:
        prompt_parts.append(listener_context_instruction)

    prompt_parts.append(f"Længdeønske: {length_instruction}")

    # Betinget logik for godnathistorie
    if is_bedtime_story:
        bedtime_instruction = [
            "\n**SÆRLIG INSTRUKTION: GODNATHISTORIE-FOKUS**",
            "Denne historie er en godnathistorie. Det er din VIGTIGSTE opgave at sikre, at historiens tone, tempo og indhold er meget roligt, trygt og beroligende. Formålet er at hjælpe barnet med at falde til ro og forberede sig på at sove.",
            "- **Variation i Navne:** Hvis brugeren ikke har angivet et specifikt navn for hovedpersonen, skal du selv finde på et passende og almindeligt dansk børnenavn (f.eks. Emil, Freja, Oscar, Ida). Det er vigtigt, at du varierer de navne, du vælger fra gang til gang, og undgår at bruge de samme navn (som f.eks. 'Luna').",
            "- **Undgå Spænding:** Minimer dramatiske, spændende eller uhyggelige elementer, især mod slutningen af historien.",
            "- **Roligt Tempo:** Fortæl historien i et roligt og afdæmpet tempo.",
            "- **Tryg Afslutning:** Sørg for at afslutningen er særligt blid, positiv og afklaret. Alle konflikter skal være løst på en tryg måde.",
            "Denne instruktion om 'godnatlæsning' TRUMFER den generelle 'Stemning' valgt af brugeren. Selvom brugeren har valgt f.eks. 'eventyrlig', skal det fortolkes som et 'roligt og trygt eventyr'."
        ]
        prompt_parts.append("\n".join(bedtime_instruction))
    else:
        # Hvis det IKKE er en godnathistorie, bruges den normale stemnings-instruktion
        prompt_parts.append(f"Stemning: {mood_prompt_part}")

    if karakter_str:
        prompt_parts.append(f"Hovedperson(er): {karakter_str}")
    if sted_str:
        prompt_parts.append(f"Sted(er): {sted_str}")
    if plot_str:
        prompt_parts.append(f"Plot/Elementer/Morale: {plot_str}")

    # Betinget logik for interaktiv historie
    if is_interactive:
        interactive_rules_list = [
            "\nINSTRUKTIONER FOR INTERAKTIV HISTORIE MED VALGMULIGHEDER (ILLUSION AF VALG):",
            "Når denne funktion er aktiv, skal du på 1-2 passende steder i historien (afhængigt af historiens samlede længde) indføre et segment med valgmuligheder for hovedpersonen. Følg denne struktur NØJE for hvert interaktivt segment:",
            "1. Fortæl en del af hovedhistorien, der naturligt leder op til et klart beslutningspunkt for hovedpersonen.",
            "2. Præsenter tydeligt TO specifikke og handlingsorienterede valgmuligheder (kald dem A og B).",
            "3. Skriv derefter en KORT (1-2 sætninger) scene for, hvad der sker, hvis hovedpersonen vælger VALG A. Start denne del med den præcise tekst 'Valgmulighed A): ' efterfulgt af scenen.",
            "4. Umiddelbart efter scenen for valg A, skriv en KORT (1-2 sætninger) scene for, hvad der sker, hvis hovedpersonen vælger VALG B. Start denne del med den præcise tekst 'Valgmulighed B): ' efterfulgt af scenen.",
            "5. VIGTIGT - FORTSÆTTELSE AF HOVEDHISTORIEN: Efter at have beskrevet de korte scener for både Valgmulighed A og B, skal du fortsætte den primære hovedhistorie. Fortsættelsen skal føles som en naturlig fortsættelse, der kunne følge efter *begge* scenarier, men **du må ALDRIG bruge formuleringer, der afslører dette eller gør valget ligegyldigt (f.eks. undgå strengt sætninger som 'Uanset hvad [X] valgte...', 'Det var lige meget, for...')**. Find i stedet en elegant og generel overgang, der samler tråden op i hovedfortællingen og opretholder illusionen om et meningsfuldt valg.",
        ]
        interactive_rules_str = "\n".join(interactive_rules_list)
        prompt_parts.append(interactive_rules_str)

    prompt_parts.append("\nGENERELLE REGLER FOR HISTORIEN:")
    prompt_parts.append("- Undgå komplekse sætninger og ord. Sproget skal være letforståeligt for børn.")
    prompt_parts.append("- Inkluder gerne gentagelser, rim eller lydeffekter, hvis det passer til historien.")
    prompt_parts.append("- Sørg for en positiv morale eller et opløftende budskab, hvis det er relevant for plottet.")
    prompt_parts.append("- Undgå vold, upassende temaer eller noget, der kan give mareridt.")

    if negative_prompt_text:
        prompt_parts.append(f"- VIGTIGT: Følgende elementer må IKKE indgå i historien: {negative_prompt_text}")

    prompt_parts.append(f"- {ending_instruction}")
    prompt_parts.append("---")
    prompt_parts.append(
        "Start outputtet med TITLEN på første linje, efterfulgt af ET ENKELT LINJESKIFT, og derefter selve historien:")

    return "\n".join(prompt_parts)