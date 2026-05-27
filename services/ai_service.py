from flask import current_app
from .lix_service import calculate_lix
from flask_login import current_user
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)

from google.generativeai.types import HarmCategory, HarmBlockThreshold
from vertexai.preview.vision_models import ImageGenerationModel
import base64
import time
import traceback
import vertexai
from prompts.image_prompt_generation_prompt import build_image_prompt_generation_prompt
from prompts.character_trait_suggestion_prompt import build_character_trait_suggestion_prompt
import json
from prompts.narrative_briefing_prompt import build_narrative_briefing_prompt
from prompts.narrative_drafting_prompt import build_narrative_drafting_prompt
from prompts.narrative_editing_prompt import build_narrative_editing_prompt
from .rag_service import find_relevant_chunks_v2
from prompts.narrative_question_prompt import build_narrative_question_prompt
from google.cloud.texttospeech_v1 import TextToSpeechClient, SynthesisInput, VoiceSelectionParams, AudioConfig, SsmlVoiceGender, AudioEncoding
from prompts.logbook_analysis_prompt import build_logbook_analysis_prompt
from google.api_core.exceptions import InternalServerError
from prompts.problem_image_prompt import build_problem_image_prompt
from prompts.quiz_generation_prompt import build_quiz_generation_prompt

_SAFETY_BLOCK_NONE = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

_SAFETY_BLOCK_MEDIUM = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

_tts_client = None
_imagen_model = None


def _get_tts_client():
    global _tts_client
    if _tts_client is None:
        _tts_client = TextToSpeechClient()
    return _tts_client


def _get_imagen_model():
    global _imagen_model
    if _imagen_model is None:
        _imagen_model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-002")
    return _imagen_model


TTS_VOICES = {
    "Zephyr": {"language_code": "en-US", "name": "Zephyr", "gender": "FEMALE"},
    "Dansk Kvinde 1 (Standard)": {"language_code": "da-DK", "name": "da-DK-Wavenet-A", "gender": "FEMALE"},
    "Dansk Mand 1 (Standard)": {"language_code": "da-DK", "name": "da-DK-Wavenet-C", "gender": "MALE"},
    "Dansk Mand 2 (Standard)": {"language_code": "da-DK", "name": "da-DK-Wavenet-D", "gender": "MALE"},
    "Dansk Kvinde 2 (Standard)": {"language_code": "da-DK", "name": "da-DK-Wavenet-E", "gender": "FEMALE"}
}


def generate_story_text_from_gemini(full_prompt_string, generation_config_settings, safety_settings_values,
                                    target_model_name='gemini-1.5-flash', number_of_results=1):
    """
    Genererer tekst ved hjælp af Google Gemini med op til 3 genforsøg ved fejl.
    """
    max_retries = 3
    model = genai.GenerativeModel(target_model_name)
    config = dict(generation_config_settings)
    config['candidate_count'] = number_of_results
    gen_config = genai.types.GenerationConfig(**config)

    for attempt in range(max_retries):
        current_app.logger.info(
            f"--- ai_service: Kalder Gemini (Forsøg {attempt + 1}/{max_retries}, Model: {target_model_name}) ---")

        try:
            response = model.generate_content(
                full_prompt_string,
                generation_config=gen_config,
                safety_settings=safety_settings_values
            )

            if response.prompt_feedback.block_reason:
                reason = response.prompt_feedback.block_reason.name
                current_app.logger.error(f"Prompt blokeret af sikkerhedsfilter. Årsag: {reason}. Stopper forsøg.")
                return [("Blokeret Indhold", f"Anmodning blokeret: {reason}")]

            results = []
            has_valid_content = False
            for candidate in response.candidates:
                if candidate.finish_reason == 'SAFETY':
                    ratings_str = ", ".join(
                        [f"{r.category.name}: {r.probability.name}" for r in candidate.safety_ratings])
                    results.append(("Blokeret Indhold", f"En variant blev blokeret. Årsag: {ratings_str}"))
                    continue

                if candidate.content and candidate.content.parts and candidate.content.parts[0].text.strip():
                    raw_text = candidate.content.parts[0].text
                    lines = raw_text.splitlines()
                    story_title = lines[0].strip() if lines and lines[0].strip() else "Uden Titel"
                    actual_story_content = "\n".join(lines[1:]).strip() if len(lines) > 1 else raw_text

                    results.append((story_title, actual_story_content))
                    has_valid_content = True
                else:
                    results.append(("Tomt Svar", "AI returnerede ikke noget indhold for denne variant."))

            if has_valid_content:
                current_app.logger.info(f"Succes på forsøg {attempt + 1}. Returnerer gyldigt indhold.")
                return results

            current_app.logger.warning(f"Intet gyldigt indhold på forsøg {attempt + 1}. Forsøger igen...")
            time.sleep(1.5)

        except Exception as e:
            current_app.logger.error(f"ai_service: Fejl på forsøg {attempt + 1}: {e}\n{traceback.format_exc()}")
            if attempt < max_retries - 1:
                time.sleep(1.5)
            else:
                return [("API Fejl", f"Teknisk fejl med AI-tjenesten efter {max_retries} forsøg: {e}")]

    current_app.logger.error(f"Kunne ikke generere gyldigt indhold efter {max_retries} forsøg.")
    return [("Fejl efter genforsøg", "AI kunne ikke generere indhold efter flere forsøg.")]


