import sys
import os
import traceback

try:
    with open(os.path.join(os.environ.get("TEMP", "."), "yet-boot.log"), "w") as f:
        f.write(f"Python: {sys.version}\n")
        f.write(f"Frozen: {getattr(sys, 'frozen', False)}\n")
        f.write(f"MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}\n")
        f.write(f"argv: {sys.argv}\n")
        f.write(f"cwd: {os.getcwd()}\n")
        try:
            import app
            f.write("app.py imported OK\n")
            f.write(f"Blueprints: {list(app.app.blueprints.keys())}\n")
        except Exception as e:
            f.write(f"Import error: {e}\n")
            traceback.print_exc(file=f)
except Exception as e:
    print(f"Fatal: {e}", file=sys.stderr)
