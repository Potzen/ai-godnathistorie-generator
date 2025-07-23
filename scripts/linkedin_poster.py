# scripts/linkedin_poster.py

import os
import sys
import datetime
import requests
import traceback

# --- Opsætning af stier for at kunne importere fra din app ---
# Dette sikrer, at scriptet kan finde dine andre filer som 'app.py' og 'services/ai_service.py'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Nødvendige imports fra dit projekt ---
from app import create_app
from prompts.linkedin_content_prompt import get_linkedin_post_prompt
# Vi importerer den specifikke Gemini-funktion fra din ai_service
from services.ai_service import generate_story_text_from_gemini
from google.generativeai.types import HarmCategory, HarmBlockThreshold


# Funktion til at generere indhold vha. din AI-service
def generate_content(post_type, topic=""):
    """Genererer indhold vha. AI-prompt og din Gemini-service."""
    week_day = datetime.datetime.now().strftime('%A')
    prompt = get_linkedin_post_prompt(post_type, week_day, topic)
    if not prompt:
        print(f"Ingen handling for post_type '{post_type}' på en {week_day}.")
        return None

    print("Genererer LinkedIn-indhold med Gemini...")

    # Konfiguration til Gemini-kaldet
    generation_config = {"max_output_tokens": 1024, "temperature": 0.7}
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    # Kald din eksisterende Gemini-funktion
    # Den returnerer en liste af tuples, vi skal bruge den første.
    results = generate_story_text_from_gemini(prompt, generation_config, safety_settings)

    if results and results[0]:
        # Vi ignorerer titlen (det første element i tuple) og tager kun indholdet
        _title, content = results[0]
        return content
    else:
        print("Fejl: Kunne ikke generere indhold fra AI-servicen.")
        return None


# Funktion til at publicere på LinkedIn
def post_to_linkedin(content):
    """Poster det genererede indhold til LinkedIn."""
    access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
    author_urn = os.getenv('LINKEDIN_ORGANIZATION_URN')

    if not all([access_token, author_urn]):
        print("Fejl: Kunne ikke finde LinkedIn API-nøgler i Environment Variables.")
        print("Tjek din Run/Debug Configuration i PyCharm.")
        return

    api_url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0'
    }
    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": content
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    print("\n--- Forsøger at poste følgende til LinkedIn ---")
    print(content)
    print("---------------------------------------------")

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()  # Kaster en fejl for HTTP-fejlkoder (4xx eller 5xx)
        print("\nSUCCESS! Opslaget blev publiceret på LinkedIn.")
        print(f"Response: {response.json()}")
    except requests.exceptions.HTTPError as err:
        print(f"\nFEJL ved publicering til LinkedIn: {err.response.status_code} - {err.response.text}")
    except Exception as e:
        print(f"\nEn uventet fejl opstod: {e}")
        traceback.print_exc()


# Hoved-blokken der kører, når du starter scriptet
if __name__ == "__main__":
    # Vi opretter en app-kontekst, så vores script har adgang til de samme
    # konfigurationer og services som resten af din Flask-app.
    app = create_app()
    with app.app_context():
        # Vælg hvilken type post, du vil teste. "daily_post" er standard.
        post_type_arg = sys.argv[1] if len(sys.argv) > 1 else "daily_post"
        print(f"Starter test-run for post-type: {post_type_arg}")

        generated_content = generate_content(post_type_arg)

        if generated_content:
            post_to_linkedin(generated_content)
        else:
            print("Processen stoppet, da der ikke blev genereret indhold.")