def generate_image_prompt_from_gemini(story_text, karakter_str, sted_str):
    """
    Genererer en billedprompt baseret på en historietekst og brugerens originale inputs.
    """
    current_app.logger.info("ai_service: Genererer billedprompt med Gemini, prioriterer brugerinput...")
    default_image_prompt = "A whimsical and enchanting fairytale illustration, child-friendly, high-quality 3D digital art, imaginative."

    try:
        gemini_model_for_prompting = genai.GenerativeModel('gemini-1.5-pro-latest')
        actual_prompt_to_gemini = build_image_prompt_generation_prompt(story_text, karakter_str, sted_str)

        response_gemini = gemini_model_for_prompting.generate_content(actual_prompt_to_gemini)

        if response_gemini.text and response_gemini.text.strip():
            generated_prompt_text = response_gemini.text.strip()
            current_app.logger.info(f"ai_service: Genereret billedprompt: {generated_prompt_text}")
            return generated_prompt_text
        else:
            current_app.logger.warning("ai_service: Gemini returnerede en tom billedprompt. Bruger standard prompt.")

    except Exception as e_gemini_prompt:
        current_app.logger.error(
            f"ai_service: Fejl under generering af billedprompt med Gemini: {e_gemini_prompt}\n{traceback.format_exc()}")

    return default_image_prompt


def generate_image_with_vertexai(image_prompt_text):
    """
    Genererer et billede ved hjælp af Vertex AI Imagen baseret på en given prompt.

    Args:
        image_prompt_text (str): Den engelske prompt, der skal bruges til billedgenerering.

    Returns:
        str or None: En base64-kodet data-URL for det genererede billede,
                     eller None hvis billedgenerering fejler efter retries.
    """
    current_app.logger.info("ai_service: Starter billedgenerering med Vertex AI Imagen...")
    current_app.logger.info(f"ai_service: Bruger billedprompt (delvis): {image_prompt_text[:100]}...")

    if not current_app.config.get('GOOGLE_CLOUD_PROJECT_ID'):
        current_app.logger.error("ai_service: FEJL - GOOGLE_CLOUD_PROJECT_ID er ikke sat. Kan ikke generere billede.")
        return None

    current_prompt_to_imagen = image_prompt_text
    image_data_url = None
    max_retries = 3
    model = _get_imagen_model()

    for attempt in range(max_retries):
        try:
            current_app.logger.info(
                f"ai_service: Imagen forsøg {attempt + 1}/{max_retries}. Prompt: {current_prompt_to_imagen[:100]}...")
            if attempt == 1:
                current_app.logger.info("ai_service: Modificerer prompt til andet Imagen-forsøg...")
                current_prompt_to_imagen += ", impressionistic oil painting"

            response_imagen = model.generate_images(
                prompt=current_prompt_to_imagen,
                number_of_images=1,
                guidance_scale=9
            )

            if response_imagen and response_imagen.images:
                image_obj = response_imagen.images[0]
                if hasattr(image_obj, '_image_bytes') and image_obj._image_bytes:
                    image_bytes = image_obj._image_bytes
                    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                    image_data_url = f"data:image/png;base64,{image_base64}"
                    current_app.logger.info("ai_service: Billede genereret succesfuldt med Vertex AI.")
                    break
                else:
                    current_app.logger.error(
                        f"ai_service: FEJL - _image_bytes mangler på billedeobjekt (forsøg {attempt + 1}).")
                    if attempt == max_retries - 1:
                        raise ValueError("EMPTY_IMAGE_BYTES_ERROR_AFTER_RETRIES")
            else:
                error_details = str(response_imagen)
                if response_imagen and hasattr(response_imagen, 'error') and response_imagen.error:
                    error_details += f" | Error Details: {response_imagen.error}"
                current_app.logger.error(
                    f"ai_service: FEJL - Vertex AI Imagen returnerede ingen billeder (forsøg {attempt + 1}). Respons: {error_details}")
                if attempt == max_retries - 1:
                    raise ValueError("EMPTY_IMAGE_LIST_ERROR_AFTER_RETRIES")

            if attempt < max_retries - 1 and not image_data_url:
                time.sleep(1.5)

        except Exception as e_attempt:
            current_app.logger.error(
                f"ai_service: Fejl i Vertex AI billedgenereringsforsøg {attempt + 1}: {e_attempt}\n{traceback.format_exc()}")
            non_retryable_errors = ["quota exceeded", "permission denied", "billing", "does not exist",
                                    "kunne ikke initialisere"]
            if any(sub.lower() in str(e_attempt).lower() for sub in non_retryable_errors) or attempt == max_retries - 1:
                current_app.logger.error(
                    f"ai_service: Ikke-genoprettelig fejl eller sidste forsøg fejlet. Stopper billedgenerering.")
                return None

            if attempt < max_retries - 1:
                time.sleep(1.5)

    if not image_data_url:
        current_app.logger.error("ai_service: Kunne ikke generere billede efter alle forsøg.")

    return image_data_url


