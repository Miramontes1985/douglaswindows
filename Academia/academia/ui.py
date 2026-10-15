from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from .qt import exec_qt, Qt, QDate, QTimer, QSize, QSettings
from .qt import QIcon, QPixmap, QDesktopServices
from .qt import QUrl
from .qt import (
    QAbstractItemView, QApplication, QButtonGroup, QComboBox, QDateEdit, QDialog,
    QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QSpinBox, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget, QFileDialog,
)

from .storage import (
    MONTHS, STATUSES, Store, invoice_status, money, month_label, month_start,
    next_month, normalized, parse_money, status_detail,
)
from .theme import ASSETS, THEMES, apply_theme, colors, icon, refresh_icons, update_button_icon


def label(text, role=None, wrap=False):
    widget = QLabel(text)
    widget.setTextFormat(Qt.PlainText)
    if role:
        widget.setProperty("role", role)
    widget.setWordWrap(wrap)
    return widget


def button(text, callback=None, variant=None, symbol=None):
    widget = QPushButton(text)
    if variant:
        widget.setProperty("variant", variant)
    if symbol:
        widget.setProperty("symbol", symbol)
        update_button_icon(widget)
        widget.setIconSize(QSize(20, 20))
    if callback:
        widget.clicked.connect(callback)
    widget.setCursor(Qt.PointingHandCursor)
    widget.setAutoDefault(False)
    return widget


def panel(name="Panel"):
    widget = QFrame()
    widget.setObjectName(name)
    return widget


def vbox(widget, margins=0, spacing=12):
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(margins, margins, margins, margins)
    layout.setSpacing(spacing)
    return layout


def clear(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().hide()
            item.widget().deleteLater()
        elif item.layout():
            clear(item.layout())


def qdate(day):
    return QDate(day.year, day.month, day.day)


def date_input(day, fmt="dd/MM/yyyy"):
    field = QDateEdit(qdate(day))
    field.setCalendarPopup(True)
    field.setDisplayFormat(fmt)
    field.setMinimumDate(QDate(1900, 1, 1))
    field.setMaximumDate(QDate(2100, 12, 31))
    return field


def confirm(parent, title, text, action, danger=False):
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setTextFormat(Qt.PlainText)
    box.setText(text)
    box.setIcon(QMessageBox.Warning if danger else QMessageBox.Question)
    cancel = box.addButton("Cancelar", QMessageBox.RejectRole)
    yes = box.addButton(action, QMessageBox.AcceptRole)
    if danger:
        yes.setProperty("variant", "danger")
    box.setDefaultButton(cancel)
    exec_qt(box)
    return box.clickedButton() == yes


def error(parent, message):
    box = QMessageBox(parent)
    box.setWindowTitle("Confira esta informação")
    box.setTextFormat(Qt.PlainText)
    box.setText(str(message))
    box.setIcon(QMessageBox.Warning)
    box.addButton("Entendi", QMessageBox.AcceptRole)
    exec_qt(box)


def make_table(headers, widths, rows):
    table = QTableWidget(rows, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setShowGrid(False)
    table.verticalHeader().hide()
    table.verticalHeader().setDefaultSectionSize(66)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSelectionMode(QAbstractItemView.SingleSelection)
    table.setAlternatingRowColors(False)
    table.setFocusPolicy(Qt.StrongFocus)
    table.setMinimumHeight(160)
    table.setFixedHeight(48 + max(1, min(rows, 8)) * 66 + 12)
    for col, width in enumerate(widths):
        if width:
            table.setColumnWidth(col, width)
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Fixed)
        else:
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)
            table.horizontalHeader().setMinimumSectionSize(170)
    table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    return table


def cell(table, row, col, text, bold=False, tooltip=None):
    item = QTableWidgetItem(str(text))
    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
    if bold:
        font = item.font()
        font.setBold(True)
        item.setFont(font)
    if tooltip:
        item.setToolTip(tooltip)
    table.setItem(row, col, item)


def cell_widget(table, row, col, widget):
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(10, 8, 10, 8)
    layout.addWidget(widget)
    table.setCellWidget(row, col, container)


def badge(text, state):
    item = label(text)
    item.setProperty("badge", state)
    item.setAlignment(Qt.AlignCenter)
    return item


