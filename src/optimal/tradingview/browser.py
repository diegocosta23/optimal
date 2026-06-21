from __future__ import annotations

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright


class BrowserManager:
    """Hanterar anslutningen till en redan öppen Chrome via CDP."""

    CDP_URL = "http://127.0.0.1:9222"

    def __init__(self) -> None:
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    def connect(self) -> bool:
        """Anslut till användarens Chrome."""

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.connect_over_cdp(
            self.CDP_URL
        )

        if not self.browser.contexts:
            raise RuntimeError("Ingen Chrome-kontext hittades.")

        self.context = self.browser.contexts[0]

        return True

    def find_superchart(self) -> Page:
        """Returnerar TradingViews Superchart om den redan är öppen."""

        assert self.context is not None

        for page in self.context.pages:

            if "tradingview.com/chart/" in page.url:
                self.page = page
                return page

        raise RuntimeError(
            "Ingen TradingView Superchart hittades."
        )

    def get_page(self) -> Page:

        if self.page is None:
            return self.find_superchart()

        return self.page

    def close(self) -> None:

        if self.playwright is not None:
            self.playwright.stop()