# Fil: app.py

# -----------------------------------------------------------------------------
# DEL 1: IMPORTS & GLOBALE UINITIALISEREDE UDVIDELSER
# -----------------------------------------------------------------------------
import base64
import os
import time
import secrets  # Bruges af config.py til default SECRET_KEY
import traceback

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from authlib.integrations.flask_client import OAuth

# Importer fra dine egne moduler
from config import Config
# Blueprints importeres inde i create_app() for at undgå cirkulære imports.

# Google / AI Biblioteker
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.cloud import aiplatform
import vertexai
# Sørg for at denne import er den korrekte for den Vertex AI model du anvender for billedgenerering
from vertexai.preview.vision_models import ImageGenerationModel
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice

# Din inspektionsblok kan forblive her, da den kører uafhængigt ved modul-load
try:
    print("--- Inspicerer vertexai.language_models ---")
    import vertexai.language_models  # Denne er kun til inspektion

    print(f"Attributter i vertexai.language_models: {dir(vertexai.language_models)}")
except ImportError as ie:
    print(f"Kunne ikke importere vertexai.language_models for inspektion: {ie}")
except Exception as e_inspect:
    print(f"Anden fejl under inspektion: {e_inspect}")

# Initialiser udvidelser globalt (uden app-instans)
db = SQLAlchemy()
login_manager = LoginManager()
oauth = OAuth()
elevenlabs_client = None  # Initialiseres i create_app


