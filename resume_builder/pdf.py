from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PdfCompileResult:
    success: bool
    pdf_path: str
    engine: str
    message: str
    log_path: str


def compile_tex_to_pdf(tex_path: str | Path) -> PdfCompileResult:
    tex_file = Path(tex_path).resolve()
    try:
        engine = _detect_engine()
    except PermissionError as exc:
        return PdfCompileResult(
            success=False,
            pdf_path="",
            engine="",
            message=f"LaTeX engine was found but access was denied: {exc}",
            log_path=str(tex_file.with_suffix(".pdf.log")),
        )
    log_path = str(tex_file.with_suffix(".pdf.log"))

    if not engine:
        return PdfCompileResult(
            success=False,
            pdf_path="",
            engine="",
            message="No LaTeX compiler found. Install xelatex or pdflatex to enable PDF export.",
            log_path=log_path,
        )

    workdir = tex_file.parent
    command = [
        engine,
        "-interaction=nonstopmode",
        "-halt-on-error",
        tex_file.name,
    ]
    try:
        result = subprocess.run(
            command,
            cwd=workdir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except PermissionError as exc:
        return PdfCompileResult(
            success=False,
            pdf_path="",
            engine=engine,
            message=f"LaTeX engine could not be executed: {exc}",
            log_path=log_path,
        )

    combined_output = "\n".join(part for part in [result.stdout, result.stderr] if part)
    Path(log_path).write_text(combined_output, encoding="utf-8")

    pdf_path = tex_file.with_suffix(".pdf")
    if result.returncode == 0 and pdf_path.exists():
        return PdfCompileResult(
            success=True,
            pdf_path=str(pdf_path),
            engine=engine,
            message=f"PDF compiled successfully with {engine}.",
            log_path=log_path,
        )

    return PdfCompileResult(
        success=False,
        pdf_path=str(pdf_path) if pdf_path.exists() else "",
        engine=engine,
        message=f"PDF compilation failed with {engine}. See log for details.",
        log_path=log_path,
    )


def _detect_engine() -> str:
    for candidate in ("xelatex", "pdflatex"):
        if shutil.which(candidate):
            return candidate
    for candidate in _well_known_windows_engines():
        try:
            if candidate.exists():
                return str(candidate)
        except PermissionError:
            return str(candidate)
    return ""


def _well_known_windows_engines() -> list[Path]:
    local_app_data = os.getenv("LOCALAPPDATA", "")
    if not local_app_data:
        return []

    roots = [
        Path(local_app_data) / "Programs" / "MiKTeX" / "miktex" / "bin" / "x64",
        Path(local_app_data) / "Programs" / "MiKTeX" / "miktex" / "bin",
    ]
    result: list[Path] = []
    for root in roots:
        result.append(root / "xelatex.exe")
        result.append(root / "pdflatex.exe")
    return result
