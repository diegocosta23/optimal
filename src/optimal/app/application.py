from __future__ import annotations

from PySide6.QtWidgets import QApplication

from src.optimal.ui.main_window import MainWindow
from src.optimal.ui.styles import build_stylesheet


def run() -> None:
    app = QApplication([])
    app.setApplicationName("Optimal")
    app.setOrganizationName("Optimal")
    app.setStyleSheet(build_stylesheet())

    window = MainWindow()
    window.show()

    app.exec()