def generate_gemini_tts_audio(text_content: str, voice_name: str = "Zephyr"):
    """
    Genererer lyd fra tekst ved hjælp af Google Text-to-Speech med
    standard Wavenet/Neural2 stemmer for streaming.

    Args:
        text_content (str): Teksten der skal konverteres til tale.
        voice_name (str): Navnet på den ønskede stemme fra TTS_VOICES.

    Yields:
        bytes: Chunks af lyddata.
    """
    logger.info(f"TTS Service: Starter lydgenerering for tekst (første 50 tegn): '{text_content[:50]}...' med stemme: {voice_name}")

    if not text_content or not text_content.strip():
        logger.warning("TTS Service: generate_gemini_tts_audio kaldt med tom tekst.")
        return

    client = _get_tts_client()

    voice_config = TTS_VOICES.get(voice_name)
    if not voice_config:
        logger.error(f"TTS Service: Ugyldigt stemmenavn '{voice_name}' valgt. Bruger standard stemme (Zephyr).")
        voice_config = TTS_VOICES["Zephyr"]

    synthesis_input = SynthesisInput(text=text_content)

    voice_selection_params = VoiceSelectionParams(
        language_code=voice_config["language_code"],
        name=voice_config["name"],
        ssml_gender=SsmlVoiceGender[voice_config["gender"]]
    )

    audio_config = AudioConfig(
        audio_encoding=AudioEncoding.MP3,
        pitch=0.0,
        speaking_rate=1.0
    )

    try:
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice_selection_params,
            audio_config=audio_config
        )

        logger.info(f"TTS Service: Modtog fuld lydrespons ({len(response.audio_content)} bytes).")

        chunk_size = 4096
        for i in range(0, len(response.audio_content), chunk_size):
            yield response.audio_content[i:i + chunk_size]

    except Exception as e:
        logger.error(f"TTS Service: Fejl under lydgenerering: {e}\n{traceback.format_exc()}")
        raise


def get_ai_suggested_character_traits(narrative_focus):
    """
    Får AI-genererede forslag til karaktertræk baseret på et narrativt fokus.
    Bruger Gemini 2.5 Pro og forventer et JSON-svar fra AI'en.

    Args:
        narrative_focus (str): Det centrale tema/udfordring.

    Returns:
        dict: Et dictionary med forslag til karaktertræk,
              eller et dictionary med en 'error' nøgle ved fejl.
    """
    user_id_for_log = current_user.id if hasattr(current_user, 'id') else 'Ukendt bruger (karaktertræk)'
    current_app.logger.info(
        f"ai_service (Bruger: {user_id_for_log}): Starter forslag til karaktertræk for fokus: '{narrative_focus}'")

    try:
        prompt_for_suggestions = build_character_trait_suggestion_prompt(narrative_focus)
        current_app.logger.debug(
            f"ai_service: Prompt til karaktertræk-forslag (delvis): {prompt_for_suggestions[:200]}...")

        model_name = 'gemini-2.5-pro-preview-06-05'
        current_app.logger.info(f"ai_service: Bruger model '{model_name}' til karaktertræk-forslag.")
        model = genai.GenerativeModel(model_name)

        generation_config_settings = {
            "max_output_tokens": 8192,
            "temperature": 0.5,
            "response_mime_type": "application/json",
        }

        response = model.generate_content(
            prompt_for_suggestions,
            generation_config=genai.types.GenerationConfig(**generation_config_settings),
            safety_settings=_SAFETY_BLOCK_MEDIUM
        )

        current_app.logger.info(
            f"ai_service (Bruger: {user_id_for_log}): Svar modtaget fra Gemini for karaktertræk.")

        try:
            if response.text:
                current_app.logger.debug(f"ai_service: Råtekst fra Gemini (karaktertræk): {response.text[:300]}...")
                cleaned_text = response.text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]

                suggested_traits = json.loads(cleaned_text.strip())
                current_app.logger.info(f"ai_service (Bruger: {user_id_for_log}): Karaktertræk parset succesfuldt.")
                return suggested_traits
            else:
                current_app.logger.error(
                    f"ai_service (Bruger: {user_id_for_log}): Tomt svar (text) fra Gemini for karaktertræk.")
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                    current_app.logger.error(f"ai_service: Prompt Feedback: {response.prompt_feedback}")
                if hasattr(response, 'candidates') and response.candidates and response.candidates[
                    0].finish_reason != 'STOP':
                    current_app.logger.error(f"ai_service: Finish reason: {response.candidates[0].finish_reason}")
                    current_app.logger.error(f"ai_service: Safety ratings: {response.candidates[0].safety_ratings}")

                return {"error": "AI returnerede et tomt svar for karaktertræk."}

        except json.JSONDecodeError as e_json:
            current_app.logger.error(
                f"ai_service (Bruger: {user_id_for_log}): Fejl ved parsing af JSON fra Gemini for karaktertræk: {e_json}")
            current_app.logger.error(f"Modtaget tekst fra AI (karaktertræk): {response.text}")
            return {"error": "Kunne ikke parse AI'ens forslag til karaktertræk (JSON formatfejl)."}
        except ValueError as e_safety:
            current_app.logger.error(
                f"ai_service (Bruger: {user_id_for_log}): Muligvis blokeret indhold fra Gemini for karaktertræk: {e_safety}")
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                current_app.logger.error(f"ai_service: Prompt Feedback: {response.prompt_feedback}")
            return {"error": "Forslag til karaktertræk blev blokeret af sikkerhedsfiltre."}
        except Exception as e_resp_text:
            current_app.logger.error(
                f"ai_service (Bruger: {user_id_for_log}): Uventet fejl ved håndtering af Gemini-svar (karaktertræk): {e_resp_text}\n{traceback.format_exc()}")
            return {"error": f"Uventet fejl ved behandling af AI-svar for karaktertræk: {str(e_resp_text)}"}

    except Exception as e:
        current_app.logger.error(
            f"ai_service (Bruger: {user_id_for_log}): Generel fejl i get_ai_suggested_character_traits: {e}\n{traceback.format_exc()}")
        return {"error": f"Intern fejl ved hentning af AI-forslag til karaktertræk: {str(e)}"}


