# Fil: prompts/narrative_drafting_prompt.py

def build_narrative_drafting_prompt(
        structured_brief,
        rag_context,
        original_user_inputs,
        continuation_context=None  # NYT: Modtager nu kontekst for fortsættelse
):
    """
    Bygger prompten for Trin 2 AI (Narrativ Udkast AI / Terapi-AI).
    Kan nu håndtere at skabe en fortsættelse baseret på continuation_context.
    """

    prompt_parts = [
        "SYSTEM INSTRUKTION: Du er en yderst kreativ og empatisk AI-assistent med speciale i at skrive engagerende børnehistorier. Du har dyb viden om narrativ terapi og pædagogik og forstår, hvordan man bruger historiefortælling til at støtte børns følelsesmæssige udvikling. Din opgave er at skrive et komplet, narrativt rigt historieudkast baseret på nedenstående information.",
        "Outputtet skal starte med historiens TITEL på den allerførste linje. Efter titlen, indsæt ET ENKELT LINJESKIFT, og start derefter selve historieteksten. Returner KUN titel og historietekst.",
        "---"
    ]

    # NYT: Tilføjelse af Kontekst-sektion HVIS det er en fortsættelse
    if continuation_context:
        strategy = continuation_context.get('strategy')
        problem_name = continuation_context.get('problem_name')
        method_name = continuation_context.get('discovered_method_name')

        context_header = "DEL 0: KONTEKST FOR FORTSÆTTELSE (MEGET VIGTIGT!)"
        context_body = ""

        if strategy == 'deepen':
            context_body = (
                f"Dette er en fortsættelse. Protagonisten har allerede opdaget en metode kaldet '{method_name}' til at håndtere problemet '{problem_name}'.\n"
                f"Den nye historie skal handle om, hvordan protagonisten **forfiner, opgraderer eller bruger denne metode på en ny måde** i mødet med det **samme problem** ('{problem_name}'). "
                "Fokus er på at bygge selvtillid og mestre metoden i en velkendt situation."
            )
        elif strategy == 'generalize':
            context_body = (
                f"Dette er en fortsættelse. Protagonisten skal nu anvende sin kendte og lærte metode, '{method_name}', til at løse en **helt ny og anderledes udfordring**.\n"
                f"Den nye historie skal illustrere, hvordan styrken eller metoden er fleksibel og kan bruges i andre sammenhænge. Problemet '{problem_name}' fra den forrige historie skal IKKE være hovedfokus her."
            )

        prompt_parts.append(context_header)
        prompt_parts.append(context_body)
        prompt_parts.append("---")

    prompt_parts.append(
        "DEL 1: BRUGERENS ØNSKER OG BARNETS PROFIL (FRA TRIN 1 BRIEF - DETTE ER DIN PRIMÆRE OG ULTIMATIVE GUIDE FOR HISTORIENS INDHOLD, INPUT SKAL ANVENDES I HISTORIEN):")
    prompt_parts.append(
        "Dette er en detaljeret opsummering af, hvad brugeren har angivet, og som din historie SKAL baseres nøje på, alle navne og input skal indgå i din historie. Dette er ufravigeligt:")
    prompt_parts.append(structured_brief)
    prompt_parts.append("---")

    if rag_context:
        prompt_parts.append("DEL 2: RELEVANT VIDEN FRA NARRATIV TERAPI (RAG KONTEKST):")
        prompt_parts.append(
            "Brug følgende principper og eksempler fra narrativ terapi til at informere din historie. Integrer dem naturligt og kreativt, hvor det passer med informationen fra DEL 1 - HUSK at som udgangspunkt skal input givet af brugeren indgå i historien, særligt eksternalisering herunder navn på problemet:")
        for i, chunk in enumerate(rag_context):
            prompt_parts.append(f"   - RAG Kontekst Uddrag #{i + 1}: \"{chunk}\"")
    else:
        prompt_parts.append("DEL 2: RELEVANT VIDEN FRA NARRATIV TERAPI (RAG KONTEKST):")
        prompt_parts.append(
            "(Ingen specifik RAG-kontekst blev fundet for denne forespørgsel. Baser din historie på generel viden om narrativ terapi og brugerens input fra DEL 1 og DEL 3.)")
    prompt_parts.append("---")

    if original_user_inputs and original_user_inputs.get('narrative_focus'):
        prompt_parts.append(
            "DEL 3: DET CENTRALE NARRATIVE FOKUS (FRA BRUGERENS OPRINDELIGE INPUT - UDDYBER PUNKT 1 I BRIEFET):")
        prompt_parts.append(
            f"Husk, det absolut centrale tema, som historien skal kredse om og belyse, er: \"{original_user_inputs.get('narrative_focus')}\". Problem-karakteren (beskrevet i DEL 1) er en manifestation af dette fokus.")
    prompt_parts.append("---")

    prompt_parts.append("DEL 4: DIN OPGAVE SOM HISTORIEFORFATTER:")

    story_length_preference = original_user_inputs.get('length', 'mellem')
    length_instruction_text = ""
    target_paragraph_count_text = ""

    if story_length_preference == 'kort':
        length_instruction_text = "Historien skal være KORT."
        target_paragraph_count_text = "Generer en historie på PRÆCIS 6 til 8 KORTE afsnit. Det er afgørende, at du ikke overskrider 8 afsnit."
    elif story_length_preference == 'mellem':
        length_instruction_text = "Historien skal være MELLEMLANG."
        target_paragraph_count_text = "Generer en historie på PRÆCIS 10 til 14 sammenhængende afsnit."
    elif story_length_preference == 'lang':
        length_instruction_text = "Historien skal være LANG OG DETALJERET."
        target_paragraph_count_text = "Generer en historie på PRÆCIS 15 til 18 fyldige afsnit. Undgå at skrive væsentligt mere end 18 afsnit."
    else:
        length_instruction_text = "Historien skal have en passende mellemlængde."
        target_paragraph_count_text = "Generer en historie på cirka 10-14 afsnit."

    prompt_parts.append(
        f"!! KRITISK INSTRUKTION - HISTORIENS LÆNGDE: {length_instruction_text} {target_paragraph_count_text} Overholdelse af dette er din vigtigste opgave udover at skabe en god historie. Undgå unødvendig fyldtekst, hvis en kortere historie er ønsket.")

    prompt_parts.append(
        "YDERLIGERE OPGAVER (udfør disse inden for den specificerede længderamme og baseret på informationen i DEL 1, 2 og 3):")

    prompt_parts.append(
        "   A.  **Skriv en Komplet Historie:** Skab en fængslende og alderssvarende børnehistorie (titel + brødtekst). "
        "**DIN VIGTIGSTE OPGAVE ER AT OVERHOLDE FØLGENDE UFRAVIGELIGE REGLER FOR BRUGERDEFINEREDE ELEMENTER. DETTE TRUMFER DIN EGEN KREATIVE FORTOLKNING AF, HVAD DER 'PASSER BEDST':**"
        "\n       1.  **Problem-Karakterens Navn/Identitet:** Hvis et specifikt navn/identitet er angivet for problem-karakteren i briefets sektion 4 (f.eks. 'LarmeFrans'), **SKAL DU BRUGE PRÆCIS DETTE NAVN/DENNE IDENTITET, OG INTET ANDET, HVER GANG PROBLEM-KARAKTEREN NÆVNES ELLER REFERERES TIL.** Dette gælder, selvom du internt mener, at et andet navn ville passe bedre teoretisk eller narrativt. Brugerens valg af navn for problem-karakteren er ABSOLUT og må IKKE ændres, omskrives eller erstattes."
        "\n       2.  **Andre Hovedkarakterers Navne:** Hvis navne er angivet for andre hovedkarakterer i briefets sektion 5 (f.eks. 'Ræven Mikkel'), SKAL disse navne bruges PRÆCIST som angivet."
        "\n       3.  **Sted(er):** Hvis specifikke steder er angivet i briefets sektion 5 (f.eks. 'Rumskib'), SKAL historien primært foregå på disse steder, eller de skal spille en central og genkendelig rolle, der bruger det/de angivne navne for stederne."
        "\n       **VIGTIGT ORDVALG (Problem-Karakter og Generelt):** Undgå at opfinde og bruge ikke-dansk-klingende eller mærkelige ord som f.eks. 'Sniken' til at navngive karakterer (specielt problem-karakteren) eller fænomener, MEDMINDRE et sådant specifikt eller usædvanligt navn eksplicit er leveret af brugeren i briefets sektion 4 (Problem-Karakterens Navn/Identitet) eller sektion 5 (Andre Hovedkarakterer). Din prioritet er ALTID at bruge de navne, brugeren har angivet. Hvis intet brugernavn er givet for problem-karakteren, og du skal beskrive den, brug da almindeligt dansk ordforråd i børne højde eller en neutral, beskrivende betegnelse (f.eks. 'Mørket', 'Angsten', 'Drilleånden' eller det der passer bedste til historien) fremfor at opfinde nye, potentielt uheldige navne."
        "\n       **Generelt for alle bruger-definerede elementer fra briefet (DEL 1): Betragt dem som faste, ikke-forhandlingsbare instruktioner. Din kreative opgave er at væve en god, narrativt funderet historie *omkring* disse faste elementer, ikke at ændre dem.**")

    prompt_parts.append("   B.  **Integrer Narrativ Teori (meget vigtigt):**")
    prompt_parts.append(
        "       - **Eksternaliser Problemet:** Baseret på brugerens 'Narrative Fokus' (fra DEL 3) OG de **specifikke detaljer for PROBLEM-KARAKTEREN angivet i briefet (DEL 1)**, giv problemet en ydre, håndterbar form. "
        "**Husk REGEL A.1: BRUG DET SPECIFIKKE NAVN/IDENTITET for problem-karakteren, som er angivet i briefets sektion 4, som den primære og ENESTE betegnelse for det eksternaliserede problem gennem HELE historien.** "
        "Gør denne korrekt navngivne problem-karakter til en aktiv og central del af historien, og brug dens angivne rolle, formål, adfærd og indflydelse som beskrevet i briefet.")
    prompt_parts.append(
        "       - **Fremhæv Barnets Styrker:** Væv barnets (protagonistens) angivne styrker og ressourcer (fra briefet i DEL 1) aktivt ind i plottet som løsningsstrategier. Vis, hvordan disse styrker hjælper med at håndtere den (korrekt navngivne) eksternaliserede problem-karakter.")
    prompt_parts.append(
        "       - **Udforsk Unikke Udfald:** Inkorporer øjeblikke, hvor problemet *ikke* har fuld magt, eller hvor protagonisten viser modstand, mestring eller en alternativ positiv respons (baseret på information i briefet i DEL 1, f.eks. 'Typisk Reaktion på Udfordring' og hvordan dette kan ændres). Forstør disse små sejre.")
    prompt_parts.append(
        "       - **Skab et Styrkende Re-fortællingsnarrativ:** Historien skal bevæge sig fra problem-mættet til løsnings- og styrke-mættet. Den skal give en følelse af håb, handlekraft (agency) og positiv udvikling for protagonisten, i tråd med 'ØNSKET UDVIKLING/MÅL FOR HISTORIEN' i briefet (DEL 1).")
    prompt_parts.append(
        "       - **Subtil Morale:** Hvis en morale er ønsket (fra briefet i DEL 1), skal den integreres organisk som en indsigt, protagonisten opnår, ikke som en direkte pegefinger.")
    prompt_parts.append(
        "   C.  **Målgruppe:** Tilpas sprog, kompleksitet og temaer til barnets alder (angivet i briefet i DEL 1).")
    prompt_parts.append(
        "   D.  **Undgå Negativer:** Respekter eventuelle 'Elementer der IKKE skal med i historien' fra briefet (DEL 1).")
    prompt_parts.append(
        "   E.  **Afslutning:** Sørg for en positiv og tryg afslutning, der er passende for en godnathistorie. Følg eventuelle specifikke instruktioner for afslutningen fra briefet (DEL 1).")

    prompt_parts.append("\nSTRUKTUR FOR DIT OUTPUT (VIGTIGT AT FØLGE PRÆCIST):")
    prompt_parts.append("TITEL PÅ HISTORIEN")
    prompt_parts.append("(enkelt linjeskift her)")
    prompt_parts.append("Selve historieteksten her...")
    prompt_parts.append("...historien fortsætter...")
    prompt_parts.append("...historien slutter her.")

    return "\n".join(prompt_parts)