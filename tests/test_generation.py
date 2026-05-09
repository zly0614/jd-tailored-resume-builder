from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from resume_builder.jd_parser import parse_job_description
from resume_builder.latex_renderer import render_resume_latex
from resume_builder.memory import append_feedback, load_memory_context
from resume_builder.profile_loader import load_profile
from resume_builder.ranking import build_ranked_resume
from resume_builder.web import app


class ResumeGenerationTest(unittest.TestCase):
    def test_can_generate_latex_resume(self) -> None:
        root = Path(__file__).resolve().parent.parent
        profile = load_profile(root / "data" / "master_profile.sample.json")
        jd_text = (root / "data" / "sample_jd.txt").read_text(encoding="utf-8")

        jd = parse_job_description(jd_text)
        ranked_resume = build_ranked_resume(profile, jd)
        latex = render_resume_latex(profile, ranked_resume)

        self.assertIn("\\section*{Work Experience}", latex)
        self.assertIn("Alex Chen", latex)
        self.assertIn("AI Product Manager", latex)

        with tempfile.TemporaryDirectory() as temp_dir:
            out_path = Path(temp_dir) / "resume.tex"
            out_path.write_text(latex, encoding="utf-8")
            self.assertTrue(out_path.exists())

    def test_feedback_memory_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.md"
            append_feedback(
                path=memory_path,
                target_role="AI Product Manager",
                feedback="Emphasize measurable impact and knowledge-base work.",
                output_path="outputs/resume.tex",
                model="gpt-4.1-mini",
            )
            memory_text = load_memory_context(memory_path)

        self.assertIn("AI Product Manager", memory_text)
        self.assertIn("Emphasize measurable impact and knowledge-base work.", memory_text)

    def test_web_homepage_renders(self) -> None:
        client = TestClient(app)
        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Jianli Creator", response.text)
        self.assertIn("Generate LaTeX Resume", response.text)