def generate_narrative_brief(original_user_inputs: dict):
    """
    Genererer et struktureret narrativt brief ved hjælp af en AI-model (Trin 1).
    """
    current_app.logger.info("AI Service: Påbegynder generering af narrativt brief (Trin 1)...")

    try:
        prompt_string = build_narrative_briefing_prompt(original_user_inputs)
        current_app.logger.debug(
            f"AI Service: Narrativ briefing prompt bygget (længde: {len(prompt_string)}). Første 200 tegn:\n{prompt_string[:200]}")

        model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')

        generation_config_settings = {
            "max_output_tokens": 4096,
            "temperature": 0.5
        }
        gen_config = genai.types.GenerationConfig(**generation_config_settings)

        current_app.logger.info(
            f"AI Service: Kalder Gemini for narrativt brief (Max Tokens: {generation_config_settings.get('max_output_tokens')}, Temp: {generation_config_settings.get('temperature')}).")

        response = model.generate_content(
            prompt_string,
            generation_config=gen_config,
            safety_settings=_SAFETY_BLOCK_NONE
        )

        narrative_brief_text = ""
        try:
            if response.candidates and response.candidates[0].content.parts:
                finish_reason_name = response.candidates[0].finish_reason.name if hasattr(
                    response.candidates[0].finish_reason, 'name') else str(response.candidates[0].finish_reason)

                if finish_reason_name == 'STOP':
                    narrative_brief_text = response.text.strip()
                    if not narrative_brief_text:
                        current_app.logger.warning(
                            "AI Service: Narrativt brief fra Gemini var tomt, selvom finish_reason var STOP.")
                        return "Fejl: AI returnerede et tomt narrativt brief."
                    current_app.logger.info("AI Service: Narrativt brief genereret succesfuldt.")
                    current_app.logger.debug(
                        f"AI Service: Genereret narrativt brief (første 200 tegn):\n{narrative_brief_text[:200]}")
                elif finish_reason_name == 'SAFETY':
                    return "Fejl: Indhold til narrativt brief blev blokeret af sikkerhedsfilter (selvom sat til NONE). Undersøg prompt/input nærmere."
                elif finish_reason_name == 'MAX_TOKENS':
                    return "Fejl: AI ramte token-grænsen under generering af narrativt brief. Input er muligvis for langt."
                else:
                    current_app.logger.error(
                        f"AI Service: Uventet finish_reason ({finish_reason_name}) for narrativt brief. Safety Ratings: {response.candidates[0].safety_ratings}")
                    return f"Fejl: AI kunne ikke generere et komplet narrativt brief (finish_reason: {finish_reason_name})."
            else:
                current_app.logger.error(
                    "AI Service: Ingen valid 'parts' fundet i content fra Gemini for narrativt brief.")
                current_app.logger.error(
                    f"AI Service: Prompt Feedback (brief): {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'Ingen prompt feedback.'}")
                if response.candidates:
                    current_app.logger.error(f"AI Service: Candidate (brief): {response.candidates[0]}")
                return "Fejl: AI returnerede intet indhold for narrativt brief (ingen 'parts')."

        except ValueError as e_text_access:
            current_app.logger.error(
                f"AI Service: Fejl ved adgang til response.text (muligvis blokeret indhold, selv med BLOCK_NONE): {e_text_access}")
            current_app.logger.error(
                f"AI Service: Prompt Feedback (brief): {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'Ingen prompt feedback.'}")
            if hasattr(response, 'candidates') and response.candidates:
                current_app.logger.error(f"AI Service: Blocked Candidates (brief): {response.candidates}")
            return "Fejl: Kunne ikke tilgå tekst-svar fra AI for narrativt brief (muligvis blokeret)."
        except Exception as e_parse:
            current_app.logger.error(
                f"AI Service: Generel fejl ved behandling af AI-svar for narrativt brief: {e_parse}\n{traceback.format_exc()}")
            return "Fejl: Generel fejl under behandling af AI-svar for narrativt brief."

        return narrative_brief_text

    except Exception as e_api:
        current_app.logger.error(
            f"AI Service: Generel fejl under generering af narrativt brief: {e_api}\n{traceback.format_exc()}")
        return f"Fejl: Teknisk fejl i AI-tjenesten under generering af narrativt brief."


