from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .draft import build_resume_draft
from .jd_parser import parse_job_description
from .latex_renderer import render_resume_latex_from_draft
from .llm import LLMEnhancer
from .memory import append_feedback, load_memory_context
from .models import LLMConfig
from .pdf import compile_tex_to_pdf
from .profile_loader import load_profile, load_profile_from_text
from .ranking import build_ranked_resume
from .template_registry import DEFAULT_TEMPLATE_KEY, get_template
from .word_template import render_resume_word_template


@dataclass
class GenerationResult:
    draft: dict
    latex: str
    output_path: str
    target_title: str
    used_model: str
    used_llm: bool
    fallback_reason: str
    pdf_path: str
    pdf_message: str
    pdf_engine: str
    pdf_log_path: str
    language: str
    template_name: str


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
    compile_pdf: bool = False,
    language: str = "en",
    template_name: str = DEFAULT_TEMPLATE_KEY,
    llm_config: LLMConfig | None = None,
    extra_context: str = "",
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
        compile_pdf=compile_pdf,
        language=language,
        template_name=template_name,
        llm_config=llm_config,
        extra_context=extra_context,
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
    compile_pdf: bool = False,
    language: str = "en",
    template_name: str = DEFAULT_TEMPLATE_KEY,
    llm_config: LLMConfig | None = None,
    extra_context: str = "",
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
        compile_pdf=compile_pdf,
        language=language,
        template_name=template_name,
        llm_config=llm_config,
        extra_context=extra_context,
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
    return str(Path("outputs") / f"{prefix}_{timestamp}.docx")


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
    compile_pdf: bool,
    language: str,
    template_name: str,
    llm_config: LLMConfig | None,
    extra_context: str,
) -> GenerationResult:
    jd = parse_job_description(jd_text)
    memory_context = _merge_context(load_memory_context(memory_file), extra_context)
    ranked_resume = build_ranked_resume(
        profile=profile,
        jd=jd,
        work_limit=work_limit,
        project_limit=project_limit,
        skill_limit=skill_limit,
        language=language,
    )

    llm = LLMEnhancer.from_config(llm_config or LLMConfig())
    fallback_reason = ""
    used_llm = False
    if mode == "llm":
        used_llm = llm.is_available()
        ranked_resume = llm.enhance(profile, jd, ranked_resume, memory_context=memory_context, language=language)
        if not used_llm:
            fallback_reason = "OPENAI_API_KEY not found. Fell back to heuristic generation."

    rendered_profile = profile
    rendered_resume = ranked_resume
    if used_llm:
        rendered_profile, rendered_resume = llm.localize_resume(profile, ranked_resume, language=language)

    template = get_template(template_name)
    draft = build_resume_draft(rendered_profile, rendered_resume, language=language)
    latex = ""
    destination = Path(out_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    pdf_path = ""
    pdf_message = ""
    pdf_engine = ""
    pdf_log_path = ""

    used_word_template = False
    if template.key == DEFAULT_TEMPLATE_KEY and template.source_file:
        template_file = _resolve_template_source_path(template.source_file)
        if template_file.exists():
            try:
                word_result = render_resume_word_template(
                    draft=draft,
                    template_path=template_file,
                    output_path=destination,
                    compile_pdf=compile_pdf,
                )
                destination = Path(word_result.docx_path)
                pdf_path = word_result.pdf_path
                pdf_message = word_result.pdf_message
                pdf_engine = "word-template"
                used_word_template = True
            except Exception as exc:
                fallback_reason = f"Word template rendering failed. Fell back to LaTeX rendering. {exc}"

    if not used_word_template:
        latex = render_resume_latex_from_draft(draft, template_name=template.key)
        destination = destination.with_suffix(".tex")
        destination.write_text(latex, encoding="utf-8")
        if compile_pdf:
            pdf_result = compile_tex_to_pdf(destination)
            pdf_path = pdf_result.pdf_path
            pdf_message = pdf_result.message
            pdf_engine = pdf_result.engine
            pdf_log_path = pdf_result.log_path

    return GenerationResult(
        draft=draft.to_dict(),
        latex=latex,
        output_path=str(destination),
        target_title=rendered_resume.target_title,
        used_model=llm.model if used_llm else "heuristic",
        used_llm=used_llm,
        fallback_reason=fallback_reason,
        pdf_path=pdf_path,
        pdf_message=pdf_message,
        pdf_engine=pdf_engine,
        pdf_log_path=pdf_log_path,
        language=language,
        template_name=template.key,
    )


def _merge_context(memory_context: str, extra_context: str) -> str:
    extra_context = extra_context.strip()
    if not extra_context:
        return memory_context
    if not memory_context:
        return f"[Supplemental Resume Notes]\n{extra_context}"
    return f"{memory_context}\n\n[Supplemental Resume Notes]\n{extra_context}"


def _resolve_template_source_path(source_file: str) -> Path:
    relative = source_file.lstrip("/").replace("/", "\\")
    return Path(__file__).resolve().parent / relative.replace("static\\", "static\\", 1)
