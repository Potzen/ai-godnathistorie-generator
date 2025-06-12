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

class ChildProfile(db.Model):
    __tablename__ = 'child_profile'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # potzen/ai-godnathistorie-generator/ai-godnathistorie-generator-5ffa7696e20a294c8648c9db4a2cb60980e2a54e/models.py
    # One-to-Many relationer til profilens attributter
    # Den første relation etablerer et backref, som de andre skal overlappe.
    strengths = db.relationship('ProfileAttribute', lazy='dynamic', cascade="all, delete-orphan",
                                backref='profile',
                                primaryjoin="and_(ChildProfile.id==ProfileAttribute.profile_id, ProfileAttribute.type=='strength')")

    # De følgende relationer overlapper den første for at undgå advarsler.
    values = db.relationship('ProfileAttribute', lazy='dynamic', cascade="all, delete-orphan",
                             primaryjoin="and_(ChildProfile.id==ProfileAttribute.profile_id, ProfileAttribute.type=='value')",
                             overlaps="profile,strengths")

    motivations = db.relationship('ProfileAttribute', lazy='dynamic', cascade="all, delete-orphan",
                                  primaryjoin="and_(ChildProfile.id==ProfileAttribute.profile_id, ProfileAttribute.type=='motivation')",
                                  overlaps="profile,strengths,values")

    reactions = db.relationship('ProfileAttribute', lazy='dynamic', cascade="all, delete-orphan",
                                primaryjoin="and_(ChildProfile.id==ProfileAttribute.profile_id, ProfileAttribute.type=='reaction')",
                                overlaps="profile,strengths,values,motivations")

    # Denne relation peger på en anden tabel ('profile_relation') og behøver derfor ikke overlaps.
    relations = db.relationship('ProfileRelation', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<ChildProfile id={self.id} name="{self.name}" user_id={self.user_id}>'

class ProfileAttribute(db.Model):
    __tablename__ = 'profile_attribute'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('child_profile.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'strength', 'value', 'motivation', 'reaction'
    content = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<ProfileAttribute id={self.id} type="{self.type}" content="{self.content[:30]}">'

class ProfileRelation(db.Model):
    __tablename__ = 'profile_relation'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('child_profile.id'), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    relation_type = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f'<ProfileRelation id={self.id} name="{self.name}" type="{self.relation_type}">'