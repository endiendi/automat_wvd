#
# --- Plik: automat_wvd.py (Finalna, czysta wersja) ---
#
"""
### Zastrzeżenie (Disclaimer) ###

Ten projekt jest przeznaczony wyłącznie do celów edukacyjnych i badawczych.
Używaj go odpowiedzialnie i tylko w odniesieniu do treści, do których posiadasz
legalne prawa. Autor nie ponosi odpowiedzialności za niewłaściwe wykorzystanie
tego narzędzia.

### Cel Skryptu ###
Powtarzalny automat działający z nowszymi wersjami Pythona (np. 3.13). Skrypt
celowo i świadomie odtwarza działającą, choć starszą, konfigurację bibliotek
(`pywidevine==1.8.0`), która jest automatycznie wybierana przez `pip` dla tej
wersji interpretera, i używa odpowiedniej dla niej metody uruchomienia.
Finalny plik `device.wvd` jest zapisywany w bieżącym folderze.
"""
import os
import subprocess
import sys
import shutil
import time
from pathlib import Path

# --- Globalna Konfiguracja ---
VENV_EXTRACTOR_PATH = Path.cwd() / "venv_extractor"
VENV_CREATOR_PATH = Path.cwd() / "venv_creator"
FRIDA_SERVER_FILENAME = "frida-server"
KEYS_FOLDER = Path.cwd() / "device"
# ### ZMIANA: Plik wyjściowy będzie w bieżącym folderze ###
FINAL_WVD_FILENAME = Path.cwd() / "device.wvd"

# --- Funkcje pomocnicze i wspólne ---
def find_android_sdk():
    sdk_path_str = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if sdk_path_str and Path(sdk_path_str).is_dir(): return Path(sdk_path_str)
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            default_path = Path(local_app_data) / "Android" / "Sdk"
            if default_path.is_dir(): return default_path
    elif sys.platform == "linux" or sys.platform == "darwin":
        default_path = Path.home() / "Android" / "Sdk"
        if default_path.is_dir(): return default_path
    return None

SDK_PATH = find_android_sdk()
ADB_PATH = None
if SDK_PATH:
    ADB_EXECUTABLE = "adb.exe" if sys.platform == "win32" else "adb"
    ADB_PATH = SDK_PATH / "platform-tools" / ADB_EXECUTABLE

def get_venv_path(venv_path: Path, executable: str):
    if sys.platform == "win32": return venv_path / "Scripts" / f"{executable}.exe"
    else: return venv_path / "bin" / executable

