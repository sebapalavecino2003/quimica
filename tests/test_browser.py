"""Pruebas unitarias para detección y manejo de Google Chrome oficial."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.browser import (
    find_google_chrome_executable,
    BrowserManager,
    ChromeNotFoundError,
    ProfileLockedError,
)


def test_find_chrome_linux_mocked():
    with patch("sys.platform", "linux"):
        with patch("shutil.which", return_value="/usr/bin/google-chrome"):
            path = find_google_chrome_executable()
            assert path == Path("/usr/bin/google-chrome")


def test_find_chrome_windows_mocked():
    target_path = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")
    with patch("sys.platform", "win32"):
        with patch("shutil.which", return_value=None):
            with patch("os.environ", {
                "ProgramFiles": "C:/Program Files",
                "ProgramFiles(x86)": "C:/Program Files (x86)",
                "LOCALAPPDATA": "C:/Users/Test/AppData/Local",
            }):
                with patch.object(Path, "exists", lambda self: self == target_path):
                    with patch.object(Path, "is_file", return_value=True):
                        path = find_google_chrome_executable()
                        assert path == target_path


def test_find_chrome_not_found():
    with patch("shutil.which", return_value=None):
        with patch.object(Path, "exists", return_value=False):
            with patch.object(Path, "is_file", return_value=False):
                path = find_google_chrome_executable()
                assert path is None


def test_browser_manager_raises_chrome_not_found():
    with patch("src.browser.find_google_chrome_executable", return_value=None):
        mgr = BrowserManager(profile_dir=Path("/tmp/test_nonexistent_profile"))
        with patch("src.browser.sync_playwright") as mock_pw:
            mock_chromium = MagicMock()
            mock_chromium.launch_persistent_context.side_effect = Exception("Executable doesn't exist")
            mock_pw.return_value.start.return_value.chromium = mock_chromium

            with pytest.raises(ChromeNotFoundError):
                mgr.start()


def test_browser_manager_raises_profile_locked():
    fake_path = Path("/usr/bin/google-chrome")
    with patch("src.browser.find_google_chrome_executable", return_value=fake_path):
        mgr = BrowserManager(profile_dir=Path("/tmp/test_locked_profile"))
        with patch("src.browser.sync_playwright") as mock_pw:
            mock_chromium = MagicMock()
            mock_chromium.launch_persistent_context.side_effect = Exception("ProcessSingleton lock active")
            mock_pw.return_value.start.return_value.chromium = mock_chromium

            with pytest.raises(ProfileLockedError):
                mgr.start()
