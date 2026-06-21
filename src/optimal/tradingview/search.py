from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Iterable

from playwright.sync_api import Locator, Page

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
        self._wait_for_page_ready(page)

        button = page.get_by_role("button", name=SEARCH_BUTTON_NAME)
        button.click()
        page.wait_for_timeout(200)

    def search_company(self, company: str) -> list[SearchResult]:
        """Sök efter ett företagsnamn och returnera synliga träffar."""

        query = company.strip()
        if not query:
            return []

        page = self.refresh()
        self.open_search()

        field = self._searchbox(page)
        field.click()
        try:
            field.fill("")
        except Exception:  # noqa: BLE001
            field.press("Control+A")
            field.press("Backspace")

        field.type(query, delay=25)
        page.wait_for_timeout(600)

        return self.read_results()

    def read_results(self) -> list[SearchResult]:
        """Läs alla synliga symbol-träffar från TradingView."""

        page = self.refresh()
        candidates = self._result_locators(page)

        results: list[SearchResult] = []
        seen: set[str] = set()

        for locator in candidates:
            try:
                count = locator.count()
            except Exception:  # noqa: BLE001
                continue

            for index in range(count):
                row = locator.nth(index)
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

        query = company.strip()
        if not query:
            raise RuntimeError("Tomt företagsnamn kunde inte väljas.")

        page = self.refresh()

        for locator in self._result_locators(page):
            try:
                # Försök exakt först, sedan mer generellt.
                locator.get_by_text(query, exact=False).first.click()
                page.wait_for_timeout(300)
                return
            except Exception:  # noqa: BLE001
                pass

            try:
                count = locator.count()
            except Exception:  # noqa: BLE001
                continue

            target = query.casefold()
            for index in range(count):
                row = locator.nth(index)
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
                    page.wait_for_timeout(300)
                    return

        # Fallback: klicka på första matchande text.
        try:
            page.get_by_text(query, exact=False).first.click()
            page.wait_for_timeout(300)
            return
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Kunde inte välja resultatet: {company}") from exc

    def _searchbox(self, page: Page) -> Locator:
        box = page.get_by_role("searchbox", name=SEARCHBOX_NAME)
        try:
            box.wait_for(state="visible", timeout=5000)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("Kunde inte hitta TradingViews sökfält.") from exc
        return box

    def _result_locators(self, page: Page) -> list[Locator]:
        return [
            page.get_by_role("option"),
            page.locator("[data-name='symbol-item']"),
            page.locator("[data-name*='search-result' i]"),
            page.locator("[role='option']"),
        ]

    def _wait_for_page_ready(self, page: Page) -> None:
        try:
            page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:  # noqa: BLE001
            pass

    def _extract_name(self, text: str) -> str:
        """Extrahera ett visningsnamn från TradingViews råtext."""

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return ""

        return " ".join(lines[0].split())