def run_command(command, check=True):
    try:
        result = subprocess.run(command, check=check, capture_output=True, text=True, encoding='utf-8', errors='replace')
        return result
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Polecenie '{' '.join(map(str, e.cmd))}' zakończyło się błędem (kod: {e.returncode}).", file=sys.stderr)
        if e.stdout: print(f"STDOUT:\n{e.stdout}", file=sys.stderr)
        if e.stderr: print(f"STDERR:\n{e.stderr}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print(f"ERROR: Nie znaleziono polecenia: {command[0]}", file=sys.stderr)
        return None

# --- Faza 1: Ekstrakcja kluczy z urządzenia ---
def run_extraction_phase():
    print("\n" + "="*60 + "\n=== FAZA 1: POBIERANIE KLUCZY Z URZĄDZENIA ===\n" + "="*60)
    print(f"\n--- Tworzenie środowiska wirtualnego w '{VENV_EXTRACTOR_PATH}'... ---")
    if not run_command([sys.executable, "-m", "venv", str(VENV_EXTRACTOR_PATH)]): return None, False, None, None
    pip_exe = get_venv_path(VENV_EXTRACTOR_PATH, "pip")
    print("--- Instalowanie 'keydive'... ---")
    result = run_command([str(pip_exe), "install", "--no-cache-dir", "keydive"])
    if not result: return None, False, None, None
    print(result.stdout)
    print("\n--- Wybór urządzenia ADB... ---")
    try:
        result = subprocess.run([str(ADB_PATH), "devices"], capture_output=True, text=True, check=True, encoding='utf-8')
        lines = result.stdout.strip().splitlines()
        devices = [line.split()[0] for line in lines[1:] if line.strip() and "device" in line]
        if not devices:
            print("ERROR: Nie znaleziono żadnego podłączonego urządzenia ADB."); return None, False, None, None
        if len(devices) == 1:
            device_serial = devices[0]; print(f"SUCCESS: Znaleziono jedno urządzenie ADB: {device_serial}. Zostanie ono użyte automatycznie.")
        else:
            print("INFO: Znaleziono więcej niż jedno urządzenie..."); [print(f"  {i}. {device}") for i, device in enumerate(devices, 1)]
            while True:
                try:
                    choice_index = int(input(f"Wybierz numer (1-{len(devices)}): ")) - 1
                    if 0 <= choice_index < len(devices):
                        device_serial = devices[choice_index]; break
                    else: print("Nieprawidłowy numer.")
                except ValueError: print("Nieprawidłowe dane.")
    except Exception as e:
        print(f"ERROR: Błąd podczas komunikacji z ADB: {e}"); return None, False, None, None
    print(f"\n--- Przygotowywanie środowiska na urządzeniu '{device_serial}'... ---")
    subprocess.run([str(ADB_PATH), "-s", device_serial, "root"], capture_output=True, text=True, timeout=10)
    time.sleep(3)
    if not Path(FRIDA_SERVER_FILENAME).is_file():
        print(f"ERROR: Nie znaleziono pliku serwera Frida ('{FRIDA_SERVER_FILENAME}')."); return device_serial, False, None, None
    subprocess.run([str(ADB_PATH), "-s", device_serial, "push", FRIDA_SERVER_FILENAME, "/data/local/tmp/frida-server"], check=True)
    subprocess.run([str(ADB_PATH), "-s", device_serial, "shell", "killall frida-server"], capture_output=True)
    time.sleep(1)
    subprocess.run([str(ADB_PATH), "-s", device_serial, "shell", "chmod 755 /data/local/tmp/frida-server"], check=True)
    subprocess.Popen([str(ADB_PATH), "-s", device_serial, "shell", "/data/local/tmp/frida-server &"])
    time.sleep(2)
    print("SUCCESS: Środowisko na urządzeniu przygotowane.")
    print("\n--- Uruchamianie 'keydive' ---\n--- WSKAZÓWKA: Odtwórz wideo na https://shaka-player-demo.appspot.com lub https://bitmovin.com/demos/drm ---")
    env = os.environ.copy(); env["PATH"] = str(ADB_PATH.parent) + os.pathsep + env.get("PATH", "")
    keydive_command = [str(get_venv_path(VENV_EXTRACTOR_PATH, "keydive")), "-s", device_serial]
    try:
        subprocess.run(keydive_command, env=env, check=True)
    except (subprocess.CalledProcessError, KeyboardInterrupt):
        print(f"\nERROR: Proces 'keydive' zakończył się błędem lub został przerwany.", file=sys.stderr); return device_serial, False, None, None
    print("\n--- Weryfikacja pobranych plików... ---")
    if not KEYS_FOLDER.is_dir():
        print(f"ERROR: Folder '{KEYS_FOLDER}' nie został utworzony.", file=sys.stderr); return device_serial, False, None, None
    client_id_files, private_key_files = list(KEYS_FOLDER.rglob('client_id.bin')), list(KEYS_FOLDER.rglob('private_key.pem'))
    if client_id_files and private_key_files:
        client_id_path, private_key_path = client_id_files[0], private_key_files[0]
        print(f"SUCCESS: Znaleziono client_id.bin w: {client_id_path}"); print(f"SUCCESS: Znaleziono private_key.pem w: {private_key_path}")
        return device_serial, True, client_id_path, private_key_path
    else:
        print(f"ERROR: Nie znaleziono plików kluczy w folderze '{KEYS_FOLDER}'.", file=sys.stderr); return device_serial, False, None, None

# --- Faza 2: Tworzenie pliku .wvd ---
def run_creation_phase(client_id_path: Path, priv_key_path: Path):
    print("\n" + "="*60 + "\n=== FAZA 2: TWORZENIE PLIKU WVD ===\n" + "="*60)
    print(f"\n--- Tworzenie środowiska wirtualnego w '{VENV_CREATOR_PATH}'... ---")
    if not run_command([sys.executable, "-m", "venv", str(VENV_CREATOR_PATH)]): return False
    
    pip_exe = get_venv_path(VENV_CREATOR_PATH, "pip")
    print("--- Instalacja 'pywidevine'... ---")
    install_command = [str(pip_exe), "install", "--no-cache-dir", "pywidevine"]
    result = run_command(install_command)
    if not result:
        print("ERROR: Instalacja pywidevine nie powiodła się.", file=sys.stderr); return False
    print(result.stdout)
    print("\nSUCCESS: Środowisko `creator` zostało pomyślnie skonfigurowane.")
    
    print(f"\n--- Tworzenie pliku {FINAL_WVD_FILENAME.name}... ---")
    
    # ### ZMIANA: Tworzymy folder tymczasowy, a potem przenosimy plik ###
    temp_output_folder = VENV_CREATOR_PATH / "temp_wvd_out"
    temp_output_folder.mkdir()

    pywidevine_exe = get_venv_path(VENV_CREATOR_PATH, "pywidevine")
    command = [
        str(pywidevine_exe), "create-device",
        "-k", str(priv_key_path), "-c", str(client_id_path),
        "-t", "ANDROID", "-l", "3", "-o", str(temp_output_folder)
    ]

    result = run_command(command)
    if result and result.returncode == 0:
        wvd_files = list(temp_output_folder.glob('*.wvd'))
        if wvd_files:
            source_file = wvd_files[0]
            # Przenosimy i zmieniamy nazwę na docelową "device.wvd"
            shutil.move(source_file, FINAL_WVD_FILENAME)
            print(f"SUCCESS: Pomyślnie utworzono plik wynikowy: {FINAL_WVD_FILENAME}")
            return True
        else:
            print(f"ERROR: Polecenie pywidevine zakończyło się, ale nie znaleziono pliku .wvd.", file=sys.stderr); return False
    else:
        print("ERROR: Faza 2 nie powiodła się. Sprawdź powyższe komunikaty błędów z pywidevine.", file=sys.stderr); return False

# --- Główna funkcja i sprzątanie ---
def cleanup(device_serial=None):
    print("\n" + "="*60 + "\n=== FAZA SPRZĄTANIA ===\n" + "="*60)
    if device_serial and ADB_PATH:
        print(f"--- Zatrzymywanie serwera Frida na urządzeniu '{device_serial}'... ---")
        subprocess.run([str(ADB_PATH), "-s", device_serial, "shell", "killall frida-server"], capture_output=True, timeout=5)
        print("INFO: Wysłano polecenie zatrzymania serwera Frida.")
    for path in [VENV_EXTRACTOR_PATH, VENV_CREATOR_PATH, KEYS_FOLDER]:
        if path.exists():
            try:
                print(f"--- Usuwanie tymczasowego folderu '{path.name}'... ---")
                if path.is_dir(): shutil.rmtree(path)
                else: path.unlink()
                print("SUCCESS: Usunięto.")
            except OSError as e: print(f"WARNING: Nie udało się usunąć '{path.name}'. Błąd: {e}", file=sys.stderr)

def main():
    print("---- AUTOMATYCZNY GENERATOR PLIKU WIDEVINE ----")
    if not ADB_PATH or not ADB_PATH.is_file():
        print("\nERROR: Nie udało się zlokalizować 'adb'.", file=sys.stderr); sys.exit(1)
    device_serial = None
    try:
        device_serial, extraction_success, client_id_path, priv_key_path = run_extraction_phase()
        if not extraction_success:
            print("\nPrzerwano proces z powodu błędu w Fazie 1.", file=sys.stderr); sys.exit(1)
        creation_success = run_creation_phase(client_id_path, priv_key_path)
        if creation_success:
            print("\n\n" + "*"*60 + "\n**** PROCES ZAKOŃCZONY POMYŚLNIE! ****\n" + f"**** Twój plik '{FINAL_WVD_FILENAME.name}' jest gotowy. ****\n" + "*"*60)
        else:
            print("\nPrzerwano proces z powodu błędu w Fazie 2.", file=sys.stderr); sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nINFO: Działanie skryptu przerwane przez użytkownika (Ctrl+C).")
    except Exception as e:
        print(f"\n\nCRITICAL: Wystąpił nieoczekiwany globalny błąd: {e}", file=sys.stderr)
    finally:
        cleanup(device_serial)

if __name__ == "__main__":
    main()