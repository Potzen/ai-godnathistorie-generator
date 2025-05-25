# Fil: prompts/narrative_drafting_prompt.py

def build_narrative_drafting_prompt(
        structured_brief,  # Outputtet fra Trin 1 (den strukturerede opsummering af brugerinput)
        rag_context,  # Liste af relevante tekst-chunks fra RAG-servicen
        original_user_inputs  # En dictionary eller objekt med de oprindelige, fulde brugerinput (for reference)
):
    """
    Bygger prompten for Trin 2 AI (Narrativ Udkast AI / Terapi-AI),
    der skal generere det første, komplette, narrativt rige historieudkast
    samt refleksionsspørgsmål.
    """

    prompt_parts = [
        "SYSTEM INSTRUKTION: Du er en yderst kreativ og empatisk AI-assistent med speciale i at skrive engagerende børnehistorier. Du har dyb viden om narrativ terapi og pædagogik og forstår, hvordan man bruger historiefortælling til at støtte børns følelsesmæssige udvikling. Din opgave er at skrive et komplet, narrativt rigt historieudkast samt 1-2 åbne refleksionsspørgsmål baseret på nedenstående information.",
        "Outputtet skal starte med historiens TITEL på den allerførste linje. Efter titlen, indsæt ET ENKELT LINJESKIFT, og start derefter selve historieteksten. Efter historieteksten, indsæt en linje med '--- REFLEKSIONSSPØRGSMÅL ---', efterfulgt af 1-2 nummererede refleksionsspørgsmål på separate linjer.",
        "---"
    ]

    prompt_parts.append("DEL 1: BRUGERENS ØNSKER OG BARNETS PROFIL (FRA TRIN 1 BRIEF):")
    prompt_parts.append("Dette er en opsummering af, hvad brugeren har angivet:")
    prompt_parts.append(structured_brief)  # Indsæt hele det brief, vi genererede i Trin 1
    prompt_parts.append("---")

    if rag_context:
        prompt_parts.append("DEL 2: RELEVANT VIDEN FRA NARRATIV TERAPI (RAG KONTEKST):")
        prompt_parts.append(
            "Brug følgende principper og eksempler fra narrativ terapi til at informere din historie. Integrer dem naturligt og kreativt:")
        for i, chunk in enumerate(rag_context):
            prompt_parts.append(f"   - RAG Kontekst Uddrag #{i + 1}: \"{chunk}\"")
        prompt_parts.append("---")
    else:
        prompt_parts.append("DEL 2: RELEVANT VIDEN FRA NARRATIV TERAPI (RAG KONTEKST):")
        prompt_parts.append(
            "(Ingen specifik RAG-kontekst blev fundet for denne forespørgsel. Baser din historie på generel viden om narrativ terapi og brugerens input.)")
        prompt_parts.append("---")

    # Her kan vi eventuelt inkludere dele af original_user_inputs igen, hvis der er detaljer
    # som briefet måske har opsummeret for meget, f.eks. specifikke navne på relationer,
    # eller hvis AI'en skal have adgang til den helt rå tekst for 'narrative_focus'.
    # For nu antager vi, at 'structured_brief' er dækkende nok sammen med RAG.
    # Vi kan tilføje original_user_inputs['narrative_focus'] for klarhed:
    if original_user_inputs and original_user_inputs.get('narrative_focus'):
        prompt_parts.append("DEL 3: SPECIFIKT NARRATIVT FOKUS (FRA BRUGERENS OPRINDELIGE INPUT):")
        prompt_parts.append(f"Husk, det centrale tema er: \"{original_user_inputs.get('narrative_focus')}\"")
        prompt_parts.append("---")

    prompt_parts.append("DEL 4: DIN OPGAVE SOM HISTORIEFORFATTER:")
    prompt_parts.append(
        "1.  **Skriv en Komplet Historie:** Skab en fængslende og alderssvarende børnehistorie (titel + brødtekst).")
    prompt_parts.append("2.  **Integrer Narrativ Teori (meget vigtigt):**")
    prompt_parts.append(
        "    - **Eksternaliser Problemet:** Baseret på brugerens 'Narrative Fokus' (og eventuel RAG-kontekst), giv problemet en ydre, håndterbar form (f.eks. en figur, en ting, en kraft). Gør det til en aktiv del af historien.")
    prompt_parts.append(
        "    - **Fremhæv Barnets Styrker:** Væv barnets (protagonistens) angivne styrker og ressourcer aktivt ind i plottet som løsningsstrategier. Vis, hvordan disse styrker hjælper med at håndtere det eksternaliserede problem.")
    prompt_parts.append(
        "    - **Udforsk Unikke Udfald:** Inkorporer øjeblikke, hvor problemet *ikke* har fuld magt, eller hvor protagonisten viser modstand, mestring eller en alternativ positiv respons. Forstør disse små sejre.")
    prompt_parts.append(
        "    - **Skab et Styrkende Re-fortællingsnarrativ:** Historien skal bevæge sig fra problem-mættet til løsnings- og styrke-mættet. Den skal give en følelse af håb, handlekraft (agency) og positiv udvikling for protagonisten.")
    prompt_parts.append(
        "    - **Subtil Morale:** Hvis en morale er ønsket (fra brugerinput), skal den integreres organisk som en indsigt, protagonisten opnår, ikke som en direkte pegefinger.")
    prompt_parts.append(
        "3.  **Målgruppe:** Tilpas sprog, kompleksitet og temaer til barnets alder (angivet i briefet).")
    prompt_parts.append("4.  **Undgå Negativer:** Respekter eventuelle 'Må IKKE indeholde' fra brugerinput.")
    prompt_parts.append(
        "5.  **Afslutning:** Sørg for en positiv og tryg afslutning, der er passende for en godnathistorie. Følg eventuelle specifikke instruktioner for afslutningen fra briefet.")
    prompt_parts.append(
        "6.  **Generer Refleksionsspørgsmål:** Efter historien, skriv 1-2 åbne, ikke-ledende refleksionsspørgsmål. Spørgsmålene skal relatere sig til historiens tema og protagonistens oplevelser og opfordre barnet til at reflektere over egne følelser og handlemuligheder. Start hvert spørgsmål på en ny linje og nummerer dem (f.eks. '1. Hvad tror du...?', '2. Hvordan ville du...?').")

    prompt_parts.append("\nSTRUKTUR FOR DIT OUTPUT:")
    prompt_parts.append("TITEL PÅ HISTORIEN")
    prompt_parts.append("(enkelt linjeskift)")
    prompt_parts.append("Selve historieteksten her...")
    prompt_parts.append("...")
    prompt_parts.append("--- REFLEKSIONSSPØRGSMÅL ---")
    prompt_parts.append("1. Dit første refleksionsspørgsmål her.")
    prompt_parts.append("2. Dit andet refleksionsspørgsmål her (hvis relevant).")

    return "\n".join(prompt_parts)


