from flask import Blueprint, render_template, current_app
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
    return render_template('index.html')

@main_bp.route('/privacy-policy')
def privacy_policy():
    current_app.logger.info("Accessing privacy policy route via main_bp.")
    return render_template('privacy_policy.html')