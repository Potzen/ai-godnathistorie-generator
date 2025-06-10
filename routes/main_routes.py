from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user
from models import Story
# import uuid # Fjern eller udkommenter denne

# Opret et Blueprint objekt.
# 'main' er navnet på dette blueprint. Det bruges internt af Flask.
# __name__ hjælper Flask med at finde templates og statiske filer relateret til dette blueprint.
main_bp = Blueprint('main', __name__, template_folder='../templates', static_folder='../static') # Tilbage til det oprindelige navn 'main'
# Bemærk: template_folder='../templates' og static_folder='../static' er vigtige,
# fordi disse filer er i en mappe ET NIVEAU OVER 'routes'-mappen.

@main_bp.route('/')
def index():
    current_app.logger.info("Accessing index route via main_bp.")
    logbook_stories = []
    # Hent kun logbogs-historier hvis en bruger er logget ind
    if current_user.is_authenticated:
        logbook_stories = Story.query.filter_by(
            user_id=current_user.id,
            is_log_entry=True
        ).order_by(Story.created_at.desc()).all()

    # Send historierne med til index.html. Listen vil være tom for gæster.
    return render_template('index.html', stories=logbook_stories)

@main_bp.route('/privacy-policy')
def privacy_policy():
    current_app.logger.info("Accessing privacy policy route via main_bp.")
    return render_template('privacy_policy.html')


@main_bp.route('/logbook')
@login_required
def logbook():
    """
    Henter og viser en liste over alle brugerens gemte logbogs-historier.
    """
    current_app.logger.info(f"Bruger {current_user.id} tilgår /logbook.")

    # Hent alle historier for den nuværende bruger, som er markeret som 'is_log_entry'.
    # Sorter dem, så de nyeste vises først.
    stories = Story.query.filter_by(user_id=current_user.id, is_log_entry=True).order_by(Story.created_at.desc()).all()

    current_app.logger.info(f"Fandt {len(stories)} gemte historier for bruger {current_user.id}.")

    # Send listen af historier til en ny template, 'logbook.html'.
    return render_template('logbook.html', stories=stories)