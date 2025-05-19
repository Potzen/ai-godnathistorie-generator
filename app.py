# === Importer nødvendige biblioteker ===
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, Response # Tilføjet Response
import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
# *** Database og Login Imports ***
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
# *** Google OAuth Imports ***
from authlib.integrations.flask_client import OAuth
# *** NYT: ElevenLabs Import ***
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings # play bruges ikke direkte her
# *** ------------------------- ***
import traceback
import secrets

import base64

# Vertex AI imports
from google.cloud import aiplatform # Til aiplatform.init()
import vertexai # <--- TILFØJET
# from vertexai.language_models import ImageGenerationModel # <--- TILFØJET/ÆNDRET

# from vertexai.preview.generative_models import ImageGenerationModel
# Eller hvis ovenstående ikke virker (afhængigt af SDK version), prøv:
# from vertexai.generative_models import ImageGenerationModel
from vertexai.preview.vision_models import ImageGenerationModel

try:
    print("--- Inspicerer vertexai.language_models ---")
    # Først, sørg for at vertexai er initialiseret, så language_models er tilgængeligt
    # Dette sker senere globalt, men for denne test kan vi prøve her også,
    # hvis den globale init ikke er nået endnu når modulet loades.
    # Det er dog bedre at stole på den globale init.
    # import os
    # GOOGLE_CLOUD_PROJECT_ID_INSPECT = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
    # VERTEX_AI_REGION_INSPECT = os.getenv('VERTEX_AI_REGION', 'us-central1')
    # if GOOGLE_CLOUD_PROJECT_ID_INSPECT:
    #     aiplatform.init(project=GOOGLE_CLOUD_PROJECT_ID_INSPECT, location=VERTEX_AI_REGION_INSPECT)
    #     vertexai.init(project=GOOGLE_CLOUD_PROJECT_ID_INSPECT, location=VERTEX_AI_REGION_INSPECT)

    import vertexai.language_models
    print(f"Attributter i vertexai.language_models: {dir(vertexai.language_models)}")
    # print("\n--- Medlemmer af vertexai.language_models (via inspect) ---")
    # for name, obj in inspect.getmembers(vertexai.language_models):
    #     if not name.startswith('_'): # Undgå interne attributter
    #         print(f"{name}: {obj}")
except ImportError as ie:
    print(f"Kunne ikke importere vertexai.language_models for inspektion: {ie}")
except Exception as e_inspect:
    print(f"Anden fejl under inspektion: {e_inspect}")

# === Konfiguration af API Nøgler og Hemmeligheder ===
# Google AI (Gemini) - Læses fra miljø/WSGI
google_api_key = os.getenv("GOOGLE_API_KEY")
# Google OAuth Klient ID og Hemmelighed - Læses fra miljø/WSGI
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
# *** NYT: ElevenLabs API Nøgle ***
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

# Tjek og konfigurer Google Gemini
if not google_api_key:
    raise ValueError("Ingen GOOGLE_API_KEY fundet. Sæt den via WSGI fil (Plan B) eller Environment Variables på Web-fanen.")
else:
    genai.configure(api_key=google_api_key)
    print("Google AI API Key configured successfully.")

# Tjek Google OAuth credentials
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
     print("ADVARSEL: GOOGLE_CLIENT_ID eller GOOGLE_CLIENT_SECRET mangler i miljøet!")
     # Login vil fejle uden disse.

# *** NYT: Initialiser ElevenLabs klient (hvis nøgle findes) ***
elevenlabs_client = None
if not ELEVENLABS_API_KEY:
    print("ADVARSEL: ELEVENLABS_API_KEY mangler! Oplæsning vil ikke virke.")
else:
    try:
        # Initialiser klienten med API-nøglen
        elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        print("ElevenLabs Client Initialized.")
    except Exception as e:
        # Log fejlen hvis initialisering fejler (f.eks. ugyldig nøgle)
        print(f"FEJL ved initialisering af ElevenLabs client: {e}")
        print(traceback.format_exc())

# === Konfiguration for Vertex AI ===
GOOGLE_CLOUD_PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT_ID') # Sørg for at denne miljøvariabel er sat!
VERTEX_AI_REGION = os.getenv('VERTEX_AI_REGION', 'us-central1') # Default til us-central1, eller sæt via miljøvariabel
vertexai.init(project=GOOGLE_CLOUD_PROJECT_ID, location=VERTEX_AI_REGION)

if not GOOGLE_CLOUD_PROJECT_ID:
    print("ADVARSEL: GOOGLE_CLOUD_PROJECT_ID mangler i miljøet! Vertex AI kald vil fejle.")
else:
    try:
        aiplatform.init(project=GOOGLE_CLOUD_PROJECT_ID, location=VERTEX_AI_REGION)
        print(f"Vertex AI Initialized (aiplatform & vertexai). Project: {GOOGLE_CLOUD_PROJECT_ID}, Region: {VERTEX_AI_REGION}")
    except Exception as e:
        print(f"FEJL ved initialisering af Vertex AI: {e}")
        print(traceback.format_exc())

# === Opret Flask App ===
app = Flask(__name__)

