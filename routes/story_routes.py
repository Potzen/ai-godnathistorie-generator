# Fil: routes/story_routes.py
from flask import Blueprint, request, jsonify, current_app
import google.generativeai as genai
import traceback
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import base64
import time
from vertexai.preview.vision_models import ImageGenerationModel
from prompts.story_generation_prompt import build_story_prompt
from services.ai_service import (
    generate_story_text_from_gemini,
    generate_image_prompt_from_gemini,
    generate_image_with_vertexai
)

story_bp = Blueprint('story', __name__, template_folder='../templates', static_folder='../static')


@story_bp.route('/generate', methods=['POST'])
def generate_story():
    data = request.get_json()
    if not data:
        return jsonify(title="Fejl", story="Ingen data modtaget."), 400
    current_app.logger.info(f"Modtaget data for /generate: {data}")

    karakterer_data = data.get('karakterer')
    steder_liste = data.get('steder')
    plots_liste = data.get('plots')
    laengde = data.get('laengde', 'kort')
    mood = data.get('mood', 'neutral')
    listeners = data.get('listeners', [])
    is_interactive = data.get('interactive', False)
    negative_prompt_text = data.get('negative_prompt', '').strip()
    # current_app.logger.info(
    #     f"Valgt længde: {laengde}, Valgt stemning: {mood}, Lyttere: {listeners}, Interaktiv: {is_interactive}, Negativ Prompt: '{negative_prompt_text}'")

    karakter_descriptions_for_prompt = []
    if karakterer_data:
        for char_obj in karakterer_data:
            desc = char_obj.get('description', '').strip()
            name = char_obj.get('name', '').strip()
            if desc: karakter_descriptions_for_prompt.append(f"{desc} ved navn {name}" if name else desc)
    karakter_str = ", ".join(
        karakter_descriptions_for_prompt) if karakter_descriptions_for_prompt else "en uspecificeret karakter"

    valid_steder = []
    if steder_liste: valid_steder = [s.strip() for s in steder_liste if s and s.strip()]
    sted_str = ", ".join(valid_steder) if valid_steder else "et uspecificeret sted"

    valid_plots = []
    if plots_liste: valid_plots = [p.strip() for p in plots_liste if p and p.strip()]
    plot_str = ", ".join(valid_plots) if valid_plots else "et uspecificeret eventyr"

    # current_app.logger.info(
    #     f"Input til historie (behandlet): Karakterer='{karakter_str}', Steder='{sted_str}', Plot/Morale='{plot_str}'")

    length_instruction = ""
    max_tokens_setting = 1000
    if laengde == 'mellem':
        length_instruction = "Skriv historien i cirka 10-14 sammenhængende afsnit. Den skal føles som en mellemlang historie."
        max_tokens_setting = 3000
    elif laengde == 'lang':
        length_instruction = "Skriv en **meget lang og detaljeret historie** på **mindst 15 fyldige afsnit**, gerne flere. Sørg for en dybdegående fortælling."
        max_tokens_setting = 7000
    else:  # kort
        length_instruction = "Skriv historien i cirka 6-8 korte, sammenhængende afsnit."
        max_tokens_setting = 1500
    # current_app.logger.info(f"Længde instruktion: {length_instruction}, Max Tokens: {max_tokens_setting}")

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
    # current_app.logger.info(f"Stemnings instruktion (til prompt): {mood_prompt_part}")

    listener_context_instruction = ""
    names_list_for_ending = []
    if listeners:
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

    ending_instruction = "VIGTIGT OM AFSLUTNINGEN: Afslut historien på en positiv og tryg måde, der er passende for en godnathistorie. Henvend dig IKKE direkte til lytteren midt i historien."
    if names_list_for_ending:
        ending_instruction = (f"VIGTIGT OM AFSLUTNINGEN: Afslut historien på en positiv og tryg måde. "
                              f"Som en ALLER SIDSTE sætning i historien, efter selve handlingen er afsluttet, sig 'Sov godt, {', '.join(names_list_for_ending[:-1])}{' og ' if len(names_list_for_ending) > 1 else ''}{names_list_for_ending[-1] if names_list_for_ending else 'lille ven'}! Drøm sødt.' "
                              f"Denne afslutning skal KUN være den sidste sætning. Henvend dig IKKE direkte til lytteren midt i historien.")

    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }
    generation_config_dict = {
        "max_output_tokens": max_tokens_setting,
        "temperature": 0.7
    }
    # Byg prompten ved hjælp af den nye funktion fra prompts/story_generation_prompt.py
    prompt = build_story_prompt(
        karakter_str=karakter_str,
        sted_str=sted_str,
        plot_str=plot_str,
        length_instruction=length_instruction,
        mood_prompt_part=mood_prompt_part,
        listener_context_instruction=listener_context_instruction,
        ending_instruction=ending_instruction,
        negative_prompt_text=negative_prompt_text,
        is_interactive=is_interactive
    )

    current_app.logger.info(
        f"--- story_routes: Forbereder kald til ai_service for historie (Max Tokens: {generation_config_dict.get('max_output_tokens')}) ---")

    try:
        story_title, actual_story_content = generate_story_text_from_gemini(
            prompt,
            generation_config_dict,
            safety_settings
        )
        current_app.logger.info(f"story_routes: Modtaget '{story_title}' fra ai_service.")
    except Exception as e:
        current_app.logger.error(
            f"story_routes: Fejl ved kald til ai_service.generate_story_text_from_gemini: {e}\n{traceback.format_exc()}")
        story_title = "Fejl (Rute Service Kald)"
        actual_story_content = "Der opstod en intern fejl under forsøg på at generere historien via AI-tjenesten."

    return jsonify(title=story_title, story=actual_story_content)


