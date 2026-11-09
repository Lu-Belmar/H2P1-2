# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [("core/templates", "core/templates"), ("staticfiles", "staticfiles")]
binaries = []
hiddenimports = [
    "webview", "tkinter", "whitenoise.middleware", "whitenoise.storage",
    "django.contrib.sessions.backends.signed_cookies", "openpyxl", "pandas",
    "core.apps", "core.urls", "pythonnet", "clr"
]


pn_datas, pn_binaries, pn_hidden = collect_all('pythonnet')
datas += pn_datas
binaries += pn_binaries
hiddenimports += pn_hidden

cl_datas, cl_binaries, cl_hidden = collect_all('clr_loader')
datas += cl_datas
binaries += cl_binaries
hiddenimports += cl_hidden

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[('core/templates', 'core/templates'), ('staticfiles', 'staticfiles')],
    hiddenimports=['webview', 'tkinter', 'whitenoise.middleware', 'whitenoise.storage', 'django.contrib.sessions.backends.signed_cookies', 'openpyxl', 'pandas', 'core.apps', 'core.urls'],
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
    name='GestionCMF',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GestionCMF',
)
