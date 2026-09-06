#!/usr/bin/env python3
"""Compile the paper and record the machine facts about the result.

Page count, per-page rendering, font/glyph status, overfull boxes and undefined
references are read out of the engine log and the produced PDF. Nobody attests
to them by hand, so the layout gate stops being a self-report.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from provenance import sha256_file, tree_snapshot

WORKFLOW_VERSION = "0.6.0"
LOG_PATTERNS = {
    "overfull": re.compile(r"^Overfull \\[hv]box", re.M),
    "underfull": re.compile(r"^Underfull \\[hv]box", re.M),
    "undefined_reference": re.compile(r"Reference `[^']*' on page \d+ undefined|There were undefined references", re.M),
    "missing_glyph": re.compile(r"Missing character: There is no ", re.M),
    "font_error": re.compile(r"(?:Font \\[^ ]+ not (?:loadable|found)|Package fontspec Error)", re.M),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read {path}: {exc}")
    if not isinstance(value, dict):
        raise SystemExit(f"expected a JSON object: {path}")
    return value


def write_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        temp_name = stream.name
    os.replace(temp_name, path)


def engine_version(engine: str) -> str:
    try:
        completed = subprocess.run([engine, "--version"], capture_output=True, text=True, check=False, timeout=60)
        return (completed.stdout or completed.stderr).strip().splitlines()[0]
    except (OSError, subprocess.SubprocessError, IndexError):
        return f"{engine} (version unknown)"


def page_count(pdf: Path) -> int:
    if shutil.which("pdfinfo"):
        completed = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=False)
        for line in completed.stdout.splitlines():
            if line.startswith("Pages:"):
                return int(line.split(":", 1)[1].strip())
    data = pdf.read_bytes()
    return max(1, len(re.findall(rb"/Type\s*/Page[^s]", data)))


def render_pages(pdf: Path, out_dir: Path) -> list[int]:
    """Rasterise every page so a reviewer looks at pixels, not at a promise."""
    if not shutil.which("pdftoppm"):
        return []
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(["pdftoppm", "-png", "-r", "110", str(pdf), str(out_dir / "page")], capture_output=True, text=True, check=False)
    if completed.returncode:
        return []
    pages = []
    for item in sorted(out_dir.glob("page-*.png")):
        match = re.search(r"page-(\d+)\.png$", item.name)
        if match:
            pages.append(int(match.group(1)))
    return sorted(pages)


def log_checks(text: str) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    counts = {name: len(pattern.findall(text)) for name, pattern in LOG_PATTERNS.items()}
    checks.append({"check_id": "LOG-OVERFULL", "category": "pagination", "status": "pass" if counts["overfull"] == 0 else "fail",
                   "notes": f"{counts['overfull']} overfull box(es) reported by the engine"})
    checks.append({"check_id": "LOG-UNDERFULL", "category": "whitespace", "status": "pass" if counts["underfull"] == 0 else "not_applicable",
                   "notes": f"{counts['underfull']} underfull box(es); loose lines are a reading judgement, not a failure"})
    checks.append({"check_id": "LOG-REFERENCES", "category": "cross_page", "status": "pass" if counts["undefined_reference"] == 0 else "fail",
                   "notes": f"{counts['undefined_reference']} undefined reference marker(s)"})
    checks.append({"check_id": "LOG-GLYPH", "category": "font_glyph", "status": "pass" if counts["missing_glyph"] == 0 else "fail",
                   "notes": f"{counts['missing_glyph']} missing-character warning(s)"})
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile the paper and write delivery/COMPILE_RECEIPT.json from observed facts")
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--passes", type=int, default=2)
    parser.add_argument("--engine")
    parser.add_argument("--attempt-id", default="ATTEMPT-001")
    parser.add_argument("--no-render", action="store_true", help="skip per-page rasterisation")
    parser.add_argument("--update-quality", action="store_true", help="refresh the machine fields of PAPER_QUALITY_REPORT.layout_report")
    args = parser.parse_args()

    root = args.project.resolve()
    if not root.is_dir():
        parser.error(f"project is not a directory: {root}")
    latex = read_object(root / "paper" / "LATEX_TEMPLATE_MANIFEST.json")
    engine = args.engine or str(latex.get("engine", "xelatex"))
    main_rel = str(latex.get("main_path", "paper/main.tex"))
    main_path = root / main_rel
    if not main_path.is_file():
        parser.error(f"LaTeX entry point is missing: {main_rel}")
    if not shutil.which(engine):
        parser.error(f"{engine} is not installed; install it or pass --engine")

    work_dir = main_path.parent
    argv = [engine, "-interaction=nonstopmode", "-halt-on-error", main_path.name]
    log_dir = root / "delivery"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_rel = "delivery/compile.log"
    transcript = ""
    exit_code = 0
    for _ in range(max(1, args.passes)):
        completed = subprocess.run(argv, cwd=work_dir, capture_output=True, text=True, check=False)
        transcript += completed.stdout + completed.stderr
        exit_code = completed.returncode
        if exit_code != 0:
            break
    engine_log = work_dir / (main_path.stem + ".log")
    if engine_log.is_file():
        transcript += "\n" + engine_log.read_text(encoding="utf-8", errors="replace")
    (root / log_rel).write_text(transcript, encoding="utf-8")

    pdf_path = work_dir / (main_path.stem + ".pdf")
    if exit_code != 0 or not pdf_path.is_file():
        print(f"compile failed (exit {exit_code}); see {log_rel}")
        return 1
    pdf_rel = pdf_path.relative_to(root).as_posix()
    checks = log_checks(transcript)
    pages_total = page_count(pdf_path)
    rendered = [] if args.no_render else render_pages(pdf_path, root / ".cumcm" / "tmp" / "pages")

    required_files = [str(value) for value in latex.get("required_files", [])]
    receipt = {
        "schema_version": WORKFLOW_VERSION,
        "artifact_type": "compile_receipt",
        "project_id": read_object(root / ".cumcm" / "state.json")["project_id"],
        "updated_at": utc_now(),
        "producer": {"kind": "script", "name": "record_compile.py", "version": WORKFLOW_VERSION},
        "selected_attempt_id": args.attempt_id,
        "source_snapshot": tree_snapshot(root, required_files, entrypoint=main_rel),
        "attempts": [
            {
                "attempt_id": args.attempt_id,
                "argv": argv,
                "engine": engine,
                "engine_version": engine_version(engine),
                "exit_code": exit_code,
                "log_path": log_rel,
                "warnings": [item["notes"] for item in checks if item["status"] == "fail"],
                "page_count": pages_total,
                "pdf_path": pdf_rel,
                "pdf_sha256": sha256_file(pdf_path),
                "font_check": "fail" if LOG_PATTERNS["font_error"].search(transcript) else "pass",
                "glyph_check": "fail" if LOG_PATTERNS["missing_glyph"].search(transcript) else "pass",
                "diagnostic_summary": "; ".join(f"{item['check_id']}={item['status']}" for item in checks),
                "completed_at": utc_now(),
            }
        ],
        "layout_report_binding": {
            "quality_report_path": "paper/PAPER_QUALITY_REPORT.json",
            "pdf_sha256": sha256_file(pdf_path),
        },
    }
    write_atomic(root / "delivery" / "COMPILE_RECEIPT.json", receipt)

    quality_path = root / "paper" / "PAPER_QUALITY_REPORT.json"
    if args.update_quality and quality_path.is_file():
        quality = read_object(quality_path)
        layout = quality.get("layout_report")
        if isinstance(layout, dict):
            layout["page_count"] = pages_total
            if rendered:
                layout["rendered_pages"] = rendered
            layout["checks"] = checks
            layout["artifact"] = {"path": pdf_rel, "sha256": sha256_file(pdf_path)}
            quality["paper_artifact"] = {"path": pdf_rel, "sha256": sha256_file(pdf_path)}
            write_atomic(quality_path, quality)
            print("refreshed PAPER_QUALITY_REPORT.layout_report machine fields; the decision is still yours")

    delivery_path = root / "delivery" / "DELIVERY_MANIFEST.json"
    if delivery_path.is_file():
        delivery = read_object(delivery_path)
        delivery["compile"] = {
            "command": " ".join(argv),
            "engine": engine,
            "exit_code": exit_code,
            "log_path": log_rel,
            "warnings": receipt["attempts"][0]["warnings"],
            "page_count": pages_total,
        }
        delivery["compile_receipt_path"] = "delivery/COMPILE_RECEIPT.json"
        write_atomic(delivery_path, delivery)
        print("refreshed DELIVERY_MANIFEST.compile")

    failures = [item["check_id"] for item in checks if item["status"] == "fail"]
    print(f"compiled {pdf_rel}: {pages_total} page(s), {len(rendered)} rendered, checks {'ok' if not failures else 'FAILED: ' + ', '.join(failures)}")
    if rendered:
        print(f"page images: .cumcm/tmp/pages/ -- these are what DELIVERY_MANIFEST.final_check must present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
