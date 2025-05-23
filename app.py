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
from extensions import db, login_manager, oauth  # <--- DENNE LINJE ER VIGTIG!
from models import User
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
# db = SQLAlchemy()
# login_manager = LoginManager()
# oauth = OAuth()
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
    from routes.auth_routes import auth_bp # Eksisterende
    from routes.story_routes import story_bp

    if 'main' not in app.blueprints:
        app.register_blueprint(main_bp)
        app.logger.info("Blueprint 'main_bp' registreret.")
    else:
        app.logger.info("Blueprint 'main_bp' var allerede registreret (undlod gen-registrering).")

    if 'auth' not in app.blueprints:
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.logger.info("Blueprint 'auth_bp' registreret med prefix /auth.")
    else:
        app.logger.info("Blueprint 'auth_bp' var allerede registreret.")

    if 'story' not in app.blueprints:
        app.register_blueprint(story_bp, url_prefix='/story')  # Vi tilføjer et prefix for story routes
        app.logger.info("Blueprint 'story_bp' registreret med prefix /story.")
    else:
        app.logger.info("Blueprint 'story_bp' var allerede registreret.")

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