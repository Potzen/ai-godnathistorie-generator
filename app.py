import base64
# Vertex AI imports
from google.cloud import aiplatform  # Til aiplatform.init()
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
import time  # Tilføjet for genforsøg-pause
# === Importer nødvendige biblioteker ===
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, Response
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
from elevenlabs import Voice
# *** ------------------------- ***
import traceback
import secrets

try:
    print("--- Inspicerer vertexai.language_models ---")
    import vertexai.language_models

    print(f"Attributter i vertexai.language_models: {dir(vertexai.language_models)}")
except ImportError as ie:
    print(f"Kunne ikke importere vertexai.language_models for inspektion: {ie}")
except Exception as e_inspect:
    print(f"Anden fejl under inspektion: {e_inspect}")

# === Konfiguration af API Nøgler og Hemmeligheder ===
google_api_key = os.getenv("GOOGLE_API_KEY")
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

if not google_api_key:
    raise ValueError(
        "Ingen GOOGLE_API_KEY fundet. Sæt den via WSGI fil (Plan B) eller Environment Variables på Web-fanen.")
else:
    genai.configure(api_key=google_api_key)
    print("Google AI API Key configured successfully.")

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    print("ADVARSEL: GOOGLE_CLIENT_ID eller GOOGLE_CLIENT_SECRET mangler i miljøet!")

elevenlabs_client = None
if not ELEVENLABS_API_KEY:
    print("ADVARSEL: ELEVENLABS_API_KEY mangler! Oplæsning vil ikke virke.")
else:
    try:
        elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        print("ElevenLabs Client Initialized.")
    except Exception as e:
        print(f"FEJL ved initialisering af ElevenLabs client: {e}")
        print(traceback.format_exc())

# === Konfiguration for Vertex AI ===
GOOGLE_CLOUD_PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT_ID')
VERTEX_AI_REGION = os.getenv('VERTEX_AI_REGION', 'us-central1')
if GOOGLE_CLOUD_PROJECT_ID:  # Kun initialiser hvis ID er sat
    try:
        aiplatform.init(project=GOOGLE_CLOUD_PROJECT_ID, location=VERTEX_AI_REGION)
        vertexai.init(project=GOOGLE_CLOUD_PROJECT_ID, location=VERTEX_AI_REGION)
        print(
            f"Vertex AI Initialized (aiplatform & vertexai). Project: {GOOGLE_CLOUD_PROJECT_ID}, Region: {VERTEX_AI_REGION}")
    except Exception as e:
        print(f"FEJL ved initialisering af Vertex AI: {e}")
        print(traceback.format_exc())
else:
    print("ADVARSEL: GOOGLE_CLOUD_PROJECT_ID mangler i miljøet! Vertex AI kald (billedgenerering) vil fejle.")

# === Opret Flask App ===
app = Flask(__name__)

# === App Konfiguration ===
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(24))
print(f"Using SECRET_KEY (length): {len(app.config['SECRET_KEY'])}")

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

app.config['GOOGLE_CLIENT_ID'] = GOOGLE_CLIENT_ID
app.config['GOOGLE_CLIENT_SECRET'] = GOOGLE_CLIENT_SECRET
app.config['GOOGLE_DISCOVERY_URL'] = "https://accounts.google.com/.well-known/openid-configuration"

# === Initialiser Udvidelser ===
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'google_login'
login_manager.login_message = "Log venligst ind for at bruge denne funktion."
login_manager.login_message_category = "info"

oauth = OAuth(app)
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url=app.config.get("GOOGLE_DISCOVERY_URL"),
        client_kwargs={'scope': 'openid email profile'}
    )
    print("OAuth Google provider registered.")
else:
    print("OAuth Google provider NOT registered due to missing credentials.")


# === Database Model (User) ===
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)

    def __repr__(self):
        return f'<User id={self.id} name={self.name} email={self.email}>'


# === User Loader Funktion ===
@login_manager.user_loader
def load_user(user_id):
    try:
        user = db.session.get(User, int(user_id))
        return user
    except Exception as e:
        print(f"Error loading user {user_id}: {e}")
        return None