# === App Konfiguration ===
# Hemmelig nøgle (meget vigtig for sessionssikkerhed)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(24))
print(f"Using SECRET_KEY (length): {len(app.config['SECRET_KEY'])}")

# Database konfiguration (SQLite)
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
if not os.path.exists(instance_path):
    try:
        os.makedirs(instance_path)
        print(f"Created directory: {instance_path}")
    except OSError as e:
        print(f"Error creating instance directory: {e}")
db_path = os.path.join(instance_path, 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Google OAuth Konfiguration til Authlib
app.config['GOOGLE_CLIENT_ID'] = GOOGLE_CLIENT_ID
app.config['GOOGLE_CLIENT_SECRET'] = GOOGLE_CLIENT_SECRET
# Bruger OpenID Connect discovery for at finde Googles endpoints automatisk
app.config['GOOGLE_DISCOVERY_URL'] = "https://accounts.google.com/.well-known/openid-configuration"

# === Initialiser Udvidelser ===
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'google_login' # Funktionens navn for login-ruten
login_manager.login_message = "Log venligst ind for at bruge denne funktion."
login_manager.login_message_category = "info" # Til flash beskeder

# Initialiser OAuth
oauth = OAuth(app)
# Registrer Google provider
# Tjekker om Client ID/Secret er sat før registrering
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url=app.config.get("GOOGLE_DISCOVERY_URL"),
        client_kwargs={
            'scope': 'openid email profile' # Standard scopes for brugerinfo
        }
    )
    print("OAuth Google provider registered.")
else:
    print("OAuth Google provider NOT registered due to missing credentials.")


# === Database Model (User) ===
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # Vores interne ID
    google_id = db.Column(db.String(100), unique=True, nullable=False) # Googles ID
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    # elevenlabs_voice_id = db.Column(db.String(50), nullable=True)
    # subscription_status = db.Column(db.String(20), default='inactive')

    def __repr__(self):
        return f'<User id={self.id} name={self.name} email={self.email}>'

# === User Loader Funktion ===
@login_manager.user_loader
def load_user(user_id):
    # Henter bruger fra DB baseret på VORES id gemt i session
    try:
        user = db.session.get(User, int(user_id))
        return user
    except Exception as e:
        print(f"Error loading user {user_id}: {e}")
        return None

# === Routes (URL stier) ===

@app.route('/')
def index():
    """ Viser hovedsiden. Sender brugerinfo med til templaten via current_user. """
    print(f"Accessing index route. User authenticated: {current_user.is_authenticated}")
    # Flask-Login gør current_user tilgængelig i Jinja2 templates automatisk
    return render_template('index.html')

# ===Route for Privatlivspolitik ===
@app.route('/privacy-policy')
def privacy_policy():
    """ Viser siden med privatlivs- og cookiepolitik. """
    print("Accessing privacy policy route.")
    return render_template('privacy_policy.html')


