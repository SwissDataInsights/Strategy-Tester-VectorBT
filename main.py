import subprocess
import sys


def run_scripts():
    python_path = sys.executable  # Używa interpretera z bieżącego środowiska

    try:
        # Uruchomienie hour_resample.py
        print("Uruchamiam hour_resample.py...")
        subprocess.run([python_path, "hour_resample.py"], check=True)
        print("Zakończono hour_resample.py.")

        # Uruchomienie data_merge.py
        print("Uruchamiam data_merge.py...")
        subprocess.run([python_path, "data_merge.py"], check=True)
        print("Zakończono data_merge.py.")

    except subprocess.CalledProcessError as e:
        print(f"Błąd podczas wykonywania skryptu: {e}")
    except Exception as e:
        print(f"Nieoczekiwany błąd: {e}")


if __name__ == "__main__":
    run_scripts()
