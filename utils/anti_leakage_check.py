#!/usr/bin/env python3
"""Anti-Leakage Check: scan for potential pre-training data leakage."""
import re
import sys
from pathlib import Path

SUSPICIOUS_PATTERNS = [
    (r"\\textit\{[^}]{30,}\}", "suspiciously long italicized text (possible copy)"),
    (r"\\textbf\{[^}]{30,}\}", "suspiciously long bold text (possible copy)"),
    (r"\\cite\{([^}]+)\}.*?\\cite\{\1\}", "self-citation loop (same key cited twice nearby)"),
]

def check(tex_file: Path) -> dict:
    text = tex_file.read_text(encoding="utf-8")
    result = {"ok": True, "findings": []}

    # Check for author/affiliation leakage
    if re.search(r"\\author|\\affiliation|\\institute|\\email", text):
        result["findings"].append("Contains author/affiliation info — verify user provided")
        result["ok"] = False

    # Check for suspicious patterns
    for pat, reason in SUSPICIOUS_PATTERNS:
        if re.search(pat, text):
            result["findings"].append(f"Pattern match: {reason}")

    return result

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <paper.tex>")
        sys.exit(1)
    r = check(Path(sys.argv[1]))
    if r["ok"] and not r["findings"]:
        print("[PASS] Anti-Leakage Check")
    else:
        print(f"[{'FAIL' if not r['ok'] else 'WARN'}] Anti-Leakage Check")
        for f in r["findings"]:
            print(f"  {f}")

if __name__ == "__main__":
    main()
