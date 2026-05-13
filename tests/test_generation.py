from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from resume_builder.draft import build_resume_draft
from resume_builder.jd_parser import parse_job_description
from resume_builder.latex_renderer import render_resume_latex, render_resume_latex_from_draft
from resume_builder.memory import append_feedback, load_memory_context
from resume_builder.pdf import compile_tex_to_pdf
from resume_builder.profile_loader import load_profile
from resume_builder.ranking import build_ranked_resume
from resume_builder.web import app


class ResumeGenerationTest(unittest.TestCase):
    def test_can_generate_latex_resume(self) -> None:
        root = Path(__file__).resolve().parent.parent
        profile = load_profile(root / "data" / "master_profile.sample.json")
        jd_text = (root / "data" / "sample_jd.txt").read_text(encoding="utf-8")

        jd = parse_job_description(jd_text)
        ranked_resume = build_ranked_resume(profile, jd, language="zh")
        latex = render_resume_latex(profile, ranked_resume, language="zh")

        self.assertIn("\\resumeSection{工作经历}", latex)
        self.assertIn("张皓淼", latex)
        self.assertIn("高级 AI 产品经理", latex)

        with tempfile.TemporaryDirectory() as temp_dir:
            out_path = Path(temp_dir) / "resume.tex"
            out_path.write_text(latex, encoding="utf-8")
            self.assertTrue(out_path.exists())

    def test_draft_layer_can_be_rendered(self) -> None:
        root = Path(__file__).resolve().parent.parent
        profile = load_profile(root / "data" / "master_profile.sample.json")
        jd_text = (root / "data" / "sample_jd.txt").read_text(encoding="utf-8")

        jd = parse_job_description(jd_text)
        ranked_resume = build_ranked_resume(profile, jd, language="zh")
        draft = build_resume_draft(profile, ranked_resume, language="zh")
        latex = render_resume_latex_from_draft(draft, template_name="modern_blocks")

        self.assertEqual(draft.sections[0].title, "目标岗位")
        self.assertTrue(any(section.key == "project" for section in draft.sections))
        self.assertIn("\\resumeSection{项目经历}", latex)

    def test_feedback_memory_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.md"
            append_feedback(
                path=memory_path,
                target_role="高级 AI 产品经理",
                feedback="请进一步突出知识库和项目成果。",
                output_path="outputs/resume.tex",
                model="MiMo-V2.5-Pro",
            )
            memory_text = load_memory_context(memory_path)

        self.assertIn("高级 AI 产品经理", memory_text)
        self.assertIn("请进一步突出知识库和项目成果。", memory_text)

    def test_web_homepage_renders(self) -> None:
        client = TestClient(app)
        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Jianli Creator", response.text)
        self.assertIn("Template Preview", response.text)
        self.assertIn("Resume Knowledge Base", response.text)
        self.assertIn("/profile-builder", response.text)

    def test_web_step_routes_render(self) -> None:
        client = TestClient(app)

        profile_response = client.post("/profile-builder", data={"template_name": "modern_blocks"})
        self.assertEqual(profile_response.status_code, 200)
        self.assertIn("建立个人简历知识库", profile_response.text)
        self.assertIn("/customize", profile_response.text)

        customize_response = client.post(
            "/customize",
            data={
                "template_name": "modern_blocks",
                "profile_text": (Path(__file__).resolve().parent.parent / "data" / "master_profile.sample.json").read_text(encoding="utf-8"),
            },
        )
        self.assertEqual(customize_response.status_code, 200)
        self.assertIn("目标岗位 JD", customize_response.text)
        self.assertIn("generate", customize_response.text)

    def test_pdf_compile_graceful_when_engine_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tex_path = Path(temp_dir) / "resume.tex"
            tex_path.write_text("\\documentclass{article}\\begin{document}test\\end{document}", encoding="utf-8")
            result = compile_tex_to_pdf(tex_path)

        if result.success:
            self.assertTrue(Path(result.pdf_path).name.endswith(".pdf"))
        else:
            self.assertTrue("LaTeX compiler" in result.message or "LaTeX engine" in result.message)
