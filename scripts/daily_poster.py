# Fil: daily_poster.p
from dotenv import load_dotenv
load_dotenv()

import os
import sys

# Føj rodmappen (GodnathistorieApp) til Python's søgesti
# Dette sikrer, at vi kan finde mapper som 'app', 'services' og 'prompts'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import base64
import traceback
import random
import vertexai
from google.oauth2 import service_account

from app import create_app
from services.ai_service import (
    generate_story_text_from_gemini,
    generate_image_prompt_from_gemini,
    generate_image_with_vertexai
)
from services.facebook_service import post_photo_to_facebook_page
from prompts.story_generation_prompt import build_story_prompt
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# --- LÆS KONFIGURATION FRA MILJØVARIABLER ---
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CLOUD_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID") # <--- RETTELSE 2: Sørger for at denne er defineret

if not all([FACEBOOK_PAGE_ID, FACEBOOK_PAGE_ACCESS_TOKEN, GOOGLE_API_KEY, GOOGLE_CLOUD_PROJECT_ID]):
    print("FEJL: En eller flere nødvendige nøgler mangler i din .env-fil (Facebook eller Google).")
    sys.exit(1)
# ------------------------------------------------

# ======================================================================
# --- KRAFTIGT UDVIDEDE LISTER FOR MAKSIMAL VARIATION ---
# ======================================================================
KARAKTERER = [
    # Dyr
    "en nysgerrig ræv ved navn Rikki",
    "en søvnig bjørn, der ledte efter den perfekte hovedpude",
    "et egern, der havde glemt, hvor den havde gemt sine nødder",
    "en klog, gammel skildpadde med et landkort på sit skjold",
    "en pingvin, der drømte om at flyve til varmere lande",
    "en lille hval, der lærte at synge havets sange",
    "en kamæleon, der ikke kunne beslutte sig for en farve",
    "et dovendyr, der altid kom for sent, men havde god tid",
    "en edderkop, der elskede at væve portrætter af sine venner",
    "en muldvarp, der var en fantastisk opdagelsesrejsende under jorden",
    "en ildflue, der var bange for mørke",
    "en stolt løve med en meget lille stemme",
    "en elefant, der var bange for mus",

    # Fantasivæsner
    "et lille spøgelse, der hellere ville kramme end skræmme",
    "en drage, der ikke kunne spy ild, men nysede funklende blomster",
    "en fe, der havde mistet sin tryllestav",
    "en havfrue, der samlede på sunkne stjerner",
    "en gnom, der passede på en have fuld af krystaller",
    "et venligt monster under sengen, der kun spiste glemte sokker",
    "en sky, der elskede at forme sig som forskellige dyr",
    "en lille trold, der boede i en træstub og samlede på knapper",
    "en enhjørning, hvis horn lyste i takt med musik",
    "en vind-ånd, der elskede at puste til mælkebøtter",

    # Ting med personlighed
    "en talende bog, der fortalte historier om sig selv",
    "et glemsomt postbud, der delte drømme ud i stedet for breve",
    "en opfinder-mus, der byggede maskiner af tandhjul og viskelædere",
    "en magisk blyant, der kunne tegne ting, som blev virkelige",
    "en gammel, rusten nøgle, der ledte efter sin lås",
    "en tekop, der altid var halvt fuld af eventyr",
    "et flyvende tæppe, der var lidt bange for højder",
    "en lygtepæl, der fortalte historier til dem, der stoppede op for at lytte"
]

STEDER = [
    # Natur & Landskaber
    "i en fortryllet skov, hvor træerne hviskede godnat",
    "på en sky, der sejlede højt på nattehimlen",
    "i en hemmelig have bag et gammelt ur",
    "på bunden af havet i en by lavet af funklende muslingeskaller",
    "i en dal, hvor ekkoerne kunne synge i kor",
    "på en øde ø, hvor sandet var lavet af gyldent sukker",
    "i en hule bag et vandfald, der glimtede i alle regnbuens farver",
    "i en by bygget i toppen af gigantiske, bløde svampe",
    "på en eng, hvor blomsterne lyste i mørket",
    "i en krystal-grotte, hvor væggene viste drømme",
    "på toppen af det højeste bjerg, tættere på stjernerne end nogensinde",
    "ved en flod, der var lavet af flydende måneskin",

    # Bygninger & Byer
    "på et bibliotek, hvor bøgerne blev levende om natten",
    "i et slot lavet udelukkende af is og sne, der aldrig smeltede",
    "i et omvendt hus, hvor man gik på loftet og sov i kælderen",
    "i et observatorium bygget til at kigge på stjernernes drømme",
    "i en lille butik, der solgte glemte minder og tabte ting",
    "på et værksted, hvor ødelagt legetøj blev repareret med magi",
    "i et bageri, hvor kagerne sang, når de var færdigbagte",
    "på et fyrtårn, der lyste for skibe, der sejlede i himmelrummet",

    # Transport & Rejse
    "på et tog lavet af stjernestøv, der kørte mellem planeterne",
    "inde i en gigantisk sæbeboble, der svævede lydløst afsted",
    "på et tæppe vævet af drømme, der kunne flyve hvorhen det ville",
    "i en ubåd formet som en hval, der udforskede havets dybeste hemmeligheder",
    "på et skib med sejl lavet af edderkoppespind, der fangede vinden"
]