# === Routes (URL stier) ===
@app.route('/')
def index():
    print(f"Accessing index route. User authenticated: {current_user.is_authenticated}")
    return render_template('index.html')


@app.route('/privacy-policy')
def privacy_policy():
    print("Accessing privacy policy route.")
    return render_template('privacy_policy.html')


# --- Route for historie-generering ('/generate') ---
@app.route('/generate', methods=['POST'])
def generate_story():
    data = request.get_json()
    if not data:
        return jsonify(title="Fejl", story="Ingen data modtaget."), 400
    print("Modtaget data for /generate:", data)

    karakterer_data = data.get('karakterer')
    steder_liste = data.get('steder')
    plots_liste = data.get('plots')
    laengde = data.get('laengde', 'kort')
    mood = data.get('mood', 'neutral')
    listeners = data.get('listeners', [])
    is_interactive = data.get('interactive', False)
    negative_prompt_text = data.get('negative_prompt', '').strip()
    print(
        f"Valgt længde: {laengde}, Valgt stemning: {mood}, Lyttere: {listeners}, Interaktiv: {is_interactive}, Negativ Prompt: '{negative_prompt_text}'")

    karakter_descriptions_for_prompt = []
    if karakterer_data:
        for char_obj in karakterer_data:
            desc = char_obj.get('description', '').strip()
            name = char_obj.get('name', '').strip()
            if desc: karakter_descriptions_for_prompt.append(f"{desc} ved navn {name}" if name else desc)
    karakter_str = ", ".join(
        karakter_descriptions_for_prompt) if karakter_descriptions_for_prompt else "en uspecificeret karakter"

    valid_steder = []
    if steder_liste: valid_steder = [s.strip() for s in steder_liste if s and s.strip()]
    sted_str = ", ".join(valid_steder) if valid_steder else "et uspecificeret sted"

    valid_plots = []
    if plots_liste: valid_plots = [p.strip() for p in plots_liste if p and p.strip()]
    plot_str = ", ".join(valid_plots) if valid_plots else "et uspecificeret eventyr"

    print(f"Input til historie (behandlet): Karakterer='{karakter_str}', Steder='{sted_str}', Plot/Morale='{plot_str}'")

    length_instruction = ""
    max_tokens_setting = 1000
    if laengde == 'mellem':
        length_instruction = "Skriv historien i cirka 10-14 sammenhængende afsnit. Den skal føles som en mellemlang historie."
        max_tokens_setting = 3000
    elif laengde == 'lang':
        length_instruction = "Skriv en **meget lang og detaljeret historie** på **mindst 15 fyldige afsnit**, gerne flere. Sørg for en dybdegående fortælling."
        max_tokens_setting = 7000
    else:  # kort
        length_instruction = "Skriv historien i cirka 6-8 korte, sammenhængende afsnit."
        max_tokens_setting = 1500

    print(f"Længde instruktion: {length_instruction}, Max Tokens: {max_tokens_setting}")

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

    listener_context_instruction = ""
    names_list_for_ending = []
    if listeners:
        listener_descriptions = []
        ages = []
        for listener in listeners:
            name = listener.get('name', '').strip()
            age_str = listener.get('age', '').strip()
            desc = name if name else 'et barn'
            if age_str:
                desc += f" på {age_str} år"
                ages.append(age_str)
            if name:
                names_list_for_ending.append(name)
            listener_descriptions.append(desc)

        if listener_descriptions:
            listener_context_instruction = f"INFO OM LYTTEREN(E): Historien læses højt for {', '.join(listener_descriptions[:-1])}{' og ' if len(listener_descriptions) > 1 else ''}{listener_descriptions[-1] if listener_descriptions else 'et barn'}."
            listener_context_instruction += " Tilpas sprog og temaer, så de er passende og engagerende for denne/disse lytter(e)."

    ending_instruction = "VIGTIGT OM AFSLUTNINGEN: Afslut historien på en positiv og tryg måde, der er passende for en godnathistorie. Henvend dig IKKE direkte til lytteren midt i historien."
    if names_list_for_ending:
        ending_instruction = (f"VIGTIGT OM AFSLUTNINGEN: Afslut historien på en positiv og tryg måde. "
                              f"Som en ALLER SIDSTE sætning i historien, efter selve handlingen er afsluttet, sig 'Sov godt, {', '.join(names_list_for_ending[:-1])}{' og ' if len(names_list_for_ending) > 1 else ''}{names_list_for_ending[-1] if names_list_for_ending else 'lille ven'}! Drøm sødt.' "
                              f"Denne afslutning skal KUN være den sidste sætning. Henvend dig IKKE direkte til lytteren midt i historien.")

    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }
    generation_config = genai.types.GenerationConfig(
        max_output_tokens=max_tokens_setting,
        temperature=0.7
    )

    prompt_parts = []
    prompt_parts.append("SYSTEM INSTRUKTION: Du er en kreativ AI, der er ekspert i at skrive godnathistorier for børn.")
    prompt_parts.append(
        "OPGAVE: Skriv en godnathistorie baseret på følgende input. Historien skal være engagerende, passende for målgruppen og have en klar begyndelse, midte og slutning.")
    prompt_parts.append(
        "FØRST, generer en kort og fængende titel til historien. Skriv KUN titlen på den allerførste linje af dit output. Efter titlen, indsæt ET ENKELT LINJESKIFT (ikke dobbelt), og start derefter selve historien.")
    prompt_parts.append("---")

    if listener_context_instruction:
        prompt_parts.append(listener_context_instruction)

    prompt_parts.append(f"Længdeønske: {length_instruction}")
    prompt_parts.append(f"Stemning: {mood_prompt_part}")

    if karakter_str: prompt_parts.append(f"Hovedperson(er): {karakter_str}")
    if sted_str: prompt_parts.append(f"Sted(er): {sted_str}")
    if plot_str: prompt_parts.append(f"Plot/Elementer/Morale: {plot_str}")

    if is_interactive:
        interactive_rules = (
            "REGLER FOR INDDRAGENDE EVENTYR MED EKSPLICITTE VALG-STIER:\n"
            # ... (din eksisterende logik for interaktive regler) ...
        )
        prompt_parts.append(f"\n{interactive_rules}")

    prompt_parts.append("\nGENERELLE REGLER FOR HISTORIEN:")
    prompt_parts.append("- Undgå komplekse sætninger og ord. Sproget skal være letforståeligt for børn.")
    prompt_parts.append("- Inkluder gerne gentagelser, rim eller lydeffekter, hvis det passer til historien.")
    prompt_parts.append("- Sørg for en positiv morale eller et opløftende budskab, hvis det er relevant for plottet.")
    prompt_parts.append("- Undgå vold, upassende temaer eller noget, der kan give mareridt.")

    if negative_prompt_text:
        prompt_parts.append(f"- VIGTIGT: Følgende elementer må IKKE indgå i historien: {negative_prompt_text}")

    prompt_parts.append(f"- {ending_instruction}")
    prompt_parts.append("---")
    prompt_parts.append(
        "Start outputtet med TITLEN på første linje, efterfulgt af ET ENKELT LINJESKIFT, og derefter selve historien:")

    prompt = "\n".join(prompt_parts)
    print(
        f"--- Sender FULD Prompt til Gemini (Max Tokens: {max_tokens_setting}) ---\n{prompt}\n------------------------------")

    story_title = "Uden Titel"
    actual_story_content = "Der opstod en fejl under historiegenerering."

    try:
        print("Initialiserer Gemini model...")
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        print(f"Bruger model: gemini-1.5-flash-latest")

        print("Sender anmodning til Google Gemini...")
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings,
        )
        print("Svar modtaget fra Google Gemini.")

        raw_text_from_gemini = ""
        try:
            raw_text_from_gemini = response.text
            parts = raw_text_from_gemini.split('\n', 1)
            if len(parts) >= 1 and parts[0].strip():
                story_title = parts[0].strip()
                if len(parts) > 1 and parts[1].strip():
                    actual_story_content = parts[1].strip()
                elif not parts[0].strip() and len(parts) > 1 and parts[1].strip():
                    story_title = "Uden Titel (Genereret)"
                    actual_story_content = parts[1].strip()
                elif parts[0].strip() and (len(parts) == 1 or not parts[1].strip()):
                    actual_story_content = "Historien mangler efter titlen."
                    print(f"Kunne kun parse titel, historien mangler. Råtekst: {raw_text_from_gemini[:200]}")
                else:
                    story_title = "Uden Titel (Parse Fejl)"
                    actual_story_content = raw_text_from_gemini
                    print(f"Kunne ikke parse titel og historie optimalt. Råtekst: {raw_text_from_gemini[:200]}")
            else:
                story_title = "Uden Titel (Intet Linjeskift)"
                actual_story_content = raw_text_from_gemini.strip() if raw_text_from_gemini.strip() else "Modtog tomt svar fra AI."
                print(f"Ingen linjeskift fundet til at adskille titel. Råtekst: {raw_text_from_gemini[:200]}")
        except ValueError as e:
            print(f"Svar blokeret af sikkerhedsfilter eller problem med response.text: {e}")
            print(
                f"Prompt Feedback: {response.prompt_feedback if response and hasattr(response, 'prompt_feedback') else 'Ingen prompt feedback tilgængelig.'}")
            story_title = "Blokeret Indhold"
            actual_story_content = "Beklager, historien kunne ikke laves, da den eller dele af den blev blokeret af indholdsfiltre. Prøv at justere dine input."
        except Exception as e_parse:
            print(f"Fejl under adgang til response.text eller parsing: {e_parse}")
            print(traceback.format_exc())
            story_title = "Parse Fejl"
            actual_story_content = "Der opstod en fejl under behandling af svaret fra AI."
            if response and response.candidates:
                try:
                    actual_story_content = response.candidates[0].content.parts[0].text
                    parts = actual_story_content.split('\n', 1)
                    if len(parts) >= 1 and parts[0].strip():
                        story_title = parts[0].strip()
                        actual_story_content = parts[1].strip() if len(parts) > 1 and parts[
                            1].strip() else "Historien mangler efter titlen."
                    print("Fallback til parsing fra response.candidates succesfuld (delvist).")
                except Exception as e_candidate:
                    print(f"Kunne heller ikke hente indhold fra response.candidates: {e_candidate}")
    except Exception as e_api:
        print(f"Fejl ved kald til Google Gemini API: {e_api}")
        print(traceback.format_exc())
        story_title = "API Fejl"
        actual_story_content = f"Beklager, jeg kunne ikke lave en historie lige nu på grund af en teknisk fejl med AI-tjenesten. Prøv venligst igen senere."

    if not isinstance(story_title, str): story_title = "Uden Titel (Intern Fejl)"
    if not isinstance(actual_story_content, str): actual_story_content = "Indhold mangler (Intern Fejl)"

    print(f"Returnerer titel: '{story_title}'")
    return jsonify(title=story_title, story=actual_story_content)


