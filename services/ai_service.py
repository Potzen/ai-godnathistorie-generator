# Fil: services/ai_service.py
from flask import current_app # For at tilgå logger og config
from flask_login import current_user
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from vertexai.preview.vision_models import ImageGenerationModel
import base64
import time
import traceback
import vertexai
from prompts.image_prompt_generation_prompt import build_image_prompt_generation_prompt
from prompts.narrative_generator_prompt import build_narrative_generator_prompt
from prompts.character_trait_suggestion_prompt import build_character_trait_suggestion_prompt
import json # Til at parse JSON-svar fra AI
from prompts.narrative_briefing_prompt import build_narrative_briefing_prompt
from prompts.narrative_drafting_prompt import build_narrative_drafting_prompt
from prompts.narrative_editing_prompt import build_narrative_editing_prompt
from services.rag_service import find_relevant_chunks_v2


def generate_story_text_from_gemini(full_prompt_string, generation_config_settings, safety_settings_values, target_model_name='gemini-1.5-flash-latest'):
    """
    Genererer en historie (titel og indhold) ved hjælp af Google Gemini.

    Args:
        full_prompt_string (str): Den komplette prompt, der skal sendes til Gemini.
        generation_config_settings (dict): Indstillinger for generation_config (f.eks. max_output_tokens, temperature).
        safety_settings_values (dict): Indstillinger for safety_settings.

    Returns:
        tuple: (story_title, actual_story_content)
               Returnerer ("Fejl Titel", "Fejl Besked") ved fejl.
    """
    current_app.logger.info(
        f"--- ai_service: Kalder Gemini for historie (Max Tokens: {generation_config_settings.get('max_output_tokens')}) ---")
    # Overvej at logge dele af prompten, men vær forsigtig med længden og evt. følsomme data.
    # current_app.logger.debug(f"Prompt til Gemini (delvis): {full_prompt_string[:200]}")

    story_title = "Uden Titel (AI Service Fejl)"
    actual_story_content = "Der opstod en fejl under historiegenerering i AI-tjenesten."

    try:
        # Brug det tilsendte modelnavn, med en fallback hvis det er None eller tomt
        actual_model_to_use = target_model_name if target_model_name and target_model_name.strip() else 'gemini-1.5-flash-latest'
        current_app.logger.info(f"ai_service: Anvender model '{actual_model_to_use}' for historiegenerering.")
        model = genai.GenerativeModel(actual_model_to_use)

        # Omdan dicts til de korrekte typer for API'et, hvis nødvændigt

        # Omdan dicts til de korrekte typer for API'et, hvis nødvendigt
        # For genai.types.GenerationConfig og safety_settings, hvis de ikke allerede er det.
        # Her antager vi, at generation_config_settings er en dict, der kan pakkes ud.
        gen_config = genai.types.GenerationConfig(**generation_config_settings)

        # Safety_settings_values forventes at være en dict som {HarmCategory.XYZ: HarmBlockThreshold.ABC}
        # Hvis det kommer som en liste af dicts, skal det måske transformeres.
        # Baseret på din nuværende kode i story_routes, er det en dict.

        response = model.generate_content(
            full_prompt_string,
            generation_config=gen_config,
            safety_settings=safety_settings_values
        )
        current_app.logger.info("ai_service: Svar modtaget fra Google Gemini.")

        raw_text_from_gemini = ""
        try:
            raw_text_from_gemini = response.text
            parts = raw_text_from_gemini.split('\n', 1)
            if len(parts) >= 1 and parts[0].strip():
                story_title = parts[0].strip()
                if len(parts) > 1 and parts[1].strip():
                    actual_story_content = parts[1].strip()
                elif not parts[0].strip() and len(parts) > 1 and parts[1].strip():  # Ingen titel, kun historie
                    story_title = "Uden Titel (Genereret)"
                    actual_story_content = parts[1].strip()
                elif parts[0].strip() and (len(parts) == 1 or not parts[1].strip()):  # Kun titel, ingen historie
                    actual_story_content = "Historien mangler efter titlen."
                    current_app.logger.warning(
                        f"ai_service: Kunne kun parse titel, historien mangler. Råtekst: {raw_text_from_gemini[:200]}")
                else:  # Kunne ikke splitte fornuftigt
                    story_title = "Uden Titel (Parse Fejl)"
                    actual_story_content = raw_text_from_gemini  # Brug råtekst som fallback
                    current_app.logger.warning(
                        f"ai_service: Kunne ikke parse titel og historie optimalt. Råtekst: {raw_text_from_gemini[:200]}")
            else:  # Tom respons eller ingen linjeskift
                story_title = "Uden Titel (Intet Linjeskift)"
                actual_story_content = raw_text_from_gemini.strip() if raw_text_from_gemini.strip() else "Modtog tomt svar fra AI."
                current_app.logger.warning(
                    f"ai_service: Ingen linjeskift fundet til at adskille titel. Råtekst: {raw_text_from_gemini[:200]}")

        except ValueError as e_safety:  # Safety filter
            current_app.logger.error(
                f"ai_service: Svar blokeret af sikkerhedsfilter eller problem med response.text: {e_safety}")
            current_app.logger.error(
                f"ai_service: Prompt Feedback: {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'Ingen prompt feedback.'}")
            if hasattr(response, 'candidates') and response.candidates:
                current_app.logger.error(f"ai_service: Blocked Candidates: {response.candidates}")
            story_title = "Blokeret Indhold"
            actual_story_content = "Beklager, historien kunne ikke laves, da den blev blokeret. Prøv at justere dine input."
        except Exception as e_parse:
            current_app.logger.error(
                f"ai_service: Fejl under adgang til response.text eller parsing: {e_parse}\n{traceback.format_exc()}")
            story_title = "Parse Fejl (AI Service)"
            actual_story_content = "Der opstod en fejl under behandling af svaret fra AI i AI-tjenesten."
            # Fallback til response.candidates hvis response.text fejler fundamentalt
            if response and response.candidates:
                try:
                    candidate_text = response.candidates[0].content.parts[0].text
                    parts = candidate_text.split('\n', 1)
                    if len(parts) >= 1 and parts[0].strip():
                        story_title = parts[0].strip()
                        actual_story_content = parts[1].strip() if len(parts) > 1 and parts[
                            1].strip() else "Historien mangler efter titlen (fallback)."
                    current_app.logger.info(
                        "ai_service: Fallback til parsing fra response.candidates succesfuld (delvist).")
                except Exception as e_candidate:
                    current_app.logger.error(
                        f"ai_service: Kunne heller ikke hente indhold fra response.candidates: {e_candidate}")

    except Exception as e_api:
        current_app.logger.error(f"ai_service: Fejl ved kald til Google Gemini API: {e_api}\n{traceback.format_exc()}")
        story_title = "API Fejl (AI Service)"
        actual_story_content = f"Beklager, teknisk fejl med AI-tjenesten (Gemini). Prøv igen senere."

    if not isinstance(story_title, str): story_title = "Uden Titel (Intern Fejl i AI Service)"
    if not isinstance(actual_story_content, str): actual_story_content = "Indhold mangler (Intern Fejl i AI Service)"

    return story_title, actual_story_content


