"""Dados fictícios, usados exclusivamente no modo de demonstração e nas prévias."""
from datetime import date, timedelta
from .storage import month_start


def seed_demo(store, today: date):
    if store.members():
        return
    store.set_basic_monthly_cents(15000, today)
    examples = [
        ("Ana Paula Martins", -8, 15000), ("Carlos Eduardo Silva", -4, 15000),
        ("Mariana Oliveira", 0, 18000), ("João Pedro Santos", 2, 15000),
        ("Fernanda Costa", 5, 18000), ("Roberto Almeida", 7, 15000),
        ("Beatriz Souza", -2, 15000), ("Paulo Henrique Lima", -1, 18000),
    ]
    for index, (name, offset, amount) in enumerate(examples):
        due = today + timedelta(days=offset)
        joined = min(month_start(due), month_start(today))
        member_id = store.save_member({
            "name": name, "phone": "(11) 90000-0000", "address": "Rua de Exemplo, 100 · Centro",
            "joined_on": joined.isoformat(), "due_day": due.day, "monthly_cents": amount,
            "fee_type": "basic" if amount == 15000 else "custom",
            "first_month": month_start(due).isoformat(), "notes": "",
        }, today)
        if index >= 6:
            for row in store.invoices(today, member_id=member_id):
                if row["due_on"] <= today.isoformat():
                    store.pay(row["id"], today, "Pix" if index == 6 else "Dinheiro", today)
