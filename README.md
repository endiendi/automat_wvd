# Automatyczny Ekstraktor Kluczy Widevine L3

Ten projekt zawiera zestaw skryptów w języku Python, które automatyzują proces ekstrakcji kluczy Widevine Content Decryption Module (CDM) z **urządzeń z systemem Android posiadających uprawnienia roota**. Wynikiem działania jest plik `device.wvd`, który może być używany przez narzędzia takie jak `yt-dlp` do pobierania treści chronionych przez DRM L3.

## Pliki w projekcie

*   `start.py` - Uniwersalny skrypt startowy. Jego zadaniem jest przygotowanie środowiska (utworzenie wirtualnego środowiska `.venv`) i uruchomienie głównego skryptu.
*   `automat_wvd3.py` - Główny skrypt, który przeprowadza cały proces ekstrakcji kluczy.
*   `frida-server` - **(Musisz dostarczyć ten plik samodzielnie)**. Jest to plik binarny serwera Frida, który musi być dopasowany do architektury procesora Twojego urządzenia Android.

## Wymagania wstępne

Zanim zaczniesz, upewnij się, że spełniasz następujące wymagania:

1.  **Python 3** zainstalowany na Twoim komputerze.
2.  **Zrootowane urządzenie z Androidem** (fizyczne lub emulator).
3.  **Włączone debugowanie USB** na urządzeniu Android.
4.  Zainstalowane **Android SDK Platform-Tools** (a w nim `adb`). Skrypt spróbuje automatycznie zlokalizować `adb`, ale najlepiej dodać folder `platform-tools` do systemowej zmiennej środowiskowej `PATH`.
5.  Pobrany plik binarny **`frida-server`**.

## Instrukcja użycia

1.  **Pobierz `frida-server`**:
    *   Przejdź na stronę oficjalnych wydań Fridy na GitHubie.
    *   Znajdź najnowszą wersję i pobierz plik `frida-server-XX.Y.ZZ-android-ARCH.xz`, gdzie `ARCH` to architektura procesora Twojego urządzenia (np. `arm64`, `x86_64`).
    *   Rozpakuj archiwum `.xz`.
    *   Zmień nazwę rozpakowanego pliku na `frida-server`.

2.  **Przygotuj folder projektu**:
    *   Umieść pliki `start.py`, `automat_wvd3.py` oraz pobrany i przemianowany `frida-server` w tym samym folderze.

3.  **Podłącz urządzenie**:
    *   Podłącz swoje urządzenie z Androidem do komputera kablem USB.
    *   Upewnij się, że urządzenie jest poprawnie wykrywane, wpisując w terminalu komendę `adb devices`. Powinieneś zobaczyć numer seryjny swojego urządzenia ze statusem `device`.

4.  **Uruchom skrypt**:
    *   Otwórz terminal lub wiersz poleceń w folderze z plikami projektu.
    *   Wpisz i wykonaj komendę:
        ```bash
        python start.py
        ```

5.  **Postępuj zgodnie z instrukcjami na ekranie**:
    *   Skrypt najpierw utworzy wirtualne środowisko Pythona.
    *   Następnie zapyta, czy zainstalować bibliotekę `keydive`, jeśli nie jest jeszcze zainstalowana. Wpisz `y` i naciśnij Enter.
    *   Jeśli podłączone jest więcej niż jedno urządzenie, zostaniesz poproszony o wybór właściwego.
    *   Skrypt automatycznie przygotuje urządzenie (uzyska uprawnienia roota i uruchomi serwer Fridy).
    *   W kluczowym momencie skrypt wyświetli komunikat: `WSKAZÓWKA: Gdy skrypt 'zawiśnie', uruchom na emulatorze aplikację DRM Info...`. **To jest moment na Twoje działanie**:
        *   Na podłączonym urządzeniu z Androidem uruchom aplikację, która korzysta z Widevine DRM. Najprostsze opcje to:
            *   Aplikacja **DRM Info** (dostępna w Sklepie Play).
            *   Odtworzenie dowolnego wideo na stronie Shaka Player Demo.
            *   Uruchomienie aplikacji streamingowej (np. Netflix).
    *   Gdy tylko moduł DRM zostanie aktywowany, `keydive` przechwyci klucze, a skrypt automatycznie wznowi działanie.

6.  **Zakończenie**:
    *   Po pomyślnym zakończeniu, w folderze projektu znajdziesz plik **`device.wvd`**.
    *   Skrypt automatycznie posprząta po sobie, usuwając pliki tymczasowe i zatrzymując serwer Fridy na urządzeniu.

## Jak to działa? (Szczegóły techniczne)

*   **`start.py`**: Ten skrypt działa jako "launcher". Najpierw sprawdza, czy istnieje folder `.venv`. Jeśli nie, tworzy go, zapewniając czyste, izolowane środowisko dla zależności projektu. Następnie wyszukuje inne skrypty `.py` w katalogu i uruchamia `automat_wvd3.py` za pomocą interpretera Pythona z wirtualnego środowiska.

*   **`automat_wvd3.py`**: To serce operacji.
    1.  **Sprawdzenie zależności**: Weryfikuje obecność biblioteki `keydive` i oferuje jej instalację przez `pip`.
    2.  **Połączenie z ADB**: Lokalizuje plik wykonywalny `adb` i wybiera aktywne urządzenie.
    3.  **Przygotowanie urządzenia**: Wysyła żądanie `adb root`, aby uzyskać najwyższe uprawnienia. Następnie kopiuje plik `frida-server` do folderu `/data/local/tmp/` na urządzeniu, nadaje mu uprawnienia do wykonywania (`chmod 755`) i uruchamia go w tle.
    4.  **Zrzut kluczy**: Wywołuje narzędzie `keydive` z odpowiednimi parametrami. `keydive` używa serwera Fridy do podpięcia się pod proces systemowy odpowiedzialny za DRM i zrzuca z pamięci klucze `client_id.bin` oraz `private_key.pem`.
    5.  **Generowanie pliku `.wvd`**: Po pomyślnym zrzucie, skrypt odnajduje pobrane pliki kluczy i łączy ich zawartość binarną w jeden plik wyjściowy `device.wvd`.
    6.  **Sprzątanie**: Na koniec usuwa folder `device/` stworzony przez `keydive` oraz, co najważniejsze, wysyła polecenie `killall frida-server` do urządzenia, aby zakończyć działanie serwera Fridy. Dzieje się to również w przypadku błędu lub przerwania skryptu przez użytkownika.

---

### Zastrzeżenie (Disclaimer)

Ten projekt jest przeznaczony wyłącznie do celów edukacyjnych i badawczych. Używaj go odpowiedzialnie i tylko w odniesieniu do treści, do których posiadasz legalne prawa. Nie ponoszę odpowiedzialności za niewłaściwe wykorzystanie tego narzędzia.