def generate_image_prompt_from_gemini(story_text):
    """
    Genererer en billedprompt baseret på en historietekst ved hjælp af Google Gemini.
    # ... (docstring fortsætter)
    """
    current_app.logger.info("ai_service: Genererer billedprompt med Gemini...")

    default_image_prompt = "A whimsical and enchanting fairytale illustration, child-friendly, high-quality 3D digital art, imaginative."
    generated_prompt_text = default_image_prompt

    if not story_text or not story_text.strip():
        current_app.logger.warning(
            "ai_service: Tom historietekst modtaget til billedprompt generering. Bruger standard prompt.")
        return default_image_prompt

    try:
        gemini_model_for_prompting = genai.GenerativeModel('gemini-1.5-flash-latest')

        # Byg prompten til billedprompt-generering ved hjælp af den nye funktion
        actual_prompt_to_gemini = build_image_prompt_generation_prompt(story_text)

        response_gemini = gemini_model_for_prompting.generate_content(
            actual_prompt_to_gemini)  # Nu bruges den prompt, der er bygget af funktionen

        if response_gemini.text and response_gemini.text.strip():
            generated_prompt_text = response_gemini.text.strip()
            current_app.logger.info(f"ai_service: Genereret billedprompt: {generated_prompt_text}")
        else:
            current_app.logger.warning("ai_service: Gemini returnerede en tom billedprompt. Bruger standard prompt.")
            # if response_gemini.prompt_feedback: current_app.logger.warning(f"Prompt feedback: {response_gemini.prompt_feedback}")

    except Exception as e_gemini_prompt:
        current_app.logger.error(
            f"ai_service: Fejl under generering af billedprompt med Gemini: {e_gemini_prompt}\n{traceback.format_exc()}")

    return generated_prompt_text


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
    max_retries = 2

    for attempt in range(max_retries):
        try:
            current_app.logger.info(
                f"ai_service: Imagen forsøg {attempt + 1}/{max_retries}. Prompt: {current_prompt_to_imagen[:100]}...")
            if attempt == 1:
                current_app.logger.info("ai_service: Modificerer prompt til andet Imagen-forsøg...")
                current_prompt_to_imagen += ", impressionistic oil painting"

            model_identifier = "imagen-3.0-generate-002"
            model = ImageGenerationModel.from_pretrained(model_identifier)

            response_imagen = model.generate_images(
                prompt=current_prompt_to_imagen,
                number_of_images=1,
                guidance_scale=30
            )

            if response_imagen and response_imagen.images:
                image_obj = response_imagen.images[0]
                if hasattr(image_obj, '_image_bytes') and image_obj._image_bytes:
                    image_bytes = image_obj._image_bytes
                    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                    image_data_url = f"data:image/png;base64,{image_base64}"
                    current_app.logger.info("ai_service: Billede genereret succesfuldt med Vertex AI.")
                    break  # Afslut loopet, da vi har et billede
                else: # Denne 'else' hører til 'if hasattr(image_obj, '_image_bytes')'
                    current_app.logger.error(
                        f"ai_service: FEJL - _image_bytes mangler på billedeobjekt (forsøg {attempt + 1}).")
                    if attempt == max_retries - 1:
                        raise ValueError("EMPTY_IMAGE_BYTES_ERROR_AFTER_RETRIES")
            else:  # Håndterer hvis response_imagen er None, eller response_imagen.images er tom/None
                error_details = str(response_imagen)
                if response_imagen and hasattr(response_imagen, 'error') and response_imagen.error:
                    error_details += f" | Error Details: {response_imagen.error}"
                if response_imagen and hasattr(response_imagen, 'details') and response_imagen.details:
                    error_details += f" | Response Details Attr: {response_imagen.details}"
                if response_imagen and hasattr(response_imagen, 'metadata') and response_imagen.metadata:
                    error_details += f" | Response Metadata: {response_imagen.metadata}"

                current_app.logger.error(
                    f"ai_service: FEJL - Vertex AI Imagen returnerede ingen billeder (forsøg {attempt + 1}). Respons: {error_details}")
                if attempt == max_retries - 1:
                    raise ValueError("EMPTY_IMAGE_LIST_ERROR_AFTER_RETRIES")

            # Vent lidt før næste forsøg, hvis dette ikke er sidste forsøg, OG vi ikke har et billede endnu
            if attempt < max_retries - 1 and not image_data_url: # image_data_url vil være None her, hvis 'break' ikke blev ramt
                time.sleep(1.5)

        except Exception as e_attempt:
            current_app.logger.error(
                f"ai_service: Fejl i Vertex AI billedgenereringsforsøg {attempt + 1}: {e_attempt}\n{traceback.format_exc()}")
            non_retryable_errors = ["quota exceeded", "permission denied", "billing", "does not exist",
                                    "kunne ikke initialisere"]
            if any(sub.lower() in str(e_attempt).lower() for sub in non_retryable_errors) or attempt == max_retries - 1:
                current_app.logger.error(
                    f"ai_service: Ikke-genoprettelig fejl eller sidste forsøg fejlet. Stopper billedgenerering.")
                return None # Returner None for at signalere fejl

            # Vent også her før et retry, hvis fejlen ikke var "non-retryable" og det ikke er sidste forsøg
            if attempt < max_retries - 1:
                time.sleep(1.5)

    # Denne loglinje skal være UDENFOR for-loopet
    if not image_data_url:
        current_app.logger.error("ai_service: Kunne ikke generere billede efter alle forsøg.")

    return image_data_url


