from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Optimal")
        self.resize(1100, 750)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        title = QLabel("Optimal")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        company = QLabel("Företag")

        self.company_input = QLineEdit()
        self.company_input.setPlaceholderText("Skriv företagsnamn...")

        self.capture_button = QPushButton("Capture")

        status = QLabel("Status")

        self.status_box = QTextEdit()
        self.status_box.setReadOnly(True)
        self.status_box.setText("Redo.")

        layout.addWidget(title)
        layout.addWidget(company)
        layout.addWidget(self.company_input)
        layout.addWidget(self.capture_button)
        layout.addWidget(status)
        layout.addWidget(self.status_box)