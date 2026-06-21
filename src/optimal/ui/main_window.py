from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QProgressBar,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    capture_requested = Signal()
    search_text_changed = Signal(str)
    company_selected = Signal(str)
    copy_zip_requested = Signal()
    open_folder_requested = Signal()
    clear_requested = Signal()

    def __init__(self) -> None:
        super().__init__()

        self._zip_filename = ""
        self._zip_path = ""

        self.setObjectName("mainWindow")
        self.setWindowTitle("Optimal")
        self.resize(1220, 860)
        self.setMinimumSize(1100, 760)

        self._build_ui()
        self._connect_signals()

        self.set_company_results([])
        self.set_result(None, None)
        self.set_status("Redo")
        self.append_log("Optimal startad.")

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(22, 22, 22, 22)
        main_layout.setSpacing(16)

        header_card = self._create_card()
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(18, 18, 18, 18)
        header_layout.setSpacing(6)

        title = QLabel("Optimal")
        title.setObjectName("titleLabel")
        subtitle = QLabel("TradingView → screenshots → ZIP → ChatGPT")
        subtitle.setObjectName("subtitleLabel")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        search_card = self._create_card()
        search_layout = QVBoxLayout(search_card)
        search_layout.setContentsMargins(18, 18, 18, 18)
        search_layout.setSpacing(12)

        search_title = QLabel("Företag")
        search_title.setObjectName("sectionLabel")

        self.company_input = QComboBox()
        self.company_input.setEditable(True)
        self.company_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.company_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        line_edit = self.company_input.lineEdit()
        if line_edit is not None:
            line_edit.setPlaceholderText("Skriv företagsnamn...")
            line_edit.textEdited.connect(self.search_text_changed.emit)
            line_edit.returnPressed.connect(self._emit_selected_company)

        self.results_hint = QLabel("Skriv ett företagsnamn för att se träffar från TradingView.")
        self.results_hint.setObjectName("subtitleLabel")

        self.company_results = QListWidget()
        self.company_results.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.company_results.setMinimumHeight(150)
        self.company_results.itemClicked.connect(self._handle_result_clicked)
        self.company_results.hide()

        search_layout.addWidget(search_title)
        search_layout.addWidget(self.company_input)
        search_layout.addWidget(self.results_hint)
        search_layout.addWidget(self.company_results)

        action_row = QHBoxLayout()
        action_row.setSpacing(12)

        self.capture_button = QPushButton("📸 Capture")
        self.capture_button.setObjectName("primaryAction")
        self.capture_button.setMinimumHeight(46)
        self.capture_button.clicked.connect(self.capture_requested.emit)

        self.capture_note = QLabel("Programmet tar 1W, 1D, 4H och 45M när allt är klart.")
        self.capture_note.setObjectName("subtitleLabel")
        self.capture_note.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        action_row.addWidget(self.capture_button, 0)
        action_row.addWidget(self.capture_note, 1)

        result_card = self._create_card()
        result_layout = QVBoxLayout(result_card)
        result_layout.setContentsMargins(18, 18, 18, 18)
        result_layout.setSpacing(12)

        result_title = QLabel("Resultat")
        result_title.setObjectName("sectionLabel")

        self.result_value = QLabel("Ingen ZIP skapad ännu.")
        self.result_value.setObjectName("resultValue")
        self.result_value.setWordWrap(True)

        self.result_path_value = QLabel("Sparad plats visas här när ZIP är klar.")
        self.result_path_value.setObjectName("resultPathValue")
        self.result_path_value.setWordWrap(True)

        result_buttons = QHBoxLayout()
        result_buttons.setSpacing(10)

        self.copy_zip_button = QPushButton("📋 Kopiera ZIP")
        self.copy_zip_button.setObjectName("successAction")
        self.copy_zip_button.setEnabled(False)
        self.copy_zip_button.clicked.connect(self.copy_zip_requested.emit)

        self.open_folder_button = QPushButton("📂 Öppna mapp")
        self.open_folder_button.setEnabled(False)
        self.open_folder_button.clicked.connect(self.open_folder_requested.emit)

        self.clear_button = QPushButton("🗑 Rensa")
        self.clear_button.setObjectName("dangerAction")
        self.clear_button.setEnabled(False)
        self.clear_button.clicked.connect(self.clear_requested.emit)

        result_buttons.addWidget(self.copy_zip_button)
        result_buttons.addWidget(self.open_folder_button)
        result_buttons.addWidget(self.clear_button)

        result_layout.addWidget(result_title)
        result_layout.addWidget(self.result_value)
        result_layout.addWidget(self.result_path_value)
        result_layout.addLayout(result_buttons)

        status_card = self._create_card()
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(18, 18, 18, 18)
        status_layout.setSpacing(10)

        status_title = QLabel("Status")
        status_title.setObjectName("sectionLabel")

        status_row = QHBoxLayout()
        status_row.setSpacing(12)

        self.status_value = QLabel("Redo")
        self.status_value.setObjectName("statusValue")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        status_row.addWidget(self.status_value, 0)
        status_row.addWidget(self.progress_bar, 1)

        status_layout.addWidget(status_title)
        status_layout.addLayout(status_row)

        log_card = self._create_card()
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(18, 18, 18, 18)
        log_layout.setSpacing(10)

        log_title = QLabel("Logg")
        log_title.setObjectName("sectionLabel")

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(180)

        log_layout.addWidget(log_title)
        log_layout.addWidget(self.log_box)

        main_layout.addWidget(header_card)
        main_layout.addWidget(search_card)
        main_layout.addLayout(action_row)
        main_layout.addWidget(result_card)
        main_layout.addWidget(status_card)
        main_layout.addWidget(log_card, 1)

    def _create_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("card", True)
        return card

    def _connect_signals(self) -> None:
        line_edit = self.company_input.lineEdit()
        if line_edit is not None:
            line_edit.textChanged.connect(self.search_text_changed.emit)

    def _emit_selected_company(self) -> None:
        company = self.current_company_text()
        if company:
            self.company_selected.emit(company)

    def _handle_result_clicked(self, item: QListWidgetItem) -> None:
        company = item.text().strip()
        if company:
            self.set_company_text(company)
            self.company_selected.emit(company)

    def set_company_text(self, text: str) -> None:
        line_edit = self.company_input.lineEdit()
        if line_edit is None:
            self.company_input.setCurrentText(text)
            return

        previous = line_edit.blockSignals(True)
        try:
            self.company_input.setCurrentText(text)
        finally:
            line_edit.blockSignals(previous)

    def current_company_text(self) -> str:
        return self.company_input.currentText().strip()

    def set_company_results(self, results: list[str]) -> None:
        self.company_results.clear()

        if not results:
            self.company_results.hide()
            self.results_hint.setText("Inga träffar ännu. Skriv ett företagsnamn för att söka.")
            self.results_hint.show()
            return

        for result in results:
            self.company_results.addItem(QListWidgetItem(result))

        self.results_hint.hide()
        self.company_results.show()

    def set_result(self, filename: str | None, path: str | None) -> None:
        if not filename or not path:
            self._zip_filename = ""
            self._zip_path = ""
            self.result_value.setText("Ingen ZIP skapad ännu.")
            self.result_path_value.setText("Sparad plats visas här när ZIP är klar.")
            self.copy_zip_button.setEnabled(False)
            self.open_folder_button.setEnabled(False)
            self.clear_button.setEnabled(False)
            return

        self._zip_filename = filename
        self._zip_path = path
        self.result_value.setText(f"✔ {filename}")
        self.result_path_value.setText(f"Sparad i: {path}")
        self.copy_zip_button.setEnabled(True)
        self.open_folder_button.setEnabled(True)
        self.clear_button.setEnabled(True)

    def set_status(self, text: str) -> None:
        self.status_value.setText(text)

    def set_busy(self, busy: bool) -> None:
        self.capture_button.setEnabled(not busy)
        self.company_input.setEnabled(not busy)
        self.company_results.setEnabled(not busy)

        if busy:
            self.capture_button.setText("Arbetar...")
            self.progress_bar.setRange(0, 0)
        else:
            self.capture_button.setText("📸 Capture")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)

    def set_progress(self, value: int) -> None:
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(max(0, min(100, value)))

    def append_log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_box.append(f"{timestamp}  {message}")
        self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())

    def clear_log(self) -> None:
        self.log_box.clear()

    def show_error(self, message: str) -> None:
        self.set_status(message)
        self.append_log(f"❌ {message}")

    def show_success(self, message: str) -> None:
        self.set_status(message)
        self.append_log(f"✅ {message}")

    def selected_zip_path(self) -> str:
        return self._zip_path

    def selected_zip_filename(self) -> str:
        return self._zip_filename
