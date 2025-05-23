# Fil: routes/auth_routes.py
from flask import Blueprint, redirect, url_for, flash, current_app, session
import traceback
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db  # Importerer db fra extensions
from models import User    # Importerer User fra models (hvis du har oprettet models.py)


auth_bp = Blueprint('auth', __name__, template_folder='../templates', static_folder='../static')


@auth_bp.route('/login')
def google_login():
    # Få adgang til den specifikke 'google' oauth client via current_app
    authlib_flask_client = current_app.extensions.get('authlib.integrations.flask_client')

    google_oauth_client = None
    if authlib_flask_client:
        try:
            google_oauth_client = authlib_flask_client.google
        except AttributeError:
            current_app.logger.error("Google OAuth klient ('google') ikke fundet som attribut på authlib_flask_client.")
            flash("Google login er ikke konfigureret korrekt på serveren (klient-attribut mangler).", "error")
            return redirect(url_for('main.index'))
    else:
        current_app.logger.error(
            "Authlib Flask Client ('authlib.integrations.flask_client') ikke fundet i current_app.extensions.")
        flash("Google login er ikke konfigureret korrekt på serveren (authlib klient mangler).", "error")
        return redirect(url_for('main.index'))

    if not google_oauth_client:
        current_app.logger.error("Google OAuth klient ikke fundet eller kunne ikke hentes.")
        flash("Google login er ikke konfigureret korrekt på serveren (klient mangler efter tjek).", "error")
        return redirect(url_for('main.index'))

    redirect_uri = url_for('auth.google_authorize', _external=True)
    current_app.logger.info(f"Redirecting to Google for login. Callback URI: {redirect_uri}")
    return google_oauth_client.authorize_redirect(redirect_uri)


