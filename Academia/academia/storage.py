"""Regras de mensalidade e persistência. Não depende da interface Qt."""
from __future__ import annotations

import calendar
import csv
import os
import sqlite3
import sys
import unicodedata
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

APP_ID = 0x44414341
SCHEMA_VERSION = 1
STATUSES = {
    "late": "Em atraso",
    "today": "Vence hoje",
    "soon": "Próximos 7 dias",
    "future": "A vencer",
    "paid": "Pago",
}
MONTHS = ("", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
          "julho", "agosto", "setembro", "outubro", "novembro", "dezembro")


def data_directory() -> Path:
    # Mantém o identificador original para continuar abrindo cadastros já existentes.
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "DouglasAcademia"
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/DouglasAcademia"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "DouglasAcademia"


def normalized(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", value.casefold())
                   if not unicodedata.combining(c))


def money(cents: int) -> str:
    whole, fraction = divmod(cents, 100)
    return f"R$ {whole:,}".replace(",", ".") + f",{fraction:02d}"


def parse_money(value: str) -> int:
    clean = value.strip().replace("R$", "").replace(" ", "")
    if "," in clean:
        clean = clean.replace(".", "").replace(",", ".")
    try:
        amount = Decimal(clean)
        if not amount.is_finite() or amount <= 0 or amount > Decimal("999999.99"):
            raise ValueError
        if amount.as_tuple().exponent < -2:
            raise ValueError
        return int(amount * 100)
    except (InvalidOperation, ValueError):
        raise ValueError("Informe um valor válido, por exemplo: 150,00.") from None


def month_start(day: date) -> date:
    return day.replace(day=1)


def next_month(day: date) -> date:
    return date(day.year + (day.month == 12), day.month % 12 + 1, 1)


def due_date(month: date, due_day: int) -> date:
    return month.replace(day=min(due_day, calendar.monthrange(month.year, month.month)[1]))


def month_label(value: str) -> str:
    day = date.fromisoformat(value)
    return f"{MONTHS[day.month].capitalize()} / {day.year}"


def invoice_status(invoice: dict, today: date) -> str:
    if invoice["paid_on"]:
        return "paid"
    due = date.fromisoformat(invoice["due_on"])
    days = (due - today).days
    return "late" if days < 0 else "today" if days == 0 else "soon" if days <= 7 else "future"


def status_detail(invoice: dict, today: date) -> str:
    status = invoice_status(invoice, today)
    days = (date.fromisoformat(invoice["due_on"]) - today).days
    if status == "late":
        return f"{abs(days)} dia{'s' if abs(days) != 1 else ''} de atraso"
    if status == "paid":
        return "Pago em " + date.fromisoformat(invoice["paid_on"]).strftime("%d/%m/%Y")
    if status == "today":
        return "Vence hoje"
    return f"Vence em {days} dia{'s' if days != 1 else ''}"


