# Fil: scripts/daily_article_poster.py
import sys
import os

# Føj rodmappen (GodnathistorieApp) til Python's søgesti
# Dette sikrer, at vi kan finde mapper som 'app', 'services' og 'prompts'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Nu vil de normale imports virke igen
from dotenv import load_dotenv

load_dotenv()

import base64
import traceback
import random
import vertexai
from google.oauth2 import service_account

from app import create_app
from services.ai_service import (
    generate_story_text_from_gemini,
    generate_image_prompt_from_gemini,
    generate_image_with_vertexai,
    generate_parenting_article
)
from services.facebook_service import post_photo_to_facebook_page
from prompts.story_generation_prompt import build_story_prompt
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# --- Konfiguration ---
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CLOUD_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")

if not all([FACEBOOK_PAGE_ID, FACEBOOK_PAGE_ACCESS_TOKEN, GOOGLE_API_KEY, GOOGLE_CLOUD_PROJECT_ID]):
    print("FEJL: Nødvendige nøgler mangler i din .env-fil.")
    sys.exit(1)

# Lister med emner...
KARAKTERER = ["en nysgerrig ræv ved navn Rikki", "et lille spøgelse, der var bange for mørke",
              "en drage, der ikke kunne spy ild, men nysede blomster", "en robot, der elskede at bage måne-kager",
              "en fe, der havde mistet sin tryllestav", "en søvnig bjørn, der ledte efter den perfekte hovedpude",
              "en sky, der elskede at forme sig som forskellige dyr",
              "en klog, gammel skildpadde med et landkort på sit skjold", "en pingvin, der drømte om at flyve",
              "et egern, der havde glemt, hvor den havde gemt sine nødder", "en modig lille ridder på en snegl",
              "en havfrue, der samlede på sunkne stjerner", "en gnom, der passede på en have fuld af krystaller",
              "en talende bog, der fortalte historier om sig selv",
              "et glemsomt postbud, der delte drømme ud i stedet for breve",
              "en opfinder-mus, der byggede maskiner af tandhjul og knapper",
              "et venligt monster under sengen, der kun spiste sokker"]
STEDER = ["i en fortryllet skov, hvor træerne hviskede godnat", "på en sky, der sejlede højt på nattehimlen",
          "i en hemmelig have bag et gammelt ur", "på bunden af havet i en by lavet af funklende muslingeskaller",
          "på et bibliotek, hvor bøgerne blev levende om natten",
          "i et slot lavet udelukkende af is og sne, der aldrig smeltede",
          "på en øde ø, hvor sandet var lavet af sukker", "inde i en gigantisk sæbeboble, der svævede afsted",
          "i et omvendt hus, hvor man gik på loftet", "på en månestråle, der fungerede som en rutsjebane",
          "i en dal, hvor ekkoerne kunne synge", "på et tog lavet af stjernestøv, der kørte mellem planeterne",
          "i en hule bag et vandfald, der glimtede i alle regnbuens farver",
          "i en by bygget i toppen af gigantiske svampe", "på et tæppe vævet af drømme, der kunne flyve"]
PLOTS = ["handlede om at finde en forsvundet stjerne", "handlede om at lære at dele sit yndlingslegetøj med en ny ven",
         "handlede om vigtigheden af at være en god ven, selv når det er svært",
         "handlede om at turde prøve noget nyt, selvom det kildede i maven",
         "handlede om at opdage magien i de små ting i hverdagen",
         "handlede om at levere en meget vigtig besked til Månekongen",
         "handlede om at bygge den hyggeligste hule i hele verden",
         "handlede om at finde de syv farver til en regnbue, der havde mistet dem",
         "handlede om at sige undskyld, selvom man ikke havde lyst",
         "handlede om at opdage, at det er okay at være anderledes",
         "handlede om at hjælpe en, der var faret vild, med at finde hjem",
         "handlede om at samle de smukkeste lyde til en godnatsang",
         "handlede om at male en solopgang, før solen stod op",
         "handlede om at finde en skat, der ikke var lavet af guld, men af venskab",
         "handlede om at tænde alle lygterne i en mørk by"]