class MemberDialog(QDialog):
    def __init__(self, store: Store, today: date, parent=None, member_id=None):
        super().__init__(parent)
        self.store, self.today, self.member_id = store, today, member_id
        member = store.member(member_id) if member_id else None
        self.setWindowTitle("Editar aluno" if member else "Cadastrar aluno")
        self.resize(660, 740)
        if self.screen():
            self.resize(660, min(740, self.screen().availableGeometry().height() - 60))
        root = vbox(self, 24, 16)
        root.addWidget(label("Editar aluno" if member else "Vamos cadastrar um aluno", "title"))
        root.addWidget(label("Preencha os dados abaixo. Nome e mensalidade são obrigatórios.", "muted", True))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        fields = QWidget()
        form = QGridLayout(fields)
        form.setContentsMargins(0, 0, 12, 4)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(8)
        form.setColumnStretch(0, 1)
        form.setColumnStretch(1, 1)
        self.name = QLineEdit(member["name"] if member else "")
        self.name.setMaxLength(120)
        self.name.setPlaceholderText("Nome completo")
        self.name.setObjectName("memberName")
        self.phone = QLineEdit(member["phone"] if member else "")
        self.phone.setMaxLength(30)
        self.phone.setPlaceholderText("(00) 00000-0000 · opcional")
        self.address = QLineEdit(member["address"] if member else "")
        self.address.setMaxLength(300)
        self.address.setPlaceholderText("Rua, número, bairro e cidade · opcional")
        self.joined = date_input(date.fromisoformat(member["joined_on"]) if member else today)
        self.joined.setMaximumDate(qdate(today))
        self.amount = QLineEdit(f'{member["monthly_cents"]/100:.2f}'.replace(".", ",") if member else "")
        self.amount.setPlaceholderText("Ex.: 150,00")
        self.amount.setMaxLength(12)
        self.amount.setObjectName("monthlyAmount")
        self.fee_type = QComboBox()
        self.fee_type.setObjectName("memberFeeType")
        self.fee_type.addItem("Mensalidade básica", "basic")
        self.fee_type.addItem("Valor personalizado", "custom")
        self.fee_type.setCurrentIndex(self.fee_type.findData(member["fee_type"] if member else "basic"))
        self._custom_amount = self.amount.text() if member and member["fee_type"] == "custom" else ""
        self.fee_note = label("", "muted", True)
        self.fee_type.currentIndexChanged.connect(self.update_fee_fields)
        self.due_day = QSpinBox()
        self.due_day.setRange(1, 31)
        self.due_day.setPrefix("Dia ")
        self.due_day.setValue(member["due_day"] if member else today.day)
        self.first_month = date_input(date.fromisoformat(member["first_month"]) if member else month_start(today), "MMMM / yyyy")
        self.first_month.setDisabled(member is not None)
        self.notes = QTextEdit(member["notes"] if member else "")
        self.notes.setAcceptRichText(False)
        self.notes.setPlaceholderText("Alguma informação que você quer lembrar? · opcional")
        self.notes.setFixedHeight(80)
        specs = [("Nome completo *", self.name, 0, 0, 2), ("Telefone", self.phone, 2, 0, 2),
                 ("Endereço", self.address, 4, 0, 2), ("Data de entrada", self.joined, 6, 0, 1),
                 ("Vencimento todo mês", self.due_day, 6, 1, 1),
                 ("Tipo de mensalidade", self.fee_type, 8, 0, 1), ("Valor da mensalidade (R$) *", self.amount, 8, 1, 1),
                 ("Primeira mensalidade", self.first_month, 10, 0, 2), ("Observações", self.notes, 13, 0, 2)]
        for text, field, row, col, span in specs:
            caption = label(text, "field")
            caption.setBuddy(field)
            form.addWidget(caption, row, col, 1, span)
            form.addWidget(field, row + 1, col, 1, span)
        form.addWidget(self.fee_note, 12, 0, 1, 2)
        self.update_fee_fields()
        scroll.setWidget(fields)
        root.addWidget(scroll, 1)
        note = label("Alterações de valor e vencimento valem para cobranças ainda não vencidas. O histórico é preservado."
                     if member else "As cobranças começam no mês escolhido. Para dias 29, 30 e 31, meses mais curtos usam o último dia.", "muted", True)
        root.addWidget(note)
        self.message = label("", "error", True)
        self.message.hide()
        root.addWidget(self.message)
        actions = QHBoxLayout()
        actions.addStretch()
        actions.addWidget(button("Cancelar", self.reject))
        self.save_button = button("Salvar alterações" if member else "Cadastrar aluno", self.save, "primary", "check")
        self.save_button.setObjectName("saveMember")
        actions.addWidget(self.save_button)
        root.addLayout(actions)
        self.name.setFocus()

    def update_fee_fields(self, *_):
        basic = self.fee_type.currentData() == "basic"
        if basic:
            if not self.amount.isReadOnly():
                self._custom_amount = self.amount.text()
            cents = self.store.basic_monthly_cents()
            self.amount.setText(f"{cents / 100:.2f}".replace(".", ",") if cents is not None else "")
            self.amount.setPlaceholderText("Defina em Mensalidades")
            self.fee_note.setText("Este aluno acompanha o valor básico definido na aba Mensalidades."
                                  if cents is not None else "Defina o valor da mensalidade básica na aba Mensalidades antes de salvar.")
        else:
            if self.amount.isReadOnly():
                self.amount.setText(self._custom_amount or self.amount.text())
            self.amount.setPlaceholderText("Ex.: 150,00")
            self.fee_note.setText("O valor personalizado é definido para este aluno e não acompanha reajustes da mensalidade básica.")
        self.amount.setReadOnly(basic)

    def save(self):
        try:
            values = {
                "name": self.name.text(), "phone": self.phone.text(), "address": self.address.text(),
                "joined_on": self.joined.date().toPython().isoformat(),
                "fee_type": self.fee_type.currentData(),
                "monthly_cents": parse_money(self.amount.text()) if self.fee_type.currentData() == "custom" else None,
                "due_day": self.due_day.value(),
                "first_month": self.first_month.date().toPython().replace(day=1).isoformat(),
                "notes": self.notes.toPlainText(),
            }
            self.member_id = self.store.save_member(values, self.today, self.member_id)
        except (ValueError, OSError) as exc:
            self.message.setText(str(exc))
            self.message.show()
            return
        self.accept()


