from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from playwright.sync_api import Page

from src.optimal.tradingview.browser import BrowserManager

SEARCH_BUTTON_NAME: Final[str] = "Search"
SEARCHBOX_NAME: Final[str] = "Symbol, ISIN, or CUSIP"


@dataclass(slots=True)
class SearchResult:
    """Ett TradingView-resultat från symbol-sökningen."""

    name: str
    raw_text: str = ""


class SearchManager:
    """Hanterar företagssökning i TradingView Superchart."""

    def __init__(self, browser: BrowserManager) -> None:
        self.browser = browser
        self.page: Page | None = None

    def refresh(self) -> Page:
        """Hämta aktuell TradingView-sida från BrowserManager."""

        self.page = self.browser.get_page()
        return self.page

    def open_search(self) -> None:
        """Öppna TradingViews sökdialog."""

        page = self.refresh()
        page.get_by_role("button", name=SEARCH_BUTTON_NAME).click()
        page.wait_for_timeout(150)

    def search_company(self, company: str) -> list[SearchResult]:
        """Sök efter ett företagsnamn och returnera synliga träffar."""

        query = company.strip()
        if not query:
            return []

        page = self.refresh()
        self.open_search()

        field = page.get_by_role("searchbox", name=SEARCHBOX_NAME)
        field.click()
        field.fill("")
        field.type(query, delay=25)

        page.wait_for_timeout(550)
        return self.read_results()

    def read_results(self) -> list[SearchResult]:
        """Läs alla synliga symbol-träffar från TradingView."""

        page = self.refresh()
        rows = page.locator("[data-name='symbol-item']")

        results: list[SearchResult] = []
        seen: set[str] = set()

        for index in range(rows.count()):
            row = rows.nth(index)
            try:
                if not row.is_visible():
                    continue
                text = row.inner_text().strip()
            except Exception:  # noqa: BLE001
                continue

            name = self._extract_name(text)
            if not name:
                continue

            key = name.casefold()
            if key in seen:
                continue

            seen.add(key)
            results.append(SearchResult(name=name, raw_text=text))

        return results

    def select_result(self, company: str) -> None:
        """Klicka på ett valt företag i resultatlistan."""

        self.select_company(company)

    def select_company(self, company: str) -> None:
        """Klicka på ett valt företag i resultatlistan."""

        query = company.strip()
        if not query:
            raise RuntimeError("Tomt företagsnamn kunde inte väljas.")

        page = self.refresh()

        try:
            page.get_by_text(query, exact=False).first.click()
            page.wait_for_timeout(250)
            return
        except Exception:  # noqa: BLE001
            pass

        rows = page.locator("[data-name='symbol-item']")
        target = query.casefold()

        for index in range(rows.count()):
            row = rows.nth(index)
            try:
                if not row.is_visible():
                    continue
                text = row.inner_text().strip()
            except Exception:  # noqa: BLE001
                continue

            name = self._extract_name(text)
            if not name:
                continue

            normalized = name.casefold()
            if target in normalized or normalized in target:
                row.click()
                page.wait_for_timeout(250)
                return

        raise RuntimeError(f"Kunde inte välja resultatet: {company}")

    def _extract_name(self, text: str) -> str:
        """Extrahera ett visningsnamn från TradingViews råtext."""

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return ""

        return " ".join(lines[0].split())
