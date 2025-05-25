# Fil: prompts/narrative_generator_prompt.py

def build_narrative_generator_prompt(
    narrative_focus,
    child_info,
    story_elements,
    desired_outcome=None # Valgfri parameter
):
    """
    Bygger den komplette prompt-streng til Trin 1: Generator-AI for "Narrativ Støtte".
    Denne prompt skal generere et første, råt historieudkast.

    Args:
        narrative_focus (str): Det centrale tema, udfordring eller fokus for historien.
        child_info (dict): Objekt med information om barnet (navne, aldre, styrker etc.).
        story_elements (dict): Objekt med standard historieelementer (karakterer, steder etc.).
        desired_outcome (str, optional): Forælderens ønskede udgang for historien. Defaults to None.

    Returns:
        str: Den færdigbyggede prompt-streng.
    """
    prompt_parts = []

    prompt_parts.append("SYSTEM INSTRUKTION: Du er en AI, der specialiserer sig i at skrive et FØRSTE UDKAST til børnehistorier med et specifikt pædagogisk eller følelsesmæssigt fokus, baseret på principper fra narrativ terapi. Din opgave er at generere en komplet historie baseret på de givne input. Dette første udkast vil senere blive analyseret og revideret af andre AI-enheder.")
    prompt_parts.append("GENEREL OPGAVE: Skriv et første udkast til en historie. Historien skal være sammenhængende og alderssvarende.")
    prompt_parts.append("FORMAT INSTRUKTION: Start outputtet med en fængende TITEL på den allerførste linje. Efter titlen, indsæt ET ENKELT LINJESKIFT, og start derefter selve historieteksten.")
    prompt_parts.append("---")

    # 1. Narrativ Fokus og Ønsket Udgang
    prompt_parts.append(f"HISTORIENS NARRATIVE FOKUS (Centralt Tema/Udfordring): {narrative_focus}")
    if desired_outcome:
        prompt_parts.append(f"FORÆLDERENS ØNSKEDE UDVIKLING/MÅL FOR BARNET GENNEM HISTORIEN: {desired_outcome}")
    prompt_parts.append("INSTRUKTION TIL AI: Integrer dette fokus og eventuelle ønskede mål subtilt i historiens handling og tematik. Det første udkast skal lægge op til, at hovedpersonen oplever eller konfronterer dette fokus.")
    prompt_parts.append("---")

    # 2. Information om Barnet/Lytteren (Hovedpersonen)
    prompt_parts.append("INFORMATION OM BARNET/LYTTEREN (som historien skal tage udgangspunkt i):")
    if child_info.get('names_ages'):
        listener_descs = []
        for listener in child_info['names_ages']:
            desc = listener.get('name', 'Et barn')
            if listener.get('age'):
                desc += f" på {listener['age']} år"
            listener_descs.append(desc)
        prompt_parts.append(f"- Lyttere: {', '.join(listener_descs)}")

    if child_info.get('strengths_characteristics'):
        prompt_parts.append(f"- Barnets Karakteristika/Styrker: {', '.join(child_info['strengths_characteristics'])}")
        prompt_parts.append("  INSTRUKTION TIL AI: Prøv at lade hovedpersonen i historien udvise eller opdage lignende styrker.")

    if child_info.get('values_beliefs'):
        prompt_parts.append(f"- Barnets Værdier/Overbevisninger (hvis angivet): {', '.join(child_info['values_beliefs'])}")

    if child_info.get('motivation_wish'):
        prompt_parts.append(f"- Barnets Motivation/Ønske (hvis angivet): {child_info['motivation_wish']}")

    if child_info.get('typical_behavior_reaction'):
        prompt_parts.append(f"- Barnets Typiske Adfærd/Reaktion (hvis angivet): {child_info['typical_behavior_reaction']}")

    if child_info.get('important_relations'):
        relation_descs = [f"{rel.get('name')} ({rel.get('relation_type')})" for rel in child_info['important_relations']]
        prompt_parts.append(f"- Vigtige Relationer for Barnet: {', '.join(relation_descs)}")
        prompt_parts.append("  INSTRUKTION TIL AI: Overvej om nogle af disse relationer kan spille en birolle eller tjene som inspiration i historien.")
    prompt_parts.append("GENEREL INSTRUKTION TIL AI FOR BARNINFO: Brug disse informationer til at gøre historiens hovedperson relaterbar og til at forme historiens udfordringer og løsninger på en måde, der giver genklang. Historien skal primært handle om en hovedperson, der afspejler barnet.")
    prompt_parts.append("---")

    # 3. Standard Historieelementer
    prompt_parts.append("STANDARD HISTORIEELEMENTER (baseret på forælderens input):")
    if story_elements.get('main_characters'):
        main_chars_descs = []
        for char in story_elements['main_characters']:
            desc = char.get('description', 'En karakter')
            if char.get('name'):
                desc += f" ved navn {char['name']}"
            main_chars_descs.append(desc)
        prompt_parts.append(f"- Hovedperson(er) i historien (udover barnets spejling): {', '.join(main_chars_descs)}")
    else:
        # Hvis ingen specifikke karakterer er angivet, sørg for at barnets spejling er hovedpersonen
        prompt_parts.append("- Hovedpersonen i historien vil primært være en spejling af barnet/lytteren.")

    if story_elements.get('places'):
        prompt_parts.append(f"- Steder i historien: {', '.join(story_elements['places'])}")
    if story_elements.get('plot_elements_morals'):
        prompt_parts.append(f"- Plot-elementer/Ønsket Morale: {', '.join(story_elements['plot_elements_morals'])}")

    length = story_elements.get('length', 'mellem')
    length_instruction = {
        'kort': "Historien skal være relativt kort, ca. 6-8 afsnit.",
        'mellem': "Historien skal have en mellemlængde, ca. 10-14 afsnit.",
        'lang': "Historien skal være lang og detaljeret, over 15 afsnit."
    }.get(length, "Historien skal have en mellemlængde, ca. 10-14 afsnit.")
    prompt_parts.append(f"- Historiens Længde: {length_instruction}")

    mood = story_elements.get('mood', 'neutral')
    mood_map = { # Genbruger lidt fra din eksisterende story_generation_prompt for konsistens
        'sød': "Historien skal have en sød og hjertevarm stemning.",
        'sjov': "Historien skal have en humoristisk og sjov tone.",
        'eventyr': "Historien skal være eventyrlig og magisk.",
        'spændende': "Historien skal være spændende og medrivende.",
        'rolig': "Historien skal have en rolig og afslappende stemning.",
        'mystisk': "Historien skal have en mystisk og gådefuld stemning.",
        'hverdagsdrama': "Historien skal omhandle genkendeligt hverdagsdrama.",
        'uhyggelig': "Historien skal have en let uhyggelig (men ikke skræmmende) stemning.",
        'tryg og magisk': "Historien skal have en tryg og magisk stemning.", # Tilføjet fra dit test-fetch
        'neutral': "Historien skal have en neutral eller blandet stemning."
    }
    prompt_parts.append(f"- Historiens Stemning: {mood_map.get(mood, mood_map['neutral'])}")

    if story_elements.get('negative_prompt'):
        prompt_parts.append(f"- Elementer der IKKE må indgå: {story_elements['negative_prompt']}")
    prompt_parts.append("---")

    # Afsluttende instruktioner for Generator-AI
    prompt_parts.append("AFSLUTTENDE INSTRUKTIONER TIL GENERATOR-AI:")
    prompt_parts.append("- Skriv et FULDSTÆNDIGT historieudkast fra start til slut, inklusive en titel på første linje.")
    prompt_parts.append("- Fokusér på at skabe en sammenhængende fortælling, der adresserer det narrative fokus.")
    prompt_parts.append("- Dette er kun det FØRSTE udkast. Det er okay, hvis det ikke er perfekt endnu ift. alle narrative principper (som eksternalisering eller re-authoring), da det vil blive forfinet senere. Men forsøg at lade hovedpersonen være aktiv og handlekraftig ift. det narrative fokus.")
    prompt_parts.append("- Undgå direkte terapeutisk sprog eller at forklare narrative principper i selve historien.")
    prompt_parts.append("- Historien skal være på dansk.")

    return "\n\n".join(prompt_parts)
