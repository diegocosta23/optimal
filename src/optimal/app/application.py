from __future__ import annotations

from PySide6.QtWidgets import QApplication

from src.optimal.controller.main_controller import MainController
from src.optimal.ui.main_window import MainWindow
from src.optimal.ui.styles import build_stylesheet


def run() -> None:
    app = QApplication([])
    app.setApplicationName("Optimal")
    app.setOrganizationName("Optimal")
    app.setStyleSheet(build_stylesheet())

    window = MainWindow()
    controller = MainController(window)
    window.controller = controller  # type: ignore[attr-defined]

    app.aboutToQuit.connect(controller.shutdown)

    window.show()

    app.exec()
