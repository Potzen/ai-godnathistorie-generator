from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user
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
    current_app.logger.info("Accessing landing page.")
    return render_template('landing.html')


@main_bp.route('/skole')
def skole():
    current_app.logger.info("Accessing /skole.")
    return render_template('skole.html', stories=_logbook_stories())


@main_bp.route('/hygge')
def hygge():
    current_app.logger.info("Accessing /hygge.")
    return render_template('hygge.html')


@main_bp.route('/stoette')
def stoette():
    current_app.logger.info("Accessing /stoette.")
    return render_template('stoette.html', stories=_logbook_stories())


@main_bp.route('/privacy-policy')
def privacy_policy():
    current_app.logger.info("Accessing privacy policy route via main_bp.")
    return render_template('privacy_policy.html')


@main_bp.route('/logbook')
@login_required
def logbook():
    stories = Story.query.filter_by(user_id=current_user.id, is_log_entry=True).order_by(Story.created_at.desc()).all()
    return render_template('logbook.html', stories=stories)