# -----------------------------------------------------------------------------
# DEL 2: APPLICATION FACTORY FUNKTION (create_app)
# -----------------------------------------------------------------------------
def create_app(config_class=Config):  # <--- HER DEFINERES create_app FUNKTIONEN
    """
    Application Factory funktion til at oprette og konfigurere Flask app'en.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # --- Initialiser API klienter og valider konfiguration ---
    try:
        config_class.validate_critical_config()
        app.logger.info("Kritiske konfigurationsvariabler er til stede.")
    except ValueError as e:
        app.logger.error(f"FEJL: Manglende kritiske konfigurationsvariabler: {e}")
        # Overvej at håndtere dette, f.eks. ved at stoppe appen.

    # Google Generative AI (Gemini)
    if app.config.get('GOOGLE_API_KEY'):
        genai.configure(api_key=app.config['GOOGLE_API_KEY'])
        app.logger.info("Google AI API Key konfigureret succesfuldt via app.config.")
    else:
        app.logger.warning("ADVARSEL: GOOGLE_API_KEY mangler i app.config! Gemini vil ikke virke.")

    # ElevenLabs Client
    global elevenlabs_client
    if app.config.get('ELEVENLABS_API_KEY'):
        try:
            elevenlabs_client = ElevenLabs(api_key=app.config['ELEVENLABS_API_KEY'])
            app.logger.info("ElevenLabs Client initialiseret succesfuldt via app.config.")
        except Exception as e:
            app.logger.error(f"FEJL ved initialisering af ElevenLabs client: {e}\n{traceback.format_exc()}")
    else:
        app.logger.warning("ADVARSEL: ELEVENLABS_API_KEY mangler i app.config! Oplæsning vil ikke virke.")

    # Vertex AI
    if app.config.get('GOOGLE_CLOUD_PROJECT_ID'):
        try:
            if app.config.get('GOOGLE_APPLICATION_CREDENTIALS'):
                app.logger.info(
                    f"INFO: GOOGLE_APPLICATION_CREDENTIALS er sat i config til: {app.config['GOOGLE_APPLICATION_CREDENTIALS']}")
            else:
                app.logger.info("INFO: GOOGLE_APPLICATION_CREDENTIALS forventes sat i miljøet.")
            aiplatform.init(project=app.config['GOOGLE_CLOUD_PROJECT_ID'], location=app.config['VERTEX_AI_REGION'])
            vertexai.init(project=app.config['GOOGLE_CLOUD_PROJECT_ID'], location=app.config['VERTEX_AI_REGION'])
            app.logger.info(
                f"Vertex AI initialiseret via app.config. Projekt: {app.config['GOOGLE_CLOUD_PROJECT_ID']}, Region: {app.config['VERTEX_AI_REGION']}")
        except Exception as e:
            app.logger.error(f"FEJL ved initialisering af Vertex AI: {e}\n{traceback.format_exc()}")
    else:
        app.logger.warning("ADVARSEL: GOOGLE_CLOUD_PROJECT_ID mangler i app.config! Vertex AI kald vil fejle.")

    # Opret 'instance' mappen hvis den ikke eksisterer
    if not os.path.exists(app.instance_path):
        try:
            os.makedirs(app.instance_path)
            app.logger.info(f"Oprettet instance mappe: {app.instance_path}")
        except OSError as e:
            app.logger.error(f"Fejl ved oprettelse af instance mappe {app.instance_path}: {e}")

    # --- Initialiser Flask Udvidelser med appen ---
    db.init_app(app)
    login_manager.init_app(app)
    oauth.init_app(app)

    login_manager.login_view = 'auth.google_login'  # Vil pege på auth blueprint, når det er oprettet
    login_manager.login_message = "Log venligst ind for at bruge denne funktion."
    login_manager.login_message_category = "info"

    # Her sker registreringen af Google provideren
    print("DEBUG: Tjekker GOOGLE_CLIENT_ID og GOOGLE_CLIENT_SECRET...")
    client_id_found = app.config.get('GOOGLE_CLIENT_ID')
    client_secret_found = app.config.get('GOOGLE_CLIENT_SECRET')
    print(
        f"DEBUG: GOOGLE_CLIENT_ID fundet: {bool(client_id_found)}, GOOGLE_CLIENT_SECRET fundet: {bool(client_secret_found)}")

    if client_id_found and client_secret_found:
        oauth.register(  # Dette kaldes på det globale oauth-objekt, som er blevet init_app'ed
            name='google',
            server_metadata_url=app.config.get("GOOGLE_DISCOVERY_URL"),
            client_kwargs={'scope': 'openid email profile'}
        )
        print("PRINT-DEBUG: OAuth Google provider registreret succesfuldt via app.config.")
    else:
        print("PRINT-DEBUG: OAuth Google provider IKKE registreret pga. manglende nøgler i app.config.")
        if not client_id_found:
            print("PRINT-DEBUG: GOOGLE_CLIENT_ID mangler eller er tom.")
        if not client_secret_found:
            print("PRINT-DEBUG: GOOGLE_CLIENT_SECRET mangler eller er tom.")

    # --- Importer og Registrer Blueprints ---
    from routes.main_routes import main_bp

    if 'main' not in app.blueprints:
        app.register_blueprint(main_bp)
        app.logger.info("Blueprint 'main_bp' registreret.")
    else:
        app.logger.info("Blueprint 'main_bp' var allerede registreret (undlod gen-registrering).")

    # Importer auth_bp LIGE FØR den skal bruges, EFTER oauth.register er kaldt
    from routes.auth_routes import auth_bp
    if 'auth' not in app.blueprints:
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.logger.info("Blueprint 'auth_bp' registreret med prefix /auth.")
    else:
        app.logger.info("Blueprint 'auth_bp' var allerede registreret.")

    # Senere: from routes.story_routes import story_bp
    # app.register_blueprint(story_bp)

    # --- Definer User Loader ---
    @login_manager.user_loader
    def load_user(user_id):
        # User modellen defineres globalt længere nede i denne fil.
        # Når den flyttes til models.py, skal den importeres her (f.eks. from .models import User)
        try:
            user = User.query.get(int(user_id))  # Bruger det globale User-objekt
            return user
        except Exception as e:
            app.logger.error(f"Fejl ved indlæsning af bruger {user_id}: {e}")
            return None

    app.logger.info("Flask app oprettelse fuldført.")
    return app


# -----------------------------------------------------------------------------
# DEL 3: DATABASE MODEL(LER) & ROUTE DEFINITIONER (MIDLERTIDIGT HER)
# -----------------------------------------------------------------------------

# === Database Model (User) ===
# DENNE SKAL SENERE FLYTTES TIL en ny fil, f.eks. models.py
class User(UserMixin, db.Model):  # UserMixin er nu importeret korrekt
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)

    def __repr__(self):
        return f'<User id={self.id} name={self.name} email={self.email}>'


# === ROUTES DER SKAL FLYTTES TIL BLUEPRINTS ===
# (Her er dine xxx_original_logic funktioner for generate_story, google_login,
# google_authorize, logout, generate_audio, generate_image_from_story)
# Disse funktioner skal IKKE have @<blueprint_name>.route decorators her.
# De er kun skabeloner for den logik, der skal flyttes.

def generate_story_original_logic():
    data = request.get_json()
    if not data:
        return jsonify(title="Fejl", story="Ingen data modtaget."), 400
    current_app.logger.info(f"Modtaget data for /generate: {data}")

    karakterer_data = data.get('karakterer')
    steder_liste = data.get('steder')
    plots_liste = data.get('plots')
    laengde = data.get('laengde', 'kort')
    mood = data.get('mood', 'neutral')
    listeners = data.get('listeners', [])
    is_interactive = data.get('interactive', False)
    negative_prompt_text = data.get('negative_prompt', '').strip()
    current_app.logger.info(
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

    current_app.logger.info(
        f"Input til historie (behandlet): Karakterer='{karakter_str}', Steder='{sted_str}', Plot/Morale='{plot_str}'")

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
    current_app.logger.info(f"Længde instruktion: {length_instruction}, Max Tokens: {max_tokens_setting}")

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
    current_app.logger.info(f"Stemnings instruktion (til prompt): {mood_prompt_part}")

    listener_context_instruction = ""
    names_list_for_ending = []
    if listeners:
        listener_descriptions = []
        # ages = [] # 'ages' blev ikke brugt
        for listener_item in listeners:
            name = listener_item.get('name', '').strip()
            age_str = listener_item.get('age', '').strip()
            desc = name if name else 'et barn'
            if age_str:
                desc += f" på {age_str} år"
                # ages.append(age_str)
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
    if listener_context_instruction: prompt_parts.append(listener_context_instruction)
    prompt_parts.append(f"Længdeønske: {length_instruction}")
    prompt_parts.append(f"Stemning: {mood_prompt_part}")
    if karakter_str: prompt_parts.append(f"Hovedperson(er): {karakter_str}")
    if sted_str: prompt_parts.append(f"Sted(er): {sted_str}")
    if plot_str: prompt_parts.append(f"Plot/Elementer/Morale: {plot_str}")
    if is_interactive:  # Denne variabel var defineret
        interactive_rules = (
            "REGLER FOR INDDRAGENDE EVENTYR MED EKSPLICITTE VALG-STIER:\n")  # ... (din interaktive logik her) ...
        prompt_parts.append(f"\n{interactive_rules}")
    prompt_parts.append("\nGENERELLE REGLER FOR HISTORIEN:")
    prompt_parts.append("- Undgå komplekse sætninger og ord. Sproget skal være letforståeligt for børn.")
    prompt_parts.append("- Inkluder gerne gentagelser, rim eller lydeffekter, hvis det passer til historien.")
    prompt_parts.append("- Sørg for en positiv morale eller et opløftende budskab, hvis det er relevant for plottet.")
    prompt_parts.append("- Undgå vold, upassende temaer eller noget, der kan give mareridt.")
    if negative_prompt_text:  # Denne variabel var defineret
        prompt_parts.append(f"- VIGTIGT: Følgende elementer må IKKE indgå i historien: {negative_prompt_text}")
    prompt_parts.append(f"- {ending_instruction}")
    prompt_parts.append("---")
    prompt_parts.append(
        "Start outputtet med TITLEN på første linje, efterfulgt af ET ENKELT LINJESKIFT, og derefter selve historien:")
    prompt = "\n".join(prompt_parts)
    current_app.logger.info(
        f"--- Sender FULD Prompt til Gemini (Max Tokens: {max_tokens_setting}) ---\n{prompt}\n------------------------------")

    story_title = "Uden Titel"
    actual_story_content = "Der opstod en fejl under historiegenerering."
    try:
        current_app.logger.info("Initialiserer Gemini model...")
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        current_app.logger.info(f"Bruger model: gemini-1.5-flash-latest")
        current_app.logger.info("Sender anmodning til Google Gemini...")
        response = model.generate_content(prompt, generation_config=generation_config, safety_settings=safety_settings)
        current_app.logger.info("Svar modtaget fra Google Gemini.")
        raw_text_from_gemini = ""
        try:
            raw_text_from_gemini = response.text
            parts = raw_text_from_gemini.split('\n', 1)
            if len(parts) >= 1 and parts[0].strip():
                story_title = parts[0].strip()
                if len(parts) > 1 and parts[1].strip():
                    actual_story_content = parts[1].strip()
                elif not parts[0].strip() and len(parts) > 1 and parts[1].strip():
                    story_title = "Uden Titel (Genereret)";
                    actual_story_content = parts[1].strip()
                elif parts[0].strip() and (len(parts) == 1 or not parts[1].strip()):
                    actual_story_content = "Historien mangler efter titlen."
                    current_app.logger.warning(
                        f"Kunne kun parse titel, historien mangler. Råtekst: {raw_text_from_gemini[:200]}")
                else:
                    story_title = "Uden Titel (Parse Fejl)";
                    actual_story_content = raw_text_from_gemini
                    current_app.logger.warning(
                        f"Kunne ikke parse titel og historie optimalt. Råtekst: {raw_text_from_gemini[:200]}")
            else:
                story_title = "Uden Titel (Intet Linjeskift)"
                actual_story_content = raw_text_from_gemini.strip() if raw_text_from_gemini.strip() else "Modtog tomt svar fra AI."
                current_app.logger.warning(
                    f"Ingen linjeskift fundet til at adskille titel. Råtekst: {raw_text_from_gemini[:200]}")
        except ValueError as e:  # Safety filter
            current_app.logger.error(f"Svar blokeret af sikkerhedsfilter eller problem med response.text: {e}")
            current_app.logger.error(
                f"Prompt Feedback: {response.prompt_feedback if response and hasattr(response, 'prompt_feedback') else 'Ingen prompt feedback.'}")
            story_title = "Blokeret Indhold"
            actual_story_content = "Beklager, historien kunne ikke laves, da den blev blokeret. Prøv at justere dine input."
        except Exception as e_parse:
            current_app.logger.error(
                f"Fejl under adgang til response.text eller parsing: {e_parse}\n{traceback.format_exc()}")
            story_title = "Parse Fejl"
            actual_story_content = "Der opstod en fejl under behandling af svaret fra AI."
            if response and response.candidates:  # Fallback
                try:
                    actual_story_content = response.candidates[0].content.parts[0].text
                    parts = actual_story_content.split('\n', 1)
                    if len(parts) >= 1 and parts[0].strip():
                        story_title = parts[0].strip()
                        actual_story_content = parts[1].strip() if len(parts) > 1 and parts[
                            1].strip() else "Historien mangler efter titlen (fallback)."
                    current_app.logger.info("Fallback til parsing fra response.candidates succesfuld (delvist).")
                except Exception as e_candidate:
                    current_app.logger.error(f"Kunne heller ikke hente indhold fra response.candidates: {e_candidate}")
    except Exception as e_api:
        current_app.logger.error(f"Fejl ved kald til Google Gemini API: {e_api}\n{traceback.format_exc()}")
        story_title = "API Fejl"
        actual_story_content = f"Beklager, teknisk fejl med AI-tjenesten. Prøv igen senere."

    if not isinstance(story_title, str): story_title = "Uden Titel (Intern Fejl)"
    if not isinstance(actual_story_content, str): actual_story_content = "Indhold mangler (Intern Fejl)"
    current_app.logger.info(f"Returnerer titel: '{story_title}'")
    return jsonify(title=story_title, story=actual_story_content)


def google_login_original_logic():
    # Tjekker nu om 'google' client er i oauth objektets dictionary af clients
    # Dette vil blive erstattet af den nye metode i auth_routes.py
    # For nu, hvis dette kaldes, vil det fejle, da oauth ikke er fuldt konfigureret globalt på samme måde.
    # Vi forventer, at denne funktion ikke kaldes direkte, men at logikken flyttes.
    if 'google' not in current_app.extensions.get('authlib.integrations.flask_client', {}):
        flash("Google login er ikke konfigureret korrekt på serveren (original_logic).", "error")
        return redirect(url_for('main.index'))
    redirect_uri = url_for('auth.google_authorize', _external=True)
    current_app.logger.info(f"Redirecting to Google (original_logic). Callback URI: {redirect_uri}")
    # Her skal vi bruge det konfigurerede oauth-objekt fra current_app
    google_client = current_app.extensions['authlib.integrations.flask_client']['google']
    return google_client.authorize_redirect(redirect_uri)


def google_authorize_original_logic():
    current_app.logger.info("Received callback from Google (original_logic).")
    google_client = current_app.extensions.get('authlib.integrations.flask_client', {}).get('google')
    if not google_client:
        flash("Google login er ikke konfigureret korrekt (authorize_original_logic).", "error")
        return redirect(url_for('main.index'))
    try:
        token = google_client.authorize_access_token()
        if not token:
            current_app.logger.warning("Login mislykkedes (original_logic): Kunne ikke autorisere access token.")
            flash("Login mislykkedes (token).", "error");
            return redirect(url_for('main.index'))
        current_app.logger.info("Access token modtaget (original_logic). Henter brugerinfo...")
        user_info = google_client.userinfo(token=token)
        if not user_info:
            current_app.logger.warning("Login mislykkedes (original_logic): Kunne ikke hente brugerinfo.")
            flash("Login mislykkedes (userinfo).", "error");
            return redirect(url_for('main.index'))

        current_app.logger.info(f"Brugerinfo modtaget (original_logic): {user_info}")
        google_user_id = user_info.get('sub')
        user_email_from_google = user_info.get('email')  # Gem e-mail fra Google
        user_name = user_info.get('name')

        if not google_user_id:
            current_app.logger.warning("Login mislykkedes (original_logic): Google user ID ('sub') ikke fundet.")
            flash("Login mislykkedes (ID).", "error");
            return redirect(url_for('main.index'))

        if not user_email_from_google:
            current_app.logger.warning(
                f"Login mislykkedes (original_logic): Ingen e-mail modtaget fra Google for bruger {google_user_id}.")
            flash("Login mislykkedes: Kunne ikke hente din e-mailadresse fra Google.", "error")
            return redirect(url_for('main.index'))

        normalized_email_from_google = user_email_from_google.lower()
        allowed_emails_lower = [email.lower() for email in current_app.config.get('ALLOWED_EMAIL_ADDRESSES', [])]

        if normalized_email_from_google not in allowed_emails_lower:
            current_app.logger.warning(
                f"Login forsøg (original_logic) fra ikke-godkendt e-mail: {user_email_from_google} (Google ID: {google_user_id}).")
            flash("Din e-mailadresse har ikke adgang til denne applikation. Kontakt venligst administratoren.", "error")
            return redirect(url_for('main.index'))

        user = User.query.filter_by(google_id=google_user_id).first()
        if user:
            current_app.logger.info(
                f"Eksisterende bruger (original_logic) fundet: {user} for e-mail {normalized_email_from_google}")
            needs_commit = False
            if user.name != user_name: user.name = user_name; needs_commit = True
            if user.email.lower() != normalized_email_from_google:
                conflicting_user_by_email = User.query.filter(User.email.ilike(normalized_email_from_google),
                                                              User.google_id != google_user_id).first()
                if not conflicting_user_by_email:
                    user.email = user_email_from_google
                    needs_commit = True
                else:
                    current_app.logger.warning(
                        f"Bruger {google_user_id}s Google e-mail ({user_email_from_google}) er allerede i brug af en anden bruger ({conflicting_user_by_email.google_id}). E-mail ikke opdateret (original_logic).")
            if needs_commit:
                try:
                    db.session.commit(); current_app.logger.info(
                        "Brugerinfo opdateret for eksisterende bruger (original_logic).")
                except Exception as e_commit:
                    db.session.rollback();
                    current_app.logger.error(f"Fejl ved opdatering af brugerinfo (original_logic): {e_commit}")
        else:
            current_app.logger.info(
                f"Ny bruger (original_logic) (Google ID: {google_user_id}) med godkendt e-mail: {user_email_from_google}. Opretter bruger...")
            existing_user_by_email = User.query.filter(User.email.ilike(normalized_email_from_google)).first()
            if existing_user_by_email:
                current_app.logger.error(
                    f"Godkendt e-mail {user_email_from_google} er allerede i databasen med et andet Google ID ({existing_user_by_email.google_id}) end det nuværende ({google_user_id}) (original_logic).")
                flash(
                    "Der opstod et problem med din konto. Kontakt administratoren (fejlkode: EMAIL_GID_MISMATCH_ORIG).",
                    "error")
                return redirect(url_for('main.index'))
            user = User(google_id=google_user_id, name=user_name, email=user_email_from_google)
            db.session.add(user)
            try:
                db.session.commit();
                current_app.logger.info(f"Ny bruger oprettet (original_logic): {user}")
            except Exception as e_commit:
                db.session.rollback();
                current_app.logger.error(
                    f"Fejl ved commit af ny bruger (original_logic): {e_commit}\n{traceback.format_exc()}")
                flash("Fejl: Kunne ikke oprette din brugerkonto (original_logic).", "error");
                return redirect(url_for('main.index'))

        login_user(user, remember=True)
        current_app.logger.info(
            f"Bruger {user.id} ({user.name}) logget ind succesfuldt (original_logic) (e-mail godkendt).")
        flash(f"Velkommen, {user.name}!", "success")
        return redirect(url_for('main.index'))

    except Exception as e:
        current_app.logger.error(
            f"Fejl under Google authorization process (original_logic): {e}\n{traceback.format_exc()}")
        flash(f"Uventet fejl under login (original_logic): {str(e)[:100]}...", "error")
        return redirect(url_for('main.index'))


def logout_original_logic():
    user_id_before = current_user.id if current_user.is_authenticated else 'anonymous'
    logout_user()
    session.clear()
    current_app.logger.info(f"Bruger {user_id_before} logget ud (original_logic).")
    flash("Du er nu logget ud.", "info")
    return redirect(url_for('main.index'))


def generate_audio_original_logic():
    # Sørg for at hente elevenlabs_client korrekt, da den nu er global
    global elevenlabs_client
    if not elevenlabs_client:
        current_app.logger.error("FEJL: ElevenLabs client ikke initialiseret i generate_audio_original_logic.")
        return jsonify({"error": "ElevenLabs client ikke initialiseret."}), 500
    data = request.get_json()
    story_text = data.get('text')
    if not story_text:
        current_app.logger.error("FEJL: Ingen tekst modtaget for lydgenerering.")
        return jsonify({"error": "Ingen tekst modtaget."}), 400
    current_app.logger.info(f"Modtaget anmodning om at generere lyd for tekst: {story_text[:50]}...")
    try:
        voice_id = "gpf7HQVro4L2OVR54kr8"
        current_app.logger.info(f"Anmoder om lyd fra ElevenLabs med stemme: {voice_id}")
        audio_stream = elevenlabs_client.generate(text=story_text, voice=Voice(voice_id=voice_id),
                                                  model='eleven_multilingual_v2')
        current_app.logger.info("Lyd-stream modtaget fra ElevenLabs.")
        return Response(audio_stream, mimetype='audio/mpeg')
    except Exception as e:
        current_app.logger.error(f"Fejl ved kald til ElevenLabs API: {e}\n{traceback.format_exc()}")
        return jsonify({"error": f"Fejl ved generering af lyd: {str(e)}"}), 500


def generate_image_from_story_original_logic():
    data = request.get_json()
    if not data or 'story_text' not in data:
        return jsonify({"error": "Mangler 'story_text' i anmodningen."}), 400
    story_text = data.get('story_text')
    if not story_text.strip():
        return jsonify({"error": "'story_text' må ikke være tom."}), 400
    current_app.logger.info(f"Modtaget anmodning til /generate_image_from_story. Historielængde: {len(story_text)}")

    generated_image_prompt_text = "En illustration af en scene fra historien."
    try:
        current_app.logger.info("Genererer billedprompt med Gemini...")
        gemini_model_for_prompting = genai.GenerativeModel('gemini-1.5-flash-latest')
        # Hele din prompt_for_image_prompt er her...
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
            f"6.  **Klarhed og Orden (Clarity & Order):** Strukturen i den **engelske** prompt du genererer bør generelt være: Subject(s) -> Action -> Setting/Details -> Style.\n"  # Bemærk: Punkt 5 mangler i din originale prompt-tekst, men det er nok en skrivefejl.
            f"7.  **Undgå (Avoid):** Ingen tekst i billedet.\n\n"
            f"DANSK HISTORIE (læs denne for at forstå indholdet, som du så skal basere den engelske billedprompt på):\n{story_text[:2000]}\n\n"
            f"GENERER DEN DETALJEREDE OG SPECIFIKKE **ENGELSKE** VISUELLE PROMPT TIL VERTEX AI IMAGEN NU (følg alle ovenstående instruktioner nøje):"
        )
        response_gemini = gemini_model_for_prompting.generate_content(prompt_for_image_prompt)
        generated_image_prompt_text = response_gemini.text.strip()
        current_app.logger.info(f"Genereret billedprompt: {generated_image_prompt_text}")
    except Exception as e_gemini_prompt:
        current_app.logger.error(f"Fejl under generering af billedprompt med Gemini: {e_gemini_prompt}")

    if not current_app.config.get('GOOGLE_CLOUD_PROJECT_ID'):
        current_app.logger.error("FEJL: GOOGLE_CLOUD_PROJECT_ID er ikke sat i app.config.")
        return jsonify({"error": "Serverkonfigurationsfejl: Projekt ID mangler."}), 500

    current_prompt_to_imagen = generated_image_prompt_text
    try:
        max_retries = 2
        for attempt in range(max_retries):
            try:
                current_app.logger.info(f"Forsøg {attempt + 1} med Imagen. Prompt: {current_prompt_to_imagen[:100]}...")
                if attempt == 1:
                    current_app.logger.info("Modificerer prompt til andet forsøg...")
                    current_prompt_to_imagen += " (different visual style, try cartoonish)"  # Eksempel på ændring
                model_identifier = "imagen-3.0-generate-002"  # Eller hvad du nu bruger
                model = ImageGenerationModel.from_pretrained(model_identifier)
                response_imagen = model.generate_images(prompt=current_prompt_to_imagen, number_of_images=1,
                                                        guidance_scale=30)
                if response_imagen and response_imagen.images:
                    image_obj = response_imagen.images[0]
                    if hasattr(image_obj, '_image_bytes') and image_obj._image_bytes:
                        image_bytes = image_obj._image_bytes
                        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                        image_data_url = f"data:image/png;base64,{image_base64}"
                        current_app.logger.info("Billede genereret succesfuldt.")
                        return jsonify({"message": "Billede genereret!", "image_url": image_data_url,
                                        "image_prompt_used": current_prompt_to_imagen})
                    else:
                        current_app.logger.error(f"FEJL: _image_bytes mangler (forsøg {attempt + 1}).")
                        if attempt == max_retries - 1: raise ValueError("EMPTY_IMAGE_BYTES_ERROR_AFTER_RETRIES")
                else:
                    current_app.logger.error(
                        f"FEJL: Imagen returnerede ingen billeder (forsøg {attempt + 1}). Respons: {response_imagen}")
                    if attempt == max_retries - 1: raise ValueError("EMPTY_IMAGE_LIST_ERROR_AFTER_RETRIES")
                if attempt < max_retries - 1: time.sleep(1.5)
            except Exception as e_attempt:  # Mere generisk for forsøg
                current_app.logger.error(f"Fejl i billedgenereringsforsøg {attempt + 1}: {e_attempt}")
                # Non-retryable logic
                non_retryable = ["quota exceeded", "permission denied", "billing", "does not exist",
                                 "Kunne ikke initialisere"]
                if any(sub in str(e_attempt).lower() for sub in non_retryable) or attempt == max_retries - 1:
                    raise
                if attempt < max_retries - 1: time.sleep(1.5)
        raise ValueError("ALL_RETRIES_FAILED_NO_IMAGE_RETURNED")
    except Exception as e_vertex:
        current_app.logger.error(f"Endelig fejl under billedgenerering: {e_vertex}\n{traceback.format_exc()}")
        user_error_msg = f"Uventet fejl: {str(e_vertex)}"
        # Din brugerfejlhåndtering her...
        if "EMPTY_IMAGE_LIST_ERROR_AFTER_RETRIES" in str(e_vertex) or \
                "EMPTY_IMAGE_BYTES_ERROR_AFTER_RETRIES" in str(e_vertex) or \
                "ALL_RETRIES_FAILED_NO_IMAGE_RETURNED" in str(e_vertex):
            user_error_msg = "Billedgeneratoren kunne ikke skabe et billede. Prøv igen."

        return jsonify({"error": user_error_msg, "image_prompt_used": current_prompt_to_imagen}), 500


# === Opret Database Tabeller ===
def create_tables(target_app):  # Modtager app instans
    with target_app.app_context():  # Bruger den korrekte app context
        print("Checking/Creating database tables...")
        try:
            db.create_all()
        except Exception as e:
            print(f"Error creating tables: {e}");
            print(traceback.format_exc())
        else:
            print("Database tables checked/created successfully.")


# -----------------------------------------------------------------------------
# DEL 4: APP KØRSEL
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    app = create_app()
    create_tables(app)  # Pass app instansen til create_tables
    app.run(debug=True, port=5000, use_reloader=False)  # use_reloader=False tilføjet