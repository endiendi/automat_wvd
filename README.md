# Automatyczny Ekstraktor Kluczy Widevine L3 (Wersja Dwuetapowa) / Automatic Widevine L3 Key Extractor (Two-Stage Version)

## Wersja Polska (PL)

Ten projekt zawiera skrypt w języku Python, który w sposób zautomatyzowany i powtarzalny przeprowadza proces ekstrakcji kluczy Widevine Content Decryption Module (CDM) z **urządzeń z systemem Android posiadających uprawnienia roota**.

Skrypt działa w dwóch fazach, tworząc dedykowane, izolowane środowiska wirtualne dla każdego etapu, co zapewnia kompatybilność i stabilność działania, nawet z nowszymi wersjami Pythona. Wynikiem działania jest plik `device.wvd`, który może być używany przez narzędzia takie jak `yt-dlp` do pobierania treści chronionych przez DRM L3.

### Testowane Środowisko

Skrypt został pomyślnie przetestowany w następującej konfiguracji:

*   **System Operacyjny**: Windows 11
*   **Wersja Python**: 3.13.5
*   **Emulator (AVD)**:
    *   **Urządzenie**: Pixel 9 Pro
    *   **API**: 35 ("VanillaIceCream", Android 15.0)
    *   **Obraz Systemu**: Google APIs Intel x86_64 Atom System Image (Ważne jest użycie obrazu "Google APIs", a nie "Google Play", aby mieć dostęp do roota).

### Pliki w projekcie

*   `automat_wvd_reczna_pywidevine.py` - Główny skrypt, który należy uruchomić.
*   `frida-server` - **(Musisz dostarczyć ten plik samodzielnie)**. Jest to plik binarny serwera Frida, który musi być dopasowany do architektury procesora Twojego urządzenia Android.

### Wymagania wstępne

Zanim zaczniesz, upewnij się, że spełniasz następujące wymagania:

1.  **Python 3** zainstalowany na Twoim komputerze.
2.  **Zrootowane urządzenie z Androidem**. Zalecany jest **emulator** skonfigurowany w Android Studio z obrazem systemu "Google APIs".
3.  **Włączone debugowanie USB** na urządzeniu Android.
4.  Zainstalowane **narzędzia Android SDK Platform-Tools** (zazwyczaj dołączane do instalacji Android Studio). Skrypt spróbuje automatycznie zlokalizować `adb`, ale zaleca się dodanie folderu z narzędziami do systemowej zmiennej środowiskowej `PATH`.
5.  Pobrany plik binarny **`frida-server`**.

### Instrukcja Przygotowania

1.  **Pobierz `frida-server`**:
    *   Przejdź na stronę oficjalnych wydań Fridy na GitHubie: https://github.com/frida/frida/releases.
    *   Znajdź odpowiednią wersję. Wersja, która działała w testowanej konfiguracji to **`frida-server-17.2.15-android-x86_64.xz`**.
    *   Pamiętaj, aby dopasować architekturę (`ARCH`) do swojego urządzenia:
        *   `x86_64` dla emulatorów na komputerach z procesorem Intel/AMD.
        *   `arm64` dla większości nowoczesnych, fizycznych telefonów.
    *   Rozpakuj archiwum `.xz`. np 7-Zip.
    *   Zmień nazwę rozpakowanego pliku na `frida-server`.

2.  **Przygotuj folder projektu**:
    *   Umieść plik skryptu `automat_wvd_reczna_pywidevine.py` oraz pobrany i przemianowany `frida-server` w tym samym folderze.

### Instrukcja Użycia

1.  **Uruchom emulator Androida**. Upewnij się, że jest w pełni załadowany i gotowy do pracy.

2.  **Uruchom skrypt**:
    *   Otwórz terminal lub wiersz poleceń w folderze z plikami projektu.
    *   Wpisz i wykonaj komendę:
        ```bash
        python automat_wvd_reczna_pywidevine.py
        ```

3.  **Postępuj zgodnie z instrukcjami na ekranie**:
    *   **Faza 1: Pobieranie Kluczy**
        *   Skrypt najpierw utworzy środowisko wirtualne `venv_extractor` i zainstaluje w nim bibliotekę `keydive`.
        *   Następnie wyświetli listę podłączonych urządzeń i poprosi Cię o wybór jednego (jeśli jest ich więcej niż jedno).
        *   Skrypt automatycznie przygotuje urządzenie (prześle i uruchomi serwer Fridy).
        *   **!!! TERAZ TWOJA KOLEJ !!!**
            *   Skrypt wyświetli komunikat `--- WSKAZÓWKA: Odtwórz wideo na https://shaka-player-demo.appspot.com ---`.
            *   **To jest moment na Twoje działanie**: na emulatorze **ręcznie** otwórz przeglądarkę Chrome, wejdź na jeden z podanych adresów (np. `https://shaka-player-demo.appspot.com` lub `https://bitmovin.com/demos/drm`) i **odtwórz wideo**.
            *   W tym czasie w terminalu powinny pojawić się logi z `keydive` świadczące o przechwytywaniu kluczy.

    *   **Faza 2: Tworzenie pliku .wvd**
        *   Po pomyślnym pobraniu kluczy, skrypt automatycznie przejdzie do drugiej fazy.
        *   Utworzy nowe środowisko wirtualne `venv_creator` i zainstaluje w nim `pywidevine`.
        *   Użyje pobranych kluczy do wygenerowania finalnego pliku.

