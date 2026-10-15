# Use o Python da arquitetura desejada e POWER_ACADEMIA_ARCH=x86/x64.
import os
import struct
from pathlib import Path

root = Path(SPECPATH)
architecture = os.environ.get("POWER_ACADEMIA_ARCH", "x64" if struct.calcsize("P") == 8 else "x86")
expected_bits = 64 if architecture == "x64" else 32
if architecture not in ("x86", "x64") or struct.calcsize("P") * 8 != expected_bits:
    raise ValueError("A arquitetura do Python precisa corresponder ao pacote solicitado.")
binding = "PySide2" if architecture == "x86" else "PySide6"
a = Analysis(
    [str(root / "main.py")],
    pathex=[str(root)], binaries=[],
    datas=[(str(root / "assets"), "assets"), (str(root / "LEIA-ME.txt"), "."), (str(root / "licenses"), "licenses")],
    hiddenimports=[binding + "." + name for name in ("QtCore", "QtGui", "QtWidgets", "QtSvg")],
    hookspath=[], runtime_hooks=[],
    excludes=["tkinter", "PyQt5", "PyQt6", "PySide6" if binding == "PySide2" else "PySide2"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="PowerAcademia",
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, icon=str(root / "assets" / "app.ico"))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="PowerAcademia")
