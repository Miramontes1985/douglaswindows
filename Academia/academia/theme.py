"""Temas claro e escuro da Power Academia."""
from pathlib import Path
import sys

from .qt import Qt
from .qt import QIcon, QPixmap, QPainter, QColor, QFont, QPalette
from .qt import QSvgRenderer
from .qt import QApplication, QLabel, QPushButton

ASSETS = Path(__file__).resolve().parent.parent / "assets"

PATHS = {
    "home": '<path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z"/>',
    "users": '<circle cx="9" cy="8" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 5a3 3 0 0 1 0 6M21 21v-3a6 6 0 0 0-4-5"/>',
    "wallet": '<rect x="3" y="5" width="18" height="15" rx="3"/><path d="M3 8V5a2 2 0 0 1 2-2h12M16 11h5v5h-5a2 2 0 0 1 0-5Z"/>',
    "backup": '<path d="M3 7h6l2 2h10v11H3ZM3 7V4h7l2 3h7M12 17v-5m-3 3 3-3 3 3"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "search": '<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/>',
    "check": '<path d="m5 12 4 4L19 6"/>',
    "arrow": '<path d="M5 12h14m-5-5 5 5-5 5"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18M8 15h2M14 15h2"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "alert": '<path d="m12 3 10 18H2Z M12 9v5m0 3v.1"/>',
    "export": '<path d="M12 3v12m-4-4 4 4 4-4M4 15v6h16v-6"/>',
    "edit": '<path d="m15 4 5 5M4 20l5-1L21 7l-5-5L4 14Z"/>',
    "refresh": '<path d="M21 4v6h-6M3 20v-6h6M20 10A8 8 0 0 0 6 6l-3 4m1 4a8 8 0 0 0 14 4l3-4"/>',
    "help": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 4 2c-1.5.8-1.5 1.5-1.5 3m0 3v.1"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/>',
    "moon": '<path d="M20.5 13.1A8.8 8.8 0 0 1 10.9 3.5a9 9 0 1 0 9.6 9.6Z"/>',
}

