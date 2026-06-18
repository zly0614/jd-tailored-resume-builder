from __future__ import annotations

import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .draft import DraftSection, ResumeDraft

_BUNDLED_SITE_PACKAGES = (
    Path.home()
    / ".cache"
    / "codex-runtimes"
    / "codex-primary-runtime"
    / "dependencies"
    / "python"
    / "Lib"
    / "site-packages"
)
if _BUNDLED_SITE_PACKAGES.exists():
    sys.path.append(str(_BUNDLED_SITE_PACKAGES))

from docx import Document  # type: ignore
from docx.text.paragraph import Paragraph  # type: ignore


@dataclass
class WordTemplateResult:
    docx_path: str
    pdf_path: str
    pdf_message: str


NAME_INDEX = 0
CONTACT_INDEX = 1
EDUCATION_RANGE = range(3, 8)
SKILL_RANGE = range(9, 12)
PROJECT_RANGE = range(13, 28)
OTHER_INDEX = 29
PROJECT_SLOTS = 3
PROJECT_LINES_PER_SLOT = 5


def render_resume_word_template(
    *,
    draft: ResumeDraft,
    template_path: Path,
    output_path: Path,
    compile_pdf: bool = False,
) -> WordTemplateResult:
    output_path = output_path.resolve().with_suffix(".docx")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path = output_path.with_suffix(".pdf") if compile_pdf else Path("")

    _convert_doc_template_to_docx(template_path, output_path)
    _fill_docx_template(output_path, draft)
    if compile_pdf:
        _export_docx_to_pdf(output_path, pdf_path, draft.photo_path)

    return WordTemplateResult(
        docx_path=str(output_path),
        pdf_path=str(pdf_path) if compile_pdf else "",
        pdf_message="PDF exported successfully from Word template." if compile_pdf else "",
    )


def _convert_doc_template_to_docx(template_path: Path, output_docx_path: Path) -> None:
    script = r"""
param([string]$TemplatePath, [string]$OutputDocxPath)
$word = $null
$doc = $null
try {
  $word = New-Object -ComObject Word.Application
  $word.Visible = $false
  $doc = $word.Documents.Open($TemplatePath)
  $doc.SaveAs([ref]$OutputDocxPath, [ref]16)
}
finally {
  if ($doc -ne $null) { try { $doc.Close($false) } catch {} }
  if ($word -ne $null) { try { $word.Quit() } catch {} }
}
"""
    _run_powershell(script, str(template_path.resolve()), str(output_docx_path))


def _export_docx_to_pdf(docx_path: Path, pdf_path: Path, photo_path: str) -> None:
    photo_argument = str(Path(photo_path).resolve()) if photo_path else ""
    script = r"""
param([string]$DocxPath, [string]$PdfPath, [string]$PhotoPath)
$word = $null
$doc = $null
try {
  $word = New-Object -ComObject Word.Application
  $word.Visible = $false
  $doc = $word.Documents.Open($DocxPath)
  if ($doc.Shapes.Count -gt 0) {
    $shape = $doc.Shapes.Item(1)
    $left = $shape.Left
    $top = $shape.Top
    $width = $shape.Width
    $height = $shape.Height
    $shape.Delete()
    if ($PhotoPath -and (Test-Path $PhotoPath)) {
      $null = $doc.Shapes.AddPicture($PhotoPath, $false, $true, $left, $top, $width, $height)
    }
  }
  $doc.Save()
  $doc.SaveAs([ref]$PdfPath, [ref]17)
}
finally {
  if ($doc -ne $null) { try { $doc.Close($false) } catch {} }
  if ($word -ne $null) { try { $word.Quit() } catch {} }
}
"""
    _run_powershell(script, str(docx_path.resolve()), str(pdf_path.resolve()), photo_argument)


def _run_powershell(script: str, *args: str) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        script_path = Path(temp_dir) / "word_template.ps1"
        script_path.write_text(script, encoding="utf-8")
        command = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
            *args,
        ]
        completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "PowerShell Word automation failed."
            raise RuntimeError(detail)


def _fill_docx_template(docx_path: Path, draft: ResumeDraft) -> None:
    document = Document(str(docx_path))
    paragraphs = document.paragraphs
    if len(paragraphs) < 30:
        raise RuntimeError(f"Unexpected template structure: expected at least 30 paragraphs, got {len(paragraphs)}.")

    _replace_if_present(paragraphs[NAME_INDEX], draft.name)
    _replace_if_present(paragraphs[CONTACT_INDEX], _build_contact_line(draft.contact_lines))

    _fill_range(
        paragraphs,
        EDUCATION_RANGE,
        _education_lines(_get_section(draft, "education")),
    )
    _fill_range(
        paragraphs,
        SKILL_RANGE,
        _skill_lines(_get_section(draft, "skills")),
    )
    _fill_range(
        paragraphs,
        PROJECT_RANGE,
        _project_lines(_get_section(draft, "project")),
    )
    _replace_if_present(paragraphs[OTHER_INDEX], _other_text(_get_section(draft, "certificates")))

    document.save(str(docx_path))


