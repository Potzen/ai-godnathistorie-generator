import base64
import json
import logging
import time
import traceback

import google.generativeai as genai
import vertexai
from flask import current_app
from flask_login import current_user
from google.api_core.exceptions import InternalServerError
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from vertexai.preview.vision_models import ImageGenerationModel

from prompts.character_trait_suggestion_prompt import build_character_trait_suggestion_prompt
from prompts.image_prompt_generation_prompt import build_image_prompt_generation_prompt
from prompts.logbook_analysis_prompt import build_logbook_analysis_prompt
from prompts.narrative_briefing_prompt import build_narrative_briefing_prompt
from prompts.narrative_drafting_prompt import build_narrative_drafting_prompt
from prompts.narrative_editing_prompt import build_narrative_editing_prompt
from prompts.narrative_question_prompt import build_narrative_question_prompt
from prompts.problem_image_prompt import build_problem_image_prompt
from services.rag_service import find_relevant_chunks_v2

logger = logging.getLogger(__name__)

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

_imagen_model = None


def _get_imagen_model():
    global _imagen_model
    if _imagen_model is None:
        _imagen_model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-002")
    return _imagen_model


def get_ai_suggested_character_traits(narrative_focus: str) -> dict:
    try:
        prompt = build_character_trait_suggestion_prompt(narrative_focus)
        model = genai.GenerativeModel('gemini-2.5-pro-preview-06-05')
        gen_config = genai.types.GenerationConfig(
            max_output_tokens=8192,
            temperature=0.5,
            response_mime_type="application/json",
        )
        response = model.generate_content(prompt, generation_config=gen_config,
                                          safety_settings=_SAFETY_BLOCK_MEDIUM)
        if not response.text:
            return {"error": "AI returnerede tomt svar for karaktertræk."}
        text = response.text.strip().lstrip("```json").rstrip("```").strip()
        return json.loads(text)
    except json.JSONDecodeError:
        current_app.logger.error(f"JSON parse fejl i get_ai_suggested_character_traits")
        return {"error": "Kunne ikke parse AI-svar (JSON formatfejl)."}
    except Exception as e:
        current_app.logger.error(f"Fejl i get_ai_suggested_character_traits: {e}\n{traceback.format_exc()}")
        return {"error": f"Intern fejl: {e}"}


def generate_narrative_brief(original_user_inputs: dict) -> str:
    try:
        prompt = build_narrative_briefing_prompt(original_user_inputs)
        model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        gen_config = genai.types.GenerationConfig(max_output_tokens=4096, temperature=0.5)
        response = model.generate_content(prompt, generation_config=gen_config,
                                          safety_settings=_SAFETY_BLOCK_NONE)

        candidate = response.candidates[0] if response.candidates else None
        if not candidate or not candidate.content.parts:
            return "Fejl: AI returnerede intet indhold for narrativt brief."

        finish = candidate.finish_reason.name if hasattr(candidate.finish_reason, 'name') else str(candidate.finish_reason)
        if finish != 'STOP':
            return f"Fejl: AI kunne ikke generere et komplet narrativt brief (finish_reason: {finish})."

        text = response.text.strip()
        if not text:
            return "Fejl: AI returnerede tomt narrativt brief."
        return text

    except Exception as e:
        current_app.logger.error(f"Fejl i generate_narrative_brief: {e}\n{traceback.format_exc()}")
        return "Fejl: Teknisk fejl under generering af narrativt brief."


def draft_narrative_story_with_rag(structured_brief: str, original_user_inputs: dict,
                                   narrative_focus_for_rag: str,
                                   continuation_context: dict = None) -> tuple:
    max_retries = 2
    for attempt in range(max_retries):
        try:
            rag_chunks = []
            if narrative_focus_for_rag and narrative_focus_for_rag.strip():
                rag_chunks = find_relevant_chunks_v2(narrative_focus_for_rag, top_k=2)

            prompt = build_narrative_drafting_prompt(
                structured_brief=structured_brief,
                rag_context=rag_chunks,
                original_user_inputs=original_user_inputs,
                continuation_context=continuation_context,
            )

            length_pref = original_user_inputs.get('length', 'mellem')
            max_tokens = 4096
            if length_pref == 'kort':
                max_tokens = 2048
            elif length_pref == 'lang':
                max_tokens = 8192

            model = genai.GenerativeModel('gemini-2.5-pro-preview-06-05')
            gen_config = genai.types.GenerationConfig(max_output_tokens=max_tokens, temperature=0.6, top_p=0.95)
            response = model.generate_content(prompt, generation_config=gen_config,
                                              safety_settings=_SAFETY_BLOCK_NONE)

            raw = response.text.strip()
            if not raw:
                raise ValueError("AI returnerede tomt historieudkast.")

            parts = raw.split('\n', 1)
            title = parts[0].strip() if parts and parts[0].strip() else "Uden Titel"
            content = parts[1].strip() if len(parts) > 1 and parts[1].strip() else raw

            return title, content

        except InternalServerError as e:
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                raise
        except Exception as e:
            current_app.logger.error(f"Fejl i draft_narrative_story: {e}\n{traceback.format_exc()}")
            raise

    raise InternalServerError("Kunne ikke generere historie efter flere forsøg.")


