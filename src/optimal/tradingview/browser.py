from __future__ import annotations

import asyncio
import threading
from typing import Final

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright


class BrowserManager:
    """Hantera anslutningen till användarens redan öppna Chrome via CDP."""

    CDP_URL: Final[str] = "http://127.0.0.1:9222"
    SUPERCHART_URL: Final[str] = "https://www.tradingview.com/chart/CZ8FDi5t/"
    SUPERCHART_PREFIX: Final[str] = "https://www.tradingview.com/chart/"

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._run_loop, name="optimal-playwright", daemon=True)
        self._loop_thread.start()

        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self._closed = False

    def connect(self) -> Page:
        """Anslut till Chrome via CDP och returnera en redan öppen TradingView-tab."""

        return self.run(self.connect_async())

    def run(self, awaitable):
        """Kör en coroutine i den dedikerade Playwright-loopen."""

        if self._closed:
            raise RuntimeError("BrowserManager är stängd.")

        future = asyncio.run_coroutine_threadsafe(awaitable, self._loop)
        return future.result()

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

    async def connect_async(self) -> Page:
        """Asynkron anslutning till Chrome via CDP."""

        if self.page is not None:
            return self.page

        if self.playwright is None:
            self.playwright = await async_playwright().start()

        try:
            self.browser = await self.playwright.chromium.connect_over_cdp(self.CDP_URL)
        except Exception as exc:  # noqa: BLE001
            await self.close_async()
            raise RuntimeError(
                "Kunde inte ansluta till Chrome via CDP. Kontrollera att Chrome körs "
                "med --remote-debugging-port=9222 och att du har öppnat TradingView "
                "i den instansen."
            ) from exc

        self.page = await self.find_superchart_async()
        return self.page

    async def find_superchart_async(self) -> Page:
        """Hitta en redan öppen TradingView Superchart-flik i alla tillgängliga kontexter."""

        if self.browser is None:
            raise RuntimeError("Chrome är inte ansluten.")

        for context in self.browser.contexts:
            for page in context.pages:
                if page.url.startswith(self.SUPERCHART_PREFIX):
                    self.context = context
                    self.page = page
                    return page

        if not self.browser.contexts:
            raise RuntimeError("Ingen Chrome-kontext hittades.")

        self.context = self.browser.contexts[0]
        page = await self.context.new_page()
        await page.goto(self.SUPERCHART_URL, wait_until="domcontentloaded")
        self.page = page
        return page

    async def describe_pages_async(self) -> list[str]:
        """Beskriv alla öppna sidor för felsökning."""

        if self.browser is None:
            return []

        lines: list[str] = []
        for context_index, context in enumerate(self.browser.contexts, start=1):
            for page_index, page in enumerate(context.pages, start=1):
                lines.append(f"Context {context_index}, Page {page_index}: {page.url}")

        return lines

    async def search_company_async(self, company: str) -> list[str]:
        """Sök efter ett företag i TradingView och returnera resultatens namn."""

        query = company.strip()
        if not query:
            return []

        page = await self._require_page_async()
        await self._open_search_async(page)
        await self._type_company_async(page, query)
        return await self._read_result_names_async(page)

    async def select_company_async(self, company: str) -> None:
        """Välj ett företag i TradingViews sökresultat."""

        query = company.strip()
        if not query:
            raise RuntimeError("Tomt företagsnamn kunde inte väljas.")

        page = await self._require_page_async()
        candidates = await self._result_locators_async(page)
        target = query.casefold()

        for locator in candidates:
            try:
                count = await locator.count()
            except Exception:  # noqa: BLE001
                continue

            for index in range(count):
                row = locator.nth(index)
                try:
                    if not await row.is_visible():
                        continue
                    text = (await row.inner_text()).strip()
                except Exception:  # noqa: BLE001
                    continue

                name = self._extract_name(text)
                if not name:
                    continue

                normalized = name.casefold()
                if target in normalized or normalized in target:
                    await row.click()
                    return

        try:
            await page.get_by_text(query, exact=False).first.click()
            return
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Kunde inte välja resultatet: {company}") from exc

    async def close_async(self) -> None:
        """Stäng Playwright-anslutningen om den finns."""

        if self.playwright is not None:
            await self.playwright.stop()

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def close(self) -> None:
        """Stäng Playwright-anslutningen och bakgrundsloopen."""

        if self._closed:
            return

        self._closed = True
        try:
            if self.playwright is not None:
                self.run(self.close_async())
        except Exception:  # noqa: BLE001
            pass

        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._loop_thread.is_alive():
            self._loop_thread.join(timeout=5)

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    async def _require_page_async(self) -> Page:
        if self.page is not None:
            return self.page
        return await self.connect_async()

    async def _open_search_async(self, page: Page) -> None:
        await page.wait_for_load_state("domcontentloaded")
        await page.get_by_role("button", name="Search").click()
        await page.wait_for_timeout(200)

    async def _type_company_async(self, page: Page, company: str) -> None:
        field = page.get_by_role("searchbox", name="Symbol, ISIN, or CUSIP")
        await field.wait_for(state="visible", timeout=5000)
        await field.click()
        try:
            await field.fill("")
        except Exception:  # noqa: BLE001
            await field.press("Control+A")
            await field.press("Backspace")
        await field.type(company, delay=25)
        await page.wait_for_timeout(600)

    async def _read_result_names_async(self, page: Page) -> list[str]:
        results: list[str] = []
        seen: set[str] = set()
        for locator in await self._result_locators_async(page):
            try:
                count = await locator.count()
            except Exception:  # noqa: BLE001
                continue

            for index in range(count):
                row = locator.nth(index)
                try:
                    if not await row.is_visible():
                        continue
                    text = (await row.inner_text()).strip()
                except Exception:  # noqa: BLE001
                    continue

                name = self._extract_name(text)
                if not name:
                    continue

                key = name.casefold()
                if key in seen:
                    continue

                seen.add(key)
                results.append(name)

        return results

    async def _result_locators_async(self, page: Page):
        return [
            page.get_by_role("option"),
            page.locator("[data-name='symbol-item']"),
            page.locator("[data-name*='search-result' i]"),
            page.locator("[role='option']"),
        ]

    def _extract_name(self, text: str) -> str:
        """Extrahera ett visningsnamn från TradingViews råtext."""

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return ""

        return " ".join(lines[0].split())
