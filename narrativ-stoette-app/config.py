import os
import secrets


class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(24))

    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    INSTANCE_PATH = os.path.join(BASEDIR, 'instance')
    DB_PATH = os.path.join(INSTANCE_PATH, 'app.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + DB_PATH
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

    GOOGLE_CLOUD_PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT_ID')
    VERTEX_AI_REGION = os.environ.get('VERTEX_AI_REGION', 'us-central1')
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

    ALLOWED_EMAIL_ADDRESSES = [
        email.strip()
        for email in os.environ.get('ALLOWED_EMAILS', 'philipotzen@gmail.com').split(',')
        if email.strip()
    ]

    @staticmethod
    def validate_critical_config():
        critical_vars = {
            "SECRET_KEY": Config.SECRET_KEY,
            "SQLALCHEMY_DATABASE_URI": Config.SQLALCHEMY_DATABASE_URI,
            "GOOGLE_API_KEY": Config.GOOGLE_API_KEY,
            "GOOGLE_CLIENT_ID": Config.GOOGLE_CLIENT_ID,
            "GOOGLE_CLIENT_SECRET": Config.GOOGLE_CLIENT_SECRET,
        }
        missing = [name for name, var in critical_vars.items() if var is None]
        if missing:
            raise ValueError(f"Manglende kritiske konfigurationsvariabler: {', '.join(missing)}")