def generate_narrative_story_step1_generator_ai(
        narrative_focus,
        child_info,
        story_elements,
        desired_outcome=None
):
    """
    Genererer det første rå udkast til en narrativ historie (Trin 1 - Generator-AI).

    Args:
        narrative_focus (str): Det centrale tema/udfordring.
        child_info (dict): Information om barnet.
        story_elements (dict): Standard historieelementer (karakterer, steder, længde, stemning etc.).
        desired_outcome (str, optional): Forælderens ønskede udgang.

    Returns:
        tuple: (story_title, actual_story_content)
               Returnerer ("Fejl Titel (Narrativ Trin 1)", "Fejl Besked") ved fejl.
    """
    user_id_for_log = current_app.login_manager._login_disabled if hasattr(current_app,
                                                                           'login_manager') and current_app.login_manager._login_disabled else (
        current_user.id if hasattr(current_user, 'id') else 'Ukendt (narrativ)')
    current_app.logger.info(
        f"ai_service (Bruger: {user_id_for_log}): Starter Trin 1 - Generator-AI for narrativ historie.")
    current_app.logger.info(f"Narrativt fokus: {narrative_focus}")

    try:
        # 1. Byg den specifikke prompt for narrativ Generator-AI
        prompt_for_narrative_generator = build_narrative_generator_prompt(
            narrative_focus=narrative_focus,
            child_info=child_info,
            story_elements=story_elements,
            desired_outcome=desired_outcome
        )
        # For debugging, log evt. dele af prompten (vær forsigtig med længde/følsomme data)
        current_app.logger.debug(
            f"ai_service: Prompt til Narrativ Generator-AI (delvis): {prompt_for_narrative_generator[:300]}...")

        # 2. Definer generation og safety settings (kan justeres specifikt for narrativt modul hvis nødvendigt)
        # Vi genbruger standardindstillingerne fra den almindelige historiegenerator for nu.
        # Længde styres primært via prompten, men max_output_tokens kan stadig være en global grænse.
        story_length = story_elements.get('length', 'mellem')
        max_tokens_setting = 1500  # Default for 'kort'
        if story_length == 'mellem':
            max_tokens_setting = 3000
        elif story_length == 'lang':
            max_tokens_setting = 7000

        # Log den faktiske max_tokens_setting der vil blive brugt
        current_app.logger.info(
            f"ai_service: Max tokens for Narrativ Generator-AI sat til: {max_tokens_setting} baseret på længde: '{story_length}'")

        generation_config_settings = {
            "max_output_tokens": max_tokens_setting,  # Juster efter behov for narrative historier
            "temperature": 0.75,  # Måske lidt højere for mere kreativitet i første udkast
            # "top_p": 0.9, # Overvej at eksperimentere med top_p og top_k
            # "top_k": 40
        }
        safety_settings_values = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

        # 3. Kald den generiske Gemini tekstgenereringsfunktion
        story_title, actual_story_content = generate_story_text_from_gemini(
            prompt_for_narrative_generator,
            generation_config_settings,
            safety_settings_values
        )

        if "Fejl" in story_title or "blokeret" in actual_story_content.lower():  # Simpel tjek for fejl fra generate_story_text_from_gemini
            current_app.logger.warning(
                f"ai_service (Bruger: {user_id_for_log}): Mulig fejl eller blokeret indhold fra Narrativ Generator-AI. Titel: {story_title}")
        else:
            current_app.logger.info(
                f"ai_service (Bruger: {user_id_for_log}): Første udkast til narrativ historie genereret. Titel: {story_title[:50]}...")

        return story_title, actual_story_content

    except Exception as e:
        current_app.logger.error(
            f"ai_service (Bruger: {user_id_for_log}): Fejl i generate_narrative_story_step1_generator_ai: {e}\n{traceback.format_exc()}")
        return "Fejl Titel (Narrativ Trin 1)", f"Der opstod en intern fejl under generering af det første historieudkast: {str(e)}"