# --- Route for historie-generering ('/generate') ---
@app.route('/generate', methods=['POST'])
def generate_story():
    """ Modtager brugerinput, bygger prompt, kalder Gemini, parser titel og historie, og returnerer begge. """
    data = request.get_json()
    if not data:
        return jsonify(title="Fejl", story="Ingen data modtaget."), 400 # Returner også en titel ved fejl
    print("Modtaget data for /generate:", data)

    # Hent alle inputs
    karakterer_data = data.get('karakterer')
    steder_liste = data.get('steder')
    plots_liste = data.get('plots')
    laengde = data.get('laengde', 'kort')
    mood = data.get('mood', 'neutral')
    listeners = data.get('listeners', [])
    # is_interactive var fjernet fra frontend, så vi sætter den til False her, medmindre den kommer med
    is_interactive = data.get('interactive', False)
    negative_prompt_text = data.get('negative_prompt', '').strip()
    print(f"Valgt længde: {laengde}, Valgt stemning: {mood}, Lyttere: {listeners}, Interaktiv: {is_interactive}, Negativ Prompt: '{negative_prompt_text}'")

    # Forbered grundlæggende strenge
    karakter_descriptions_for_prompt = []
    if karakterer_data:
        for char_obj in karakterer_data:
            desc = char_obj.get('description','').strip()
            name = char_obj.get('name','').strip()
            if desc: karakter_descriptions_for_prompt.append(f"{desc} ved navn {name}" if name else desc)
    karakter_str = ", ".join(karakter_descriptions_for_prompt) if karakter_descriptions_for_prompt else "en uspecificeret karakter" # Undgå tom streng

    valid_steder = []
    if steder_liste: valid_steder = [s.strip() for s in steder_liste if s and s.strip()]
    sted_str = ", ".join(valid_steder) if valid_steder else "et uspecificeret sted" # Undgå tom streng

    valid_plots = []
    if plots_liste: valid_plots = [p.strip() for p in plots_liste if p and p.strip()]
    plot_str = ", ".join(valid_plots) if valid_plots else "et uspecificeret eventyr" # Undgå tom streng

    print(f"Input til historie (behandlet): Karakterer='{karakter_str}', Steder='{sted_str}', Plot/Morale='{plot_str}'")

    # Definer Længde-instruktion og max_tokens
    length_instruction = ""
    max_tokens_setting = 1000 # Default for 'kort'
    if laengde == 'mellem':
        length_instruction = "Skriv historien i cirka 10-14 sammenhængende afsnit. Den skal føles som en mellemlang historie."
        max_tokens_setting = 3000
    elif laengde == 'lang':
        length_instruction = "Skriv en **meget lang og detaljeret historie** på **mindst 15 fyldige afsnit**, gerne flere. Sørg for en dybdegående fortælling."
        # Bemærk: Gemini 1.5 Flash har en context window, men output tokens kan stadig være en begrænsning.
        # For "meget lang" kan det være nødvendigt at justere forventningerne eller bruge en model med større output kapacitet, hvis Flash er for begrænset.
        max_tokens_setting = 7000 # Justeret lidt ned fra 8000 for en sikkerheds skyld ift. Flash model
    else: # kort
        length_instruction = "Skriv historien i cirka 6-8 korte, sammenhængende afsnit."
        max_tokens_setting = 1500 # Lidt mere plads til 'kort'

    print(f"Længde instruktion: {length_instruction}, Max Tokens: {max_tokens_setting}")

    # Definer stemnings-instruktion
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
    print(f"Stemnings instruktion (til prompt): {mood_prompt_part}")

    # Byg Lytter Kontekst og Afslutnings-instruktion (uændret fra din kode)
    listener_context_instruction = ""
    names_list_for_ending = []
    # ... (din eksisterende logik for listener_context_instruction og ending_instruction) ...
    # For at gøre det kort, indsætter jeg en placeholder her - brug din eksisterende kode for lyttere.
    if listeners:
        listener_descriptions = []
        ages = [] # Gem aldre for evt. tilpasning
        for listener in listeners:
            name = listener.get('name','').strip()
            age_str = listener.get('age','').strip()
            desc = name if name else 'et barn'
            if age_str:
                desc += f" på {age_str} år"
                ages.append(age_str)
            if name:
                names_list_for_ending.append(name)
            listener_descriptions.append(desc)

        if listener_descriptions:
            listener_context_instruction = f"INFO OM LYTTEREN(E): Historien læses højt for {', '.join(listener_descriptions[:-1])}{' og ' if len(listener_descriptions) > 1 else ''}{listener_descriptions[-1] if listener_descriptions else 'et barn'}."
            # Tilføj evt. mere kontekst baseret på alder her, hvis du ønsker
            listener_context_instruction += " Tilpas sprog og temaer, så de er passende og engagerende for denne/disse lytter(e)."

    ending_instruction = "VIGTIGT OM AFSLUTNINGEN: Afslut historien på en positiv og tryg måde, der er passende for en godnathistorie. Henvend dig IKKE direkte til lytteren midt i historien."
    if names_list_for_ending:
        ending_instruction = (f"VIGTIGT OM AFSLUTNINGEN: Afslut historien på en positiv og tryg måde. "
                              f"Som en ALLER SIDSTE sætning i historien, efter selve handlingen er afsluttet, sig 'Sov godt, {', '.join(names_list_for_ending[:-1])}{' og ' if len(names_list_for_ending) > 1 else ''}{names_list_for_ending[-1] if names_list_for_ending else 'lille ven'}! Drøm sødt.' "
                              f"Denne afslutning skal KUN være den sidste sætning. Henvend dig IKKE direkte til lytteren midt i historien.")


    # Definer safety_settings og generation_config (uændret)
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }
    generation_config = genai.types.GenerationConfig(
        max_output_tokens=max_tokens_setting,
        temperature=0.7 # Du kan justere temperaturen for mere/mindre kreativitet
    )

    # === JUSTERING AF PROMPT FOR TITEL ===
    prompt_parts = []
    prompt_parts.append("SYSTEM INSTRUKTION: Du er en kreativ AI, der er ekspert i at skrive godnathistorier for børn.")
    prompt_parts.append("OPGAVE: Skriv en godnathistorie baseret på følgende input. Historien skal være engagerende, passende for målgruppen og have en klar begyndelse, midte og slutning.")

    # NY INSTRUKTION FOR TITEL
    prompt_parts.append("FØRST, generer en kort og fængende titel til historien. Skriv KUN titlen på den allerførste linje af dit output. Efter titlen, indsæt ET ENKELT LINJESKIFT (ikke dobbelt), og start derefter selve historien.")
    prompt_parts.append("---") # Separator for klarhed

    if listener_context_instruction:
        prompt_parts.append(listener_context_instruction)

    prompt_parts.append(f"Længdeønske: {length_instruction}")
    prompt_parts.append(f"Stemning: {mood_prompt_part}")

    if karakter_str: prompt_parts.append(f"Hovedperson(er): {karakter_str}")
    if sted_str: prompt_parts.append(f"Sted(er): {sted_str}")
    if plot_str: prompt_parts.append(f"Plot/Elementer/Morale: {plot_str}")

    # Interaktiv mode er fjernet fra UI, men koden er her hvis det genaktiveres
    if is_interactive:
        interactive_rules = (
            "REGLER FOR INDDRAGENDE EVENTYR MED EKSPLICITTE VALG-STIER:\n"
            "- Historien skal indeholde mindst TO (2) steder, hvor lytteren gives et KLART valg mellem TO (2) muligheder (A eller B) for handlingens videre forløb.\n"
            "- Hvert valg skal præsenteres tydeligt, f.eks.: 'Skal [karakter] nu A) [mulighed A] eller B) [mulighed B]?'\n"
            "- EFTER hvert valgpunkt, skriv KUN den sti, der følger fra VALG A. Marker starten på denne sti med 'STI A:'.\n"
            "- Umiddelbart EFTER STI A er færdig, skriv KUN den sti, der følger fra VALG B. Marker starten på denne sti med 'STI B:'.\n"
            "- Sørg for at STI A og STI B er klart adskilte og hver især udgør en meningsfuld fortsættelse.\n"
            "- EFTER den sidste STI B (for det sidste valgpunkt) er færdig, skriv en GENERISK SAMMENFATTENDE AFSLUTNING på historien, der IKKE afhænger af de specifikke valg, der er taget. Denne afslutning skal opsummere eventyret på en generel måde og give en følelse af afslutning, uanset hvilke stier lytteren ville have valgt."
        )
        prompt_parts.append(f"\n{interactive_rules}")

    prompt_parts.append("\nGENERELLE REGLER FOR HISTORIEN:")
    prompt_parts.append("- Undgå komplekse sætninger og ord. Sproget skal være letforståeligt for børn.")
    prompt_parts.append("- Inkluder gerne gentagelser, rim eller lydeffekter, hvis det passer til historien.")
    prompt_parts.append("- Sørg for en positiv morale eller et opløftende budskab, hvis det er relevant for plottet.")
    prompt_parts.append("- Undgå vold, upassende temaer eller noget, der kan give mareridt.")

    if negative_prompt_text:
        prompt_parts.append(f"- VIGTIGT: Følgende elementer må IKKE indgå i historien: {negative_prompt_text}")

    prompt_parts.append(f"- {ending_instruction}") # Afslutningsinstruktion
    prompt_parts.append("---")
    prompt_parts.append("Start outputtet med TITLEN på første linje, efterfulgt af ET ENKELT LINJESKIFT, og derefter selve historien:")

    prompt = "\n".join(prompt_parts)
    print(f"--- Sender FULD Prompt til Gemini (Max Tokens: {max_tokens_setting}) ---\n{prompt}\n------------------------------")

    # API Kald og Respons Håndtering
    story_title = "Uden Titel" # Default hvis intet findes
    actual_story_content = "Der opstod en fejl under historiegenerering." # Default

    try:
        print("Initialiserer Gemini model...")
        # Brug den model, der er konfigureret. Gemini 1.5 Flash er typisk 'gemini-1.5-flash-latest'.
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        print(f"Bruger model: gemini-1.5-flash-latest") # Eller hvad din model nu hedder

        print("Sender anmodning til Google Gemini...")
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings,
            # request_options={"timeout": 100} # Overvej timeout hvis kald tager for lang tid
        )
        print("Svar modtaget fra Google Gemini.")

        # === NY PARSING AF TITEL OG HISTORIE ===
        raw_text_from_gemini = ""
        try:
            raw_text_from_gemini = response.text
            # Split ved det første linjeskift. Alt før er titel, alt efter er historie.
            parts = raw_text_from_gemini.split('\n', 1)
            if len(parts) >= 1 and parts[0].strip(): # Sørg for at der er en titel
                story_title = parts[0].strip()
                if len(parts) > 1 and parts[1].strip(): # Sørg for at der er en historie
                    actual_story_content = parts[1].strip()
                elif not parts[0].strip() and len(parts) > 1 and parts[1].strip(): # Hvis første linje er tom, men der er en historie
                    story_title = "Uden Titel (Genereret)" # Sæt en default titel
                    actual_story_content = parts[1].strip()
                elif parts[0].strip() and (len(parts) == 1 or not parts[1].strip()): # Der er en titel, men ingen efterfølgende historie
                    actual_story_content = "Historien mangler efter titlen."
                    print(f"Kunne kun parse titel, historien mangler. Råtekst: {raw_text_from_gemini[:200]}")
                else: # Kunne ikke parse meningsfuldt, brug råtekst
                    story_title = "Uden Titel (Parse Fejl)"
                    actual_story_content = raw_text_from_gemini
                    print(f"Kunne ikke parse titel og historie optimalt. Råtekst: {raw_text_from_gemini[:200]}")

            else: # Ingen linjeskift fundet, eller første linje er tom - antag det hele er historie (eller fejl)
                story_title = "Uden Titel (Intet Linjeskift)"
                actual_story_content = raw_text_from_gemini.strip() if raw_text_from_gemini.strip() else "Modtog tomt svar fra AI."
                print(f"Ingen linjeskift fundet til at adskille titel. Råtekst: {raw_text_from_gemini[:200]}")

        except ValueError as e: # Typisk safety filter
             print(f"Svar blokeret af sikkerhedsfilter eller problem med response.text: {e}")
             print(f"Prompt Feedback: {response.prompt_feedback if response and hasattr(response, 'prompt_feedback') else 'Ingen prompt feedback tilgængelig.'}")
             story_title = "Blokeret Indhold"
             actual_story_content = "Beklager, historien kunne ikke laves, da den eller dele af den blev blokeret af indholdsfiltre. Prøv at justere dine input."
        except Exception as e_parse: # Andre fejl under .text adgang eller parsing
            print(f"Fejl under adgang til response.text eller parsing: {e_parse}")
            print(traceback.format_exc())
            story_title = "Parse Fejl"
            actual_story_content = "Der opstod en fejl under behandling af svaret fra AI."
            # Prøv at se om der er kandidater, hvis .text fejlede direkte
            if response and response.candidates:
                try:
                    actual_story_content = response.candidates[0].content.parts[0].text
                    # Prøv igen at parse titel herfra, hvis det er relevant
                    parts = actual_story_content.split('\n', 1)
                    if len(parts) >= 1 and parts[0].strip():
                        story_title = parts[0].strip()
                        actual_story_content = parts[1].strip() if len(parts) > 1 and parts[1].strip() else "Historien mangler efter titlen."
                    print("Fallback til parsing fra response.candidates succesfuld (delvist).")
                except Exception as e_candidate:
                    print(f"Kunne heller ikke hente indhold fra response.candidates: {e_candidate}")


    except Exception as e_api: # Generel API kaldsfejl
        print(f"Fejl ved kald til Google Gemini API: {e_api}")
        print(traceback.format_exc())
        story_title = "API Fejl"
        actual_story_content = f"Beklager, jeg kunne ikke lave en historie lige nu på grund af en teknisk fejl med AI-tjenesten. Prøv venligst igen senere."

    # Sikrer at vi altid har en streng, selv hvis noget gik helt galt
    if not isinstance(story_title, str): story_title = "Uden Titel (Intern Fejl)"
    if not isinstance(actual_story_content, str): actual_story_content = "Indhold mangler (Intern Fejl)"

    print(f"Returnerer titel: '{story_title}'")
    # print(f"Returnerer historie (start): '{actual_story_content[:100]}...'") # Undlad at printe hele historien i log

    return jsonify(title=story_title, story=actual_story_content)

