"""Testa fluxos reais de cadastro, busca, filtros e recebimento na interface Qt."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import tempfile
import unittest
from datetime import date
from unittest.mock import patch

from academia.qt import QCoreApplication, QEvent, QLocale, QTimer, Qt
from academia.qt import qt_test
QTest = qt_test()
from academia.qt import QApplication, QDialog, QLabel, QPushButton, QTableWidget

from academia.storage import Store
from academia.demo import seed_demo
from academia.theme import apply_theme
from academia.ui import MainWindow, MemberDialog, PaymentDialog, MemberProfile

TODAY = date(2026, 10, 14)


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        QLocale.setDefault(QLocale("pt_BR"))
        apply_theme(cls.app)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(self.tmp.name)
        self.window = MainWindow(self.store, today_provider=lambda: TODAY)
        self.window.show()
        self.pump()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.pump()
        self.store.close()
        self.tmp.cleanup()

    def pump(self):
        self.app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.app.processEvents()

    def add(self, name="José de Exemplo", due_day=14):
        return self.store.save_member(dict(name=name, phone="(11) 90000-0000", address="Rua A",
            joined_on="2026-10-01", due_day=due_day, monthly_cents=15000,
            first_month="2026-10-01", notes=""), TODAY)

    def test_registration_validation_then_save_and_search(self):
        dialog = MemberDialog(self.store, TODAY, self.window)
        dialog.show()
        QTest.mouseClick(dialog.save_button, Qt.LeftButton)
        self.assertTrue(dialog.message.isVisible())
        self.assertFalse(self.store.members())
        dialog.name.setText("José de Exemplo")
        dialog.amount.setText("160,50")
        QTest.mouseClick(dialog.save_button, Qt.LeftButton)
        self.assertEqual(dialog.result(), QDialog.Accepted)
        self.assertEqual(self.store.members()[0]["monthly_cents"], 16050)
        self.window.open_page("members")
        self.window.search_members.setText("JOSE")
        self.pump()
        table = self.window.findChild(QTableWidget, "membersTable")
        self.assertEqual(table.rowCount(), 1)
        self.assertEqual(table.item(0, 0).text(), "José de Exemplo")
        dialog.deleteLater()

    def test_filters_and_payment_through_modal(self):
        self.add("Aluno atrasado", 10)
        self.add("Aluno de hoje", 14)
        self.add("Aluno da semana", 21)
        self.window.refresh()
        QTest.mouseClick(self.window.nav["invoices"], Qt.LeftButton)
        self.pump()
        for state in ("late", "today", "soon"):
            QTest.mouseClick(self.window.filter_buttons[state], Qt.LeftButton)
            self.pump()
            table = self.window.invoice_results.findChild(QTableWidget)
            self.assertEqual(table.rowCount(), 1)
        QTest.mouseClick(self.window.filter_buttons["today"], Qt.LeftButton)
        self.pump()
        table = self.window.invoice_results.findChild(QTableWidget)
        receive = table.cellWidget(0, 4).findChild(QPushButton)
        def accept_payment():
            modal = self.app.activeModalWidget()
            if isinstance(modal, PaymentDialog):
                modal.method.setCurrentText("Dinheiro")
                modal.accept()
        QTimer.singleShot(10, accept_payment)
        QTest.mouseClick(receive, Qt.LeftButton)
        self.pump()
        self.assertEqual(len(self.store.invoices(TODAY, "paid")), 1)
        self.assertEqual(self.store.summary(TODAY)["received"], 15000)
        self.assertFalse(self.store.invoices(TODAY, "today"))
        QTest.mouseClick(self.window.filter_buttons["paid"], Qt.LeftButton)
        self.pump()
        self.assertEqual(self.window.invoice_results.findChild(QTableWidget).rowCount(), 1)

    def test_profile_deactivate_and_delete_have_working_controls(self):
        mid = self.add()
        profile = MemberProfile(self.window, mid)
        profile.show()
        with patch("academia.ui.confirm", return_value=True):
            profile.toggle()
        self.assertFalse(self.store.member(mid)["active"])
        with patch("academia.ui.confirm", return_value=True):
            profile.toggle()
        self.assertTrue(self.store.member(mid)["active"])
        with patch("academia.ui.confirm", return_value=True):
            profile.delete()
        self.assertFalse(self.store.members())
        self.assertTrue(list((self.store.directory / "backups").glob("antes-de-excluir-*.sqlite3")))
        profile.deleteLater()

    def test_dashboard_fits_small_window_and_navigation_does_not_overlap(self):
        self.window.resize(1024, 700)
        self.pump()
        self.assertEqual(self.window.cards_layout.rowCount(), 2)
        self.assertTrue(self.window.cards[0].geometry().bottom() < self.window.cards[2].geometry().top())
        self.window.open_page("members")
        self.pump()
        self.assertEqual(self.window.page, "members")
        self.assertFalse(self.window.nav["home"].isChecked())
        self.assertTrue(self.window.nav["members"].isChecked())

    def test_midnight_updates_due_status_while_open(self):
        self.add(due_day=14)
        self.assertEqual(len(self.store.invoices(TODAY, "today")), 1)
        self.window.today_provider = lambda: date(2026, 10, 15)
        self.window.check_day()
        self.assertEqual(self.window.today, date(2026, 10, 15))
        self.assertEqual(self.store.summary(self.window.today)["late_count"], 1)

    def test_theme_switch_preserves_current_filter_and_remembers_choice(self):
        self.add()
        self.window.open_page("invoices")
        self.window.search_invoices.setText("JOSE")
        self.window.set_invoice_filter("today")
        self.pump()
        before = self.store.invoices(TODAY, "all")
        QTest.mouseClick(self.window.theme_buttons["dark"], Qt.LeftButton)
        self.pump()
        self.assertEqual(self.app.property("themeMode"), "dark")
        self.assertEqual(self.window.search_invoices.text(), "JOSE")
        self.assertEqual(self.window.invoice_filter, "today")
        self.assertEqual(self.store.invoices(TODAY, "all"), before)
        self.assertTrue(self.window.theme_buttons["dark"].isChecked())
        self.assertFalse(self.window.theme_buttons["light"].isChecked())
        theme_top = self.window.theme_buttons["dark"].mapTo(self.window, self.window.theme_buttons["dark"].rect().topLeft()).y()
        data_bottom = self.window.nav["data"].mapTo(self.window, self.window.nav["data"].rect().bottomLeft()).y()
        self.assertGreater(theme_top, data_bottom)
        self.window.close()
        self.window.deleteLater()
        self.pump()
        self.window = MainWindow(self.store, today_provider=lambda: TODAY)
        self.window.show()
        self.pump()
        self.assertEqual(self.window.theme_mode, "dark")
        QTest.mouseClick(self.window.theme_buttons["light"], Qt.LeftButton)
        self.pump()
        self.assertEqual(self.app.property("themeMode"), "light")
        self.assertEqual(self.window.settings.value("aparencia/tema"), "light")

    def test_preview_uses_power_branding_without_demo_banners(self):
        seed_demo(self.store, TODAY)
        preview = MainWindow(self.store, demo=True, today_provider=lambda: TODAY)
        preview.show()
        self.pump()
        self.assertEqual(preview.windowTitle(), "Power Academia")
        self.assertEqual(preview.findChild(QLabel, "BrandTitle").text(), "POWER")
        self.assertFalse(preview.statusBar().isVisible())
        for page in ("home", "members", "invoices", "data"):
            preview.open_page(page)
            self.pump()
            texts = " ".join(item.text().casefold() for item in preview.findChildren(QLabel))
            self.assertNotIn("demonstração", texts)
            self.assertNotIn("douglas coach", texts)
            self.assertNotIn("douglas academia", texts)
        self.assertTrue(all(not row["notes"] for row in self.store.members()))
        preview.close()
        preview.deleteLater()


if __name__ == "__main__":
    unittest.main()
