# Fil: routes/auth_routes.py
from flask import Blueprint, redirect, url_for, flash, current_app, session, request, render_template
import traceback  # Selvom ikke brugt aktivt pt., kan det være nyttigt for generel fejlfinding
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User

auth_bp = Blueprint('auth', __name__, template_folder='../templates', static_folder='../static')


@auth_bp.route('/login')
def google_login():
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
    authlib_flask_extension = current_app.extensions.get('authlib.integrations.flask_client')

    if not authlib_flask_extension:
        current_app.logger.error("Authlib Flask Client ikke fundet i authorize.")
        flash("Google login er ikke konfigureret korrekt (authlib klient mangler i authorize).", "error")
        return redirect(url_for('main.index'))
    try:
        google_oauth_client = authlib_flask_extension.google
    except AttributeError:
        current_app.logger.error("Google OAuth klient-attribut ikke fundet i authorize.")
        flash("Google login er ikke konfigureret korrekt (klient-attribut mangler i authorize).", "error")
        return redirect(url_for('main.index'))
    if not google_oauth_client:
        current_app.logger.error("Google OAuth klient ikke fundet efter attribut-tjek i authorize.")
        flash("Google login er ikke konfigureret korrekt (klient mangler efter tjek i authorize).", "error")
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
        user_email_from_google = user_info.get('email')
        user_name = user_info.get('name')

        if not google_user_id:
            current_app.logger.warning("Login mislykkedes: Google user ID ('sub') ikke fundet.")
            flash("Login mislykkedes (ID).", "error")
            return redirect(url_for('main.index'))
        if not user_email_from_google:
            current_app.logger.warning(
                f"Login mislykkedes: Ingen e-mail modtaget fra Google for bruger {google_user_id}.")
            flash("Login mislykkedes: Kunne ikke hente din e-mailadresse fra Google.", "error")
            return redirect(url_for('main.index'))

        normalized_email_from_google = user_email_from_google.lower()
        allowed_emails_lower = [email.lower() for email in current_app.config.get('ALLOWED_EMAIL_ADDRESSES', [])]

        if normalized_email_from_google not in allowed_emails_lower:
            current_app.logger.warning(
                f"Login forsøg fra ikke-godkendt e-mail: {user_email_from_google} (Google ID: {google_user_id}).")
            flash("Din e-mailadresse har ikke adgang til denne applikation.", "error")
            return redirect(url_for('main.index'))

        user = User.query.filter_by(google_id=google_user_id).first()
        needs_commit = False

        if user:  # Eksisterende bruger fundet
            current_app.logger.info(
                f"Eksisterende Google-bruger fundet: ID={user.id}, Email={user.email}, Nuværende Rolle='{user.role}'")

            if user.name != user_name:
                user.name = user_name
                needs_commit = True

            if user.email and user.email.lower() != normalized_email_from_google:
                conflicting_user_by_email = User.query.filter(User.email.ilike(normalized_email_from_google),
                                                              User.google_id != google_user_id).first()
                if not conflicting_user_by_email:
                    user.email = user_email_from_google
                    needs_commit = True
                else:
                    current_app.logger.warning(
                        f"Bruger {google_user_id}s Google e-mail ({user_email_from_google}) er allerede i brug af en anden bruger ({conflicting_user_by_email.google_id}). E-mail ikke opdateret.")
            elif not user.email and user_email_from_google:
                user.email = user_email_from_google
                needs_commit = True

            # ---- START DEBUGGING OG ROLLETILDELING FOR EKSTISTERENDE BRUGER ----
            current_app.logger.debug(f"--- Rolle-tjek for eksisterende bruger: {normalized_email_from_google} ---")

            premium_emails_config = current_app.config.get('PREMIUM_TIER_GOOGLE_EMAILS', [])
            basic_emails_config = current_app.config.get('BASIC_TIER_GOOGLE_EMAILS', [])

            current_app.logger.debug(f"Config - PREMIUM_TIER_GOOGLE_EMAILS: {premium_emails_config}")
            current_app.logger.debug(f"Config - BASIC_TIER_GOOGLE_EMAILS: {basic_emails_config}")

            premium_emails_lower = [e.lower() for e in premium_emails_config]
            basic_emails_lower = [e.lower() for e in basic_emails_config]

            current_app.logger.debug(f"Normaliseret e-mail for tjek: '{normalized_email_from_google}'")
            current_app.logger.debug(f"Lowercase Premium e-mails fra config: {premium_emails_lower}")
            current_app.logger.debug(f"Lowercase Basic e-mails fra config: {basic_emails_lower}")

            original_role_from_db = user.role
            current_app.logger.debug(f"Brugerens nuværende rolle fra DB: '{original_role_from_db}'")

            potential_new_role = 'free'
            if normalized_email_from_google in premium_emails_lower:
                potential_new_role = 'premium'
                current_app.logger.debug(f"E-mail fundet i premium_emails_lower. Potentiel ny rolle: 'premium'")
            elif normalized_email_from_google in basic_emails_lower:
                potential_new_role = 'basic'
                current_app.logger.debug(f"E-mail fundet i basic_emails_lower. Potentiel ny rolle: 'basic'")
            else:
                current_app.logger.debug(f"E-mail IKKE fundet i premium/basic lister. Potentiel ny rolle: 'free'")

            if user.role != potential_new_role:
                user.role = potential_new_role
                needs_commit = True
                current_app.logger.info(
                    f"ROLLE ÆNDRET: Bruger {user.email} rolle opdateret fra '{original_role_from_db}' til '{user.role}'. 'needs_commit' er nu: {needs_commit}.")
            else:
                current_app.logger.debug(
                    f"Brugerens rolle '{user.role}' er uændret. 'needs_commit' status (før evt. navn/email ændring): {needs_commit}")

            current_app.logger.debug(
                f"--- Slut på rolle-tjek. Endelig user.role: '{user.role}', needs_commit: {needs_commit} ---")
            # ---- SLUT DEBUGGING AF ROLLETILDELING ----

            if needs_commit:
                try:
                    db.session.commit()
                    current_app.logger.info(
                        f"Brugerinfo (inkl. mulig rolle) opdateret for eksisterende bruger: {user.email}, ny rolle: {user.role}")
                except Exception as e_commit:
                    db.session.rollback()
                    current_app.logger.error(f"Fejl ved opdatering af brugerinfo for eksisterende bruger: {e_commit}")

        else:  # Ny bruger
            current_app.logger.info(
                f"Ny Google-bruger (ID: {google_user_id}), e-mail: {user_email_from_google}. Opretter...")
            existing_user_by_email = User.query.filter(User.email.ilike(normalized_email_from_google)).first()
            if existing_user_by_email:
                current_app.logger.error(
                    f"Godkendt e-mail {user_email_from_google} er allerede i databasen med et andet Google ID ({existing_user_by_email.google_id}). Login for {google_user_id} afbrudt.")
                flash(
                    "Der opstod et problem med din konto. Kontakt administratoren (fejlkode: EMAIL_GID_MISMATCH_NEW_USER).",
                    "error")
                return redirect(url_for('main.index'))

            # Bestem rolle for ny bruger
            assigned_role = 'free'
            premium_emails_lower = [e.lower() for e in current_app.config.get('PREMIUM_TIER_GOOGLE_EMAILS', [])]
            basic_emails_lower = [e.lower() for e in current_app.config.get('BASIC_TIER_GOOGLE_EMAILS', [])]

            current_app.logger.debug(f"Ny bruger - Tjekker rolle for {normalized_email_from_google}:")
            current_app.logger.debug(
                f"Ny bruger - Config PREMIUM_TIER_GOOGLE_EMAILS: {current_app.config.get('PREMIUM_TIER_GOOGLE_EMAILS', [])}")
            current_app.logger.debug(
                f"Ny bruger - Config BASIC_TIER_GOOGLE_EMAILS: {current_app.config.get('BASIC_TIER_GOOGLE_EMAILS', [])}")

            if normalized_email_from_google in premium_emails_lower:
                assigned_role = 'premium'
            elif normalized_email_from_google in basic_emails_lower:
                assigned_role = 'basic'

            current_app.logger.info(f"Ny bruger {normalized_email_from_google} tildeles rollen '{assigned_role}'.")

            user = User(google_id=google_user_id, name=user_name, email=user_email_from_google, role=assigned_role)
            db.session.add(user)
            try:
                db.session.commit()
                current_app.logger.info(f"Ny bruger oprettet: {user} med rolle '{user.role}'")
            except Exception as e_commit:
                db.session.rollback()
                current_app.logger.error(f"Fejl ved commit af ny bruger: {e_commit}\n{traceback.format_exc()}")
                flash("Fejl: Kunne ikke oprette din brugerkonto.", "error")
                return redirect(url_for('main.index'))

        login_user(user, remember=True)
        current_app.logger.info(
            f"Bruger {user.id} ({user.name}, Rolle: {user.role}) logget ind succesfuldt (e-mail godkendt via Google).")
        flash(f"Velkommen, {user.name}!", "success")
        return redirect(url_for('main.index'))

    except Exception as e:
        current_app.logger.error(f"Fejl under Google authorization process: {e}\n{traceback.format_exc()}")
        flash(f"Uventet fejl under Google login: {str(e)[:100]}...", "error")
        return redirect(url_for('main.index'))


