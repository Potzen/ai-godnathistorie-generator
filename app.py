# === Importer nødvendige biblioteker ===
from flask import Flask, render_template, request, jsonify
import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# === Konfiguration af Google AI API Nøgle ===
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    raise ValueError("Ingen GOOGLE_API_KEY fundet. Sæt den via WSGI fil (Plan B) eller Environment Variables på Web-fanen.")
else:
    genai.configure(api_key=google_api_key)
    print("Google AI API Key configured successfully.")

# === Opret Flask App ===
app = Flask(__name__)

# === Routes (URL stier) ===

@app.route('/')
def index():
    """ Viser hovedsiden ved at rendere index.html filen. """
    return render_template('index.html')

# --- Route for historie-generering ('/generate') ---
@app.route('/generate', methods=['POST'])
def generate_story():
    """ Modtager brugerinput, bygger den FULDE detaljerede prompt, kalder Gemini, og returnerer historien. """
    data = request.get_json()
    print("Modtaget data for /generate:", data)

    # Hent alle inputs
    karakterer_data = data.get('karakterer', [{'description': 'en glad sky', 'name': ''}])
    steder_liste = data.get('steder', ['højt oppe på himlen'])
    plots_liste = data.get('plots', ['legede med solen'])
    laengde = data.get('laengde', 'mellem')
    mood = data.get('mood', 'neutral')
    listeners = data.get('listeners', [])
    is_interactive = data.get('interactive', False)
    print(f"Valgt længde: {laengde}, Valgt stemning: {mood}, Lyttere: {listeners}, Interaktiv: {is_interactive}")

    # Forbered grundlæggende strenge (karakter, sted, plot)
    if not karakterer_data: karakterer_data = [{'description': 'en glad sky', 'name': ''}]
    if not steder_liste: steder_liste = ['højt oppe på himlen']
    if not plots_liste: plots_liste = ['legede med solen']

    karakter_descriptions_for_prompt = []
    for char_obj in karakterer_data:
        desc = char_obj.get('description','').strip(); name = char_obj.get('name','').strip()
        if desc: # Kræv mindst en beskrivelse
            karakter_descriptions_for_prompt.append(f"{desc} ved navn {name}" if name else desc)
    # Sørg for default hvis listen ender tom
    karakter_str = ", ".join(karakter_descriptions_for_prompt) if karakter_descriptions_for_prompt else "en glad sky"

    sted_str = ", ".join(steder_liste) if steder_liste else "højt oppe på himlen"
    plot_str = ", ".join(plots_liste) if plots_liste else "legede med solen"
    print(f"Input til historie: Karakterer='{karakter_str}', Steder='{sted_str}', Plots='{plot_str}'")

    # Definer Længde-instruktion og max_tokens (bruger tegn for mega_lang)
    length_instruction = ""
    max_tokens_setting = 1000
    if laengde == 'kort':
        length_instruction = "Skriv historien i cirka 3-4 korte afsnit."
        max_tokens_setting = 400
    elif laengde == 'lang':
        length_instruction = "Skriv historien i cirka 10-14 afsnit. Sørg for god detaljegrad."
        max_tokens_setting = 3000
    elif laengde == 'mega_lang':
        length_instruction = "Skriv en **meget lang og dybdegående** historie på **mindst 9000 tegn**. Historien skal have flere faser, udvikling for karaktererne, mange detaljerede beskrivelser og gerne flere sammenhængende begivenheder eller del-eventyr. Undgå at afslutte historien for tidligt."
        max_tokens_setting = 8000
    else: # Default til 'mellem'
        length_instruction = "Skriv historien i cirka 6-8 afsnit."
        max_tokens_setting = 1000
    print(f"Længde instruktion: {length_instruction}, Max Tokens: {max_tokens_setting}")

    # Definer MERE SPECIFIK stemnings-instruktion
    mood_instruction = ""
    if mood == 'sød': mood_instruction = "Historien skal have en **meget sød, hjertevarm og kærlig stemning**. Fokusér på venskab, omsorg, glæde og positive følelser."
    elif mood == 'sjov': mood_instruction = "Historien skal have en **tydelig humoristisk, fjollet og sjov tone**. Brug gerne overdrivelser, skøre situationer eller uventede, komiske hændelser. Den skal være let og få lytteren til at grine."
    elif mood == 'eventyr': mood_instruction = "Historien skal være et **klassisk eventyr med magi, fantasi og måske en lille rejse eller opgave**. Skab en fortryllende og eventyrlig atmosfære."
    elif mood == 'spændende': mood_instruction = "Skriv en **spændende historie med fremdrift og suspense (passende for børn)**. Byg op til en udfordring, et mysterium eller en opdagelse. Skab en følelse af forventning, men undgå at gøre det for skræmmende."
    elif mood == 'rolig': mood_instruction = "Skriv en **meget rolig, blid og afslappende historie**. Fokusér på sanseindtryk, natur, tryghed, hygge og et langsomt tempo. Undgå konflikter og pludselige hændelser. Perfekt til at falde i søvn til."
    elif mood == 'mystisk': mood_instruction = "Historien skal have en **mystisk og hemmelighedsfuld stemning**. Brug elementer som gåder, skjulte steder, uforklarlige hændelser eller en følelse af undren. Hold det nysgerrighedsvækkende, ikke uhyggeligt."
    elif mood == 'hverdagsdrama': mood_instruction = "Historien skal handle om et **genkendeligt hverdagsdrama eller en lille konflikt (passende for børn)**. Det kan være at miste noget, blive uvenner (og gode venner igen), overvinde en lille frygt, eller lære noget nyt. Fokusér på følelser og en realistisk (men positiv) løsning."
    elif mood == 'uhyggelig': mood_instruction = "Historien skal have en **uhyggelig og lettere dyster stemning**. Fokusér på skygger, lyde i mørket, ukendte ting og en følelse af spænding/mystik, men sørg for en **meget tryg og positiv opløsning** til sidst, hvor alt viser sig at være ufarligt eller venligt."
    # Byg streng til prompt
    mood_prompt_part = f"Stemning: {mood_instruction}" if mood_instruction else "Stemning: Neutral / Blandet."
    print(f"Stemnings instruktion (til prompt): {mood_prompt_part}")

    # Byg Lytter Kontekst og Afslutnings-instruktion
    listener_context_instruction = ""; names_list_for_ending = []
    if listeners:
        listener_descriptions = []; ages = []
        for listener in listeners:
            name = listener.get('name'); age = listener.get('age')
            desc = name if name else 'et barn'
            if age: desc += f" på {age} år"; ages.append(age)
            if name: names_list_for_ending.append(name)
            listener_descriptions.append(desc)
        if listener_descriptions:
             listener_context_instruction = f"INFO OM LYTTEREN(E): Denne historie skal læses højt for {', '.join(listener_descriptions)}. Tilpas venligst sprog, tone og kompleksitet, så det passer til denne målgruppe (aldre: {', '.join(ages)})."

    ending_instruction = ""
    if names_list_for_ending:
        ending_instruction = f"VIGTIGT OM AFSLUTNINGEN: Afslut historien med et kort (1-2 sætninger) beroligende afsnit, der opsummerer historiens positive følelse og skaber en rolig overgang til, at lytteren ({', '.join(names_list_for_ending)}) nu skal sove. Du kan bruge navnet/navnene i denne afsluttende del (f.eks. 'Sov nu godt, {names_list_for_ending[0]}'). Henvend dig IKKE direkte til lytteren med navn MIDT i selve historien, KUN i denne specifikke afslutning."
    else:
        ending_instruction = "VIGTIGT OM AFSLUTNINGEN: Afslut historien med et kort (1-2 sætninger) beroligende afsnit, der opsummerer historiens positive følelse og skaber en rolig overgang til, at lytteren nu skal sove. Henvend dig IKKE direkte til lytteren midt i historien."


    # Definer safety_settings (KORREKT UDSKREVET)
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }

    # Definer generation_config
    generation_config = genai.types.GenerationConfig(
        max_output_tokens=max_tokens_setting, # Bruger den justerede værdi
        temperature=0.7
    )

    # === Byg Prompt baseret på Interaktiv Status (RETTET INDRYKNING/SYNTAX) ===
    prompt = ""
    plot_morale_line = f"Plot/Elementer/Morale (kan være en ting, en hændelse eller et tema/morale historien skal illustrere): {plot_str}"

    if is_interactive:
        # Sørg for korrekt indrykning her
        print("Bygger FULD INTERAKTIV prompt...")
        interactive_rules = """
        REGLER FOR INDDRAGENDE EVENTYR MED EKSPLICITTE VALG-STIER:
        1. Fortæl historien flydende. Inkluder 2-3 steder, hvor hovedpersonen står over for et simpelt valg med 2-3 klare muligheder (nummerér eller bogstavér dem, f.eks. (1), (2) eller (A), (B)).
        2. Præsenter valget og mulighederne tydeligt for lytteren. Afslut præsentationen med en klar opfordring til lytteren om at vælge, f.eks.: "Hvad skal [Karakter] gøre nu? Vælg (A) eller (B):".
        3. KONSEKVENS-SNIPPETS: Umiddelbart EFTER opfordringen til at vælge, skriv **korte, separate tekst-afsnit** for **HVER** af de mulige valg. Start hvert afsnit tydeligt med markøren for valget og en klar indikation, f.eks.:
           "Valg (A): [Kort beskrivelse af hvad der sker ved valg A]..."
           "Valg (B): [Kort beskrivelse af hvad der sker ved valg B]..."
           (Disse snippets skal være relativt korte (1-3 sætninger)).
        4. SAMMENFLETNING (REVIDERET): **Direkte efter** alle konsekvens-snippets, skriv et **nyt afsnit**, der **sømløst fortsætter hovedhistorien uden at opsummere eller referere direkte** til de lige præsenterede valgmuligheder eller deres specifikke konsekvens-snippets. **Undgå helt** formuleringer som "Uanset om X skete eller Y skete...". Start blot med at beskrive karakterens næste handling, observation eller hvad der sker i omgivelserne. Eksempel: "Lidt efter stod [Karakter] igen og så sig omkring i [Stedet]..." eller "Pludselig lød der en ny lyd fra...".
        5. Fortsæt hovedhistorien efter sammenfletnings-afsnittet indtil næste valgpunkt eller slutningen.
        6. Følg stadig de generelle regler for tone, sprog og børnevenlighed.
        """
        # Sørg for korrekt indrykning af f-strengen
        prompt = f"""
{listener_context_instruction}

---
OPGAVE: Skriv et INDDRAGENDE eventyr baseret på følgende, og følg de specifikke regler nedenfor:
Længde: {length_instruction}
{mood_prompt_part}
Hovedpersoner: {karakter_str}
Steder: {sted_str}
{plot_morale_line}

{interactive_rules}

GENERELLE REGLER (gælder stadig):
- Historien skal være på dansk.
- Den skal være positiv og børnevenlig.
- Den skal være simpel med klar begyndelse, midte og slutning.
- Undgå alt voldeligt og upassende for børn (hold 'uhyggelig' stemning passende).
- {ending_instruction}
---
Start historien her:
"""
    # Sørg for korrekt indrykning af else
    else: # Hvis IKKE interaktiv
        # Sørg for korrekt indrykning her
        print("Bygger FULD NORMAL prompt...")
        # Sørg for korrekt indrykning af f-strengen
        prompt = f"""
{listener_context_instruction}

---
OPGAVE: Skriv en godnathistorie baseret på følgende:
Længde: {length_instruction}
{mood_prompt_part}
Hovedpersoner: {karakter_str}
Steder: {sted_str}
{plot_morale_line}
GENERELLE REGLER:
- Historien skal være på dansk.
- Den skal være positiv og børnevenlig.
- Den skal være simpel med klar begyndelse, midte og slutning.
- Historien skal bære præg af en godnathistorie
- Undgå alt voldeligt og upassende for børn (hold 'uhyggelig' stemning passende).
- {ending_instruction}
---
Start historien her:
"""

    # Ryd op i prompten (korrekt indrykning her)
    prompt = "\n".join(line.strip() for line in prompt.strip().splitlines() if line.strip())
    print(f"--- Sender FULD Prompt til Gemini (Max Tokens: {max_tokens_setting}) ---\n{prompt}\n------------------------------")

    # --- API Kald og Respons Håndtering ---
    try:
        # Sørg for korrekt indrykning her
        print("Initialiserer Gemini model...")
        model = genai.GenerativeModel('gemini-1.5-pro-latest') # Bruger Pro model
        print("Bruger model: gemini-1.5-pro-latest")

        print("Sender anmodning til Google Gemini...")
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings
            )
        print("Svar modtaget fra Google Gemini.")
        try:
            actual_story = response.text
        except ValueError as e:
             print(f"Svar blokeret af sikkerhedsfilter: {e}"); print(f"Prompt Feedback: {response.prompt_feedback}")
             actual_story = "Beklager, historien kunne ikke laves, da indholdet blev blokeret af sikkerhedsfiltre. Prøv med andre ord."
    except Exception as e:
        print(f"Fejl ved kald til Google Gemini: {e}")
        actual_story = f"Beklager, jeg kunne ikke lave en historie lige nu på grund af en fejl: {e}. Prøv venligst igen."

    # Sørg for korrekt indrykning her
    return jsonify(story=actual_story)

# === Start Webserveren (Ignoreres af PythonAnywhere) ===
# Sørg for korrekt indrykning her
if __name__ == '__main__':
    app.run(debug=True)