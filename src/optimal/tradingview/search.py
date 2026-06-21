from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import Locator, Page

from src.optimal.tradingview.browser import BrowserManager
from src.optimal.tradingview.selectors import TradingViewSelectors


@dataclass(slots=True)
class SearchResult:
    """Ett sökresultat från TradingView."""

    name: str
    raw_text: str = ""


class SearchManager:
    """Hanterar företagssökningen i TradingView."""

    def __init__(self, browser: BrowserManager) -> None:
        self.browser = browser
        self.selectors = TradingViewSelectors()
        self.page: Page | None = None

    def refresh_page(self) -> Page:
        """Hämta aktuell TradingView-sida från BrowserManager."""

        self.page = self.browser.get_page()
        return self.page

    def _require_page(self) -> Page:
        if self.page is None:
            return self.refresh_page()
        return self.page

    def _search_button(self) -> Locator | None:
        page = self._require_page()
        return self.selectors.first_visible(page, self.selectors.search_button_selectors)

    def _search_input(self) -> Locator:
        page = self._require_page()
        locator = self.selectors.first_visible(page, self.selectors.search_input_selectors)
        if locator is None:
            raise RuntimeError("Kunde inte hitta TradingViews sökfält.")
        return locator

    def open_search(self) -> None:
        """Öppna TradingViews sökdialog eller fokusera befintligt fält."""

        page = self.refresh_page()

        button = self._search_button()
        if button is not None:
            button.click()
            page.wait_for_timeout(150)
            return

        shortcuts = ("Control+K", "Alt+S", "Control+Shift+P")
        for shortcut in shortcuts:
            try:
                page.keyboard.press(shortcut)
                page.wait_for_timeout(150)
                if self.selectors.first_visible(page, self.selectors.search_input_selectors):
                    return
            except Exception:  # noqa: BLE001
                continue

        raise RuntimeError("Kunde inte öppna TradingViews sökning.")

    def search_company(self, company: str, wait_ms: int = 350) -> list[SearchResult]:
        """Skriv ett företagsnamn i TradingView och hämta träffarna."""

        query = company.strip()
        if not query:
            return []

        page = self.refresh_page()
        self.open_search()

        field = self._search_input()
        field.click()
        try:
            field.fill(query)
        except Exception:  # noqa: BLE001
            field.press("Control+A")
            field.type(query, delay=20)

        page.wait_for_timeout(wait_ms)
        return self.read_results()

    def read_results(self) -> list[SearchResult]:
        """Läs alla synliga resultat i TradingViews söklista."""

        page = self.refresh_page()
        results: list[SearchResult] = []
        seen: set[str] = set()

        for selector in self.selectors.result_row_selectors:
            locator = page.locator(selector)

            try:
                count = locator.count()
            except Exception:  # noqa: BLE001
                continue

            for index in range(count):
                item = locator.nth(index)
                try:
                    if not item.is_visible():
                        continue
                    text = item.inner_text().strip()
                except Exception:  # noqa: BLE001
                    continue

                name = self._normalize_result_name(text)
                if not name:
                    continue

                key = name.casefold()
                if key in seen:
                    continue

                seen.add(key)
                results.append(SearchResult(name=name, raw_text=text))

        return results

    def select_result(self, company: str) -> None:
        """Klicka på ett specifikt resultat i TradingView."""

        target = self._normalize_result_name(company).casefold()
        if not target:
            raise RuntimeError("Tomt företagsnamn kunde inte väljas.")

        page = self.refresh_page()

        for selector in self.selectors.result_row_selectors:
            locator = page.locator(selector)

            try:
                count = locator.count()
            except Exception:  # noqa: BLE001
                continue

            for index in range(count):
                item = locator.nth(index)
                try:
                    if not item.is_visible():
                        continue
                    text = item.inner_text().strip()
                except Exception:  # noqa: BLE001
                    continue

                name = self._normalize_result_name(text).casefold()
                if not name:
                    continue

                if target in name or name in target:
                    item.click()
                    page.wait_for_timeout(250)
                    return

        try:
            page.get_by_text(company, exact=False).first.click()
            page.wait_for_timeout(250)
            return
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Kunde inte välja resultatet: {company}") from exc

    def _normalize_result_name(self, text: str) -> str:
        """Gör TradingView-text mer användbar som visningsnamn."""

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return ""

        first_line = lines[0]
        return " ".join(first_line.split())
