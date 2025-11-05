# tools/repair_health_anchor.py
import re
from pathlib import Path

p = Path("api/server.py")  # run from your scripts\tbcv root
src = p.read_text(encoding="utf-8")

changed = False

# 1) Fix the broken call: turn "FastAPI\n(" back into "FastAPI("
if "FastAPI\n(" in src:
    src = src.replace("FastAPI\n(", "FastAPI(")
    changed = True

# 2) Remove the previously inserted top-level health block if present
#    (the one that starts with this marker)
marker = "\n# --- Strict health endpoints: live vs ready (DB required) ---"
if marker in src:
    # Greedy remove of that whole block until the first blank line after health()
    pattern = (
        r"\n# --- Strict health endpoints: live vs ready \(DB required\) ---"
        r".*?@app\.get\('/health'\).*?def health\(response: Response\):"
        r".*?return health_ready\(response\)\n"
    )
    src2 = re.sub(pattern, "\n", src, flags=re.S)
    if src2 != src:
        src = src2
        changed = True

if changed:
    p.write_text(src, encoding="utf-8")
    print("Repaired server.py")
else:
    print("No repair needed")
