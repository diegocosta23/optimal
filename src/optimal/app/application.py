from PySide6.QtWidgets import QApplication

from src.optimal.ui.main_window import MainWindow


def run() -> None:
    app = QApplication([])

    window = MainWindow()
    window.show()

    app.exec()