import os
import logging
import traceback

from flask import Flask, request, jsonify, redirect, url_for

from config import Config
from extensions import db, login_manager, oauth, migrate
from models import User
from services.rag_service import initialize_knowledge_base

import google.generativeai as genai
from google.cloud import aiplatform
import vertexai



logging.basicConfig(level=logging.DEBUG)


def create_app(config_class=Config):
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
    migrate.init_app(app, db)  # Initialiser Flask-Migrate

    login_manager.login_view = 'auth.google_login'
    login_manager.login_message = "Log venligst ind for at bruge denne funktion."
    login_manager.login_message_category = "info"

    @login_manager.unauthorized_handler
    def unauthorized():
        """
        Håndterer uautoriserede forsøg på at tilgå beskyttede routes.
        Returnerer JSON-fejl for API-kald (forventer JSON), ellers redirect.
        """
        # Hvis requestet forventer JSON (typisk et API-kald fra JavaScript)
        if request.accept_mimetypes.accept_json and \
                not request.accept_mimetypes.accept_html:
            app.logger.warning(f"Uautoriseret API-kald til: {request.endpoint} fra IP: {request.remote_addr}")
            return jsonify(error="Login påkrævet for at tilgå denne ressource.",
                           login_url=url_for('auth.google_login')), 401

        # For almindelige browser-requests, fortsæt med standard omdirigering
        app.logger.info(f"Uautoriseret browser-kald til: {request.endpoint}. Omdirigerer til login.")
        return redirect(url_for(login_manager.login_view))

    client_id_found = app.config.get('GOOGLE_CLIENT_ID')
    client_secret_found = app.config.get('GOOGLE_CLIENT_SECRET')

    if client_id_found and client_secret_found:
        oauth.register(
            name='google',
            server_metadata_url=app.config.get("GOOGLE_DISCOVERY_URL"),
            client_kwargs={'scope': 'openid email profile'}
        )
        app.logger.info("OAuth Google provider registreret succesfuldt.")
    else:
        app.logger.warning("OAuth Google provider IKKE registreret pga. manglende GOOGLE_CLIENT_ID/SECRET.")

    from routes.main_routes import main_bp
    from routes.auth_routes import auth_bp
    from routes.story_routes import story_bp
    from routes.narrative_routes import narrative_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(story_bp, url_prefix='/story')
    app.register_blueprint(narrative_bp)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except Exception as e:
            app.logger.error(f"Fejl ved indlæsning af bruger {user_id}: {e}")
            return None

    with app.app_context():
        try:
            initialize_knowledge_base()
            app.logger.info("RAG Videnbase initialiseret succesfuldt.")
        except Exception as e:
            app.logger.error(
                f"FEJL under initialisering af RAG Videnbase: {e}\n{traceback.format_exc()}")

    app.logger.info("Flask app oprettelse fuldført.")
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000, use_reloader=False)