def get_ai_suggested_character_traits(narrative_focus):
    """
    Får AI-genererede forslag til karaktertræk baseret på et narrativt fokus.
    Bruger Gemini 1.5 Pro og forventer et JSON-svar fra AI'en.

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
        # 1. Byg prompten
        prompt_for_suggestions = build_character_trait_suggestion_prompt(narrative_focus)
        current_app.logger.debug(
            f"ai_service: Prompt til karaktertræk-forslag (delvis): {prompt_for_suggestions[:200]}...")

        # 2. Konfigurer og kald Gemini 2.5 Pro
        model_name = 'gemini-2.5-pro-preview-05-06'

        current_app.logger.info(f"ai_service: Bruger model '{model_name}' til karaktertræk-forslag.")
        model = genai.GenerativeModel(model_name)

        generation_config_settings = {
            "max_output_tokens": 8192,  # JSON-output kan være lidt langt
            "temperature": 0.5,  # Lavere temperatur for mere fokuseret/forudsigeligt JSON output
            "response_mime_type": "application/json",  # Bed AI'en om at formatere output som JSON
        }
        safety_settings_values = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

        response = model.generate_content(
            prompt_for_suggestions,
            generation_config=genai.types.GenerationConfig(**generation_config_settings),
            safety_settings=safety_settings_values
        )

        current_app.logger.info(
            f"ai_service (Bruger: {user_id_for_log}): Svar modtaget fra Gemini for karaktertræk.")

        # 3. Parse AI'ens svar (forventer JSON)
        try:
            # response.text bør indeholde den JSON-formaterede streng
            if response.text:
                current_app.logger.debug(f"ai_service: Råtekst fra Gemini (karaktertræk): {response.text[:300]}...")
                # Fjern eventuelle markdown ```json ... ``` hvis AI'en tilføjer det
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
        except ValueError as e_safety:  # Kan opstå hvis indhold blokeres før .text tilgås
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



def generate_narrative_brief(
        original_user_inputs: dict  # Modtager nu hele dictionary med brugerinput
):
    """
    Genererer et struktureret narrativt brief ved hjælp af en AI-model (Trin 1).
    AI'en instrueres af en prompt (bygget af build_narrative_briefing_prompt)
    til at opsummere de originale brugerinput i et specifikt format.

    Args:
        original_user_inputs (dict): En dictionary indeholdende alle brugerens inputfelter.

    Returns:
        str: Det genererede narrative brief som en tekststreng,
             eller en fejlbesked streng ved fejl.
    """
    current_app.logger.info("AI Service: Påbegynder generering af narrativt brief (Trin 1)...")

    try:
        # Byg prompten ved hjælp af den importerede funktion,
        # som nu selv håndterer udpakning af værdier fra original_user_inputs.
        prompt_string = build_narrative_briefing_prompt(original_user_inputs)

        current_app.logger.debug(
            f"AI Service: Narrativ briefing prompt bygget (længde: {len(prompt_string)}). Første 200 tegn:\n{prompt_string[:200]}")

        # Konfigurer AI-modellen
        model = genai.GenerativeModel('gemini-2.5-pro-preview-05-06')  # Opdateret model for Trin 1

        # Justerede safety settings for brief-generering for at minimere blokering
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        generation_config_settings = {
            "max_output_tokens": 4096,  # Forøget for 2.5 Pro modellen
            "temperature": 0.5  # Lavere temp for mere præcis opsummering af input
        }
        gen_config = genai.types.GenerationConfig(**generation_config_settings)

        current_app.logger.info(
            f"AI Service: Kalder Gemini for narrativt brief (Max Tokens: {generation_config_settings.get('max_output_tokens')}, Temp: {generation_config_settings.get('temperature')}).")

        response = model.generate_content(
            prompt_string,
            generation_config=gen_config,
            safety_settings=safety_settings
        )

        narrative_brief_text = ""
        try:
            # Forbedret tjek af respons og finish_reason
            if response.candidates and response.candidates[0].content.parts:
                if response.candidates[0].finish_reason == 1:  # FINISH_REASON_STOP
                    narrative_brief_text = response.text.strip()
                    if not narrative_brief_text:
                        current_app.logger.warning(
                            "AI Service: Narrativt brief fra Gemini var tomt, selvom finish_reason var STOP.")
                        return "Fejl: AI returnerede et tomt narrativt brief."
                    current_app.logger.info("AI Service: Narrativt brief genereret succesfuldt.")
                    current_app.logger.debug(
                        f"AI Service: Genereret narrativt brief (første 200 tegn):\n{narrative_brief_text[:200]}")
                else:  # Håndter andre finish_reasons
                    finish_reason_val = response.candidates[0].finish_reason
                    current_app.logger.error(
                        f"AI Service: Uventet finish_reason ({finish_reason_val}) for narrativt brief. Safety Ratings: {response.candidates[0].safety_ratings}")
                    if finish_reason_val == 2:  # SAFETY
                        return "Fejl: Indhold til narrativt brief blev blokeret af sikkerhedsfilter (selvom sat til NONE). Undersøg prompt/input nærmere."
                    elif finish_reason_val == 3:  # MAX_TOKENS
                        return "Fejl: AI ramte token-grænsen under generering af narrativt brief. Input er muligvis for langt."
                    else:
                        return f"Fejl: AI kunne ikke generere et komplet narrativt brief (finish_reason: {finish_reason_val})."
            else:  # Ingen valid 'parts' i content
                current_app.logger.error(
                    "AI Service: Ingen valid 'parts' fundet i content fra Gemini for narrativt brief.")
                current_app.logger.error(
                    f"AI Service: Prompt Feedback (brief): {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'Ingen prompt feedback.'}")
                if response.candidates:
                    current_app.logger.error(f"AI Service: Candidate (brief): {response.candidates[0]}")
                return "Fejl: AI returnerede intet indhold for narrativt brief (ingen 'parts')."

        except ValueError as e_text_access:  # Fanger specifikt hvis .text fejler pga. ingen valid part
            current_app.logger.error(
                f"AI Service: Fejl ved adgang til response.text (muligvis blokeret indhold, selv med BLOCK_NONE): {e_text_access}")
            current_app.logger.error(
                f"AI Service: Prompt Feedback (brief): {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'Ingen prompt feedback.'}")
            if hasattr(response, 'candidates') and response.candidates:
                current_app.logger.error(f"AI Service: Blocked Candidates (brief): {response.candidates}")
            return "Fejl: Kunne ikke tilgå tekst-svar fra AI for narrativt brief (muligvis blokeret)."
        except Exception as e_parse:  # Generel parsing eller anden fejl
            current_app.logger.error(
                f"AI Service: Generel fejl ved behandling af AI-svar for narrativt brief: {e_parse}\n{traceback.format_exc()}")
            return "Fejl: Generel fejl under behandling af AI-svar for narrativt brief."

        return narrative_brief_text

    except Exception as e_api:
        current_app.logger.error(
            f"AI Service: Generel fejl under generering af narrativt brief: {e_api}\n{traceback.format_exc()}")
        return f"Fejl: Teknisk fejl i AI-tjenesten under generering af narrativt brief."


def draft_narrative_story_with_rag(
        structured_brief,  # Output fra Trin 1
        original_user_inputs,  # Dictionary med alle originale brugerinput
        narrative_focus_for_rag  # Specifikt felt fra brugerinput til RAG-søgning, f.eks. 'narrative_focus' strengen
):
    """
    Genererer et første udkast til en narrativ historie og refleksionsspørgsmål
    ved hjælp af en AI-model, det strukturerede brief fra Trin 1, og RAG-kontekst.
    Dette er Trin 2 i den reviderede narrative AI-proces.

    Args:
        structured_brief (str): Det brief, der blev genereret af Trin 1 AI.
        original_user_inputs (dict): En dictionary med de oprindelige brugerinput.
                                     Kan bruges til at give AI'en adgang til råtekst
                                     eller detaljer, der måtte være opsummeret i briefet.
        narrative_focus_for_rag (str): Den tekststreng (typisk brugerens narrative fokus),
                                       der skal bruges til at søge i RAG-videnbasen.

    Returns:
        tuple: (story_title, story_content, reflection_questions)
               Hvor reflection_questions er en liste af strenge.
               Returnerer (None, "Fejlbesked...", []) ved fejl.
    """
    current_app.logger.info("AI Service: Påbegynder udarbejdelse af narrativ historie med RAG (Trin 2)...")
    story_title = None
    story_content = "Fejl: Kunne ikke generere historieudkast (Trin 2)."
    reflection_questions = []

    # 1. Hent RAG-kontekst
    rag_chunks = []
    if narrative_focus_for_rag and narrative_focus_for_rag.strip():
        try:
            current_app.logger.info(
                f"AI Service: Henter RAG-kontekst baseret på: '{narrative_focus_for_rag[:100]}...'")
            rag_chunks = find_relevant_chunks_v2(narrative_focus_for_rag,
                                              top_k=2)  # Hent f.eks. top 2 relevante chunks
            if rag_chunks:
                current_app.logger.info(f"AI Service: {len(rag_chunks)} RAG-chunks fundet.")
                for i, chunk_text in enumerate(rag_chunks):
                    current_app.logger.debug(f"AI Service: RAG Chunk #{i + 1}: {chunk_text[:100]}...")
            else:
                current_app.logger.info("AI Service: Ingen relevante RAG-chunks fundet.")
        except Exception as e_rag:
            current_app.logger.error(
                f"AI Service: Fejl under hentning af RAG-kontekst: {e_rag}\n{traceback.format_exc()}")
            # Fortsæt uden RAG-kontekst, men log fejlen. AI'en får besked i prompten.
            rag_chunks = []  # Sikrer at det er en tom liste
    else:
        current_app.logger.warning("AI Service: narrative_focus_for_rag var tom. Skipper RAG-søgning.")

    try:
        # 2. Byg prompten til Trin 2 AI'en
        prompt_string = build_narrative_drafting_prompt(
            structured_brief=structured_brief,
            rag_context=rag_chunks,
            original_user_inputs=original_user_inputs
        )
        current_app.logger.debug(
            f"AI Service: Narrativ drafting prompt bygget (længde: {len(prompt_string)}). Første 300 tegn:\n{prompt_string[:300]}")

        # 3. Konfigurer og kald AI-modellen
        # Anbefalet model er Gemini 2.5 Pro ifølge modulbeskrivelsen.
        # For nuværende test kan vi starte med 'gemini-1.5-pro-latest' eller 'gemini-1.5-flash-latest'
        # 'gemini-1.5-pro-latest' er kraftigere og bedre til kreativ skrivning end flash.
        # Husk at 'gemini-2.5-pro-preview-05-06' var den specifikke model nævnt.
        # Hvis den ikke er tilgængelig via din API-nøgle, brug en tilgængelig Pro-model.
        # Lad os prøve med 'gemini-1.5-pro-latest' som et godt kompromis for nu.
        ai_model_name = 'gemini-2.5-pro-preview-05-06'
        model = genai.GenerativeModel(ai_model_name)
        current_app.logger.info(f"AI Service: Anvender AI-model '{ai_model_name}' for Trin 2.")

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

        story_length_preference = original_user_inputs.get('length', 'mellem')
        max_tokens_for_draft = 8192  # Default til den højeste værdi (for 'lang' og fallback)

        if story_length_preference == 'kort':
            max_tokens_for_draft = 2048  # Lavere grænse for "kort" (plads til ca. 6-8 afsnit + spørgsmål)
        elif story_length_preference == 'mellem':
            max_tokens_for_draft = 4096  # Mellem grænse for "mellem" (plads til ca. 10-14 afsnit + spørgsmål)
        # Hvis 'lang', forbliver den 8192

        current_app.logger.info(
            f"AI Service (Trin 2 Udkast): Ønsket længde '{story_length_preference}'. Sætter max_tokens_for_draft til {max_tokens_for_draft}.")
        # --- SLUT PÅ NY DYNAMISK MAX_OUTPUT_TOKENS LOGIK ---

        generation_config_settings = {
            "max_output_tokens": max_tokens_for_draft,  # BRUGER NU DEN DYNAMISKE VÆRDI
            "temperature": 0.6,
            "top_p": 0.95,
        }
        gen_config = genai.types.GenerationConfig(**generation_config_settings)

        current_app.logger.info(
            f"AI Service: Kalder Gemini for narrativt historieudkast (Max Tokens: {gen_config.max_output_tokens}, Temp: {gen_config.temperature}).")

        response = model.generate_content(
            prompt_string,
            generation_config=gen_config,
            safety_settings=safety_settings
        )

        # 4. Parse svaret fra AI'en
        raw_response_text = ""
        try:
            raw_response_text = response.text.strip()
            if not raw_response_text:
                current_app.logger.warning("AI Service: Historieudkast (Trin 2) fra Gemini var tomt.")
                story_content = "Fejl: AI returnerede et tomt historieudkast."
                return story_title, story_content, reflection_questions

            current_app.logger.info("AI Service: Historieudkast (Trin 2) genereret succesfuldt.")
            current_app.logger.debug(
                f"AI Service: KOMPLET Rå output fra Trin 2 AI:\n---- START ----\n{raw_response_text}\n---- SLUT ----")


            # Parsing af titel, historie og refleksionsspørgsmål
            parts = raw_response_text.split("--- REFLEKSIONSSPØRGSMÅL ---", 1)
            story_with_title = parts[0].strip()

            title_story_parts = story_with_title.split('\n', 1)
            if title_story_parts:
                story_title = title_story_parts[0].strip()
                story_content = title_story_parts[1].strip() if len(title_story_parts) > 1 else ""
            else:  # Skulle ikke ske hvis AI følger format
                story_title = "Uden Titel (Parse Fejl)"
                story_content = story_with_title  # Hele outputtet som historie

            if len(parts) > 1 and parts[1].strip():
                questions_raw = parts[1].strip()
                # Split spørgsmål baseret på nummerering (f.eks. "1. ...", "2. ...")
                # Dette er en simpel parser; kan gøres mere robust.
                qs = questions_raw.split('\n')
                for q_line in qs:
                    q_line_stripped = q_line.strip()
                    # Fjern "1. ", "2. " osv.
                    if q_line_stripped and (q_line_stripped.startswith(tuple(f"{i}." for i in range(1, 10)))):
                        reflection_questions.append(q_line_stripped[q_line_stripped.find('.') + 1:].strip())
                    elif q_line_stripped:  # Hvis det ikke er nummereret, men der er tekst
                        reflection_questions.append(q_line_stripped)
                current_app.logger.info(f"AI Service: Parsede {len(reflection_questions)} refleksionsspørgsmål.")
            else:
                current_app.logger.warning("AI Service: Ingen refleksionsspørgsmål fundet efter separatoren.")

            if not story_content:
                current_app.logger.warning("AI Service: Selve historieteksten er tom efter parsing.")
                story_content = "Historien mangler indhold."


        except ValueError as e_safety:  # Håndter hvis AI'ens svar blokeres
            current_app.logger.error(
                f"AI Service: Svar til historieudkast (Trin 2) blokeret af sikkerhedsfilter: {e_safety}")
            current_app.logger.error(
                f"AI Service: Prompt Feedback (Trin 2): {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'Ingen prompt feedback.'}")
            story_content = "Fejl: Indhold til historien blev blokeret af AI'en. Prøv at justere dine input."
            # story_title forbliver None eller hvad den var før
        except Exception as e_parse:
            current_app.logger.error(
                f"AI Service: Fejl ved parsing af AI-svar (Trin 2): {e_parse}\n{traceback.format_exc()}")
            story_content = f"Fejl: Kunne ikke parse svaret fra AI for historieudkast (Trin 2). Rå output: {raw_response_text[:200]}..."
            # story_title forbliver None

    except Exception as e_general:
        current_app.logger.error(
            f"AI Service: Generel fejl under udarbejdelse af historieudkast (Trin 2): {e_general}\n{traceback.format_exc()}")
        story_content = f"Fejl: Teknisk fejl i AI-tjenesten under udarbejdelse af historieudkast (Trin 2)."
        # story_title forbliver None

    return story_title, story_content, reflection_questions

def edit_narrative_story(
        story_draft_title: str,
        story_draft_content: str,
        original_user_inputs: dict
):
    """
    Finpudser et eksisterende narrativt historieudkast ved hjælp af Redaktør-AI (Trin 3).

    Args:
        story_draft_title (str): Titlen på historieudkastet fra Trin 2.
        story_draft_content (str): Selve historieudkastet fra Trin 2.
        original_user_inputs (dict): De oprindelige brugerinput for kontekst.

    Returns:
        tuple: (edited_title, edited_content)
               Returnerer (None, "Fejlbesked...") eller (original_title, "Fejlbesked...") ved fejl.
    """
    current_app.logger.info("AI Service: Påbegynder Trin 3 - Redigering af narrativ historie...")
    edited_title = story_draft_title # Fallback til original titel
    edited_content = "Fejl: Kunne ikke redigere historieudkast (Trin 3)."

    try:
        # 1. Byg prompten til Redaktør-AI'en
        prompt_string = build_narrative_editing_prompt(
            story_draft_title=story_draft_title,
            story_draft_content=story_draft_content,
            original_user_inputs=original_user_inputs
        )
        current_app.logger.debug(
            f"AI Service: Narrativ editing prompt bygget (længde: {len(prompt_string)}). Første 300 tegn:\n{prompt_string[:300]}")

        # 2. Konfigurer og kald AI-modellen (Gemini 1.5 Flash er et godt valg her [cite: 149, 150])
        # Modulbeskrivelsen nævner Gemini 2.0 Flash, men vi bruger 'gemini-1.5-flash-latest' som er tilgængelig.
        ai_model_name = 'gemini-2.5-pro-preview-05-06'
        model = genai.GenerativeModel(ai_model_name)
        current_app.logger.info(f"AI Service: Anvender AI-model '{ai_model_name}' for Trin 3 (Redaktør).")

        # Safety settings (kan genbruges)
        safety_settings = {
                     HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                     HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                     HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                     HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                 }

        # Generation config for redigering:
        # Max output tokens bør være lidt mere end forventet output for at give plads.
        # Temperatur kan være lidt lavere for at holde sig tættere på originalen, men stadig tillade forbedringer.
        # Længden bestemmes af brugerens input 'length' i original_user_inputs [cite: 156]
        # story_length = original_user_inputs.get('length', 'mellem')
        # max_tokens_for_editing = 2048  # Default for 'kort' / 'mellem'
        # if story_length == 'lang':
        #    max_tokens_for_editing = 4096 # Mere plads til lange historier
        # elif story_length == 'mellem':
        #     max_tokens_for_editing = 3072 # Lidt mere end kort

        # current_app.logger.info(
        #    f"AI Service (Redaktør): Max tokens sat til {max_tokens_for_editing} baseret på ønsket længde '{story_length}'.")

        generation_config_settings = {
            "max_output_tokens": 8192, #max_tokens_for_editing hvis den skal følge overstående
            "temperature": 0.65, # Lidt lavere for mere fokuseret redigering
            # "top_p": 0.9, # Kan overvejes
        }
        gen_config = genai.types.GenerationConfig(**generation_config_settings)

        current_app.logger.info(
            f"AI Service: Kalder Gemini for redigering af historie (Max Tokens: {gen_config.max_output_tokens}, Temp: {gen_config.temperature}).")

        response = model.generate_content(
            prompt_string,
            generation_config=gen_config,
            safety_settings=safety_settings
        )

        # 3. Parse svaret fra AI'en (forventer titel på første linje, så historien)
        raw_edited_text = ""
        try:
            raw_edited_text = response.text.strip()
            if not raw_edited_text:
                current_app.logger.warning("AI Service: Redigeret historie (Trin 3) fra Gemini var tomt. Returnerer originalt udkast.")
                # Hvis redigering fejler eller returnerer tomt, kan vi overveje at returnere det uredigerede udkast fra Trin 2
                return story_draft_title, story_draft_content + "\n\n(Redigering mislykkedes, viser uredigeret udkast)"

            current_app.logger.info("AI Service: Redigeret historie (Trin 3) modtaget.")
            current_app.logger.debug(
                f"AI Service: Rå output fra Trin 3 AI (første 300 tegn):\n{raw_edited_text[:300]}")

            # Simpel parsing: titel på første linje, resten er historie
            parts = raw_edited_text.split('\n', 1)
            if len(parts) >= 1 and parts[0].strip():
                edited_title = parts[0].strip()
                if len(parts) > 1 and parts[1].strip():
                    edited_content = parts[1].strip()
                else: # Kun titel, ingen historie - usandsynligt for redigering
                    current_app.logger.warning(f"AI Service (Redaktør): Modtog kun titel, ingen historietekst. Titel: '{edited_title}'. Råtekst: {raw_edited_text[:200]}")
                    edited_content = "Historien mangler efter titlen (Redigeringsfejl)."
            else: # Tom respons eller ingen linjeskift (usandsynligt hvis AI følger prompt)
                current_app.logger.warning(f"AI Service (Redaktør): Kunne ikke parse titel og historie fra redigeret output. Råtekst: {raw_edited_text[:200]}")
                edited_title = story_draft_title # Fallback til original titel
                edited_content = raw_edited_text # Brug råtekst som fallback for indhold

            if not edited_content:
                 current_app.logger.warning("AI Service (Redaktør): Selve historieteksten er tom efter parsing. Returnerer original.")
                 return story_draft_title, story_draft_content + "\n\n(Redigering resulterede i tom historie, viser uredigeret udkast)"


        except ValueError as e_safety:
            current_app.logger.error(
                f"AI Service: Svar til redigeret historie (Trin 3) blokeret: {e_safety}")
            current_app.logger.error(
                f"AI Service: Prompt Feedback (Trin 3): {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'Ingen prompt feedback.'}")
            edited_content = f"Fejl: Indhold til den redigerede historie blev blokeret. Viser uredigeret udkast: \n\n{story_draft_content}"
            # edited_title forbliver originalens titel
        except Exception as e_parse:
            current_app.logger.error(
                f"AI Service: Fejl ved parsing af AI-svar (Trin 3): {e_parse}\n{traceback.format_exc()}")
            edited_content = f"Fejl: Kunne ikke parse AI-svar for redigeret historie (Trin 3). Viser uredigeret: \n\n{story_draft_content}"
            # edited_title forbliver originalens titel

    except Exception as e_general:
        current_app.logger.error(
            f"AI Service: Generel fejl under redigering af historie (Trin 3): {e_general}\n{traceback.format_exc()}")
        edited_content = f"Fejl: Teknisk fejl i AI-service (Trin 3). Viser uredigeret: \n\n{story_draft_content}"
        # edited_title forbliver originalens titel

    return edited_title, edited_content