# === LOGIN/LOGOUT ROUTES ===

@app.route('/login')
def google_login():
    """ Starter Google login flowet. """
    if 'google' not in oauth._registry:
        flash("Google login er ikke konfigureret korrekt på serveren.", "error")
        return redirect(url_for('index'))
    redirect_uri = url_for('google_authorize', _external=True)
    print(f"Redirecting to Google for login. Callback URI: {redirect_uri}")
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def google_authorize():
    """ Håndterer tilbagekaldet fra Google. """
    print("Received callback from Google.")
    if 'google' not in oauth._registry:
        flash("Google login er ikke konfigureret korrekt på serveren.", "error")
        return redirect(url_for('index'))
    try:
        token = oauth.google.authorize_access_token()
        if not token:
            print("Failed to authorize access token."); flash("Login mislykkedes (token).", "error"); return redirect(url_for('index'))
        print("Access token received. Fetching user info...")
        user_info = oauth.google.userinfo(token=token)
        if not user_info:
             print("Could not fetch user info."); flash("Login mislykkedes (userinfo).", "error"); return redirect(url_for('index'))

        print(f"User info received: {user_info}")
        google_user_id = user_info.get('sub')
        user_email = user_info.get('email')
        user_name = user_info.get('name')

        if not google_user_id:
             print("Google user ID ('sub') not found."); flash("Login mislykkedes (ID).", "error"); return redirect(url_for('index'))

        # Find eller Opret Bruger i DB
        user = User.query.filter_by(google_id=google_user_id).first()
        if user: # Eksisterende bruger
            print(f"Existing user found: {user}")
            needs_commit = False
            if user.name != user_name: user.name = user_name; needs_commit = True
            if user.email != user_email:
                 existing_email = User.query.filter_by(email=user_email).first()
                 if not existing_email or existing_email.google_id == google_user_id:
                     user.email = user_email; needs_commit = True
                 else: print(f"Warning: Email {user_email} already exists...")
            if needs_commit:
                try: db.session.commit(); print("User info updated.")
                except Exception as e: db.session.rollback(); print(f"Error updating user info: {e}")
        else: # Ny bruger
            print(f"New user detected. Creating user...")
            user = User(google_id=google_user_id, name=user_name, email=user_email)
            db.session.add(user)
            try: db.session.commit(); print(f"New user created: {user}")
            except Exception as e:
                db.session.rollback(); print(f"Error committing new user: {e}"); print(traceback.format_exc())
                flash("Fejl: Kunne ikke oprette bruger.", "error"); return redirect(url_for('index'))

        # Log brugeren ind
        login_user(user, remember=True)
        print(f"User {user.id} logged in successfully.")
        flash(f"Velkommen, {user.name}!", "success")
        return redirect(url_for('index')) # Tilbage til forsiden

    except Exception as e:
        print(f"Error during Google authorization: {e}"); print(traceback.format_exc())
        flash(f"Der opstod en uventet fejl under login: {e}", "error")
        return redirect(url_for('index'))


