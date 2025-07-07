# Fil: scheduler.py
import schedule
import time
import sys

# Føj rodmappen (GodnathistorieApp) til Python's søgesti
# Dette sikrer, at vi kan finde mapper som 'app', 'services' og 'prompts'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from daily_poster import run_daily_job

def job_wrapper():
    """
    En lille "wrapper"-funktion, der logger, før og efter jobbet kører.
    """
    print(f"Starter det planlagte job nu: {time.ctime()}")
    try:
        run_daily_job()
        print(f"Jobbet er fuldført succesfuldt: {time.ctime()}")
    except Exception as e:
        print(f"En fejl opstod under kørsel af det planlagte job: {e}")

# --- PLANLÆG DIT JOB HER ---
# Eksempel: Kør jobbet hver dag kl. 08:00 om morgenen.
# Du kan ændre "08:00" til et hvilket som helst tidspunkt.
schedule.every(2).days.at("10:00").do(job_wrapper)

# Du kan bruge et af disse eksempler til at teste, uden at skulle vente en hel dag:
# schedule.every(1).minutes.do(job_wrapper)  # Kør hvert minut
# schedule.every(10).seconds.do(job_wrapper) # Kør hvert 10. sekund (kun til hurtig test)

print("Scheduler er startet. Venter på det planlagte tidspunkt for at køre jobbet...")
print(f"Næste kørsel er planlagt til: {schedule.next_run}")

# Dette er et evigt loop, der konstant tjekker, om et job skal køres.
while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except KeyboardInterrupt:
        print("\nScheduler stoppet manuelt.")
        sys.exit(0)