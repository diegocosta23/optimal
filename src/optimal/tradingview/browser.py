from __future__ import annotations

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright


class BrowserManager:
    """Hantera anslutningen till användarens redan öppna Chrome via CDP."""

    CDP_URL = "http://127.0.0.1:9222"
    SUPERCHART_URL = "https://www.tradingview.com/chart/CZ8FDi5t/"
    SUPERCHART_PREFIX = "https://www.tradingview.com/chart/"

    def __init__(self) -> None:
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    def connect(self) -> Page:
        """Anslut till Chrome via CDP och returnera TradingView Superchart."""

        if self.page is not None:
            return self.page

        self.playwright = sync_playwright().start()

        try:
            self.browser = self.playwright.chromium.connect_over_cdp(self.CDP_URL)
        except Exception as exc:  # noqa: BLE001
            self.close()
            raise RuntimeError(
                "Kunde inte ansluta till Chrome via CDP. Starta din vanliga Chrome "
                "med --remote-debugging-port=9222 och öppna sedan din inloggade "
                "TradingView Superchart där."
            ) from exc

        if not self.browser.contexts:
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