@app.route('/logout')
@login_required
def logout():
    """ Logger brugeren ud. """
    user_id_before = current_user.id if current_user.is_authenticated else 'anonymous'
    logout_user()
    session.clear()
    print(f"User {user_id_before} logged out.")
    flash("Du er nu logget ud.", "info")
    return redirect(url_for('index'))


# === *** NY ROUTE: Generer Lyd med ElevenLabs *** ===
@app.route('/generate_audio', methods=['POST'])
# @login_required # <-- TILFØJ DENNE LINJE SENERE for at kræve login/betaling
def generate_audio():
    """ Modtager tekst og returnerer MP3 lyd genereret af ElevenLabs. """
    # Tjek om klienten blev initialiseret korrekt ved opstart
    if not elevenlabs_client:
        print("ERROR: ElevenLabs client not initialized in generate_audio.")
        return jsonify({"error": "ElevenLabs client not initialized. Check API key setup."}), 500

    data = request.get_json()
    story_text = data.get('text')

    if not story_text:
        print("ERROR: No text provided for audio generation.")
        return jsonify({"error": "No text provided for audio generation."}), 400

    print(f"Received request to generate audio for text starting with: {story_text[:50]}...")

    try:
        # --- Vælg Stemme ---
        # Brug et specifikt Voice ID fra din ElevenLabs konto.
        # Find ID'et på deres hjemmeside under "Voices" -> "Voice Lab".
        # Erstat 'YOUR_CHOSEN_VOICE_ID' med det faktiske ID.
        # Populære pre-made stemmer har også navne som 'Rachel', 'Adam', 'Antoni' osv.
        # voice_id = "gpf7HQVro4L2OVR54kr8" # Eksempel: ID for "Rachel" (kan ændre sig!)
        voice_id = "gpf7HQVro4L2OVR54kr8" # Brug navnet på en pre-made stemme til test

        # Senere: Hvis brugeren har en gemt klonet stemme:
        # if current_user.is_authenticated and hasattr(current_user, 'elevenlabs_voice_id') and current_user.elevenlabs_voice_id:
        #    voice_id = current_user.elevenlabs_voice_id
        #    print(f"Using custom voice ID for user {current_user.id}: {voice_id}")
        # else:
        #    print(f"Using default voice: {voice_id}")

        print(f"Requesting audio from ElevenLabs using voice: {voice_id}")
        # Generer lyden - dette returnerer en iterator af bytes
        audio_stream = elevenlabs_client.generate(
            text=story_text,
            voice=Voice(
                 voice_id=voice_id,
                 # settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True) # Valgfri finjustering
                 ),
            model='eleven_multilingual_v2' # Vælg model
        )

        print("Audio stream received from ElevenLabs.")

        # Stream lyden direkte tilbage til browseren
        # Sæt den korrekte MIME type for MP3 lyd
        return Response(audio_stream, mimetype='audio/mpeg')

    except Exception as e:
        # Log den fulde fejl for bedre debugging
        print(f"Error calling ElevenLabs API: {e}")
        print(traceback.format_exc())
        # Returner en JSON fejlbesked, så frontend kan vise noget
        return jsonify({"error": f"Fejl ved generering af lyd: {e}"}), 500

