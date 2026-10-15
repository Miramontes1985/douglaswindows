"""Entrada do aplicativo. Execute python main.py --demo para experimentar."""
from __future__ import annotations

import argparse
import os
import logging
import sys
import tempfile
from pathlib import Path
from datetime import date

from academia.qt import BINDING, exec_qt, Qt, QCoreApplication, QLocale, QLockFile, QTimer
from academia.qt import QApplication, QMessageBox

from academia.storage import Store, data_directory
from academia.theme import apply_theme
from academia.ui import MainWindow


def main():
    parser = argparse.ArgumentParser(description="Power Academia — gestão local de alunos e mensalidades")
    parser.add_argument("--data-dir", type=Path, help="Pasta alternativa para os dados locais")
    parser.add_argument("--demo", action="store_true", help="Abrir com dados fictícios em uma pasta temporária")
    parser.add_argument("--self-test", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.self_test:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if BINDING == "PySide2":
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv[:1])
    app.setApplicationName("Power Academia")
    app.setOrganizationName("Power Academia")
    QLocale.setDefault(QLocale("pt_BR"))
    apply_theme(app)
    temporary = tempfile.TemporaryDirectory(prefix="power-academia-demo-") if args.demo or args.self_test else None
    directory = Path(temporary.name) if temporary else (args.data_dir or data_directory())
    store = None
    lock = None
    try:
        directory.mkdir(parents=True, exist_ok=True)
        lock = QLockFile(str(directory / "academia.lock"))
        lock.setStaleLockTime(60_000)
        if not lock.tryLock(100):
            QMessageBox.information(None, "Power Academia", "O aplicativo já está aberto com estes dados.\n\nUse a janela que já está aberta.")
            return 0
        logging.basicConfig(filename=str(directory / "academia.log"), level=logging.ERROR,
                            format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8")

        def report_exception(kind, value, traceback):
            logging.error("Erro ao executar uma ação", exc_info=(kind, value, traceback))
            QMessageBox.warning(None, "Não foi possível concluir", "Não foi possível concluir esta ação.\n\n"
                                "Feche e abra o aplicativo e tente novamente. Se o problema continuar, consulte o arquivo academia.log na pasta dos dados.")
        sys.excepthook = report_exception
        store = Store(directory)
        if args.demo:
            from academia.demo import seed_demo
            seed_demo(store, date.today())
        store.automatic_backup(date.today())
        window = MainWindow(store, demo=args.demo)
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PowerAcademia.Desktop.1")
        window.show()
        if args.self_test:
            from academia.diagnostics import verify_packaged_app
            QTimer.singleShot(0, lambda: app.exit(verify_packaged_app(window, args.self_test)))
        return exec_qt(app)
    except Exception as exc:
        logging.exception("Falha ao abrir o aplicativo")
        QMessageBox.critical(None, "Não foi possível abrir", "Não foi possível abrir os dados da academia.\n\n"
                             "Confira se a pasta está disponível e se há espaço no computador.\n\n" + str(exc))
        return 1
    finally:
        if store:
            store.close()
        if lock:
            lock.unlock()
        # No Windows, o arquivo de log aberto impede remover a pasta temporária.
        logging.shutdown()
        if temporary:
            temporary.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
