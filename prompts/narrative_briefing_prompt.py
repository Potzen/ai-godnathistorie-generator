# Fil: prompts/narrative_briefing_prompt.py

def build_narrative_briefing_prompt(
    narrative_focus, # Tema, Udfordring eller Fokus for Historien
    story_goal, # Ønsket Udgang/Mål for Historien
    child_name,
    child_age,
    child_strengths, # Liste af strenge
    child_values, # Liste af strenge
    child_motivation, # Streng
    child_typical_reaction, # Streng
    important_relations, # Liste af dicts, f.eks. [{'name': 'Mor', 'type': 'støtte'}]
    # Følgende er standard historieelementer, som også kan informere briefet
    main_character_description=None, # Beskrivelse af hovedperson (hvis forskellig fra barnet)
    story_place=None, # Steder for historien
    story_plot_elements=None, # Plot-elementer/ønsket morale
    negative_prompt=None # Hvad historien IKKE skal indeholde
):
    """
    Bygger prompten for Trin 1 AI (Input-Forberedende AI),
    der skal generere et struktureret "narrativt brief".
    """

    prompt_parts = [
        "SYSTEM INSTRUKTION: Du er en analytisk AI-assistent. Din opgave er IKKE at skrive en historie, men at forberede et detaljeret og struktureret 'narrativt brief' baseret på brugerens input. Dette brief vil blive givet videre til en anden AI (en kreativ historieforfatter) for at skrive selve den narrative børnehistorie. Dit output skal være klart, koncis og handlingsorienteret for historieforfatteren.",
        "Dit output SKAL KUN være selve det narrative brief, uden indledende eller afsluttende høflighedsfraser.",
        "--- BRUGERINPUT MODTAGET ---"
    ]

    if narrative_focus:
        prompt_parts.append(f"1. NARRATIVT FOKUS (Tema/Udfordring): {narrative_focus}")

    if story_goal:
        prompt_parts.append(f"2. ØNSKET UDGANG/MÅL FOR HISTORIEN: {story_goal}")

    prompt_parts.append("\n3. INFORMATION OM BARNET (CENTRALT FOR HISTORIENS PROTAGONIST):")
    if child_name:
        prompt_parts.append(f"   - Navn: {child_name}")
    if child_age:
        prompt_parts.append(f"   - Alder: {child_age}")
    if child_strengths:
        prompt_parts.append(f"   - Styrker/Ressourcer: {', '.join(child_strengths)}")
    if child_values:
        prompt_parts.append(f"   - Værdier/Overbevisninger: {', '.join(child_values)}")
    if child_motivation:
        prompt_parts.append(f"   - Dybeste Ønske/Motivation (udover problem): {child_motivation}")
    if child_typical_reaction:
        prompt_parts.append(f"   - Typisk Reaktion på Udfordring (som historien kan arbejde med): {child_typical_reaction}")
    if important_relations:
        relations_str = ", ".join([f"{rel.get('name', 'Ukendt')} ({rel.get('type', 'relation')})" for rel in important_relations])
        prompt_parts.append(f"   - Vigtige Relationer (støttefigurer): {relations_str}")

    # Optionelle, generelle historieelementer, der kan berige briefet
    prompt_parts.append("\n4. GENERELLE HISTORIEELEMENTER (HVIS ANGIVET AF BRUGER):")
    has_general_elements = False
    if main_character_description:
        prompt_parts.append(f"   - Hovedkarakter (hvis forskellig fra barnet): {main_character_description}")
        has_general_elements = True
    if story_place:
        prompt_parts.append(f"   - Sted(er) for historien: {story_place}")
        has_general_elements = True
    if story_plot_elements:
        prompt_parts.append(f"   - Plot-elementer/Ønsket Morale: {story_plot_elements}")
        has_general_elements = True
    if negative_prompt:
        prompt_parts.append(f"   - Må IKKE indeholde: {negative_prompt}")
        has_general_elements = True
    if not has_general_elements:
        prompt_parts.append("   (Ingen specifikke generelle historieelementer angivet udover det narrative fokus og barnets information).")

    prompt_parts.append("\n--- DIN OPGAVE (AI DATA-OPSAMLER) ---")
    prompt_parts.append(
        "Din eneste opgave er at tage alle de ovenstående brugerinput og præsentere dem på en struktureret og letlæselig måde. Du skal IKKE analysere, fortolke, foreslå narrative strategier (som eksternalisering), eller tilføje egne ideer. Du skal blot fungere som en dataopsamler og -formidler.")
    prompt_parts.append("Dit output skal KUN være den strukturerede opsummering af de modtagne data.")
    prompt_parts.append(
        "Brug følgende format og overskrifter. Hvis et felt ikke er angivet af brugeren, skriv 'Ikke angivet'.")

    prompt_parts.append("\nSTRUKTURERET OPSUMMERING AF BRUGERINPUT:")
    prompt_parts.append("========================================")

    prompt_parts.append("\n1. NARRATIVT FOKUS (TEMA/UDFORDRING):")
    prompt_parts.append(f"   - {narrative_focus if narrative_focus else 'Ikke angivet'}")

    prompt_parts.append("\n2. ØNSKET UDGANG/MÅL FOR HISTORIEN:")
    prompt_parts.append(f"   - {story_goal if story_goal else 'Ikke angivet'}")

    prompt_parts.append("\n3. INFORMATION OM BARNET:")
    prompt_parts.append(f"   - Navn: {child_name if child_name else 'Ikke angivet'}")
    prompt_parts.append(f"   - Alder: {child_age if child_age else 'Ikke angivet'}")
    prompt_parts.append(f"   - Styrker/Ressourcer: {', '.join(child_strengths) if child_strengths else 'Ikke angivet'}")
    prompt_parts.append(f"   - Værdier/Overbevisninger: {', '.join(child_values) if child_values else 'Ikke angivet'}")
    prompt_parts.append(f"   - Dybeste Ønske/Motivation: {child_motivation if child_motivation else 'Ikke angivet'}")
    prompt_parts.append(
        f"   - Typisk Reaktion på Udfordring: {child_typical_reaction if child_typical_reaction else 'Ikke angivet'}")
    if important_relations:
        relations_str = ", ".join(
            [f"{rel.get('name', 'Ukendt')} ({rel.get('type', 'relation')})" for rel in important_relations])
        prompt_parts.append(f"   - Vigtige Relationer: {relations_str}")
    else:
        prompt_parts.append("   - Vigtige Relationer: Ikke angivet")

    prompt_parts.append("\n4. GENERELLE HISTORIEELEMENTER:")
    prompt_parts.append(
        f"   - Hovedkarakter (hvis forskellig fra barnet): {main_character_description if main_character_description else 'Ikke angivet'}")
    prompt_parts.append(f"   - Sted(er) for historien: {story_place if story_place else 'Ikke angivet'}")
    prompt_parts.append(
        f"   - Plot-elementer/Ønsket Morale: {story_plot_elements if story_plot_elements else 'Ikke angivet'}")
    prompt_parts.append(f"   - Må IKKE indeholde: {negative_prompt if negative_prompt else 'Ikke angivet'}")

    prompt_parts.append("\n========================================")
    prompt_parts.append(
        "HUSK: Output kun ovenstående strukturerede opsummering. Ingen yderligere tekst, analyse eller historie.")

    return "\n".join(prompt_parts)

# Eksempel på hvordan funktionen kan kaldes (til test)
if __name__ == '__main__':
    example_brief_prompt = build_narrative_briefing_prompt(
        narrative_focus="Min datter på 6 år er bange for mørke og monstre under sengen.",
        story_goal="At hun føler sig mere modig og tryg ved sengetid.",
        child_name="Lily",
        child_age="6",
        child_strengths=["Fantasifuld", "God til at tegne", "Elsker sin bamse Bruno"],
        child_values=[], # Tom for test
        child_motivation="Vil gerne sove med lyset slukket",
        child_typical_reaction=None, # Tom for test
        important_relations=[{'name': 'Bamse Bruno', 'type': 'tryghedsgiver'}, {'name': 'Mor', 'type': 'hjælper'}],
        negative_prompt="Ingen rigtige monstre, der er onde"
    )
    print(example_brief_prompt)