from __future__ import annotations

from datetime import datetime
from pathlib import Path


def load_memory_context(path: str | Path, max_chars: int = 4000) -> str:
    memory_path = Path(path)
    if not memory_path.exists():
        return ""
    text = memory_path.read_text(encoding="utf-8")
    return text[-max_chars:]


def append_feedback(
    path: str | Path,
    target_role: str,
    feedback: str,
    output_path: str = "",
    model: str = "",
) -> None:
    memory_path = Path(path)
    if not memory_path.exists():
        memory_path.write_text(
            "# Resume Memory\n\n用于记录每次简历生成后的用户反馈，帮助后续生成持续贴近用户偏好。\n",
            encoding="utf-8",
        )

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "",
        f"## {timestamp}",
        f"- Target Role: {target_role or 'Unknown'}",
        f"- Output File: {output_path or 'N/A'}",
        f"- Model: {model or 'heuristic'}",
        "- Feedback:",
        feedback.strip(),
        "",
    ]
    with memory_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
