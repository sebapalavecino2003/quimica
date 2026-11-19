"""Módulo de gestión del navegador Playwright con Google Chrome oficial y perfil persistente."""

import os
import shutil
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, BrowserContext, Page, Playwright
from src.config import Config


class ChromeNotFoundError(Exception):
    """Excepción lanzada cuando no se encuentra Google Chrome oficial en el sistema."""
    pass


class ProfileLockedError(Exception):
    """Excepción lanzada cuando el perfil de usuario está bloqueado por otra instancia."""
    pass


def find_google_chrome_executable() -> Path | None:
    """Busca el ejecutable oficial de Google Chrome en Windows, Linux y macOS."""
    # 1. Comprobación en PATH del sistema
    candidates_in_path = ["chrome", "google-chrome", "google-chrome-stable"]
    for name in candidates_in_path:
        found = shutil.which(name)
        if found:
            return Path(found)

    # 2. Rutas estándar en Windows
    if sys.platform.startswith("win"):
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
        local_app_data = os.environ.get("LOCALAPPDATA", "")

        windows_paths = [
            Path(program_files) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(program_files_x86) / "Google" / "Chrome" / "Application" / "chrome.exe",
        ]
        if local_app_data:
            windows_paths.append(
                Path(local_app_data) / "Google" / "Chrome" / "Application" / "chrome.exe"
            )

        for p in windows_paths:
            if p.exists() and p.is_file():
                return p

        # Intento mediante el Registro de Windows (winreg)
        try:
            import winreg  # type: ignore

            reg_keys = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
            ]
            for root, subkey in reg_keys:
                try:
                    with winreg.OpenKey(root, subkey) as key:
                        val, _ = winreg.QueryValueEx(key, "")
                        if val and Path(val).is_file():
                            return Path(val)
                except OSError:
                    continue
        except ImportError:
            pass

    # 3. Rutas estándar en Linux
    elif sys.platform.startswith("linux"):
        linux_paths = [
            Path("/usr/bin/google-chrome"),
            Path("/usr/bin/google-chrome-stable"),
            Path("/opt/google/chrome/chrome"),
            Path("/opt/google/chrome/google-chrome"),
        ]
        for p in linux_paths:
            if p.exists() and p.is_file():
                return p

    # 4. Rutas estándar en macOS
    elif sys.platform == "darwin":
        mac_path = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        if mac_path.exists() and mac_path.is_file():
            return mac_path

    return None


class BrowserManager:
    def __init__(self, profile_dir: Path | None = None, headless: bool | None = None):
        self.profile_dir = profile_dir or Config.BROWSER_PROFILE_DIR
        self.headless = headless if headless is not None else Config.HEADLESS
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    def start(self) -> Page:
        """Inicia Google Chrome oficial con perfil persistente en modo visible."""
        chrome_exec = find_google_chrome_executable()

        self._playwright = sync_playwright().start()

        launch_kwargs = {
            "user_data_dir": str(self.profile_dir),
            "headless": self.headless,
            "channel": "chrome",
            "viewport": {"width": 1280, "height": 900},
            "args": [
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
            ],
            "ignore_default_args": ["--enable-automation"],
        }

        # Si se detectó la ruta explícita del ejecutable, se puede especificar
        if chrome_exec and chrome_exec.exists():
            launch_kwargs["executable_path"] = str(chrome_exec)

        try:
            self._context = self._playwright.chromium.launch_persistent_context(**launch_kwargs)
        except Exception as exc:
            err_msg = str(exc).lower()
            if "singletonlock" in err_msg or "processsingleton" in err_msg or "user data directory is already in use" in err_msg:
                self.close()
                raise ProfileLockedError(
                    f"El perfil de automatización en '{self.profile_dir}' está bloqueado por otra instancia de Chrome.\n"
                    "Por favor cierre la ventana de Chrome existente o finalice el proceso antes de reintentar."
                ) from exc
            elif "executable doesn't exist" in err_msg or "cannot find chrome" in err_msg or not chrome_exec:
                self.close()
                raise ChromeNotFoundError(
                    "Google Chrome no está instalado o no fue encontrado en las rutas estándar del sistema.\n"
                    "Por favor descargue e instale Google Chrome oficial desde: https://www.google.com/chrome/"
                ) from exc
            else:
                self.close()
                raise exc

        pages = self._context.pages
        self._page = pages[0] if pages else self._context.new_page()
        return self._page

    def navigate_to(self, url: str) -> None:
        """Navega a una URL específica."""
        if not self._page:
            raise RuntimeError("El navegador no ha sido iniciado.")
        self._page.goto(url, wait_until="domcontentloaded", timeout=60000)

    @property
    def page(self) -> Page:
        if not self._page:
            raise RuntimeError("El navegador no ha sido iniciado.")
        return self._page

    def keep_open_until_user_closes(self) -> None:
        """Mantiene el navegador abierto indefinidamente para revisión manual."""
        if not self._page:
            return
        print("\n[INFO] Google Chrome permanece abierto para tu revisión.")
        print("[INFO] Presioná Enter en esta terminal cuando desees finalizar la sesión del asistente...")
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            pass
        finally:
            self.close()

    def close(self) -> None:
        """Cierra el contexto y Playwright limpiamente."""
        if self._context:
            try:
                self._context.close()
            except Exception:
                pass
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
