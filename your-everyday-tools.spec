# -*- mode: python ; coding: utf-8 -*-
import sys
import os
import glob

from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Paths relative to this .spec file
ROOT = os.path.abspath(os.path.dirname(SPECPATH)) if 'SPECPATH' in dir() else os.path.abspath('.')

# Platform-specific settings
is_win = sys.platform == 'win32'
is_mac = sys.platform == 'darwin'

# ── Collect native binaries for small bundled deps ─────────────────────────
def _collect_dlls(base_dir, patterns, dest='.'):
    """Return list of (src_path, dest_subdir) tuples for PyInstaller binaries."""
    result = []
    for pattern in patterns:
        for p in glob.glob(os.path.join(base_dir, pattern)):
            result.append((p, dest))
    return result

_bundled_bins = []
_extra_datas = []
_extra_hidden = []

# pyzbar: libiconv.dll + libzbar-64.dll live inside the pyzbar package dir
try:
    import pyzbar as _pyzbar
    _pyzbar_dir = os.path.dirname(_pyzbar.__file__)
    _bundled_bins += _collect_dlls(_pyzbar_dir, ['*.dll'], dest='pyzbar')
    _d, _b, _h = collect_all('pyzbar')
    _extra_datas += _d
    _bundled_bins += _b
    _extra_hidden += _h
except ImportError:
    pass

# pillow-heif: libheif, libde265, libx265 live in site-packages root
try:
    import site as _site
    _site_dir = next(iter(_site.getsitepackages()), ROOT)
    _bundled_bins += _collect_dlls(_site_dir, ['libheif*.dll', 'libde265*.dll', 'libx265*.dll'])
    _bundled_bins += _collect_dlls(_site_dir, ['_pillow_heif*.pyd'])
    _d, _b, _h = collect_all('pillow_heif')
    _extra_datas += _d
    _bundled_bins += _b
    _extra_hidden += _h
except ImportError:
    pass

# pdf2docx needs cv2 (opencv) — PyInstaller often misses these without collect_all
for _pkg in ('pdf2docx', 'cv2', 'pdfplumber', 'matplotlib'):
    try:
        _d, _b, _h = collect_all(_pkg)
        _extra_datas += _d
        _bundled_bins += _b
        _extra_hidden += _h
    except Exception:
        pass
# ───────────────────────────────────────────────────────────────────────────

a = Analysis(
    ['app.py'],
    pathex=[ROOT],
    binaries=_bundled_bins,
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('utils', 'utils'),
        ('routes', 'routes'),
        ('images', 'images'),
        # vendor/ffmpeg and vendor/tesseract are NOT bundled —
        # they are downloaded on first run via the Electron downloader.
    ] + _extra_datas,
    hiddenimports=_extra_hidden + [
        # Route blueprints
        'routes.convert_tools',
        'routes.pdf_tools',
        'routes.image_tools',
        'routes.text_tools',
        'routes.calculator_tools',
        'routes.qr_tools',
        'routes.security_tools',
        'routes.spreadsheet_tools',
        'routes.dev_tools',
        'routes.archive_tools',
        'routes.media_tools',
        'routes.capabilities',
        'routes._helpers',
        # Utils
        'utils.file_utils',
        'utils.capabilities',
        'utils.pymupdf',
        # Core deps that PyInstaller often misses
        'PIL',
        'PIL._tkinter_finder',
        'fitz',
        'qrcode',
        'qrcode.image.pil',
        'markdown',
        'reportlab',
        'reportlab.graphics',
        'reportlab.lib.pagesizes',
        'reportlab.pdfgen.canvas',
        'svglib',
        'svglib.svglib',
        'docx',
        'openpyxl',
        'xlrd',
        'sqlparse',
        'croniter',
        'jsonpath_ng',
        'jsonpath_ng.ext',
        'barcode',
        'barcode.codex',
        'barcode.ean',
        'barcode.upc',
        # PowerPoint support
        'pptx',
        'pptx.util',
        # Optional deps (re-included after img2pdf fix)
        'pdf2docx',
        'pdfplumber',
        'img2pdf',
        'cv2',
        'numpy',
        'numpy.core',
        'pytesseract',
        'ezdxf',
        'ezdxf.addons',
        'ezdxf.addons.drawing',
        'ezdxf.addons.drawing.matplotlib',
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends',
        'matplotlib.backends.backend_agg',
        # Bundled small deps (now always included)
        'pyzbar',
        'pyzbar.pyzbar',
        'pyzbar.libraries',
        'pillow_heif',
        # cryptography — needed by Encrypt/Decrypt File tools
        'cryptography',
        'cryptography.hazmat',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.primitives.ciphers',
        'cryptography.hazmat.primitives.ciphers.algorithms',
        'cryptography.hazmat.primitives.ciphers.modes',
        'cryptography.hazmat.primitives.kdf.pbkdf2',
        'cryptography.hazmat.primitives.hashes',
        'cryptography.hazmat.primitives.padding',
        'cryptography.hazmat.backends',
        'cryptography.hazmat.backends.openssl',
        # WSGI server
        'waitress',
        # Jinja2 / Flask internals
        'jinja2',
        'jinja2.ext',
        'markupsafe',
        'flask.json',
        'werkzeug',
        'werkzeug.serving',
        'email.mime.text',
        # jaraco.text — pkg_resources imports this at startup (line 90).
        # PyInstaller detects it automatically via the pyi_rth_pkgres hook,
        # but listing it explicitly ensures it's always included.
        'jaraco.text',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy optional deps to keep the bundle small
        'rembg',
        'onnxruntime',
        'onnxruntime_gpu',
        'tensorflow',
        'torch',
        'torchvision',
        'torchaudio',
        'numpy.distutils',
        'tkinter',
        '_tkinter',
        'unittest',
        'test',
        'setuptools',
        'pip',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='YourEverydayTools',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='images/icon.ico' if is_win and os.path.exists('images/icon.ico') else
         'images/icon.icns' if is_mac and os.path.exists('images/icon.icns') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='YourEverydayTools',
)

if is_mac:
    app_bundle = BUNDLE(
        exe,
        name='YourEverydayTools.app',
        icon='images/icon.icns' if os.path.exists('images/icon.icns') else None,
        bundle_identifier='com.youreverydaytools.desktop',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleName': 'Your Everyday Tools',
            'NSHighResolutionCapable': True,
        },
    )
