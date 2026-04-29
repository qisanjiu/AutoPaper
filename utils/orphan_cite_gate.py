#!/usr/bin/env python3
"""Orphan Cite Gate: ensure every \cite{KEY} exists in refs.bib."""
import re
import sys
from pathlib import Path

def check(tex_file: Path, bib_file: Path) -> dict:
    tex = tex_file.read_text(encoding="utf-8")
    bib = bib_file.read_text(encoding="utf-8")
    result = {"ok": True, "orphan_cites": [], "orphan_entries": []}

    # Extract cite keys
    cite_keys = set()
    for m in re.findall(r"\\cite[pt]?\{([^}]+)\}", tex):
        cite_keys.update(k.strip() for k in m.split(","))

    # Extract bib keys
    bib_keys = set(re.findall(r"^\s*@\w+\{([^,\s]+)", bib, re.M))

    for key in cite_keys:
        if key not in bib_keys:
            result["orphan_cites"].append(key)
            result["ok"] = False

    for key in bib_keys:
        if key not in cite_keys:
            result["orphan_entries"].append(key)

    return result

def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <paper.tex> <refs.bib>")
        sys.exit(1)
    r = check(Path(sys.argv[1]), Path(sys.argv[2]))
    if r["ok"]:
        print("[PASS] Orphan Cite Gate")
    else:
        print("[FAIL] Orphan Cite Gate")
        for k in r["orphan_cites"]:
            print(f"  ORPHAN CITE: {k}")
    if r["orphan_entries"]:
        print(f"  WARN: {len(r['orphan_entries'])} unused bib entries")

if __name__ == "__main__":
    main()
