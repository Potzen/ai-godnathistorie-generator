# Fil: prompts/narrative_briefing_prompt.py

def build_narrative_briefing_prompt(
        original_user_inputs: dict
):
    """
    Bygger prompten for Trin 1 AI (Input-Forberedende AI),
    der skal generere et struktureret "narrativt brief".
    Dette brief skal indeholde ALLE relevante brugerinput.
    """

    # Hent alle nødvendige værdier fra original_user_inputs (som i den version du viste mig på 191 linjer)
    narrative_focus = original_user_inputs.get('narrative_focus', '').strip()
    story_goal = original_user_inputs.get('story_goal', '').strip()
    child_name = original_user_inputs.get('child_name', '').strip()
    child_age = original_user_inputs.get('child_age', '').strip()
    child_strengths = original_user_inputs.get('child_strengths', [])
    child_values = original_user_inputs.get('child_values', [])
    child_motivation = original_user_inputs.get('child_motivation', '').strip()
    child_typical_reaction = original_user_inputs.get('child_typical_reaction', '').strip()
    important_relations_list = original_user_inputs.get('important_relations', [])

    problem_identity_name = original_user_inputs.get('narrative_problem_identity_name', '').strip()
    problem_role_function = original_user_inputs.get('narrative_problem_role_function', '').strip()
    problem_purpose_intention = original_user_inputs.get('narrative_problem_purpose_intention', '').strip()
    problem_behavior_action = original_user_inputs.get('narrative_problem_behavior_action', '').strip()
    problem_influence = original_user_inputs.get('narrative_problem_influence', '').strip()

    main_characters_list = original_user_inputs.get('main_characters', [])
    story_places_list = original_user_inputs.get('places', [])
    story_plot_elements_list = original_user_inputs.get('plot_elements', [])
    negative_prompt = original_user_inputs.get('negative_prompt', '').strip()
    user_selected_length = original_user_inputs.get('length', 'mellem')
    user_selected_mood = original_user_inputs.get('mood', 'neutral')

    # Formater lister (som før)
    child_strengths_str = ", ".join(filter(None, child_strengths)) if child_strengths else 'Ikke angivet'
    child_values_str = ", ".join(filter(None, child_values)) if child_values else 'Ikke angivet'

    important_relations_display = []
    if important_relations_list:
        for rel in important_relations_list:
            name = rel.get('name', '').strip()
            rtype = rel.get('type', '').strip()
            if name or rtype:
                important_relations_display.append(f"{name} (Type: {rtype})" if name and rtype else name or rtype)
    important_relations_str = ", ".join(important_relations_display) if important_relations_display else 'Ikke angivet'

    main_character_descriptions = []
    if main_characters_list:
        for char_obj in main_characters_list:
            desc = char_obj.get('description', '').strip()
            name = char_obj.get('name', '').strip()
            if desc or name:
                main_character_descriptions.append(
                    f"Beskrivelse: {desc}, Navn: {name}" if name and desc else (name or desc))
    main_characters_str = "; ".join(
        main_character_descriptions) if main_character_descriptions else 'Ikke specificeret (fokus på barnets spejling)'

    story_place_str = ", ".join(filter(None, story_places_list)) if story_places_list else 'Ikke specificeret af bruger'
    story_plot_elements_str = ", ".join(
        filter(None, story_plot_elements_list)) if story_plot_elements_list else 'Ikke specificeret af bruger'

    prompt_parts = [
        "SYSTEM INSTRUKTION: Du er en analytisk AI-assistent. Din opgave er IKKE at skrive en historie selv, men at omhyggeligt forberede et detaljeret og struktureret 'narrativt brief' baseret på de brugerinput, du modtager nedenfor. Dette brief vil blive givet videre til en anden AI (en kreativ historieforfatter). Dit output skal være en præcis og komplet opsummering af ALLE de angivne brugerinput, formateret som specificeret.",
        "Dit output SKAL KUN være selve det narrative brief, startende med 'STRUKTURERET OPSUMMERING AF BRUGERINPUT:' og sluttende med '========================================', uden yderligere indledende eller afsluttende tekst.",

        "\n--- DETALJERET BRUGERINPUT SOM SKAL OPSUMMERES NØJAGTIGT ---",
        f"1. Narrativt Fokus (Tema/Udfordring): {narrative_focus if narrative_focus else 'Ikke angivet af bruger'}",
        f"2. Ønsket Udvikling/Mål for Historien: {story_goal if story_goal else 'Ikke angivet af bruger'}",
        "\n3. Information om Barnet (Protagonistens Udgangspunkt):",
        f"   - Barnets Navn: {child_name if child_name else 'Ikke angivet af bruger'}",
        f"   - Barnets Alder: {child_age if child_age else 'Ikke angivet af bruger'}",
        f"   - Barnets Styrker/Ressourcer: {child_strengths_str if child_strengths else 'Ikke angivet af bruger'}",
        # Brug _str versioner
        f"   - Barnets Værdier/Overbevisninger: {child_values_str if child_values else 'Ikke angivet af bruger'}",
        # Brug _str versioner
        f"   - Barnets Dybeste Ønske/Motivation (udover problemfokus): {child_motivation if child_motivation else 'Ikke angivet af bruger'}",
        f"   - Barnets Typiske Reaktion på Udfordring: {child_typical_reaction if child_typical_reaction else 'Ikke angivet af bruger'}",
        f"   - Barnets Vigtige Relationer (Støttefigurer): {important_relations_str if important_relations_list else 'Ikke angivet af bruger'}",
        # Brug _str version
        "\n4. Information om Problem-Karakteren (Brugerens eksternalisering):",
        f"   - Problemets Navn/Identitet: {problem_identity_name if problem_identity_name else 'Ikke specificeret af bruger'}",
        f"   - Problemets Rolle/Funktion: {problem_role_function if problem_role_function else 'Ikke specificeret af bruger'}",
        f"   - Problemets Formål/Intention: {problem_purpose_intention if problem_purpose_intention else 'Ikke specificeret af bruger'}",
        f"   - Problemets Adfærd/Handling: {problem_behavior_action if problem_behavior_action else 'Ikke specificeret af bruger'}",
        f"   - Problemets Indflydelse på Hovedpersonen: {problem_influence if problem_influence else 'Ikke specificeret af bruger'}",
        "\n5. Generelle Historieelementer og Rammer (Fra Brugerinput):",
        f"   - Andre Hovedkarakterer i Historien: {main_characters_str if main_characters_list else 'Ikke specificeret af bruger'}",
        # Brug _str version
        f"   - Sted(er) hvor historien skal foregå: {story_place_str if story_places_list else 'Ikke specificeret af bruger'}",
        # Brug _str version
        f"   - Plot-elementer eller Ønsket Morale: {story_plot_elements_str if story_plot_elements_list else 'Ikke specificeret af bruger'}",
        # Brug _str version
        f"   - Elementer der IKKE skal med i historien: {negative_prompt if negative_prompt else 'Ingen specifikke undtagelser fra bruger.'}",
        f"   - Ønsket Historiens Længde: {user_selected_length if user_selected_length else 'Mellem (standard)'}",
        f"   - Ønsket Historiens Stemning: {user_selected_mood if user_selected_mood else 'Neutral (standard)'}",

        "\n--- DIN OPGAVE: STRUKTURERET OPSUMMERING ---",
        "Baseret EKSKLUSIVT på de ovenstående 'DETALJERET BRUGERINPUT SOM SKAL OPSUMMERES NØJAGTIGT', generer nu en 'STRUKTURERET OPSUMMERING AF BRUGERINPUT' der følger formatet nedenfor PRÆCIST. Hvert punkt i din opsummering SKAL afspejle den information, der er givet for det korresponderende punkt i 'DETALJERET BRUGERINPUT'. Hvis et felt var 'Ikke angivet af bruger' eller 'Ikke specificeret af bruger' ovenfor, skal det også angives sådan i din opsummering. Foretag INGEN analyse, fortolkning, eller udeladelser af de angivne informationer.",

        "\nSTRUKTURERET OPSUMMERING AF BRUGERINPUT (DIT OUTPUT SKAL FØLGE DENNE STRUKTUR NØJE):",
        "========================================",
        "\n1. NARRATIVT FOKUS (TEMA/UDFORDRING):",
        f"   - [Her skal du indsætte værdien fra '1. Narrativt Fokus' fra ovenstående brugerinput]",
        "\n2. ØNSKET UDVIKLING/MÅL FOR HISTORIEN:",
        f"   - [Her skal du indsætte værdien fra '2. Ønsket Udvikling/Mål' fra ovenstående brugerinput]",
        "\n3. INFORMATION OM BARNET (PROTAGONISTENS UDGANGSPUNKT):",
        f"   - Navn: [Her skal du indsætte værdien fra 'Barnets Navn' fra ovenstående brugerinput]",
        f"   - Alder: [Her skal du indsætte værdien fra 'Barnets Alder' fra ovenstående brugerinput]",
        f"   - Styrker/Ressourcer: [Her skal du indsætte værdien fra 'Barnets Styrker/Ressourcer' fra ovenstående brugerinput]",
        f"   - Værdier/Overbevisninger: [Her skal du indsætte værdien fra 'Barnets Værdier/Overbevisninger' fra ovenstående brugerinput]",
        f"   - Dybeste Ønske/Motivation (udover problemfokus): [Her skal du indsætte værdien fra 'Barnets Dybeste Ønske/Motivation' fra ovenstående brugerinput]",
        f"   - Typisk Reaktion på Udfordring: [Her skal du indsætte værdien fra 'Barnets Typiske Reaktion' fra ovenstående brugerinput]",
        f"   - Vigtige Relationer (Støttefigurer): [Her skal du indsætte værdien fra 'Barnets Vigtige Relationer' fra ovenstående brugerinput]",
        "\n4. PROBLEM-KARAKTER (EKSTERNALISERING AF UDFORDRING - SOM ANGIVET AF BRUGER):",
        f"   - Navn/Identitet for Problemet: [Her skal du indsætte værdien fra 'Problemets Navn/Identitet' fra ovenstående brugerinput]",
        f"   - Problemets Rolle/Funktion: [Her skal du indsætte værdien fra 'Problemets Rolle/Funktion' fra ovenstående brugerinput]",
        f"   - Problemets Formål/Intention: [Her skal du indsætte værdien fra 'Problemets Formål/Intention' fra ovenstående brugerinput]",
        f"   - Problemets Adfærd/Handling: [Her skal du indsætte værdien fra 'Problemets Adfærd/Handling' fra ovenstående brugerinput]",
        f"   - Problemets Indflydelse på Hovedpersonen: [Her skal du indsætte værdien fra 'Problemets Indflydelse' fra ovenstående brugerinput]",
        "\n5. GENERELLE HISTORIEELEMENTER OG RAMMER (SOM ANGIVET AF BRUGER):",
        f"   - Andre Hovedkarakterer i Historien: [Her skal du indsætte værdien fra 'Andre Hovedkarakterer' fra ovenstående brugerinput]",
        f"   - Sted(er) hvor historien skal foregå: [Her skal du indsætte værdien fra 'Sted(er)' fra ovenstående brugerinput]",
        f"   - Plot-elementer eller Ønsket Morale: [Her skal du indsætte værdien fra 'Plot-elementer' fra ovenstående brugerinput]",
        f"   - Elementer der IKKE skal med i historien: [Her skal du indsætte værdien fra 'Elementer der IKKE skal med' fra ovenstående brugerinput]",
        f"   - Ønsket Historiens Længde: [Her skal du indsætte værdien fra 'Ønsket Historiens Længde' fra ovenstående brugerinput]",
        f"   - Ønsket Historiens Stemning: [Her skal du indsætte værdien fra 'Ønsket Historiens Stemning' fra ovenstående brugerinput]",
        "\n========================================",
        "HUSK: Dit eneste output er den STRUKTUREREDE OPSUMMERING ovenfor, hvor du har udfyldt [pladsholderne] med den korresponderende information fra 'DETALJERET BRUGERINPUT'-sektionen. Vær præcis og komplet."
    ]
    return "\n".join(prompt_parts)

