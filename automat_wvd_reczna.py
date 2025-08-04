"""
### Zastrzeżenie (Disclaimer) ###

Ten projekt jest przeznaczony wyłącznie do celów edukacyjnych i badawczych.
Używaj go odpowiedzialnie i tylko w odniesieniu do treści, do których posiadasz
legalne prawa. Autor nie ponosi odpowiedzialności za niewłaściwe wykorzystanie
tego narzędzia.
"""
import os
import subprocess
import sys
import shutil
import time
from pathlib import Path

# --- Konfiguracja ---
OUTPUT_WVD_FILENAME = "device.wvd"
FRIDA_SERVER_FILENAME = "frida-server" 

# ... (wszystkie funkcje pomocnicze od check_and_install_keydive do cleanup pozostają BEZ ZMIAN) ...
def check_and_install_keydive():
    try:
        import keydive
        print("INFO: Biblioteka 'keydive' jest już zainstalowana.")
    except ImportError:
        print("WARNING: Biblioteka 'keydive' nie jest zainstalowana.")
        answer = input("Czy chcesz ją teraz zainstalować? [Y/n]: ").lower().strip()
        if answer in ["", "y", "yes"]:
            print("INFO: Instalowanie 'keydive'...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "keydive"])
                print("SUCCESS: Pomyślnie zainstalowano 'keydive'.")
            except subprocess.CalledProcessError as e:
                print(f"ERROR: Nie udało się zainstalować 'keydive'. Błąd: {e}")
                sys.exit(1)
        else:
            print("INFO: Instalacja anulowana. Skrypt nie może kontynuować.")
            sys.exit(1)

def find_android_sdk():
    sdk_path_str = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if sdk_path_str and Path(sdk_path_str).is_dir(): return Path(sdk_path_str)
    
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            default_path = Path(local_app_data) / "Android" / "Sdk"
            if default_path.is_dir(): return default_path
    elif sys.platform == "linux" or sys.platform == "darwin": # Linux lub macOS
        default_path = Path.home() / "Android" / "Sdk"
        if default_path.is_dir(): return default_path
    return None

SDK_PATH = find_android_sdk()
ADB_PATH = None
if SDK_PATH:
    ADB_EXECUTABLE = "adb.exe" if sys.platform == "win32" else "adb"
    ADB_PATH = SDK_PATH / "platform-tools" / ADB_EXECUTABLE

def select_adb_device():
    print("INFO: Sprawdzanie połączenia z urządzeniem ADB...")
    try:
        result = subprocess.run([str(ADB_PATH), "devices"], capture_output=True, text=True, check=True, encoding='utf-8')
        lines = result.stdout.strip().splitlines()
        devices = [line.split()[0] for line in lines[1:] if line.strip() and "device" in line]
        if not devices:
            print("ERROR: Nie znaleziono żadnego podłączonego urządzenia ADB.")
            return None
        if len(devices) == 1:
            print(f"SUCCESS: Znaleziono jedno urządzenie ADB: {devices[0]}. Zostanie ono użyte automatycznie.")
            return devices[0]
        print("INFO: Znaleziono więcej niż jedno urządzenie. Wybierz, którego chcesz użyć:")
        for i, device in enumerate(devices, 1): print(f"  {i}. {device}")
        while True:
            try:
                choice_index = int(input(f"Wybierz numer (1-{len(devices)}): ")) - 1
                if 0 <= choice_index < len(devices): return devices[choice_index]
                else: print("Nieprawidłowy numer.")
            except ValueError: print("Nieprawidłowe dane. Wpisz numer.")
    except Exception as e:
        print(f"ERROR: Błąd podczas komunikacji z ADB: {e}")
        return None

def prepare_device_environment(device_serial):
    print("\n--- Krok 2: Automatyczne przygotowywanie środowiska na urządzeniu ---")
    print("INFO: Próba przełączenia ADB w tryb roota...")
    try:
        subprocess.run([str(ADB_PATH), "-s", device_serial, "root"], capture_output=True, text=True, check=True, timeout=10)
        time.sleep(3)
        verify_result = subprocess.run([str(ADB_PATH), "-s", device_serial, "shell", "whoami"], capture_output=True, text=True, check=True, timeout=10)
        if "root" not in verify_result.stdout:
            print("ERROR: Nie udało się uzyskać uprawnień roota.")
            return False
        print("SUCCESS: Połączenie ADB ma uprawnienia roota.")
    except Exception:
        print("ERROR: Komenda 'adb root' nie powiodła się.")
        return False
    if not Path(FRIDA_SERVER_FILENAME).is_file():
        print(f"ERROR: Nie znaleziono pliku serwera Frida ('{FRIDA_SERVER_FILENAME}').")
        return False
    print(f"INFO: Wysyłanie serwera Frida na urządzenie...")
    subprocess.run([str(ADB_PATH), "-s", device_serial, "push", FRIDA_SERVER_FILENAME, "/data/local/tmp/frida-server"], check=True)
    print("INFO: Zatrzymywanie/uruchamianie serwera Frida...")
    subprocess.run([str(ADB_PATH), "-s", device_serial, "shell", "killall frida-server"], capture_output=True)
    time.sleep(1)
    subprocess.run([str(ADB_PATH), "-s", device_serial, "shell", "chmod 755 /data/local/tmp/frida-server"], check=True)
    subprocess.Popen([str(ADB_PATH), "-s", device_serial, "shell", "/data/local/tmp/frida-server &"])
    time.sleep(2)
    print("SUCCESS: Środowisko na urządzeniu zostało w pełni przygotowane.")
    return True

def dump_widevine_keys(device_serial=None):
    print("\n--- Krok 3: Uruchamianie 'keydive' w celu pobrania kluczy ---\n")
    print("---                    WSKAZÓWKA:                         ---")
    print("Gdy skrypt 'zawiśnie', na emulatorze odtwórz wideo na stronie: \nhttps://shaka-player-demo.appspot.com lub https://bitmovin.com/demos/drmn\n")
    try:
        command = ["keydive"]
        if device_serial: command.extend(["-s", device_serial])
        env = os.environ.copy()
        platform_tools_path = str(ADB_PATH.parent)
        env["PATH"] = platform_tools_path + os.pathsep + env.get("PATH", "")
        subprocess.run(command, check=True, env=env)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\nERROR: Wystąpił krytyczny błąd podczas uruchamiania 'keydive'.")
        return False

def generate_wvd_file(priv_key_path, client_id_path):
    print(f"\n--- Krok 4: Tworzenie pliku '{OUTPUT_WVD_FILENAME}' ---")
    try:
        with open(priv_key_path, 'rb') as f_priv, open(client_id_path, 'rb') as f_cid:
            private_key_data = f_priv.read()
            client_id_data = f_cid.read()
        with open(OUTPUT_WVD_FILENAME, 'wb') as f_wvd:
            f_wvd.write(private_key_data)
            f_wvd.write(client_id_data)
        print(f"SUCCESS: Pomyślnie utworzono plik '{OUTPUT_WVD_FILENAME}'.")
        return True
    except IOError as e:
        print(f"ERROR: Nie udało się odczytać lub zapisać plików. Błąd: {e}")
        return False

def cleanup():
    print("\n--- Krok 5: Sprzątanie plików pośrednich ---")
    device_folder = Path("device")
    if device_folder.is_dir():
        try:
            shutil.rmtree(device_folder)
            print("SUCCESS: Usunięto tymczasowy folder 'device'.")
        except OSError as e:
            print(f"WARNING: Nie udało się usunąć folderu 'device'. Błąd: {e}")

def main():
    """Główna funkcja skryptu."""
    print("---- AUTOMATYCZNY GENERATOR PLIKU WIDEVINE WVD (v7 - Finalna) ----")
    
    selected_device = None  # Inicjalizujemy zmienną, aby była dostępna w 'finally'
    try:
        # Krok 0: Sprawdzenie zależności
        check_and_install_keydive()

        if not ADB_PATH or not ADB_PATH.is_file(): 
            print("\nERROR: Nie udało się zlokalizować 'adb'.")
            sys.exit(1)
        
        # Krok 1: Wybór urządzenia
        selected_device = select_adb_device()
        if not selected_device:
            sys.exit(1)

        # Kroki 2-5: Główna logika
        if prepare_device_environment(selected_device):
            if dump_widevine_keys(selected_device):
                print("\nINFO: Przeszukiwanie folderów w poszukiwaniu pobranych kluczy...")
                client_id_files = list(Path.cwd().rglob('client_id.bin'))
                private_key_files = list(Path.cwd().rglob('private_key.pem'))
                if client_id_files and private_key_files:
                    client_id_path = client_id_files[0]
                    private_key_path = private_key_files[0]
                    print(f"SUCCESS: Znaleziono klucze w folderze: {client_id_path.parent}")
                    if generate_wvd_file(private_key_path, client_id_path):
                        cleanup()
                        print(f"\n--- ZAKOŃCZONO POMYŚLNIE ---")
                        print(f"Twój plik '{OUTPUT_WVD_FILENAME}' jest gotowy do użycia.")
                else:
                    print("ERROR: Nie znaleziono plików 'client_id.bin' i 'private_key.pem'.")

    except KeyboardInterrupt:
        print("\n\nINFO: Działanie skryptu przerwane przez użytkownika (Ctrl+C).")
    except Exception as e:
        print(f"\n\nCRITICAL: Wystąpił nieoczekiwany błąd: {e}")
    finally:
        # --- NOWA LOGIKA: Blok sprzątający, który wykonuje się ZAWSZE ---
        if selected_device:
            print("\n--- Krok Ostateczny: Zatrzymywanie serwera Frida na urządzeniu ---")
            subprocess.run([str(ADB_PATH), "-s", selected_device, "shell", "killall frida-server"], capture_output=True, timeout=5)
            print(f"INFO: Wyslano polecenie zatrzymania serwera Frida na urzadzeniu '{selected_device}'.")

if __name__ == "__main__":
    main()