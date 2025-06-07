# Fil: manage_users.py (tidligere create_users_script.py)
import os
import sys
import traceback

# Tilføj projektets rodmappe til Python Path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from app import create_app
    from extensions import db
    from models import User
except ImportError as e:
    print(f"Fejl: Kunne ikke importere nødvendige app-komponenter: {e}")
    sys.exit(1)

# -----------------------------------------------------------------------------
# DEFINER BRUGERE DER SKAL OPRETTES ELLER OPDATERES HER
# -----------------------------------------------------------------------------
# For at opgradere en eksisterende bruger:
# Tilføj deres e-mail og den nye rolle ('premium') til listen.
# Scriptet finder brugeren og opdaterer kun rollen.
# Password-feltet vil blive ignoreret for eksisterende brugere.
USERS_TO_MANAGE = [
    {
        "email": "en.eksisterende.bruger@example.com",  # E-mail på en bruger, der selv har oprettet sig som 'basic'
        "role": "premium",
        "name": "Opgraderet Bruger Navn",  # Navn vil også blive opdateret, hvis det er anderledes
        "password": ""  # Password ignoreres for eksisterende brugere, kan være tomt
    },
    {
        "email": "en.helt.ny.bruger@example.com",
        "password": "SuperHemmeligt123",
        "role": "premium",
        "name": "Ny Premium Bruger"
    },
]


def manage_users_in_db(app_instance, users_data):
    """
    Opretter eller opdaterer brugere i databasen.
    Denne funktion er IKKE-DESTRUKTIV. Den sletter ikke eksisterende brugere.
    """
    print("\n--- Starter Brugerhåndterings-script (Opret/Opdater) ---")
    users_created = 0
    users_updated = 0
    users_skipped = 0

    with app_instance.app_context():
        for user_info in users_data:
            email = user_info.get("email")
            role = user_info.get("role")
            name = user_info.get("name")
            password = user_info.get("password")

            if not email or not role:
                print(f"FEJL: Manglende 'email' eller 'role' for et indslag. Skipper: {user_info}")
                continue

            try:
                # Find brugeren (case-insensitive)
                existing_user = User.query.filter(User.email.ilike(email.lower())).first()

                if existing_user:
                    # BRUGEREN FINDES - OPDATER HVIS NØDVENDIGT
                    print(f"  INFO: Bruger '{email}' fundet i databasen.")
                    made_change = False
                    if existing_user.role != role:
                        print(f"    -> ACTION: Opdaterer rolle fra '{existing_user.role}' til '{role}'.")
                        existing_user.role = role
                        made_change = True

                    if name and existing_user.name != name:
                        print(f"    -> ACTION: Opdaterer navn fra '{existing_user.name}' til '{name}'.")
                        existing_user.name = name
                        made_change = True

                    if not made_change:
                        print("    -> INFO: Ingen ændringer i rolle eller navn. Intet at opdatere.")
                    else:
                        users_updated += 1

                else:
                    # BRUGEREN FINDES IKKE - OPRET NY
                    print(f"  INFO: Bruger '{email}' ikke fundet. Opretter ny bruger.")
                    if not password:
                        print(f"    -> FEJL: Kodeord mangler for ny bruger '{email}'. Skipper.")
                        continue

                    # Generer unik placeholder for google_id
                    i = 1
                    base_placeholder_google_id = f"manual_script_{email.lower().split('@')[0]}"
                    placeholder_google_id = f"{base_placeholder_google_id}_{i}"
                    while User.query.filter_by(google_id=placeholder_google_id).first():
                        i += 1
                        placeholder_google_id = f"{base_placeholder_google_id}_{i}"

                    new_user = User(
                        google_id=placeholder_google_id,
                        email=email.lower(),
                        name=name if name else email.lower().split('@')[0],
                        role=role
                    )
                    new_user.set_password(password)
                    db.session.add(new_user)
                    print(f"    -> SUCCESS: Bruger '{email}' klargjort til oprettelse med rolle '{role}'.")
                    users_created += 1

            except Exception as e:
                print(f"  ALVORLIG FEJL under behandling af '{email}': {e}")
                traceback.print_exc()

        # Commit alle ændringer (både nye og opdaterede) til databasen
        if users_created > 0 or users_updated > 0:
            try:
                db.session.commit()
                print(f"\nCOMMIT SUCCESS: {users_created} bruger(e) oprettet, {users_updated} bruger(e) opdateret.")
            except Exception as e:
                db.session.rollback()
                print(f"\nCOMMIT FEJL: Kunne ikke gemme ændringer i databasen: {e}")
                print("Alle ændringer i denne kørsel er rullet tilbage.")
        else:
            print("\nINFO: Ingen nye brugere at oprette eller eksisterende at opdatere.")

    print("\n--- Brugerhåndterings-script Afsluttet ---")


if __name__ == "__main__":
    flask_app = create_app()
    # Kør bruger-logikken med applikationskontekst
    manage_users_in_db(flask_app, USERS_TO_MANAGE)