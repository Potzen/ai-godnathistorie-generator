# Fil: routes/auth_routes.py
from flask import Blueprint, redirect, url_for, flash, current_app, session, request, render_template
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

    # Hent Authlib Flask klient-udvidelsen
    authlib_flask_extension = current_app.extensions.get('authlib.integrations.flask_client')

    if not authlib_flask_extension:
        current_app.logger.error("Authlib Flask Client ('authlib.integrations.flask_client') ikke fundet i current_app.extensions i authorize.")
        flash("Google login er ikke konfigureret korrekt på serveren (authlib klient mangler i authorize).", "error")
        return redirect(url_for('main.index'))

    try:
        # Tilgå 'google' klienten som en attribut
        google_oauth_client = authlib_flask_extension.google
    except AttributeError:
        current_app.logger.error("Google OAuth klient ('google') ikke fundet som attribut på authlib_flask_extension i authorize.")
        flash("Google login er ikke konfigureret korrekt på serveren (klient-attribut mangler i authorize).", "error")
        return redirect(url_for('main.index'))

    # Ekstra tjek, selvom AttributeError burde fange det.
    if not google_oauth_client:
        current_app.logger.error("Google OAuth klient ikke fundet eller kunne ikke hentes efter attribut-tjek i authorize.")
        flash("Google login er ikke konfigureret korrekt på serveren (klient mangler efter tjek i authorize).", "error")
        return redirect(url_for('main.index'))

    try:
        token = google_oauth_client.authorize_access_token()
        # ... resten af din funktion fortsætter herfra ...
        # (Sørg for at resten af din logik, inklusiv email-tjek, er som før)

        if not token:
            current_app.logger.warning("Login mislykkedes: Kunne ikke autorisere access token.")
            flash("Login mislykkedes (token).", "error")
            return redirect(url_for('main.index'))

        current_app.logger.info("Access token modtaget. Henter brugerinfo...")
        user_info = google_oauth_client.userinfo(token=token) # Sørg for at userinfo kaldes på google_oauth_client
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
            current_app.logger.warning(f"Login mislykkedes: Ingen e-mail modtaget fra Google for bruger {google_user_id}.")
            flash("Login mislykkedes: Kunne ikke hente din e-mailadresse fra Google.", "error")
            return redirect(url_for('main.index'))

        normalized_email_from_google = user_email_from_google.lower()
        allowed_emails_lower = [email.lower() for email in current_app.config.get('ALLOWED_EMAIL_ADDRESSES', [])]

        if normalized_email_from_google not in allowed_emails_lower:
            current_app.logger.warning(f"Login forsøg fra ikke-godkendt e-mail: {user_email_from_google} (Google ID: {google_user_id}).")
            flash("Din e-mailadresse har ikke adgang til denne applikation. Kontakt venligst administratoren.", "error")
            return redirect(url_for('main.index'))

        user = User.query.filter_by(google_id=google_user_id).first()
        if user:
            current_app.logger.info(f"Eksisterende bruger (baseret på Google ID) fundet: {user} for e-mail {normalized_email_from_google}")
            needs_commit = False
            if user.name != user_name:
                user.name = user_name
                needs_commit = True
            if user.email and user.email.lower() != normalized_email_from_google: # Tjek om user.email eksisterer
                conflicting_user_by_email = User.query.filter(User.email.ilike(normalized_email_from_google), User.google_id != google_user_id).first()
                if not conflicting_user_by_email:
                    user.email = user_email_from_google
                    needs_commit = True
                else:
                    current_app.logger.warning(f"Bruger {google_user_id}s Google e-mail ({user_email_from_google}) er allerede i brug af en anden bruger ({conflicting_user_by_email.google_id}). E-mail ikke opdateret.")
            elif not user.email and user_email_from_google: # Hvis brugeren ikke har en email, men Google sender en
                user.email = user_email_from_google
                needs_commit = True

                # Tildel rolle baseret på e-mail lister fra config
                premium_emails = [e.lower() for e in current_app.config.get('PREMIUM_TIER_GOOGLE_EMAILS', [])]
                basic_emails = [e.lower() for e in current_app.config.get('BASIC_TIER_GOOGLE_EMAILS', [])]
                current_role = user.role  # Gem nuværende rolle for at se om den ændres

                if normalized_email_from_google in premium_emails:
                    user.role = 'premium'
                elif normalized_email_from_google in basic_emails:
                    user.role = 'basic'
                else:
                    user.role = 'free'

                if user.role != current_role:
                    needs_commit = True
                    current_app.logger.info(
                        f"Bruger {user.email} rolle opdateret fra '{current_role}' til '{user.role}'.")
                elif not current_role:  # Hvis rollen var None/tom før (usandsynligt med default, men for en sikkerheds skyld)
                    needs_commit = True
                    current_app.logger.info(f"Bruger {user.email} rolle sat til '{user.role}'.")

            if needs_commit:
                try:
                    db.session.commit()
                    current_app.logger.info("Brugerinfo opdateret for eksisterende bruger.")
                except Exception as e_commit:
                    db.session.rollback()
                    current_app.logger.error(f"Fejl ved opdatering af brugerinfo for eksisterende bruger: {e_commit}")

        else:
            current_app.logger.info(f"Ny bruger (Google ID: {google_user_id}) med godkendt e-mail: {user_email_from_google}. Opretter bruger...")
            existing_user_by_email = User.query.filter(User.email.ilike(normalized_email_from_google)).first()
            if existing_user_by_email:
                current_app.logger.error(f"Godkendt e-mail {user_email_from_google} er allerede i databasen med et andet Google ID ({existing_user_by_email.google_id}) end det nuværende ({google_user_id}).")
                flash("Der opstod et problem med din konto. Kontakt venligst administratoren (fejlkode: EMAIL_GID_MISMATCH).", "error")
                return redirect(url_for('main.index'))

            # Bestem rolle for ny bruger
            assigned_role = 'free'  # Standardrollen fra User modellen vil også være 'free', men vi er eksplicitte her.
            premium_emails = [e.lower() for e in current_app.config.get('PREMIUM_TIER_GOOGLE_EMAILS', [])]
            basic_emails = [e.lower() for e in current_app.config.get('BASIC_TIER_GOOGLE_EMAILS', [])]

            # normalized_email_from_google er allerede defineret tidligere i funktionen
            if normalized_email_from_google in premium_emails:
                assigned_role = 'premium'
            elif normalized_email_from_google in basic_emails:
                assigned_role = 'basic'

            current_app.logger.info(f"Ny bruger {normalized_email_from_google} tildeles rollen '{assigned_role}'.")

            user = User(google_id=google_user_id, name=user_name, email=user_email_from_google, role=assigned_role)
            db.session.add(user)
            try:
                db.session.commit()
                current_app.logger.info(f"Ny bruger oprettet: {user}")
            except Exception as e_commit:
                db.session.rollback()
                current_app.logger.error(f"Fejl ved commit af ny bruger: {e_commit}\n{traceback.format_exc()}")
                flash("Fejl: Kunne ikke oprette din brugerkonto.", "error")
                return redirect(url_for('main.index'))

        login_user(user, remember=True)
        current_app.logger.info(f"Bruger {user.id} ({user.name}) logget ind succesfuldt (e-mail godkendt).")
        flash(f"Velkommen, {user.name}!", "success")
        return redirect(url_for('main.index'))

    except Exception as e:
        current_app.logger.error(f"Fejl under Google authorization process: {e}\n{traceback.format_exc()}")
        flash(f"Uventet fejl under login: {str(e)[:100]}...", "error")
        return redirect(url_for('main.index'))

