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
        mid = store.save_member({"name": "Teste de instalação", "joined_on": today.isoformat(),
            "due_day": today.day, "monthly_cents": 15000, "first_month": today.replace(day=1).isoformat()}, today)
        window.refresh()
        for mode in ("dark", "light"):
            window.set_theme(mode)
            for page in ("home", "members", "invoices", "data"):
                window.open_page(page)
        invoice = store.invoices(today, member_id=mid)[0]
        for dialog in (MemberDialog(store, today, window), PaymentDialog(invoice, today, window)):
            dialog.show()
            QtCore.QCoreApplication.processEvents()
            dialog.close()
        store.pay(invoice["id"], today, "Pix", today)
        assert store.summary(today)["received"] == 15000
        store.export_members(store.directory / "alunos.csv")
        copy = store.backup(store.directory / "verificacao.sqlite3")
        store.delete_member(mid)
        store.restore(copy)
        assert store.member(mid)["name"] == "Teste de instalação"
        assert store.summary(today)["received"] == 15000
        result["ok"] = True
    except Exception:
        result["error"] = traceback.format_exc()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if result["ok"] else 1
