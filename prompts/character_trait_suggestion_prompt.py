# Fil: prompts/character_trait_suggestion_prompt.py

def build_character_trait_suggestion_prompt(narrative_focus):
    """
    Bygger en prompt til AI'en for at få forslag til karaktertræk baseret
    på et narrativt fokus. Instruerer AI'en til at returnere output som JSON.

    Args:
        narrative_focus (str): Det centrale tema, udfordring eller fokus for historien.

    Returns:
        str: Den færdigbyggede prompt-streng.
    """
    prompt_parts = []

    prompt_parts.append("SYSTEM INSTRUKTION: Du er en AI-assistent med ekspertise i narrativ pædagogik og karakterdesign for børnehistorier. Din opgave er at foreslå karaktertræk for to typer karakterer baseret på et givent narrativt fokus. Dit output SKAL være en valid JSON-formateret streng.")
    prompt_parts.append("---")

    prompt_parts.append(f"NARRATIVT FOKUS (Tema/Udfordring): \"{narrative_focus}\"")
    prompt_parts.append("---")

    prompt_parts.append("OPGAVE: Baseret på ovenstående narrative fokus, generer forslag til karaktertræk for følgende to karaktertyper:")

    prompt_parts.append("\n1. PROBLEM-KARAKTER (En eksternalisering af problemet/udfordringen):")
    prompt_parts.append("   - Forslag til Identitet/Navn (f.eks. 'Bekymringsmonsteret', 'Tvivls-skyggen')")
    prompt_parts.append("   - Forslag til Rolle/Funktion i historien (hvordan manifesterer problemet sig?)")
    prompt_parts.append("   - Forslag til Formål/Intention (hvad 'ønsker' problemet at opnå for hovedpersonen, utilsigtet eller ej?)")
    prompt_parts.append("   - Forslag til Adfærd/Handling (hvordan opfører problem-karakteren sig typisk?)")
    prompt_parts.append("   - Forslag til Indflydelse på hovedpersonen (hvordan påvirker den hovedpersonen?)")

    prompt_parts.append("\n2. PROTAGONIST/HJÆLPER-KARAKTER (Typisk barnet eller en støttende figur):")
    prompt_parts.append("   - Forslag til Styrker (som kan hjælpe med at håndtere det narrative fokus)")
    prompt_parts.append("   - Forslag til Værdier (som er relevante for det narrative fokus)")
    prompt_parts.append("   - Forslag til Motivation/Ønske (i relation til det narrative fokus)")
    prompt_parts.append("   - Forslag til Typisk Adfærd/Reaktion (når konfronteret med det narrative fokus)")
    prompt_parts.append("   - Forslag til Vigtige Relationer (som kan støtte eller være en del af løsningen)")
    prompt_parts.append("---")

    prompt_parts.append("OUTPUT FORMAT INSTRUKTION:")
    prompt_parts.append("Returner dit svar som en enkelt JSON-formateret streng. JSON-objektet skal have to nøgler på øverste niveau: 'problem_character_suggestions' og 'protagonist_character_suggestions'.")
    prompt_parts.append("Hver af disse nøgler skal have et objekt som værdi, hvor nøglerne er de specifikke karaktertræk (f.eks. 'identity_name', 'role_function' for problem-karakteren, og 'strengths', 'values' for protagonisten). Værdierne skal være strenge eller lister af strenge med dine forslag.")
    prompt_parts.append("Eksempel på outputstruktur (kun for illustration, dine forslag vil være anderledes):")
    prompt_parts.append("""
    ```json
    {
      "problem_character_suggestions": {
        "identity_name": ["Navneforslag 1", "Navneforslag 2"],
        "role_function": ["Rolleforslag 1"],
        "purpose_intention": ["Formålsforslag 1"],
        "behavior_action": ["Adfærdsforslag 1", "Adfærdsforslag 2"],
        "influence_on_protagonist": ["Indflydelsesforslag 1"]
      },
      "protagonist_character_suggestions": {
        "strengths": ["Styrkeforslag 1", "Styrkeforslag 2"],
        "values": ["Værdiforslag 1"],
        "motivation_wish": ["Motivationsforslag 1"],
        "typical_behavior_reaction": ["Reaktionsforslag 1"],
        "important_relations": ["Relationsforslag 1", "Relationsforslag 2"]
      }
    }
    ```
    """)
    prompt_parts.append("Sørg for at JSON'en er valid. Generer KUN JSON-strengen.")

    return "\n\n".join(prompt_parts)