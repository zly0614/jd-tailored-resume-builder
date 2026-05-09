from __future__ import annotations

from .models import CandidateProfile, RankedResume


def _escape_latex(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def _render_bullets(items: list[str]) -> str:
    if not items:
        return ""
    rows = "\n".join(f"\\item {_escape_latex(item)}" for item in items)
    return "\\begin{itemize}\n" + rows + "\n\\end{itemize}"


def render_resume_latex(profile: CandidateProfile, ranked_resume: RankedResume) -> str:
    basic = profile.basic_info
    links = " \\textbar{} ".join(_escape_latex(item) for item in basic.links)
    skills = " \\textbar{} ".join(_escape_latex(item) for item in ranked_resume.highlighted_skills)

    work_sections = []
    for item in ranked_resume.work_experiences:
        work_sections.append(
            "\n".join(
                [
                    f"\\textbf{{{_escape_latex(item.title)}}} \\hfill {_escape_latex(item.start)} -- {_escape_latex(item.end)}\\\\",
                    f"{_escape_latex(item.company)} \\hfill {_escape_latex(item.location)}\\\\",
                    _render_bullets(item.bullets),
                ]
            )
        )

    project_sections = []
    for item in ranked_resume.project_experiences:
        project_sections.append(
            "\n".join(
                [
                    f"\\textbf{{{_escape_latex(item.name)}}} \\hfill {_escape_latex(item.start)} -- {_escape_latex(item.end)}\\\\",
                    f"{_escape_latex(item.role)}\\\\",
                    _render_bullets(item.bullets),
                ]
            )
        )

    education_rows = []
    for item in profile.education:
        education_rows.append(
            f"\\textbf{{{_escape_latex(item.school)}}} \\hfill {_escape_latex(item.start)} -- {_escape_latex(item.end)}\\\\"
            f"{_escape_latex(item.degree)} in {_escape_latex(item.major)}\\\\"
        )

    certificate_rows = []
    for item in profile.certificates:
        certificate_rows.append(
            f"{_escape_latex(item.name)} ({_escape_latex(item.issuer)}, {_escape_latex(item.year)})\\\\"
        )

    return f"""\\documentclass[11pt]{{article}}
\\usepackage[a4paper,margin=0.7in]{{geometry}}
\\usepackage{{enumitem}}
\\usepackage[hidelinks]{{hyperref}}
\\setlist[itemize]{{leftmargin=1.2em, itemsep=0.2em, topsep=0.2em}}
\\pagestyle{{empty}}

\\begin{{document}}

\\begin{{center}}
{{\\LARGE \\textbf{{{_escape_latex(basic.name)}}}}}\\\\
{_escape_latex(basic.title)}\\\\
{_escape_latex(basic.email)} \\textbar{{}} {_escape_latex(basic.phone)} \\textbar{{}} {_escape_latex(basic.location)}\\\\
{links}
\\end{{center}}

\\section*{{Target Role}}
{_escape_latex(ranked_resume.target_title)}

\\section*{{Professional Summary}}
{_escape_latex(ranked_resume.summary)}

\\section*{{Selected Skills}}
{skills}

\\section*{{Work Experience}}
{"\\vspace{0.5em}\n".join(work_sections)}

\\section*{{Project Experience}}
{"\\vspace{0.5em}\n".join(project_sections)}

\\section*{{Education}}
{"\n".join(education_rows)}

\\section*{{Certificates}}
{"\n".join(certificate_rows)}

\\end{{document}}
"""
