# Fil: models.py
from extensions import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    # Fortæl SQLAlchemy at det er okay at genbruge/udvide en eksisterende tabeldefinition
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)

    def __repr__(self):
        return f'<User id={self.id} name={self.name} email={self.email}>'