def edit_narrative_story(story_draft_title: str, story_draft_content: str,
                         original_user_inputs: dict) -> tuple:
    try:
        prompt = build_narrative_editing_prompt(
            story_draft_title=story_draft_title,
            story_draft_content=story_draft_content,
            original_user_inputs=original_user_inputs,
        )
        model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        gen_config = genai.types.GenerationConfig(max_output_tokens=8192, temperature=0.65)
        response = model.generate_content(prompt, generation_config=gen_config,
                                          safety_settings=_SAFETY_BLOCK_NONE)

        raw = response.text.strip()
        if not raw:
            return story_draft_title, story_draft_content

        parts = raw.split('\n', 1)
        title = parts[0].strip() if parts[0].strip() else story_draft_title
        content = parts[1].strip() if len(parts) > 1 and parts[1].strip() else raw

        return title, content

    except Exception as e:
        current_app.logger.error(f"Fejl i edit_narrative_story: {e}\n{traceback.format_exc()}")
        return story_draft_title, story_draft_content


def analyze_story_for_logbook(story_content: str) -> dict:
    try:
        prompt = build_logbook_analysis_prompt(story_content)
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        gen_config = genai.types.GenerationConfig(temperature=0.4, response_mime_type="application/json")
        response = model.generate_content(prompt, generation_config=gen_config)
        return json.loads(response.text)
    except json.JSONDecodeError as e:
        current_app.logger.error(f"JSON fejl i analyze_story_for_logbook: {e}")
        return {"error": "AI returnerede ugyldigt format."}
    except Exception as e:
        current_app.logger.error(f"Fejl i analyze_story_for_logbook: {e}\n{traceback.format_exc()}")
        return {"error": f"Teknisk fejl: {e}"}


def generate_image_prompt_from_gemini(story_text: str, karakter_str: str, sted_str: str) -> str:
    default = "A whimsical fairytale illustration, child-friendly, high-quality 3D digital art."
    try:
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        prompt = build_image_prompt_generation_prompt(story_text, karakter_str, sted_str)
        response = model.generate_content(prompt)
        if response.text and response.text.strip():
            return response.text.strip()
    except Exception as e:
        current_app.logger.error(f"Fejl i generate_image_prompt_from_gemini: {e}")
    return default


def generate_image_with_vertexai(image_prompt_text: str):
    if not current_app.config.get('GOOGLE_CLOUD_PROJECT_ID'):
        current_app.logger.error("GOOGLE_CLOUD_PROJECT_ID mangler – kan ikke generere billede.")
        return None

    model = _get_imagen_model()
    current_prompt = image_prompt_text

    for attempt in range(3):
        try:
            if attempt == 1:
                current_prompt += ", impressionistic oil painting"

            response = model.generate_images(prompt=current_prompt, number_of_images=1, guidance_scale=9)

            if response and response.images:
                img = response.images[0]
                if hasattr(img, '_image_bytes') and img._image_bytes:
                    b64 = base64.b64encode(img._image_bytes).decode('utf-8')
                    return f"data:image/png;base64,{b64}"

            if attempt == 2:
                return None

            time.sleep(1.5)

        except Exception as e:
            current_app.logger.error(f"Imagen fejl (forsøg {attempt + 1}): {e}")
            non_retryable = ["quota exceeded", "permission denied", "billing", "does not exist"]
            if any(s in str(e).lower() for s in non_retryable) or attempt == 2:
                return None
            time.sleep(1.5)

    return None


def generate_reflection_questions(final_story_title: str, final_story_content: str,
                                  narrative_brief: str, original_user_inputs: dict) -> list:
    try:
        prompt = build_narrative_question_prompt(
            final_story_title=final_story_title,
            final_story_content=final_story_content,
            narrative_brief=narrative_brief,
            original_user_inputs=original_user_inputs,
        )
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        gen_config = genai.types.GenerationConfig(max_output_tokens=2048, temperature=0.7)
        response = model.generate_content(prompt, generation_config=gen_config,
                                          safety_settings=_SAFETY_BLOCK_NONE)
        raw = response.text.strip()
        if not raw:
            return []
        questions = []
        for line in raw.split('\n'):
            line = line.strip()
            if line.startswith(tuple(f"{i}." for i in range(1, 10))):
                line = line[line.find('.') + 1:].strip()
            elif line.startswith('-'):
                line = line[1:].strip()
            if line:
                questions.append(line)
        return questions
    except Exception as e:
        current_app.logger.error(f"Fejl i generate_reflection_questions: {e}\n{traceback.format_exc()}")
        return []


def generate_problem_image(narrative_data: dict) -> dict:
    try:
        prompt = build_problem_image_prompt(narrative_data)
        image_url = generate_image_with_vertexai(prompt)
        if image_url:
            return {"image_url": image_url, "image_prompt_used": prompt}
        return {"error": "Kunne ikke generere problem-billede."}
    except Exception as e:
        current_app.logger.error(f"Fejl i generate_problem_image: {e}\n{traceback.format_exc()}")
        return {"error": f"Intern fejl: {e}"}
