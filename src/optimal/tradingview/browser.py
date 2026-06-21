from __future__ import annotations

import os
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright


class BrowserManager:
    """Hantera anslutningen till TradingView via Chrome och CDP."""

    CDP_URL = "http://127.0.0.1:9222"
    SUPERCHART_URL = "https://www.tradingview.com/chart/CZ8FDi5t/"
    SUPERCHART_PREFIX = "https://www.tradingview.com/chart/"
    CHROME_CANDIDATES = (
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
    )

    def __init__(self) -> None:
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.chrome_process: subprocess.Popen[bytes] | None = None
        self.debug_profile_dir = Path(tempfile.gettempdir()) / "optimal-chrome-debug-profile"

    def connect(self) -> Page:
        """Anslut till Chrome via CDP och returnera TradingView Superchart."""

        if self.page is not None:
            return self.page

        self.playwright = sync_playwright().start()

        if not self._connect_over_cdp():
            self._start_chrome_for_debugging()
            self._wait_for_cdp_ready()

            if not self._connect_over_cdp():
                self.close()
                raise RuntimeError(
                    "Kunde inte ansluta till Chrome via CDP ens efter automatisk start."
                )

        if self.browser is None or not self.browser.contexts:
            self.close()
            raise RuntimeError("Ingen Chrome-kontext hittades.")

        self.context = self.browser.contexts[0]
        self.page = self.ensure_superchart()
        return self.page

    def is_connected(self) -> bool:
        return self.playwright is not None and self.browser is not None and self.context is not None

    def get_page(self) -> Page:
        """Returnera en aktiv TradingView-sida."""

        if self.page is None:
            return self.connect()

        return self.page

    def find_superchart(self) -> Page:
        """Hitta en redan öppen TradingView Superchart-flik."""

        if self.context is None:
            raise RuntimeError("Chrome är inte ansluten.")

        for page in self.context.pages:
            if page.url.startswith(self.SUPERCHART_PREFIX):
                self.page = page
                return page

        raise RuntimeError("Ingen TradingView Superchart hittades.")

    def ensure_superchart(self) -> Page:
        """Hitta Superchart eller öppna den fasta chart-URL:en."""

        if self.context is None:
            raise RuntimeError("Chrome är inte ansluten.")

        try:
            page = self.find_superchart()
        except RuntimeError:
            page = self.context.new_page()
            page.goto(self.SUPERCHART_URL, wait_until="domcontentloaded")
            self.page = page
            return page

        try:
            page.wait_for_load_state("domcontentloaded")
        except Exception:  # noqa: BLE001
            pass

        self.page = page
        return page

    def close(self) -> None:
        """Stäng Playwright-anslutningen om den finns."""

        if self.playwright is not None:
            self.playwright.stop()

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def _connect_over_cdp(self) -> bool:
        """Försök att ansluta till en redan körande CDP-instans."""

        if self.playwright is None:
            raise RuntimeError("Playwright är inte startad.")

        try:
            self.browser = self.playwright.chromium.connect_over_cdp(self.CDP_URL)
            return True
        except Exception:  # noqa: BLE001
            self.browser = None
            self.context = None
            self.page = None
            return False

    def _start_chrome_for_debugging(self) -> None:
        """Starta Chrome med remote debugging om den inte redan körs."""

        chrome_path = self._find_chrome_executable()
        self.debug_profile_dir.mkdir(parents=True, exist_ok=True)

        if self.chrome_process is not None and self.chrome_process.poll() is None:
            return

        creationflags = 0
        if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
            creationflags |= subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
        if hasattr(subprocess, "DETACHED_PROCESS"):
            creationflags |= subprocess.DETACHED_PROCESS  # type: ignore[attr-defined]

        args = [
            str(chrome_path),
            f"--remote-debugging-port=9222",
            f"--user-data-dir={self.debug_profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-popup-blocking",
            "--disable-features=Translate",
            "--new-window",
            self.SUPERCHART_URL,
        ]

        self.chrome_process = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )

    def _find_chrome_executable(self) -> Path:
        """Hitta den lokala Chrome-installationen."""

        for candidate in self.CHROME_CANDIDATES:
            if candidate.is_file():
                return candidate

        raise RuntimeError(
            "Kunde inte hitta Chrome. Förväntade mig chrome.exe i Program Files eller LocalAppData."
        )

    def _wait_for_cdp_ready(self, timeout_seconds: float = 20.0) -> None:
        """Vänta tills Chrome-CDP svarar."""

        deadline = time.monotonic() + timeout_seconds
        last_error: Exception | None = None

        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(f"{self.CDP_URL}/json/version", timeout=2) as response:
                    if response.status == 200:
                        return
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = exc
                time.sleep(0.5)

        raise RuntimeError("Chrome svarade inte på CDP i tid.") from last_error
