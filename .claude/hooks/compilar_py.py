import json
import py_compile
import sys
import tempfile
from pathlib import Path

ruta = json.load(sys.stdin).get("tool_input", {}).get("file_path", "")
if ruta.endswith(".py") and Path(ruta).is_file():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            py_compile.compile(ruta, cfile=str(Path(tmp) / "x.pyc"), doraise=True)
        except py_compile.PyCompileError as error:
            print(error.msg, file=sys.stderr)
            sys.exit(2)
