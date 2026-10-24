"""
Merkezi Modern Koyu Tema (QSS) ve Renk Paleti
Kullanıcının beğendiği görsel kimlik (#1e1f26, #262b33, #00a8ff, Segoe UI)
tüm pencereler ve diyaloglar için tek bir yerden yönetilir.
"""

DARK_THEME_QSS = """
/* Genel Pencere ve Zemin */
QMainWindow, QDialog {
    background-color: #1e1f26;
    color: #ffffff;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
}

QWidget {
    color: #f1f2f6;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
    outline: none;
}

/* Paneller ve Kartlar */
QFrame#cardFrame, QFrame#sidebarFrame, QFrame#filterFrame {
    background-color: #262b33;
    border-radius: 12px;
    border: 1px solid #333945;
}

/* Başlıklar ve Etiketler */
QLabel {
    color: #dcdde1;
    font-weight: 500;
}

QLabel#headerTitle {
    color: #00a8ff;
    font-size: 16pt;
    font-weight: bold;
}

QLabel#statValue {
    color: #ffffff;
    font-size: 18pt;
    font-weight: bold;
}

QLabel#statLabel {
    color: #a4b0be;
    font-size: 9pt;
    font-weight: 600;
    text-transform: uppercase;
}

/* Metin Giriş Kutuları */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #2f3640;
    border: 1.5px solid #3d4451;
    border-radius: 6px;
    padding: 3px 8px;
    color: #ffffff;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
    min-height: 26px;
    selection-background-color: #00a8ff;
}

QSpinBox, QDoubleSpinBox, QDateEdit {
    background-color: #2f3640;
    border: 1.5px solid #3d4451;
    border-radius: 6px;
    padding: 2px 6px;
    color: #ffffff;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
    min-height: 26px;
    selection-background-color: #00a8ff;
}

QSpinBox::up-button, QDoubleSpinBox::up-button, QDateEdit::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #3d4451;
}

QSpinBox::down-button, QDoubleSpinBox::down-button, QDateEdit::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 20px;
    border-left: 1px solid #3d4451;
}

QSpinBox QLineEdit, QDoubleSpinBox QLineEdit, QDateEdit QLineEdit {
    padding: 0px 4px;
    border: none;
    background: transparent;
    min-height: 20px;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QComboBox:focus, QTextEdit:focus {
    border: 1.5px solid #00a8ff;
    background-color: #353b48;
}

QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDateEdit:disabled {
    background-color: #23272e;
    color: #718093;
    border-color: #2f3640;
}

/* Açılır Menü (ComboBox) */
QComboBox {
    background-color: #2f3640;
    border: 1.5px solid #3d4451;
    border-radius: 6px;
    padding: 3px 8px;
    color: #ffffff;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
    min-height: 26px;
    min-width: 120px;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left: none;
}

QComboBox QAbstractItemView {
    background-color: #262b33;
    color: #ffffff;
    border: 1px solid #00a8ff;
    border-radius: 6px;
    selection-background-color: #00a8ff;
    selection-color: #ffffff;
    padding: 4px;
}

/* Butonlar */
QPushButton {
    background-color: #00a8ff;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 5px 12px;
    font-weight: bold;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
    min-height: 26px;
}

QPushButton:hover {
    background-color: #0097e6;
}

QPushButton:pressed {
    background-color: #0084c7;
}

QPushButton:disabled {
    background-color: #383e4a;
    color: #718093;
}

QPushButton#btnSuccess {
    background-color: #2ecc71;
}
QPushButton#btnSuccess:hover {
    background-color: #27ae60;
}

QPushButton#btnDanger {
    background-color: #e74c3c;
}
QPushButton#btnDanger:hover {
    background-color: #c0392b;
}

QPushButton#btnWarning {
    background-color: #f39c12;
}
QPushButton#btnWarning:hover {
    background-color: #d68910;
}

QPushButton#btnSecondary {
    background-color: #3d4451;
    color: #dcdde1;
}
QPushButton#btnSecondary:hover {
    background-color: #4b5464;
}

/* Tablolar (QTableWidget & QTableView) */
QTableWidget, QTableView {
    background-color: #262b33;
    border: 1px solid #333945;
    border-radius: 8px;
    gridline-color: #2f3640;
    color: #f5f6fa;
    selection-background-color: #00a8ff;
    selection-color: #ffffff;
    outline: none;
}

QTableWidget::item, QTableView::item {
    padding: 8px;
    border-bottom: 1px solid #2d333e;
}

QTableWidget::item:selected, QTableView::item:selected {
    background-color: #0984e3;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #1f232a;
    color: #00a8ff;
    padding: 6px 8px;
    font-weight: bold;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
    min-height: 26px;
    border: none;
    border-right: 1px solid #2d333e;
    border-bottom: 2px solid #00a8ff;
}

/* Kaydırma Çubuğu (QScrollBar) */
QScrollBar:vertical {
    background-color: #1e1f26;
    width: 10px;
    margin: 0px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #3d4451;
    min-height: 25px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background-color: #00a8ff;
}

QScrollBar:horizontal {
    background-color: #1e1f26;
    height: 10px;
    margin: 0px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #3d4451;
    min-width: 25px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #00a8ff;
}

QScrollBar::add-line, QScrollBar::sub-line {
    width: 0px;
    height: 0px;
}

/* Sekmeler (QTabWidget) */
QTabWidget::pane {
    border: 1px solid #333945;
    background-color: #262b33;
    border-radius: 8px;
}

QTabBar::tab {
    background-color: #1f232a;
    color: #a4b0be;
    padding: 8px 18px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #262b33;
    color: #00a8ff;
    font-weight: bold;
    border-bottom: 2px solid #00a8ff;
}

/* Durum Çubuğu (QStatusBar) */
QStatusBar {
    background-color: #1a1b21;
    color: #a4b0be;
    border-top: 1px solid #2f3640;
}
"""


def apply_theme(app_or_widget):
    """Uygulama veya pencere düzeyinde temayı uygular."""
    app_or_widget.setStyleSheet(DARK_THEME_QSS)
