# Fil: routes/story_routes.py (Korrekt og fuld version)
from flask import Blueprint, request, jsonify, current_app, Response
import traceback
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from flask_login import login_required, current_user
from prompts.story_generation_prompt import build_story_prompt
from services.ai_service import (
    generate_story_text_from_gemini,
    generate_image_prompt_from_gemini,
    generate_image_with_vertexai,
    generate_gemini_tts_audio,
    refine_story_for_lix
)

story_bp = Blueprint('story', __name__, template_folder='../templates', static_folder='../static')

@story_bp.route('/generate', methods=['POST'])
def generate_story():
    data = request.get_json()
    if not data:
        return jsonify(title="Fejl", story="Ingen data modtaget."), 400
    current_app.logger.info(f"Modtaget data for /generate: {data}")

    # 1. Udpak alle nødvendige data fra request
    karakterer_data = data.get('karakterer', [])
    steder_liste = data.get('steder', [])
    plots_liste = data.get('plots', [])
    laengde = data.get('laengde', 'kort')
    mood = data.get('mood', 'neutral')
    listeners = data.get('listeners', [])
    is_interactive = data.get('interactive', False)
    is_bedtime_story = data.get('is_bedtime_story', False)
    negative_prompt_text = data.get('negative_prompt', '').strip()
    selected_model_from_frontend = data.get('selected_model')

    current_app.logger.info(f"--- generate_story route: is_interactive flag from frontend: {is_interactive} ---")

    # 2. Bearbejd data til prompt-strenge
    karakter_descriptions_for_prompt = []
    if karakterer_data:
        for char_obj in karakterer_data:
            desc = char_obj.get('description', '').strip()
            name = char_obj.get('name', '').strip()
            if desc:
                karakter_descriptions_for_prompt.append(f"{desc} ved navn {name}" if name else desc)
    karakter_str = ", ".join(karakter_descriptions_for_prompt) if karakter_descriptions_for_prompt else "en uspecificeret karakter"

    valid_steder = [s.strip() for s in steder_liste if s and s.strip()]
    sted_str = ", ".join(valid_steder) if valid_steder else "et uspecificeret sted"

    valid_plots = [p.strip() for p in plots_liste if p and p.strip()]
    plot_str = ", ".join(valid_plots) if valid_plots else "et uspecificeret eventyr"

    mood_instruction_map = {
        'sød': "Historien skal have en **meget sød, hjertevarm og kærlig** stemning.",
        'sjov': "Historien skal have en **tydelig humoristisk og sjov** tone, gerne med absurde eller skøre elementer.",
        'eventyr': "Historien skal være **eventyrlig og magisk**, fyldt med opdagelser og undren.",
        'spændende': "Historien skal være **spændende og medrivende**, med en vis grad af mystik eller udfordringer.",
        'rolig': "Historien skal have en **meget rolig, afslappende og beroligende** stemning, perfekt til at falde i søvn til.",
        'mystisk': "Historien skal have en **mystisk og gådefuld** stemning, hvor ikke alt er, som det ser ud.",
        'hverdagsdrama': "Historien skal omhandle **hverdagsdrama med små, genkendelige konflikter** og løsninger, passende for børn.",
        'uhyggelig': "Historien skal have en **let uhyggelig, men ikke skræmmende**, stemning, passende for en godnathistorie hvor lidt gys er ok."
    }
    mood_prompt_part = mood_instruction_map.get(mood, "Stemning: Neutral / Blandet.")

    # VIGTIG RETTELSE: Initialiser ending_instruction FØR if-blokken
    ending_instruction = "VIGTIGT OM AFSLUTNINGEN: Afslut historien på en positiv og opløftende måde."

    listener_context_instruction = ""
    if listeners:
        names_list_for_ending = []
        listener_descriptions = []
        for listener_item in listeners:
            name = listener_item.get('name', '').strip()
            age_str = listener_item.get('age', '').strip()
            desc = name if name else 'et barn'
            if age_str:
                desc += f" på {age_str} år"
            if name:
                names_list_for_ending.append(name)
            listener_descriptions.append(desc)

        if listener_descriptions:
            listener_context_instruction = f"INFO OM LYTTEREN(E): Historien læses højt for {', '.join(listener_descriptions[:-1])}{' og ' if len(listener_descriptions) > 1 else ''}{listener_descriptions[-1] if listener_descriptions else 'et barn'}."
            listener_context_instruction += " Tilpas sprog og temaer, så de er passende og engagerende for denne/disse lytter(e)."

        if is_bedtime_story:
            if names_list_for_ending:
                ending_instruction = (f"VIGTIGT OM AFSLUTNINGEN: Afslut historien på en positiv og tryg måde. "
                                      f"Som en ALLER SIDSTE sætning i historien, efter selve handlingen er afsluttet, sig 'Sov godt, {', '.join(names_list_for_ending[:-1])}{' og ' if len(names_list_for_ending) > 1 else ''}{names_list_for_ending[-1] if names_list_for_ending else 'lille ven'}! Drøm sødt.' "
                                      f"Denne afslutning skal KUN være den sidste sætning. Henvend dig IKKE direkte til lytteren midt i historien.")
            else:
                ending_instruction = "VIGTIGT OM AFSLUTNINGEN: Afslut historien på en positiv, tryg og beroligende måde, der er passende for en godnathistorie. Henvend dig IKKE direkte til lytteren midt i historien."

    # 3. Bestem AI-model og indstillinger
    target_model_name = 'gemini-1.5-flash-latest'
    # Tjek for brugerens rolle, hvis du har et login-system
    # For nu antager vi, at valget fra frontend er det primære
    if selected_model_from_frontend:
         target_model_name = selected_model_from_frontend

    pro_model_identifier = 'gemini-2.5-pro-preview-05-06'
    if target_model_name == pro_model_identifier:
        if laengde == 'kort':
            length_instruction = "Skriv historien i cirka 6-8 afsnit. Den skal være relativt kortfattet, men velformuleret."
            max_tokens_setting = 3072
        elif laengde == 'mellem':
            length_instruction = "Skriv historien i cirka 10-14 sammenhængende afsnit. Den skal føles som en mellemlang historie med passende dybde."
            max_tokens_setting = 4096
        else: # lang
            length_instruction = "Skriv en **meget lang og detaljeret historie** på **mindst 15-18 fyldige afsnit**. Sørg for en dybdegående fortælling."
            max_tokens_setting = 8192
    else:  # Standard for 'gemini-1.5-flash-latest'
        if laengde == 'kort':
            length_instruction = "Skriv historien i cirka 6-8 korte, sammenhængende afsnit."
            max_tokens_setting = 1500
        elif laengde == 'mellem':
            length_instruction = "Skriv historien i cirka 10-14 sammenhængende afsnit. Den skal føles som en mellemlang historie."
            max_tokens_setting = 3000
        else: # lang
            length_instruction = "Skriv en **meget lang og detaljeret historie** på **mindst 15 fyldige afsnit**, gerne flere. Sørg for en dybdegående fortælling."
            max_tokens_setting = 7000

    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
    generation_config_dict = {
        "max_output_tokens": max_tokens_setting,
        "temperature": 0.7
    }

    # 4. Byg prompten
    prompt = build_story_prompt(
        karakter_str=karakter_str,
        sted_str=sted_str,
        plot_str=plot_str,
        length_instruction=length_instruction,
        mood_prompt_part=mood_prompt_part,
        listener_context_instruction=listener_context_instruction,
        ending_instruction=ending_instruction,
        negative_prompt_text=negative_prompt_text,
        is_interactive=is_interactive,
        is_bedtime_story=is_bedtime_story
    )

    # 5. Kald AI service
    try:
        story_title, actual_story_content = generate_story_text_from_gemini(
            full_prompt_string=prompt,
            generation_config_settings=generation_config_dict,
            safety_settings_values=safety_settings,
            target_model_name=target_model_name
        )
    except Exception as e:
        current_app.logger.error(f"Fejl ved kald til ai_service: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "Intern serverfejl under historiegenerering."}), 500

    return jsonify(title=story_title, story=actual_story_content)


@story_bp.route('/generate_lix', methods=['POST'])
@login_required
def generate_lix_story_route():
    """
    API endpoint til Læsehesten-modulet.
    Bygger en avanceret "one-shot" prompt og kalder AI'en én gang.
    """
    if current_user.role not in ['basic', 'premium']:
        return jsonify({"error": "Læsehesten er en Premium-funktion."}), 403

    data = request.get_json()
    if not data:
        return jsonify(error="Ingen data modtaget."), 400

    current_app.logger.info(f"Bruger {current_user.id}: Modtaget anmodning til /generate_lix med data: {data}")

    # --- 1. Indsaml og valider input ---
    target_lix = data.get('target_lix')
    if not isinstance(target_lix, int) or not (5 <= target_lix <= 55):
        return jsonify(error="Ugyldigt eller manglende LIX-tal."), 400

    story_elements = data.get('elements', [])
    custom_words = data.get('custom_words', [])
    karakter_str = ", ".join(story_elements + custom_words) if (
                story_elements or custom_words) else "en uspecificeret karakter"

    plot_str = data.get('plot', 'et uspecificeret eventyr')
    laengde = data.get('laengde', 'mellem')
    mood = data.get('mood', 'neutral')
    negative_prompt_text = data.get('negative_prompt', '').strip()
    focus_letter = data.get('focus_letter', '')

    # --- 2. Forbered AI-konfiguration ---
    target_model_name = 'gemini-2.5-pro-preview-05-06'

    length_map = {
        'kort': ("Skriv historien i cirka 6-8 afsnit.", 3072),
        'mellem': ("Skriv historien i cirka 10-14 afsnit.", 4096),
        'lang': ("Skriv en lang historie på mindst 15-18 afsnit.", 8192)
    }
    length_instruction, max_tokens_setting = length_map.get(laengde, length_map['mellem'])

    generation_config_dict = {"max_output_tokens": max_tokens_setting, "temperature": 0.75}
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    # --- 3. Byg den smarte prompt og kald AI'en ÉN gang ---
    # --- 3. Byg den smarte prompt og kald AI'en (med genforsøg) ---
    final_title, final_content, final_lix, error_message = None, None, None, None
    max_retries = 2  # Prøv op til 2 gange

    for attempt in range(max_retries):
        try:
            current_app.logger.info(f"Bruger {current_user.id}: Starter genereringsforsøg #{attempt + 1}")

            # Juster temperaturen en smule på andet forsøg for at fremprovokere et andet resultat
            current_temp = generation_config_dict.get("temperature", 0.75)
            if attempt > 0:
                generation_config_dict["temperature"] = min(current_temp + 0.1, 1.0)  # Gør temperaturen lidt højere
                current_app.logger.info(
                    f"Genforsøg #{attempt + 1}: Justerer temperaturen til {generation_config_dict['temperature']}")

            final_prompt = build_story_prompt(
                karakter_str=karakter_str,
                sted_str="et passende sted for historien",
                plot_str=plot_str,
                length_instruction=length_instruction,
                mood_prompt_part=f"Historien skal have en {mood} stemning.",
                listener_context_instruction="",
                ending_instruction="Afslut historien på en positiv og opløftende måde.",
                negative_prompt_text=negative_prompt_text,
                focus_letter=focus_letter,
                target_lix=target_lix
            )

            current_app.logger.info(
                f"Bruger {current_user.id}: Kalder AI med 'one-shot' LIX-prompt (forsøg #{attempt + 1}).")

            final_title, final_content = generate_story_text_from_gemini(
                full_prompt_string=final_prompt,
                generation_config_settings=generation_config_dict,
                safety_settings_values=safety_settings,
                target_model_name=target_model_name
            )

            # Tjek for fejl/blokering. Hvis der er en, vil den kaste en exception og vi ryger til 'except' blokken
            if "Fejl" in final_title or "blokeret" in final_content:
                # Dette er en sikkerhedsforanstaltning, men den primære fejl fanges af .text accessoren
                raise ValueError("Generering blokeret af AI-tjenesten.")

            # Hvis vi når hertil, var forsøget en succes. Beregn lix og afslut loopet.
            from services.lix_service import calculate_lix
            final_lix = calculate_lix(final_content)
            error_message = None  # Nulstil eventuel tidligere fejl
            current_app.logger.info(f"Bruger {current_user.id}: Succesfuld generering på forsøg #{attempt + 1}.")
            break  # Afslut loopet ved succes

        except Exception as e:
            error_message = str(e)
            current_app.logger.error(
                f"Fejl under 'one-shot' LIX-generering for bruger {current_user.id} (forsøg #{attempt + 1}): {e}\n{traceback.format_exc()}")
            if attempt == max_retries - 1:
                # Sidste forsøg er fejlet. Send en brugervenlig besked i stedet for en 500-fejl.
                current_app.logger.error(
                    f"Alle {max_retries} forsøg fejlede for bruger {current_user.id}. Returnerer brugervenlig fejlbesked.")
                return jsonify(
                    status="all_attempts_failed",
                    title="Historien kunne ikke skabes",
                    story=(
                        "Vi beklager! AI'en kunne desværre ikke skabe en historie med de valgte indstillinger, selv efter flere forsøg. "
                        "Dette sker nogle gange med meget specifikke eller ekstreme LIX-tal.\n\n"
                        "Prøv venligst igen med et lidt andet LIX-tal eller andre elementer."
                    )
                )
    # --- 4. Returner det endelige resultat ---
    response_data = {
        "title": final_title,
        "story": final_content,
        "final_lix_score": final_lix,
        "status": "success"
    }

    LIX_TOLERANCE = 5
    if final_lix is not None and abs(final_lix - target_lix) > LIX_TOLERANCE:
        response_data[
            'warning_message'] = f"Historien blev genereret med LIX {final_lix}, hvilket afviger lidt fra målet på {target_lix}. AI'en gør sit bedste, men præcis LIX-styring er svær!"

    return jsonify(response_data)

@story_bp.route('/generate_image_from_story', methods=['POST'])
@login_required
def generate_image_from_story():
    data = request.get_json()
    if not data or 'story_text' not in data:
        return jsonify({"error": "Mangler 'story_text'."}), 400
    story_text = data.get('story_text')
    try:
        image_prompt = generate_image_prompt_from_gemini(story_text)
        image_data_url = generate_image_with_vertexai(image_prompt)
        if image_data_url:
            return jsonify({"image_url": image_data_url, "image_prompt_used": image_prompt})
        else:
            return jsonify({"error": "Kunne ikke generere billede."}), 500
    except Exception as e:
        current_app.logger.error(f"Fejl under billedgenerering: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "Intern serverfejl under billedgenerering."}), 500

@story_bp.route('/generate_audio', methods=['POST'])
@login_required
def generate_audio():
    if current_user.role not in ['basic', 'premium']:
        return jsonify({"error": "Adgang nægtet."}), 403
    data = request.get_json()
    story_text = data.get('text')
    voice_name = data.get('voice_name', 'Zephyr')
    if not story_text:
        return jsonify({"error": "Ingen tekst modtaget."}), 400
    try:
        audio_stream = generate_gemini_tts_audio(story_text, voice_name)
        return Response(audio_stream, mimetype='audio/mpeg')
    except Exception as e:
        current_app.logger.error(f"Fejl ved lydgenerering: {e}\n{traceback.format_exc()}")
        return jsonify({"error": f"Fejl ved generering af lyd: {str(e)}"}), 500