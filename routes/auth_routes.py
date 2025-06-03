# Fil: routes/auth_routes.py
from flask import Blueprint, redirect, url_for, flash, current_app, session, request, render_template
import traceback
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User
from werkzeug.security import generate_password_hash, check_password_hash # Tilføjet denne import

auth_bp = Blueprint('auth', __name__, template_folder='../templates', static_folder='../static')

@auth_bp.route('/google-login') # Ny, dedikeret rute til at initiere Google login
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

        # Først, forsøg at finde brugeren baseret på det rigtige google_id
        user = User.query.filter_by(google_id=google_user_id).first()
        needs_commit = False

        if user:  # Eksisterende Google-bruger fundet (matchet på google_id)
            current_app.logger.info(
                f"Eksisterende Google-bruger fundet via google_id: {user.email} (ID={user.id}), Nuværende Rolle='{user.role}'")
            # Opdater navn hvis nødvendigt
            if user.name != user_name:
                user.name = user_name
                needs_commit = True
            # Opdater e-mail hvis nødvendigt (og hvis den ikke konflikter)
            if user.email and user.email.lower() != normalized_email_from_google:
                conflicting_user_by_email = User.query.filter(User.email.ilike(normalized_email_from_google),
                                                              User.google_id != google_user_id).first()
                if not conflicting_user_by_email:
                    user.email = user_email_from_google  # Gemmer den case Google sender
                    needs_commit = True
                else:
                    current_app.logger.warning(
                        f"Google e-mail ({user_email_from_google}) for bruger {google_user_id} er allerede i brug af en anden bruger ({conflicting_user_by_email.google_id}). E-mail ikke opdateret.")
            elif not user.email and user_email_from_google:  # Hvis e-mail feltet var tomt før
                user.email = user_email_from_google
                needs_commit = True

            # Gen-evaluer altid rolle baseret på config.py lister ved Google login
            original_role_from_db = user.role
            potential_new_role = 'free'
            premium_emails_lower = [e.lower() for e in current_app.config.get('PREMIUM_TIER_GOOGLE_EMAILS', [])]
            basic_emails_lower = [e.lower() for e in current_app.config.get('BASIC_TIER_GOOGLE_EMAILS', [])]

            if normalized_email_from_google in premium_emails_lower:
                potential_new_role = 'premium'
            elif normalized_email_from_google in basic_emails_lower:
                potential_new_role = 'basic'

            if user.role != potential_new_role:
                user.role = potential_new_role
                needs_commit = True
                current_app.logger.info(
                    f"ROLLE ÆNDRET (eks. Google-bruger): {user.email} rolle opdateret fra '{original_role_from_db}' til '{user.role}'.")

            if needs_commit:
                try:
                    db.session.commit()
                    current_app.logger.info(
                        f"Brugerinfo opdateret for eksisterende Google-bruger: {user.email}, ny rolle: {user.role}")
                except Exception as e_commit:
                    db.session.rollback()
                    current_app.logger.error(f"Fejl ved opdatering af eksisterende Google-bruger: {e_commit}")
                    # Undlad at flashe fejl her, da brugeren stadig logges ind

            login_user(user, remember=True)
            flash(f"Velkommen tilbage, {user.name}!", "success")
            return redirect(url_for('main.index'))

        else:  # Bruger ikke fundet på google_id. Tjek om e-mailen eksisterer (f.eks. manuelt oprettet bruger)
            current_app.logger.info(
                f"Google ID '{google_user_id}' ikke fundet. Tjekker for eksisterende e-mail: {normalized_email_from_google}...")
            user = User.query.filter(User.email.ilike(normalized_email_from_google)).first()

            if user:  # JA, brugeren findes allerede på e-mail (f.eks. manuelt oprettet med placeholder google_id)
                current_app.logger.info(
                    f"Bruger fundet på e-mail: {user.email} (DB ID: {user.id}, DB Google ID: {user.google_id}). Linker Google-konto og opdaterer.")
                needs_commit = False

                # 1. Opdater til det rigtige google_id (erstatter placeholder)
                if user.google_id != google_user_id:  # Dette er vigtigt for at linke
                    user.google_id = google_user_id
                    needs_commit = True
                    current_app.logger.info(f"  google_id for {user.email} opdateret til '{google_user_id}'.")

                # 2. Opdater navn, hvis det fra Google er anderledes
                if user.name != user_name:
                    user.name = user_name
                    needs_commit = True
                    current_app.logger.info(f"  Navn for {user.email} opdateret til '{user.name}'.")

                # 3. Bestem og opdater rolle baseret på config.py lister
                original_role_from_db = user.role
                potential_new_role = 'free'
                premium_emails_lower = [e.lower() for e in current_app.config.get('PREMIUM_TIER_GOOGLE_EMAILS', [])]
                basic_emails_lower = [e.lower() for e in current_app.config.get('BASIC_TIER_GOOGLE_EMAILS', [])]

                if normalized_email_from_google in premium_emails_lower:
                    potential_new_role = 'premium'
                elif normalized_email_from_google in basic_emails_lower:
                    potential_new_role = 'basic'

                if user.role != potential_new_role:
                    user.role = potential_new_role
                    needs_commit = True
                    current_app.logger.info(
                        f"  ROLLE ÆNDRET (Google-link for eks. e-mail): {user.email} rolle opdateret fra '{original_role_from_db}' til '{user.role}'.")
                else:
                    current_app.logger.info(
                        f"  ROLLE UÆNDRET (Google-link for eks. e-mail): {user.email} rolle er stadig '{user.role}'.")

                if needs_commit:
                    try:
                        db.session.commit()
                        current_app.logger.info(
                            f"  Bruger {user.email} succesfuldt linket til Google ID og opdateret i DB.")
                    except Exception as e_commit:
                        db.session.rollback()
                        current_app.logger.error(
                            f"  Fejl ved commit for linkning af Google-konto til eksisterende e-mail ({user.email}): {e_commit}")
                        flash("Der opstod en fejl under tilknytning af din Google-konto. Prøv igen.", "error")
                        return redirect(url_for('main.index'))

                login_user(user, remember=True)
                flash(f"Din konto er nu succesfuldt tilknyttet Google. Velkommen, {user.name}!", "success")
                return redirect(url_for('main.index'))

            else:  # HELT ny bruger (hverken google_id eller e-mail findes i databasen)
                current_app.logger.info(
                    f"Helt ny bruger: {user_email_from_google}. Opretter med Google ID {google_user_id}.")
                assigned_role = 'free'
                premium_emails_lower = [e.lower() for e in current_app.config.get('PREMIUM_TIER_GOOGLE_EMAILS', [])]
                basic_emails_lower = [e.lower() for e in current_app.config.get('BASIC_TIER_GOOGLE_EMAILS', [])]

                if normalized_email_from_google in premium_emails_lower:
                    assigned_role = 'premium'
                elif normalized_email_from_google in basic_emails_lower:
                    assigned_role = 'basic'
                current_app.logger.info(
                    f"  Ny Google-bruger {normalized_email_from_google} tildeles rollen '{assigned_role}'.")

                user = User(google_id=google_user_id, name=user_name, email=user_email_from_google, role=assigned_role)
                db.session.add(user)
                try:
                    db.session.commit()
                    current_app.logger.info(f"  Ny bruger oprettet via Google: {user} med rolle '{user.role}'")
                except Exception as e_commit:
                    db.session.rollback()
                    current_app.logger.error(
                        f"  Fejl ved commit af helt ny Google-bruger: {e_commit}\n{traceback.format_exc()}")
                    flash("Fejl: Kunne ikke oprette din brugerkonto via Google.", "error")
                    return redirect(url_for('main.index'))

                login_user(user, remember=True)
                current_app.logger.info(
                    f"  Bruger {user.id} ({user.name}, Rolle: {user.role}) logget ind via Google (nyoprettet).")
                flash(f"Velkommen, {user.name}! Din konto er oprettet.", "success")
                return redirect(url_for('main.index'))

    except Exception as e:
        current_app.logger.error(f"Fejl under Google authorization process: {e}\n{traceback.format_exc()}")
        flash(f"Uventet fejl under Google login: {str(e)[:100]}...", "error")
        return redirect(url_for('main.index'))


