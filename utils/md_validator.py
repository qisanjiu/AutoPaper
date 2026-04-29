#!/usr/bin/env python3
"""Validate a Stage output markdown against Universal Document Schema."""
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "核心内容",
    "Reasoning Trail",
    "验证与检查",
    "风险与限制",
    "下游接口",
    "回溯触发器",
]

def validate(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    result = {"ok": True, "errors": [], "warnings": []}

    # 1. Front matter
    if not text.startswith("---"):
        result["errors"].append("Missing YAML front matter")
        result["ok"] = False
    else:
        fm_end = text.find("---", 3)
        if fm_end == -1:
            result["errors"].append("Unclosed YAML front matter")
            result["ok"] = False

    # 2. Required sections
    for sec in REQUIRED_SECTIONS:
        if sec not in text:
            result["errors"].append(f"Missing section: {sec}")
            result["ok"] = False

    # 3. Downstream Interface count
    di_match = re.search(r"下游接口.*?$(.+?)(?=^## |^# |\\Z)", text, re.M | re.S)
    if di_match:
        items = re.findall(r"^\d+\.\s", di_match.group(1), re.M)
        if len(items) < 3:
            result["warnings"].append(f"Downstream Interface has only {len(items)} items (need ≥3)")
    else:
        result["warnings"].append("Could not parse Downstream Interface section")

    # 4. Backtrack Triggers count
    bt_match = re.search(r"回溯触发器.*?$(.+?)(?=^## |^# |\\Z)", text, re.M | re.S)
    if bt_match:
        items = re.findall(r"^[-*]\s", bt_match.group(1), re.M)
        if len(items) < 1:
            result["warnings"].append("Backtrack Triggers has 0 items (need ≥1)")
    else:
        result["warnings"].append("Could not parse Backtrack Triggers section")

    return result

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path/to/S{NN}_*.md>")
        sys.exit(1)
    for p in sys.argv[1:]:
        r = validate(Path(p))
        status = "PASS" if r["ok"] else "FAIL"
        print(f"[{status}] {p}")
        for e in r["errors"]:
            print(f"  ERROR: {e}")
        for w in r["warnings"]:
            print(f"  WARN:  {w}")

if __name__ == "__main__":
    main()