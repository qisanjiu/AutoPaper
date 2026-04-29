#!/usr/bin/env python3
"""LaTeX Sanity Check: multi-pass compilation with bibtex support."""
import subprocess
import sys
from pathlib import Path


def compile_tex(tex_file: Path, max_passes: int = 4, use_bibtex: bool = True) -> dict:
    """
    Compile a LaTeX document with standard multi-pass workflow:
    pdflatex -> bibtex (if .bib exists) -> pdflatex -> pdflatex
    
    Returns dict with compilation results.
    """
    result = {
        "ok": True,
        "errors": [],
        "warnings": [],
        "pdf_path": None,
        "passes": 0,
    }
    
    if not tex_file.exists():
        result["errors"].append(f"File not found: {tex_file}")
        result["ok"] = False
        return result
    
    cwd = tex_file.parent
    stem = tex_file.stem
    pdf_file = cwd / f"{stem}.pdf"
    bib_file = cwd / f"{stem}.bib"
    aux_file = cwd / f"{stem}.aux"
    
    compiler = "pdflatex"
    
    # Check compiler availability
    try:
        subprocess.run([compiler, "--version"], capture_output=True, timeout=5)
    except FileNotFoundError:
        result["warnings"].append(f"{compiler} not found — skipping compilation")
        return result
    
    # Pass 1: pdflatex
    log = _run_compiler(compiler, tex_file, cwd, result)
    result["passes"] += 1
    
    # Check for fatal errors after first pass
    if _has_fatal_error(log):
        result["errors"].append("Fatal LaTeX error on first pass")
        result["ok"] = False
        return result
    
    # BibTeX pass (if .bib file exists and use_bibtex is enabled)
    if use_bibtex and bib_file.exists():
        try:
            bib_proc = subprocess.run(
                ["bibtex", stem],
                capture_output=True, text=True, cwd=cwd, timeout=30
            )
            bib_log = bib_proc.stdout + bib_proc.stderr
            if "Error" in bib_log:
                result["warnings"].append("BibTeX reported errors (non-fatal)")
        except FileNotFoundError:
            result["warnings"].append("bibtex not found — skipping bibliography compilation")
        except subprocess.TimeoutExpired:
            result["warnings"].append("BibTeX compilation timed out")
    
    # Pass 2: pdflatex (resolve cross-references)
    log = _run_compiler(compiler, tex_file, cwd, result)
    result["passes"] += 1
    
    # Pass 3: pdflatex (finalize)
    log = _run_compiler(compiler, tex_file, cwd, result)
    result["passes"] += 1
    
    # Check for remaining issues
    _parse_log(log, result)
    
    # Check if PDF was produced
    if pdf_file.exists() and pdf_file.stat().st_size > 0:
        result["pdf_path"] = str(pdf_file)
    else:
        result["errors"].append("PDF was not produced")
        result["ok"] = False
    
    return result


def _run_compiler(compiler: str, tex_file: Path, cwd: Path, result: dict) -> str:
    """Run pdflatex and return the combined stdout+stderr log."""
    try:
        proc = subprocess.run(
            [compiler, "-interaction=nonstopmode", str(tex_file)],
            capture_output=True, text=True, cwd=cwd, timeout=120
        )
        log = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        result["errors"].append("Compilation timed out")
        result["ok"] = False
        log = ""
    except Exception as e:
        result["errors"].append(f"Compiler error: {e}")
        result["ok"] = False
        log = ""
    return log


def _has_fatal_error(log: str) -> bool:
    """Check if the log contains fatal LaTeX errors."""
    fatal_indicators = [
        "! Emergency stop",
        "Fatal error",
        "! LaTeX Error: File",
        "! I can't find file",
    ]
    for indicator in fatal_indicators:
        if indicator in log:
            return True
    return False


def _parse_log(log: str, result: dict):
    """Parse LaTeX log for errors and warnings."""
    if "! Undefined control sequence" in log:
        result["errors"].append("Undefined control sequence")
        result["ok"] = False
    if "! LaTeX Error" in log:
        # Filter out non-fatal errors
        for line in log.splitlines():
            if "! LaTeX Error" in line and "undefined" not in line.lower():
                result["errors"].append(line.strip())
                result["ok"] = False
    if "?" in log and "Reference" in log:
        result["warnings"].append("Possible undefined references")
    if "Overfull" in log:
        result["warnings"].append("Overfull hbox detected")
    if "Underfull" in log:
        result["warnings"].append("Underfull hbox detected")
    
    # Check for undefined citations
    undefined_refs = set()
    for line in log.splitlines():
        if "undefined on input line" in line.lower():
            undefined_refs.add(line.strip())
    if undefined_refs:
        result["warnings"].append(f"Undefined references: {len(undefined_refs)}")


def check(tex_file: Path, max_pages: int = None) -> dict:
    """
    Backward-compatible wrapper: compile and check for errors.
    
    Args:
        tex_file: Path to the .tex file
        max_pages: Optional page limit to enforce
    """
    result = compile_tex(tex_file)
    
    # Page count check (if pdftotext or pdfinfo is available)
    if max_pages is not None and result.get("pdf_path"):
        try:
            pdfinfo = subprocess.run(
                ["pdfinfo", result["pdf_path"]],
                capture_output=True, text=True, timeout=10
            )
            for line in pdfinfo.stdout.splitlines():
                if line.startswith("Pages:"):
                    pages = int(line.split(":")[1].strip())
                    if pages > max_pages:
                        result["errors"].append(
                            f"Page limit exceeded: {pages} pages (limit: {max_pages})"
                        )
                        result["ok"] = False
                    break
        except FileNotFoundError:
            result["warnings"].append("pdfinfo not found — skipping page count check")
        except Exception as e:
            result["warnings"].append(f"Page count check failed: {e}")
    
    return result


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <paper.tex> [max_pages]")
        sys.exit(1)
    
    tex_path = Path(sys.argv[1])
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    r = check(tex_path, max_pages)
    status = "PASS" if r["ok"] else "FAIL"
    print(f"[{status}] LaTeX Sanity ({r['passes']} passes)")
    for e in r["errors"]:
        print(f"  ERROR: {e}")
    for w in r["warnings"]:
        print(f"  WARN:  {w}")
    if r["pdf_path"]:
        print(f"  PDF:   {r['pdf_path']}")


if __name__ == "__main__":
    main()
