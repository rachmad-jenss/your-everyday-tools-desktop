# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

# Paths relative to this .spec file
ROOT = os.path.abspath(os.path.dirname(SPECPATH)) if 'SPECPATH' in dir() else os.path.abspath('.')

# Platform-specific settings
is_win = sys.platform == 'win32'
is_mac = sys.platform == 'darwin'

a = Analysis(
    ['app.py'],
    pathex=[ROOT],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('utils', 'utils'),
        ('routes', 'routes'),
        ('images', 'images'),
        ('vendor/ffmpeg', 'vendor/ffmpeg'),
        ('vendor/tesseract', 'vendor/tesseract'),
    ],
    hiddenimports=[
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
        'routes._helpers',
        # Utils
        'utils.file_utils',
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
        'pytesseract',
        'ezdxf',
        'ezdxf.addons',
        'ezdxf.addons.drawing',
        'ezdxf.addons.drawing.matplotlib',
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends',
        'matplotlib.backends.backend_agg',
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
        'img2pdf',
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
