# Fil: create_users_script.py
import os
import sys

# Tilføj projektets rodmappe til Python Path, så vi kan importere app-moduler
# Dette er nødvendigt, hvis scriptet køres direkte og ikke er en del af et installeret package.
# Juster stien, hvis 'app.py' eller 'config.py' ikke er i forældremappen til dette script.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from app import create_app  # Importer din application factory
    from extensions import db  # Importer db fra extensions
    from models import User  # Importer User modellen
except ImportError as e:
    print(f"Fejl: Kunne ikke importere nødvendige app-komponenter: {e}")
    print("Sørg for, at scriptet køres fra projektets rodmappe, eller at stien er korrekt sat.")
    sys.exit(1)

# -----------------------------------------------------------------------------
# DEFINER BRUGERE DER SKAL OPRETTES HER
# -----------------------------------------------------------------------------
# Hver dictionary repræsenterer en bruger, der skal oprettes.
# Tilføj eller fjern brugere fra denne liste efter behov.
USERS_TO_CREATE = [
    {
        "email": "testpremium1@example.com",
        "password": "PremiumBrugerKode1!",
        "role": "premium",
        "name": "Peter Premium"
    },
    {
        "email": "testbasic1@example.com",
        "password": "BasicBrugerKode123$",
        "role": "basic",
        "name": "Bente Basic"
    },
    {
        "email": "testfree1@example.com",
        "password": "FreeBrugerKode456#",
        "role": "free",
        "name": "Frede Free"
    },
    # {
    #     "email": "endnuenbruger@example.com",
    #     "password": "SuperHemmeligt789",
    #     "role": "premium",
    #     "name": "Hemmelig Agent"
    # },
]


def create_users_in_db(app_instance, users_data):
    """
    Opretter brugere i databasen baseret på den medfølgende data.
    Denne funktion forventer at blive kaldt inden for en Flask applikationskontekst.
    """
    print("\n--- Starter Brugeroprettelses-script ---")
    successful_creations = 0
    failed_creations = 0

    for user_info in users_data:
        email = user_info.get("email")
        password = user_info.get("password")
        role = user_info.get("role")
        name = user_info.get("name", "")  # Gør navn valgfrit

        if not email or not password or not role:
            print(f"FEJL: Manglende data for en bruger (e-mail, password, eller rolle). Skipper: {user_info}")
            failed_creations += 1
            continue

        print(f"\nBehandler bruger: {email} (Rolle: {role})")

        # Tjek om e-mailen allerede eksisterer
        try:
            existing_user = User.query.filter(User.email.ilike(email.lower())).first()
            if existing_user:
                print(f"  INFO: Bruger med e-mail '{email}' eksisterer allerede. Skipper oprettelse.")
                # Overvej om du vil opdatere rollen eller andre felter for eksisterende brugere her
                continue  # Gå til næste bruger i listen

            # Generer en unik placeholder for google_id
            i = 1
            # Gør placeholder lidt mere unik for at undgå kollisioner, hvis email-delen er den samme
            base_placeholder_google_id = f"manual_script_{email.split('@')[0]}"
            placeholder_google_id = f"{base_placeholder_google_id}_{i}"
            while User.query.filter_by(google_id=placeholder_google_id).first():
                i += 1
                placeholder_google_id = f"{base_placeholder_google_id}_{i}"

            print(f"  INFO: Genereret unik placeholder google_id: {placeholder_google_id}")

            # Opret det nye User-objekt
            new_user = User(
                google_id=placeholder_google_id,
                email=email.lower(),
                name=name,
                role=role
            )

            new_user.set_password(password)

            db.session.add(new_user)
            print(f"  SUCCESS: Bruger '{email}' (Navn: '{name}') forberedt til oprettelse med rolle '{role}'.")
            successful_creations += 1

        except Exception as e:
            print(f"  FEJL under forberedelse af bruger '{email}': {e}")
            failed_creations += 1
            # Spring over denne bruger, hvis der opstår en fejl før commit
            continue

            # Gem alle succesfuldt forberedte brugere i databasen
    if successful_creations > 0:
        try:
            db.session.commit()
            print(f"\nCOMMIT SUCCESS: {successful_creations} bruger(e) blev gemt i databasen.")
        except Exception as e:
            db.session.rollback()
            print(f"\nCOMMIT FEJL: Kunne ikke gemme de nye brugere i databasen: {e}")
            print("Alle ændringer i denne kørsel er rullet tilbage.")
            # Sæt tællere til 0, da intet blev gemt
            failed_creations += successful_creations
            successful_creations = 0
    else:
        print("\nINFO: Ingen nye brugere at gemme i databasen.")

    print("\n--- Brugeroprettelses-script Afsluttet ---")
    print(f"Resultat: {successful_creations} bruger(e) oprettet succesfuldt.")
    if failed_creations > 0:
        print(f"Resultat: {failed_creations} bruger(e) fejlede eller blev skippet.")


if __name__ == "__main__":
    flask_app = create_app()  # Opret en instans af din Flask app

    # Kør brugeroprettelseslogikken inden for applikationens kontekst
    with flask_app.app_context():
        create_users_in_db(flask_app, USERS_TO_CREATE)