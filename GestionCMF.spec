# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [("core/templates", "core/templates"), ("staticfiles", "staticfiles")]
binaries = []
hiddenimports = [
    "webview", "tkinter", "whitenoise.middleware", "whitenoise.storage",
    "django.contrib.sessions.backends.signed_cookies", "openpyxl", "pandas", "numpy",
    "core.apps", "core.urls", "pythonnet", "clr"
]

for pkg in ("pythonnet", "clr_loader"):
    p_datas, p_bins, p_hidden = collect_all(pkg)
    datas += p_datas
    binaries += p_bins
    hiddenimports += p_hidden

a = Analysis(
    ["run_app.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GestionCMF",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="GestionCMF",
)