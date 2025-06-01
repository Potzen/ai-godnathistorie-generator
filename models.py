# Fil: models.py
from extensions import db
from flask_login import UserMixin
# Importer til kodeordshåndtering - flyttes ind i metoderne for at undgå cirkulær import ved opstart
# from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    # Fortæl SQLAlchemy at det er okay at genbruge/udvide en eksisterende tabeldefinition
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)

    # Nye felter for rolle og kodeord
    role = db.Column(db.String(50), nullable=False, default='free')  # Roller: 'free', 'basic', 'premium'
    password_hash = db.Column(db.String(256), nullable=True)  # Nullable for Google-brugere

    def set_password(self, password):
        from werkzeug.security import generate_password_hash # Import her for at undgå potentielle opstartsproblemer
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash # Import her
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User id={self.id} name={self.name} email={self.email} role={self.role}>' # Tilføjet role til repr