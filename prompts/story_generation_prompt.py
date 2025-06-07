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
            "- **Variation i Navne:** Hvis brugeren ikke har angivet et specifikt navn for hovedpersonen, skal du selv finde på et passende og almindeligt dansk børnenavn (f.eks. Emil, Freja, Oscar, Ida). Det er vigtigt, at du varierer de navne, du vælger fra gang til gang, og undgår at bruge navne som f.eks. 'Luna'.",
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
            "\nSÆRLIG INSTRUKTION: INTERAKTIV HISTORIE",
            "Dette skal være en interaktiv historie. Det betyder, at du på 1-2 passende steder i historien skal skabe et øjeblik, hvor læseren føler, de har et valg. Gør det på en naturlig og læsevenlig måde, uden at du skriver instruktions-overskrifter som 'OPTÆGT' eller 'SPØRGSMÅL' i den endelige tekst.",
            "Flowet for et interaktivt øjeblik skal være som følger:",
            "1. Først bygger du op til et valg for hovedpersonen i et almindeligt afsnit.",
            "2. Så stiller du spørgsmålet direkte i teksten, f.eks. 'Hvad skulle [Navn] nu gøre? A) Gå over broen, eller B) Følge stien langs floden?'.",
            "3. Lige efter, i et nyt afsnit, starter du med 'Valgmulighed A): ' og beskriver den korte scene for det valg i 1-2 sætninger.",
            "4. I et nyt afsnit lige bagefter, starter du med 'Valgmulighed B): ' og beskriver den korte scene for det andet valg i 1-2 sætninger.",
            "5. Til sidst fortsætter du hovedhistorien i et nyt afsnit. Meget vigtigt: Fortsættelsen skal kunne passe efter begge valg, men du må absolut ikke nævne det. Undgå ord som 'uanset' eller 'lige meget hvad'. Lad blot historien glide naturligt videre ved f.eks. at fokusere på hovedpersonens følelser eller omgivelserne."
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