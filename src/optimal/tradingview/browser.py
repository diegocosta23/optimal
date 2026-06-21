from __future__ import annotations

import time
import urllib.error
import urllib.request
from typing import Final

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright


class BrowserManager:
    """Hantera anslutningen till användarens redan öppna Chrome via CDP."""

    CDP_URL: Final[str] = "http://127.0.0.1:9222"
    SUPERCHART_PREFIX: Final[str] = "https://www.tradingview.com/chart/"
    CDP_READY_TIMEOUT_SECONDS: Final[float] = 15.0

    def __init__(self) -> None:
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    def connect(self) -> Page:
        """Anslut till Chrome via CDP och returnera en redan öppen TradingView-tab."""

        if self.page is not None:
            return self.page

        self.playwright = sync_playwright().start()
        self._wait_for_cdp_ready()

        if not self._connect_over_cdp():
            self.close()
            raise RuntimeError(
                "Kunde inte ansluta till Chrome via CDP. Kontrollera att Chrome körs "
                "med --remote-debugging-port=9222 och att du har öppnat TradingView "
                "i den instansen."
            )

        self.page = self.find_superchart()
        return self.page

    def is_connected(self) -> bool:
        return (
            self.playwright is not None
            and self.browser is not None
            and self.context is not None
            and self.page is not None
        )

    def get_page(self) -> Page:
        """Returnera en aktiv TradingView-sida."""

        if self.page is None:
            return self.connect()

        return self.page

    def find_superchart(self) -> Page:
        """Hitta en redan öppen TradingView Superchart-flik i alla tillgängliga kontexter."""

        if self.browser is None:
            raise RuntimeError("Chrome är inte ansluten.")

        for context in self.browser.contexts:
            for page in context.pages:
                if page.url.startswith(self.SUPERCHART_PREFIX):
                    self.context = context
                    self.page = page
                    return page

        pages = self.describe_pages()
        detail = "\n".join(pages) if pages else "(inga öppna sidor hittades)"
        raise RuntimeError(
            "Ingen TradingView Superchart hittades i den öppna Chrome-instansen. "
            "Öppna TradingView-sidan först och försök igen.\n\n" + detail
        )

    def describe_pages(self) -> list[str]:
        """Beskriv alla öppna sidor för felsökning."""

        if self.browser is None:
            return []

        lines: list[str] = []
        for context_index, context in enumerate(self.browser.contexts, start=1):
            for page_index, page in enumerate(context.pages, start=1):
                lines.append(f"Context {context_index}, Page {page_index}: {page.url}")

        return lines

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

    def _wait_for_cdp_ready(self) -> None:
        """Vänta tills Chrome-CDP svarar eller tiden går ut."""

        deadline = time.monotonic() + self.CDP_READY_TIMEOUT_SECONDS
        last_error: Exception | None = None

        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(f"{self.CDP_URL}/json/version", timeout=2) as response:
                    if response.status == 200:
                        return
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = exc
                time.sleep(0.5)

        raise RuntimeError(
            "Chrome svarade inte på CDP i tid. Starta Chrome med "
            "--remote-debugging-port=9222 och öppna TradingView i den instansen."
        ) from last_error
