# Fil: routes/auth_routes.py
from flask import Blueprint, redirect, url_for, flash, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db, User # Vi beholder db og User fra app indtil videre
# oauth importeres ikke direkte her længere


auth_bp = Blueprint('auth', __name__, template_folder='../templates', static_folder='../static')


@auth_bp.route('/login')
def google_login():
    # Få adgang til den specifikke 'google' oauth client via current_app
    google_oauth_client = current_app.extensions.get('authlib.integrations.flask_client', {}).get('google')

    if not google_oauth_client: # Tjek om klienten overhovedet findes
        current_app.logger.error("Google OAuth klient ikke fundet via current_app.extensions.")
        flash("Google login er ikke konfigureret korrekt på serveren (klient mangler).", "error")
        return redirect(url_for('main.index'))

    # Authlib's 'google' client objekt har direkte metoder som 'authorize_redirect'
    redirect_uri = url_for('auth.google_authorize', _external=True)
    current_app.logger.info(f"Redirecting to Google for login. Callback URI: {redirect_uri}")
    return google_oauth_client.authorize_redirect(redirect_uri) # <--- BRUG google_oauth_client

    redirect_uri = url_for('auth.google_authorize', _external=True)
    current_app.logger.info(f"Redirecting to Google for login. Callback URI: {redirect_uri}")
    return oauth.google.authorize_redirect(redirect_uri)


# Fil: routes/auth_routes.py
# ... (andre imports og auth_bp definition øverst) ...

@auth_bp.route('/authorize')
def google_authorize():
    current_app.logger.info("Received callback from Google.")

    # Få adgang til den specifikke 'google' oauth client via current_app.extensions
    google_oauth_client = current_app.extensions.get('authlib.integrations.flask_client', {}).get('google')

    if not google_oauth_client:
        current_app.logger.error("Google OAuth klient ikke fundet via current_app.extensions i authorize.")
        flash("Google login er ikke konfigureret korrekt på serveren (authorize klient mangler).", "error")
        return redirect(url_for('main.index'))  # main.index peger på index i main_bp

    try:
        token = google_oauth_client.authorize_access_token()  # Brug den hentede klient
        if not token:
            current_app.logger.warning("Login mislykkedes: Kunne ikke autorisere access token.")
            flash("Login mislykkedes (token).", "error")
            return redirect(url_for('main.index'))

        current_app.logger.info("Access token modtaget. Henter brugerinfo...")
        user_info = google_oauth_client.userinfo(token=token)  # Brug den hentede klient
        if not user_info:
            current_app.logger.warning("Login mislykkedes: Kunne ikke hente brugerinfo.")
            flash("Login mislykkedes (userinfo).", "error")
            return redirect(url_for('main.index'))

        current_app.logger.info(f"Brugerinfo modtaget: {user_info}")
        google_user_id = user_info.get('sub')
        user_email = user_info.get('email')
        user_name = user_info.get('name')

        if not google_user_id:
            current_app.logger.warning("Login mislykkedes: Google user ID ('sub') ikke fundet.")
            flash("Login mislykkedes (ID).", "error")
            return redirect(url_for('main.index'))

        user = User.query.filter_by(google_id=google_user_id).first()
        if user:
            current_app.logger.info(f"Eksisterende bruger fundet: {user}")
            needs_commit = False
            if user.name != user_name:
                user.name = user_name
                needs_commit = True
            if user.email != user_email:
                existing_email_user = User.query.filter(User.email == user_email,
                                                        User.google_id != google_user_id).first()
                if not existing_email_user:
                    user.email = user_email
                    needs_commit = True
                else:
                    current_app.logger.warning(
                        f"E-mail {user_email} er allerede i brug af en anden Google konto ({existing_email_user.google_id}). Kan ikke opdatere for bruger {google_user_id}.")
            if needs_commit:
                try:
                    db.session.commit()
                    current_app.logger.info("Brugerinfo opdateret.")
                except Exception as e_commit:
                    db.session.rollback()
                    current_app.logger.error(f"Fejl ved opdatering af brugerinfo: {e_commit}")
        else:
            current_app.logger.info(f"Ny bruger detekteret. Opretter bruger...")
            existing_email_user = User.query.filter_by(email=user_email).first()
            if existing_email_user:
                current_app.logger.warning(
                    f"Ny bruger forsøgte at registrere med e-mail {user_email}, som allerede er i brug af google_id {existing_email_user.google_id}.")
                flash(
                    "Denne e-mailadresse er allerede registreret. Log venligst ind med den korrekte Google konto eller kontakt support.",
                    "error")
                return redirect(url_for('main.index'))

            user = User(google_id=google_user_id, name=user_name, email=user_email)
            db.session.add(user)
            try:
                db.session.commit()
                current_app.logger.info(f"Ny bruger oprettet: {user}")
            except Exception as e_commit:
                db.session.rollback()
                current_app.logger.error(f"Fejl ved commit af ny bruger: {e_commit}\n{traceback.format_exc()}")
                flash("Fejl: Kunne ikke oprette bruger.", "error")
                return redirect(url_for('main.index'))

        login_user(user, remember=True)
        current_app.logger.info(f"Bruger {user.id} ({user.name}) logget ind succesfuldt.")
        flash(f"Velkommen, {user.name}!", "success")
        return redirect(url_for('main.index'))

    except Exception as e:
        current_app.logger.error(f"Fejl under Google authorization process: {e}\n{traceback.format_exc()}")
        # Begræns længden af fejlmeddelelsen for at undgå for lange flash-beskeder
        flash(f"Uventet fejl under login: {str(e)[:100]}...", "error")
        return redirect(url_for('main.index'))


@auth_bp.route('/logout')
@login_required
def logout():
    user_id_before = current_user.id if current_user.is_authenticated else 'anonymous'
    logout_user()
    # session.clear() # Normalt ikke nødvendigt, logout_user håndterer det meste. Kan genindsættes hvis specifikke session data skal fjernes.
    current_app.logger.info(f"Bruger {user_id_before} logget ud.")
    flash("Du er nu logget ud.", "info")
    return redirect(url_for('main.index'))