def generate_sophisticated_post():
    print("Starter generering af artikel-opslag...")

    dagens_karakter = random.choice(KARAKTERER)
    dagens_sted = random.choice(STEDER)
    dagens_plot = random.choice(PLOTS)
    print(f"Dagens tema: '{dagens_plot}'")

    story_prompt = build_story_prompt(karakter_str=dagens_karakter, sted_str=dagens_sted, plot_str=dagens_plot,
                                      length_instruction="Skriv en kort historie.",
                                      mood_prompt_part="Stemningen skal være magisk.", listener_context_instruction="",
                                      ending_instruction="Afslut positivt.", negative_prompt_text="ingen farlige dyr",
                                      is_bedtime_story=True)
    story_results = generate_story_text_from_gemini(story_prompt, {"max_output_tokens": 1500, "temperature": 0.75}, {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE})
    if not story_results or "Fejl" in story_results[0][0]:
        raise Exception("Kunne ikke generere baggrunds-historie.")

    story_title, story_content = story_results[0]
    print(f"Baggrunds-historie genereret: '{story_title}'")

    parent_article = generate_parenting_article(story_title, dagens_plot)
    if not parent_article:
        raise Exception("Kunne ikke generere pædagogisk artikel.")
    print("Pædagogisk artikel genereret.")

    branding_url = "www.readmeastory.app"
    final_post_text = (
        f"{parent_article}\n\n"
        f"✨ Dagens godnathistorie, '{story_title}', er inspireret af dette tema.\n"
        f"Læs den og hundredvis af andre personlige godnathistorier på {branding_url}!\n\n"
        f"#Godnathistorie #Forældre #Børneopdragelse #LæsningForBørn #AI"
    )

    try:
        credentials_path = "/home/Potzen/gen-lang-client-0269317733-c9b35424f793.json"
        credentials = service_account.Credentials.from_service_account_file(credentials_path, scopes=[
            "https://www.googleapis.com/auth/cloud-platform"])
        vertexai.init(project=GOOGLE_CLOUD_PROJECT_ID, credentials=credentials)
    except Exception as e:
        print(f"KRITISK FEJL under indlæsning af nøglefil: {e}")
        raise e

    image_prompt = generate_image_prompt_from_gemini(story_content, dagens_karakter, dagens_sted)
    image_data_url = generate_image_with_vertexai(image_prompt)
    if not image_data_url:
        raise Exception("Kunne ikke generere billede fra AI-servicen.")

    try:
        header, encoded_data = image_data_url.split(',', 1)
        image_bytes = base64.b64decode(encoded_data)
        temp_image_path = "daily_article_image.png"
        with open(temp_image_path, "wb") as f:
            f.write(image_bytes)
        print(f"Billede genereret og gemt midlertidigt som '{temp_image_path}'")
        return final_post_text, temp_image_path
    except Exception as e:
        raise Exception(f"Fejl under klargøring af billede: {e}")


def run_article_job():
    app = create_app()
    with app.app_context():
        temp_image_path = None
        try:
            post_text, temp_image_path = generate_sophisticated_post()
            post_photo_to_facebook_page(page_id=FACEBOOK_PAGE_ID, page_access_token=FACEBOOK_PAGE_ACCESS_TOKEN,
                                        image_path=temp_image_path, caption=post_text)
            print("\nArtikel-opslag er fuldført succesfuldt!")
        except Exception as e:
            print(f"\nEn fejl opstod under artikel-jobbet: {e}")
            traceback.print_exc()
        finally:
            if temp_image_path and os.path.exists(temp_image_path):
                os.remove(temp_image_path)
                print(f"Midlertidig billedfil '{temp_image_path}' er blevet slettet.")


if __name__ == "__main__":
    run_article_job()