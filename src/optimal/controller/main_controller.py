from __future__ import annotations

from PySide6.QtCore import QObject, QTimer

from src.optimal.tradingview.browser import BrowserManager
from src.optimal.tradingview.search import SearchManager
from src.optimal.ui.main_window import MainWindow


class MainController(QObject):
    """Kopplar GUI:t mot TradingView-arbetsflödet."""

    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)

        self.window = window
        self.browser = BrowserManager()
        self.search = SearchManager(self.browser)
        self._latest_query = ""

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._perform_search)

        self._connect_signals()

    def _connect_signals(self) -> None:
        self.window.search_text_changed.connect(self._on_search_text_changed)
        self.window.company_selected.connect(self._on_company_selected)
        self.window.capture_requested.connect(self._on_capture_requested)
        self.window.copy_zip_requested.connect(self._on_copy_zip_requested)
        self.window.open_folder_requested.connect(self._on_open_folder_requested)
        self.window.clear_requested.connect(self._on_clear_requested)

    def _on_search_text_changed(self, text: str) -> None:
        self._latest_query = text.strip()

        if len(self._latest_query) < 2:
            self._search_timer.stop()
            self.window.set_company_results([])
            self.window.set_status("Redo")
            return

        self.window.set_status(f"Söker: {self._latest_query}")
        self._search_timer.start()

    def _perform_search(self) -> None:
        query = self._latest_query.strip()
        if len(query) < 2:
            return

        try:
            results = self.search.search_company(query)
            names = [result.name for result in results]
            self.window.set_company_results(names)

            if names:
                self.window.set_status(f"{len(names)} träffar")
                self.window.append_log(f"Sökning klar: {query} ({len(names)} träffar)")
            else:
                self.window.set_status("Inga träffar")
                self.window.append_log(f"Sökning klar: {query} (inga träffar)")
        except Exception as exc:  # noqa: BLE001
            self.window.set_company_results([])
            self.window.show_error(str(exc))

    def _on_company_selected(self, company: str) -> None:
        company = company.strip()
        if not company:
            return

        try:
            self.window.set_status(f"Väljer: {company}")
            self.search.select_result(company)
            self.window.append_log(f"Valde: {company}")
            self.window.show_success(f"Vald: {company}")
        except Exception as exc:  # noqa: BLE001
            self.window.show_error(str(exc))

    def _on_capture_requested(self) -> None:
        self.window.show_error("Capture byggs i nästa steg.")

    def _on_copy_zip_requested(self) -> None:
        self.window.show_error("Kopiera ZIP byggs i nästa steg.")

    def _on_open_folder_requested(self) -> None:
        self.window.show_error("Öppna mapp byggs i nästa steg.")

    def _on_clear_requested(self) -> None:
        self._latest_query = ""
        self._search_timer.stop()
        self.window.set_company_text("")
        self.window.set_company_results([])
        self.window.set_result(None, None)
        self.window.clear_log()
        self.window.set_status("Redo")
        self.window.append_log("Rensat.")

    def shutdown(self) -> None:
        """Stäng externa anslutningar snyggt när appen avslutas."""

        self.browser.close()
