def build_quiz_generation_prompt(story_content: str, lix_score: int) -> str:
    """
    Bygger en prompt til at generere en multiple-choice quiz baseret på en historie.
    """

    difficulty_instruction = ""
    if lix_score <= 20:
        difficulty_instruction = "Spørgsmålene skal være meget simple og direkte. De skal teste genkaldelse af information, som er eksplicit nævnt i teksten. Brug simple ord i både spørgsmål og svar."
    elif 21 <= lix_score <= 35:
        difficulty_instruction = "Spørgsmålene må gerne kræve en smule forståelse og sammenfatning af information. Svarene skal kunne findes relativt let i teksten."
    else:
        difficulty_instruction = "Spørgsmålene må gerne være mere udfordrende og kræve, at man drager simple konklusioner baseret på teksten. Ordbrugen kan være mere avanceret."

    prompt = f"""
SYSTEM INSTRUKTION:
Du er en pædagogisk assistent, der er ekspert i at lave læseforståelses-opgaver for børn. Din opgave er at generere en kort multiple-choice quiz baseret på den vedlagte historie.

KRITISKE REGLER FOR DIT OUTPUT:
1.  Dit output SKAL være en valid JSON-array.
2.  Arrayet skal indeholde PRÆCIS 4 objekter.
3.  Hvert objekt repræsenterer et spørgsmål og skal have følgende nøgler: "question" (en streng), "options" (en liste med PRÆCIS 4 streng-svar), og "correct_answer_index" (et heltal fra 0 til 3, der angiver det korrekte svar i 'options'-listen).

HISTORIE TIL ANALYSE:
---
{story_content}
---

DIN OPGAVE:
Generer nu en quiz med 4 spørgsmål baseret på historien. Følg disse retningslinjer:

-   **Sværhedsgrad:** {difficulty_instruction}
-   **Korrekthed:** Sørg for, at kun ét svar er korrekt. De andre tre svar skal være plausible, men forkerte (distraktorer).
-   **Format:** Returner KUN det færdige JSON-array, intet andet.

Eksempel på det forventede JSON-format:
[
  {{
    "question": "Hvad fandt musen i skoven?",
    "options": ["En gulerod", "Et gyldent agern", "En rød bold", "En venlig ugle"],
    "correct_answer_index": 1
  }},
  ... (tre spørgsmål mere)
]
"""
    return prompt