4.  **Zakończenie**:
    *   Po pomyślnym zakończeniu, w folderze projektu znajdziesz plik **`device.wvd`**.
    *   Skrypt automatycznie posprząta po sobie, usuwając tymczasowe foldery (`venv_extractor`, `venv_creator`, `device`) i zatrzymując serwer Fridy na urządzeniu.

### Zastrzeżenie (Disclaimer)

Ten projekt jest przeznaczony wyłącznie do celów edukacyjnych i badawczych. Używaj go odpowiedzialnie i tylko w odniesieniu do treści, do których posiadasz legalne prawa. Nie ponoszę odpowiedzialności za niewłaściwe wykorzystanie tego narzędzia.

---

## English Version (EN)

This project contains a Python script that automates and repeats the process of extracting Widevine Content Decryption Module (CDM) keys from **rooted Android devices**.

The script operates in two phases, creating dedicated, isolated virtual environments for each stage. This ensures compatibility and stability, even with newer Python versions. The result is a `device.wvd` file that can be used by tools like `yt-dlp` to download DRM L3 protected content.

### Tested Environment

The script was successfully tested in the following configuration:

*   **Operating System**: Windows 11
*   **Python Version**: 3.13.5
*   **Emulator (AVD)**:
    *   **Device**: Pixel 9 Pro
    *   **API**: 35 ("VanillaIceCream", Android 15.0)
    *   **System Image**: Google APIs Intel x86_64 Atom System Image (It is important to use a "Google APIs" image, not "Google Play", to have root access).

### Files in the project

*   `automat_wvd_reczna_pywidevine.py` - The main script to run.
*   `frida-server` - **(You must provide this file yourself)**. This is the Frida server binary, which must match the processor architecture of your Android device.

### Prerequisites

Before you begin, make sure you meet the following requirements:

1.  **Python 3** installed on your computer.
2.  **A rooted Android device**. An **emulator** configured in Android Studio with a "Google APIs" system image is recommended.
3.  **USB debugging enabled** on the Android device.
4.  **Android SDK Platform-Tools** installed (usually included with the Android Studio installation). The script will try to locate `adb` automatically, but it is recommended to add the tools folder to the system's `PATH` environment variable.
5.  The **`frida-server`** binary downloaded.

### Preparation Instructions

1.  **Download `frida-server`**:
    *   Go to the official Frida releases page on GitHub: https://github.com/frida/frida/releases.
    *   Find the appropriate version. The version that worked in the tested configuration is **`frida-server-17.2.15-android-x86_64.xz`**.
    *   Remember to match the architecture (`ARCH`) to your device:
        *   `x86_64` for emulators on computers with an Intel/AMD processor.
        *   `arm64` for most modern physical phones.
    *   Unpack the `.xz` archive (e.g., using 7-Zip).
    *   Rename the unpacked file to `frida-server`.

2.  **Prepare the project folder**:
    *   Place the `automat_wvd_reczna_pywidevine.py` script and the downloaded and renamed `frida-server` in the same folder.

### Usage Instructions

1.  **Start the Android emulator**. Make sure it is fully loaded and ready.

2.  **Run the script**:
    *   Open a terminal or command prompt in the project folder.
    *   Type and execute the command:
        ```bash
        python automat_wvd_reczna_pywidevine.py
        ```

3.  **Follow the on-screen instructions**:
    *   **Phase 1: Key Extraction**
        *   The script will first create a virtual environment `venv_extractor` and install the `keydive` library in it.
        *   It will then display a list of connected devices and ask you to choose one (if there is more than one).
        *   The script will automatically prepare the device (upload and run the Frida server).
        *   **!!! NOW IT'S YOUR TURN !!!**
            *   The script will display the message `--- HINT: Play a video on https://shaka-player-demo.appspot.com ---`.
            *   **This is where you need to act**: on the emulator, **manually** open the Chrome browser, go to one of the provided addresses (e.g., `https://shaka-player-demo.appspot.com` or `https://bitmovin.com/demos/drm`) and **play a video**.
            *   During this time, logs from `keydive` should appear in the terminal, indicating that keys are being captured.

    *   **Phase 2: Creating the .wvd file**
        *   After successfully extracting the keys, the script will automatically proceed to the second phase.
        *   It will create a new virtual environment `venv_creator` and install `pywidevine` in it.
        *   It will use the extracted keys to generate the final file.

4.  **Conclusion**:
    *   Upon successful completion, you will find the **`device.wvd`** file in the project folder.
    *   The script will automatically clean up after itself by removing temporary folders (`venv_extractor`, `venv_creator`, `device`) and stopping the Frida server on the device.

### Zastrzeżenie (Disclaimer)

This project is intended for educational and research purposes only. Use it responsibly and only with content to which you have legal rights. The author is not responsible for any misuse of this tool.
