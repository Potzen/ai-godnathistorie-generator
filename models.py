import secrets
from extensions import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

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
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # --- NYE FELTER TIL LOGBOG & TERAPEUTISK SPORING ---

    # KATEGORISERING & RELATIONER
    # Rationale: For at kunne filtrere og skabe serier af historier.
    source = db.Column(db.String(50),
                       nullable=True)  # F.eks. 'Narrativ Støtte', 'Højtlæsning'. Giver mulighed for filtrering.
    is_log_entry = db.Column(db.Boolean, default=False,
                             nullable=False, index=True)  # Kritisk flag for at adskille rå historier fra dokumenterede "missioner".

    # --- NYE FELTER TIL SERIE-HÅNDTERING ---
    series_part = db.Column(db.Integer, default=1)  # Sporer det globale "Del X"-nummer i en serie.
    strategy_used = db.Column(db.String(50), nullable=True)  # Gemmer f.eks. "Dyk Dybere" eller "Flyv Højere".

    parent_story_id = db.Column(db.Integer, db.ForeignKey('story.id'),
                                nullable=True, index=True)  # Link til den direkte forælder-historie.
    root_story_id = db.Column(db.Integer, db.ForeignKey('story.id'),
                              nullable=True, index=True)  # Link til den absolutte moderhistorie i serien.
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
    lix_score_stored = db.Column(db.Integer, nullable=True)  # LIX-score gemt ved generering i Læsehesten.

    def __repr__(self):
        return f'<Story id={self.id} title="{self.title}" user_id={self.user_id} is_log_entry={self.is_log_entry}>'

class ChildProfile(db.Model):
    __tablename__ = 'child_profile'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    profile_id = db.Column(db.Integer, db.ForeignKey('child_profile.id'), nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False)  # 'strength', 'value', 'motivation', 'reaction'
    content = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<ProfileAttribute id={self.id} type="{self.type}" content="{self.content[:30]}">'

class ProfileRelation(db.Model):
    __tablename__ = 'profile_relation'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('child_profile.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=True)
    relation_type = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f'<ProfileRelation id={self.id} name="{self.name}" type="{self.relation_type}">'


class Classroom(db.Model):
    __tablename__ = 'classroom'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    invite_code = db.Column(db.String(8), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    teacher = db.relationship('User', backref='classrooms')
    members = db.relationship('ClassroomStudent', backref='classroom', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Classroom id={self.id} name="{self.name}" teacher_id={self.teacher_id}>'

    @staticmethod
    def generate_invite_code():
        while True:
            code = secrets.token_urlsafe(6)[:8].upper()
            if not Classroom.query.filter_by(invite_code=code).first():
                return code


class ClassroomStudent(db.Model):
    __tablename__ = 'classroom_student'
    id = db.Column(db.Integer, primary_key=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False, index=True)
    student_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('User', backref='classroom_memberships')
    __table_args__ = (db.UniqueConstraint('classroom_id', 'student_user_id'),)

    def __repr__(self):
        return f'<ClassroomStudent classroom_id={self.classroom_id} student_id={self.student_user_id}>'


class QuizResult(db.Model):
    __tablename__ = 'quiz_result'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=True, index=True)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False, default=4)
    answers_json = db.Column(db.Text, nullable=True)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='quiz_results')
    story = db.relationship('Story', backref='quiz_results')

    def __repr__(self):
        return f'<QuizResult id={self.id} user_id={self.user_id} score={self.score}/{self.total_questions}>'