# === --------------------------------------- ===

# === NY ROUTE: Billedgenerering ===
@app.route('/generate_image_from_story', methods=['POST'])
# @login_required # Midlertidigt fjernet for nemmere test, kan genaktiveres
def generate_image_from_story():
    """
    Modtager historietekst, genererer en billedprompt, genererer et billede,
    og returnerer billedet som en base64 data URL.
    """
    data = request.get_json()
    if not data or 'story_text' not in data:
        return jsonify({"error": "Mangler 'story_text' i anmodningen."}), 400

    story_text = data.get('story_text')
    if not story_text.strip():
        return jsonify({"error": "'story_text' må ikke være tom."}), 400

    print(f"Modtaget anmodning til /generate_image_from_story. Historielængde: {len(story_text)}")

    # --- Step 1: Generer en billedprompt fra historieteksten vha. Gemini ---
    generated_image_prompt_text = "En illustration af en scene fra historien." # Fallback
    try:
        print("Genererer billedprompt med Gemini...")
        # Du kan genbruge din eksisterende Gemini model initialisering, hvis den er global
        # ellers initialiser den her:

        gemini_model_for_prompting = genai.GenerativeModel('gemini-1.5-flash-latest') # Eller den model du foretrækker

        prompt_for_image_prompt = (
            f"Opgave: Baseret på følgende danske historie, skal du skrive en **meget specifik og detaljeret visuel prompt på ENGELSK** (ca. 40-70 ord). "
            f"Denne engelske prompt skal bruges af AI billedgeneratoren Vertex AI Imagen og skal følge Googles bedste praksis for Imagen-prompts.\n\n"
            f"VIGTIGE INSTRUKTIONER TIL DEN **ENGELSKE** VISUELLE PROMPT, DU (GEMINI) SKAL GENERERE:\n"
            f"1.  **Hovedmotiv Først (Subject First & Clear):** Start ALTID med en klar **engelsk** beskrivelse af hovedperson(er), dyr eller centrale objekter. Vær bogstavelig for at undgå fejlfortolkning.\n"
            f"2.  **Handling og Interaktion (Action & Interaction):** Beskriv tydeligt på **engelsk**, hvad subjekt(erne) gør, og hvordan de interagerer.\n"
            f"3.  **Omgivelser og Baggrund (Setting & Background):** Beskriv Detaljer stedet/baggrunden på **engelsk**. Inkluder vigtige elementer fra historien, der definerer scenen.\n"
            f"4.  **Billedstil (Image Style - MEGET VIGTIGT - skal ligne en poleret 3D animationsfilm scene):\n"
            f"    - Den **engelske** prompt skal ALTID afsluttes med en præcis stilbeskrivelse. Oversæt og brug følgende kerneelementer i din **engelske** stilbeskrivelse: "
            f"'Style: Child-friendly high-quality 3D digital illustration, fairytale-like and imaginative.'\n"
            f"6.  **Klarhed og Orden (Clarity & Order):** Strukturen i den **engelske** prompt du genererer bør generelt være: Subject(s) -> Action -> Setting/Details -> Style.\n"
            f"7.  **Undgå (Avoid):** Ingen tekst i billedet.\n\n"
            f"DANSK HISTORIE (læs denne for at forstå indholdet, som du så skal basere den engelske billedprompt på):\n{story_text[:2000]}\n\n"
            f"GENERER DEN DETALJEREDE OG SPECIFIKKE **ENGELSKE** VISUELLE PROMPT TIL VERTEX AI IMAGEN NU (følg alle ovenstående instruktioner nøje):"
        )

        response_gemini = gemini_model_for_prompting.generate_content(prompt_for_image_prompt)
        generated_image_prompt_text = response_gemini.text.strip()
        print(f"Genereret billedprompt: {generated_image_prompt_text}")

    except Exception as e_gemini_prompt:
        print(f"Fejl under generering af billedprompt med Gemini: {e_gemini_prompt}")
        # Fortsæt med fallback prompten, eller returner fejl her hvis kritisk
        # return jsonify({"error": f"Kunne ikke generere billedprompt: {e_gemini_prompt}"}), 500

    # --- Step 2: Generer billede med Vertex AI Imagen ---
    if not GOOGLE_CLOUD_PROJECT_ID: # Tjek igen før API kald
        print("FEJL: GOOGLE_CLOUD_PROJECT_ID er ikke sat. Kan ikke kalde Vertex AI.")
        return jsonify({"error": "Serverkonfigurationsfejl: Projekt ID mangler for billedgenerering."}), 500

    try:
        print(f"Genererer billede med Vertex AI Imagen. Prompt: {generated_image_prompt_text}")

        # Definer den ønskede Imagen 3 model

        model_identifier_imagen3 = "imagen-3.0-generate-002"
        print(f"Forsøger at bruge Imagen model: {model_identifier_imagen3}")

        try:
            model = ImageGenerationModel.from_pretrained(model_identifier_imagen3)
            print(f"Succesfuldt loaded Imagen model: {model_identifier_imagen3}")
        except Exception as e:
            print(f"FEJL: Kunne ikke loade modellen '{model_identifier_imagen3}'. Fejl: {e}")
            print(
                "Falder tilbage til den oprindelige model 'imagegeneration@006' eller stopper, afhængigt af din ønskede fejlhåndtering.")
            # Du kan vælge at falde tilbage eller kaste en fejl her:
            # model = ImageGenerationModel.from_pretrained("imagegeneration@006") # Fallback-mulighed
            raise ValueError(
                f"Kunne ikke initialisere den specificerede Imagen 3 model: {model_identifier_imagen3}. Tjek tilgængelighed og modelnavn.") from e

        # Generer billeder
        response_imagen = model.generate_images(
            prompt=generated_image_prompt_text,
            number_of_images=1,
            guidance_scale=30,
            # Du kan tilføje flere parametre her hvis nødvendigt:
            # seed=12345,
            # aspect_ratio="1:1", # f.eks. "1:1", "16:9", "9:16"
            # guidance_scale=7,
            # negative_prompt="dårlig kvalitet, tekst, vandmærke",
        )

        # ... (kode før dette, inklusiv response_imagen = model.generate_images(...))

        # Først, tjek om 'images' listen overhovedet er der og har elementer
        if not response_imagen or not response_imagen.images:  # Tjekker om listen er tom eller None
            print("FEJL: Vertex AI Imagen returnerede et svar uden en 'images' liste eller en tom 'images' liste.")
            print(f"Streng repræsentation af Fuld Imagen response: {response_imagen}")  # Den du havde

            # === NYT TILFØJET HER FOR AT INSPEKTERE response_imagen OBJEKTET ===
            print(f"Attributter og metoder på response_imagen (dir): {dir(response_imagen)}")
            try:
                print(f"Værdier af attributter på response_imagen (vars): {vars(response_imagen)}")
            except TypeError:
                print("Kunne ikke køre vars() på response_imagen objektet direkte.")

            # Tjek om der er en generel 'error' eller 'status' eller 'reason' attribut på selve response_imagen
            if hasattr(response_imagen, 'error'):
                print(f"response_imagen.error: {response_imagen.error}")
            if hasattr(response_imagen, 'status_message'):  # Navne kan variere
                print(f"response_imagen.status_message: {response_imagen.status_message}")
            if hasattr(response_imagen, 'generation_metadata'):  # Eller lignende
                print(f"response_imagen.generation_metadata: {response_imagen.generation_metadata}")
            # =======================================================================

            raise ValueError(
                "Vertex AI Imagen returnerede et uventet svar (ingen billedliste). Tjek logs for response_imagen detaljer.")

        # Nu ved vi, at response_imagen.images er en liste og ikke er tom.
        # Tag fat i det første (og eneste, da number_of_images=1) billedeobjekt.
        image_obj = response_imagen.images[0]
        # ... (resten af koden for at tjekke image_obj, som kun køres hvis images listen IKKE er tom)

        # Tjek for billedbytes og log detaljer, hvis de mangler
        if not hasattr(image_obj, '_image_bytes') or not image_obj._image_bytes:
            print("FEJL: _image_bytes mangler eller er tom i det returnerede billedeobjekt.")
            # Log alle attributter af image_obj for at se, hvad API'et returnerede
            try:
                print(f"Detaljer om billedeobjektet (vars): {vars(image_obj)}")
            except TypeError:
                print(f"Kunne ikke køre vars() på image_obj. Objekt type: {type(image_obj)}")

            print(f"Detaljer om billedeobjektet (dir): {dir(image_obj)}")  # Viser alle metoder og attributter

            # Tjek specifikt for felter, der kan indikere årsagen
            if hasattr(image_obj, 'finish_reason'):  # Ofte brugt i generative modeller
                print(f"Billedeobjekt finish_reason: {image_obj.finish_reason}")
            if hasattr(image_obj,
                       'error_message'):  # Nogle API'er har et 'error' felt i responsen (tjek også for 'error')
                print(f"Billedeobjekt error_message: {image_obj.error_message}")
            if hasattr(image_obj, 'error') and image_obj.error:  # Tjek også for et 'error' objekt/dictionary
                print(f"Billedeobjekt error detaljer: {image_obj.error}")
            if hasattr(image_obj, 'status'):
                print(f"Billedeobjekt status: {image_obj.status}")
            # Du kan tilføje flere 'hasattr' tjek for andre potentielle felter baseret på outputtet fra dir(image_obj)

            raise ValueError(  # Din oprindelige fejl, men nu med mere kontekst i loggen
                "Vertex AI Imagen returnerede ikke gyldige billeddata. Tjek serverlogs for detaljer fra image_obj."
            )

        # Hvis vi når hertil, er _image_bytes til stede
        image_bytes = image_obj._image_bytes

        image_base64 = base64.b64encode(image_bytes).decode('utf-8')


        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        image_data_url = f"data:image/png;base64,{image_base64}"
        print("Billede genereret succesfuldt og konverteret til data URL.")

        return jsonify({
            "message": "Billede genereret!",
            "image_url": image_data_url,
            "image_prompt_used": generated_image_prompt_text
        })

    except Exception as e_vertex:
        print(f"Fejl under billedgenerering med Vertex AI Imagen: {e_vertex}")
        print(traceback.format_exc())
        error_message_to_user = f"Kunne ikke generere billede. Detaljer: {e_vertex}"
        if "permission denied" in str(e_vertex).lower() or "billing" in str(e_vertex).lower():
            error_message_to_user = "Billedgenerering fejlede pga. et problem med serverens adgangsrettigheder eller faktureringskonto. Kontakt administratoren."
        elif "quota" in str(e_vertex).lower():
            error_message_to_user = "Billedgenereringskvoten er opbrugt. Prøv igen senere."
        elif "does not exist or you do not have permission" in str(
                e_vertex).lower():  # Fejl hvis model ikke findes eller manglende rettigheder
            error_message_to_user = "Billedmodellen ('imagegeneration@006') kunne ikke tilgås. Kontroller modelnavn og dine tilladelser i Google Cloud."

        return jsonify({"error": error_message_to_user, "image_prompt_used": generated_image_prompt_text}), 500

# === Opret Database Tabeller ===
def create_tables():
    with app.app_context():
        print("Checking/Creating database tables...")
        try: db.create_all()
        except Exception as e: print(f"Error creating tables: {e}"); print(traceback.format_exc())
        else: print("Database tables checked/created successfully.")

# === Start Webserveren ===
if __name__ == '__main__':
    create_tables()
    # Sørg for at host er 0.0.0.0 hvis du vil tilgå fra andre enheder på dit lokale netværk
    # port=5000 er standard
    app.run(debug=True, port=5000)

