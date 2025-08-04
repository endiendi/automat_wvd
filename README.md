# Automatyczny Ekstraktor Kluczy Widevine L3

Ten projekt zawiera zestaw skryptów w języku Python, które automatyzują proces ekstrakcji kluczy Widevine Content Decryption Module (CDM) z **urządzeń z systemem Android posiadających uprawnienia roota**. Wynikiem działania jest plik `device.wvd`, który może być używany przez narzędzia takie jak `yt-dlp` do pobierania treści chronionych przez DRM L3.

## Pliki w projekcie

*   `start.py` - **(Zalecany sposób uruchomienia)** Uniwersalny skrypt startowy. Jego zadaniem jest przygotowanie środowiska (utworzenie wirtualnego środowiska `.venv`) i uruchomienie wybranego przez użytkownika skryptu głównego.
*   `automat_wvd_automatyczna.py` - W pełni zautomatyzowany skrypt, idealny do użytku z **emulatorami Android Studio**. Samodzielnie listuje, uruchamia wybrany emulator (AVD) i otwiera w nim stronę testową DRM, aby wywołać proces ekstrakcji.
*   `automat_wvd_reczna.py` - Skrypt do użytku z **fizycznymi urządzeniami** lub ręcznie uruchomionymi emulatorami. Wymaga od użytkownika manualnego uruchomienia aplikacji lub wideo z DRM na urządzeniu w odpowiednim momencie.
*   `frida-server` - **(Musisz dostarczyć ten plik samodzielnie)**. Jest to plik binarny serwera Frida, który musi być dopasowany do architektury procesora Twojego urządzenia Android.

## Wymagania wstępne

Zanim zaczniesz, upewnij się, że spełniasz następujące wymagania:

1.  **Python 3** zainstalowany na Twoim komputerze.
2.  **Zrootowane urządzenie z Androidem**. Może to być urządzenie fizyczne lub **emulator** skonfigurowany w Android Studio. Posiadanie Android Studio z co najmniej jednym skonfigurowanym AVD (Android Virtual Device) jest zalecane dla skryptu `automatyczna.py`.
3.  **Włączone debugowanie USB** na urządzeniu Android.
4.  Zainstalowane **Android SDK Platform-Tools**. Skrypt spróbuje automatycznie zlokalizować `adb` i `emulator`, ale najlepiej dodać folder z narzędziami do systemowej zmiennej środowiskowej `PATH`.
5.  Pobrany plik binarny **`frida-server`**. Można go znaleźć na stronie z wydaniami Fridy: https://github.com/frida/frida/releases.

## Instrukcja użycia

1.  **Pobierz `frida-server`**:
    *   Przejdź na stronę oficjalnych wydań Fridy na GitHubie: https://github.com/frida/frida/releases.
    *   Znajdź najnowszą wersję i pobierz plik `frida-server-XX.Y.ZZ-android-ARCH.xz`, gdzie `ARCH` to architektura procesora Twojego urządzenia (np. `arm64` dla większości fizycznych telefonów, `x86_64` dla emulatorów na komputerach z procesorem Intel/AMD).
    *   Rozpakuj archiwum `.xz`.
    *   Zmień nazwę rozpakowanego pliku na `frida-server`.

2.  **Przygotuj folder projektu**:
    *   Umieść pliki `start.py`, `automat_wvd_automatyczna.py`, `automat_wvd_reczna.py` oraz pobrany i przemianowany `frida-server` w tym samym folderze.

3.  **Uruchom skrypt startowy**:
    *   Otwórz terminal lub wiersz poleceń w folderze z plikami projektu.
    *   Wpisz i wykonaj komendę:
        ```bash
        python start.py
        ```
    *   Skrypt `start.py` najpierw utworzy wirtualne środowisko Pythona (`.venv`), jeśli jeszcze nie istnieje.

4.  **Wybierz skrypt do uruchomienia**:
    *   Launcher poprosi Cię o wybór jednego z dostępnych skryptów (`automatyczna` lub `reczna`). Wybierz numer i naciśnij Enter.

