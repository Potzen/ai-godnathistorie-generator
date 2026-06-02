# Fil: prompts/problem_image_prompt.py

def build_problem_image_prompt(narrative_data: dict) -> str:
    """
    Bygger en prompt til at generere et billede, der eksternaliserer et problem
    fra en narrativ historie, baseret på narrative data.
    """
    problem_name = narrative_data.get('narrative_problem_identity_name') or "en udefineret bekymring"
    problem_behavior = narrative_data.get('narrative_problem_behavior_action') or "at føles overvældende"
    mood = narrative_data.get('mood', 'tænksom')

    mood_map = {
        'håbefuld': 'hopeful, gentle light',
        'tænksom': 'thoughtful, slightly melancholic, muted colors',
        'magisk': 'magical, ethereal, glowing particles',
        'eventyrlig': 'adventurous, vibrant',
        'rolig': 'calm, serene, soft focus',
        'sjov': 'whimsical, quirky, playful'
    }
    mood_description = mood_map.get(mood, 'neutral tone')

    prompt = (
        f"Task: Create a visual prompt in ENGLISH for an AI image generator (Imagen). "
        f"The goal is to create a symbolic and child-friendly visualization of an abstract problem, based on the principles of narrative therapy. This is called 'externalizing the problem'.\n\n"

        f"CRITICAL INSTRUCTIONS FOR THE ENGLISH PROMPT:\n"
        f"1.  **DO NOT DEPICT A CHILD OR ANY HUMAN-LIKE FIGURE.** The image must focus solely on the visual metaphor for the problem itself. This is non-negotiable.\n"
        f"2.  **Externalize, Don't Frighten:** The goal is to make the problem a tangible 'character' or 'object', not a terrifying monster. It should be something a child can observe from a distance, perhaps with a touch of mystery or peculiarity, but not horror. The tone should be symbolic.\n"
        f"3.  **Use Provided Details:** Base the visualization on the Danish details provided below.\n"
        f"    - The problem's name/identity is: '{problem_name}'.\n"
        f"    - Its behavior is: '{problem_behavior}'.\n"
        f"    - The desired mood is: '{mood_description}'.\n"
        f"4.  **Structure and Style:** Start the prompt with the main subject. The prompt must end with: 'Style: high-quality 3D digital illustration, symbolic, child-friendly, imaginative, cinematic lighting.'\n\n"

        f"DANISH CONTEXT (for your understanding):\n"
        f" - Problem Navn: {problem_name}\n"
        f" - Problem Adfærd: {problem_behavior}\n"
        f" - Stemning: {mood}\n\n"
        f"GENERATE THE ENGLISH VISUAL PROMPT NOW:"
    )
    return prompt