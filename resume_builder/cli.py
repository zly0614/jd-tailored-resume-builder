from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .latex_setup import install_latex
from .models import LLMConfig
from .service import generate_resume, store_feedback


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate tailored LaTeX resumes from a master profile and job description.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Generate a tailored resume in LaTeX format.")
    generate.add_argument("--profile", required=True, help="Path to the candidate master profile JSON file.")
    generate.add_argument("--jd-file", required=True, help="Path to the JD text file.")
    generate.add_argument("--out", required=True, help="Output path for the generated .tex file.")
    generate.add_argument("--work-limit", type=int, default=4, help="Maximum number of work experiences to include.")
    generate.add_argument("--project-limit", type=int, default=3, help="Maximum number of project experiences to include.")
    generate.add_argument("--skill-limit", type=int, default=12, help="Maximum number of skills to include.")
    generate.add_argument("--mode", choices=["heuristic", "llm"], default="llm", help="Resume generation mode.")
    generate.add_argument("--language", choices=["zh", "en"], default="zh", help="Resume output language.")
    generate.add_argument("--template", default="modern_blocks", help="Resume template key.")
    generate.add_argument("--memory-file", default="memory.md", help="Path to the feedback memory markdown file.")
    generate.add_argument("--feedback", default="", help="Optional inline user feedback to append after generation.")
    generate.add_argument("--skip-feedback", action="store_true", help="Skip interactive feedback collection.")
    generate.add_argument("--compile-pdf", action="store_true", help="Compile the generated .tex file into a PDF when a LaTeX engine is available.")
    generate.add_argument("--llm-model", default="", help="Override the LLM model name.")
    generate.add_argument("--llm-base-url", default="", help="Override the OpenAI-compatible base URL.")
    generate.add_argument("--llm-api-key", default="", help="Override the API key for this run.")

    serve = subparsers.add_parser("serve", help="Start the local web app.")
    serve.add_argument("--host", default="127.0.0.1", help="Host for the local web server.")
    serve.add_argument("--port", type=int, default=8000, help="Port for the local web server.")

    install_latex_parser = subparsers.add_parser("install-latex", help="Install a local LaTeX engine for PDF export.")
    install_latex_parser.add_argument("--provider", choices=["auto", "miktex-private", "choco"], default="auto", help="Package provider to use for installing LaTeX.")

    feedback = subparsers.add_parser("feedback", help="Append standalone feedback into the memory file.")
    feedback.add_argument("--memory-file", default="memory.md", help="Path to the feedback memory markdown file.")
    feedback.add_argument("--target-role", default="", help="Target role for this feedback entry.")
    feedback.add_argument("--feedback", required=True, help="Feedback content to store.")
    feedback.add_argument("--out", default="", help="Optional output file related to the feedback.")
    feedback.add_argument("--model", default="", help="Optional model name related to the feedback.")

    return parser


def run_generate(args: argparse.Namespace) -> int:
    jd_text = Path(args.jd_file).read_text(encoding="utf-8")
    result = generate_resume(
        profile_path=args.profile,
        jd_text=jd_text,
        out_path=args.out,
        mode=args.mode,
        memory_file=args.memory_file,
        work_limit=args.work_limit,
        project_limit=args.project_limit,
        skill_limit=args.skill_limit,
        compile_pdf=args.compile_pdf,
        language=args.language,
        template_name=args.template,
        llm_config=LLMConfig(
            model=args.llm_model,
            base_url=args.llm_base_url,
            api_key=args.llm_api_key,
        ),
    )

    feedback = args.feedback.strip()
    if not feedback and not args.skip_feedback and sys.stdin.isatty():
        feedback = _prompt_feedback()

    if feedback:
        store_feedback(
            memory_file=args.memory_file,
            target_role=result.target_title,
            feedback=feedback,
            output_path=result.output_path,
            model=result.used_model,
        )
        print(f"Stored feedback in: {args.memory_file}")

    print(f"Generated LaTeX resume at: {result.output_path}")
    if args.compile_pdf:
        print(result.pdf_message)
        if result.pdf_path:
            print(f"PDF path: {result.pdf_path}")
    if result.fallback_reason:
        print(result.fallback_reason)
    return 0


def run_feedback(args: argparse.Namespace) -> int:
    store_feedback(
        memory_file=args.memory_file,
        target_role=args.target_role,
        feedback=args.feedback,
        output_path=args.out,
        model=args.model,
    )
    print(f"Stored feedback in: {args.memory_file}")
    return 0


def run_install_latex(args: argparse.Namespace) -> int:
    result = install_latex(provider=args.provider)
    print(result.message)
    if result.command:
        print(f"Install command: {result.command}")
    if result.engine_path:
        print(f"Detected engine: {result.engine_path}")
    return 0 if result.success else 1


def run_serve(args: argparse.Namespace) -> int:
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError("uvicorn is required to run the web app.") from exc

    uvicorn.run("resume_builder.web:app", host=args.host, port=args.port, reload=False)
    return 0


def _prompt_feedback() -> str:
    print("Resume generated. Enter feedback to improve future results, or press Enter to skip:")
    return input("> ").strip()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        return run_generate(args)
    if args.command == "install-latex":
        return run_install_latex(args)
    if args.command == "serve":
        return run_serve(args)
    if args.command == "feedback":
        return run_feedback(args)

    parser.print_help()
    return 1