def draft_narrative_story_with_rag(
        structured_brief,
        original_user_inputs,
        narrative_focus_for_rag,
        continuation_context=None
):
    """
    Genererer et første udkast til en narrativ historie med retry-logik.
    """
    current_app.logger.info("AI Service: Påbegynder udarbejdelse af narrativ historie med RAG (Trin 2)...")

    max_retries = 2
    for attempt in range(max_retries):
        try:
            current_app.logger.info(f"Forsøg {attempt + 1}/{max_retries} på at generere narrativt udkast.")

            rag_chunks = []
            if narrative_focus_for_rag and narrative_focus_for_rag.strip():
                rag_chunks = find_relevant_chunks_v2(narrative_focus_for_rag, top_k=2)

            prompt_string = build_narrative_drafting_prompt(
                structured_brief=structured_brief,
                rag_context=rag_chunks,
                original_user_inputs=original_user_inputs,
                continuation_context=continuation_context
            )
            ai_model_name = 'gemini-2.5-pro-preview-06-05'
            model = genai.GenerativeModel(ai_model_name)
            story_length_preference = original_user_inputs.get('length', 'mellem')
            max_tokens_for_draft = 8192
            if story_length_preference == 'kort':
                max_tokens_for_draft = 2048
            elif story_length_preference == 'mellem':
                max_tokens_for_draft = 4096

            generation_config_settings = {
                "max_output_tokens": max_tokens_for_draft, "temperature": 0.6, "top_p": 0.95
            }
            gen_config = genai.types.GenerationConfig(**generation_config_settings)

            response = model.generate_content(
                prompt_string,
                generation_config=gen_config,
                safety_settings=_SAFETY_BLOCK_NONE
            )

            raw_response_text = response.text.strip()
            if not raw_response_text:
                raise ValueError("AI returnerede et tomt historieudkast.")

            title_story_parts = raw_response_text.split('\n', 1)
            story_title = title_story_parts[0].strip() if title_story_parts and title_story_parts[
                0].strip() else "Uden Titel"
            story_content = title_story_parts[1].strip() if len(title_story_parts) > 1 and title_story_parts[
                1].strip() else raw_response_text

            current_app.logger.info(f"Succes på forsøg {attempt + 1}. Returnerer historie.")

            return story_title, story_content

        except InternalServerError as e:
            current_app.logger.warning(f"Google returnerede en intern serverfejl på forsøg {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                current_app.logger.info("Venter 2 sekunder og prøver igen...")
                time.sleep(2)
            else:
                current_app.logger.error("Alle genforsøg fejlede med InternalServerError. Kaster fejlen videre.")
                raise e

        except Exception as e:
            current_app.logger.error(
                f"En ikke-genoprettelig fejl opstod under udarbejdelse af historieudkast: {e}\n{traceback.format_exc()}")
            raise e

    raise InternalServerError("Kunne ikke generere historie efter flere forsøg på grund af interne fejl hos Google.")


def generate_reflection_questions_step4(
        final_story_title: str,
        final_story_content: str,
        narrative_brief: str,
        original_user_inputs: dict
):
    """
    Genererer refleksionsspørgsmål baseret på den endelige historie og det narrative brief (Trin 4).
    """
    current_app.logger.info("AI Service: Påbegynder Trin 4 - Generering af refleksionsspørgsmål...")
    reflection_questions = []

    try:
        prompt_string = build_narrative_question_prompt(
            final_story_title=final_story_title,
            final_story_content=final_story_content,
            narrative_brief=narrative_brief,
            original_user_inputs=original_user_inputs
        )
        current_app.logger.debug(
            f"AI Service (Trin 4): Spørgsmålsprompt bygget (længde: {len(prompt_string)}). Første 200 tegn:\n{prompt_string[:200]}"
        )

        ai_model_name = 'gemini-1.5-pro-latest'
        model = genai.GenerativeModel(ai_model_name)
        current_app.logger.info(f"AI Service (Trin 4): Anvender AI-model '{ai_model_name}' for spørgsmålsgenerering.")

        generation_config_settings = {
            "max_output_tokens": 2048,
            "temperature": 0.7,
        }
        gen_config = genai.types.GenerationConfig(**generation_config_settings)

        current_app.logger.info(
            f"AI Service (Trin 4): Kalder Gemini for refleksionsspørgsmål (Max Tokens: {gen_config.max_output_tokens}, Temp: {gen_config.temperature})."
        )

        response = model.generate_content(
            prompt_string,
            generation_config=gen_config,
            safety_settings=_SAFETY_BLOCK_NONE
        )

        raw_questions_text = ""
        try:
            raw_questions_text = response.text.strip()
            if not raw_questions_text:
                current_app.logger.warning("AI Service (Trin 4): AI returnerede tom tekst for spørgsmål.")
                return []

            current_app.logger.info("AI Service (Trin 4): Råtekst for spørgsmål modtaget.")
            current_app.logger.debug(f"AI Service (Trin 4): Rå output for spørgsmål:\n{raw_questions_text}")

            potential_questions = raw_questions_text.split('\n')
            for q_line in potential_questions:
                q_line_stripped = q_line.strip()
                if q_line_stripped.startswith(tuple(f"{i}." for i in range(1, 10))):
                    q_to_add = q_line_stripped[q_line_stripped.find('.') + 1:].strip()
                elif q_line_stripped.startswith('-'):
                    q_to_add = q_line_stripped[1:].strip()
                else:
                    q_to_add = q_line_stripped

                if q_to_add:
                    reflection_questions.append(q_to_add)

            if not reflection_questions:
                current_app.logger.warning("AI Service (Trin 4): Kunne ikke parse nogen spørgsmål fra AI'ens output, selvom tekst var til stede.")
            else:
                current_app.logger.info(f"AI Service (Trin 4): Parsede {len(reflection_questions)} refleksionsspørgsmål.")

        except ValueError as e_safety:
            current_app.logger.error(
                f"AI Service (Trin 4): Svar til spørgsmål blokeret af sikkerhedsfilter: {e_safety}"
            )
            current_app.logger.error(
                f"AI Service (Trin 4): Prompt Feedback: {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'Ingen prompt feedback.'}"
            )
            return []
        except Exception as e_parse:
            current_app.logger.error(
                f"AI Service (Trin 4): Fejl ved parsing af AI-svar for spørgsmål: {e_parse}\n{traceback.format_exc()}"
            )
            return []

    except Exception as e_general:
        current_app.logger.error(
            f"AI Service (Trin 4): Generel fejl under generering af refleksionsspørgsmål: {e_general}\n{traceback.format_exc()}"
        )
        return []

    return reflection_questions


def edit_narrative_story(
        story_draft_title: str,
        story_draft_content: str,
        original_user_inputs: dict
):
    """
    Finpudser et eksisterende narrativt historieudkast ved hjælp af Redaktør-AI (Trin 3).
    """
    current_app.logger.info("AI Service: Påbegynder Trin 3 - Redigering af narrativ historie...")
    edited_title = story_draft_title
    edited_content = "Fejl: Kunne ikke redigere historieudkast (Trin 3)."

    try:
        prompt_string = build_narrative_editing_prompt(
            story_draft_title=story_draft_title,
            story_draft_content=story_draft_content,
            original_user_inputs=original_user_inputs
        )
        current_app.logger.debug(
            f"AI Service: Narrativ editing prompt bygget (længde: {len(prompt_string)}). Første 300 tegn:\n{prompt_string[:300]}")

        ai_model_name = 'gemini-2.5-flash-preview-05-20'
        model = genai.GenerativeModel(ai_model_name)
        current_app.logger.info(f"AI Service: Anvender AI-model '{ai_model_name}' for Trin 3 (Redaktør).")

        generation_config_settings = {
            "max_output_tokens": 8192,
            "temperature": 0.65,
        }
        gen_config = genai.types.GenerationConfig(**generation_config_settings)

        current_app.logger.info(
            f"AI Service: Kalder Gemini for redigering af historie (Max Tokens: {gen_config.max_output_tokens}, Temp: {gen_config.temperature}).")

        response = model.generate_content(
            prompt_string,
            generation_config=gen_config,
            safety_settings=_SAFETY_BLOCK_NONE
        )

        raw_edited_text = ""
        try:
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                finish_reason_output = candidate.finish_reason.name if hasattr(candidate.finish_reason,
                                                                               'name') else candidate.finish_reason
                current_app.logger.info(f"AI Service (Redaktør Trin 3): Finish Reason: {finish_reason_output}")
                current_app.logger.info(f"AI Service (Redaktør Trin 3): Safety Ratings: {candidate.safety_ratings}")
            else:
                current_app.logger.warning(
                    "AI Service (Redaktør Trin 3): Ingen 'candidates' fundet i responsen.")
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                current_app.logger.info(f"AI Service (Redaktør Trin 3): Prompt Feedback: {response.prompt_feedback}")
            raw_edited_text = response.text.strip()
            if not raw_edited_text:
                current_app.logger.warning("AI Service: Redigeret historie (Trin 3) fra Gemini var tomt. Returnerer originalt udkast.")
                return story_draft_title, story_draft_content + "\n\n(Redigering mislykkedes, viser uredigeret udkast)"

            current_app.logger.info("AI Service: Redigeret historie (Trin 3) modtaget.")
            current_app.logger.debug(
                f"AI Service: Rå output fra Trin 3 AI (første 300 tegn):\n{raw_edited_text[:300]}")

            parts = raw_edited_text.split('\n', 1)
            if len(parts) >= 1 and parts[0].strip():
                edited_title = parts[0].strip()
                if len(parts) > 1 and parts[1].strip():
                    edited_content = parts[1].strip()
                else:
                    current_app.logger.warning(f"AI Service (Redaktør): Modtog kun titel, ingen historietekst. Titel: '{edited_title}'.")
                    edited_content = "Historien mangler efter titlen (Redigeringsfejl)."
            else:
                current_app.logger.warning(f"AI Service (Redaktør): Kunne ikke parse titel og historie fra redigeret output. Råtekst: {raw_edited_text[:200]}")
                edited_title = story_draft_title
                edited_content = raw_edited_text

            if not edited_content:
                current_app.logger.warning("AI Service (Redaktør): Selve historieteksten er tom efter parsing. Returnerer original.")
                return story_draft_title, story_draft_content + "\n\n(Redigering resulterede i tom historie, viser uredigeret udkast)"

        except ValueError as e_safety:
            current_app.logger.error(
                f"AI Service: Svar til redigeret historie (Trin 3) blokeret: {e_safety}")
            current_app.logger.error(
                f"AI Service: Prompt Feedback (Trin 3): {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'Ingen prompt feedback.'}")
            edited_content = f"Fejl: Indhold til den redigerede historie blev blokeret. Viser uredigeret udkast: \n\n{story_draft_content}"
        except Exception as e_parse:
            current_app.logger.error(
                f"AI Service: Fejl ved parsing af AI-svar (Trin 3): {e_parse}\n{traceback.format_exc()}")
            edited_content = f"Fejl: Kunne ikke parse AI-svar for redigeret historie (Trin 3). Viser uredigeret: \n\n{story_draft_content}"

    except Exception as e_general:
        current_app.logger.error(
            f"AI Service: Generel fejl under redigering af historie (Trin 3): {e_general}\n{traceback.format_exc()}")
        edited_content = f"Fejl: Teknisk fejl i AI-service (Trin 3). Viser uredigeret: \n\n{story_draft_content}"

    return edited_title, edited_content


def refine_story_for_lix(story_title: str, story_content: str, target_lix: int, generation_config_settings: dict, target_model_name: str):
    """
    Tager et eksisterende historieudkast og justerer det iterativt for at ramme et mål-LIX.
    """
    MAX_RETRIES = 2
    LIX_TOLERANCE = 4

    current_title = story_title
    current_content = story_content
    final_lix = calculate_lix(current_content)

    current_app.logger.info(
        f"LIX-justering starter. Mål: {target_lix}, Start LIX: {final_lix}, Tolerance: +/-{LIX_TOLERANCE}")

    for attempt in range(MAX_RETRIES):
        if abs(final_lix - target_lix) <= LIX_TOLERANCE:
            current_app.logger.info(f"LIX-mål opnået på forsøg {attempt}. Endelig LIX: {final_lix}")
            return current_title, current_content, final_lix

        if final_lix > target_lix:
            instruction = f"Gør sproget markant simplere. Brug kortere sætninger og færre lange ord (ord med mere end 6 bogstaver) for at sænke læsbarhedsniveauet."
        else:
            instruction = f"Gør sproget mere avanceret. Brug lidt længere og mere komplekse sætninger og et mere varieret ordforråd med flere lange ord (ord med mere end 6 bogstaver) for at hæve læsbarhedsniveauet."

        revision_prompt = (
            f"SYSTEM INSTRUKTION: Du er en dygtig redaktør, der skal omskrive en børnehistorie for at ramme et bestemt læsbarhedsniveau (LIX).\n"
            f"OPGAVE: Omskriv den følgende historie. Bevar plottet, karaktererne og den generelle stemning, men juster sproget for at ændre LIX-tallet.\n"
            f"MÅL-LIX: ca. {target_lix}\n"
            f"NUVÆRENDE LIX: {final_lix}\n"
            f"INSTRUKTION: {instruction}\n"
            f"VIGTIGT FORMAT: Start dit svar med historiens titel på den allerførste linje, efterfulgt af et enkelt linjeskift, og derefter den fulde, omskrevne historie.\n\n"
            f"--- ORIGINAL HISTORIE (TITEL: {current_title}) ---\n{current_content}\n\n"
            f"--- DIN REVIDEREDE HISTORIE ---\n"
        )

        current_app.logger.info(
            f"LIX-justeringsforsøg #{attempt + 1}: LIX er {final_lix}, bygger ny prompt for at ramme {target_lix}.")
        current_app.logger.debug(f"Justeringsprompt (delvis): {revision_prompt[:300]}")

        try:
            results = generate_story_text_from_gemini(
                full_prompt_string=revision_prompt,
                generation_config_settings=generation_config_settings,
                safety_settings_values=_SAFETY_BLOCK_NONE,
                target_model_name=target_model_name
            )

            if not results:
                current_app.logger.error(
                    f"LIX-justering: Tomt resultat under justeringsforsøg #{attempt + 1}. Afbryder.")
                return current_title, current_content, final_lix

            revised_title, revised_content = results[0]

            if "Fejl" in revised_title or "blokeret" in revised_content:
                current_app.logger.error(
                    f"LIX-justering: Fejl eller blokeret indhold modtaget under justeringsforsøg #{attempt + 1}. Afbryder.")
                return current_title, current_content, final_lix

            current_title = revised_title
            current_content = revised_content
            final_lix = calculate_lix(current_content)

        except Exception as e:
            current_app.logger.error(f"LIX-justering: Fejl under AI-kald i forsøg #{attempt + 1}: {e}")
            return current_title, current_content, final_lix

    current_app.logger.warning(
        f"LIX-justering: Max antal forsøg ({MAX_RETRIES}) nået. Returnerer bedste forsøg med LIX: {final_lix}")
    return current_title, current_content, final_lix


def analyze_story_for_logbook(story_content: str) -> dict:
    """
    Analyserer en historie og returnerer en struktureret ordbog med narrative indsigter.
    """
    current_app.logger.info("AI Service: Starter analyse af historie for logbog...")
    try:
        prompt = build_logbook_analysis_prompt(story_content)

        model = genai.GenerativeModel('gemini-1.5-pro-latest')

        generation_config = genai.types.GenerationConfig(
            temperature=0.4,
            response_mime_type="application/json"
        )

        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )

        analysis_result = json.loads(response.text)
        current_app.logger.info("AI Service: Succesfuld analyse af historie. JSON parset.")
        return analysis_result

    except json.JSONDecodeError as e:
        current_app.logger.error(f"AI Service: JSONDecodeError ved analyse af historie: {e}")
        current_app.logger.error(f"AI'ens rå output: {response.text}")
        return {"error": "AI'en returnerede et ugyldigt format."}
    except Exception as e:
        current_app.logger.error(f"AI Service: Generel fejl ved analyse af historie: {e}\n{traceback.format_exc()}")
        return {"error": f"En teknisk fejl opstod under analysen: {e}"}


