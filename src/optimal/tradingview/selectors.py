from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from playwright.sync_api import Locator, Page


@dataclass(frozen=True, slots=True)
class TradingViewSelectors:
    """Samlar alla TradingView-selectorer på ett ställe."""

    search_button_selectors: tuple[str, ...] = (
        "[aria-label*='Search' i]",
        "[aria-label*='Symbol' i]",
        "button[title*='Search' i]",
        "button[data-name*='search' i]",
        "button:has-text('Search')",
        "button:has-text('Symbol')",
    )
    search_input_selectors: tuple[str, ...] = (
        "input[placeholder*='Search' i]",
        "input[aria-label*='Search' i]",
        "[role='textbox']",
        "input[type='text']",
        "textarea",
    )
    result_row_selectors: tuple[str, ...] = (
        "[data-name='symbol-item']",
        "[data-name*='search-result' i]",
        "[role='option']",
        "li",
        "tr",
    )

    def first_visible(self, page: Page, selectors: Iterable[str]) -> Locator | None:
        """Returnerar första synliga locatorn från en uppsättning CSS-selectorer."""

        for selector in selectors:
            locator = page.locator(selector)
            try:
                if locator.count() > 0 and locator.first.is_visible():
                    return locator.first
            except Exception:  # noqa: BLE001
                continue

        return None