class PaymentDialog(QDialog):
    def __init__(self, invoice, today, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar pagamento")
        self.setMinimumWidth(490)
        root = vbox(self, 28, 18)
        root.addWidget(label("Registrar pagamento", "title"))
        root.addWidget(label(invoice["name"], "section"))
        details = panel()
        info = vbox(details, 20, 8)
        info.addWidget(label(month_label(invoice["month"]), "muted"))
        amount = label(money(invoice["amount_cents"]), "amount")
        info.addWidget(amount)
        info.addWidget(label("Vencimento: " + date.fromisoformat(invoice["due_on"]).strftime("%d/%m/%Y"), "muted"))
        root.addWidget(details)
        root.addWidget(label("Recebido em", "field"))
        self.paid_on = date_input(today)
        self.paid_on.setMaximumDate(qdate(today))
        root.addWidget(self.paid_on)
        root.addWidget(label("Forma de pagamento", "field"))
        self.method = QComboBox()
        self.method.addItems(["Pix", "Dinheiro", "Cartão", "Transferência", "Outro"])
        root.addWidget(self.method)
        root.addWidget(label("Confirme somente depois de receber o valor integral.", "muted", True))
        actions = QHBoxLayout()
        actions.addWidget(button("Cancelar", self.reject))
        actions.addWidget(button("Confirmar recebimento", self.accept, "primary", "check"))
        root.addLayout(actions)


class MemberProfile(QDialog):
    def __init__(self, owner, member_id):
        super().__init__(owner)
        self.owner, self.member_id = owner, member_id
        self.setWindowTitle("Ficha do aluno")
        self.resize(1000, 720)
        self.root = vbox(self, 26, 16)
        self.render()

    def render(self):
        clear(self.root)
        member = self.owner.store.member(self.member_id)
        head = QHBoxLayout()
        name = label(member["name"], "title", True)
        head.addWidget(name, 1)
        head.addWidget(badge("Ativo" if member["active"] else "Inativo", "active" if member["active"] else "inactive"))
        self.root.addLayout(head)
        info = panel()
        lines = vbox(info, 18, 7)
        fee_label = "Mensalidade básica" if member["fee_type"] == "basic" else "Mensalidade personalizada"
        lines.addWidget(label(f"{fee_label}: {money(member['monthly_cents'])}   •   Vencimento: dia {member['due_day']:02d}"))
        lines.addWidget(label("Entrou em " + date.fromisoformat(member["joined_on"]).strftime("%d/%m/%Y"), "muted"))
        lines.addWidget(label("Telefone: " + (member["phone"] or "Não informado"), "muted"))
        lines.addWidget(label("Endereço: " + (member["address"] or "Não informado"), "muted", True))
        if member["notes"]:
            lines.addWidget(label("Observações: " + member["notes"], "muted", True))
        self.root.addWidget(info)
        controls = QHBoxLayout()
        controls.addWidget(button("Editar cadastro", self.edit, symbol="edit"))
        controls.addWidget(button("Desativar aluno" if member["active"] else "Reativar aluno", self.toggle))
        controls.addStretch()
        controls.addWidget(button("Excluir aluno", self.delete, "danger"))
        self.root.addLayout(controls)
        rows = self.owner.store.invoices(self.owner.today, "all", member_id=self.member_id)
        pending = sum(row["amount_cents"] for row in rows if not row["paid_on"])
        self.root.addWidget(label("Histórico de mensalidades", "section"))
        self.root.addWidget(label(f"Total em aberto: {money(pending)}", "muted"))
        # Mantém a ficha utilizável mesmo em uma tela menor.
        scroller = QScrollArea()
        scroller.setWidgetResizable(True)
        table = self.owner.invoice_table(rows, compact=True, after=self.render)
        table.setMinimumHeight(120)
        scroller.setWidget(table)
        self.root.addWidget(scroller, 1)
        actions = QHBoxLayout()
        actions.addStretch()
        actions.addWidget(button("Fechar ficha", self.accept))
        self.root.addLayout(actions)

    def edit(self):
        dialog = MemberDialog(self.owner.store, self.owner.today, self, self.member_id)
        if exec_qt(dialog) == QDialog.Accepted:
            self.owner.refresh("Cadastro atualizado.")
            self.render()

    def toggle(self):
        member = self.owner.store.member(self.member_id)
        active = not bool(member["active"])
        message = ("O aluno voltará a ter mensalidades a partir do próximo vencimento. O período inativo não será cobrado."
                   if active else "Novas cobranças serão interrompidas. Pagamentos e mensalidades atrasadas ficam no histórico.")
        if confirm(self, "Reativar aluno" if active else "Desativar aluno", message,
                   "Reativar aluno" if active else "Desativar aluno"):
            self.owner.store.set_active(self.member_id, active, self.owner.today)
            self.owner.refresh("Situação do aluno atualizada.")
            self.render()

    def delete(self):
        member = self.owner.store.member(self.member_id)
        if confirm(self, "Excluir aluno", f"Excluir {member['name']} e todo o seu histórico de mensalidades?\n\n"
                   "Esta ação é definitiva. Para apenas interromper cobranças, use Desativar aluno.", "Excluir definitivamente", True):
            # Uma cópia permite recuperar exclusões acidentais pelo menu de dados.
            folder = self.owner.store.directory / "backups"
            folder.mkdir(exist_ok=True)
            self.owner.store.backup(folder / f"antes-de-excluir-{datetime.now():%Y%m%d-%H%M%S-%f}.sqlite3")
            self.owner.store.delete_member(self.member_id)
            self.owner.refresh("Aluno excluído. Uma cópia anterior à exclusão foi guardada.")
            self.accept()


class MainWindow(QMainWindow):
    def __init__(self, store, demo=False, today_provider=date.today):
        super().__init__()
        self.store, self.demo, self.today_provider = store, demo, today_provider
        self.settings = QSettings(str(store.directory / "preferencias.ini"), QSettings.IniFormat)
        saved_theme = self.settings.value("aparencia/tema", "light")
        self.theme_mode = saved_theme if saved_theme in THEMES else "light"
        apply_theme(QApplication.instance(), self.theme_mode)
        self.today = today_provider()
        self.page = "home"
        self.cards_layout = None
        self.cards = []
        self.member_search = ""
        self.member_activity = "active"
        self.invoice_search = ""
        self.invoice_filter = "open"
        self.store.refresh(self.today)
        self.setWindowTitle("Power Academia")
        self.setWindowIcon(QIcon(str(ASSETS / "douglas.png")))
        self.resize(1360, 900)
        self.setMinimumSize(980, 640)
        shell = QWidget()
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        sidebar = panel("Sidebar")
        sidebar.setFixedWidth(230)
        side = vbox(sidebar, 20, 9)
        portrait = QLabel()
        portrait.setPixmap(QPixmap(str(ASSETS / "douglas.png")).scaled(112, 112, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        portrait.setAlignment(Qt.AlignCenter)
        side.addSpacing(14)
        side.addWidget(portrait)
        brand = label("POWER")
        brand.setObjectName("BrandTitle")
        brand.setAlignment(Qt.AlignCenter)
        side.addWidget(brand)
        sub = label("A C A D E M I A")
        sub.setObjectName("BrandSub")
        sub.setAlignment(Qt.AlignCenter)
        side.addWidget(sub)
        side.addSpacing(25)
        menu = label("DIA A DIA", "muted")
        menu.setObjectName("MenuCaption")
        side.addWidget(menu)
        self.nav = {}
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        for key, text, symbol in [("home", "Visão geral", "home"), ("members", "Alunos", "users"),
                                  ("invoices", "Mensalidades", "wallet"), ("data", "Dados e backup", "backup")]:
            nav = button(text, lambda checked=False, k=key: self.open_page(k), "nav", symbol)
            nav.setCheckable(True)
            self.nav_group.addButton(nav)
            self.nav[key] = nav
            side.addWidget(nav)
        side.addSpacing(14)
        separator = QFrame()
        separator.setObjectName("SideSeparator")
        side.addWidget(separator)
        theme_row = QHBoxLayout()
        theme_row.setSpacing(8)
        self.theme_buttons = {}
        self.theme_group = QButtonGroup(self)
        self.theme_group.setExclusive(True)
        for mode, text, symbol in [("light", "Claro", "sun"), ("dark", "Escuro", "moon")]:
            control = button(text, lambda checked=False, m=mode: self.set_theme(m), "theme", symbol)
            control.setObjectName(f"theme_{mode}")
            control.setCheckable(True)
            control.setChecked(mode == self.theme_mode)
            control.setToolTip("Usar tema " + ("claro" if mode == "light" else "escuro"))
            control.setAccessibleName("Tema claro" if mode == "light" else "Tema escuro")
            self.theme_group.addButton(control)
            self.theme_buttons[mode] = control
            theme_row.addWidget(control, 1)
        side.addLayout(theme_row)
        side.addStretch()
        shell_layout.addWidget(sidebar)
        self.scroller = QScrollArea()
        self.scroller.setWidgetResizable(True)
        self.content = QWidget()
        self.content.setObjectName("MainContent")
        self.body = vbox(self.content, 30, 22)
        self.scroller.setWidget(self.content)
        shell_layout.addWidget(self.scroller, 1)
        self.setCentralWidget(shell)
        self.statusBar().messageChanged.connect(lambda text: self.statusBar().setVisible(bool(text)))
        self.statusBar().hide()
        self.open_page("home")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_day)
        self.timer.start(60_000)

    def set_theme(self, mode):
        if mode not in THEMES:
            return
        self.theme_mode = mode
        self.settings.setValue("aparencia/tema", mode)
        self.settings.sync()
        apply_theme(QApplication.instance(), mode)
        self.theme_buttons[mode].setChecked(True)
        refresh_icons(self)
        for field in self.findChildren(QLineEdit):
            for action in field.actions():
                if action.property("symbol"):
                    action.setIcon(icon(action.property("symbol")))

    def check_day(self):
        if self.today_provider() != self.today:
            self.today = self.today_provider()
            self.refresh()

    def refresh(self, message=""):
        self.today = self.today_provider()
        self.store.refresh(self.today)
        self.store.automatic_backup(self.today)
        self.open_page(self.page)
        if message:
            self.statusBar().showMessage(message, 12000)

    def open_page(self, page):
        self.page = page
        self.cards_layout = None
        self.cards = []
        clear(self.body)
        self.nav[page].setChecked(True)
        top = QHBoxLayout()
        top.addWidget(label("SUA ACADEMIA, EM DIA", "eyebrow"))
        top.addStretch()
        top.addWidget(label(f"{self.today.day:02d} de {MONTHS[self.today.month]} de {self.today.year}", "muted"))
        self.body.addLayout(top)
        titles = {
            "home": ("Visão geral", "Um olhar rápido para o que precisa da sua atenção."),
            "members": ("Seus alunos", "Cadastre, encontre e acompanhe cada aluno da academia."),
            "invoices": ("Mensalidades", "Saiba quem já pagou e quais mensalidades estão em aberto."),
            "data": ("Dados e backup", "Seus cadastros e pagamentos, sempre com você."),
        }
        title, subtitle = titles[page]
        heading = QHBoxLayout()
        words = QVBoxLayout()
        words.setSpacing(5)
        words.addWidget(label(title, "title"))
        words.addWidget(label(subtitle, "muted", True))
        heading.addLayout(words, 1)
        if page in ("home", "members"):
            heading.addWidget(button("Cadastrar aluno", self.add_member, "primary", "plus"))
        self.body.addLayout(heading)
        {"home": self.build_home, "members": self.build_members,
         "invoices": self.build_invoices, "data": self.build_data}[page]()
        self.body.addStretch()
        refresh_icons(self)
        self.scroller.verticalScrollBar().setValue(0)

    def add_member(self):
        dialog = MemberDialog(self.store, self.today, self)
        if exec_qt(dialog) == QDialog.Accepted:
            self.refresh("Aluno cadastrado. As mensalidades já estão disponíveis.")

    def show_member(self, member_id):
        exec_qt(MemberProfile(self, member_id))

    def build_home(self):
        summary = self.store.summary(self.today)
        welcome = panel("Welcome")
        line = QHBoxLayout(welcome)
        line.setContentsMargins(24, 22, 24, 22)
        words = QVBoxLayout()
        words.setSpacing(9)
        greeting = "Bom dia" if datetime.now().hour < 12 else "Boa tarde" if datetime.now().hour < 18 else "Boa noite"
        hi = label(f"{greeting}, Douglas.")
        hi.setObjectName("WelcomeTitle")
        words.addWidget(hi)
        attention = summary["late_count"] + summary["today_count"]
        words.addWidget(label(f"Você tem {attention} mensalidade{'s' if attention != 1 else ''} em atraso ou vencendo hoje."
                              if attention else "Tudo em dia por aqui. Confira os próximos vencimentos abaixo.", "muted", True))
        line.addLayout(words, 1)
        line.addWidget(button("Ver mensalidades", lambda: self.open_page("invoices"), symbol="arrow"))
        self.body.addWidget(welcome)
        cards = QGridLayout()
        cards.setSpacing(14)
        self.cards_layout = cards
        self.cards = []
        for title, value, detail, tone, symbol, target in [
            ("Alunos ativos", str(summary["active"]), "matrículas em andamento", "neutral", "users", "members"),
            ("Em atraso", money(summary["late"]), f'{summary["late_count"]} mensalidade(s)', "late", "alert", "late"),
            ("Vence hoje", money(summary["today"]), f'{summary["today_count"]} mensalidade(s)', "today", "calendar", "today"),
            ("Próximos 7 dias", money(summary["soon"]), f'{summary["soon_count"]} mensalidade(s)', "neutral", "clock", "soon"),
        ]:
            card = panel("Card")
            card.setProperty("tone", tone)
            card.setMinimumWidth(195)
            inside = vbox(card, 18, 10)
            title_line = QHBoxLayout()
            title_line.addWidget(label(title, "cardtitle"), 1)
            glyph = QLabel()
            glyph.setProperty("symbol", symbol)
            glyph.setProperty("iconTone", "danger" if tone == "late" else "icon")
            glyph.setPixmap(icon(symbol, colors()[glyph.property("iconTone")], 20).pixmap(20, 20))
            title_line.addWidget(glyph)
            inside.addLayout(title_line)
            inside.addWidget(label(value, "metric"))
            inside.addWidget(label(detail, "muted"))
            inside.addWidget(button("Ver alunos  →" if target == "members" else "Ver mensalidades  →",
                                     lambda checked=False, t=target: self.card_click(t), "link"))
            self.cards.append(card)
        self.arrange_cards()
        self.body.addLayout(cards)
        received = panel("Received")
        strip = QHBoxLayout(received)
        strip.setContentsMargins(18, 13, 18, 13)
        strip.addWidget(label("✓  Recebido neste mês"))
        strip.addStretch()
        total = label(money(summary["received"]))
        total.setObjectName("ReceivedTotal")
        strip.addWidget(total)
        self.body.addWidget(received)
        area = panel()
        layout = vbox(area, 0, 0)
        heading = QHBoxLayout()
        heading.setContentsMargins(20, 18, 20, 18)
        heading.addWidget(label("Mensalidades que pedem atenção", "section"), 1)
        heading.addWidget(button("Ver todas  →", lambda: self.open_page("invoices"), "link"))
        layout.addLayout(heading)
        rows = [row for row in self.store.invoices(self.today) if row["status"] in ("late", "today", "soon")]
        if rows:
            layout.addWidget(self.invoice_table(rows[:8]))
        else:
            layout.addWidget(self.empty("Nenhuma mensalidade precisa de atenção.", "Os próximos vencimentos aparecerão aqui automaticamente."))
        self.body.addWidget(area)

    def arrange_cards(self):
        if not self.cards_layout:
            return
        columns = 4 if self.width() >= 1200 else 2
        for i, card in enumerate(self.cards):
            self.cards_layout.addWidget(card, i // columns, i % columns)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.arrange_cards()

    def card_click(self, target):
        if target == "members":
            self.open_page("members")
        else:
            self.invoice_filter = target
            self.open_page("invoices")

    def empty(self, title, subtitle):
        widget = QWidget()
        layout = vbox(widget, 30, 10)
        main = label(title, "section", True)
        main.setAlignment(Qt.AlignCenter)
        sub = label(subtitle, "muted", True)
        sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(main)
        layout.addWidget(sub)
        return widget

    def invoice_table(self, rows, compact=False, after=None):
        headers = ["Referência", "Vencimento", "Valor", "Situação", ""] if compact else ["Aluno / referência", "Vencimento", "Valor", "Situação", ""]
        table = make_table(headers, [0, 125, 130, 160, 150], len(rows))
        for r, item in enumerate(rows):
            cell(table, r, 0, month_label(item["month"]) if compact else item["name"], True,
                 item["name"] + " · " + month_label(item["month"]))
            if not compact:
                table.takeItem(r, 0)
                info = QWidget()
                lines = vbox(info, 0, 3)
                lines.setContentsMargins(12, 8, 8, 8)
                lines.addWidget(label(item["name"]))
                lines.addWidget(label(month_label(item["month"]), "muted"))
                table.setCellWidget(r, 0, info)
            cell(table, r, 1, date.fromisoformat(item["due_on"]).strftime("%d/%m/%Y"), tooltip=status_detail(item, self.today))
            cell(table, r, 2, money(item["amount_cents"]), True)
            cell_widget(table, r, 3, badge("Em atraso" if item["status"] == "late" else "Vence hoje" if item["status"] == "today"
                                         else "Pago" if item["status"] == "paid" else "Em breve" if item["status"] == "soon" else "A vencer", item["status"]))
            if item["paid_on"]:
                control = button("Desfazer", lambda checked=False, i=item["id"]: self.undo_payment(i, after), "link")
                control.setToolTip(status_detail(item, self.today) + " · " + item["payment_method"])
            else:
                control = button("Receber", lambda checked=False, i=item["id"]: self.receive(i, after), "receive", "check")
                control.setToolTip("Registrar o recebimento de " + money(item["amount_cents"]))
            cell_widget(table, r, 4, control)
        if not compact:
            table.cellDoubleClicked.connect(lambda row, col: self.show_member(rows[row]["member_id"]))
        return table

    def receive(self, invoice_id, after=None):
        invoice = self.store.invoice(invoice_id)
        dialog = PaymentDialog(invoice, self.today, self)
        if exec_qt(dialog) == QDialog.Accepted:
            self.store.pay(invoice_id, dialog.paid_on.date().toPython(), dialog.method.currentText(), self.today)
            self.refresh("Pagamento registrado com sucesso.")
            if after:
                after()

    def undo_payment(self, invoice_id, after=None):
        invoice = self.store.invoice(invoice_id)
        if confirm(self, "Desfazer recebimento", f"Desfazer o pagamento de {money(invoice['amount_cents'])} de {invoice['name']}?\n\n"
                   "A mensalidade voltará a aparecer em aberto.", "Desfazer recebimento"):
            self.store.undo_payment(invoice_id)
            self.refresh("Recebimento desfeito. A mensalidade está em aberto.")
            if after:
                after()

    def search_input(self, text, placeholder):
        field = QLineEdit(text)
        field.setPlaceholderText(placeholder)
        field.setClearButtonEnabled(True)
        action = field.addAction(icon("search"), QLineEdit.LeadingPosition)
        action.setProperty("symbol", "search")
        field.setMinimumWidth(230)
        return field

    def build_members(self):
        bar = QHBoxLayout()
        self.search_members = self.search_input(self.member_search, "Buscar aluno por nome ou telefone")
        self.search_members.setObjectName("searchMembers")
        self.search_members.textChanged.connect(self.filter_members)
        bar.addWidget(self.search_members, 1)
        self.activity = QComboBox()
        for text, value in [("Alunos ativos", "active"), ("Alunos inativos", "inactive"), ("Todos os alunos", "all")]:
            self.activity.addItem(text, value)
        self.activity.setCurrentIndex(self.activity.findData(self.member_activity))
        self.activity.currentIndexChanged.connect(self.filter_members)
        bar.addWidget(self.activity)
        bar.addWidget(button("Exportar Excel", self.export_members, symbol="export"))
        self.body.addLayout(bar)
        self.member_results = QWidget()
        self.member_result_layout = vbox(self.member_results)
        self.body.addWidget(self.member_results)
        self.update_member_results()

    def filter_members(self, *_):
        self.member_search = self.search_members.text()
        self.member_activity = self.activity.currentData()
        self.update_member_results()

    def update_member_results(self):
        clear(self.member_result_layout)
        rows = self.store.members(self.member_search, self.member_activity)
        self.member_result_layout.addWidget(label(f"{len(rows)} aluno(s) encontrado(s). Clique em Ver ficha para editar ou consultar o histórico.", "muted", True))
        if not rows:
            self.member_result_layout.addWidget(self.empty("Nenhum aluno encontrado.", "Cadastre seu primeiro aluno ou tente outra busca."))
            return
        area = panel()
        layout = vbox(area)
        table = make_table(["Aluno", "Telefone", "Mensalidade", "Vencimento", "Situação", ""], [0, 160, 130, 120, 110, 130], len(rows))
        table.setObjectName("membersTable")
        for r, item in enumerate(rows):
            cell(table, r, 0, item["name"], True, item["name"])
            cell(table, r, 1, item["phone"] or "—")
            cell(table, r, 2, money(item["monthly_cents"]),
                 tooltip="Mensalidade básica" if item["fee_type"] == "basic" else "Valor personalizado")
            cell(table, r, 3, f"Todo dia {item['due_day']:02d}")
            cell_widget(table, r, 4, badge("Ativo" if item["active"] else "Inativo", "active" if item["active"] else "inactive"))
            cell_widget(table, r, 5, button("Ver ficha", lambda checked=False, i=item["id"]: self.show_member(i), "link"))
        table.cellDoubleClicked.connect(lambda r, col: self.show_member(rows[r]["id"]))
        layout.addWidget(table)
        self.member_result_layout.addWidget(area)

    def build_invoices(self):
        settings = panel()
        settings_layout = vbox(settings, 20, 10)
        settings_layout.addWidget(label("Mensalidade básica", "section"))
        settings_layout.addWidget(label("Ao atualizar, o novo valor vale para todos os alunos com mensalidade básica, "
                                        "nas cobranças de hoje em diante. Mensalidades pagas ou já vencidas mantêm o valor anterior.", "muted", True))
        amount_label = label("Valor da mensalidade (R$)", "field")
        settings_layout.addWidget(amount_label)
        row = QHBoxLayout()
        cents = self.store.basic_monthly_cents()
        self.basic_amount = QLineEdit(f"{cents / 100:.2f}".replace(".", ",") if cents is not None else "")
        self.basic_amount.setObjectName("basicMonthlyAmount")
        self.basic_amount.setPlaceholderText("Ex.: 150,00")
        self.basic_amount.setMaxLength(12)
        self.basic_amount.setMaximumWidth(230)
        amount_label.setBuddy(self.basic_amount)
        row.addWidget(self.basic_amount)
        self.update_basic_button = button("Atualizar", self.update_basic_fee, "primary", "check")
        self.update_basic_button.setObjectName("updateBasicMonthlyAmount")
        row.addWidget(self.update_basic_button)
        row.addStretch()
        settings_layout.addLayout(row)
        self.basic_message = label("", "error", True)
        self.basic_message.hide()
        settings_layout.addWidget(self.basic_message)
        if cents is None:
            settings_layout.addWidget(label("Defina o valor básico para usá-lo no cadastro de novos alunos.", "muted", True))
        self.body.addWidget(settings)
        self.filter_buttons = {}
        filters = QHBoxLayout()
        filters.setSpacing(4)
        self.filters_group = QButtonGroup(self)
        for text, state in [("Em aberto", "open"), ("Em atraso", "late"), ("Vence hoje", "today"),
                            ("Próximos 7 dias", "soon"), ("Pagas", "paid"), ("Todas", "all")]:
            item = button(text, lambda checked=False, s=state: self.set_invoice_filter(s), "filter")
            item.setCheckable(True)
            item.setChecked(state == self.invoice_filter)
            self.filters_group.addButton(item)
            self.filter_buttons[state] = item
            filters.addWidget(item)
        filters.addStretch()
        self.body.addLayout(filters)
        tools = QHBoxLayout()
        self.search_invoices = self.search_input(self.invoice_search, "Buscar mensalidades por aluno")
        self.search_invoices.textChanged.connect(self.filter_invoices)
        tools.addWidget(self.search_invoices, 1)
        tools.addWidget(button("Atualizar lista", lambda: self.refresh("Mensalidades atualizadas."), symbol="refresh"))
        tools.addWidget(button("Exportar Excel", self.export_invoices, symbol="export"))
        self.body.addLayout(tools)
        self.invoice_results = QWidget()
        self.invoice_result_layout = vbox(self.invoice_results)
        self.body.addWidget(self.invoice_results)
        self.update_invoice_results()
        self.body.addWidget(label("As mensalidades são criadas automaticamente. Próximos 7 dias inclui de amanhã até o 7º dia; hoje tem um filtro próprio.", "muted", True))

    def update_basic_fee(self):
        try:
            cents = parse_money(self.basic_amount.text())
            self.store.set_basic_monthly_cents(cents, self.today_provider())
        except (ValueError, OSError) as exc:
            self.basic_message.setText(str(exc))
            self.basic_message.show()
            return
        self.refresh(f"Mensalidade básica atualizada para {money(cents)} em todos os alunos vinculados.")

    def set_invoice_filter(self, state):
        self.invoice_filter = state
        self.update_invoice_results()

    def filter_invoices(self, text):
        self.invoice_search = text
        self.update_invoice_results()

    def update_invoice_results(self):
        clear(self.invoice_result_layout)
        rows = self.store.invoices(self.today, self.invoice_filter, self.invoice_search)
        total = sum(row["amount_cents"] for row in rows)
        self.invoice_result_layout.addWidget(label(f"{len(rows)} mensalidade(s)  •  Total da seleção: {money(total)}", "section"))
        area = panel()
        layout = vbox(area)
        if rows:
            layout.addWidget(self.invoice_table(rows))
        else:
            layout.addWidget(self.empty("Nenhuma mensalidade nesta seleção.", "Escolha outro filtro ou busque por outro aluno."))
        self.invoice_result_layout.addWidget(area)

    def build_data(self):
        for title, detail, action, callback, symbol in [
            ("Guardar uma cópia de segurança", "Salva todos os alunos e o histórico de pagamentos em um único arquivo.", "Salvar backup", self.save_backup, "backup"),
            ("Recuperar uma cópia de segurança", "Substitui os dados atuais pelos de uma cópia anterior. Antes, guardamos uma cópia dos dados atuais.", "Restaurar backup", self.restore_backup, "refresh"),
            ("Abrir no Excel", "Exporte a lista de alunos ou use os filtros em Mensalidades para exportar as cobranças desejadas.", "Exportar alunos", self.export_members, "export"),
        ]:
            area = panel()
            line = QHBoxLayout(area)
            line.setContentsMargins(24, 22, 24, 22)
            words = QVBoxLayout()
            words.setSpacing(8)
            words.addWidget(label(title, "section"))
            words.addWidget(label(detail, "muted", True))
            line.addLayout(words, 1)
            line.addSpacing(20)
            line.addWidget(button(action, callback, symbol=symbol))
            self.body.addWidget(area)
        area = panel()
        layout = vbox(area, 24)
        layout.addWidget(label("Onde estão meus dados?", "section"))
        layout.addWidget(label("Cópias automáticas diárias: as últimas 30 ficam na pasta backups.", "muted", True))
        path = label(str(self.store.directory), "muted", True)
        path.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(path)
        buttons = QHBoxLayout()
        buttons.addWidget(button("Abrir pasta dos dados", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.store.directory))), symbol="backup"))
        buttons.addStretch()
        layout.addLayout(buttons)
        self.body.addWidget(area)
        self.body.addWidget(label("Como usar: cadastre um aluno → confira as mensalidades → clique em Receber quando ele pagar. Para editar ou excluir, abra a ficha do aluno.", "muted", True))

    def save_backup(self):
        destination, _ = QFileDialog.getSaveFileName(self, "Guardar cópia de segurança", f"academia-backup-{self.today:%Y-%m-%d}.sqlite3", "Cópia da academia (*.sqlite3)")
        if destination:
            try:
                self.store.backup(destination)
                self.statusBar().showMessage("Cópia de segurança salva em " + destination, 20000)
                QMessageBox.information(self, "Cópia salva", "Sua cópia de segurança foi salva.\n\n" + destination)
            except (OSError, ValueError) as exc:
                error(self, exc)

    def restore_backup(self):
        source, _ = QFileDialog.getOpenFileName(self, "Escolher cópia de segurança", "", "Cópia da academia (*.sqlite3)")
        if source and confirm(self, "Restaurar cópia", "Os cadastros e pagamentos atuais serão substituídos pelo conteúdo da cópia escolhida.\n\n"
                              "Uma cópia dos dados atuais será guardada antes da restauração.", "Restaurar esta cópia", True):
            try:
                safety = self.store.restore(source)
                self.refresh("Cópia restaurada com sucesso.")
                QMessageBox.information(self, "Dados recuperados", "Cópia restaurada. Os dados que estavam aqui foram guardados em:\n\n" + str(safety))
            except (OSError, ValueError) as exc:
                error(self, exc)

    def export_members(self):
        destination, _ = QFileDialog.getSaveFileName(self, "Exportar alunos para Excel", "alunos-academia.csv", "Planilha para Excel (*.csv)")
        if destination:
            try:
                self.store.export_members(destination)
                self.statusBar().showMessage("Lista de todos os alunos exportada para " + destination, 20000)
            except OSError as exc:
                error(self, "Não foi possível salvar. Feche o arquivo no Excel e tente novamente.\n" + str(exc))

    def export_invoices(self):
        destination, _ = QFileDialog.getSaveFileName(self, "Exportar mensalidades para Excel", "mensalidades-academia.csv", "Planilha para Excel (*.csv)")
        if destination:
            try:
                self.store.export_invoices(destination, self.store.invoices(self.today, self.invoice_filter, self.invoice_search), self.today)
                self.statusBar().showMessage("Mensalidades da seleção exportadas para " + destination, 20000)
            except OSError as exc:
                error(self, "Não foi possível salvar. Feche o arquivo no Excel e tente novamente.\n" + str(exc))

    def closeEvent(self, event):
        try:
            self.store.automatic_backup(self.today)
        except OSError:
            # O banco principal já foi gravado; um backup sem espaço não impede fechar.
            pass
        event.accept()
