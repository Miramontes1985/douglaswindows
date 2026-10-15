"""Captura a interface real nos dois temas, usando somente dados fictícios."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import sys
import tempfile
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from academia.qt import QCoreApplication, QEvent, QLocale
from academia.qt import QApplication
from academia.storage import Store
from academia.demo import seed_demo
from academia.theme import apply_theme
from academia.ui import MainWindow, MemberDialog, PaymentDialog, MemberProfile

app = QApplication([])
QLocale.setDefault(QLocale("pt_BR"))
apply_theme(app)
today = date(2026, 10, 14)
folder = Path(__file__).resolve().parents[1] / "docs" / "previas"
folder.mkdir(parents=True, exist_ok=True)


def settle():
    app.processEvents()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    app.processEvents()


with tempfile.TemporaryDirectory(prefix="power-academia-preview-") as tmp:
    store = Store(tmp)
    seed_demo(store, today)
    window = MainWindow(store, demo=True, today_provider=lambda: today)
    window.resize(1360, 940)
    window.show()
    for theme, suffix in [("light", ""), ("dark", "-escuro")]:
        window.set_theme(theme)
        for page, name in [("home", "visao-geral"), ("members", "alunos"),
                           ("invoices", "mensalidades"), ("data", "backup")]:
            window.open_page(page)
            settle()
            window.scroller.verticalScrollBar().setValue(0)
            settle()
            window.grab().save(str(folder / f"{name}{suffix}.png"))
        for name, dialog in [
            ("cadastro", MemberDialog(store, today, window)),
            ("recebimento", PaymentDialog(store.invoices(today)[0], today, window)),
            ("ficha", MemberProfile(window, store.members()[0]["id"])),
        ]:
            dialog.show()
            settle()
            dialog.grab().save(str(folder / f"{name}{suffix}.png"))
            dialog.close()
            dialog.deleteLater()
            settle()
    window.close()
    store.close()
print(folder)