@story_bp.route('/generate_image_from_story', methods=['POST'])
def generate_image_from_story():
    data = request.get_json()
    if not data or 'story_text' not in data:
        current_app.logger.error("story_routes: Mangler 'story_text' i /generate_image_from_story anmodning.")
        return jsonify({"error": "Mangler 'story_text' i anmodningen."}), 400

    story_text = data.get('story_text')
    if not story_text.strip():
        current_app.logger.error("story_routes: 'story_text' er tom i /generate_image_from_story anmodning.")
        return jsonify({"error": "'story_text' må ikke være tom."}), 400

    current_app.logger.info(
        f"story_routes: Modtaget anmodning til /generate_image_from_story. Historielængde: {len(story_text)}")

    # Trin 1: Generer billedprompten via ai_service
    try:
        current_app.logger.info("story_routes: Kalder ai_service for at generere billedprompt...")
        image_prompt = generate_image_prompt_from_gemini(story_text)
        if not image_prompt:
            current_app.logger.warning("story_routes: Modtog ingen (eller standard) billedprompt fra ai_service.")
    except Exception as e_prompt_service:
        current_app.logger.error(
            f"story_routes: Fejl ved kald til ai_service.generate_image_prompt_from_gemini: {e_prompt_service}\n{traceback.format_exc()}")
        return jsonify({"error": "Fejl under generering af billedbeskrivelse.",
                        "image_prompt_used": "Fejl under promptgenerering"}), 500

    current_app.logger.info(f"story_routes: Billedprompt modtaget fra ai_service (delvis): {image_prompt[:100]}...")

    # Trin 2: Generer selve billedet via ai_service med den genererede prompt
    image_data_url = None
    try:
        current_app.logger.info("story_routes: Kalder ai_service for at generere billede med Vertex AI...")
        image_data_url = generate_image_with_vertexai(image_prompt)
    except Exception as e_image_service:
        current_app.logger.error(
            f"story_routes: Fejl ved kald til ai_service.generate_image_with_vertexai: {e_image_service}\n{traceback.format_exc()}")
        return jsonify(
            {"error": "Fejl under selve billedgenereringen via AI-tjenesten.", "image_prompt_used": image_prompt}), 500

    if image_data_url:
        current_app.logger.info("story_routes: Billede genereret succesfuldt via ai_service.")
        return jsonify({
            "message": "Billede genereret!",
            "image_url": image_data_url,
            "image_prompt_used": image_prompt
        })
    else:
        current_app.logger.error("story_routes: ai_service returnerede intet billede (None).")
        return jsonify({"error": "Billedgeneratoren kunne ikke skabe et billede efter flere forsøg. Prøv igen.",
                        "image_prompt_used": image_prompt}), 500

# Her ville generate_audio senere blive tilføjet, hvis vi arbejdede på den:
# @story_bp.route('/generate_audio', methods=['POST'])
# def generate_audio():
#     # Logik for lydgenerering, der kalder en funktion i ai_service.py
#     pass