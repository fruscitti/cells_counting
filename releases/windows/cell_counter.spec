# releases/windows/cell_counter.spec
# PyInstaller spec for Cell Counter Windows build
# Run from repo root:
#   pyinstaller releases/windows/cell_counter.spec --distpath releases/dist --workpath releases/build
#
# Uses collect_all('PySide6') to ensure platforms/qwindows.dll is included (avoids qt.qpa.plugin crash).

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = [], [], []

# Collect all PySide6 plugin data (includes platforms/ folder with qwindows.dll)
tmp_ret = collect_all('PySide6')
datas        += tmp_ret[0]
binaries     += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Additional hidden imports for OpenCV, NumPy, pandas
hiddenimports += ['cv2', 'numpy', 'pandas']

a = Analysis(
    ['../../app.py'],
    pathex=['../..'],
    binaries=binaries,
    datas=datas + [('../../icon.png', '.')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CellCounter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # no console window for end users
    icon='../../icon.png',   # Pillow auto-converts PNG to .ico at build time
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CellCounter',      # output directory: releases/dist/CellCounter/
)
