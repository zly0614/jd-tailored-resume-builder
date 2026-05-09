from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from .service import default_output_path, generate_resume_from_text, store_feedback

app = FastAPI(title="Jianli Creator")
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROFILE = (ROOT / "data" / "master_profile.sample.json").read_text(encoding="utf-8")
DEFAULT_JD = (ROOT / "data" / "sample_jd.txt").read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "profile_text": DEFAULT_PROFILE,
            "jd_text": DEFAULT_JD,
            "latex": "",
            "message": "",
            "error": "",
            "target_role": "",
            "output_path": "",
            "used_model": "",
            "mode": "llm",
            "memory_file": "memory.md",
        },
    )


@app.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    profile_text: str = Form(...),
    jd_text: str = Form(...),
    mode: str = Form("llm"),
    memory_file: str = Form("memory.md"),
) -> HTMLResponse:
    try:
        result = generate_resume_from_text(
            profile_text=profile_text,
            jd_text=jd_text,
            out_path=default_output_path(),
            mode=mode,
            memory_file=memory_file,
        )
        message = f"Resume generated. Current model: {result.used_model}."
        if result.fallback_reason:
            message = f"{message} {result.fallback_reason}"
        context = {
            "profile_text": profile_text,
            "jd_text": jd_text,
            "latex": result.latex,
            "message": message,
            "error": "",
            "target_role": result.target_title,
            "output_path": result.output_path,
            "used_model": result.used_model,
            "mode": mode,
            "memory_file": memory_file,
        }
    except Exception as exc:
        context = {
            "profile_text": profile_text,
            "jd_text": jd_text,
            "latex": "",
            "message": "",
            "error": f"Generation failed: {exc}",
            "target_role": "",
            "output_path": "",
            "used_model": "",
            "mode": mode,
            "memory_file": memory_file,
        }
    return templates.TemplateResponse(request, "index.html", context)


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
    feedback_text: str = Form(...),
) -> HTMLResponse:
    message = "Feedback saved into memory.md for future generations."
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
        "index.html",
        {
            "profile_text": profile_text,
            "jd_text": jd_text,
            "latex": latex,
            "message": message,
            "error": error,
            "target_role": target_role,
            "output_path": output_path,
            "used_model": used_model,
            "mode": mode,
            "memory_file": memory_file,
        },
    )


@app.get("/download")
async def download(path: str) -> FileResponse:
    file_path = Path(path)
    return FileResponse(file_path, filename=file_path.name, media_type="application/x-tex")
