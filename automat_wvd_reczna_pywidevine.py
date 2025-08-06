#
# --- Plik: automat_wvd_reczna_pywidevine_multilang.py (Wersja z wyborem języka) ---
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

======================================================================================

### Disclaimer ###

This project is intended for educational and research purposes only.
Use it responsibly and only with content to which you have
legal rights. The author is not responsible for any misuse
of this tool.

### Script's Purpose ###
A repeatable automaton that works with newer Python versions (e.g., 3.13). The
script intentionally and consciously replicates a working, albeit older, library
setup (`pywidevine==1.8.0`), which is automatically selected by `pip` for this
interpreter version, and uses the appropriate method to run it.
The final `device.wvd` file is saved in the current folder.
"""
import os
import subprocess
import sys
import shutil
import time
from pathlib import Path

# --- Global Language Configuration ---
LANG = "pl"  # Domyślny język, zostanie zmieniony przez select_language()

MESSAGES = {
    "lang_prompt": {
        "pl": "Wybierz wersję językową (Choose language version):\n 1. Polski (default)\n 2. English\nWybór [1]: ",
        "en": "Wybierz wersję językową (Choose language version):\n 1. Polski (default)\n 2. English\nChoice [1]: "
    },
    "main_title": {
        "pl": "---- AUTOMATYCZNY GENERATOR PLIKU WIDEVINE ----",
        "en": "---- AUTOMATIC WIDEVINE FILE GENERATOR ----"
    },
    "adb_not_found": {
        "pl": "\nERROR: Nie udało się zlokalizować 'adb'.",
        "en": "\nERROR: Could not locate 'adb'."
    },
    "phase1_header": {
        "pl": "\n" + "="*60 + "\n=== FAZA 1: POBIERANIE KLUCZY Z URZĄDZENIA ===\n" + "="*60,
        "en": "\n" + "="*60 + "\n=== PHASE 1: EXTRACTING KEYS FROM DEVICE ===\n" + "="*60
    },
    "creating_venv": {
        "pl": "\n--- Tworzenie środowiska wirtualnego w '{path}'... ---",
        "en": "\n--- Creating a virtual environment in '{path}'... ---"
    },
    "installing_lib": {
        "pl": "--- Instalowanie '{library}'... ---",
        "en": "--- Installing '{library}'... ---"
    },
    "select_adb_device": {
        "pl": "\n--- Wybór urządzenia ADB... ---",
        "en": "\n--- Selecting ADB device... ---"
    },
    "no_adb_device_found": {
        "pl": "ERROR: Nie znaleziono żadnego podłączonego urządzenia ADB.",
        "en": "ERROR: No connected ADB devices found."
    },
    "single_adb_device_found": {
        "pl": "SUCCESS: Znaleziono jedno urządzenie ADB: {serial}. Zostanie ono użyte automatycznie.",
        "en": "SUCCESS: Found one ADB device: {serial}. It will be used automatically."
    },
    "multiple_adb_devices_found": {
        "pl": "INFO: Znaleziono więcej niż jedno urządzenie...",
        "en": "INFO: More than one device found..."
    },
    "select_device_prompt": {
        "pl": "Wybierz numer (1-{count}): ",
        "en": "Select number (1-{count}): "
    },
    "invalid_number": {
        "pl": "Nieprawidłowy numer.",
        "en": "Invalid number."
    },
    "invalid_input": {
        "pl": "Nieprawidłowe dane.",
        "en": "Invalid input."
    },
    "adb_comm_error": {
        "pl": "ERROR: Błąd podczas komunikacji z ADB: {e}",
        "en": "ERROR: Error during ADB communication: {e}"
    },
    "preparing_device_env": {
        "pl": "\n--- Przygotowywanie środowiska na urządzeniu '{serial}'... ---",
        "en": "\n--- Preparing environment on device '{serial}'... ---"
    },
    "frida_server_not_found": {
        "pl": "ERROR: Nie znaleziono pliku serwera Frida ('{filename}').",
        "en": "ERROR: Frida server file ('{filename}') not found."
    },
    "device_env_success": {
        "pl": "SUCCESS: Środowisko na urządzeniu przygotowane.",
        "en": "SUCCESS: Environment on the device has been prepared."
    },
    "running_keydive": {
        "pl": "\n--- Uruchamianie 'keydive' ---\n\n--- WSKAZÓWKA: Odtwórz wideo na https://shaka-player-demo.appspot.com lub https://bitmovin.com/demos/drm ---\n",
        "en": "\n--- Running 'keydive' ---\n\n--- HINT: Play a video on https://shaka-player-demo.appspot.com or https://bitmovin.com/demos/drm ---\n"
    },
    "keydive_error": {
        "pl": "\nERROR: Proces 'keydive' zakończył się błędem lub został przerwany.",
        "en": "\nERROR: The 'keydive' process failed or was interrupted."
    },
    "verifying_files": {
        "pl": "\n--- Weryfikacja pobranych plików... ---",
        "en": "\n--- Verifying downloaded files... ---"
    },
    "keys_folder_not_created": {
        "pl": "ERROR: Folder '{folder}' nie został utworzony.",
        "en": "ERROR: Folder '{folder}' was not created."
    },
    "client_id_found": {
        "pl": "SUCCESS: Znaleziono client_id.bin w: {path}",
        "en": "SUCCESS: Found client_id.bin at: {path}"
    },
    "private_key_found": {
        "pl": "SUCCESS: Znaleziono private_key.pem w: {path}",
        "en": "SUCCESS: Found private_key.pem at: {path}"
    },
    "key_files_not_found": {
        "pl": "ERROR: Nie znaleziono plików kluczy w folderze '{folder}'.",
        "en": "ERROR: Key files not found in folder '{folder}'."
    },
    "phase2_header": {
        "pl": "\n" + "="*60 + "\n=== FAZA 2: TWORZENIE PLIKU WVD ===\n" + "="*60,
        "en": "\n" + "="*60 + "\n=== PHASE 2: CREATING WVD FILE ===\n" + "="*60
    },
    "pywidevine_install_fail": {
        "pl": "ERROR: Instalacja pywidevine nie powiodła się.",
        "en": "ERROR: pywidevine installation failed."
    },
    "creator_env_success": {
        "pl": "\nSUCCESS: Środowisko `creator` zostało pomyślnie skonfigurowane.",
        "en": "\nSUCCESS: `creator` environment configured successfully."
    },
    "creating_wvd_file": {
        "pl": "\n--- Tworzenie pliku {filename}... ---",
        "en": "\n--- Creating {filename} file... ---"
    },
    "wvd_file_created_success": {
        "pl": "SUCCESS: Pomyślnie utworzono plik wynikowy: {filename}",
        "en": "SUCCESS: Successfully created output file: {filename}"
    },
    "wvd_file_not_found_after_run": {
        "pl": "ERROR: Polecenie pywidevine zakończyło się, ale nie znaleziono pliku .wvd.",
        "en": "ERROR: pywidevine command finished, but no .wvd file was found."
    },
    "phase2_failed": {
        "pl": "ERROR: Faza 2 nie powiodła się. Sprawdź powyższe komunikaty błędów z pywidevine.",
        "en": "ERROR: Phase 2 failed. Check the pywidevine error messages above."
    },
    "cleanup_header": {
        "pl": "\n" + "="*60 + "\n=== FAZA SPRZĄTANIA ===\n" + "="*60,
        "en": "\n" + "="*60 + "\n=== CLEANUP PHASE ===\n" + "="*60
    },
    "stopping_frida": {
        "pl": "--- Zatrzymywanie serwera Frida na urządzeniu '{serial}'... ---",
        "en": "--- Stopping Frida server on device '{serial}'... ---"
    },
    "frida_stop_sent": {
        "pl": "INFO: Wysłano polecenie zatrzymania serwera Frida.",
        "en": "INFO: Sent command to stop Frida server."
    },
    "removing_temp_folder": {
        "pl": "--- Usuwanie tymczasowego folderu '{folder}'... ---",
        "en": "--- Removing temporary folder '{folder}'... ---"
    },
    "removed_success": {
        "pl": "SUCCESS: Usunięto.",
        "en": "SUCCESS: Removed."
    },
    "remove_warning": {
        "pl": "WARNING: Nie udało się usunąć '{folder}'. Błąd: {e}",
        "en": "WARNING: Failed to remove '{folder}'. Error: {e}"
    },
    "phase1_interrupted": {
        "pl": "\nPrzerwano proces z powodu błędu w Fazie 1.",
        "en": "\nProcess aborted due to an error in Phase 1."
    },
    "process_finished_success": {
        "pl": "\n\n" + "*"*60 + "\n**** PROCES ZAKOŃCZONY POMYŚLNIE! ****\n" + "**** Twój plik '{filename}' jest gotowy. ****\n" + "*"*60,
        "en": "\n\n" + "*"*60 + "\n**** PROCESS COMPLETED SUCCESSFULLY! ****\n" + "**** Your file '{filename}' is ready. ****\n" + "*"*60
    },
    "phase2_interrupted": {
        "pl": "\nPrzerwano proces z powodu błędu w Fazie 2.",
        "en": "\nProcess aborted due to an error in Phase 2."
    },
    "user_interrupt": {
        "pl": "\n\nINFO: Działanie skryptu przerwane przez użytkownika (Ctrl+C).",
        "en": "\n\nINFO: Script execution interrupted by user (Ctrl+C)."
    },
    "critical_error": {
        "pl": "\n\nCRITICAL: Wystąpił nieoczekiwany globalny błąd: {e}",
        "en": "\n\nCRITICAL: An unexpected global error occurred: {e}"
    },
    "command_error": {
        "pl": "ERROR: Polecenie '{cmd}' zakończyło się błędem (kod: {code}).",
        "en": "ERROR: Command '{cmd}' failed with exit code {code}."
    },
    "command_not_found": {
        "pl": "ERROR: Nie znaleziono polecenia: {cmd}",
        "en": "ERROR: Command not found: {cmd}"
    }
}

def _(key):
    """Pobiera przetłumaczony tekst na podstawie globalnego języka."""
    return MESSAGES[key][LANG]

# --- Globalna Konfiguracja ---
VENV_EXTRACTOR_PATH = Path.cwd() / "venv_extractor"
VENV_CREATOR_PATH = Path.cwd() / "venv_creator"
FRIDA_SERVER_FILENAME = "frida-server"
KEYS_FOLDER = Path.cwd() / "device"
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
        print(_("command_error").format(cmd=' '.join(map(str, e.cmd)), code=e.returncode), file=sys.stderr)
        if e.stdout: print(f"STDOUT:\n{e.stdout}", file=sys.stderr)
        if e.stderr: print(f"STDERR:\n{e.stderr}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print(_("command_not_found").format(cmd=command[0]), file=sys.stderr)
        return None

# --- Faza 1: Ekstrakcja kluczy z urządzenia ---
def run_extraction_phase():
    print(_("phase1_header"))
    print(_("creating_venv").format(path=VENV_EXTRACTOR_PATH))
    if not run_command([sys.executable, "-m", "venv", str(VENV_EXTRACTOR_PATH)]): return None, False, None, None
    pip_exe = get_venv_path(VENV_EXTRACTOR_PATH, "pip")
    print(_("installing_lib").format(library='keydive'))
    result = run_command([str(pip_exe), "install", "--no-cache-dir", "keydive"])
    if not result: return None, False, None, None
    print(result.stdout)
    print(_("select_adb_device"))
    try:
        result = subprocess.run([str(ADB_PATH), "devices"], capture_output=True, text=True, check=True, encoding='utf-8')
        lines = result.stdout.strip().splitlines()
        devices = [line.split()[0] for line in lines[1:] if line.strip() and "device" in line]
        if not devices:
            print(_("no_adb_device_found")); return None, False, None, None
        if len(devices) == 1:
            device_serial = devices[0]; print(_("single_adb_device_found").format(serial=device_serial))
        else:
            print(_("multiple_adb_devices_found")); [print(f"  {i}. {device}") for i, device in enumerate(devices, 1)]
            while True:
                try:
                    choice_index = int(input(_("select_device_prompt").format(count=len(devices)))) - 1
                    if 0 <= choice_index < len(devices):
                        device_serial = devices[choice_index]; break
                    else: print(_("invalid_number"))
                except ValueError: print(_("invalid_input"))
    except Exception as e:
        print(_("adb_comm_error").format(e=e)); return None, False, None, None
    print(_("preparing_device_env").format(serial=device_serial))
    subprocess.run([str(ADB_PATH), "-s", device_serial, "root"], capture_output=True, text=True, timeout=10)
    time.sleep(3)
    if not Path(FRIDA_SERVER_FILENAME).is_file():
        print(_("frida_server_not_found").format(filename=FRIDA_SERVER_FILENAME)); return device_serial, False, None, None
    subprocess.run([str(ADB_PATH), "-s", device_serial, "push", FRIDA_SERVER_FILENAME, "/data/local/tmp/frida-server"], check=True)
    subprocess.run([str(ADB_PATH), "-s", device_serial, "shell", "killall frida-server"], capture_output=True)
    time.sleep(1)
    subprocess.run([str(ADB_PATH), "-s", device_serial, "shell", "chmod 755 /data/local/tmp/frida-server"], check=True)
    subprocess.Popen([str(ADB_PATH), "-s", device_serial, "shell", "/data/local/tmp/frida-server &"])
    time.sleep(2)
    print(_("device_env_success"))
    print(_("running_keydive"))
    env = os.environ.copy(); env["PATH"] = str(ADB_PATH.parent) + os.pathsep + env.get("PATH", "")
    keydive_command = [str(get_venv_path(VENV_EXTRACTOR_PATH, "keydive")), "-s", device_serial]
    try:
        subprocess.run(keydive_command, env=env, check=True)
    except (subprocess.CalledProcessError, KeyboardInterrupt):
        print(_("keydive_error"), file=sys.stderr); return device_serial, False, None, None
    print(_("verifying_files"))
    if not KEYS_FOLDER.is_dir():
        print(_("keys_folder_not_created").format(folder=KEYS_FOLDER), file=sys.stderr); return device_serial, False, None, None
    client_id_files, private_key_files = list(KEYS_FOLDER.rglob('client_id.bin')), list(KEYS_FOLDER.rglob('private_key.pem'))
    if client_id_files and private_key_files:
        client_id_path, private_key_path = client_id_files[0], private_key_files[0]
        print(_("client_id_found").format(path=client_id_path)); print(_("private_key_found").format(path=private_key_path))
        return device_serial, True, client_id_path, private_key_path
    else:
        print(_("key_files_not_found").format(folder=KEYS_FOLDER), file=sys.stderr); return device_serial, False, None, None

# --- Faza 2: Tworzenie pliku .wvd ---
def run_creation_phase(client_id_path: Path, priv_key_path: Path):
    print(_("phase2_header"))
    print(_("creating_venv").format(path=VENV_CREATOR_PATH))
    if not run_command([sys.executable, "-m", "venv", str(VENV_CREATOR_PATH)]): return False
    
    pip_exe = get_venv_path(VENV_CREATOR_PATH, "pip")
    print(_("installing_lib").format(library='pywidevine'))
    install_command = [str(pip_exe), "install", "--no-cache-dir", "pywidevine"]
    result = run_command(install_command)
    if not result:
        print(_("pywidevine_install_fail"), file=sys.stderr); return False
    print(result.stdout)
    print(_("creator_env_success"))
    
    print(_("creating_wvd_file").format(filename=FINAL_WVD_FILENAME.name))
    
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
            shutil.move(source_file, FINAL_WVD_FILENAME)
            print(_("wvd_file_created_success").format(filename=FINAL_WVD_FILENAME))
            return True
        else:
            print(_("wvd_file_not_found_after_run"), file=sys.stderr); return False
    else:
        print(_("phase2_failed"), file=sys.stderr); return False

# --- Główna funkcja i sprzątanie ---
def cleanup(device_serial=None):
    print(_("cleanup_header"))
    if device_serial and ADB_PATH:
        print(_("stopping_frida").format(serial=device_serial))
        subprocess.run([str(ADB_PATH), "-s", device_serial, "shell", "killall frida-server"], capture_output=True, timeout=5)
        print(_("frida_stop_sent"))
    for path in [VENV_EXTRACTOR_PATH, VENV_CREATOR_PATH, KEYS_FOLDER]:
        if path.exists():
            try:
                print(_("removing_temp_folder").format(folder=path.name))
                if path.is_dir(): shutil.rmtree(path)
                else: path.unlink()
                print(_("removed_success"))
            except OSError as e: print(_("remove_warning").format(folder=path.name, e=e), file=sys.stderr)

def select_language():
    """Prosi użytkownika o wybór języka i ustawia globalną zmienną LANG."""
    global LANG
    while True:
        choice = input(_("lang_prompt")).strip()
        if choice == '1' or choice == '':
            LANG = 'pl'
            return
        elif choice == '2':
            LANG = 'en'
            return
        else:
            print("Invalid choice. Please enter 1 or 2.")

def main():
    select_language()
    print(_("main_title"))
    if not ADB_PATH or not ADB_PATH.is_file():
        print(_("adb_not_found"), file=sys.stderr); sys.exit(1)
    device_serial = None
    try:
        device_serial, extraction_success, client_id_path, priv_key_path = run_extraction_phase()
        if not extraction_success:
            print(_("phase1_interrupted"), file=sys.stderr); sys.exit(1)
        creation_success = run_creation_phase(client_id_path, priv_key_path)
        if creation_success:
            print(_("process_finished_success").format(filename=FINAL_WVD_FILENAME.name))
        else:
            print(_("phase2_interrupted"), file=sys.stderr); sys.exit(1)
    except KeyboardInterrupt:
        print(_("user_interrupt"))
    except Exception as e:
        print(_("critical_error").format(e=e), file=sys.stderr)
    finally:
        cleanup(device_serial)

if __name__ == "__main__":
    main()