@auth_bp.route('/authorize')
def google_authorize():
    current_app.logger.info("Received callback from Google.")
    google_oauth_client = current_app.extensions.get('authlib.integrations.flask_client', {}).get('google')

    if not google_oauth_client:
        current_app.logger.error("Google OAuth klient ikke fundet via current_app.extensions i authorize.")
        flash("Google login er ikke konfigureret korrekt på serveren (authorize klient mangler).", "error")
        return redirect(url_for('main.index'))

    try:
        token = google_oauth_client.authorize_access_token()
        if not token:
            current_app.logger.warning("Login mislykkedes: Kunne ikke autorisere access token.")
            flash("Login mislykkedes (token).", "error")
            return redirect(url_for('main.index'))

        current_app.logger.info("Access token modtaget. Henter brugerinfo...")
        user_info = google_oauth_client.userinfo(token=token)
        if not user_info:
            current_app.logger.warning("Login mislykkedes: Kunne ikke hente brugerinfo.")
            flash("Login mislykkedes (userinfo).", "error")
            return redirect(url_for('main.index'))

        current_app.logger.info(f"Brugerinfo modtaget: {user_info}")
        google_user_id = user_info.get('sub')
        user_email_from_google = user_info.get('email') # Gem e-mail fra Google
        user_name = user_info.get('name')

        if not google_user_id:
            current_app.logger.warning("Login mislykkedes: Google user ID ('sub') ikke fundet.")
            flash("Login mislykkedes (ID).", "error")
            return redirect(url_for('main.index'))

        if not user_email_from_google: # Vigtigt at vi har en e-mail at tjekke mod
            current_app.logger.warning(f"Login mislykkedes: Ingen e-mail modtaget fra Google for bruger {google_user_id}.")
            flash("Login mislykkedes: Kunne ikke hente din e-mailadresse fra Google.", "error")
            return redirect(url_for('main.index'))

        # --- NYT: Tjek om e-mailen er på den godkendte liste ---
        # Gør sammenligningen case-insensitive ved at konvertere begge til små bogstaver
        normalized_email_from_google = user_email_from_google.lower()
        allowed_emails_lower = [email.lower() for email in current_app.config.get('ALLOWED_EMAIL_ADDRESSES', [])]

        if normalized_email_from_google not in allowed_emails_lower:
            current_app.logger.warning(f"Login forsøg fra ikke-godkendt e-mail: {user_email_from_google} (Google ID: {google_user_id}).")
            flash("Din e-mailadresse har ikke adgang til denne applikation. Kontakt venligst administratoren.", "error")
            return redirect(url_for('main.index'))
        # --- SLUT PÅ NYT TJEK ---

        # Fortsæt med at finde eller oprette brugeren, nu hvor vi ved, e-mailen er godkendt
        user = User.query.filter_by(google_id=google_user_id).first()
        if user: # Bruger med dette Google ID findes allerede
            current_app.logger.info(f"Eksisterende bruger (baseret på Google ID) fundet: {user} for e-mail {normalized_email_from_google}")
            # Opdater navn og e-mail hvis de har ændret sig hos Google,
            # men kun hvis e-mailen ikke konflikter med en anden eksisterende bruger.
            needs_commit = False
            if user.name != user_name:
                user.name = user_name
                needs_commit = True
            if user.email.lower() != normalized_email_from_google:
                # Tjek om den nye e-mail (fra Google) allerede er i brug af en *anden* bruger
                conflicting_user_by_email = User.query.filter(User.email.ilike(normalized_email_from_google), User.google_id != google_user_id).first()
                if not conflicting_user_by_email:
                    user.email = user_email_from_google # Opdater til den e-mail Google sender
                    needs_commit = True
                else:
                    current_app.logger.warning(f"Bruger {google_user_id}s Google e-mail ({user_email_from_google}) er allerede i brug af en anden bruger ({conflicting_user_by_email.google_id}). E-mail ikke opdateret.")

            if needs_commit:
                try:
                    db.session.commit()
                    current_app.logger.info("Brugerinfo opdateret for eksisterende bruger.")
                except Exception as e_commit:
                    db.session.rollback()
                    current_app.logger.error(f"Fejl ved opdatering af brugerinfo for eksisterende bruger: {e_commit}")

        else: # Ny bruger (Google ID ikke set før), men e-mailen ER på godkendt liste
              # Vi skal nu oprette brugeren.
            current_app.logger.info(f"Ny bruger (Google ID: {google_user_id}) med godkendt e-mail: {user_email_from_google}. Opretter bruger...")

            # Ekstra sikkerhed: Tjek om e-mailen (som vi ved er godkendt) allerede er knyttet til en *anden* Google ID i vores DB
            # Dette burde ikke ske ofte, hvis Google ID er vores primære nøgle, men for en sikkerheds skyld.
            existing_user_by_email = User.query.filter(User.email.ilike(normalized_email_from_google)).first()
            if existing_user_by_email:
                # Dette er en mærkelig situation: e-mailen er godkendt, men allerede i DB med et andet google_id.
                # Måske skal brugeren logge ind med den *oprindelige* Google-konto, der var knyttet til e-mailen?
                # Eller vi kan tillade opdatering af google_id på den eksisterende e-mail bruger (mere komplekst).
                # For nu, lad os give en fejl, da det indikerer en potentiel datakonflikt.
                current_app.logger.error(f"Godkendt e-mail {user_email_from_google} er allerede i databasen med et andet Google ID ({existing_user_by_email.google_id}) end det nuværende ({google_user_id}).")
                flash("Der opstod et problem med din konto. Kontakt venligst administratoren (fejlkode: EMAIL_GID_MISMATCH).", "error")
                return redirect(url_for('main.index'))

            user = User(google_id=google_user_id, name=user_name, email=user_email_from_google) # Brug e-mail fra Google
            db.session.add(user)
            try:
                db.session.commit()
                current_app.logger.info(f"Ny bruger oprettet: {user}")
            except Exception as e_commit:
                db.session.rollback()
                current_app.logger.error(f"Fejl ved commit af ny bruger: {e_commit}\n{traceback.format_exc()}")
                flash("Fejl: Kunne ikke oprette din brugerkonto.", "error")
                return redirect(url_for('main.index'))

        # Fælles for både eksisterende (godkendt) og nyoprettet (godkendt) bruger:
        login_user(user, remember=True)
        current_app.logger.info(f"Bruger {user.id} ({user.name}) logget ind succesfuldt (e-mail godkendt).")
        flash(f"Velkommen, {user.name}!", "success")
        return redirect(url_for('main.index'))

    except Exception as e:
        current_app.logger.error(f"Fejl under Google authorization process: {e}\n{traceback.format_exc()}")
        flash(f"Uventet fejl under login: {str(e)[:100]}...", "error")
        return redirect(url_for('main.index'))


@auth_bp.route('/logout')
@login_required
def logout():
    user_id_before = current_user.id if current_user.is_authenticated else 'anonymous'
    logout_user()
    current_app.logger.info(f"Bruger {user_id_before} logget ud.")
    flash("Du er nu logget ud.", "info")
    return redirect(url_for('main.index'))