5.  **Postępuj zgodnie z instrukcjami wybranego skryptu**:
    *   Każdy ze skryptów najpierw sprawdzi, czy masz zainstalowaną bibliotekę `keydive` i w razie potrzeby zapyta o zgodę na instalację.
    *   **Jeśli wybrałeś `automat_wvd_automatyczna.py`:**
        *   Skrypt wyświetli listę dostępnych emulatorów (AVD) i poprosi o wybór jednego do uruchomienia.
        *   Następnie zapyta, którą stronę testową DRM otworzyć na emulatorze.
        *   Reszta procesu (uruchomienie emulatora, otwarcie strony, ekstrakcja kluczy) odbędzie się **automatycznie**.
    *   **Jeśli wybrałeś `automat_wvd_reczna.py`:**
        *   Podłącz fizyczne urządzenie lub uruchom emulator ręcznie.
        *   Skrypt wyświetli listę podłączonych urządzeń i poprosi o wybór.
        *   W kluczowym momencie skrypt wyświetli komunikat `!!! TERAZ TWOJA KOLEJ !!!`. **To jest moment na Twoje działanie**: na urządzeniu/emulatorze **ręcznie** uruchom aplikację (np. DRM Info) lub odtwórz wideo chronione przez DRM, aby aktywować proces systemowy.

6.  **Zakończenie**:
    *   Po pomyślnym zakończeniu, w folderze projektu znajdziesz plik **`device.wvd`**.
    *   Skrypty automatycznie posprzątają po sobie, usuwając pliki tymczasowe i zatrzymując serwer Fridy (oraz emulator, jeśli był uruchamiany automatycznie).

## Jak to działa? (Szczegóły techniczne)

*   **`start.py`**: Ten skrypt działa jako "launcher". Najpierw sprawdza, czy istnieje folder `.venv`. Jeśli nie, tworzy go, zapewniając czyste, izolowane środowisko dla zależności projektu. Następnie wyszukuje inne skrypty `.py` w katalogu, pozwala użytkownikowi wybrać jeden z nich i uruchamia go za pomocą interpretera Pythona z wirtualnego środowiska.

*   **`automat_wvd_automatyczna.py`**: To w pełni zautomatyzowana wersja.
    1.  **Wybór emulatora**: Listuje dostępne AVD (`emulator -list-avds`) i prosi użytkownika o wybór.
    2.  **Uruchomienie**: Startuje wybrany emulator z dodatkowymi flagami (`-writable-system`, `-no-snapshot-load`).
    3.  **Synchronizacja**: Czeka, aż emulator w pełni się uruchomi, sprawdzając właściwość systemową `sys.boot_completed`.
    4.  **Automatyzacja DRM**: Otwiera wybraną przez użytkownika stronę testową DRM za pomocą komendy `adb shell am start`, co automatycznie aktywuje potrzebny proces.
    5.  **Ekstrakcja i Sprzątanie**: Uruchamia serwer Fridy, wykonuje zrzut kluczy za pomocą `keydive`, generuje plik `.wvd`, a na końcu zatrzymuje serwer Fridy i **automatycznie zamyka emulator**.

*   **`automat_wvd_reczna.py`**: To wersja wymagająca interakcji.
    1.  **Wybór urządzenia**: Listuje podłączone urządzenia (`adb devices`) i prosi o wybór.
    2.  **Przygotowanie**: Uzyskuje uprawnienia roota i uruchamia serwer Fridy na wybranym urządzeniu.
    3.  **Pauza na akcję użytkownika**: Skrypt zatrzymuje się i informuje użytkownika, aby **ręcznie** uruchomił na urządzeniu aplikację lub wideo z DRM.
    4.  **Ekstrakcja i Sprzątanie**: Po aktywacji procesu DRM przez użytkownika, `keydive` przechwytuje klucze. Skrypt generuje plik `.wvd` i na końcu zatrzymuje serwer Fridy.

---

### Zastrzeżenie (Disclaimer)

Ten projekt jest przeznaczony wyłącznie do celów edukacyjnych i badawczych. Używaj go odpowiedzialnie i tylko w odniesieniu do treści, do których posiadasz legalne prawa. Nie ponoszę odpowiedzialności za niewłaściwe wykorzystanie tego narzędzia.