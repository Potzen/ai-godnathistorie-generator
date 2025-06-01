# Fil: extensions.py
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth # Importer OAuth her

db = SQLAlchemy()
login_manager = LoginManager()
oauth = OAuth() # Definer oauth objektet her
migrate = Migrate()