# Fil: routes/story_routes.py (Korrekt og fuld version)
from flask import Blueprint, request, jsonify, current_app, Response
import traceback
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from flask_login import login_required, current_user
from models import Story
from extensions import db
from prompts.story_generation_prompt import build_story_prompt
from services.ai_service import (
    generate_story_text_from_gemini,
    generate_image_prompt_from_gemini,
    generate_image_with_vertexai,
    generate_gemini_tts_audio
)
from services.lix_service import calculate_lix
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.api_core.exceptions import InternalServerError

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

    pro_model_identifier = 'gemini-2.5-pro-preview-06-05'
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
    API endpoint til Læsehesten.
    Bruger nu ét API-kald til at generere flere kandidater for robusthed og effektivitet.
    """
    # ... (hele sektionen med dataindsamling og prompt-bygning er uændret) ...
    if current_user.role not in ['basic', 'premium']:
        return jsonify({"error": "Læsehesten er en Premium-funktion."}), 403
    data = request.get_json()
    if not data:
        return jsonify(error="Ingen data modtaget."), 400
    current_app.logger.info(f"Bruger {current_user.id}: Modtaget LIX-anmodning: {data}")
    target_lix = data.get('target_lix')
    story_elements = data.get('elements', [])
    custom_words = data.get('custom_words', [])
    karakter_str = ", ".join(story_elements + custom_words) if (
                story_elements or custom_words) else "en uspecificeret karakter"
    plot_str = data.get('plot', 'et uspecificeret eventyr')
    laengde = data.get('laengde', 'mellem')
    mood = data.get('mood', 'neutral')
    negative_prompt_text = data.get('negative_prompt', '').strip()
    focus_letter = data.get('focus_letter', '')
    length_map = {
        'kort': ("Skriv historien i cirka 6-8 afsnit.", 3072),
        'mellem': ("Skriv historien i cirka 10-14 afsnit.", 4096),
        'lang': ("Skriv en lang historie på mindst 15-18 afsnit.", 8192)
    }
    length_instruction, max_tokens_setting = length_map.get(laengde, length_map['mellem'])
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
    final_prompt = build_story_prompt(
        karakter_str=karakter_str, sted_str="et passende sted for historien", plot_str=plot_str,
        length_instruction=length_instruction, mood_prompt_part=f"Historien skal have en {mood} stemning.",
        listener_context_instruction="", ending_instruction="Afslut historien på en positiv og opløftende måde.",
        negative_prompt_text=negative_prompt_text, focus_letter=focus_letter, target_lix=target_lix
    )

    successful_story = None
    used_fallback = False

    try:
        # Første forsøg: Bed Pro-modellen om 3 svar på én gang
        pro_model_name = 'gemini-2.5-pro-preview-06-05'
        generation_config_dict = {"max_output_tokens": max_tokens_setting, "temperature": 0.85}

        current_app.logger.info(f"Forsøger at generere 3 kandidater med {pro_model_name}")
        results = generate_story_text_from_gemini(
            final_prompt, generation_config_dict, safety_settings, pro_model_name, number_of_results=3
        )

        # Find den første succesfulde historie fra resultaterne
        for title, content in results:
            if "Fejl" not in title and "blokeret" not in content:
                successful_story = {"title": title, "content": content}
                break

        if not successful_story:
            raise InternalServerError("Alle kandidater fra Pro-modellen fejlede eller blev blokeret.")

    except (InternalServerError, ValueError) as e:
        current_app.logger.warning(f"Pro-model fejlede: {e}. Aktiverer fallback til Flash-model.")
        try:
            fallback_model = 'gemini-1.5-flash-latest'
            gen_config = {"max_output_tokens": 7000, "temperature": 0.7}
            # Bed Flash-modellen om ét enkelt, sikkert svar
            results = generate_story_text_from_gemini(final_prompt, gen_config, safety_settings, fallback_model,
                                                      number_of_results=1)

            if results and "Fejl" not in results[0][0]:
                successful_story = {"title": results[0][0], "content": results[0][1]}
                used_fallback = True
            else:
                raise ValueError("Fallback-modellen fejlede også.")

        except Exception as fallback_e:
            current_app.logger.error(f"Fallback-model fejlede: {fallback_e}")
            return jsonify({"error": "Kunne desværre ikke skabe historien. Begge AI-modeller fejlede."}), 500

    # --- Håndter svar (denne del er næsten uændret) ---
    final_title = successful_story["title"]
    final_content = successful_story["content"]
    from services.lix_service import calculate_lix
    final_lix = calculate_lix(final_content)

    response_data = {"title": final_title, "story": final_content, "final_lix_score": final_lix, "status": "success"}
    warning_messages = []
    if used_fallback:
        warning_messages.append(
            "Historien blev skabt med vores standard AI-model, da Pro-modellen var midlertidigt utilgængelig.")
    LIX_TOLERANCE = 5
    if final_lix is not None and abs(final_lix - target_lix) > LIX_TOLERANCE:
        warning_messages.append(
            f"Historien blev genereret med LIX {final_lix}, hvilket afviger lidt fra målet på {target_lix}.")
    if warning_messages:
        response_data['warning_message'] = " ".join(warning_messages)

    return jsonify(response_data)


# I routes/story_routes.py
@story_bp.route('/generate_image_from_story', methods=['POST'])
@login_required
def generate_image_from_story():
    data = request.get_json()
    if not data or 'story_text' not in data:
        return jsonify({"error": "Mangler 'story_text'."}), 400

    # Hent alle data fra request
    story_text = data.get('story_text')
    karakterer_data = data.get('karakterer', [])
    steder_liste = data.get('steder', [])

    # Bearbejd brugerinput (genbrugt logik fra /generate)
    karakter_descriptions = [
        f"{char.get('description', '')} ved navn {char.get('name', '')}".strip()
        for char in karakterer_data if char.get('description')
    ]
    karakter_str = ", ".join(karakter_descriptions) if karakter_descriptions else "en uspecificeret karakter"
    sted_str = ", ".join(filter(None, steder_liste)) if steder_liste else "et uspecificeret sted"

    try:
        # Kald service-funktionen med de nye argumenter
        image_prompt = generate_image_prompt_from_gemini(story_text, karakter_str, sted_str)
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


@story_bp.route('/save_to_logbook', methods=['POST'])
@login_required
def save_story_to_logbook():
    """
    Modtager en historie genereret i Højtlæsning og gemmer den som en logbogs-entry.
    """
    if not request.is_json:
        return jsonify({"error": "Anmodning skal være JSON."}), 415

    data = request.get_json()
    title = data.get('title')
    content = data.get('content')

    if not title or not content:
        return jsonify({"error": "Både titel og indhold er påkrævet."}), 400

    try:
        # Opret en ny Story-instans i databasen
        new_story = Story(
            title=title,
            content=content,
            user_id=current_user.id,
            source='Højtlæsning',  # Angiver hvor historien kommer fra
            is_log_entry=True  # Markerer den med det samme som en logbogs-entry
        )
        db.session.add(new_story)
        db.session.commit()

        current_app.logger.info(
            f"Bruger {current_user.id} gemte Højtlæsnings-historie '{title}' til logbogen (Ny ID: {new_story.id}).")

        return jsonify({
            "success": True,
            "message": "Historien er gemt i din logbog!",
            "story_id": new_story.id
        }), 201  # 201 Created

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Fejl ved gemning af Højtlæsnings-historie til logbog: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "En intern fejl opstod under gemning."}), 500