class Store:
    def __init__(self, directory: str | Path):
        self.directory = Path(directory).expanduser().resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "academia.sqlite3"
        self.connection = sqlite3.connect(self.path, timeout=10)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute("PRAGMA busy_timeout=10000")
        identity = self.connection.execute("PRAGMA application_id").fetchone()[0]
        version = self.connection.execute("PRAGMA user_version").fetchone()[0]
        if identity not in (0, APP_ID) or version > SCHEMA_VERSION:
            self.connection.close()
            raise ValueError("Este arquivo de dados não é compatível com esta versão do aplicativo.")
        self.connection.executescript(f"""
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL CHECK(length(trim(name)) >= 2),
                phone TEXT NOT NULL DEFAULT '',
                address TEXT NOT NULL DEFAULT '',
                joined_on TEXT NOT NULL,
                due_day INTEGER NOT NULL CHECK(due_day BETWEEN 1 AND 31),
                monthly_cents INTEGER NOT NULL CHECK(monthly_cents > 0),
                first_month TEXT NOT NULL,
                billing_from TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY,
                member_id INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
                month TEXT NOT NULL,
                due_on TEXT NOT NULL,
                amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
                paid_on TEXT,
                payment_method TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(member_id, month)
            );
            CREATE INDEX IF NOT EXISTS invoice_due_idx ON invoices(due_on, paid_on);
            PRAGMA application_id={APP_ID};
            PRAGMA user_version={SCHEMA_VERSION};
        """)

    def close(self):
        self.connection.close()

    def member(self, member_id: int) -> dict:
        row = self.connection.execute("SELECT * FROM members WHERE id=?", (member_id,)).fetchone()
        if row is None:
            raise ValueError("Este aluno não está mais cadastrado. Atualize a lista.")
        return dict(row)

    def members(self, search: str = "", activity: str = "all") -> list[dict]:
        rows = [dict(row) for row in self.connection.execute("SELECT * FROM members")]
        query = normalized(search.strip())
        return sorted((row for row in rows
                       if (activity == "all" or bool(row["active"]) == (activity == "active"))
                       and (not query or query in normalized(row["name"] + " " + row["phone"]))),
                      key=lambda row: normalized(row["name"]))

    def save_member(self, values: dict, today: date, member_id: int | None = None) -> int:
        data = {key: str(values.get(key, "")).strip() for key in ("name", "phone", "address", "notes")}
        if not 2 <= len(data["name"]) <= 120:
            raise ValueError("Informe o nome do aluno, com pelo menos 2 letras.")
        try:
            data["joined_on"] = date.fromisoformat(values["joined_on"]).isoformat()
            data["due_day"] = int(values["due_day"])
            data["monthly_cents"] = int(values["monthly_cents"])
            data["first_month"] = month_start(date.fromisoformat(values["first_month"])).isoformat()
        except (KeyError, ValueError, TypeError):
            raise ValueError("Confira as datas, o dia do vencimento e o valor da mensalidade.") from None
        if not 1 <= data["due_day"] <= 31:
            raise ValueError("O dia do vencimento deve ficar entre 1 e 31.")
        if not 1 <= data["monthly_cents"] <= 99999999:
            raise ValueError("A mensalidade deve ser maior que zero.")
        if data["first_month"] < data["joined_on"][:7] + "-01":
            raise ValueError("A primeira mensalidade não pode ser anterior ao mês de entrada.")
        if date.fromisoformat(data["joined_on"]) > today:
            raise ValueError("A data de entrada não pode ser no futuro.")
        with self.connection:
            if member_id is None:
                cursor = self.connection.execute("""
                    INSERT INTO members(name,phone,address,joined_on,due_day,monthly_cents,
                                        first_month,billing_from,notes)
                    VALUES(:name,:phone,:address,:joined_on,:due_day,:monthly_cents,
                           :first_month,:first_month,:notes)
                """, data)
                member_id = cursor.lastrowid
            else:
                old = self.member(member_id)
                if data["first_month"] != old["first_month"]:
                    raise ValueError("O mês inicial é definido no cadastro e não pode ser alterado.")
                self.connection.execute("""
                    UPDATE members SET name=:name,phone=:phone,address=:address,joined_on=:joined_on,
                        due_day=:due_day,monthly_cents=:monthly_cents,notes=:notes WHERE id=:id
                """, {**data, "id": member_id})
                for row in self.connection.execute(
                        "SELECT id,month FROM invoices WHERE member_id=? AND paid_on IS NULL AND due_on>=?",
                        (member_id, today.isoformat())).fetchall():
                    # Não transforma uma cobrança futura em dívida retroativa ao editar o dia.
                    new_due = max(today, due_date(date.fromisoformat(row["month"]), data["due_day"]))
                    self.connection.execute("UPDATE invoices SET due_on=?,amount_cents=? WHERE id=?",
                                            (new_due.isoformat(), data["monthly_cents"], row["id"]))
            self._generate(today)
        return member_id

    def _generate(self, today: date):
        horizon = month_start(today + timedelta(days=7))
        for member in self.connection.execute("SELECT * FROM members WHERE active=1").fetchall():
            month = date.fromisoformat(member["billing_from"])
            while month <= horizon:
                self.connection.execute("""
                    INSERT OR IGNORE INTO invoices(member_id,month,due_on,amount_cents)
                    VALUES(?,?,?,?)
                """, (member["id"], month.isoformat(), due_date(month, member["due_day"]).isoformat(),
                      member["monthly_cents"]))
                month = next_month(month)

    def refresh(self, today: date):
        with self.connection:
            self._generate(today)

    def set_active(self, member_id: int, active: bool, today: date):
        member = self.member(member_id)
        if bool(member["active"]) == active:
            return
        with self.connection:
            if active:
                first = month_start(today)
                if due_date(first, member["due_day"]) < today:
                    first = next_month(first)
                first = max(first, date.fromisoformat(member["first_month"]))
                self.connection.execute("UPDATE members SET active=1,billing_from=? WHERE id=?",
                                        (first.isoformat(), member_id))
                self._generate(today)
            else:
                self.connection.execute("UPDATE members SET active=0 WHERE id=?", (member_id,))
                self.connection.execute("DELETE FROM invoices WHERE member_id=? AND paid_on IS NULL AND due_on>=?",
                                        (member_id, today.isoformat()))

    def delete_member(self, member_id: int):
        self.member(member_id)
        with self.connection:
            self.connection.execute("DELETE FROM members WHERE id=?", (member_id,))

    def invoices(self, today: date, status: str = "open", search: str = "",
                 member_id: int | None = None) -> list[dict]:
        query = normalized(search.strip())
        result = []
        for row in self.connection.execute("""
            SELECT i.*,m.name,m.phone,m.active FROM invoices i JOIN members m ON m.id=i.member_id
            ORDER BY i.due_on,i.id
        """):
            item = dict(row)
            state = invoice_status(item, today)
            if member_id is not None and item["member_id"] != member_id:
                continue
            if query and query not in normalized(item["name"] + " " + item["phone"]):
                continue
            if status == "open" and state == "paid":
                continue
            if status not in ("all", "open") and state != status:
                continue
            item["status"] = state
            result.append(item)
        return result

    def invoice(self, invoice_id: int) -> dict:
        row = self.connection.execute("""SELECT i.*,m.name FROM invoices i
            JOIN members m ON m.id=i.member_id WHERE i.id=?""", (invoice_id,)).fetchone()
        if row is None:
            raise ValueError("Esta mensalidade não está mais disponível. Atualize a lista.")
        return dict(row)

    def pay(self, invoice_id: int, paid_on: date, method: str, today: date):
        invoice = self.invoice(invoice_id)
        if invoice["paid_on"]:
            raise ValueError("Esta mensalidade já está paga.")
        if paid_on > today:
            raise ValueError("O recebimento não pode ter uma data futura.")
        if method not in ("Pix", "Dinheiro", "Cartão", "Transferência", "Outro"):
            raise ValueError("Escolha como o aluno pagou.")
        with self.connection:
            self.connection.execute("UPDATE invoices SET paid_on=?,payment_method=? WHERE id=?",
                                    (paid_on.isoformat(), method, invoice_id))

    def undo_payment(self, invoice_id: int):
        with self.connection:
            self.connection.execute("UPDATE invoices SET paid_on=NULL,payment_method='' WHERE id=?", (invoice_id,))

    def summary(self, today: date) -> dict:
        invoices = self.invoices(today, "all")
        return {
            "active": len(self.members(activity="active")),
            **{key: sum(row["amount_cents"] for row in invoices if row["status"] == key)
               for key in ("late", "today", "soon")},
            "late_count": sum(row["status"] == "late" for row in invoices),
            "today_count": sum(row["status"] == "today" for row in invoices),
            "soon_count": sum(row["status"] == "soon" for row in invoices),
            "received": sum(row["amount_cents"] for row in invoices
                            if row["paid_on"] and row["paid_on"][:7] == today.isoformat()[:7]),
        }

    def backup(self, destination: str | Path) -> Path:
        destination = Path(destination).expanduser().resolve()
        if destination == self.path:
            raise ValueError("Escolha outro arquivo para salvar a cópia de segurança.")
        if destination.exists():
            raise ValueError("Já existe um arquivo com esse nome. Escolha outro nome para o backup.")
        # Cria primeiro ao lado do destino. Um erro não deixa uma cópia parcial visível.
        temporary = destination.with_name(destination.name + ".partial")
        try:
            with sqlite3.connect(temporary) as output:
                self.connection.backup(output)
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)
        return destination

    def automatic_backup(self, today: date) -> Path:
        folder = self.directory / "backups"
        folder.mkdir(exist_ok=True)
        destination = folder / f"academia-{today.isoformat()}.sqlite3"
        temporary = folder / f".diario-{uuid.uuid4().hex}.sqlite3"
        try:
            self.backup(temporary)
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)
        # Conserva as últimas 30 cópias diárias; backups manuais não são apagados.
        for old in sorted(folder.glob("academia-????-??-??.sqlite3"), reverse=True)[30:]:
            old.unlink()
        return destination

    def restore(self, source: str | Path) -> Path:
        source = Path(source).expanduser().resolve()
        if source == self.path:
            raise ValueError("Este já é o arquivo de dados em uso.")
        if not source.is_file():
            raise ValueError("A cópia de segurança não foi encontrada.")
        candidate = None
        try:
            candidate = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)
            if (candidate.execute("PRAGMA application_id").fetchone()[0] != APP_ID
                    or candidate.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION
                    or candidate.execute("PRAGMA integrity_check").fetchone()[0] != "ok"):
                raise ValueError("O arquivo escolhido não é um backup válido da Power Academia.")
            # Confere as tabelas/colunas antes de tocar nos dados atuais.
            candidate.execute("SELECT name,phone,address,joined_on,due_day,monthly_cents,first_month,billing_from,active,notes FROM members LIMIT 1")
            candidate.execute("SELECT member_id,month,due_on,amount_cents,paid_on,payment_method FROM invoices LIMIT 1")
            if candidate.execute("PRAGMA foreign_key_check").fetchone():
                raise ValueError("O backup contém registros incompletos e não pode ser restaurado.")
            folder = self.directory / "backups"
            folder.mkdir(exist_ok=True)
            safety = self.backup(folder / f"antes-de-restaurar-{datetime.now():%Y%m%d-%H%M%S-%f}.sqlite3")
            candidate.backup(self.connection)
            self.connection.execute("PRAGMA foreign_keys=ON")
            return safety
        except sqlite3.DatabaseError:
            raise ValueError("Não foi possível ler esse backup. Escolha uma cópia criada pelo aplicativo.") from None
        finally:
            if candidate:
                candidate.close()

    @staticmethod
    def _csv_text(value):
        # Evita interpretar um nome/endereço como fórmula ao abrir a exportação no Excel.
        text = str(value)
        return "'" + text if text.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else text

    def export_members(self, destination: str | Path):
        with open(destination, "w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle, delimiter=";")
            writer.writerow(["Nome", "Telefone", "Endereço", "Data de entrada", "Dia de vencimento",
                             "Mensalidade (R$)", "Situação", "Observações"])
            for row in self.members():
                writer.writerow([self._csv_text(row["name"]), self._csv_text(row["phone"]),
                                 self._csv_text(row["address"]), date.fromisoformat(row["joined_on"]).strftime("%d/%m/%Y"),
                                 row["due_day"], f'{row["monthly_cents"]/100:.2f}'.replace(".", ","),
                                 "Ativo" if row["active"] else "Inativo", self._csv_text(row["notes"])])

    def export_invoices(self, destination: str | Path, invoices: list[dict], today: date):
        with open(destination, "w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle, delimiter=";")
            writer.writerow(["Aluno", "Referência", "Vencimento", "Valor (R$)", "Situação", "Recebido em", "Forma de pagamento"])
            for row in invoices:
                writer.writerow([self._csv_text(row["name"]), month_label(row["month"]),
                                 date.fromisoformat(row["due_on"]).strftime("%d/%m/%Y"),
                                 f'{row["amount_cents"]/100:.2f}'.replace(".", ","),
                                 STATUSES[invoice_status(row, today)],
                                 date.fromisoformat(row["paid_on"]).strftime("%d/%m/%Y") if row["paid_on"] else "",
                                 row["payment_method"]])
