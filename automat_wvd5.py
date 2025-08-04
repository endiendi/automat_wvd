# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import shutil
import time
from pathlib import Path

# --- Konfiguracja ---
OUTPUT_WVD_FILENAME = "device.wvd"
FRIDA_SERVER_FILENAME = "frida-server" 
DRM_TEST_URLS = {
    "1": "https://bitmovin.com/demos/drm",
    "2": "https://shaka-player-demo.appspot.com/",
    "3": "https://www.skyshowtime.com/"
}

# --- Logika Wyszukiwania Ścieżek i Narzędzi ---
def find_android_sdk():
    sdk_path_str = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if sdk_path_str and Path(sdk_path_str).is_dir(): return Path(sdk_path_str)
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            default_path = Path(local_app_data) / "Android" / "Sdk"
            if default_path.is_dir(): return default_path
    print("ERROR: Nie udało się automatycznie zlokalizować Android SDK.")
    return None

SDK_PATH = find_android_sdk()
ADB_PATH = None
EMULATOR_PATH = None
if SDK_PATH:
    ADB_EXECUTABLE = "adb.exe" if sys.platform == "win32" else "adb"
    EMULATOR_EXECUTABLE = "emulator.exe" if sys.platform == "win32" else "emulator"
    ADB_PATH = SDK_PATH / "platform-tools" / ADB_EXECUTABLE
    EMULATOR_PATH = SDK_PATH / "emulator" / EMULATOR_EXECUTABLE

# --- Funkcje Pomocnicze ---
def check_and_install_keydive():
    try:
        import keydive
    except ImportError:
        print("WARNING: Biblioteka 'keydive' nie jest zainstalowana.")
        answer = input("Czy chcesz ją teraz zainstalować? [Y/n]: ").lower().strip()
        if answer in ["", "y", "yes"]:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "keydive"])
        else:
            sys.exit(1)

def select_adb_device():
    result = subprocess.run([str(ADB_PATH), "devices"], capture_output=True, text=True, check=True, encoding='utf-8')
    lines = result.stdout.strip().splitlines()
    devices = [line.split()[0] for line in lines[1:] if line.strip() and "device" in line]
    if not devices:
        print("ERROR: Nie znaleziono żadnego podłączonego urządzenia ADB.")
        return None
    if len(devices) == 1:
        return devices[0]
    print("INFO: Znaleziono więcej niż jedno urządzenie. Wybierz jedno:")
    for i, device in enumerate(devices, 1): print(f"  {i}. {device}")
    while True:
        try:
            choice = int(input(f"Wybierz numer (1-{len(devices)}): ")) - 1
            if 0 <= choice < len(devices): return devices[choice]
        except (ValueError, IndexError): print("Nieprawidłowe dane.")

def select_and_launch_emulator():
    proc = subprocess.run([str(EMULATOR_PATH), "-list-avds"], capture_output=True, text=True, check=True, encoding='utf-8')
    available_avds = [line.strip() for line in proc.stdout.strip().split('\n') if line.strip()]
    if not available_avds:
        print("ERROR: Nie znaleziono żadnych skonfigurowanych emulatorów (AVD).")
        return None, None
    print("INFO: Znaleziono następujące emulatory (AVD):")
    for i, name in enumerate(available_avds, 1): print(f"  {i}. {name}")
    avd_name = None
    while True:
        try:
            choice = int(input(f"Wybierz numer emulatora do uruchomienia (1-{len(available_avds)}): ")) - 1
            if 0 <= choice < len(available_avds):
                avd_name = available_avds[choice]
                break
        except (ValueError, IndexError): print("Nieprawidłowe dane.")
    
    print("\nKtórą stronę otworzyć na emulatorze?")
    for key, value in DRM_TEST_URLS.items(): print(f"  {key}. {value}")
    url_choice = None
    while True:
        choice = input(f"Wybierz numer strony (1-{len(DRM_TEST_URLS)}): ").strip()
        if choice in DRM_TEST_URLS:
            url_choice = DRM_TEST_URLS[choice]
            break
        else: print("Nieprawidłowy numer.")

    print(f"INFO: Uruchamianie emulatora '{avd_name}'...")
    emulator_process = subprocess.Popen([str(EMULATOR_PATH), "-avd", avd_name, "-writable-system", "-no-snapshot-load", "-no-snapshot-save"])
    
    print("INFO: Oczekiwanie na pełne uruchomienie systemu Android...")
    subprocess.run([str(ADB_PATH), "wait-for-device"], timeout=300, check=True)
    device_serial = subprocess.run([str(ADB_PATH), "get-serialno"], capture_output=True, text=True, check=True).stdout.strip()
    while "1" not in subprocess.run([str(ADB_PATH), "-s", device_serial, "shell", "getprop", "sys.boot_completed"], capture_output=True, text=True).stdout:
        time.sleep(2)
    return device_serial, emulator_process, url_choice

