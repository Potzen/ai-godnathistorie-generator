# Fil: prompts/story_generation_prompt.py

def build_story_prompt(
        karakter_str,
        sted_str,
        plot_str,
        length_instruction,
        mood_prompt_part,
        listener_context_instruction,
        ending_instruction,
        negative_prompt_text,
        is_interactive=False  # Beholder denne parameter, selvom den ikke bruges aktivt i prompten lige nu
):
    """
    Bygger den komplette prompt-streng til generering af en godnathistorie.
    """
    prompt_parts = []
    prompt_parts.append("SYSTEM INSTRUKTION: Du er en kreativ AI, der er ekspert i at skrive godnathistorier for børn.")
    prompt_parts.append(
        "OPGAVE: Skriv en godnathistorie baseret på følgende input. Historien skal være engagerende, passende for målgruppen og have en klar begyndelse, midte og slutning.")
    prompt_parts.append(
        "FØRST, generer en kort og fængende titel til historien. Skriv KUN titlen på den allerførste linje af dit output. Efter titlen, indsæt ET ENKELT LINJESKIFT (ikke dobbelt), og start derefter selve historien.")
    prompt_parts.append("---")

    if listener_context_instruction:
        prompt_parts.append(listener_context_instruction)

    prompt_parts.append(f"Længdeønske: {length_instruction}")
    prompt_parts.append(f"Stemning: {mood_prompt_part}")

    if karakter_str:
        prompt_parts.append(f"Hovedperson(er): {karakter_str}")
    if sted_str:
        prompt_parts.append(f"Sted(er): {sted_str}")
    if plot_str:
        prompt_parts.append(f"Plot/Elementer/Morale: {plot_str}")

    # if is_interactive: # Logik for interaktivitet er pt. ikke fuldt implementeret i prompten
    #     interactive_rules = (
    #         "REGLER FOR INDDRAGENDE EVENTYR MED EKSPLICITTE VALG-STIER:\n"
    #         # "... (din interaktive logik her) ..." # Denne del mangler stadig definition
    #     )
    #     prompt_parts.append(f"\n{interactive_rules}")

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