import os
import sys

# Tilføj projektets rodmappe til Python Path, så vi kan importere app-moduler
# Dette er nødvendigt, hvis scriptet køres direkte og ikke er en del af et installeret package.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from app import create_app  # Importer din application factory
    from models import User  # Importer User modellen
except ImportError as e:
    print(f"Fejl: Kunne ikke importere nødvendige app-komponenter: {e}")
    print("Sørg for, at scriptet køres fra projektets rodmappe, eller at stien er korrekt sat.")
    sys.exit(1)


def list_all_users():
    """
    Trækker og udskriver en liste over alle oprettede brugere i databasen.
    """
    print("\n--- Lister alle brugere i databasen ---")

    app = create_app()  # Opret en instans af din Flask app

    # Kør databaseforespørgslen inden for applikationens kontekst
    with app.app_context():
        try:
            users = User.query.all()  # Henter alle brugere fra databasen

            if not users:
                print("Ingen brugere fundet i databasen.")
                return

            print("Fundne brugere:")
            print("--------------------------------------------------------------------------------")
            for user in users:
                # Bruger User-modellens __repr__ metode for en pæn udskrift
                print(user)
            print("--------------------------------------------------------------------------------")

        except Exception as e:
            print(f"FEJL: Der opstod en fejl under hentning af brugere: {e}")
            print("Sørg for, at din database er initialiseret, og at miljøvariabler er sat korrekt.")
            print(f"Detaljer: {e.__class__.__name__}: {e}")
            # traceback.print_exc() # Fjern kommentar for mere detaljeret fejlsporing under udvikling

    print("\n--- Brugerliste afsluttet ---")


if __name__ == "__main__":
    list_all_users()