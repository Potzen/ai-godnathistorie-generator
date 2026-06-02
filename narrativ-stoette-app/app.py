import os
import logging
import traceback

from flask import Flask, request, jsonify, redirect, url_for
from config import Config
from extensions import db, login_manager, oauth, migrate
from models import User
from services.rag_service import initialize_knowledge_base

import google.generativeai as genai
import vertexai
from google.cloud import aiplatform

logging.basicConfig(level=logging.DEBUG)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    try:
        config_class.validate_critical_config()
        app.logger.info("Konfiguration valideret.")
    except ValueError as e:
        app.logger.error(f"Konfigurationsfejl: {e}")

    if app.config.get('GOOGLE_API_KEY'):
        genai.configure(api_key=app.config['GOOGLE_API_KEY'])
        app.logger.info("Google AI API Key konfigureret.")
    else:
        app.logger.warning("GOOGLE_API_KEY mangler – Gemini vil ikke virke.")

    if app.config.get('GOOGLE_CLOUD_PROJECT_ID'):
        try:
            aiplatform.init(
                project=app.config['GOOGLE_CLOUD_PROJECT_ID'],
                location=app.config['VERTEX_AI_REGION']
            )
            vertexai.init(
                project=app.config['GOOGLE_CLOUD_PROJECT_ID'],
                location=app.config['VERTEX_AI_REGION']
            )
            app.logger.info("Vertex AI initialiseret.")
        except Exception as e:
            app.logger.error(f"Vertex AI initialiseringsfejl: {e}")
    else:
        app.logger.warning("GOOGLE_CLOUD_PROJECT_ID mangler – billedgenerering vil ikke virke.")

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    oauth.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login_page'
    login_manager.login_message = "Log venligst ind for at bruge denne funktion."
    login_manager.login_message_category = "info"

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify(error="Login påkrævet.", login_url=url_for('auth.login_page')), 401
        return redirect(url_for(login_manager.login_view))

    if app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET'):
        oauth.register(
            name='google',
            server_metadata_url=app.config['GOOGLE_DISCOVERY_URL'],
            client_kwargs={'scope': 'openid email profile'}
        )
        app.logger.info("Google OAuth provider registreret.")
    else:
        app.logger.warning("Google OAuth ikke registreret – mangler CLIENT_ID/SECRET.")

    from routes.auth_routes import auth_bp
    from routes.main_routes import main_bp
    from routes.narrative_routes import narrative_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(narrative_bp)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    with app.app_context():
        try:
            initialize_knowledge_base()
            app.logger.info("RAG videnbase initialiseret.")
        except Exception as e:
            app.logger.error(f"RAG initialiseringsfejl: {e}\n{traceback.format_exc()}")

    app.logger.info("App klar.")
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001, use_reloader=False)
