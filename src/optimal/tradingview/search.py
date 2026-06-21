from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import Locator, Page

from src.optimal.tradingview.browser import BrowserManager


@dataclass(slots=True)
class SearchResult:
    name: str


class SearchManager:
    """Hanterar företagssökningen i TradingView."""

    def __init__(self, browser: BrowserManager) -> None:
        self.browser = browser
        self.page: Page = browser.get_page()

    def _search_button(self) -> Locator:
        return self.page.get_by_label("Symbol Search")

    def _search_input(self) -> Locator:
        return self.page.locator("input")

    def open_search(self) -> None:
        self._search_button().click()

    def search_company(self, company: str) -> None:
        self.open_search()

        field = self._search_input().first
        field.fill("")
        field.fill(company)

    def results(self) -> list[SearchResult]:
        items = self.page.locator('[data-name="symbol-item"]')

        results: list[SearchResult] = []

        count = items.count()

        for i in range(count):
            text = items.nth(i).inner_text().strip()

            if text:
                results.append(SearchResult(text))

        return results