def generate_problem_image(narrative_data: dict):
    """
    Orkestrerer genereringen af et billede, der visualiserer et problem.
    """
    current_app.logger.info("ai_service: Starter generering af 'problem-billede'.")
    try:
        final_imagen_prompt = build_problem_image_prompt(narrative_data)
        image_data_url = generate_image_with_vertexai(final_imagen_prompt)

        if image_data_url:
            return {"image_url": image_data_url, "image_prompt_used": final_imagen_prompt}
        else:
            return {"error": "Kunne ikke generere problem-billede med Vertex AI."}

    except Exception as e:
        current_app.logger.error(f"Fejl i generate_problem_image: {e}\n{traceback.format_exc()}")
        return {"error": f"Intern fejl under generering af problem-billede: {e}"}


def generate_quiz_for_story(story_content: str, lix_score: int) -> dict:
    """
    Genererer en JSON-baseret quiz for en given historie og LIX-score.
    """
    current_app.logger.info(f"AI Service: Starter quiz-generering for historie med LIX: {lix_score}")
    try:
        prompt = build_quiz_generation_prompt(story_content, lix_score)

        model = genai.GenerativeModel('gemini-1.5-pro-latest')

        generation_config = genai.types.GenerationConfig(
            temperature=0.5,
            response_mime_type="application/json"
        )

        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=_SAFETY_BLOCK_NONE
        )

        quiz_data = json.loads(response.text)
        current_app.logger.info("AI Service: Succesfuld generering af quiz-data.")
        return {"questions": quiz_data}

    except json.JSONDecodeError as e:
        current_app.logger.error(f"AI Service (Quiz): JSONDecodeError: {e}. Rå output: {response.text}")
        return {"error": "AI'en returnerede et ugyldigt format for quizzen."}
    except Exception as e:
        current_app.logger.error(f"AI Service (Quiz): Generel fejl: {e}\n{traceback.format_exc()}")
        return {"error": f"En teknisk fejl opstod under quiz-generering: {e}"}
