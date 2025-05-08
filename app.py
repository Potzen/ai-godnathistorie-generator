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
# *** ------------------------------------------------------ ***

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
# Denne funktion er den fulde version fra før login/TTS blev tilføjet
@app.route('/generate', methods=['POST'])
def generate_story():
    """ Modtager brugerinput, bygger prompt UDEN defaults, kalder Gemini, og returnerer historien. """
    data = request.get_json()
    if not data:
        return jsonify(story="Fejl: Ingen data modtaget."), 400
    print("Modtaget data for /generate:", data)

    # Hent alle inputs
    karakterer_data = data.get('karakterer')
    steder_liste = data.get('steder')
    plots_liste = data.get('plots')
    laengde = data.get('laengde', 'kort')
    mood = data.get('mood', 'neutral')
    listeners = data.get('listeners', [])
    is_interactive = data.get('interactive', False)
    negative_prompt_text = data.get('negative_prompt', '').strip()
    print(f"Valgt længde: {laengde}, Valgt stemning: {mood}, Lyttere: {listeners}, Interaktiv: {is_interactive}, Negativ Prompt: '{negative_prompt_text}'")

    # Forbered grundlæggende strenge (UDEN DEFAULTS)
    karakter_descriptions_for_prompt = []
    if karakterer_data:
        for char_obj in karakterer_data:
            desc = char_obj.get('description','').strip(); name = char_obj.get('name','').strip()
            if desc: karakter_descriptions_for_prompt.append(f"{desc} ved navn {name}" if name else desc)
    karakter_str = ", ".join(karakter_descriptions_for_prompt)

    valid_steder = []
    if steder_liste: valid_steder = [s.strip() for s in steder_liste if s and s.strip()]
    sted_str = ", ".join(valid_steder)

    valid_plots = []
    if plots_liste: valid_plots = [p.strip() for p in plots_liste if p and p.strip()]
    plot_str = ", ".join(valid_plots)

    print(f"Input til historie (behandlet): Karakterer='{karakter_str}', Steder='{sted_str}', Plot/Morale='{plot_str}'")

    # Definer Længde-instruktion og max_tokens
    length_instruction = ""; max_tokens_setting = 1000
    if laengde == 'mellem': length_instruction = "Skriv historien i cirka 10-14 afsnit..."; max_tokens_setting = 3000
    elif laengde == 'lang': length_instruction = "Skriv en **meget lang...** historie på **mindst 9000 tegn**..."; max_tokens_setting = 8000
    else: length_instruction = "Skriv historien i cirka 6-8 afsnit."; max_tokens_setting = 1000
    print(f"Længde instruktion: {length_instruction}, Max Tokens: {max_tokens_setting}")

    # Definer MERE SPECIFIK stemnings-instruktion
    mood_instruction = ""
    if mood == 'sød': mood_instruction = "Historien skal have en **meget sød...** stemning."
    elif mood == 'sjov': mood_instruction = "Historien skal have en **tydelig humoristisk...** tone."
    # ... (alle andre elif for stemninger) ...
    elif mood == 'uhyggelig': mood_instruction = "Historien skal have en **uhyggelig...** stemning..."
    mood_prompt_part = f"Stemning: {mood_instruction}" if mood_instruction else "Stemning: Neutral / Blandet."
    print(f"Stemnings instruktion (til prompt): {mood_prompt_part}")

    # Byg Lytter Kontekst og Afslutnings-instruktion
    listener_context_instruction = ""; names_list_for_ending = []
    if listeners:
        listener_descriptions = []; ages = []
        for listener in listeners:
            name = listener.get('name'); age = listener.get('age')
            desc = name if name else 'et barn'
            if age: desc += f" på {age} år"; ages.append(age)
            if name: names_list_for_ending.append(name)
            listener_descriptions.append(desc)
        if listener_descriptions:
             listener_context_instruction = f"INFO OM LYTTEREN(E): ..." # Forkortet

    ending_instruction = ""
    if names_list_for_ending: ending_instruction = f"VIGTIGT OM AFSLUTNINGEN: ... KUN i denne specifikke afslutning."
    else: ending_instruction = "VIGTIGT OM AFSLUTNINGEN: ... Henvend dig IKKE direkte til lytteren midt i historien."

    # Definer safety_settings og generation_config
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

    # Byg Prompt - Dele tilføjes KUN hvis de har indhold
    prompt_parts = []
    if listener_context_instruction: prompt_parts.append(listener_context_instruction); prompt_parts.append("\n---")
    prompt_parts.append(f"OPGAVE: Skriv et {'INDDRAGENDE eventyr' if is_interactive else 'godnathistorie'} baseret på følgende:")
    prompt_parts.append(f"Længde: {length_instruction}")
    prompt_parts.append(mood_prompt_part)
    if karakter_str: prompt_parts.append(f"Hovedpersoner: {karakter_str}")
    if sted_str: prompt_parts.append(f"Steder: {sted_str}")
    if plot_str: prompt_parts.append(f"Plot/Elementer/Morale: {plot_str}")

    if is_interactive:
        interactive_rules = """REGLER FOR INDDRAGENDE EVENTYR MED EKSPLICITTE VALG-STIER: ... """ # Fuld definition som før
        prompt_parts.append(f"\n{interactive_rules}")

    prompt_parts.append("\nGENERELLE REGLER:")
    # ... (alle generelle regler som før) ...
    if negative_prompt_text: prompt_parts.append(f"- VIGTIGT: Følgende elementer må IKKE indgå: {negative_prompt_text}")
    prompt_parts.append(f"- {ending_instruction}")
    prompt_parts.append("---"); prompt_parts.append("Start historien her:")

    prompt = "\n".join(prompt_parts)
    print(f"--- Sender FULD Prompt til Gemini (Max Tokens: {max_tokens_setting}) ---\n{prompt}\n------------------------------")

    # API Kald og Respons Håndtering
    actual_story = "Der opstod en uventet fejl før API kald."
    try:
        print("Initialiserer Gemini model...")
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        print("Bruger model: gemini-1.5-flash-latest")
        print("Sender anmodning til Google Gemini...")
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings
            )
        print("Svar modtaget fra Google Gemini.")
        try:
            actual_story = response.text
        except ValueError as e:
             print(f"Svar blokeret af sikkerhedsfilter: {e}"); print(f"Prompt Feedback: {response.prompt_feedback}")
             actual_story = "Beklager, historien kunne ikke laves..."
    except Exception as e:
        print(f"Fejl ved kald til Google Gemini: {e}")
        print(traceback.format_exc())
        actual_story = f"Beklager, jeg kunne ikke lave en historie lige nu pga. fejl: {e}..."

    return jsonify(story=actual_story)


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

