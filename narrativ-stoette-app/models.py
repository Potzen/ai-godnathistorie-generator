from extensions import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)

    stories = db.relationship('Story', backref='author', lazy='dynamic')
    profiles = db.relationship('ChildProfile', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User id={self.id} name={self.name} email={self.email}>'


class Story(db.Model):
    __tablename__ = 'story'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    source = db.Column(db.String(50), nullable=True)
    is_log_entry = db.Column(db.Boolean, default=False, nullable=False)

    series_part = db.Column(db.Integer, default=1)
    strategy_used = db.Column(db.String(50), nullable=True)
    parent_story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=True)
    root_story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=True)

    children_stories = db.relationship(
        'Story',
        backref=db.backref('parent_story', remote_side=[id]),
        lazy='dynamic',
        foreign_keys=[parent_story_id]
    )

    problem_name = db.Column(db.String(150), nullable=True)
    problem_category = db.Column(db.String(150), nullable=True)
    problem_influence = db.Column(db.Text, nullable=True)
    unique_outcome = db.Column(db.Text, nullable=True)
    discovered_method_name = db.Column(db.String(150), nullable=True)
    strength_type = db.Column(db.String(150), nullable=True)
    discovered_method_steps = db.Column(db.Text, nullable=True)
    child_values = db.Column(db.Text, nullable=True)
    support_system = db.Column(db.Text, nullable=True)

    ai_summary = db.Column(db.Text, nullable=True)
    user_notes = db.Column(db.Text, nullable=True)
    progress_before = db.Column(db.Integer, nullable=True)
    progress_after = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f'<Story id={self.id} title="{self.title}" user_id={self.user_id}>'


class ChildProfile(db.Model):
    __tablename__ = 'child_profile'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    strengths = db.relationship(
        'ProfileAttribute', lazy='dynamic', cascade='all, delete-orphan',
        backref='profile',
        primaryjoin="and_(ChildProfile.id==ProfileAttribute.profile_id, ProfileAttribute.type=='strength')"
    )
    values = db.relationship(
        'ProfileAttribute', lazy='dynamic', cascade='all, delete-orphan',
        primaryjoin="and_(ChildProfile.id==ProfileAttribute.profile_id, ProfileAttribute.type=='value')",
        overlaps='profile,strengths'
    )
    motivations = db.relationship(
        'ProfileAttribute', lazy='dynamic', cascade='all, delete-orphan',
        primaryjoin="and_(ChildProfile.id==ProfileAttribute.profile_id, ProfileAttribute.type=='motivation')",
        overlaps='profile,strengths,values'
    )
    reactions = db.relationship(
        'ProfileAttribute', lazy='dynamic', cascade='all, delete-orphan',
        primaryjoin="and_(ChildProfile.id==ProfileAttribute.profile_id, ProfileAttribute.type=='reaction')",
        overlaps='profile,strengths,values,motivations'
    )
    relations = db.relationship('ProfileRelation', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ChildProfile id={self.id} name="{self.name}">'


class ProfileAttribute(db.Model):
    __tablename__ = 'profile_attribute'

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('child_profile.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<ProfileAttribute type="{self.type}" content="{self.content[:30]}">'


class ProfileRelation(db.Model):
    __tablename__ = 'profile_relation'

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('child_profile.id'), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    relation_type = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f'<ProfileRelation name="{self.name}" type="{self.relation_type}">'
