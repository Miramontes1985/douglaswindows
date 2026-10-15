import csv
import sqlite3
from contextlib import closing
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from academia.storage import (
    APP_ID, Store, due_date, invoice_status, money, parse_money,
)

TODAY = date(2026, 10, 14)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(self.tmp.name)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def member(self, **overrides):
        values = dict(name="João da Silva", phone="(11) 99999-0000", address="Rua A, 100",
                      joined_on="2026-08-01", due_day=10, monthly_cents=15000,
                      first_month="2026-10-01", notes="")
        values.update(overrides)
        return self.store.save_member(values, TODAY)

    def test_create_search_edit_and_reopen(self):
        mid = self.member()
        self.assertEqual(self.store.members("JOAO")[0]["id"], mid)
        member = self.store.member(mid)
        member.update(name="João Santos", address="Rua B, 200")
        self.store.save_member(member, TODAY, mid)
        self.store.close()
        self.store = Store(self.tmp.name)
        self.assertEqual(self.store.member(mid)["address"], "Rua B, 200")
        self.assertEqual(len(self.store.members("santos")), 1)

    def test_months_are_recurring_without_duplicates(self):
        self.member(first_month="2026-08-01")
        self.store.refresh(TODAY)
        self.store.refresh(TODAY)
        self.assertEqual([r["month"] for r in self.store.invoices(TODAY)],
                         ["2026-08-01", "2026-09-01", "2026-10-01"])
        self.store.refresh(date(2026, 11, 15))
        self.assertEqual(len(self.store.invoices(date(2026, 11, 15))), 4)

    def test_starting_month_does_not_create_older_debt(self):
        self.member(joined_on="2020-01-01", first_month="2026-10-01")
        self.assertEqual(len(self.store.invoices(TODAY)), 1)

    def test_future_first_month_has_no_current_charge(self):
        self.member(first_month="2026-12-01")
        self.assertFalse(self.store.invoices(TODAY))

    def test_day_31_and_leap_year(self):
        self.assertEqual(due_date(date(2026, 2, 1), 31), date(2026, 2, 28))
        self.assertEqual(due_date(date(2028, 2, 1), 31), date(2028, 2, 29))
        self.assertEqual(due_date(date(2026, 4, 1), 31), date(2026, 4, 30))
        self.assertEqual(due_date(date(2026, 3, 1), 31), date(2026, 3, 31))

    def test_filter_boundaries(self):
        for offset, state in [(-1, "late"), (0, "today"), (1, "soon"), (7, "soon"), (8, "future")]:
            with self.subTest(offset=offset):
                inv = {"due_on": (TODAY + timedelta(days=offset)).isoformat(), "paid_on": None}
                self.assertEqual(invoice_status(inv, TODAY), state)
        inv["paid_on"] = TODAY.isoformat()
        self.assertEqual(invoice_status(inv, TODAY), "paid")

    def test_soon_crosses_year_boundary(self):
        today = date(2026, 12, 29)
        self.member(due_day=3, first_month="2026-12-01")
        self.store.refresh(today)
        soon = self.store.invoices(today, "soon")
        self.assertEqual([r["due_on"] for r in soon], ["2027-01-03"])

    def test_pay_is_persisted_and_not_double_counted(self):
        self.member()
        inv = self.store.invoices(TODAY)[0]
        self.store.pay(inv["id"], TODAY, "Pix", TODAY)
        self.assertFalse(self.store.invoices(TODAY, "late"))
        self.assertEqual(self.store.summary(TODAY)["received"], 15000)
        self.assertEqual(self.store.invoices(TODAY, "paid")[0]["payment_method"], "Pix")
        with self.assertRaises(ValueError):
            self.store.pay(inv["id"], TODAY, "Pix", TODAY)
        self.store.close()
        self.store = Store(self.tmp.name)
        self.assertEqual(self.store.invoices(TODAY, "paid")[0]["paid_on"], TODAY.isoformat())
        self.store.undo_payment(inv["id"])
        self.assertEqual(self.store.summary(TODAY)["received"], 0)
        self.assertEqual(len(self.store.invoices(TODAY, "late")), 1)

    def test_future_payment_rejected(self):
        self.member()
        inv = self.store.invoices(TODAY)[0]
        with self.assertRaises(ValueError):
            self.store.pay(inv["id"], TODAY + timedelta(days=1), "Pix", TODAY)
        self.assertFalse(self.store.invoice(inv["id"])["paid_on"])

    def test_summary_received_uses_payment_month(self):
        self.member(first_month="2026-09-01")
        rows = self.store.invoices(TODAY)
        self.store.pay(rows[0]["id"], date(2026, 9, 20), "Dinheiro", TODAY)
        self.store.pay(rows[1]["id"], TODAY, "Cartão", TODAY)
        self.assertEqual(self.store.summary(TODAY)["received"], 15000)

    def test_edit_preserves_paid_and_overdue_invoices(self):
        mid = self.member(first_month="2026-09-01", due_day=20)
        rows = self.store.invoices(TODAY)
        self.store.pay(rows[0]["id"], TODAY, "Pix", TODAY)
        member = self.store.member(mid)
        member.update(monthly_cents=18000, due_day=25)
        self.store.save_member(member, TODAY, mid)
        all_rows = self.store.invoices(TODAY, "all")
        self.assertEqual(all_rows[0]["amount_cents"], 15000)
        self.assertEqual(all_rows[0]["due_on"], "2026-09-20")
        self.assertEqual(all_rows[1]["amount_cents"], 18000)
        self.assertEqual(all_rows[1]["due_on"], "2026-10-25")
        # Uma mensalidade já vencida também não muda ao editar o cadastro.
        mid2 = self.member(name="Maria", due_day=1)
        member2 = self.store.member(mid2)
        member2.update(monthly_cents=20000, due_day=20)
        self.store.save_member(member2, TODAY, mid2)
        self.assertEqual(self.store.invoices(TODAY, member_id=mid2)[0]["amount_cents"], 15000)

    def test_edit_due_day_does_not_backdate_future_invoice(self):
        mid = self.member(due_day=20)
        member = self.store.member(mid)
        member["due_day"] = 5
        self.store.save_member(member, TODAY, mid)
        self.assertEqual(self.store.invoices(TODAY, member_id=mid)[0]["due_on"], "2026-10-14")

    def test_basic_fee_updates_linked_members_and_preserves_history(self):
        self.store.set_basic_monthly_cents(15000, TODAY)
        paid = self.member(name="Aluno pago", fee_type="basic", due_day=20)
        paid_invoice = self.store.invoices(TODAY, member_id=paid)[0]
        self.store.pay(paid_invoice["id"], TODAY, "Pix", TODAY)
        late = self.member(name="Aluno atrasado", fee_type="basic", due_day=10)
        due = self.member(name="Aluno de hoje", fee_type="basic", due_day=14)
        future = self.member(name="Aluno futuro", fee_type="basic", due_day=20)
        inactive = self.member(name="Aluno inativo", fee_type="basic", due_day=20)
        self.store.set_active(inactive, False, TODAY)
        custom = self.member(name="Aluno personalizado", due_day=20)

        self.store.set_basic_monthly_cents(18050, TODAY)
        for mid in (paid, late, due, future, inactive):
            self.assertEqual(self.store.member(mid)["monthly_cents"], 18050)
        self.assertEqual(self.store.member(custom)["monthly_cents"], 15000)
        for mid, expected in ((paid, 15000), (late, 15000), (due, 18050), (future, 18050), (custom, 15000)):
            self.assertEqual(self.store.invoices(TODAY, "all", member_id=mid)[0]["amount_cents"], expected)
        self.assertFalse(self.store.invoices(TODAY, member_id=inactive))
        self.store.undo_payment(paid_invoice["id"])
        self.assertEqual(self.store.invoice(paid_invoice["id"])["amount_cents"], 15000)

        self.store.close()
        self.store = Store(self.tmp.name)
        self.assertEqual(self.store.basic_monthly_cents(), 18050)
        self.store.refresh(date(2026, 11, 14))
        self.assertEqual(self.store.invoices(date(2026, 11, 14), member_id=late)[-1]["amount_cents"], 18050)
        self.store.set_active(inactive, True, date(2026, 11, 14))
        self.assertEqual(self.store.invoices(date(2026, 11, 14), member_id=inactive)[0]["amount_cents"], 18050)

    def test_basic_fee_update_generates_missed_months_at_previous_price(self):
        self.store.set_basic_monthly_cents(15000, TODAY)
        mid = self.member(fee_type="basic", due_day=20)
        later = date(2027, 1, 14)
        self.store.set_basic_monthly_cents(20000, later)
        rows = self.store.invoices(later, member_id=mid)
        self.assertEqual([row["amount_cents"] for row in rows], [15000, 15000, 15000, 20000])
        self.assertEqual(rows[-1]["due_on"], "2027-01-20")

    def test_basic_fee_updates_prepared_next_month_and_new_students(self):
        self.store.set_basic_monthly_cents(15000, TODAY)
        mid = self.member(fee_type="basic", due_day=3)
        later = date(2026, 10, 29)
        self.store.refresh(later)
        self.store.set_basic_monthly_cents(17500, later)
        rows = self.store.invoices(later, member_id=mid)
        self.assertEqual([row["amount_cents"] for row in rows], [15000, 17500])
        new = self.member(name="Novo aluno", fee_type="basic", monthly_cents=1)
        self.assertEqual(self.store.member(new)["monthly_cents"], 17500)

    def test_switching_between_basic_and_custom_prices(self):
        self.store.set_basic_monthly_cents(17000, TODAY)
        mid = self.member(due_day=20)
        member = self.store.member(mid)
        member.update(fee_type="basic", monthly_cents=1)
        self.store.save_member(member, TODAY, mid)
        self.assertEqual(self.store.member(mid)["monthly_cents"], 17000)
        member = self.store.member(mid)
        member.update(fee_type="custom", monthly_cents=13500)
        self.store.save_member(member, TODAY, mid)
        self.store.set_basic_monthly_cents(19000, TODAY)
        self.assertEqual(self.store.member(mid)["monthly_cents"], 13500)
        self.assertEqual(self.store.invoices(TODAY, member_id=mid)[0]["amount_cents"], 13500)

    def test_basic_fee_requires_configuration_and_rejects_invalid_updates(self):
        self.assertIsNone(self.store.basic_monthly_cents())
        with self.assertRaisesRegex(ValueError, "aba Mensalidades"):
            self.member(fee_type="basic")
        self.assertFalse(self.store.members())
        self.store.set_basic_monthly_cents(15000, TODAY)
        mid = self.member(fee_type="basic")
        for value in (0, -10, 100000000, 150.5, "15000", None, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.store.set_basic_monthly_cents(value, TODAY)
            self.assertEqual(self.store.basic_monthly_cents(), 15000)
            self.assertEqual(self.store.member(mid)["monthly_cents"], 15000)

    def legacy_backup(self):
        target = Path(self.tmp.name) / "versao-1.sqlite3"
        self.store.backup(target)
        with closing(sqlite3.connect(target)) as connection:
            connection.executescript("""
                ALTER TABLE members DROP COLUMN fee_type;
                DROP TABLE billing_settings;
                PRAGMA user_version=1;
            """)
        return target

    def test_legacy_database_and_backups_migrate_without_changing_prices(self):
        mid = self.member(monthly_cents=14500)
        legacy = self.legacy_backup()
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "academia.sqlite3").write_bytes(legacy.read_bytes())
            migrated = Store(directory)
            try:
                self.assertEqual(migrated.member(mid)["fee_type"], "custom")
                self.assertEqual(migrated.member(mid)["monthly_cents"], 14500)
                self.assertIsNone(migrated.basic_monthly_cents())
                migrated.set_basic_monthly_cents(18000, TODAY)
                self.assertEqual(migrated.member(mid)["monthly_cents"], 14500)
            finally:
                migrated.close()
        self.store.set_basic_monthly_cents(20000, TODAY)
        self.store.restore(legacy)
        self.assertIsNone(self.store.basic_monthly_cents())
        self.assertEqual(self.store.member(mid)["fee_type"], "custom")
        self.assertEqual(self.store.invoices(TODAY)[0]["amount_cents"], 14500)
        with closing(sqlite3.connect(legacy)) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 1)

    def test_backup_restores_basic_fee_and_member_selection(self):
        self.store.set_basic_monthly_cents(15000, TODAY)
        mid = self.member(fee_type="basic", due_day=20)
        target = self.store.backup(Path(self.tmp.name) / "basica.sqlite3")
        self.store.set_basic_monthly_cents(20000, TODAY)
        self.store.restore(target)
        self.assertEqual(self.store.basic_monthly_cents(), 15000)
        self.assertEqual(self.store.member(mid)["fee_type"], "basic")
        self.store.set_basic_monthly_cents(18000, TODAY)
        self.assertEqual(self.store.invoices(TODAY)[0]["amount_cents"], 18000)

    def test_deactivate_preserves_debt_and_skips_inactive_months(self):
        mid = self.member(due_day=10)
        self.store.set_active(mid, False, TODAY)
        later = date(2027, 1, 15)
        self.store.refresh(later)
        self.assertEqual(len(self.store.invoices(later, member_id=mid)), 1)
        self.store.set_active(mid, True, later)
        self.assertEqual(self.store.member(mid)["billing_from"], "2027-02-01")
        self.store.refresh(date(2027, 2, 10))
        rows = self.store.invoices(date(2027, 2, 10), member_id=mid)
        self.assertEqual([r["month"] for r in rows], ["2026-10-01", "2027-02-01"])

    def test_deactivate_removes_unpaid_future_and_keeps_prepayment(self):
        mid = self.member(due_day=20)
        self.store.set_active(mid, False, TODAY)
        self.assertFalse(self.store.invoices(TODAY))
        self.store.set_active(mid, True, TODAY)
        row = self.store.invoices(TODAY)[0]
        self.store.pay(row["id"], TODAY, "Pix", TODAY)
        self.store.set_active(mid, False, TODAY)
        self.assertEqual(len(self.store.invoices(TODAY, "paid")), 1)
        self.assertFalse(self.store.members(activity="active"))
        self.assertEqual(len(self.store.members(activity="inactive")), 1)

    def test_delete_cascades_history(self):
        mid = self.member()
        self.store.delete_member(mid)
        self.assertFalse(self.store.members())
        self.assertFalse(self.store.invoices(TODAY, "all"))
        self.assertFalse(self.store.connection.execute("PRAGMA foreign_key_check").fetchall())

    def test_backup_restore_preserves_safety_copy(self):
        mid = self.member()
        target = Path(self.tmp.name) / "copia.sqlite3"
        self.store.backup(target)
        self.store.pay(self.store.invoices(TODAY)[0]["id"], TODAY, "Pix", TODAY)
        self.member(name="Outro aluno")
        safety = self.store.restore(target)
        self.assertTrue(safety.is_file())
        self.assertEqual(len(self.store.members()), 1)
        self.assertFalse(self.store.invoices(TODAY, "paid"))
        with closing(sqlite3.connect(safety)) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM members").fetchone()[0], 2)
            self.assertIsNotNone(connection.execute("SELECT paid_on FROM invoices ORDER BY id").fetchone()[0])

    def test_invalid_restore_does_not_touch_current_data(self):
        self.member()
        for filename, data in [("texto.sqlite3", b"isto nao e um banco"), ("vazio.sqlite3", b"")]:
            path = Path(self.tmp.name) / filename
            path.write_bytes(data)
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                self.store.restore(path)
            self.assertEqual(len(self.store.members()), 1)

    def test_future_schema_restore_rejected(self):
        path = Path(self.tmp.name) / "future.sqlite3"
        with closing(sqlite3.connect(path)) as connection:
            connection.execute(f"PRAGMA application_id={APP_ID}")
            connection.execute("PRAGMA user_version=999")
        with self.assertRaises(ValueError):
            self.store.restore(path)

    def test_daily_backup_contains_latest_changes_and_keeps_30(self):
        first = self.store.automatic_backup(TODAY)
        self.member()
        self.store.automatic_backup(TODAY)
        with closing(sqlite3.connect(first)) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM members").fetchone()[0], 1)
        for offset in range(35):
            self.store.automatic_backup(TODAY + timedelta(days=offset))
        self.assertEqual(len(list((Path(self.tmp.name) / "backups").glob("academia-*.sqlite3"))), 30)

    def test_backup_does_not_overwrite_existing_or_live_database(self):
        with self.assertRaises(ValueError):
            self.store.backup(self.store.path)
        path = Path(self.tmp.name) / "manual.sqlite3"
        path.write_bytes(b"existing")
        with self.assertRaises(ValueError):
            self.store.backup(path)
        self.assertEqual(path.read_bytes(), b"existing")

    def test_export_is_excel_readable_and_preserves_accents(self):
        self.member(name="Álvaro", address="=1+1")
        target = Path(self.tmp.name) / "alunos.csv"
        self.store.export_members(target)
        self.assertTrue(target.read_bytes().startswith(b"\xef\xbb\xbf"))
        with target.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.reader(handle, delimiter=";"))
        self.assertEqual(rows[1][0], "Álvaro")
        self.assertEqual(rows[1][2], "'=1+1")
        self.assertEqual(rows[1][5], "150,00")
        self.store.export_invoices(target, self.store.invoices(TODAY, "late"), TODAY)
        self.assertIn("Em atraso", target.read_text(encoding="utf-8-sig"))

    def test_validation_is_atomic(self):
        for values in [{"name": " "}, {"due_day": 32}, {"monthly_cents": 0},
                       {"first_month": "2020-01-01"}, {"joined_on": "2030-01-01"}]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.member(**values)
            self.assertFalse(self.store.members())

    def test_currency_uses_integer_cents(self):
        self.assertEqual(parse_money("R$ 1.234,56"), 123456)
        self.assertEqual(parse_money("150,00"), 15000)
        self.assertEqual(parse_money("150.50"), 15050)
        self.assertEqual(money(123456), "R$ 1.234,56")
        for invalid in ("", "0", "-20", "NaN", "Inf", "1,001", "1000000", "abc"):
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                parse_money(invalid)


if __name__ == "__main__":
    unittest.main()
