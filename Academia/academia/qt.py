"""API compartilhada: Qt 6 no pacote x64 e Qt 5 no pacote x86."""
from __future__ import annotations

import importlib
import os
import struct
import sys

BINDING = os.environ.get("POWER_ACADEMIA_QT_BINDING")
if BINDING is None:
    BINDING = "PySide2" if sys.platform == "win32" and struct.calcsize("P") == 4 else "PySide6"
if BINDING not in ("PySide2", "PySide6"):
    raise ValueError("Biblioteca de interface inválida.")

QtCore = importlib.import_module(BINDING + ".QtCore")
QtGui = importlib.import_module(BINDING + ".QtGui")
QtWidgets = importlib.import_module(BINDING + ".QtWidgets")
QtSvg = importlib.import_module(BINDING + ".QtSvg")

for module, names in [
    (QtCore, "Qt QDate QTimer QSize QSettings QUrl QLocale QLockFile QCoreApplication QEvent"),
    (QtGui, "QIcon QPixmap QDesktopServices QPainter QColor QFont QPalette"),
    (QtSvg, "QSvgRenderer"),
    (QtWidgets, "QAbstractItemView QApplication QButtonGroup QComboBox QDateEdit QDialog QFrame QGridLayout QHBoxLayout QHeaderView QLabel QLineEdit QMainWindow QMessageBox QPushButton QScrollArea QSpinBox QTableWidget QTableWidgetItem QTextEdit QVBoxLayout QWidget QFileDialog"),
]:
    for name in names.split():
        globals()[name] = getattr(module, name)


def exec_qt(widget):
    """Qt 5 usa exec_; Qt 6 usa exec."""
    method = getattr(widget, "exec", None) or widget.exec_
    return method()


def qt_test():
    return importlib.import_module(BINDING + ".QtTest").QTest