# === LOGIN/LOGOUT ROUTES ===
@app.route('/login')
def google_login():
    if 'google' not in oauth._registry:
        flash("Google login er ikke konfigureret korrekt på serveren.", "error")
        return redirect(url_for('index'))
    redirect_uri = url_for('google_authorize', _external=True)
    print(f"Redirecting to Google for login. Callback URI: {redirect_uri}")
    return oauth.google.authorize_redirect(redirect_uri)


@app.route('/authorize')
def google_authorize():
    print("Received callback from Google.")
    if 'google' not in oauth._registry:
        flash("Google login er ikke konfigureret korrekt på serveren.", "error")
        return redirect(url_for('index'))
    try:
        token = oauth.google.authorize_access_token()
        if not token:
            print("Failed to authorize access token.");
            flash("Login mislykkedes (token).", "error");
            return redirect(url_for('index'))
        print("Access token received. Fetching user info...")
        user_info = oauth.google.userinfo(token=token)
        if not user_info:
            print("Could not fetch user info.");
            flash("Login mislykkedes (userinfo).", "error");
            return redirect(url_for('index'))

        print(f"User info received: {user_info}")
        google_user_id = user_info.get('sub')
        user_email = user_info.get('email')
        user_name = user_info.get('name')

        if not google_user_id:
            print("Google user ID ('sub') not found.");
            flash("Login mislykkedes (ID).", "error");
            return redirect(url_for('index'))

        user = User.query.filter_by(google_id=google_user_id).first()
        if user:
            print(f"Existing user found: {user}")
            needs_commit = False
            if user.name != user_name: user.name = user_name; needs_commit = True
            if user.email != user_email:
                existing_email = User.query.filter_by(email=user_email).first()
                if not existing_email or existing_email.google_id == google_user_id:
                    user.email = user_email;
                    needs_commit = True
                else:
                    print(f"Warning: Email {user_email} already exists...")
            if needs_commit:
                try:
                    db.session.commit(); print("User info updated.")
                except Exception as e:
                    db.session.rollback(); print(f"Error updating user info: {e}")
        else:
            print(f"New user detected. Creating user...")
            user = User(google_id=google_user_id, name=user_name, email=user_email)
            db.session.add(user)
            try:
                db.session.commit(); print(f"New user created: {user}")
            except Exception as e:
                db.session.rollback();
                print(f"Error committing new user: {e}");
                print(traceback.format_exc())
                flash("Fejl: Kunne ikke oprette bruger.", "error");
                return redirect(url_for('index'))

        login_user(user, remember=True)
        print(f"User {user.id} logged in successfully.")
        flash(f"Velkommen, {user.name}!", "success")
        return redirect(url_for('index'))

    except Exception as e:
        print(f"Error during Google authorization: {e}");
        print(traceback.format_exc())
        flash(f"Der opstod en uventet fejl under login: {e}", "error")
        return redirect(url_for('index'))


