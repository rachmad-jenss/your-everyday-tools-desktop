from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import threading
import time
import venv
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = ROOT / ".venv"
STATE_DIR = VENV_DIR / ".everytools"
CORE_REQ = ROOT / "requirements-core.txt"
OPTIONAL_REQ = ROOT / "requirements-optional.txt"
APP_URL = "http://localhost:5000"


def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def env() -> dict[str, str]:
    result = os.environ.copy()
    result["PYTHONNOUSERSITE"] = "1"
    result.setdefault("PIP_DISABLE_PIP_VERSION_CHECK", "1")
    return result


def run(cmd: list[str | Path], *, check: bool = True, log_file=None) -> subprocess.CompletedProcess:
    text_cmd = " ".join(str(part) for part in cmd)
    print(f"  > {text_cmd}")
    stdout = log_file if log_file else None
    stderr = subprocess.STDOUT if log_file else None
    proc = subprocess.run(
        [str(part) for part in cmd],
        cwd=ROOT,
        env=env(),
        stdout=stdout,
        stderr=stderr,
    )
    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, [str(part) for part in cmd])
    return proc


def file_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def stamp_path(name: str) -> Path:
    return STATE_DIR / f"{name}.sha256"


def stamp_matches(name: str, expected: str) -> bool:
    path = stamp_path(name)
    return path.exists() and path.read_text(encoding="utf-8").strip() == expected


def write_stamp(name: str, value: str) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    stamp_path(name).write_text(value + "\n", encoding="utf-8")


def check_python_version() -> None:
    if sys.version_info < (3, 10):
        print()
        print("  Python 3.10 or newer is required.")
        print(f"  Current Python: {sys.version.split()[0]}")
        raise SystemExit(1)


def create_venv() -> None:
    if venv_python().exists():
        return

    print()
    print("  First-time setup: creating a private .venv for EveryTools...")
    print("  This keeps the app away from broken global Python packages.")
    print()
    try:
        venv.EnvBuilder(with_pip=True, clear=False).create(VENV_DIR)
    except Exception as exc:
        print()
        print("  Could not create the virtual environment.")
        print("  On Linux, install the venv package first, for example:")
        print("      sudo apt install python3-venv")
        print()
        print(f"  Details: {exc}")
        raise SystemExit(1) from exc


def pip_install_core(*, force: bool = False) -> None:
    expected = file_hash([CORE_REQ])
    if not force and stamp_matches("core", expected):
        print("  Core Python dependencies are already installed.")
        return

    print()
    print("  Installing core Python dependencies...")
    print()
    py = venv_python()

    run([py, "-m", "ensurepip", "--upgrade"], check=False)
    run([py, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=False)

    # Remove the unrelated PyPI packages that can shadow PyMuPDF's `fitz`.
    run([py, "-m", "pip", "uninstall", "-y", "fitz", "frontend"], check=False)

    run([py, "-m", "pip", "install", "-r", CORE_REQ])
    write_stamp("core", expected)


def parse_requirements(path: Path) -> list[str]:
    requirements = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        requirements.append(line)
    return requirements


def pip_install_optional(*, force: bool = False) -> None:
    expected = file_hash([OPTIONAL_REQ])
    if not force and stamp_matches("optional", expected):
        print("  Optional Python packages were already attempted.")
        return

    requirements = parse_requirements(OPTIONAL_REQ)
    if not requirements:
        write_stamp("optional", expected)
        return

    print()
    print("  Installing optional Python packages best-effort...")
    print("  If one optional package fails, the app will still start.")
    print()

    log_path = STATE_DIR / "optional-install.log"
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    with log_path.open("w", encoding="utf-8") as log:
        for requirement in requirements:
            log.write(f"\n\n=== {requirement} ===\n")
            log.flush()
            proc = run(
                [venv_python(), "-m", "pip", "install", requirement],
                check=False,
                log_file=log,
            )
            if proc.returncode != 0:
                failures.append(requirement)
                print(f"    optional install skipped/failed: {requirement}")

    write_stamp("optional", expected)
    if failures:
        print()
        print("  Some optional packages could not be installed:")
        print("    " + ", ".join(failures))
        print(f"  Details were saved to: {log_path}")
        print("  The app will still run; affected tools will show install hints.")


def verify_core_imports() -> bool:
    code = (
        "import flask, PIL, fitz\n"
        "assert hasattr(fitz, 'open'), getattr(fitz, '__file__', 'unknown')\n"
    )
    proc = subprocess.run(
        [str(venv_python()), "-c", code],
        cwd=ROOT,
        env=env(),
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return True
    print(proc.stdout.strip())
    print(proc.stderr.strip())
    return False


def native_engine_note() -> None:
    try:
        from utils.capabilities import find_soffice
    except Exception:
        find_soffice = lambda: None

    missing = []
    if not find_soffice():
        missing.append("LibreOffice")
    if not shutil.which("ffmpeg"):
        missing.append("FFmpeg")
    if not shutil.which("tesseract"):
        missing.append("Tesseract")
    if not (shutil.which("ODAFileConverter") or shutil.which("oda_file_converter")):
        missing.append("ODA File Converter")

    if missing:
        print()
        print("  Optional native engines not detected:")
        print("    " + ", ".join(missing))
        print("  EveryTools will still start. The app shows install hints and uses")
        print("  these engines automatically when they are installed locally.")


def open_browser_later() -> None:
    time.sleep(2)
    webbrowser.open(APP_URL)


def start_app() -> int:
    print()
    print("  ============================================================")
    print(f"    EveryTools is starting at {APP_URL}")
    print("    Close this window or press Ctrl+C to stop the server.")
    print("  ============================================================")
    print()

    threading.Thread(target=open_browser_later, daemon=True).start()
    try:
        return subprocess.call([str(venv_python()), str(ROOT / "app.py")], cwd=ROOT, env=env())
    except KeyboardInterrupt:
        return 0


def main() -> int:
    repair = "--repair" in sys.argv
    check_python_version()
    create_venv()
    pip_install_core(force=repair)

    if not verify_core_imports():
        print()
        print("  Core dependency check failed. Repairing the virtual environment...")
        pip_install_core(force=True)
        if not verify_core_imports():
            print()
            print("  EveryTools could not install the required Python packages.")
            print("  Check your internet connection, then run the launcher again.")
            return 1

    pip_install_optional(force=repair)
    native_engine_note()
    return start_app()


if __name__ == "__main__":
    raise SystemExit(main())