@auth_bp.route('/login-email', methods=['GET', 'POST'])
def email_password_login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))  # Hvis allerede logget ind, send til forside

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('E-mail og kodeord skal udfyldes.', 'warning')
            return redirect(url_for('auth.email_password_login'))

        user = User.query.filter(User.email.ilike(email.lower())).first()

        if user and user.password_hash and user.check_password(password):
            login_user(user,
                       remember=request.form.get('remember_me', type=bool))  # Husk mig funktionalitet (valgfri)
            current_app.logger.info(f"Bruger {user.email} logget ind succesfuldt med e-mail/kodeord.")
            flash(f'Velkommen tilbage, {user.name or user.email}!', 'success')

            # Håndter redirect efter login (f.eks. hvis brugeren prøvede at tilgå en beskyttet side)
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):  # Sikkerhedscheck for next_page
                return redirect(next_page)
            return redirect(url_for('main.index'))
        else:
            current_app.logger.warning(f"Mislykket login forsøg for e-mail: {email}.")
            flash('Ugyldig e-mail eller kodeord. Prøv igen.', 'danger')
            # Vi redirecter for at undgå at POST-data genindsendes ved refresh
            return redirect(url_for('auth.email_password_login'))

    # Hvis metoden er GET, eller hvis POST fejler og vi ikke omdirigerer internt i POST-blokken
    return render_template('login_email.html')  # Vi opretter denne fil senere

@auth_bp.route('/logout')
@login_required
def logout():
    user_id_before = current_user.id if current_user.is_authenticated else 'anonymous'
    logout_user()
    current_app.logger.info(f"Bruger {user_id_before} logget ud.")
    flash("Du er nu logget ud.", "info")
    return redirect(url_for('main.index'))