PLOTS = [
    # Quests & Opgaver
    "handlede om at finde en forsvundet stjerne og sætte den tilbage på himlen",
    "handlede om at levere en meget vigtig og hemmelig besked til Månekongen",
    "handlede om at bygge den hyggeligste hule i hele verden",
    "handlede om at finde de syv farver til en regnbue, der havde mistet dem",
    "handlede om at samle de smukkeste lyde i skoven til en godnatsang",
    "handlede om at male en solopgang, før solen selv nåede at stå op",
    "handlede om at finde en skat, der ikke var lavet af guld, men af venskab",
    "handlede om at tænde alle lygterne i en by, der var gået i sort",
    "handlede om at finde en magisk opskrift på den sødeste drømmesaft",

    # Følelser & Venskab
    "handlede om at lære at dele sit yndlingslegetøj med en ny ven",
    "handlede om vigtigheden af at være en god ven, selv når det er svært",
    "handlede om at sige undskyld, selvom man ikke havde lyst",
    "handlede om at hjælpe en, der var faret vild, med at finde hjem",
    "handlede om at opdage, at det er okay at være anderledes",
    "handlede om at trøste en ven, der var ked af det",
    "handlede om at lære at lytte, ikke bare med ørerne, men med hjertet",
    "handlede om at finde ud af, at man er modigere, end man selv tror",

    # Opdagelse & Magi
    "handlede om at turde prøve noget nyt, selvom det kildede i maven",
    "handlede om at opdage magien i de små, stille ting i hverdagen",
    "handlede om at finde ud af, hvor skyerne sover om natten",
    "handlede om at lære dyrenes hemmelige sprog",
    "handlede om at finde en dør, der førte til et sted, der ikke var på noget kort",
    "handlede om at opdage, at musik kan få selv de tristeste planter til at gro"
]
# ======================================================================


# ======================================================================

def generate_daily_content():
    """
    Trin 1: Genererer en ny, TILFÆLDIG historie og et billede hver gang.
    """
    print("Starter generering af dagens indhold...")

    dagens_karakter = random.choice(KARAKTERER)
    dagens_sted = random.choice(STEDER)
    dagens_plot = random.choice(PLOTS)

    print(
        f"Dagens emne: '{dagens_karakter}' som befinder sig '{dagens_sted}', og historien skal handle om '{dagens_plot}'.")

    prompt = build_story_prompt(
        karakter_str=dagens_karakter,
        sted_str=dagens_sted,
        plot_str=dagens_plot,
        length_instruction="Skriv en kort og hjertevarm historie.",
        mood_prompt_part="Stemningen skal være magisk og beroligende.",
        listener_context_instruction="",
        ending_instruction="Afslut historien på en positiv og opløftende måde.",
        negative_prompt_text="ingen farlige dyr",
        is_bedtime_story=True
    )

    generation_config = {"max_output_tokens": 1500, "temperature": 0.75}
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    story_results = generate_story_text_from_gemini(prompt, generation_config, safety_settings)
    if not story_results or "Fejl" in story_results[0][0]:
        raise Exception("Kunne ikke generere historietekst fra AI-servicen.")

    story_title, story_content = story_results[0]
    print(f"Historie genereret: '{story_title}'")

    branding_url = "www.readmeastory.app"
    full_story_text = (
        f"✨ Dagens Godnathistorie ✨\n\n"
        f"Titel: {story_title}\n\n"
        f"{story_content}\n\n"
        f"--- Skabt af {branding_url} ---"
    )

    # ======================================================================
    # === ÆNDRING: MEST ROBUSTE METODE - Indlæs nøglefil direkte ===
    # ======================================================================
    try:
        print("Indlæser Google-nøglefil direkte til Vertex AI...")

        # Definer den absolutte sti til din nøglefil på serveren
        credentials_path = "/home/Potzen/gen-lang-client-0269317733-c9b35424f793.json"

        # Opret et credentials-objekt direkte fra filstien
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

        # Initialiser Vertex AI med de direkte indlæste credentials
        vertexai.init(project=GOOGLE_CLOUD_PROJECT_ID, credentials=credentials)

        print("Vertex AI initialiseret succesfuldt med direkte nøglefil.")
    except Exception as e:
        print(f"KRITISK FEJL under direkte indlæsning af nøglefil: {e}")
        raise e
    # ======================================================================
    image_prompt = generate_image_prompt_from_gemini(story_content, dagens_karakter, dagens_sted)
    image_data_url = generate_image_with_vertexai(image_prompt)
    if not image_data_url:
        raise Exception("Kunne ikke generere billede fra AI-servicen.")

    try:
        header, encoded_data = image_data_url.split(',', 1)
        image_bytes = base64.b64decode(encoded_data)
        temp_image_path = "daily_post_image.png"
        with open(temp_image_path, "wb") as f:
            f.write(image_bytes)

        print(f"Billede genereret og gemt midlertidigt som '{temp_image_path}'")
        return full_story_text, temp_image_path
    except Exception as e:
        raise Exception(f"Fejl under klargøring af billede: {e}")


def run_daily_job():
    app = create_app()
    with app.app_context():
        temp_image_path = None
        try:
            story_text, temp_image_path = generate_daily_content()
            post_photo_to_facebook_page(
                page_id=FACEBOOK_PAGE_ID,
                page_access_token=FACEBOOK_PAGE_ACCESS_TOKEN,
                image_path=temp_image_path,
                caption=story_text
            )
            print("\nDagens job er fuldført succesfuldt!")
        except Exception as e:
            print(f"\nEn fejl opstod under dagens job: {e}")
            traceback.print_exc()
        finally:
            if temp_image_path and os.path.exists(temp_image_path):
                os.remove(temp_image_path)
                print(f"Midlertidig billedfil '{temp_image_path}' er blevet slettet.")


if __name__ == "__main__":
    run_daily_job()