THEMES = {
    "light": {
        "bg": "#f5f3f2", "surface": "#ffffff", "surface_muted": "#faf8f6",
        "text": "#231f1d", "title": "#211b18", "muted": "#706a66", "line": "#e6dfdb",
        "input_line": "#dcd1cb", "hover": "#faf4f0", "hover_line": "#baaba3", "pressed": "#efdfd7",
        "disabled": "#a59c96", "disabled_bg": "#f2eeeb", "placeholder": "#8d8077",
        "primary": "#d91b24", "primary_hover": "#b7151e", "primary_pressed": "#a80f16",
        "accent": "#b71921", "accent_bg": "#fff0ed", "accent_line": "#f0d0c9", "focus": "#bf332f",
        "danger": "#a31218", "danger_bg": "#fff0ee", "danger_line": "#edc4c4", "danger_hover": "#ffe6e3",
        "warning": "#855400", "warning_bg": "#fff4d8", "soon": "#825b20", "soon_bg": "#fff6e5",
        "success": "#246344", "success_bg": "#eaf5ed", "success_line": "#d2e7db", "success_hover": "#dbeee2",
        "neutral": "#62564f", "neutral_bg": "#f1eeeb", "metric": "#2d2622", "icon": "#89776b",
        "eyebrow": "#8d5149", "welcome": "#fff9f5", "welcome_line": "#ead7cb", "welcome_text": "#31201a",
        "received": "#edf5ee", "received_line": "#d7e6d8", "received_text": "#28553c",
        "row_line": "#f0eae6", "selection": "#fff1eb", "header": "#7e6e64",
        "scroll": "#f0ebe7", "scroll_handle": "#c4b5ac", "tooltip": "#2a2320", "tooltip_text": "#ffffff",
        "side": "#fffdfb", "side_text": "#62564f", "side_muted": "#8a766a", "side_line": "#e6ddd5",
        "side_hover": "#f4ebe5", "side_selected": "#fff0ec", "side_selected_text": "#ab1b23", "side_selected_line": "#edccc4",
        "theme_selected": "#fff4d8", "theme_text": "#855400", "theme_line": "#ead09b",
    },
    "dark": {
        "bg": "#191716", "surface": "#25211f", "surface_muted": "#211e1c",
        "text": "#f0e8e1", "title": "#fff5ec", "muted": "#c1b1a7", "line": "#443a34",
        "input_line": "#594b43", "hover": "#352c27", "hover_line": "#7d6658", "pressed": "#49372f",
        "disabled": "#9a8b80", "disabled_bg": "#302925", "placeholder": "#ad9c90",
        "primary": "#c92430", "primary_hover": "#df3340", "primary_pressed": "#a81c27",
        "accent": "#ff8588", "accent_bg": "#412629", "accent_line": "#6e363b", "focus": "#edb36d",
        "danger": "#ff9397", "danger_bg": "#41272a", "danger_line": "#704047", "danger_hover": "#563033",
        "warning": "#f2c26f", "warning_bg": "#45371f", "soon": "#e5c18b", "soon_bg": "#3c3122",
        "success": "#a4dcba", "success_bg": "#243a2e", "success_line": "#3f6450", "success_hover": "#304e3d",
        "neutral": "#d0bfb2", "neutral_bg": "#3a312c", "metric": "#fff1e4", "icon": "#ceb197",
        "eyebrow": "#d6a581", "welcome": "#30231f", "welcome_line": "#604133", "welcome_text": "#ffe6cd",
        "received": "#243a2d", "received_line": "#3c5946", "received_text": "#b4dfbe",
        "row_line": "#3d322c", "selection": "#49332b", "header": "#cebaaa",
        "scroll": "#2b2420", "scroll_handle": "#6b5649", "tooltip": "#f5e7db", "tooltip_text": "#241c18",
        "side": "#121110", "side_text": "#d0c1b6", "side_muted": "#af998a", "side_line": "#382c24",
        "side_hover": "#2f2520", "side_selected": "#47282a", "side_selected_text": "#fff1e6", "side_selected_line": "#784349",
        "theme_selected": "#44351f", "theme_text": "#f2c26f", "theme_line": "#806134",
    },
}


def colors() -> dict:
    app = QApplication.instance()
    mode = app.property("themeMode") if app else "light"
    return THEMES.get(mode, THEMES["light"])


def icon(name: str, color: str | None = None, size: int = 22) -> QIcon:
    color = color or colors()["icon"]
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{PATHS[name]}</svg>'
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    QSvgRenderer(svg.encode()).render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return QIcon(pixmap)


def update_button_icon(widget):
    symbol = widget.property("symbol")
    if not symbol:
        return
    theme = colors()
    variant = widget.property("variant")
    color = ("#ffffff" if variant == "primary" else
             theme["side_selected_text" if widget.isChecked() else "side_text"] if variant == "nav" else
             theme["theme_text" if widget.isChecked() else "side_text"] if variant == "theme" else
             theme["success"] if variant == "receive" else theme["icon"])
    widget.setIcon(icon(symbol, color))


def refresh_icons(root):
    for widget in root.findChildren(QPushButton):
        update_button_icon(widget)
    for widget in root.findChildren(QLabel):
        if widget.property("symbol"):
            widget.setPixmap(icon(widget.property("symbol"), colors()[widget.property("iconTone")], 20).pixmap(20, 20))