@auth_bp.route('/login', methods=['GET', 'POST']) # Sørg for at den har methods=['GET', 'POST']
def auth_login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST': # Dette er for når formularen POSTes
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('E-mail og kodeord skal udfyldes.', 'warning')
            return render_template('auth_login.html')

        user = User.query.filter(User.email.ilike(email.lower())).first()

        if user and user.password_hash and user.check_password(password):
            login_user(user, remember=request.form.get('remember_me', type=bool))
            current_app.logger.info(
                f"Bruger {user.email} (Rolle: {user.role}) logget ind succesfuldt med e-mail/kodeord."
            )
            flash(f'Velkommen tilbage, {user.name or user.email}!', 'success')

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('main.index'))
        else:
            current_app.logger.warning(f"Mislykket e-mail/kodeord login forsøg for e-mail: {email}.")
            flash('Ugyldig e-mail eller kodeord. Prøv igen.', 'danger')
            return render_template('auth_login.html')

    return render_template('auth_login.html') # Dette er for GET-kaldet, der viser login-formularen

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash('Du er allerede logget ind.', 'info')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not email or not password or not confirm_password:
            flash('Alle obligatoriske felter (E-mail, Kodeord, Bekræft Kodeord) skal udfyldes.', 'warning')
            return render_template('signup_email.html', name=name, email=email)

        if password != confirm_password:
            flash('Kodeordene stemmer ikke overens. Prøv igen.', 'warning')
            return render_template('signup_email.html', name=name, email=email)

        if len(password) < 6: # Minimum længde for adgangskode
            flash('Kodeordet skal være på mindst 6 tegn.', 'warning')
            return render_template('signup_email.html', name=name, email=email)

        # Tjek om e-mail allerede eksisterer
        # Bruger ilike for case-insensitive tjek for at undgå at "Test@example.com" og "test@example.com" betragtes som forskellige
        existing_user_by_email = User.query.filter(User.email.ilike(email.lower())).first()
        if existing_user_by_email:
            flash('En bruger med denne e-mailadresse eksisterer allerede.', 'danger')
            return render_template('signup_email.html', name=name, email=email)

        # Generer et unikt placeholder for google_id
        # Dette er nødvendigt, da google_id er nullable=False i modellen, men vi skal give den en værdi
        # for brugere, der opretter sig med e-mail.
        # Vi sikrer, at placeholderen er unik ved at tilføje et løbenummer.
        i = 1
        base_placeholder_google_id = f"manual_reg_{email.split('@')[0]}"
        placeholder_google_id = f"{base_placeholder_google_id}_{i}"
        while User.query.filter_by(google_id=placeholder_google_id).first():
            i += 1
            placeholder_google_id = f"{base_placeholder_google_id}_{i}"
        current_app.logger.info(f"Generated unique placeholder google_id: {placeholder_google_id}")

        new_user = User(
            name=name if name else email.split('@')[0], # Brug navn hvis angivet, ellers del af email før @
            email=email.lower(), # Gem email i lowercase for konsistens
            google_id=placeholder_google_id, # Placeholder for e-mail-brugere
            role='basic' # Standardrolle for nye registreringer
        )
        new_user.set_password(password) # Hasher kodeordet

        db.session.add(new_user)
        try:
            db.session.commit()
            current_app.logger.info(f"New user registered: {new_user.email} with role {new_user.role}")
            login_user(new_user) # Log ind den nye bruger
            flash('Din konto er nu oprettet og du er logget ind!', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error during new user registration commit: {e}\n{traceback.format_exc()}")
            flash('Der opstod en fejl under oprettelse af kontoen. Prøv igen.', 'danger')
            return render_template('signup_email.html', name=name, email=email)

    return render_template('signup_email.html')

@auth_bp.route('/logout')
@login_required
def logout():
    user_id_before = current_user.id if current_user.is_authenticated else 'anonymous'
    user_role_before = current_user.role if current_user.is_authenticated else 'N/A'
    logout_user()
    current_app.logger.info(f"Bruger {user_id_before} (Rolle: {user_role_before}) logget ud.")
    flash("Du er nu logget ud.", "info")
    return redirect(url_for('main.index'))