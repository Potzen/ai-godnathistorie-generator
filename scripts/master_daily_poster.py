# scripts/master_daily_poster.py
import sys
import os
import random
import traceback
import base64
from datetime import datetime
from dotenv import load_dotenv

# --- Indlæsning af .env og credentials ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
if credentials_path:
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
else:
    print("ADVARSEL: GOOGLE_APPLICATION_CREDENTIALS mangler. Vertex AI vil fejle.")

sys.path.append(project_root)

# --- Projekt-specifikke imports ---
from app import create_app
from services.ai_service import (
    generate_story_text_from_gemini,
    generate_image_with_vertexai
)
from services.facebook_service import post_photo_to_facebook_page
from prompts.weekly_prompts import PROMPTS, IMAGE_SCENE_GENERATOR_PROMPT
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# --- TEMA-BANK ---
THEME_BANK = {
    "Samarbejde": "Lære at arbejde sammen med andre for at løse et problem eller nå et fælles mål.",
    "Frygt for mørke": "Håndtering af den almindelige frygt for mørket og at være alene om natten.",
    "At dele med andre": "Vigtigheden af at dele legetøj og opmærksomhed med søskende eller venner.",
    "Venskab": "Hvad det vil sige at være en god ven, og hvordan man skaber og vedligeholder venskaber.",
    "Følelsen af at være udenfor": "Når man føler sig anderledes eller holdt udenfor i en gruppe.",
    "At sige undskyld": "Modet til at indrømme en fejl og sige undskyld.",
    "Fantasi og kreativitet": "At bruge sin fantasi til at skabe nye verdener og løse problemer.",
    "Utålmodighed": "At lære at vente på tur og forstå, at gode ting kan tage tid.",
    "Selvtillid": "At tro på sig selv og turde prøve nye ting, selvom det er svært.",
    "Miljøbevidsthed": "At passe på naturen og vores planet på en børnevenlig måde.",
}

SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}


def get_prompt_type_for_today():
    weekday = datetime.now().weekday()
    if weekday in [0, 2]: return "article"
    if weekday in [1, 3]: return "connection_tip"
    if weekday == 4: return "weekend"
    if weekday == 5: return "character"
    return None


def main():
    print(f"--- Starter Content Generator - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")

    app = create_app()
    prompt_type = get_prompt_type_for_today()

    if prompt_type is None:
        print("Ingen opslag planlagt for i dag. Afslutter.")
        return

    print(f"Valgt opslags-type for i dag: '{prompt_type}'")
    temp_image_path = None

    with app.app_context():
        try:
            theme_name, theme_description = random.choice(list(THEME_BANK.items()))
            print(f"Valgt tema: '{theme_name}'")

            story_data = {
                "theme_name": theme_name,
                "theme_description": theme_description,
            }

            prompt_template = PROMPTS.get(prompt_type)
            if prompt_template is None:
                raise ValueError(f"Kunne ikke finde en prompt for typen '{prompt_type}'.")

            print("Trin 1: Genererer tekst til Facebook-opslag...")
            gen_config_text = {"max_output_tokens": 2048, "temperature": 0.8}
            formatted_prompt_text = prompt_template.format(**story_data)

            results = generate_story_text_from_gemini(formatted_prompt_text, gen_config_text, SAFETY_SETTINGS)
            if not results or "Fejl" in results[0][0] or "Blokeret" in results[0][0]:
                raise ValueError(f"Kunne ikke generere tekst fra AI. Grund: {results[0][1] if results else 'Ukendt'}")

            _title, post_text = results[0]
            print("Tekst genereret succesfuldt.")

            # === OPDATERET BILLEDE-GENERERING ===
            print("Trin 2: Genererer unik visuel scene baseret på den færdige tekst...")
            # Vi bruger nu den færdige 'post_text' som inspiration for billedet
            scene_gen_prompt = IMAGE_SCENE_GENERATOR_PROMPT.format(theme_name=theme_name, post_text=post_text)
            gen_config_scene = {"max_output_tokens": 1024, "temperature": 0.85}
            scene_results = generate_story_text_from_gemini(scene_gen_prompt, gen_config_scene, SAFETY_SETTINGS)

            if not scene_results or "Fejl" in scene_results[0][0]:
                raise ValueError("Kunne ikke generere en visuel scene-beskrivelse.")

            _scene_title, scene_description = scene_results[0]
            print(f"Visuel scene genereret: {scene_description[:120]}...")

            final_image_prompt = (
                f"{scene_description} "
                "Style: Whimsical and enchanting fairytale illustration, 3D digital art, high-quality, cinematic lighting, soft and dreamy atmosphere, child-friendly."
            )

            print("Trin 3: Genererer det endelige billede...")
            image_data_url = generate_image_with_vertexai(final_image_prompt)
            if image_data_url is None:
                raise ValueError("Kunne ikke generere billed-URL fra Vertex AI.")

            header, encoded_data = image_data_url.split(',', 1)
            image_bytes = base64.b64decode(encoded_data)
            temp_image_path = "daily_master_post_image.png"
            with open(temp_image_path, "wb") as f:
                f.write(image_bytes)
            print(f"Billede gemt midlertidigt som '{temp_image_path}'")

            print("Trin 4: Poster til Facebook...")
            page_id = os.getenv("FACEBOOK_PAGE_ID")
            access_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")

            if not page_id or not access_token:
                raise ValueError("FEJL: FACEBOOK_PAGE_ID eller FACEBOOK_PAGE_ACCESS_TOKEN mangler i .env-filen.")

            post_photo_to_facebook_page(
                page_id=page_id,
                page_access_token=access_token,
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

    print("--- Content Generator færdig ---")


if __name__ == "__main__":
    main()