from __future__ import annotations


def build_stylesheet() -> str:
    return """
    QWidget#mainWindow {
        background-color: #0b1220;
        color: #e5eefc;
        font-family: "Segoe UI";
        font-size: 10.5pt;
    }

    QFrame[card="true"] {
        background-color: #111a2c;
        border: 1px solid #22304a;
        border-radius: 18px;
    }

    QLabel#titleLabel {
        font-size: 24px;
        font-weight: 700;
        color: #f4f7fb;
    }

    QLabel#subtitleLabel {
        color: #94a3b8;
        font-size: 10.5pt;
    }

    QLabel#sectionLabel {
        font-size: 11pt;
        font-weight: 600;
        color: #d7e2f2;
    }

    QLabel#statusValue {
        padding: 6px 10px;
        border-radius: 999px;
        background-color: #18253a;
        border: 1px solid #263654;
        color: #dbeafe;
    }

    QLabel#resultValue {
        padding: 8px 12px;
        border-radius: 10px;
        background-color: #0f1728;
        border: 1px solid #24324a;
        color: #f8fafc;
    }

    QLabel#resultPathValue {
        color: #a7b4c9;
    }

    QLineEdit,
    QComboBox {
        background-color: #0f1728;
        color: #f8fafc;
        border: 1px solid #2a3954;
        border-radius: 12px;
        padding: 10px 12px;
        selection-background-color: #2563eb;
        selection-color: white;
    }

    QComboBox::drop-down {
        border: none;
        width: 28px;
    }

    QComboBox QAbstractItemView {
        background-color: #0f1728;
        color: #f8fafc;
        selection-background-color: #2563eb;
        border: 1px solid #2a3954;
        outline: 0;
    }

    QListWidget,
    QTextEdit {
        background-color: #0f1728;
        color: #e5eefc;
        border: 1px solid #2a3954;
        border-radius: 14px;
        padding: 10px;
        selection-background-color: #2563eb;
        selection-color: white;
    }

    QListWidget::item {
        padding: 8px 10px;
        border-radius: 8px;
    }

    QListWidget::item:selected {
        background-color: #1d4ed8;
    }

    QPushButton {
        border-radius: 12px;
        padding: 10px 16px;
        border: 1px solid #30415f;
        background-color: #18253a;
        color: #f4f7fb;
        font-weight: 600;
    }

    QPushButton:hover {
        background-color: #22314b;
    }

    QPushButton:pressed {
        background-color: #0f1728;
    }

    QPushButton:disabled {
        color: #6b7280;
        background-color: #101826;
        border-color: #1f2a3b;
    }

    QPushButton#primaryAction {
        background-color: #2563eb;
        border: 1px solid #3b82f6;
        font-size: 11pt;
        padding: 12px 18px;
    }

    QPushButton#primaryAction:hover {
        background-color: #1d4ed8;
    }

    QPushButton#successAction {
        background-color: #0f7b55;
        border: 1px solid #18a36f;
    }

    QPushButton#successAction:hover {
        background-color: #0c6848;
    }

    QPushButton#dangerAction {
        background-color: #7f1d1d;
        border: 1px solid #b91c1c;
    }

    QPushButton#dangerAction:hover {
        background-color: #991b1b;
    }

    QProgressBar {
        background-color: #0f1728;
        border: 1px solid #2a3954;
        border-radius: 10px;
        text-align: center;
        color: #e5eefc;
        height: 20px;
    }

    QProgressBar::chunk {
        border-radius: 10px;
        background-color: #2563eb;
    }
    """