# if __name__ == '__main__': ... (testblokken kan forblive som den er) ...


if __name__ == '__main__':  # Denne del er kun til test og påvirker ikke importen
    example_inputs_for_brief = {
        'narrative_focus': "Min søn er bange for edderkopper i sit værelse.",
        'story_goal': "At han ser edderkopper som mindre farlige eller endda interessante.",
        'child_name': "Leo",
        'child_age': "7",
        'child_strengths': ["Nysgerrig", "Modig når det gælder"],
        'child_values': ["Dyrevelfærd (generelt)"],
        'child_motivation': "Vil gerne kunne sove uden at tjekke loftet konstant.",
        'child_typical_reaction': "Råber og løber væk.",
        'important_relations': [{'name': 'Far', 'type': 'Trøster og fjerner edderkopper'}],
        'narrative_problem_identity_name': "Kravle-Kræet Kenny",
        'narrative_problem_role_function': "Dukker uventet op på væggen",
        'narrative_problem_purpose_intention': "Vil bare finde et roligt hjørne",
        'narrative_problem_behavior_action': "Bevæger sig hurtigt, gemmer sig",
        'narrative_problem_influence': "Gør Leo panisk",
        'main_characters': [{'description': 'En klog gammel flue', 'name': 'Professor Pip'}],
        'places': ["Leos værelse", "Under sengen"],
        'plot_elements': ["Leo lærer at edderkopper spiser myg"],
        'negative_prompt': "Ingen bidende edderkopper",
        'length': "mellem",
        'mood': "positiv og lærerig"
    }
    brief_prompt = build_narrative_briefing_prompt(example_inputs_for_brief)
    print(brief_prompt)