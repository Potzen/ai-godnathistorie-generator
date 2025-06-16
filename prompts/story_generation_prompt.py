# Fil: prompts/story_generation_prompt.py
from flask import current_app


def build_story_prompt(
        karakter_str,
        sted_str,
        plot_str,
        length_instruction,
        mood_prompt_part,
        listener_context_instruction, # <-- TILFØJET IGEN
        ending_instruction,
        negative_prompt_text,
        is_interactive=False,
        is_bedtime_story=False,
        focus_letter=None,
        target_lix=None
):
    """
    Bygger den komplette prompt-streng til historiegenerering med ny, kreativ logik for lave LIX-tal.
    """
    current_app.logger.info(
        f"--- build_story_prompt (v3 - Kreativ): is_interactive={is_interactive}, is_bedtime={is_bedtime_story}, target_lix={target_lix} ---")

    # Starten af prompten er den samme
    prompt_parts = [
        "SYSTEM INSTRUKTION: Du er en dygtig og alsidig AI-historiefortæller for børn. Du mestrer forskellige genrer og stemninger og respekterer brugerens input som den primære rettesnor.",
        "OPGAVE: Skriv en historie baseret på følgende input.",
        "FORMAT: Start outputtet med en kort, fængende TITEL på den allerførste linje. Efter titlen, indsæt ET ENKELT LINJESKIFT, og start derefter selve historien.",
        "---",
        "**BRUGERENS INPUT (KERNEELEMENTER):**",
        f"- Hovedperson(er): {karakter_str}",
        f"- Sted(er): {sted_str}",
        f"- Plot/Elementer/Morale: {plot_str}",
        "---"
    ]

    # --- NY KREATIV LIX-INSTRUKTION ---
    if target_lix is not None:
        prompt_parts.append("**KRITISK INSTRUKTION: SPROGLIGT NIVEAU OG STIL**")

        if target_lix <= 19:
            # Her kommer den nye, kreative tilgang
            lix_instruction = (
                f"**ROLLE:** Du er en pædagog, der fortæller en historie til et **vuggestuebarn (1-2 år)**.\n"
                f"**STIL:** Dit sprog skal være som i en **pegebog**. Tænk i meget korte, simple sætninger, der beskriver én ting ad gangen. Gentagelser er rigtig gode. Sproget skal være rytmisk og roligt.\n"
                f"**EKSEMPEL PÅ STIL:** 'Se myren. Myren er lille. Den går på en sti. Stien er lang. Myren finder et blad. Bladet er grønt.'\n"
                f"**VIGTIGT:** Fokusér på at skabe en **varm og menneskelig fortællerstemme**, ikke på at overholde matematiske regler. Målet er en naturlig, simpel historie, der føles som en rolig stund, ikke en robot-tekst. Dit mål er at ramme LIX {target_lix} ved at efterligne denne pædagogiske pegebogs-stil."
            )
            prompt_parts.append(lix_instruction)

        # De andre LIX-niveauer kan forblive som de var, da de ikke er problematiske
        elif 20 <= target_lix <= 29:
            prompt_parts.append(
                f"Mål-LIX: {target_lix}. Dette er for en læser, der er ved at få fat. Brug simple, korte til mellemlange sætninger. Hold sætningsstrukturen klar og ligetil.")
        elif 30 <= target_lix <= 44:
            prompt_parts.append(
                f"Mål-LIX: {target_lix}. Dette er for en sikker læser. Brug mere komplekse og varierede sætningslængder og et rigere ordforråd.")
        else:  # target_lix >= 45
            prompt_parts.append(
                f"Mål-LIX: {target_lix}. Dette er for en meget erfaren læser. Skriv med litterær kvalitet, komplekse sætningsstrukturer og et sofistikeret ordforråd.")

    # Resten af prompten fortsætter som før
    if negative_prompt_text:
        prompt_parts.append(f"- **Må IKKE indeholde:** {negative_prompt_text}")

    prompt_parts.append("---")
    prompt_parts.append(
        "Start dit output med TITLEN på første linje, efterfulgt af ET ENKELT LINJESKIFT, og derefter selve historien:")

    return "\n".join(prompt_parts)