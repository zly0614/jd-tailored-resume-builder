from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .jd_parser import parse_job_description
from .latex_renderer import render_resume_latex
from .llm import LLMEnhancer
from .memory import append_feedback, load_memory_context
from .profile_loader import load_profile, load_profile_from_text
from .ranking import build_ranked_resume


@dataclass
class GenerationResult:
    latex: str
    output_path: str
    target_title: str
    used_model: str
    used_llm: bool
    fallback_reason: str


def generate_resume(
    *,
    profile_path: str,
    jd_text: str,
    out_path: str,
    mode: str = "llm",
    memory_file: str = "memory.md",
    work_limit: int = 4,
    project_limit: int = 3,
    skill_limit: int = 12,
) -> GenerationResult:
    profile = load_profile(profile_path)
    return _generate_from_profile(
        profile=profile,
        jd_text=jd_text,
        out_path=out_path,
        mode=mode,
        memory_file=memory_file,
        work_limit=work_limit,
        project_limit=project_limit,
        skill_limit=skill_limit,
    )


def generate_resume_from_text(
    *,
    profile_text: str,
    jd_text: str,
    out_path: str,
    mode: str = "llm",
    memory_file: str = "memory.md",
    work_limit: int = 4,
    project_limit: int = 3,
    skill_limit: int = 12,
) -> GenerationResult:
    profile = load_profile_from_text(profile_text)
    return _generate_from_profile(
        profile=profile,
        jd_text=jd_text,
        out_path=out_path,
        mode=mode,
        memory_file=memory_file,
        work_limit=work_limit,
        project_limit=project_limit,
        skill_limit=skill_limit,
    )


def store_feedback(
    *,
    memory_file: str,
    target_role: str,
    feedback: str,
    output_path: str = "",
    model: str = "",
) -> None:
    append_feedback(
        path=memory_file,
        target_role=target_role,
        feedback=feedback,
        output_path=output_path,
        model=model,
    )


def default_output_path(prefix: str = "resume_web") -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return str(Path("outputs") / f"{prefix}_{timestamp}.tex")


def _generate_from_profile(
    *,
    profile,
    jd_text: str,
    out_path: str,
    mode: str,
    memory_file: str,
    work_limit: int,
    project_limit: int,
    skill_limit: int,
) -> GenerationResult:
    jd = parse_job_description(jd_text)
    memory_context = load_memory_context(memory_file)
    ranked_resume = build_ranked_resume(
        profile=profile,
        jd=jd,
        work_limit=work_limit,
        project_limit=project_limit,
        skill_limit=skill_limit,
    )

    llm = LLMEnhancer()
    fallback_reason = ""
    used_llm = False
    if mode == "llm":
        used_llm = llm.is_available()
        ranked_resume = llm.enhance(profile, jd, ranked_resume, memory_context=memory_context)
        if not used_llm:
            fallback_reason = "OPENAI_API_KEY not found. Fell back to heuristic generation."

    latex = render_resume_latex(profile, ranked_resume)
    destination = Path(out_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(latex, encoding="utf-8")

    return GenerationResult(
        latex=latex,
        output_path=str(destination),
        target_title=ranked_resume.target_title,
        used_model=llm.model if used_llm else "heuristic",
        used_llm=used_llm,
        fallback_reason=fallback_reason,
    )