@auth_bp.route('/login-email', methods=['GET', 'POST'])
def email_password_login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('E-mail og kodeord skal udfyldes.', 'warning')
            return redirect(url_for('auth.email_password_login'))

        user = User.query.filter(User.email.ilike(email.lower())).first()

        if user and user.password_hash and user.check_password(password):
            login_user(user, remember=request.form.get('remember_me', type=bool))
            current_app.logger.info(
                f"Bruger {user.email} (Rolle: {user.role}) logget ind succesfuldt med e-mail/kodeord.")
            flash(f'Velkommen tilbage, {user.name or user.email}!', 'success')

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('main.index'))
        else:
            current_app.logger.warning(f"Mislykket e-mail/kodeord login forsøg for e-mail: {email}.")
            flash('Ugyldig e-mail eller kodeord. Prøv igen.', 'danger')
            return redirect(url_for('auth.email_password_login'))

    return render_template('login_email.html')


@auth_bp.route('/logout')
@login_required
def logout():
    user_id_before = current_user.id if current_user.is_authenticated else 'anonymous'
    user_role_before = current_user.role if current_user.is_authenticated else 'N/A'
    logout_user()
    current_app.logger.info(f"Bruger {user_id_before} (Rolle: {user_role_before}) logget ud.")
    flash("Du er nu logget ud.", "info")
    return redirect(url_for('main.index'))