# Eksempel på hvordan funktionen kan kaldes (til test)
if __name__ == '__main__':
    example_structured_brief = """
STRUKTURERET OPSUMMERING AF BRUGERINPUT:
========================================
1. NARRATIVT FOKUS (TEMA/UDFORDRING):
   - Min datter på 6 år er bange for mørke og monstre under sengen.
2. ØNSKET UDGANG/MÅL FOR HISTORIEN:
   - At hun føler sig mere modig og tryg ved sengetid.
3. INFORMATION OM BARNET:
   - Navn: Lily
   - Alder: 6
   - Styrker/Ressourcer: Fantasifuld, God til at tegne, Elsker sin bamse Bruno
   - Værdier/Overbevisninger: Ikke angivet
   - Dybeste Ønske/Motivation: Vil gerne sove med lyset slukket
   - Typisk Reaktion på Udfordring: Ikke angivet
   - Vigtige Relationer: Bamse Bruno (tryghedsgiver), Mor (hjælper)
4. GENERELLE HISTORIEELEMENTER:
   - Hovedkarakter (hvis forskellig fra barnet): Ikke angivet
   - Sted(er) for historien: Ikke angivet
   - Plot-elementer/Ønsket Morale: Ikke angivet
   - Må IKKE indeholde: Ingen rigtige monstre, der er onde
========================================
    """
    example_rag_context = [
        "Externalisering: Et af narrativ terapiens mest magtfulde redskaber. Det handler om at adskille et problem fra identiteten – f.eks. at se 'vrede' som en 'vred trold'. Dette reducerer skam og øger handlekraft.",
        "Unikke Udfald: Narrativ terapi søger aktivt efter øjeblikke, hvor problemet ikke havde fuld magt, eller hvor barnet udviste modstand eller mestring. Disse små sejre forstørres."
    ]
    example_original_inputs = {
        "narrative_focus": "Min datter på 6 år er bange for mørke og monstre under sengen.",
        "child_age": "6"
        # ... andre originale input kan tilføjes her for fuldstændighed ...
    }

    drafting_prompt = build_narrative_drafting_prompt(
        structured_brief=example_structured_brief,
        rag_context=example_rag_context,
        original_user_inputs=example_original_inputs
    )
    print(drafting_prompt)