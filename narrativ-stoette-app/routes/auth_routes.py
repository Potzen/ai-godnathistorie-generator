import traceback
from flask import Blueprint, redirect, url_for, flash, current_app, session, request, render_template
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User

auth_bp = Blueprint('auth', __name__, template_folder='../templates', static_folder='../static')


@auth_bp.route('/google-login')
def google_login():
    authlib_client = current_app.extensions.get('authlib.integrations.flask_client')
    if not authlib_client:
        flash("Google login er ikke konfigureret korrekt.", "error")
        return redirect(url_for('main.index'))
    try:
        google_client = authlib_client.google
    except AttributeError:
        flash("Google login er ikke konfigureret korrekt.", "error")
        return redirect(url_for('main.index'))

    redirect_uri = url_for('auth.google_authorize', _external=True)
    return google_client.authorize_redirect(redirect_uri)


@auth_bp.route('/authorize')
def google_authorize():
    authlib_client = current_app.extensions.get('authlib.integrations.flask_client')
    if not authlib_client:
        flash("Google login fejlede.", "error")
        return redirect(url_for('main.index'))
    try:
        google_client = authlib_client.google
    except AttributeError:
        flash("Google login fejlede.", "error")
        return redirect(url_for('main.index'))

    try:
        token = google_client.authorize_access_token()
        if not token:
            flash("Login mislykkedes.", "error")
            return redirect(url_for('main.index'))

        user_info = google_client.userinfo(token=token)
        if not user_info:
            flash("Kunne ikke hente brugerinfo.", "error")
            return redirect(url_for('main.index'))

        google_user_id = user_info.get('sub')
        user_email = user_info.get('email')
        user_name = user_info.get('name')

        if not google_user_id or not user_email:
            flash("Login mislykkedes: manglende data fra Google.", "error")
            return redirect(url_for('main.index'))

        normalized_email = user_email.lower()
        allowed = [e.lower() for e in current_app.config.get('ALLOWED_EMAIL_ADDRESSES', [])]

        if normalized_email not in allowed:
            flash("Din e-mailadresse har ikke adgang til denne applikation.", "error")
            return redirect(url_for('main.index'))

        user = User.query.filter_by(google_id=google_user_id).first()
        if not user:
            user = User.query.filter(User.email.ilike(normalized_email)).first()

        if user:
            needs_commit = False
            if user.google_id != google_user_id:
                user.google_id = google_user_id
                needs_commit = True
            if user.name != user_name:
                user.name = user_name
                needs_commit = True
            if needs_commit:
                try:
                    db.session.commit()
                except Exception:
                    db.session.rollback()
            login_user(user, remember=True)
            flash(f"Velkommen tilbage, {user.name}!", "success")
            return redirect(url_for('main.index'))

        new_user = User(google_id=google_user_id, name=user_name, email=user_email)
        db.session.add(new_user)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash("Fejl: Kunne ikke oprette konto.", "error")
            return redirect(url_for('main.index'))

        login_user(new_user, remember=True)
        flash(f"Velkommen, {new_user.name}! Din konto er oprettet.", "success")
        return redirect(url_for('main.index'))

    except Exception as e:
        current_app.logger.error(f"Google auth fejl: {e}\n{traceback.format_exc()}")
        flash("Uventet fejl under Google login.", "error")
        return redirect(url_for('main.index'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('E-mail og kodeord er påkrævet.', 'warning')
            return render_template('login.html')

        user = User.query.filter(User.email.ilike(email.lower())).first()
        if user and user.check_password(password):
            login_user(user, remember=bool(request.form.get('remember_me')))
            flash(f'Velkommen, {user.name or user.email}!', 'success')
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('main.index'))

        flash('Ugyldig e-mail eller kodeord.', 'danger')
        return render_template('login.html')

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not email or not password or not confirm:
            flash('Alle felter er påkrævet.', 'warning')
            return render_template('register.html', name=name, email=email)
        if password != confirm:
            flash('Kodeordene stemmer ikke overens.', 'warning')
            return render_template('register.html', name=name, email=email)
        if len(password) < 6:
            flash('Kodeordet skal være mindst 6 tegn.', 'warning')
            return render_template('register.html', name=name, email=email)

        normalized_email = email.lower()
        allowed = [e.lower() for e in current_app.config.get('ALLOWED_EMAIL_ADDRESSES', [])]
        if allowed and normalized_email not in allowed:
            flash('Denne e-mailadresse er ikke godkendt til registrering.', 'danger')
            return render_template('register.html', name=name, email=email)

        if User.query.filter(User.email.ilike(normalized_email)).first():
            flash('Der findes allerede en bruger med denne e-mail.', 'danger')
            return render_template('register.html', name=name, email=email)

        i = 1
        base = f"manual_{email.split('@')[0]}"
        placeholder = f"{base}_{i}"
        while User.query.filter_by(google_id=placeholder).first():
            i += 1
            placeholder = f"{base}_{i}"

        new_user = User(
            name=name or email.split('@')[0],
            email=normalized_email,
            google_id=placeholder,
        )
        new_user.set_password(password)
        db.session.add(new_user)
        try:
            db.session.commit()
            login_user(new_user)
            flash('Din konto er oprettet!', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            flash('Fejl under oprettelse af konto. Prøv igen.', 'danger')
            return render_template('register.html', name=name, email=email)

    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash("Du er nu logget ud.", "info")
    return redirect(url_for('main.index'))
