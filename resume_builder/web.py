from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .local_config import load_local_llm_config
from .models import LLMConfig
from .profile_loader import load_profile_from_text
from .service import default_output_path, generate_resume_from_text, store_feedback
from .template_registry import get_template, template_options

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "static"
DEFAULT_PROFILE = (ROOT / "data" / "master_profile.sample.json").read_text(encoding="utf-8")
DEFAULT_JD = (ROOT / "data" / "sample_jd.txt").read_text(encoding="utf-8")
DEFAULT_LLM = load_local_llm_config(ROOT)
TEMPLATE_OPTIONS = template_options()

app = FastAPI(title="Jianli Creator")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "choose_template.html", _template_context("modern_blocks"))


@app.post("/profile-builder", response_class=HTMLResponse)
async def profile_builder(
    request: Request,
    template_name: str = Form("modern_blocks"),
    profile_text: str = Form(DEFAULT_PROFILE),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "build_profile.html",
        _profile_context(template_name=template_name, profile_text=profile_text),
    )


@app.post("/customize", response_class=HTMLResponse)
async def customize_resume(
    request: Request,
    template_name: str = Form("modern_blocks"),
    profile_text: str = Form(DEFAULT_PROFILE),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "customize_resume.html",
        _customize_context(
            template_name=template_name,
            profile_text=profile_text,
        ),
    )


@app.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    profile_text: str = Form(...),
    jd_text: str = Form(...),
    mode: str = Form("llm"),
    memory_file: str = Form("memory.md"),
    compile_pdf: str = Form("true"),
    language: str = Form("zh"),
    template_name: str = Form("modern_blocks"),
    llm_model: str = Form("MiMo-V2.5-Pro"),
    llm_base_url: str = Form("https://token-plan-cn.xiaomimimo.com/v1"),
    llm_api_key: str = Form(""),
    supplement_text: str = Form(""),
) -> HTMLResponse:
    try:
        result = generate_resume_from_text(
            profile_text=profile_text,
            jd_text=jd_text,
            out_path=default_output_path(),
            mode=mode,
            memory_file=memory_file,
            compile_pdf=compile_pdf == "true",
            language=language,
            template_name=template_name,
            llm_config=LLMConfig(
                model=llm_model,
                base_url=llm_base_url,
                api_key=llm_api_key,
            ),
            extra_context=supplement_text,
        )
        message = f"简历已生成，当前模型：{result.used_model}。"
        if result.fallback_reason:
            message = f"{message} {result.fallback_reason}"
        if result.pdf_message:
            message = f"{message} {result.pdf_message}"
        return templates.TemplateResponse(
            request,
            "result.html",
            _result_context(
                template_name=template_name,
                profile_text=profile_text,
                jd_text=jd_text,
                latex=result.latex,
                message=message,
                target_role=result.target_title,
                output_path=result.output_path,
                used_model=result.used_model,
                draft_json=json.dumps(result.draft, ensure_ascii=False, indent=2),
                mode=mode,
                memory_file=memory_file,
                compile_pdf=compile_pdf == "true",
                pdf_path=result.pdf_path,
                pdf_message=result.pdf_message,
                pdf_log_path=result.pdf_log_path,
                language=language,
                llm_model=llm_model,
                llm_base_url=llm_base_url,
                llm_api_key=llm_api_key,
                supplement_text=supplement_text,
            ),
        )
    except Exception as exc:
        return templates.TemplateResponse(
            request,
            "customize_resume.html",
            _customize_context(
                template_name=template_name,
                profile_text=profile_text,
                jd_text=jd_text,
                mode=mode,
                memory_file=memory_file,
                compile_pdf=compile_pdf == "true",
                language=language,
                llm_model=llm_model,
                llm_base_url=llm_base_url,
                llm_api_key=llm_api_key,
                supplement_text=supplement_text,
                error=f"Generation failed: {exc}",
            ),
        )


