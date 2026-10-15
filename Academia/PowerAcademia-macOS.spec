"""Pacote nativo para testar a Power Academia no macOS."""
import platform
import sysconfig
from pathlib import Path

root = Path(SPECPATH)
minimum_system = max(
    ["12.0", sysconfig.get_config_var("MACOSX_DEPLOYMENT_TARGET") or "12.0"],
    key=lambda value: tuple(int(part) for part in value.split(".")),
)
a = Analysis(
    [str(root / "main.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[(str(root / "assets"), "assets"),
           (str(root / "LEIA-ME.txt"), "."),
           (str(root / "licenses"), "licenses")],
    hiddenimports=["PySide6." + name for name in ("QtCore", "QtGui", "QtWidgets", "QtSvg")],
    hookspath=[], runtime_hooks=[],
    excludes=["tkinter", "PyQt5", "PyQt6", "PySide2"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name="PowerAcademia",
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=False, argv_emulation=False, target_arch=platform.machine(),
    codesign_identity=None, entitlements_file=None,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="PowerAcademia")
app = BUNDLE(
    coll,
    name="Power Academia.app",
    icon=str(root / "build" / "macos" / "PowerAcademia.icns"),
    bundle_identifier="br.poweracademia.desktop",
    info_plist={
        "CFBundleDisplayName": "Power Academia",
        "CFBundleName": "Power Academia",
        "CFBundleShortVersionString": "1.1.0",
        "CFBundleVersion": "1.1.0",
        "CFBundleDevelopmentRegion": "pt_BR",
        "CFBundleLocalizations": ["pt-BR"],
        "LSApplicationCategoryType": "public.app-category.business",
        "LSMinimumSystemVersion": minimum_system,
        "NSHighResolutionCapable": True,
    },
)