def prepare_device_environment(device_serial):
    print("\n--- Krok 3: Przygotowywanie środowiska Frida ---")
    if not Path(FRIDA_SERVER_FILENAME).is_file():
        print(f"ERROR: Nie znaleziono pliku '{FRIDA_SERVER_FILENAME}'.")
        return False
    print("INFO: Wysyłanie i uruchamianie serwera Frida...")
    subprocess.run([str(ADB_PATH), "-s", device_serial, "push", FRIDA_SERVER_FILENAME, "/data/local/tmp/frida-server"], check=True)
    subprocess.run([str(ADB_PATH), "-s", device_serial, "shell", "killall frida-server"], capture_output=True)
    time.sleep(1)
    subprocess.run([str(ADB_PATH), "-s", device_serial, "shell", "chmod 755 /data/local/tmp/frida-server"], check=True)
    subprocess.Popen([str(ADB_PATH), "-s", device_serial, "shell", "/data/local/tmp/frida-server &"])
    # Zwiększamy czas, aby serwer się w pełni zainicjował
    print("INFO: Oczekiwanie na inicjalizację serwera Frida...")
    time.sleep(5) 
    return True

def generate_wvd_file():
    print("\n--- Krok 5: Tworzenie pliku .wvd ---")
    client_id_files = list(Path.cwd().rglob('client_id.bin'))
    private_key_files = list(Path.cwd().rglob('private_key.pem'))
    if not (client_id_files and private_key_files):
        print("ERROR: Nie znaleziono plików 'client_id.bin' i 'private_key.pem'.")
        return
    client_id_path, private_key_path = client_id_files[0], private_key_files[0]
    print(f"SUCCESS: Znaleziono klucze w: {client_id_path.parent}")
    with open(OUTPUT_WVD_FILENAME, 'wb') as f_wvd:
        f_wvd.write(client_id_path.read_bytes())
        f_wvd.write(private_key_path.read_bytes())
    print(f"SUCCESS: Pomyślnie utworzono plik '{OUTPUT_WVD_FILENAME}'.")

def cleanup():
    print("\n--- Krok Ostateczny: Sprzątanie ---")
    device_folder = Path("device")
    if device_folder.is_dir():
        for attempt in range(3):
            try:
                shutil.rmtree(device_folder)
                print("SUCCESS: Usunięto folder 'device'.")
                return
            except PermissionError:
                time.sleep(1)
        print("ERROR: Nie udało się usunąć folderu 'device'.")

def main():
    print("--- AUTOMATYCZNY GENERATOR PLIKU WIDEVINE WVD (v12.1 - Golden Master) ---")
    
    selected_device, emulator_process, url_to_open = None, None, None
    try:
        check_and_install_keydive()
        if not SDK_PATH: sys.exit(1)

        print("\n--- Krok 1: Wybór trybu pracy ---")
        mode = input("  1. Użyj podłączonego urządzenia\n  2. Uruchom nowy emulator\nWybierz tryb (1-2): ").strip()

        if mode == "1":
            selected_device = select_adb_device()
        elif mode == "2":
            selected_device, emulator_process, url_to_open = select_and_launch_emulator()
        else:
            print("Nieprawidłowy wybór.")
            sys.exit(1)

        if not selected_device: sys.exit(1)

        print("\n--- Krok 2: Uzyskiwanie uprawnień roota ---")
        try:
            subprocess.run([str(ADB_PATH), "-s", selected_device, "root"], capture_output=True, text=True, check=True, timeout=10)
            time.sleep(3)
            subprocess.run([str(ADB_PATH), "-s", selected_device, "wait-for-device"], timeout=60, check=True)
            time.sleep(5)
            print("SUCCESS: Urządzenie jest stabilne i ma uprawnienia roota.")
        except Exception:
            print("WARNING: Komenda 'adb root' nie powiodła się.")

        if url_to_open:
            print(f"INFO: Otwieranie strony '{url_to_open}'...")
            subprocess.run([str(ADB_PATH), "-s", selected_device, "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url_to_open], check=True)

        if prepare_device_environment(selected_device):
            print("\n" + "="*60 + "\n" + "!!! TERAZ TWOJA KOLEJ !!!".center(60) + "\n" + "="*60)
            print("1. Na emulatorze, odtwórz wideo DRM, aby wywołać proces.")
            print("2. Obserwuj to okno - 'keydive' powinien przechwycić klucze.")
            print("3. Gdy 'keydive' zakończy pracę i zapisze pliki, skrypt automatycznie przejdzie dalej.")
            
            command = ["keydive"]
            if selected_device: command.extend(["-s", selected_device])
            env = os.environ.copy()
            env["PATH"] = str(ADB_PATH.parent) + os.pathsep + env.get("PATH", "")
            subprocess.run(command, check=True, env=env)

            generate_wvd_file()
            print(f"\n--- ZAKOŃCZONO POMYŚLNIE ---")
            
    except KeyboardInterrupt:
        print("\n\nINFO: Działanie skryptu przerwane.")
    except Exception as e:
        print(f"\n\nCRITICAL: Wystąpił błąd: {e}")
    finally:
        cleanup()
        if selected_device:
            subprocess.run([str(ADB_PATH), "-s", selected_device, "shell", "killall frida-server"], capture_output=True, timeout=5)
            print(f"INFO: Wyslano polecenie zatrzymania serwera Frida na '{selected_device}'.")
        if emulator_process:
            print("INFO: Zamykanie emulatora...")
            if selected_device:
                subprocess.run([str(ADB_PATH), "-s", selected_device, "emu", "kill"], capture_output=True, timeout=10)
            emulator_process.wait(timeout=30)
            print("SUCCESS: Emulator zamknięty.")
        print("--- Koniec pracy. ---")

if __name__ == "__main__":
    main()