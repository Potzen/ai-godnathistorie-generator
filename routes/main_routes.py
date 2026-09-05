from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user
from extensions import db
from models import Story

main_bp = Blueprint('main', __name__, template_folder='../templates', static_folder='../static')


def _has_logbook_stories():
    """Har den aktuelle bruger mindst én gemt logbogs-historie?

    Siderne bruger kun dette til at vælge mellem "Henter historier..." og
    "Du har endnu ikke gemt nogen historier" - selve listen hentes bagefter
    via /api/logbook/filter. Derfor stiller vi et EXISTS-spørgsmål i stedet
    for at hente alle rækker med fuldt historieindhold ved hver sidevisning.
    """
    if not current_user.is_authenticated:
        return False
    return db.session.query(
        Story.query.filter_by(user_id=current_user.id, is_log_entry=True).exists()
    ).scalar()


@main_bp.route('/')
def index():
    return render_template('landing.html')


@main_bp.route('/skole')
def skole():
    return render_template('skole.html', stories=_has_logbook_stories())


@main_bp.route('/hjemmelaesning')
def hjemmelaesning():
    """Hjemmelæsning - historier til den daglige læsning derhjemme.

    Hed tidligere "Hygge". Navnet er ændret, fordi modulet ikke længere kun
    er godnathistorier: det viser ugens fokus fra skolen, så det barnet
    øver i klassen, er det, der øves ved sengekanten.
    """
    return render_template('hjemmelaesning.html')


@main_bp.route('/hygge')
def hygge():
    """Gammelt navn. Bogmærker og delte links skal blive ved at virke."""
    return redirect(url_for('main.hjemmelaesning'), code=301)


@main_bp.route('/stoette')
def stoette():
    return render_template('stoette.html', stories=_has_logbook_stories())


@main_bp.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')


@main_bp.route('/logbook')
def logbook():
    """Logbogen har ikke længere sin egen side.

    Den vises nu indlejret på /skole og /stoette. Ruten pegede på en
    'logbook.html', der ikke findes i templates/, så den fejlede med 500.
    Vi sender i stedet brugeren hen, hvor logbogen faktisk er.
    """
    return redirect(url_for('main.skole'))