@app.route('/logout')
@login_required
def logout():
    user_id_before = current_user.id if current_user.is_authenticated else 'anonymous'
    logout_user()
    session.clear()
    print(f"User {user_id_before} logged out.")
    flash("Du er nu logget ud.", "info")
    return redirect(url_for('index'))


# === *** NY ROUTE: Generer Lyd med ElevenLabs *** ===
@app.route('/generate_audio', methods=['POST'])
def generate_audio():
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
        voice_id = "gpf7HQVro4L2OVR54kr8"
        print(f"Requesting audio from ElevenLabs using voice: {voice_id}")
        audio_stream = elevenlabs_client.generate(
            text=story_text,
            voice=Voice(voice_id=voice_id),
            model='eleven_multilingual_v2'
        )
        print("Audio stream received from ElevenLabs.")
        return Response(audio_stream, mimetype='audio/mpeg')
    except Exception as e:
        print(f"Error calling ElevenLabs API: {e}")
        print(traceback.format_exc())
        return jsonify({"error": f"Fejl ved generering af lyd: {e}"}), 500


# === NY ROUTE: Billedgenerering ===
@app.route('/generate_image_from_story', methods=['POST'])
def generate_image_from_story():
    data = request.get_json()
    if not data or 'story_text' not in data:
        return jsonify({"error": "Mangler 'story_text' i anmodningen."}), 400

    story_text = data.get('story_text')
    if not story_text.strip():
        return jsonify({"error": "'story_text' må ikke være tom."}), 400

    print(f"Modtaget anmodning til /generate_image_from_story. Historielængde: {len(story_text)}")

    generated_image_prompt_text = "En illustration af en scene fra historien."
    try:
        print("Genererer billedprompt med Gemini...")
        gemini_model_for_prompting = genai.GenerativeModel('gemini-1.5-flash-latest')
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
        # Fortsæt med fallback prompten, da billedgenerering stadig kan forsøges
        # eller returner en fejl her, hvis promptgenerering er kritisk.
        # For nu fortsætter vi.

    if not GOOGLE_CLOUD_PROJECT_ID:
        print("FEJL: GOOGLE_CLOUD_PROJECT_ID er ikke sat. Kan ikke kalde Vertex AI.")
        return jsonify({"error": "Serverkonfigurationsfejl: Projekt ID mangler for billedgenerering."}), 500

    # Initialiser current_prompt_to_imagen med den oprindeligt genererede prompt
    # Dette sikrer, at den er defineret, selvom løkken ikke kører eller fejler tidligt.
    current_prompt_to_imagen = generated_image_prompt_text

    # Ydre try-blok for at fange den endelige fejl efter genforsøg
    try:
        max_retries = 2
        for attempt in range(max_retries):
            # Denne try-blok er for hvert enkelt forsøg
            try:
                print(f"Forsøg {attempt + 1} på at generere billede med Vertex AI Imagen.")
                # Sæt/opdater current_prompt_to_imagen for dette forsøg
                if attempt == 0:
                    current_prompt_to_imagen = generated_image_prompt_text
                elif attempt == 1:  # Andet forsøg - modificer prompten
                    print("Modificerer prompt til andet forsøg...")
                    prompt_suffix_variation = " (different visual interpretation, focus on a key moment)"
                    current_prompt_to_imagen = generated_image_prompt_text + prompt_suffix_variation  # Start fra den oprindelige
                    print(f"Ny modificeret prompt: {current_prompt_to_imagen}")

                model_identifier_imagen3 = "imagen-3.0-generate-002"
                print(f"Bruger Imagen model: {model_identifier_imagen3} med prompt: {current_prompt_to_imagen}")

                try:
                    model = ImageGenerationModel.from_pretrained(model_identifier_imagen3)
                    print(f"Succesfuldt loaded Imagen model: {model_identifier_imagen3}")
                except Exception as e_load_model:
                    print(f"FEJL: Kunne ikke loade modellen '{model_identifier_imagen3}'. Fejl: {e_load_model}")
                    raise ValueError(
                        f"Kunne ikke initialisere billedgenereringsmodellen: {model_identifier_imagen3}.") from e_load_model

                response_imagen = model.generate_images(
                    prompt=current_prompt_to_imagen,
                    number_of_images=1,
                    guidance_scale=30,
                )

                if response_imagen and response_imagen.images:
                    image_obj = response_imagen.images[0]
                    if hasattr(image_obj, '_image_bytes') and image_obj._image_bytes:
                        image_bytes = image_obj._image_bytes
                        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                        image_data_url = f"data:image/png;base64,{image_base64}"
                        print("Billede genereret succesfuldt og konverteret til data URL.")
                        return jsonify({
                            "message": "Billede genereret!",
                            "image_url": image_data_url,
                            "image_prompt_used": current_prompt_to_imagen
                        })
                    else:
                        print(
                            f"FEJL: _image_bytes mangler eller er tom i det returnerede billedeobjekt (forsøg {attempt + 1}).")
                        if attempt == max_retries - 1:
                            raise ValueError("EMPTY_IMAGE_BYTES_ERROR_AFTER_RETRIES")
                else:
                    print(
                        f"FEJL: Vertex AI Imagen returnerede et svar uden en 'images' liste eller en tom 'images' liste (forsøg {attempt + 1}).")
                    print(f"Streng repræsentation af Fuld Imagen response: {response_imagen}")
                    if attempt == max_retries - 1:
                        raise ValueError("EMPTY_IMAGE_LIST_ERROR_AFTER_RETRIES")

                # Pause før næste forsøg, hvis der er flere forsøg tilbage
                if attempt < max_retries - 1:
                    print(f"Venter før næste genforsøg...")
                    time.sleep(1.5)

            # Indre except-blok: Fanger fejl specifikt for dette forsøg
            except Exception as e_attempt_specific:
                print(f"Fejl under billedgenereringsforsøg {attempt + 1}: {e_attempt_specific}")
                # Hvis det er en ikke-genprøvbar fejl, eller sidste forsøg, re-raise fejlen
                # så den fanges af den ydre 'except Exception as e_vertex:'
                non_retryable_error_substrings = [
                    "quota exceeded",
                    "permission denied",
                    "billing",
                    "does not exist or you do not have permission",
                    "Kunne ikke initialisere billedgenereringsmodellen"
                ]
                is_non_retryable = any(sub in str(e_attempt_specific).lower() for sub in non_retryable_error_substrings)

                if is_non_retryable or attempt == max_retries - 1:
                    print(f"Fejl er ikke-genprøvbar eller sidste forsøg. Re-raiser fejlen.")
                    raise  # Re-raise den nuværende exception

                # For andre fejl, log og lad løkken fortsætte til næste forsøg
                print(f"Fortsætter til næste genforsøg efter fejl: {e_attempt_specific}")
                if attempt < max_retries - 1:  # Sørg for kun at sove hvis der er flere forsøg
                    time.sleep(1.5)

        # Hvis løkken fuldføres uden at returnere et billede (dvs. alle forsøg resulterede i tomme lister/bytes,
        # men uden at kaste en fejl, der blev re-raised ovenfor), så er noget galt.
        # Dette burde ideelt set ikke ske hvis logikken ovenfor korrekt re-raiser på sidste forsøg.
        print("FEJL: Alle billedgenereringsforsøg mislykkedes uden at returnere et billede.")
        raise ValueError("ALL_RETRIES_FAILED_NO_IMAGE_RETURNED")


    # Ydre except-blok: Fanger den endelige fejl efter alle genforsøg, eller ikke-genprøvbare fejl
    except Exception as e_vertex:
        final_error_message_for_log = f"Endelig fejl under billedgenerering med Vertex AI Imagen: {e_vertex}"
        print(final_error_message_for_log)
        print(traceback.format_exc())

        user_facing_error_message = f"Der opstod en uventet fejl under billedgenerering: {str(e_vertex)}"

        if "EMPTY_IMAGE_LIST_ERROR_AFTER_RETRIES" in str(e_vertex) or \
                "EMPTY_IMAGE_BYTES_ERROR_AFTER_RETRIES" in str(e_vertex) or \
                "ALL_RETRIES_FAILED_NO_IMAGE_RETURNED" in str(e_vertex):  # Tilføjet ny generel fejl
            user_facing_error_message = "Billedgeneratoren kunne desværre ikke skabe et billede til denne historie, selv efter flere forsøg. Prøv eventuelt at justere historieinputtet eller prøv igen senere."
        elif "permission denied" in str(e_vertex).lower() or "billing" in str(e_vertex).lower():
            user_facing_error_message = "Billedgenerering fejlede pga. et problem med serverens adgangsrettigheder eller faktureringskonto. Kontakt administratoren."
        elif "quota exceeded" in str(e_vertex).lower():
            user_facing_error_message = "Billedgenereringskvoten er opbrugt. Prøv igen senere."
        elif "does not exist or you do not have permission" in str(e_vertex).lower() or \
                "Kunne ikke initialisere billedgenereringsmodellen" in str(
            e_vertex).lower():  # Inkluderer model init fejl
            user_facing_error_message = "Billedmodellen kunne ikke tilgås eller initialiseres korrekt. Kontakt administratoren."

        return jsonify({"error": user_facing_error_message, "image_prompt_used": current_prompt_to_imagen}), 500


# === Opret Database Tabeller ===
def create_tables():
    with app.app_context():
        print("Checking/Creating database tables...")
        try:
            db.create_all()
        except Exception as e:
            print(f"Error creating tables: {e}"); print(traceback.format_exc())
        else:
            print("Database tables checked/created successfully.")


# === Start Webserveren ===
if __name__ == '__main__':
    create_tables()
    app.run(debug=True, port=5000)