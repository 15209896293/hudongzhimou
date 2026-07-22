# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('models', 'models'), ('data', 'data'), ('assets', 'assets')]
binaries = []
hiddenimports = ['PyQt5.sip', 'PyQt5.QtMultimedia', 'pyttsx3.drivers', 'pyttsx3.drivers.sapi5', 'onnxruntime', 'rtmlib', 'ui.stats_components', 'ui.stats_components.today_tab', 'ui.stats_components.week_tab', 'ui.stats_components.month_tab', 'ui.stats_components.goals_tab', 'ui.stats_components.base_components']
tmp_ret = collect_all('rtmlib')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
# Also collect onnxruntime data files (DLLs)
try:
    tmp_ret_ort = collect_all('onnxruntime')
    datas += tmp_ret_ort[0]; binaries += tmp_ret_ort[1]; hiddenimports += tmp_ret_ort[2]
except Exception:
    print("WARNING: Could not collect onnxruntime package data")


a = Analysis(
    ['run.py'],
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
    name='GoodGYM',
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
    icon=['assets\\Logo.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GoodGYM',
)
