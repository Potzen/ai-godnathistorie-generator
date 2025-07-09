# scripts/master_daily_poster.py
import sys
import os
import random
import traceback
import base64
from datetime import datetime

# Denne vigtige blok sikrer, at scriptet kan finde dine andre moduler
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Projekt-specifikke imports ---
from app import create_app
from models import Story
from services.ai_service import (
    generate_story_text_from_gemini,
    generate_image_prompt_from_gemini,
    generate_image_with_vertexai
)
from services.facebook_service import post_photo_to_facebook_page
from prompts.weekly_prompts import PROMPTS

from google.generativeai.types import HarmCategory, HarmBlockThreshold

SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}


def get_prompt_type_for_today():
    """Vælger en prompt-type baseret på ugedagen (Mandag=0, ..., Søndag=6)."""
    weekday = datetime.now().weekday()
    if weekday in [0, 2]: return "article"
    if weekday in [1, 3]: return "connection_tip"
    if weekday == 4: return "weekend"
    if weekday == 5: return "character"
    return None


def main():
    print(f"--- Starter Master Poster - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    app = create_app()
    prompt_type = get_prompt_type_for_today()

    if prompt_type is None:
        print("Ingen opslag planlagt for i dag. Afslutter.")
        return

    print(f"Valgt prompt-type for i dag: '{prompt_type}'")
    temp_image_path = None

    with app.app_context():
        try:
            # 1. Hent en tilfældig historie
            # *** HER ER RETTELSEN ***
            # Vi bruger .isnot(None) for en korrekt SQLAlchemy-forespørgsel
            stories = Story.query.filter(Story.is_log_entry == True, Story.problem_name.isnot(None)).all()
            if not stories:
                print(
                    "FEJL: Ingen passende historier fundet i databasen. Krav: is_log_entry=True og skal have et problem_name.")
                return

            random_story = random.choice(stories)
            print(f"Valgt historie: '{random_story.title}' (ID: {random_story.id})")

            # 2. Forbered data til at formatere prompten
            story_data = {
                "title": random_story.title,
                "problem_name": random_story.problem_name,
                "character_name": random_story.problem_name,
            }

            prompt_template = PROMPTS.get(prompt_type)
            if prompt_template is None:
                raise ValueError(f"Kunne ikke finde en prompt for typen '{prompt_type}'.")

            # 3. Generer tekst-indhold til opslaget
            print("Genererer tekst til opslag...")
            gen_config = {"max_output_tokens": 1024, "temperature": 0.75}
            formatted_prompt = prompt_template.format(**story_data)

            results = generate_story_text_from_gemini(formatted_prompt, gen_config, SAFETY_SETTINGS)
            if not results or "Fejl" in results[0][0] or "Blokeret" in results[0][0]:
                raise ValueError(f"Kunne ikke generere tekst fra AI. Grund: {results[0][1] if results else 'Ukendt'}")

            _title, post_text = results[0]
            print("Tekst genereret succesfuldt.")

            # 4. Generer et billede til opslaget
            print("Genererer billede til opslag...")
            image_prompt_text = generate_image_prompt_from_gemini(
                story_text=random_story.content,
                karakter_str=random_story.problem_name,
                sted_str="et passende sted for historien"
            )
            image_data_url = generate_image_with_vertexai(image_prompt_text)
            if image_data_url is None:
                raise ValueError("Kunne ikke generere billed-URL fra Vertex AI.")

            header, encoded_data = image_data_url.split(',', 1)
            image_bytes = base64.b64decode(encoded_data)
            temp_image_path = "daily_master_post_image.png"
            with open(temp_image_path, "wb") as f:
                f.write(image_bytes)
            print(f"Billede gemt midlertidigt som '{temp_image_path}'")

            # 5. Post til Facebook
            print("Poster til Facebook...")
            post_photo_to_facebook_page(
                page_id=app.config["FACEBOOK_PAGE_ID"],
                page_access_token=app.config["FACEBOOK_PAGE_ACCESS_TOKEN"],
                image_path=temp_image_path,
                caption=post_text
            )
            print("SUCCESS: Opslag blev publiceret på Facebook!")

        except Exception as e:
            print(f"FEJL: En fejl opstod i main-loop: {e}")
            traceback.print_exc()
        finally:
            if temp_image_path and os.path.exists(temp_image_path):
                os.remove(temp_image_path)
                print(f"Midlertidig billedfil slettet: {temp_image_path}")

    print("--- Master Poster færdig ---")


if __name__ == "__main__":
    main()