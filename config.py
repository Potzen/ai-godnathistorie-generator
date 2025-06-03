import os
import secrets

class Config:
    """
    Grundlæggende konfigurationsklasse for Flask applikationen.
    Indstillinger hentes fra miljøvariabler, hvor det er muligt,
    ellers bruges standardværdier (især relevant for udvikling).
    """

    # Sikkerhedsnøgle for Flask sessions og andre sikkerhedsrelaterede funktioner
    # Det er VIGTIGT at denne holdes hemmelig i produktion.
    # Henter fra miljøvariabel FLASK_SECRET_KEY, ellers genereres en ny.
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(24))

    # Database konfiguration
    # Definerer stien til SQLite databasen.
    # Vi konstruerer stien baseret på rodmappen af applikationen.
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    INSTANCE_PATH = os.path.join(BASEDIR, 'instance')
    DB_PATH = os.path.join(INSTANCE_PATH, 'app.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + DB_PATH
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Google API Nøgle (til Gemini)
    # Hentes fra miljøvariabel GOOGLE_API_KEY.
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

    # Google OAuth 2.0 Klient ID og Hemmelighed (til Login med Google)
    # Hentes fra miljøvariabler.
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

    # ElevenLabs API Nøgle (til Tekst-til-Tale)
    # Hentes fra miljøvariabel ELEVENLABS_API_KEY.
    # ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY')

    # Vertex AI Konfiguration (til Billedgenerering)
    # Hentes fra miljøvariabler.
    GOOGLE_CLOUD_PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT_ID')
    VERTEX_AI_REGION = os.environ.get('VERTEX_AI_REGION', 'us-central1') # Standard til us-central1 hvis ikke sat
    # Stien til GOOGLE_APPLICATION_CREDENTIALS filen håndteres typisk direkte
    # af Google's biblioteker, når miljøvariablen er sat i selve miljøet (f.eks. i WSGI filen på PythonAnywhere).
    # Vi inkluderer den her for fuldstændighedens skyld, men den bruges ikke aktivt til at *sætte* miljøvariablen.
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

    # Liste over godkendte e-mailadresser til login
    # Tilføj de e-mailadresser, der skal have adgang, her.
    # VIGTIGT: Sørg for, at e-mailadresser skrives med små bogstaver for at undgå case-sensitivitets problemer.
    ALLOWED_EMAIL_ADDRESSES = [
        "philipotzen@gmail.com",
        "en.anden.godkendt.email@example.com",
        # Tilføj flere e-mailadresser efter behov
    ]

    # E-mail lister for specifikke brugerroller (Google Login)
    # Brugere på disse lister skal også være i ALLOWED_EMAIL_ADDRESSES
    BASIC_TIER_GOOGLE_EMAILS = [
        # "basic_google_bruger1@gmail.com",
        # "basic_google_bruger2@example.com",
    ]

    PREMIUM_TIER_GOOGLE_EMAILS = [
        # "premium_google_bruger1@gmail.com",
        "philipotzen@gmail.com",  # Eksempel: philipotzen@gmail.com er premium
    ]

    # Validering (valgfrit men god praksis)
    @staticmethod
    def validate_critical_config():
        critical_vars = {
            "SECRET_KEY": Config.SECRET_KEY,
            "SQLALCHEMY_DATABASE_URI": Config.SQLALCHEMY_DATABASE_URI,
            "GOOGLE_API_KEY": Config.GOOGLE_API_KEY,
            "GOOGLE_CLIENT_ID": Config.GOOGLE_CLIENT_ID,
            "GOOGLE_CLIENT_SECRET": Config.GOOGLE_CLIENT_SECRET
            # ELEVENLABS_API_KEY og GOOGLE_CLOUD_PROJECT_ID kan være valgfrie afhængigt af brug
        }
        missing = [name for name, var in critical_vars.items() if var is None]
        if missing:
            raise ValueError(f"Manglende kritiske konfigurationsvariabler: {', '.join(missing)}. Sørg for at miljøvariabler er sat.")

# Her kan du tilføje andre konfigurationsklasser, f.eks. for produktion eller test, hvis nødvendigt.
# class ProductionConfig(Config):
#     DEBUG = False
#
# class DevelopmentConfig(Config):
#     DEBUG = True