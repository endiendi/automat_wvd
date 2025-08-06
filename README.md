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
4.  Zainstalowane **Android SDK Platform-Tools**. Skrypt spróbuje automatycznie zlokalizować `adb`, ale najlepiej dodać folder z narzędziami do systemowej zmiennej środowiskowej `PATH`.
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


4.  **Zakończenie**:
    *   Po pomyślnym zakończeniu, w folderze projektu znajdziesz plik **`device.wvd`**.
    *   Skrypt automatycznie posprząta po sobie, usuwając tymczasowe foldery (`venv_extractor`, `venv_creator`, `device`) i zatrzymując serwer Fridy na urządzeniu.

---

### Zastrzeżenie (Disclaimer)

Ten projekt jest przeznaczony wyłącznie do celów edukacyjnych i badawczych. Używaj go odpowiedzialnie i tylko w odniesieniu do treści, do których posiadasz legalne prawa. Nie ponoszę odpowiedzialności za niewłaściwe wykorzystanie tego narzędzia.