def _replace_if_present(paragraph: Paragraph, text: str) -> None:
    if not text.strip():
        return
    if paragraph.runs:
        paragraph.runs[0].text = text
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.text = text


def _fill_range(paragraphs: list[Paragraph], paragraph_range: range, new_lines: list[str]) -> None:
    existing_lines = [paragraphs[index].text for index in paragraph_range]
    final_lines = _pad_or_trim(new_lines, len(existing_lines), existing_lines)
    for index, text in zip(paragraph_range, final_lines):
        _replace_if_present(paragraphs[index], text)


def _pad_or_trim(lines: list[str], size: int, fallback: list[str]) -> list[str]:
    cleaned = [line.strip() for line in lines if line.strip()]
    if not cleaned:
        return fallback[:size]
    return (cleaned + fallback)[:size]


def _build_contact_line(contact_lines: list[str]) -> str:
    pieces: list[str] = []
    for line in contact_lines:
        stripped = line.strip()
        if not stripped:
            continue
        compact = stripped.replace("电话：", "").replace("邮箱：", "").replace("地点：", "").strip()
        if compact:
            pieces.append(stripped)

    merged = "  ".join(piece for piece in pieces if piece)
    return merged if merged else ""


def _get_section(draft: ResumeDraft, key: str) -> DraftSection | None:
    for section in draft.sections:
        if section.key == key:
            return section
    return None


def _education_lines(section: DraftSection | None) -> list[str]:
    if not section or not section.items:
        return []

    lines: list[str] = []
    for item in section.items[:2]:
        summary = " ".join(part for part in [item.subheading, item.heading, item.date_range] if part).strip()
        if summary:
            lines.append(summary)
        if item.bullets:
            lines.append("核心课程：" + "、".join(item.bullets[:4]))
    return lines[: len(EDUCATION_RANGE)]


def _skill_lines(section: DraftSection | None) -> list[str]:
    if not section or not section.content.strip():
        return []

    skills = [part.strip() for part in section.content.split("/") if part.strip()]
    groups = [
        ("算法与模型：", skills[0:4]),
        ("训练与推理：", skills[4:8]),
        ("工程与Agent：", skills[8:12]),
    ]

    lines: list[str] = []
    for label, items in groups:
        if items:
            lines.append(label + "、".join(items))
    return lines[: len(SKILL_RANGE)]


def _project_lines(section: DraftSection | None) -> list[str]:
    if not section or not section.items:
        return []

    lines: list[str] = []
    for item in section.items[:PROJECT_SLOTS]:
        title = item.heading.strip()
        if item.date_range:
            title = f"{title}                                      {item.date_range}"
        bullets = [bullet.strip() for bullet in item.bullets if bullet.strip()]
        chunk = [title]
        labels = ["任务介绍：", "关键实现：", "效果产出：", "补充说明："]
        for label, bullet in zip(labels, bullets):
            chunk.append(label + _shorten_text(bullet, max_units=46))
        while len(chunk) < PROJECT_LINES_PER_SLOT:
            chunk.append("补充说明：")
        lines.extend(chunk[:PROJECT_LINES_PER_SLOT])

    return lines[: len(PROJECT_RANGE)]


def _other_text(section: DraftSection | None) -> str:
    if not section or not section.items:
        return ""
    parts = []
    for item in section.items:
        text = " ".join(part for part in [item.heading, item.subheading] if part).strip()
        if text:
            parts.append(text)
    return "；".join(parts)


def _shorten_text(text: str, *, max_units: int) -> str:
    normalized = " ".join(text.replace("\n", " ").split())
    for separator in ("；", "。", "，", ",", "：", ":"):
        if separator in normalized:
            candidate = normalized.split(separator, 1)[0].strip()
            if candidate:
                normalized = candidate
                break

    if _display_units(normalized) <= max_units:
        return normalized

    shortened = []
    units = 0
    for char in normalized:
        weight = 1 if ord(char) < 128 else 2
        if units + weight > max_units - 2:
            break
        shortened.append(char)
        units += weight
    return "".join(shortened).rstrip() + "..."


def _display_units(text: str) -> int:
    return sum(1 if ord(char) < 128 else 2 for char in text)