def apply_theme(app, mode="light"):
    mode = mode if mode in THEMES else "light"
    theme = THEMES[mode]
    app.setProperty("themeMode", mode)
    app.setStyle("Fusion")
    font = QFont("Segoe UI" if sys.platform == "win32" else "Arial")
    font.setPixelSize(16)
    app.setFont(font)
    palette = QPalette()
    for role, key in {
        QPalette.Window: "bg", QPalette.WindowText: "text",
        QPalette.Base: "surface", QPalette.AlternateBase: "surface_muted",
        QPalette.Text: "text", QPalette.Button: "surface",
        QPalette.ButtonText: "text", QPalette.PlaceholderText: "placeholder",
        QPalette.Highlight: "primary", QPalette.HighlightedText: "tooltip_text",
        QPalette.ToolTipBase: "tooltip", QPalette.ToolTipText: "tooltip_text",
        QPalette.Link: "accent",
    }.items():
        palette.setColor(role, QColor(theme[key]))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    for role in (QPalette.Text, QPalette.ButtonText, QPalette.WindowText):
        palette.setColor(QPalette.Disabled, role, QColor(theme["disabled"]))
    app.setPalette(palette)
    style = STYLE
    for key, value in theme.items():
        style = style.replace(f"@{key}@", value)
    app.setStyleSheet(style)


