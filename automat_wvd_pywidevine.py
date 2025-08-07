#
# --- Plik: automat_wvd_reczna_pywidevine.py (Wersja z ulepszoną automatyzacją) ---
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
import logging
from pathlib import Path
import json
import urllib.request
import lzma

# --- Global Language Configuration ---
LANG = "pl"  # Domyślny język, zostanie zmieniony przez select_language()

# --- Global Logging Configuration ---
LOG_FILENAME = "diagnostic_log.txt"
logger = logging.getLogger(__name__)
g_script_successful = False
g_user_interrupted = False


# --- Multilingual Messages ---
MESSAGES = {
    "lang_prompt": {
        "pl": "\nWybierz wersję językową (Choose language version):\n\n 1. Polski (default)\n 2. English\nWybór [1]: ",
        "en": "\nChoose language version:\n\n 1. Polski (default)\n 2. English\nChoice [1]: "
    },
    "main_title": {
        "pl": "\n---- AUTOMATYCZNY GENERATOR PLIKU WIDEVINE ----",
        "en": "\n---- AUTOMATIC WIDEVINE FILE GENERATOR ----"
    },
    "adb_not_found": {
        "pl": "\nCRITICAL: Nie udało się zlokalizować 'adb'. Upewnij się, że Android SDK jest zainstalowany i zmienna środowiskowa ANDROID_HOME jest ustawiona poprawnie.",
        "en": "\nCRITICAL: Could not locate 'adb'. Make sure the Android SDK is installed and the ANDROID_HOME environment variable is set correctly."
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
        "pl": "INFO: Nie znaleziono żadnego podłączonego urządzenia ADB. Możesz uruchomić nowe.",
        "en": "INFO: No connected ADB devices found. You can launch a new one."
    },
    "single_adb_device_found": {
        "pl": "INFO: Znaleziono jedno urządzenie: {avd_name} ({serial}).",
        "en": "INFO: Found one device: {avd_name} ({serial})."
    },
    "multiple_adb_devices_found": {
        "pl": "INFO: Znaleziono wiele urządzeń. Wybierz jedno z listy.\n",
        "en": "INFO: Multiple devices found. Please select one from the list.\n"
    },
    "select_device_prompt": {
        "pl": "Wybierz numer (1-{count}) lub [U] aby uruchomić nowy emulator: ",
        "en": "Select number (1-{count}) or [L] to launch a new emulator: "
    },
    "device_display_format": {
        "pl": "  {index}. {avd_name} ({serial})",
        "en": "  {index}. {avd_name} ({serial})"
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
        "en": "SUCCESS: Device environment prepared."
    },
    "running_keydive": {
        "pl": "\n--- Uruchamianie 'keydive' ---\n",
        "en": "\n--- Running 'keydive' ---\n"
    },
    "keydive_manual_hint": {
        "pl": "--- WSKAZÓWKA: Odtwórz wideo na https://shaka-player-demo.appspot.com lub https://bitmovin.com/demos/drm ---",
        "en": "--- HINT: Play a video on https://shaka-player-demo.appspot.com or https://bitmovin.com/demos/drm ---"
    },
    "manual_play_hint": {
        "pl": "WSKAZÓWKA: Jeśli wideo nie uruchomiło się automatycznie, naciśnij przycisk 'Play' przy wideo obsługującym DRM na stronie, aby wywołać proces DRM. \nMoże również pojawić się komunikat z prośbą o zalogowanie się na konto Google — nie musisz się logować.",
        "en": "HINT: If the video does not start automatically, press the 'Play' button on a DRM-enabled video on the page to trigger the DRM process. \nA message asking you to sign in to a Google account may also appear — you do not need to sign in."
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
        "pl": "\n\n" + "*"*60 + "\n**** PROCES ZAKOŃCZONY POMYŚLNIE! ****\n" + "**** Plik '{filename}' jest gotowy. ****\n" + "*"*60,
        "en": "\n\n" + "*"*60 + "\n**** PROCESS COMPLETED SUCCESSFULLY! ****\n" + "**** The file '{filename}' is ready. ****\n" + "*"*60
    },
    "phase2_interrupted": {
        "pl": "\nPrzerwano proces z powodu błędu w Fazie 2.",
        "en": "\nProcess aborted due to an error in Phase 2."
    },
    "user_interrupt": {
        "pl": "\n\nPrzerwano przez użytkownika.",
        "en": "\n\nInterrupted by user."
    },
    "critical_error": {
        "pl": "\n\nCRITICAL: Wystąpił nieoczekiwany globalny błąd: {e}",
        "en": "\n\nCRITICAL: An unexpected global error occurred: {e}"
    },
    "command_error": {
        "pl": "ERROR: Polecenie '{cmd}' zakończyło się błędem (kod: {code}).",
        "en": "ERROR: Command '{cmd}' failed with exit code {code}."
    },
    "command_timeout": {
        "pl": "ERROR: Polecenie '{cmd}' przekroczyło limit czasu.",
        "en": "ERROR: Command '{cmd}' timed out."
    },
    "command_not_found": {
        "pl": "ERROR: Nie znaleziono polecenia: {cmd}",
        "en": "ERROR: Command not found: {cmd}"
    },
    "venv_creation_notice": {
        "pl": "INFO: Tworzenie środowisk wirtualnych i instalacja bibliotek może potrwać kilka minut. Prosimy o cierpliwość.",
        "en": "INFO: Creating virtual environments and installing libraries may take a few minutes. Please be patient."
    },
    "press_enter_to_exit": {
        "pl": "\nNaciśnij Enter, aby zakończyć działanie skryptu...",
        "en": "\nPress Enter to exit the script..."
    },
    "cleanup_warning": {
        "pl": "\nWARNING: Znaleziono pozostałości z poprzedniego uruchomienia:",
        "en": "\nWARNING: Found leftovers from a previous run:"
    },
    "cleanup_prompt": {
        "pl": "Czy chcesz je teraz usunąć, aby kontynuować? [T/n]: ",
        "en": "Do you want to remove them now to continue? [Y/n]: "
    },
    "cleanup_in_progress": {
        "pl": "--- Usuwanie {path}...",
        "en": "--- Removing {path}..."
    },
    "cleanup_success": {
        "pl": "SUCCESS: Pomyślnie posprzątano.",
        "en": "SUCCESS: Cleanup successful."
    },
    "cleanup_aborted": {
        "pl": "INFO: Sprzątanie anulowane. Skrypt nie może kontynuować.",
        "en": "INFO: Cleanup aborted. The script cannot continue."
    },
    "frida_server_missing_error": {
        "pl": """
CRITICAL: Nie można kontynuować bez pliku '{filename}'.
Uruchom skrypt ponownie i zgódź się na automatyczne pobranie.""",
        "en": """
CRITICAL: Cannot continue without the '{filename}' file.
Please restart the script and agree to the automatic download."""
    },
    "checking_architecture": {
        "pl": "\n--- Sprawdzanie architektury urządzenia... ---",
        "en": "\n--- Checking device architecture... ---"
    },
    "architecture_found": {
        "pl": "SUCCESS: Wykryta architektura urządzenia: {arch}",
        "en": "SUCCESS: Detected device architecture: {arch}"
    },
    "architecture_fail": {
        "pl": "ERROR: Nie udało się ustalić architektury urządzenia. Nie można automatycznie pobrać serwera Frida.",
        "en": "ERROR: Could not determine device architecture. Cannot automatically download Frida server."
    },
    "frida_exists_prompt": {
        "pl": "INFO: Plik 'frida-server' już istnieje. Chcesz go użyć, czy pobrać najnowszą wersję?\n(U)żyj istniejącego, (P)obierz najnowszą: [U/p]: ",
        "en": "INFO: The 'frida-server' file already exists. Do you want to use it or download the latest version?\n(U)se existing, (D)ownload latest: [U/d] "
    },
    "frida_download_prompt": {
        "pl": "INFO: Plik 'frida-server' jest wymagany. Czy chcesz go teraz automatycznie pobrać? [T/n]: ",
        "en": "INFO: The 'frida-server' file is required. Do you want to download it automatically now? [Y/n]: "
    },
    "frida_api_fail": {
        "pl": "ERROR: Nie udało się połączyć z API GitHub w celu znalezienia najnowszej wersji Frida.",
        "en": "ERROR: Failed to connect to the GitHub API to find the latest Frida release."
    },
    "frida_asset_not_found": {
        "pl": "ERROR: Nie znaleziono odpowiedniego pliku serwera Frida dla architektury '{arch}' w najnowszym wydaniu.",
        "en": "ERROR: Could not find a suitable Frida server asset for architecture '{arch}' in the latest release."
    },
    "frida_downloading": {
        "pl": "--- Pobieranie serwera Frida dla architektury {arch}... ---",
        "en": "--- Downloading Frida server for {arch} architecture... ---"
    },
    "frida_download_fail": {
        "pl": "ERROR: Pobieranie pliku serwera Frida nie powiodło się.",
        "en": "ERROR: Failed to download the Frida server file."
    },
    "frida_unpacking": {
        "pl": "--- Rozpakowywanie archiwum serwera Frida... ---",
        "en": "--- Unpacking the Frida server archive... ---"
    },
    "frida_unpack_fail": {
        "pl": "ERROR: Rozpakowywanie pliku serwera Frida nie powiodło się.",
        "en": "ERROR: Failed to unpack the Frida server file."
    },
    "frida_success": {
        "pl": "SUCCESS: Serwer Frida został pomyślnie pobrany i przygotowany jako '{filename}'.",
        "en": "SUCCESS: Frida server was successfully downloaded and prepared as '{filename}'."
    },
    "log_file_kept": {
        "pl": "\nINFO: Proces zakończył się błędem. Plik diagnostyczny został zapisany jako '{log_filename}' w celu analizy.",
        "en": "\nINFO: The process failed. A diagnostic log file has been saved as '{log_filename}' for analysis."
    },
    "log_file_removing": {
        "pl": "--- Usuwanie pliku diagnostycznego '{log_filename}'... ---",
        "en": "--- Removing diagnostic log file '{log_filename}'... ---"
    },
    "log_file_removed": {
        "pl": "SUCCESS: Usunięto plik diagnostyczny.",
        "en": "SUCCESS: Diagnostic log file removed."
    },
    "frida_using_existing": {
        "pl": "INFO: Używam istniejącego pliku 'frida-server' zgodnie z poleceniem.",
        "en": "INFO: Using existing 'frida-server' file as requested."
    },
    "invalid_lang_choice": {
        "pl": "Nieprawidłowy wybór. Wprowadź 1 lub 2.",
        "en": "Invalid choice. Please enter 1 or 2."
    },
    "log_file_remove_warning": {
        "pl": "WARNING: Nie można usunąć pliku logu '{log_filename}'. Błąd: {e}",
        "en": "WARNING: Could not remove log file '{log_filename}'. Error: {e}"
    },
    # START: Nowe komunikaty dla automatyzacji
    "emulator_not_found": {
        "pl": "CRITICAL: Nie udało się zlokalizować 'emulator'. Sprawdź, czy ścieżka do Android SDK jest poprawna.",
        "en": "CRITICAL: Could not locate 'emulator'. Check if the Android SDK path is correct."
    },
    "no_avds_found": {
        "pl": "ERROR: Nie znaleziono żadnych skonfigurowanych emulatorów (AVD). Utwórz AVD w Android Studio.",
        "en": "ERROR: No configured emulators (AVD) found. Please create an AVD in Android Studio."
    },
    "launching_emulator_title": {
        "pl": "\n--- Uruchamianie emulatora ---",
        "en": "\n--- Launching Emulator ---"
    },
    "select_avd_prompt": {
        "pl": "Wybierz numer emulatora do uruchomienia (1-{count}): ",
        "en": "Select emulator number to launch (1-{count}): "
    },
    "launching_avd": {
        "pl": "INFO: Uruchamianie emulatora '{avd_name}'... To może chwilę potrwać.",
        "en": "INFO: Launching emulator '{avd_name}'... This may take a moment."
    },
    "waiting_for_boot": {
        "pl": "INFO: Oczekiwanie na pełne uruchomienie systemu Android...",
        "en": "INFO: Waiting for Android system to fully boot..."
    },
    "emulator_boot_success": {
        "pl": "SUCCESS: Emulator jest gotowy do pracy (serial: {serial}).",
        "en": "SUCCESS: Emulator is ready (serial: {serial})."
    },
    "prompt_auto_play": {
        "pl": "\nCzy chcesz, abym automatycznie otworzył stronę z wideo DRM? [T/n]: ",
        "en": "\nDo you want me to automatically open a DRM video page? [Y/n]: "
    },
    "select_drm_page": {
        "pl": "\nWybierz stronę do otwarcia:\n",
        "en": "\nSelect a page to open:\n"
    },
    "select_drm_page_prompt": {
        "pl": "Twój wybór [1]: ",
        "en": "Your choice [1]: "
    },
    "opening_url": {
        "pl": "INFO: Otwieranie adresu URL '{url}' na urządzeniu...",
        "en": "INFO: Opening URL '{url}' on the device..."
    },
    "shutting_down_emulator": {
        "pl": "--- Zamykanie emulatora... ---",
        "en": "--- Shutting down the emulator... ---"
    },
    "emulator_shutdown_success": {
        "pl": "SUCCESS: Emulator został zamknięty.",
        "en": "SUCCESS: Emulator has been shut down."
    },
    "emulator_shutdown_fail": {
        "pl": "WARNING: Emulator mógł nie zostać zamknięty poprawnie. Może być konieczne zamknięcie go ręcznie.",
        "en": "WARNING: The emulator may not have shut down correctly. You might need to close it manually."
    },
    "getting_devices_before_launch": {
        "pl": "INFO: Sprawdzanie listy urządzeń przed uruchomieniem...",
        "en": "INFO: Checking device list before launch..."
    },
    "waiting_for_new_device": {
        "pl": "INFO: Oczekiwanie na pojawienie się nowego emulatora na liście urządzeń...",
        "en": "INFO: Waiting for the new emulator to appear on the device list..."
    },
    "new_device_found": {
        "pl": "SUCCESS: Wykryto nowy emulator o numerze seryjnym: {serial}",
        "en": "SUCCESS: Detected new emulator with serial: {serial}"
    },
    "new_device_timeout": {
        "pl": "ERROR: Przekroczono limit czasu oczekiwania na pojawienie się nowego emulatora.",
        "en": "ERROR: Timed out waiting for the new emulator to appear."
    },
    "emulator_boot_timeout": {
        "pl": "ERROR: Przekroczono limit czasu oczekiwania na pełne uruchomienie emulatora.",
        "en": "ERROR: Timed out waiting for the emulator to fully boot."
    },
    "restarting_adb_server": {
        "pl": "INFO: Restartowanie serwera ADB w celu zapewnienia stabilnego połączenia z nowym emulatorem...",
        "en": "INFO: Restarting ADB server to ensure a stable connection with the new emulator..."
    },
    "adb_server_restart_success": {
        "pl": "SUCCESS: Serwer ADB został pomyślnie zrestartowany.",
        "en": "SUCCESS: ADB server restarted successfully."
    },
    "keydive_stabilization_wait": {
        "pl": "INFO: Oczekiwanie {seconds}s na ustabilizowanie się keydive (może to spowodować chwilowe zamknięcie przeglądarki)...",
        "en": "INFO: Waiting {seconds}s for keydive to stabilize (this may cause the browser to close temporarily)..."
    }
    # END: Nowe komunikaty
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
DRM_TEST_URLS = {
    "1": "https://bitmovin.com/demos/drm",
    "2": "https://shaka-player-demo.appspot.com/"
}

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
EMULATOR_PATH = None # NOWOŚĆ
if SDK_PATH:
    ADB_EXECUTABLE = "adb.exe" if sys.platform == "win32" else "adb"
    EMULATOR_EXECUTABLE = "emulator.exe" if sys.platform == "win32" else "emulator" # NOWOŚĆ
    ADB_PATH = SDK_PATH / "platform-tools" / ADB_EXECUTABLE
    EMULATOR_PATH = SDK_PATH / "emulator" / EMULATOR_EXECUTABLE # NOWOŚĆ

def get_venv_path(venv_path: Path, executable: str):
    if sys.platform == "win32": return venv_path / "Scripts" / f"{executable}.exe"
    else: return venv_path / "bin" / executable

def setup_logging():
    """Konfiguruje logowanie do pliku i konsoli."""
    if Path(LOG_FILENAME).exists():
        Path(LOG_FILENAME).unlink()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler = logging.FileHandler(LOG_FILENAME, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(console_handler)

def run_command(command, check=True, env=None, timeout=None):
    try:
        logger.debug(f"Running command: {' '.join(map(str, command))}")
        result = subprocess.run(command, check=check, capture_output=True, text=True, encoding='utf-8', errors='replace', env=env, timeout=timeout)
        if result.stdout: logger.debug(f"STDOUT:\n{result.stdout.strip()}")
        if result.stderr: logger.debug(f"STDERR:\n{result.stderr.strip()}")
        return result
    except subprocess.TimeoutExpired:
        logger.error(_("command_timeout").format(cmd=' '.join(map(str, command))))
        return None
    except subprocess.CalledProcessError as e:
        logger.error(_("command_error").format(cmd=' '.join(map(str, e.cmd)), code=e.returncode))
        if e.stdout: logger.error(f"STDOUT:\n{e.stdout.strip()}")
        if e.stderr: logger.error(f"STDERR:\n{e.stderr.strip()}")
        return None
    except FileNotFoundError:
        logger.error(_("command_not_found").format(cmd=command[0]))
        return None

def get_connected_serials() -> list[str]:
    """Zwraca listę numerów seryjnych podłączonych urządzeń."""
    result = run_command([str(ADB_PATH), "devices"], check=False)
    if not result or result.returncode != 0 or not result.stdout:
        logger.debug("Polecenie adb devices nie powiodło się lub zwróciło pusty wynik.")
        return []
    lines = result.stdout.strip().splitlines()
    # Zwraca listę numerów seryjnych dla urządzeń, które nie są 'offline'
    return [line.split()[0] for line in lines[1:] if line.strip() and "offline" not in line.split()]

# START: NOWA ZMODYFIKOWANA FUNKCJA
def launch_new_emulator():
    """Wyświetla listę AVD, pozwala wybrać jedno, uruchamia je i czeka na gotowość."""
    logger.info(_("launching_emulator_title"))
    if not EMULATOR_PATH or not EMULATOR_PATH.is_file():
        logger.critical(_("emulator_not_found"))
        return None, None

    list_avds_cmd = [str(EMULATOR_PATH), "-list-avds"]
    result = run_command(list_avds_cmd)
    if not result or not result.stdout.strip():
        logger.error(_("no_avds_found"))
        return None, None
    
    available_avds = [line.strip() for line in result.stdout.strip().splitlines()]
    for i, name in enumerate(available_avds, 1):
        logger.info(f"  {i}. {name}")
    
    avd_name_to_launch = None
    while True:
        try:
            choice = int(input(_("select_avd_prompt").format(count=len(available_avds)))) - 1
            if 0 <= choice < len(available_avds):
                avd_name_to_launch = available_avds[choice]
                break
            else:
                logger.warning(_("invalid_number"))
        except ValueError:
            logger.warning(_("invalid_input"))

    logger.info(_("getting_devices_before_launch"))
    serials_before = set(get_connected_serials())
    logger.debug(f"Urządzenia przed uruchomieniem: {serials_before}")

    logger.info(_("launching_avd").format(avd_name=avd_name_to_launch))
    emulator_process = subprocess.Popen(
        [str(EMULATOR_PATH), "-avd", avd_name_to_launch, "-writable-system", "-no-snapshot-load"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    logger.info(_("waiting_for_new_device"))
    new_device_serial = None
    start_time = time.time()
    timeout = 180  # 3 minuty na pojawienie się urządzenia
    while time.time() - start_time < timeout:
        serials_after = set(get_connected_serials())
        new_serials = serials_after - serials_before
        if len(new_serials) == 1:
            new_device_serial = new_serials.pop()
            logger.info(_("new_device_found").format(serial=new_device_serial))
            break
        time.sleep(3)

    if not new_device_serial:
        logger.error(_("new_device_timeout"))
        if emulator_process: emulator_process.terminate()
        return None, None

    # Teraz mamy konkretny numer seryjny i używamy go do dalszych poleceń
    device_serial = new_device_serial
    logger.info(_("waiting_for_boot"))
    boot_timeout = 180  # Kolejne 3 minuty na pełne uruchomienie
    boot_start_time = time.time()
    while time.time() - boot_start_time < boot_timeout:
        boot_prop_result = run_command([str(ADB_PATH), "-s", device_serial, "shell", "getprop", "sys.boot_completed"])
        if boot_prop_result and "1" in boot_prop_result.stdout:
            logger.info(_("emulator_boot_success").format(serial=device_serial))
            
            # Dodajemy dodatkowy, krótki czas oczekiwania, aby upewnić się, że wszystkie usługi systemowe
            # (jak menedżer pakietów, który obsługuje intencje 'am start') są w pełni gotowe.
            time.sleep(5)
            
            logger.info(_("restarting_adb_server"))
            run_command([str(ADB_PATH), "kill-server"], check=False)
            time.sleep(2)
            run_command([str(ADB_PATH), "start-server"], check=True)
            time.sleep(2)
            logger.info(_("adb_server_restart_success"))
            return device_serial, emulator_process
        time.sleep(3)

    logger.error(_("emulator_boot_timeout"))
    if emulator_process: emulator_process.terminate()
    return None, None

def select_or_launch_device():
    """Wyszukuje podłączone urządzenia lub pozwala uruchomić nowe."""
    logger.info(_("select_adb_device"))
    try:
        # Dodajemy timeout, aby zapobiec zawieszeniu się skryptu, jeśli serwer ADB nie odpowiada.
        result = run_command([str(ADB_PATH), "devices"], timeout=15)
        if not result:
            logger.error(_("adb_comm_error").format(e="Nie można uzyskać listy urządzeń. Sprawdź połączenie i serwer ADB."))
            return None, None

        lines = result.stdout.strip().splitlines()
        serials = [line.split()[0] for line in lines[1:] if line.strip() and "device" in line]
        
        if not serials:
            logger.info(_("no_adb_device_found"))
            return launch_new_emulator()

        device_details = []
        for serial in serials:
            try:
                avd_name_proc = run_command([str(ADB_PATH), "-s", serial, "emu", "avd", "name"], check=False, timeout=10)
                avd_name = avd_name_proc.stdout.strip().splitlines()[0] if avd_name_proc and avd_name_proc.stdout else serial
                device_details.append((serial, avd_name))
            except Exception:
                device_details.append((serial, serial))

        if len(device_details) == 1:
            device_serial, avd_name = device_details[0]
            logger.info(_("single_adb_device_found").format(avd_name=avd_name, serial=device_serial))
            return device_serial, None
        else:
            logger.info(_("multiple_adb_devices_found"))
            for i, (serial, avd_name) in enumerate(device_details, 1):
                logger.info(_("device_display_format").format(index=i, avd_name=avd_name, serial=serial))
            
            while True:
                launch_char = 'u' if LANG == 'pl' else 'l'
                choice_str = input(_("select_device_prompt").format(count=len(device_details))).lower().strip()
                if choice_str == launch_char:
                    return launch_new_emulator()
                try:
                    choice_index = int(choice_str) - 1
                    if 0 <= choice_index < len(device_details):
                        return device_details[choice_index][0], None
                    else:
                        logger.warning(_("invalid_number"))
                except ValueError:
                    logger.warning(_("invalid_input"))
    except Exception as e:
        logger.error(_("adb_comm_error").format(e=e))
        return None, None
# END: NOWA ZMODYFIKOWANA FUNKCJA

# START: NOWA FUNKCJA
def prompt_for_video_action() -> tuple[bool, str | None]:
    """Pyta użytkownika o akcję wideo i ZWRACA jego wybór."""
    try:
        answer = input(_("prompt_auto_play")).lower().strip()
        
        if answer.startswith('n'):
            # Użytkownik nie chce automatyzacji
            return False, None

        # Użytkownik chce automatyzacji, pytamy o stronę
        logger.info(_("select_drm_page"))
        for key, value in DRM_TEST_URLS.items():
            logger.info(f"  {key}. {value}")
        
        url_to_open = None
        while True:
            choice = input(_("select_drm_page_prompt")).strip()
            
            if choice == '':
                choice = '1'
            
            if choice in DRM_TEST_URLS:
                url_to_open = DRM_TEST_URLS[choice]
                return True, url_to_open
            else:
                logger.warning(_("invalid_input"))

    except (KeyboardInterrupt, EOFError):
        logger.info(_("user_interrupt"))
        raise
    
    return False, None # Fallback w razie nieoczekiwanego wyjścia z pętli
# END: NOWA FUNKCJA

def _trigger_drm_on_device(device_serial: str, url: str):
    """
    Otwiera podany adres URL na urządzeniu, aby wywołać DRM.
    Otwiera go dwukrotnie, aby obejść potencjalny problem z zamykaniem przeglądarki przez keydive.
    """
    open_url_cmd = [str(ADB_PATH), "-s", device_serial, "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url]

    # 1. Otwórz stronę po raz pierwszy. Może zostać zamknięta przez keydive.
    logger.info(_("opening_url").format(url=url) + " (próba 1/2)")
    try:
        subprocess.run(open_url_cmd, check=False, timeout=15, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        logger.warning("Polecenie otwarcia URL przekroczyło limit czasu, ale prawdopodobnie wykonało się w tle.")

    # 2. Poczekaj, aż keydive się ustabilizuje.
    stabilization_time = 10
    logger.info(_("keydive_stabilization_wait").format(seconds=stabilization_time))
    time.sleep(stabilization_time)

    # 3. Otwórz stronę ponownie, aby na pewno była na pierwszym planie.
    logger.info(_("opening_url").format(url=url) + " (próba 2/2)")
    try:
        subprocess.run(open_url_cmd, check=False, timeout=15, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        logger.warning("Polecenie otwarcia URL (2) przekroczyło limit czasu, ale mogło się wykonać.")
    
    logger.info(_("manual_play_hint"))

# --- Faza 1: Ekstrakcja kluczy z urządzenia ---
def run_extraction_phase(device_serial: str, user_action: tuple[bool, str | None]):
    logger.info(_("phase1_header"))
    logger.info(_("venv_creation_notice"))
    logger.info(_("creating_venv").format(path=VENV_EXTRACTOR_PATH))
    if not run_command([sys.executable, "-m", "venv", "--upgrade-deps", str(VENV_EXTRACTOR_PATH)]): return False, None, None
    
    python_in_venv = get_venv_path(VENV_EXTRACTOR_PATH, "python")
    
    logger.info(_("installing_lib").format(library='keydive'))
    install_result = run_command([str(python_in_venv), "-m", "pip", "install", "--no-cache-dir", "keydive"], timeout=600)
    if not install_result: return False, None, None

    logger.info(_("preparing_device_env").format(serial=device_serial))
    run_command([str(ADB_PATH), "-s", device_serial, "root"], check=False)
    time.sleep(3)
    if not Path(FRIDA_SERVER_FILENAME).is_file():
        logger.error(_("frida_server_not_found").format(filename=FRIDA_SERVER_FILENAME))
        return False, None, None
    if not run_command([str(ADB_PATH), "-s", device_serial, "push", FRIDA_SERVER_FILENAME, "/data/local/tmp/frida-server"]):
        return False, None, None
    run_command([str(ADB_PATH), "-s", device_serial, "shell", "killall frida-server"], check=False)
    time.sleep(1)
    if not run_command([str(ADB_PATH), "-s", device_serial, "shell", "chmod 755 /data/local/tmp/frida-server"]):
        return False, None, None
    subprocess.Popen([str(ADB_PATH), "-s", device_serial, "shell", "/data/local/tmp/frida-server &"])
    time.sleep(2)
    logger.info(_("device_env_success"))
    
    logger.info(_("running_keydive"))
    env = os.environ.copy(); env["PATH"] = str(ADB_PATH.parent) + os.pathsep + env.get("PATH", "")
    keydive_command = [
        str(get_venv_path(VENV_EXTRACTOR_PATH, "keydive")),
        "-s", device_serial,
        "--output", str(KEYS_FOLDER)
    ]
    
    keydive_process = None
    try:
        # Uruchom keydive w tle, aby mógł nasłuchiwać zdarzeń DRM
        logger.debug(f"Starting keydive process: {' '.join(keydive_command)}")
        keydive_process = subprocess.Popen(
            keydive_command, 
            stdin=subprocess.DEVNULL,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        # Teraz, gdy keydive nasłuchuje, wykonaj akcję wybraną przez użytkownika wcześniej
        should_open, url = user_action
        if should_open and url:
            _trigger_drm_on_device(device_serial, url)
        else:
            # Użytkownik wybrał opcję ręczną
            logger.info(_("keydive_manual_hint"))

        # Czekaj na zakończenie procesu keydive.
        # To jest moment, w którym użytkownik powinien odtworzyć wideo.
        # keydive zakończy się sam, gdy przechwyci klucze.
        stdout, stderr = keydive_process.communicate()
        
        logger.debug(f"keydive STDOUT:\n{stdout}")
        if stderr: logger.debug(f"keydive STDERR:\n{stderr}")

        if keydive_process.returncode != 0:
            logger.error(_("keydive_error"))
            logger.error(f"keydive stderr:\n{stderr}")
            return False, None, None

    except KeyboardInterrupt:
        if keydive_process: keydive_process.terminate()
        raise

    logger.info(_("verifying_files"))
    if not KEYS_FOLDER.is_dir():
        logger.error(_("keys_folder_not_created").format(folder=KEYS_FOLDER)); return False, None, None
    client_id_files, private_key_files = list(KEYS_FOLDER.rglob('client_id.bin')), list(KEYS_FOLDER.rglob('private_key.pem'))
    if client_id_files and private_key_files:
        client_id_path, private_key_path = client_id_files[0], private_key_files[0]
        logger.info(_("client_id_found").format(path=client_id_path)); logger.info(_("private_key_found").format(path=private_key_path))
        return True, client_id_path, private_key_path
    else:
        logger.error(_("key_files_not_found").format(folder=KEYS_FOLDER)); return False, None, None

# --- Faza 2: Tworzenie pliku .wvd ---
def run_creation_phase(client_id_path: Path, priv_key_path: Path):
    logger.info(_("phase2_header"))
    logger.info(_("creating_venv").format(path=VENV_CREATOR_PATH))
    if not run_command([sys.executable, "-m", "venv", "--upgrade-deps", str(VENV_CREATOR_PATH)]): return False
    
    python_in_venv = get_venv_path(VENV_CREATOR_PATH, "python")
    logger.info(_("installing_lib").format(library='pywidevine'))
    install_command = [str(python_in_venv), "-m", "pip", "install", "--no-cache-dir", "pywidevine"]
    result = run_command(install_command, timeout=600)
    if not result:
        logger.error(_("pywidevine_install_fail")); return False
    
    logger.info(_("creator_env_success"))
    
    logger.info(_("creating_wvd_file").format(filename=FINAL_WVD_FILENAME.name))
    
    temp_output_folder = VENV_CREATOR_PATH / "temp_wvd_out"
    temp_output_folder.mkdir(exist_ok=True)

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
            shutil.move(str(source_file), FINAL_WVD_FILENAME)
            logger.info(_("wvd_file_created_success").format(filename=FINAL_WVD_FILENAME.name))
            return True
        else:
            logger.error(_("wvd_file_not_found_after_run")); return False
    else:
        logger.error(_("phase2_failed")); return False

# --- Główna funkcja i sprzątanie ---
def cleanup(device_serial=None, emulator_process=None): # ZMODYFIKOWANA
    logger.info(_("cleanup_header"))
    
    # START: NOWA CZĘŚĆ
    if emulator_process:
        logger.info(_("shutting_down_emulator"))
        try:
            if device_serial:
                run_command([str(ADB_PATH), "-s", device_serial, "emu", "kill"], check=False)
            emulator_process.terminate()
            emulator_process.wait(timeout=30)
            logger.info(_("emulator_shutdown_success"))
        except (subprocess.TimeoutExpired, Exception) as e:
            logger.warning(_("emulator_shutdown_fail"))
            logger.debug(f"Emulator shutdown error: {e}")
    # END: NOWA CZĘŚĆ

    if device_serial and ADB_PATH:
        logger.info(_("stopping_frida").format(serial=device_serial))
        # Zmieniono z `run_command` na bezpośrednie wywołanie `subprocess.run`,
        # aby uniknąć problemów z I/O podczas zamykania skryptu, które mogły
        # powodować błąd KeyboardInterrupt.
        kill_cmd = [str(ADB_PATH), "-s", device_serial, "shell", "killall", "frida-server"]
        try:
            subprocess.run(kill_cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        except Exception as e:
            logger.warning(f"Wystąpił błąd podczas próby zatrzymania serwera Frida, ale kontynuuję sprzątanie. Błąd: {e}")
        logger.info(_("frida_stop_sent"))
    for path in [VENV_EXTRACTOR_PATH, VENV_CREATOR_PATH, KEYS_FOLDER]:
        if path.exists():
            try:
                logger.info(_("removing_temp_folder").format(folder=path.name))
                if path.is_dir(): shutil.rmtree(path)
                else: path.unlink()
                logger.info(_("removed_success"))
            except OSError as e: logger.warning(_("remove_warning").format(folder=path.name, e=e))

    log_file_path = Path(LOG_FILENAME)
    should_delete_log = g_script_successful or g_user_interrupted

    if log_file_path.exists():
        if should_delete_log:
            logger.info(_("log_file_removing").format(log_filename=LOG_FILENAME))
        else:
            logger.info(_("log_file_kept").format(log_filename=LOG_FILENAME))

    logging.shutdown()

    if should_delete_log and log_file_path.exists():
        try:
            log_file_path.unlink()
            print(_("log_file_removed"))
        except OSError as e:
            print(_("log_file_remove_warning").format(log_filename=LOG_FILENAME, e=e))

def select_language():
    """Prosi użytkownika o wybór języka i ustawia globalną zmienną LANG."""
    global LANG
    while True:
        choice = input(MESSAGES["lang_prompt"]["pl"]).strip()
        if choice == '1' or choice == '':
            LANG = 'pl'
            return
        elif choice == '2':
            LANG = 'en'
            return
        else:
            print(MESSAGES["invalid_lang_choice"]["pl"] + " / " + MESSAGES["invalid_lang_choice"]["en"])

def get_device_architecture(device_serial: str):
    """Pobiera architekturę procesora z urządzenia."""
    logger.info(_("checking_architecture"))
    result = run_command([str(ADB_PATH), "-s", device_serial, "shell", "getprop", "ro.product.cpu.abi"])
    if result and result.stdout:
        arch = result.stdout.strip()
        logger.info(_("architecture_found").format(arch=arch))
        return arch
    logger.error(_("architecture_fail"))
    return None

def download_and_prepare_frida_server(architecture: str) -> bool:
    """Pobiera, rozpakowuje i przygotowuje odpowiedni plik frida-server."""
    api_url = "https://api.github.com/repos/frida/frida/releases/latest"
    try:
        with urllib.request.urlopen(api_url) as response:
            release_data = json.loads(response.read().decode())
    except Exception as e:
        logger.error(_("frida_api_fail"))
        logger.debug(f"GitHub API error: {e}")
        return False

    tag_name = release_data.get('tag_name')
    if not tag_name:
        logger.error(_("frida_api_fail"))
        return False

    asset_name = f"frida-server-{tag_name}-android-{architecture}.xz"
    download_url = next((asset.get('browser_download_url') for asset in release_data.get('assets', []) if asset.get('name') == asset_name), None)

    if not download_url:
        logger.error(_("frida_asset_not_found").format(arch=architecture))
        return False

    xz_filename = Path(asset_name)
    logger.info(_("frida_downloading").format(arch=architecture))
    try:
        urllib.request.urlretrieve(download_url, xz_filename)
    except Exception as e:
        logger.error(_("frida_download_fail")); logger.debug(f"Download error: {e}")
        return False

    logger.info(_("frida_unpacking"))
    try:
        with lzma.open(xz_filename, 'rb') as f_in, open(FRIDA_SERVER_FILENAME, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
        if sys.platform != "win32": os.chmod(FRIDA_SERVER_FILENAME, 0o755)
    except Exception as e:
        logger.error(_("frida_unpack_fail")); logger.debug(f"Unpack error: {e}")
        return False
    finally:
        if xz_filename.exists(): xz_filename.unlink()

    logger.info(_("frida_success").format(filename=FRIDA_SERVER_FILENAME))
    return True

def ensure_correct_frida_server(device_serial: str) -> bool:
    """Orkiestruje proces sprawdzania i pobierania serwera Frida."""
    arch = get_device_architecture(device_serial)
    if not arch: return False

    prompt_key = "frida_exists_prompt" if Path(FRIDA_SERVER_FILENAME).is_file() else "frida_download_prompt"
    use_existing_char = 'u'
    download_char = 'p' if LANG == 'pl' else 'd'
    confirm_char = 't' if LANG == 'pl' else 'y'
    
    try:
        answer = input(_(prompt_key)).lower().strip()
        if prompt_key == "frida_exists_prompt":
            if answer.startswith(download_char):
                return download_and_prepare_frida_server(arch)
            logger.info(_("frida_using_existing"))
            return True
        elif prompt_key == "frida_download_prompt":
            if answer == '' or answer.startswith(confirm_char):
                return download_and_prepare_frida_server(arch)
    except (KeyboardInterrupt, EOFError):
        pass

    logger.critical(_("frida_server_missing_error").format(filename=FRIDA_SERVER_FILENAME))
    return False

def check_and_perform_cleanup():
    """Sprawdza pozostałości i pyta użytkownika o ich usunięcie."""
    leftover_paths = [p for p in [VENV_EXTRACTOR_PATH, VENV_CREATOR_PATH, KEYS_FOLDER] if p.exists()]
    if not leftover_paths:
        return True

    logger.warning(_("cleanup_warning"))
    for path in leftover_paths:
        logger.warning(f"  - {path.name}")
    
    try:
        answer = input(_("cleanup_prompt")).lower().strip()
        if answer in ["", "y", "t", "yes", "tak"]:
            for path in leftover_paths:
                logger.info(_("cleanup_in_progress").format(path=path.name))
                if path.is_dir(): shutil.rmtree(path)
                else: path.unlink()
            logger.info(_("cleanup_success"))
            return True
        else:
            logger.info(_("cleanup_aborted"))
            return False
    except (KeyboardInterrupt, EOFError):
        logger.info("\n" + _("cleanup_aborted"))
        return False

def main():
    global g_script_successful, g_user_interrupted
    device_serial = None
    emulator_process = None # NOWOŚĆ
    try:
        select_language()
        setup_logging()
        if not check_and_perform_cleanup(): sys.exit(1)
        logger.info(_("main_title"))
        if not ADB_PATH or not ADB_PATH.is_file():
            logger.critical(_("adb_not_found")); sys.exit(1)
        
        # Pytaj o akcję PRZED wyborem urządzenia
        user_action_choice = prompt_for_video_action()
        
        # Teraz wybierz urządzenie
        device_serial, emulator_process = select_or_launch_device()
        if not device_serial:
            sys.exit(1)
            
        if not ensure_correct_frida_server(device_serial):
            sys.exit(1)

        extraction_success, client_id_path, priv_key_path = run_extraction_phase(device_serial, user_action_choice)
        if not extraction_success:
            logger.error(_("phase1_interrupted")); sys.exit(1)
        
        creation_success = run_creation_phase(client_id_path, priv_key_path)
        if creation_success:
            logger.info(_("process_finished_success").format(filename=FINAL_WVD_FILENAME.name))
            g_script_successful = True
        else:
            logger.error(_("phase2_interrupted")); sys.exit(1)

    except KeyboardInterrupt:
        g_user_interrupted = True
        logger.info(_("user_interrupt"))
    except Exception as e:
        logger.debug("Caught exception in main loop", exc_info=True)
        logger.critical(_("critical_error").format(e=e))
    finally:
        # ZMODYFIKOWANA LOGIKA
        cleanup(device_serial, emulator_process)
        if not g_user_interrupted:
            try:
                input(_("press_enter_to_exit"))
            except (KeyboardInterrupt, EOFError):
                pass

if __name__ == "__main__":
    main()