# Fil: models.py
from extensions import db
from flask_login import UserMixin
from datetime import datetime


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

    # Relation til historier
    stories = db.relationship('Story', backref='author', lazy='dynamic')

    def set_password(self, password):
        from werkzeug.security import generate_password_hash  # Import her for at undgå potentielle opstartsproblemer
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash  # Import her
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User id={self.id} name={self.name} email={self.email} role={self.role}>'  # Tilføjet role til repr


class Story(db.Model):
    __tablename__ = 'story'

    # --- KERNE DATA (EKSISTERENDE + NYE) ---
    # Rationale: De grundlæggende felter for enhver historie.
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- NYE FELTER TIL LOGBOG & TERAPEUTISK SPORING ---

    # KATEGORISERING & RELATIONER
    # Rationale: For at kunne filtrere og skabe serier af historier.
    source = db.Column(db.String(50),
                       nullable=True)  # F.eks. 'Narrativ Støtte', 'Højtlæsning'. Giver mulighed for filtrering.
    is_log_entry = db.Column(db.Boolean, default=False,
                             nullable=False)  # Kritisk flag for at adskille rå historier fra dokumenterede "missioner".

    # --- NYE FELTER TIL SERIE-HÅNDTERING ---
    series_part = db.Column(db.Integer, default=1)  # Sporer det globale "Del X"-nummer i en serie.
    strategy_used = db.Column(db.String(50), nullable=True)  # Gemmer f.eks. "Dyk Dybere" eller "Flyv Højere".

    parent_story_id = db.Column(db.Integer, db.ForeignKey('story.id'),
                                nullable=True)  # Link til den direkte forælder-historie.
    root_story_id = db.Column(db.Integer, db.ForeignKey('story.id'),
                              nullable=True)  # Link til den absolutte moderhistorie i serien.
    # -----------------------------------------

    # Relation for at finde børnehistorier nemt
    children_stories = db.relationship('Story', backref=db.backref('parent_story', remote_side=[id]),
                                       lazy='dynamic', foreign_keys=[parent_story_id])

    # AI-ASSISTERET DOKUMENTATION
    # Rationale: Disse felter gemmer de strukturerede "guldkorn" fra den narrative analyse. De udgør kernen i dokumentationen.
    problem_name = db.Column(db.String(150), nullable=True)  # Eksternalisering af problemet, f.eks. "Vrede-vulkanen".
    problem_category = db.Column(db.String(150), nullable=True)  # F.eks. "Følelse", "Social Udfordring"
    problem_influence = db.Column(db.Text, nullable=True)  # Hvordan problemet konkret påvirker barnet.
    unique_outcome = db.Column(db.Text, nullable=True)  # Beskrivelsen af "glimtet" - barnets succesfulde handling.
    discovered_method_name = db.Column(db.String(150), nullable=True)  # Navnet på den metode/styrke, der blev brugt.
    strength_type = db.Column(db.String(150), nullable=True)  # NYT FELT: F.eks. "Kreativitet", "Empati", "Logik"
    discovered_method_steps = db.Column(db.Text, nullable=True)  # En trin-for-trin guide til metoden.
    child_values = db.Column(db.Text, nullable=True)  # De underliggende værdier, barnet forsvarede (f.eks. "Mod, Venskab").
    support_system = db.Column(db.Text, nullable=True)  # De "vidner" eller hjælpere, der var til stede.

    # BRUGER-INPUT & METADATA
    # Rationale: Giver brugeren direkte ejerskab og mulighed for at tilføje kvalitativ og kvantitativ data.
    ai_summary = db.Column(db.Text, nullable=True)  # Gemmer det AI-genererede resumé (både standard og progression).
    user_notes = db.Column(db.Text, nullable=True)  # Forælderens/barnets egne, løbende refleksioner.
    progress_before = db.Column(db.Integer, nullable=True)  # Vurdering af problemets styrke (1-10) før historien.
    progress_after = db.Column(db.Integer, nullable=True)  # Vurdering efter. Giver målbar data.

    def __repr__(self):
        return f'<Story id={self.id} title="{self.title}" user_id={self.user_id} is_log_entry={self.is_log_entry}>'