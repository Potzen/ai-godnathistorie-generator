# ERSTAT HELE FUNKTIONEN I prompts/story_generation_prompt.py
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
        is_bedtime_story=False,
        focus_letter=None,
        target_lix=None
):
    """
    Bygger den komplette prompt-streng til historiegenerering med en neutral tilgang til LIX-historier.
    """
    current_app.logger.info(
        f"--- build_story_prompt (v4 - Neutral LIX): is_interactive={is_interactive}, is_bedtime={is_bedtime_story}, target_lix={target_lix} ---")

    prompt_parts = [
        "SYSTEM INSTRUKTION: Du er en dygtig og alsidig AI-historiefortæller for børn. Du mestrer forskellige genrer og stemninger og respekterer brugerens input som den primære rettesnor.",
        "OPGAVE: Skriv en historie baseret på følgende input.",
        "FORMAT: Start outputtet med en kort, fængende TITEL på den allerførste linje. Efter titlen, indsæt ET ENKELT LINJESKIFT, og start derefter selve historien.",
        "---",
        "**BRUGERENS INPUT (KERNEELEMENTER):**",
        f"- Hovedperson(er): {karakter_str}",
        f"- Sted(er): {sted_str}",
        f"- Plot/Elementer/Morale: {plot_str}",
    ]

    if focus_letter:
        prompt_parts.append(
            f"- **Fokus Bogstav/Lyd:** '{focus_letter}'. Sørg for at inkludere ord, der indeholder dette bogstav (eller disse bogstaver) hyppigt og naturligt i historien. Dette er for at øve udtalen.")

    prompt_parts.append("---")

    if target_lix is not None:
        prompt_parts.append("**KRITISK INSTRUKTION: SPROGLIGT NIVEAU OG STIL (LÆSEHESTEN)**")
        # ---- HER ER ÆNDRINGEN ----
        if target_lix <= 19:
            lix_instruction = (
                f"**ROLLE:** Du er forfatter af børnebøger for de alleryngste (1-3 år).\n"
                f"**STIL:** Skriv i en **pegebogs-stil**. Brug meget korte, simple og konkrete sætninger. Gentagelser er et godt virkemiddel. Sproget skal være rytmisk og let at afkode.\n"
                f"**EKSEMPEL PÅ STIL:** 'Se myren. Myren er lille. Den går på en sti. Stien er lang. Myren finder et blad. Bladet er grønt.'\n"
                f"**VIGTIGT:** Målet er en **klar og simpel historie**. Undgå komplekse koncepter. Dit mål er at ramme LIX {target_lix} ved at efterligne denne simple pegebogs-stil."
            )
            prompt_parts.append(lix_instruction)
        # De andre LIX-niveauer er allerede neutrale, så de forbliver uændrede.
        elif 20 <= target_lix <= 29:
            prompt_parts.append(
                f"Mål-LIX: {target_lix}. Dette er for en læser, der er ved at få fat. Brug simple, korte til mellemlange sætninger. Hold sætningsstrukturen klar og ligetil.")
        elif 30 <= target_lix <= 44:
            prompt_parts.append(
                f"Mål-LIX: {target_lix}. Dette er for en sikker læser. Brug mere komplekse og varierede sætningslængder og et rigere ordforråd.")
        else: # LIX > 44
            prompt_parts.append(
                f"Mål-LIX: {target_lix}. Dette er for en meget erfaren læser. Skriv med litterær kvalitet, komplekse sætningsstrukturer og et sofistikeret ordforråd.")
        # Tilføj en generel negativ instruktion for alle LIX-historier
        prompt_parts.append("\n**GENEREL REGEL FOR LÆSEHESTEN:** Afslut historien på en neutral eller positiv måde. **Undgå at afslutte som en godnathistorie** (f.eks. med 'Sov godt'), medmindre brugeren specifikt har bedt om det via 'Godnatlæsning'-funktionen.")

    # Almindelig historie-logik (uændret)
    else:
        prompt_parts.extend([
            "**BRUGERENS INPUT (RAMMER & STEMNING):**",
            f"- Historiens Længde: {length_instruction}",
            f"- Historiens Stemning: {mood_prompt_part}",
        ])
        if listener_context_instruction:
            prompt_parts.append(listener_context_instruction)
        if is_interactive:
            prompt_parts.append("- **INTERAKTIV HISTORIE:** Inkorporer 1-2 meningsfulde valg i historien, hvor læseren kan vælge, hvad der skal ske. Præsenter valget klart, f.eks.: 'Hvad tror du, [karakter] gjorde nu? A) ... eller B) ...'. Fortsæt historien baseret på et af valgene.")
        if is_bedtime_story:
             prompt_parts.append("- **GODNATLÆSNING:** Dette er en godnathistorie. Sørg for, at stemningen er **ekstra rolig, tryg og beroligende**. Undgå alt for spændende eller skræmmende elementer. Afslutningen skal være meget afdæmpet.")

    if negative_prompt_text:
        prompt_parts.append(f"- **Må IKKE indeholde:** {negative_prompt_text}")

    prompt_parts.append("---")
    prompt_parts.append(
        "Start dit output med TITLEN på første linje, efterfulgt af ET ENKELT LINJESKIFT, og derefter selve historien:")

    return "\\n".join(prompt_parts)