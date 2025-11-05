#!/usr/bin/env python3
# Deterministic anchor-patch applier.
import json, sys, os, glob
from pathlib import Path

def apply_patch(root: Path, patch_file: Path, report: list):
    p = json.loads(patch_file.read_text(encoding="utf-8"))
    file_rel = p["file"]
    target = root / file_rel
    if not target.exists():
        report.append({"change_id": p.get("change_id"), "file": file_rel, "status": "error", "reason": "file_not_found"})
        return
    txt = target.read_text(encoding="utf-8", errors="ignore")
    anchor = p["anchor"]["find"]
    where = p["anchor"].get("where","after")
    idx = txt.find(anchor)
    if idx < 0:
        report.append({"change_id": p.get("change_id"), "file": file_rel, "status": "error", "reason": "anchor_not_found", "anchor": anchor})
        return
    if where == "after":
        insert_at = idx + len(anchor)
    elif where == "before":
        insert_at = idx
    else:
        report.append({"change_id": p.get("change_id"), "file": file_rel, "status": "error", "reason": f"invalid_where:{where}"})
        return

    action = p["action"]
    content = "\n".join(p.get("content", [])) + ("\n" if p.get("content") else "")
    if action == "insert":
        new_txt = txt[:insert_at] + ("\n" + content) + txt[insert_at:]
    elif action == "replace":
        new_txt = txt.replace(anchor, content)
    elif action == "delete":
        new_txt = txt.replace(anchor, "")
    else:
        report.append({"change_id": p.get("change_id"), "file": file_rel, "status": "error", "reason": f"invalid_action:{action}"})
        return
    target.write_text(new_txt, encoding="utf-8")
    report.append({"change_id": p.get("change_id"), "file": file_rel, "status": "ok", "action": action})

def main():
    root = Path(".").resolve()
    patch_dir = Path("patches")
    if not patch_dir.exists():
        print("No patches directory", file=sys.stderr)
        sys.exit(2)
    report = []
    for pf in sorted(patch_dir.glob("*.pat.json")):
        apply_patch(root, pf, report)
    Path("reports").mkdir(exist_ok=True)
    (Path("reports")/"patch_apply.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Applied", len(report), "patch(es).")

if __name__ == "__main__":
    main()
