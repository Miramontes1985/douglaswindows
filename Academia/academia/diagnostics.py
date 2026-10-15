"""Verificação do executável empacotado, sempre em dados temporários."""
from __future__ import annotations

import json
import platform
import struct
import sys
import traceback
from datetime import date
from pathlib import Path

from .qt import BINDING, QtCore


def verify_packaged_app(window, destination: Path) -> int:
    result = {"ok": False, "architecture": struct.calcsize("P") * 8,
              "binding": BINDING, "qt": QtCore.qVersion(), "python": platform.python_version(),
              "windows": platform.platform(), "frozen": bool(getattr(sys, "frozen", False))}
    try:
        from .theme import ASSETS
        from .ui import MemberDialog, PaymentDialog
        store, today = window.store, date.today()
        assert (ASSETS / "douglas.png").is_file(), "Retrato não incluído no pacote"
        store.set_basic_monthly_cents(15000, today)
        mid = store.save_member({"name": "Teste de instalação", "joined_on": today.isoformat(),
            "due_day": today.day, "fee_type": "basic", "first_month": today.replace(day=1).isoformat()}, today)
        window.refresh()
        for mode in ("dark", "light"):
            window.set_theme(mode)
            for page in ("home", "members", "invoices", "data"):
                window.open_page(page)
        window.open_page("invoices")
        window.basic_amount.setText("175,50")
        window.update_basic_button.click()
        assert store.basic_monthly_cents() == 17550
        assert store.member(mid)["monthly_cents"] == 17550
        invoice = store.invoices(today, member_id=mid)[0]
        assert invoice["amount_cents"] == 17550
        for dialog in (MemberDialog(store, today, window), PaymentDialog(invoice, today, window)):
            dialog.show()
            QtCore.QCoreApplication.processEvents()
            dialog.close()
        store.pay(invoice["id"], today, "Pix", today)
        assert store.summary(today)["received"] == 17550
        store.export_members(store.directory / "alunos.csv")
        copy = store.backup(store.directory / "verificacao.sqlite3")
        store.delete_member(mid)
        store.restore(copy)
        assert store.member(mid)["name"] == "Teste de instalação"
        assert store.summary(today)["received"] == 17550
        assert store.basic_monthly_cents() == 17550
        assert store.member(mid)["fee_type"] == "basic"
        result["ok"] = True
    except Exception:
        result["error"] = traceback.format_exc()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if result["ok"] else 1