STYLE = """
QWidget { color: @text@; }
QMainWindow, QDialog, #MainContent { background: @bg@; }
QLabel { background: transparent; }
QLabel[role="muted"] { color: @muted@; font-size: 14px; }
QLabel[role="eyebrow"] { color: @eyebrow@; font-size: 12px; font-weight: 700; letter-spacing: 2px; }
QLabel[role="title"] { color: @title@; font-size: 30px; font-weight: 700; }
QLabel[role="section"] { font-size: 19px; font-weight: 700; }
QLabel[role="field"] { font-size: 14px; font-weight: 600; }
QLabel[role="error"] { color: @danger@; background: @danger_bg@; border-radius: 8px; padding: 10px; }
QLabel[role="amount"] { color: @received_text@; font-size: 36px; font-weight: 700; }
#Sidebar { background: @side@; border: none; border-right: 1px solid @side_line@; }
#Sidebar QLabel { color: @side_text@; }
#Sidebar QLabel[role="muted"] { color: @side_muted@; }
#BrandTitle { color: @title@; font-size: 25px; font-weight: 700; letter-spacing: 3px; }
#BrandSub { color: @side_muted@; font-size: 12px; letter-spacing: 3px; }
#MenuCaption { color: @side_muted@; font-size: 11px; letter-spacing: 2px; }
#SideSeparator { background: @side_line@; max-height: 1px; }
QPushButton { background: @surface@; border: 1px solid @input_line@; border-radius: 9px;
    padding: 10px 16px; font-size: 15px; font-weight: 600; min-height: 22px; }
QPushButton:hover { background: @hover@; border-color: @hover_line@; }
QPushButton:pressed { background: @pressed@; }
QPushButton:focus { border: 2px solid @focus@; }
QPushButton:disabled { color: @disabled@; background: @disabled_bg@; border-color: @line@; }
QPushButton[variant="primary"] { background: @primary@; color: #ffffff; border: 1px solid @primary@; }
QPushButton[variant="primary"]:hover { background: @primary_hover@; border-color: @primary_hover@; }
QPushButton[variant="primary"]:pressed { background: @primary_pressed@; }
QPushButton[variant="danger"] { color: @danger@; border-color: @danger_line@; background: @danger_bg@; }
QPushButton[variant="danger"]:hover { background: @danger_hover@; }
QPushButton[variant="link"] { border: none; color: @accent@; background: transparent; padding: 6px; }
QPushButton[variant="link"]:hover { background: @accent_bg@; }
QPushButton[variant="nav"] { text-align: left; background: transparent; color: @side_text@;
    border: 1px solid transparent; padding: 13px 14px; font-size: 15px; font-weight: 500; }
QPushButton[variant="nav"]:hover { background: @side_hover@; color: @title@; }
QPushButton[variant="nav"]:checked { background: @side_selected@; color: @side_selected_text@; border-color: @side_selected_line@; }
QPushButton[variant="nav"]:focus { border-color: @focus@; }
QPushButton[variant="theme"] { color: @side_text@; background: transparent; border: 1px solid @side_line@; padding: 10px 8px; font-size: 14px; }
QPushButton[variant="theme"]:hover { background: @side_hover@; }
QPushButton[variant="theme"]:checked { background: @theme_selected@; color: @theme_text@; border-color: @theme_line@; }
QPushButton[variant="filter"] { background: transparent; border-color: transparent; color: @muted@;
    font-size: 14px; padding: 10px 12px; }
QPushButton[variant="filter"]:checked { color: @accent@; background: @accent_bg@; border-color: @accent_line@; }
QPushButton[variant="filter"]:hover { background: @hover@; }
QPushButton[variant="receive"] { color: @success@; background: @success_bg@; border-color: @success_line@;
    padding: 7px 11px; font-size: 14px; min-height: 20px; }
QPushButton[variant="receive"]:hover { background: @success_hover@; }
#Card, #Panel { background: @surface@; border: 1px solid @line@; border-radius: 12px; }
#Card QLabel[role="metric"] { font-size: 29px; font-weight: 700; color: @metric@; }
#Card[tone="late"] QLabel[role="metric"] { color: @danger@; }
#Card[tone="today"] QLabel[role="metric"] { color: @warning@; }
#Card QLabel[role="cardtitle"] { font-size: 14px; color: @muted@; font-weight: 600; }
#Welcome { background: @welcome@; border: 1px solid @welcome_line@; border-radius: 12px; }
#WelcomeTitle { color: @welcome_text@; font-size: 24px; font-weight: 700; }
#Received { background: @received@; border: 1px solid @received_line@; border-radius: 9px; }
#Received QLabel { color: @received_text@; }
#ReceivedTotal { font-weight: 700; font-size: 19px; }
QLineEdit, QDateEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {
    background: @surface@; border: 1px solid @input_line@; border-radius: 8px;
    padding: 9px 11px; min-height: 24px; font-size: 16px; selection-background-color: @primary@; selection-color: #ffffff; }
QLineEdit:focus, QDateEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus { border: 2px solid @focus@; }
QLineEdit:disabled, QDateEdit:disabled { background: @disabled_bg@; color: @disabled@; }
QDateEdit::drop-down, QComboBox::drop-down { width: 26px; border: none; }
QSpinBox::up-button, QSpinBox::down-button { width: 23px; }
QComboBox QAbstractItemView { background: @surface@; padding: 6px; selection-background-color: @accent_bg@; selection-color: @accent@; }
QTableWidget { background: @surface@; border: none; outline: 0; gridline-color: transparent;
    selection-background-color: @selection@; selection-color: @text@; }
QTableWidget::item { border-bottom: 1px solid @row_line@; padding: 8px 12px; }
QTableWidget::item:selected { background: @selection@; color: @text@; }
QHeaderView::section { background: @surface_muted@; color: @header@; border: none;
    border-bottom: 1px solid @line@; padding: 13px 12px; font-size: 13px; font-weight: 600; text-align: left; }
QLabel[badge] { border-radius: 6px; padding: 7px 9px; font-size: 13px; font-weight: 600; }
QLabel[badge="late"] { background: @danger_bg@; color: @danger@; }
QLabel[badge="today"] { background: @warning_bg@; color: @warning@; }
QLabel[badge="soon"] { background: @soon_bg@; color: @soon@; }
QLabel[badge="paid"], QLabel[badge="active"] { background: @success_bg@; color: @success@; }
QLabel[badge="future"], QLabel[badge="inactive"] { background: @neutral_bg@; color: @neutral@; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: @scroll@; width: 10px; border-radius: 5px; }
QScrollBar::handle:vertical { background: @scroll_handle@; min-height: 25px; border-radius: 5px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: @scroll@; height: 10px; }
QScrollBar::handle:horizontal { background: @scroll_handle@; min-width: 25px; border-radius: 5px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QStatusBar { background: @surface@; color: @muted@; border-top: 1px solid @line@; font-size: 12px; }
QToolTip { background: @tooltip@; color: @tooltip_text@; border: none; padding: 8px; }
QCalendarWidget QWidget { background: @surface@; color: @text@; }
QCalendarWidget QToolButton { background: @surface_muted@; color: @text@; border: none; padding: 8px; }
QCalendarWidget QAbstractItemView { selection-background-color: @primary@; selection-color: #ffffff; }
"""