@app.post("/feedback", response_class=HTMLResponse)
async def feedback(
    request: Request,
    profile_text: str = Form(...),
    jd_text: str = Form(...),
    latex: str = Form(...),
    target_role: str = Form(""),
    output_path: str = Form(""),
    used_model: str = Form(""),
    memory_file: str = Form("memory.md"),
    mode: str = Form("llm"),
    compile_pdf: str = Form("true"),
    pdf_path: str = Form(""),
    pdf_log_path: str = Form(""),
    language: str = Form("zh"),
    template_name: str = Form("modern_blocks"),
    llm_model: str = Form("MiMo-V2.5-Pro"),
    llm_base_url: str = Form("https://token-plan-cn.xiaomimimo.com/v1"),
    llm_api_key: str = Form(""),
    supplement_text: str = Form(""),
    draft_json: str = Form(""),
    feedback_text: str = Form(...),
) -> HTMLResponse:
    message = "反馈已写入 memory.md，后续生成会继续参考。"
    error = ""
    try:
        store_feedback(
            memory_file=memory_file,
            target_role=target_role,
            feedback=feedback_text,
            output_path=output_path,
            model=used_model,
        )
    except Exception as exc:
        message = ""
        error = f"Feedback save failed: {exc}"

    return templates.TemplateResponse(
        request,
        "result.html",
        _result_context(
            template_name=template_name,
            profile_text=profile_text,
            jd_text=jd_text,
            latex=latex,
            message=message,
            error=error,
            target_role=target_role,
            output_path=output_path,
            used_model=used_model,
            draft_json=draft_json,
            mode=mode,
            memory_file=memory_file,
            compile_pdf=compile_pdf == "true",
            pdf_path=pdf_path,
            pdf_log_path=pdf_log_path,
            language=language,
            llm_model=llm_model,
            llm_base_url=llm_base_url,
            llm_api_key=llm_api_key,
            supplement_text=supplement_text,
        ),
    )


@app.get("/download")
async def download(path: str) -> FileResponse:
    file_path = Path(path)
    media_type = "application/pdf" if file_path.suffix.lower() == ".pdf" else "application/x-tex"
    return FileResponse(file_path, filename=file_path.name, media_type=media_type)


def _template_context(template_name: str, **overrides: object) -> dict[str, object]:
    context: dict[str, object] = {
        "template_name": template_name,
        "template_options": TEMPLATE_OPTIONS,
        "selected_template": get_template(template_name),
    }
    context.update(overrides)
    return context


def _profile_context(template_name: str, profile_text: str, **overrides: object) -> dict[str, object]:
    context = _template_context(
        template_name,
        profile_text=profile_text,
        builder_seed=json.dumps(_build_builder_seed(profile_text), ensure_ascii=False),
    )
    context.update(overrides)
    return context


def _customize_context(template_name: str, profile_text: str, **overrides: object) -> dict[str, object]:
    context = _template_context(
        template_name,
        profile_text=profile_text,
        jd_text=DEFAULT_JD,
        error="",
        mode="llm",
        memory_file="memory.md",
        compile_pdf=True,
        language="zh",
        llm_model=DEFAULT_LLM.model or "MiMo-V2.5-Pro",
        llm_base_url=DEFAULT_LLM.base_url or "https://token-plan-cn.xiaomimimo.com/v1",
        llm_api_key=DEFAULT_LLM.api_key,
        supplement_text="",
    )
    context.update(overrides)
    return context


def _result_context(template_name: str, profile_text: str, jd_text: str, **overrides: object) -> dict[str, object]:
    context = _customize_context(
        template_name=template_name,
        profile_text=profile_text,
        jd_text=jd_text,
        latex="",
        message="",
        target_role="",
        output_path="",
        used_model="",
        draft_json="",
        pdf_path="",
        pdf_message="",
        pdf_log_path="",
    )
    context.update(overrides)
    return context


def _build_builder_seed(profile_text: str) -> dict[str, object]:
    try:
        profile = load_profile_from_text(profile_text)
    except Exception:
        return {
            "basic_info": {
                "name": "",
                "title": "",
                "email": "",
                "phone": "",
                "location": "",
                "links": [],
            },
            "summary_options": [""],
            "skills": {"Core Skills": []},
            "work_experiences": [],
            "project_experiences": [],
            "education": [],
        }

    return {
        "basic_info": {
            "name": profile.basic_info.name,
            "title": profile.basic_info.title,
            "email": profile.basic_info.email,
            "phone": profile.basic_info.phone,
            "location": profile.basic_info.location,
            "links": profile.basic_info.links,
        },
        "summary_options": profile.summary_options or [""],
        "skills": profile.skills or {"Core Skills": []},
        "work_experiences": [
            {
                "company": item.company,
                "title": item.title,
                "start": item.start,
                "end": item.end,
                "location": item.location,
                "tags": item.tags,
                "bullets": item.bullets,
            }
            for item in profile.work_experiences
        ],
        "project_experiences": [
            {
                "name": item.name,
                "role": item.role,
                "start": item.start,
                "end": item.end,
                "tags": item.tags,
                "bullets": item.bullets,
            }
            for item in profile.project_experiences
        ],
        "education": [
            {
                "school": item.school,
                "degree": item.degree,
                "major": item.major,
                "start": item.start,
                "end": item.end,
            }
            for item in profile.education
        ],
    }
