# Fil: services/ai_service.py
from flask import current_app # For at tilgå logger og config
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from vertexai.preview.vision_models import ImageGenerationModel
import base64
import time
import traceback
import vertexai
from prompts.image_prompt_generation_prompt import build_image_prompt_generation_prompt

# Her vil vi senere definere funktioner som:
# - generate_story_text(prompt_details)
# - generate_image_prompt(story_text)
# - generate_image(image_prompt)
# - (Senere) generate_audio_tts(text_to_speak)

def generate_story_text_from_gemini(full_prompt_string, generation_config_settings, safety_settings_values):
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
        model = genai.GenerativeModel('gemini-1.5-flash-latest')  # Sørg for at modelnavn er korrekt

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
                f"ai_service: Prompt Feedback: {response.prompt_feedback if response and hasattr(response, 'prompt_feedback') else 'Ingen prompt feedback.'}")
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
    max_retries = 2  # Samme retry-logik som før

    for attempt in range(max_retries):
        try:
            current_app.logger.info(
                f"ai_service: Imagen forsøg {attempt + 1}/{max_retries}. Prompt: {current_prompt_to_imagen[:100]}...")
            if attempt == 1:  # Andet forsøg
                current_app.logger.info("ai_service: Modificerer prompt til andet Imagen-forsøg...")
                # Overvej en mere sofistikeret måde at ændre prompten på, hvis nødvendigt
                current_prompt_to_imagen += ", impressionistic oil painting"
                # ", cinematic lighting, detailed, sharp focus, vibrant colors"
                # ", different composition"
                # Eller måske en helt anden stil: ", cartoonish, playful"
                # Eller tilføj negativ prompt: ", negative_prompt='text, blurry, watermark'"

            # Sørg for at ImageGenerationModel er importeret øverst i filen
            model_identifier = "imagen-3.0-generate-002"  # Eller den model du bruger
            model = ImageGenerationModel.from_pretrained(model_identifier)

            # Antal billeder sat til 1, som i din oprindelige kode
            response_imagen = model.generate_images(
                prompt=current_prompt_to_imagen,
                number_of_images=1,
                guidance_scale=30  # Værdi fra din oprindelige kode
                # Du kan tilføje andre parametre her om nødvendigt, f.eks. aspect_ratio, seed
            )

            if response_imagen and response_imagen.images:
                image_obj = response_imagen.images[0]
                if hasattr(image_obj, '_image_bytes') and image_obj._image_bytes:
                    image_bytes = image_obj._image_bytes
                    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                    image_data_url = f"data:image/png;base64,{image_base64}"
                    current_app.logger.info("ai_service: Billede genereret succesfuldt med Vertex AI.")
                    break  # Afslut loopet, da vi har et billede
                else:
                    current_app.logger.error(
                        f"ai_service: FEJL - _image_bytes mangler på billedeobjekt (forsøg {attempt + 1}).")
                    if attempt == max_retries - 1:
                        raise ValueError("EMPTY_IMAGE_BYTES_ERROR_AFTER_RETRIES")
            else:
                current_app.logger.error(
                    f"ai_service: FEJL - Vertex AI Imagen returnerede ingen billeder (forsøg {attempt + 1}). Respons: {response_imagen}")
                if attempt == max_retries - 1:
                    raise ValueError("EMPTY_IMAGE_LIST_ERROR_AFTER_RETRIES")

            if attempt < max_retries - 1:
                time.sleep(1.5)  # Vent lidt før næste forsøg

        except Exception as e_attempt:
            current_app.logger.error(
                f"ai_service: Fejl i Vertex AI billedgenereringsforsøg {attempt + 1}: {e_attempt}\n{traceback.format_exc()}")
            non_retryable_errors = ["quota exceeded", "permission denied", "billing", "does not exist",
                                    "kunne ikke initialisere"]
            if any(sub.lower() in str(e_attempt).lower() for sub in non_retryable_errors) or attempt == max_retries - 1:
                current_app.logger.error(
                    f"ai_service: Ikke-genoprettelig fejl eller sidste forsøg fejlet. Stopper billedgenerering.")
                return None  # Returner None for at signalere fejl

            if attempt < max_retries - 1:
                time.sleep(1.5)  # Vent lidt før næste forsøg

    if not image_data_url:
        current_app.logger.error("ai_service: Kunne ikke generere billede efter alle forsøg.")

    return image_data_url