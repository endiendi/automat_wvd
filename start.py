import os
import sys
import subprocess
from pathlib import Path

# --- Konfiguracja ---
# Nazwa folderu środowiska wirtualnego
VENV_NAME = ".venv"

def find_python_scripts(current_script_name):
    """Znajduje wszystkie skrypty .py w bieżącym folderze, oprócz samego siebie."""
    scripts = []
    for file in Path.cwd().glob('*.py'):
        if file.name != current_script_name:
            scripts.append(file)
    return scripts

def select_script_to_run(scripts):
    """Wyświetla listę skryptów i pozwala użytkownikowi wybrać jeden."""
    if not scripts:
        return None
    
    if len(scripts) == 1:
        print(f"INFO: Znaleziono jeden skrypt do uruchomienia: '{scripts[0].name}'. Zostanie on użyty automatycznie.")
        return scripts[0]
        
    print("\nINFO: Znaleziono wiecej niz jeden skrypt. Wybierz, ktory chcesz uruchomic:")
    for i, script in enumerate(scripts, 1):
        print(f"  {i}. {script.name}")
    
    while True:
        try:
            choice = input(f"Wybierz numer (1-{len(scripts)}): ")
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(scripts):
                return scripts[choice_index]
            else:
                print("Nieprawidlowy numer. Sprobuj ponownie.")
        except (ValueError, IndexError):
            print("Nieprawidlowe dane. Wpisz numer z listy.")
        except (KeyboardInterrupt, EOFError):
            print("\nAnulowano wybór.")
            return None

def main():
    """Główna funkcja skryptu startowego."""
    print("--- Uniwersalny Skrypt Startowy dla Projektow Python ---")
    
    # --- NOWA LOGIKA: Wybór skryptu ---
    current_script_name = Path(__file__).name
    available_scripts = find_python_scripts(current_script_name)
    
    script_to_run_path = select_script_to_run(available_scripts)
    
    if not script_to_run_path:
        print("\nERROR: Nie znaleziono lub nie wybrano zadnego skryptu do uruchomienia.")
        sys.exit(1)
        
    print(f"\nINFO: Wybrano skrypt: '{script_to_run_path.name}'")
    
    # --- Reszta logiki pozostaje taka sama ---
    base_path = Path(__file__).parent
    venv_path = base_path / VENV_NAME

    if not venv_path.is_dir():
        print(f"\nINFO: Srodowisko wirtualne '{VENV_NAME}' nie istnieje. Tworzenie...")
        try:
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
            print("SUCCESS: Srodowisko wirtualne zostalo utworzone.")
        except subprocess.CalledProcessError:
            print("\nERROR: Nie udalo sie utworzyc srodowiska wirtualnego.")
            sys.exit(1)
    else:
        print(f"\nINFO: Srodowisko wirtualne '{VENV_NAME}' juz istnieje.")

    if sys.platform == "win32":
        python_executable = venv_path / "Scripts" / "python.exe"
    else:
        python_executable = venv_path / "bin" / "python"

    if not python_executable.exists():
        print(f"\nERROR: Nie mozna znalezc interpretera Python w srodowisku wirtualnym!")
        sys.exit(1)
    
    print(f"\n--- Uruchamianie '{script_to_run_path.name}' za pomoca srodowiska wirtualnego ---")
    print("-" * 60)
    
    try:
        subprocess.run([str(python_executable), str(script_to_run_path)])
    except Exception as e:
        print(f"\nERROR: Wystapil nieoczekiwany blad podczas uruchamiania skryptu: {e}")

    print("-" * 60)
    print("INFO: Dzialanie skryptu zakonczone.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nINFO: Dzialanie skryptu startowego przerwane przez uzytkownika.")
    finally:
        # Zmieniony komunikat
        print("\nNacisnij dowolny klawisz, aby zakonczyc skrypt.")
        if sys.platform == "win32":
            os.system("pause >nul")
        else:
            # Ta metoda może nadal powodować EOFError, jeśli stdout jest przekierowany,
            # ale dla typowego użycia terminala jest wystarczająca.
            try:
                input()
            except EOFError:
                pass