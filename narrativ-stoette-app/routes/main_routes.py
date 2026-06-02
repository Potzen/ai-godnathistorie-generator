from flask import Blueprint, render_template, current_app
from flask_login import current_user
from models import Story

main_bp = Blueprint('main', __name__, template_folder='../templates', static_folder='../static')


def _logbook_stories():
    if current_user.is_authenticated:
        return Story.query.filter_by(
            user_id=current_user.id,
            is_log_entry=True
        ).order_by(Story.created_at.desc()).all()
    return []


@main_bp.route('/')
def index():
    return render_template('index.html', stories=_logbook_stories())


@main_bp.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')
