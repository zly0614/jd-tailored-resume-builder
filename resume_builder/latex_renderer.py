from __future__ import annotations

from pathlib import Path
from string import Template

from .draft import ResumeDraft, build_resume_draft
from .models import CandidateProfile, RankedResume
from .template_registry import get_template


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


def _photo_block(photo_path: str, language: str) -> str:
    if photo_path:
        candidate = Path(photo_path)
        if candidate.exists():
            normalized = candidate.resolve().as_posix()
            return (
                r"\includegraphics[width=2.95cm,height=3.95cm,keepaspectratio]"
                + "{\\detokenize{"
                + normalized
                + "}}"
            )
    label = "\u7167\u7247" if language == "zh" else "Photo"
    return (
        r"\fcolorbox{resumeaccent}{white}{"
        r"\begin{minipage}[c][3.95cm][c]{2.95cm}"
        r"\centering\small\color{resumelight}"
        + _escape_latex(label)
        + r"\end{minipage}}"
    )


def _normalize_url(url: str) -> str:
    cleaned = url.strip()
    if cleaned.startswith(("http://", "https://", "mailto:")):
        return cleaned
    return "https://" + cleaned


def _render_links(items: list[str]) -> str:
    rendered: list[str] = []
    for item in items:
        text = item.strip()
        if not text:
            continue
        if ":" in text:
            label, value = text.split(":", 1)
            safe_label = _escape_latex(label.strip())
            value = value.strip()
            safe_value = _escape_latex(value)
            rendered.append(
                safe_label + r": " + r"\href{" + _normalize_url(value) + "}{" + safe_value + "}"
            )
        else:
            rendered.append(_escape_latex(text))
    if not rendered:
        return ""
    if len(rendered) == 1:
        return rendered[0]
    if len(rendered) == 2:
        return rendered[0] + r" \quad | \quad " + rendered[1]
    return (
        rendered[0]
        + r" \quad | \quad "
        + rendered[1]
        + r"\\[0.12em]"
        + r" \quad | \quad ".join(rendered[2:])
    )


def _render_bullets(items: list[str]) -> str:
    if not items:
        return ""
    rows = "\n".join(f"\\item {_escape_latex(item)}" for item in items)
    return "\\begin{itemize}\n" + rows + "\n\\end{itemize}"


def _render_text_section(content: str) -> str:
    return "{\\normalsize " + _escape_latex(content) + "}\\par"


def _render_card(heading: str, subheading: str, date_range: str, bullets: list[str]) -> str:
    body = [
        f"\\resumeEntry{{{_escape_latex(heading)}}}{{{_escape_latex(date_range)}}}",
    ]
    if subheading:
        body.append(f"\\resumeMeta{{{_escape_latex(subheading)}}}")
    if bullets:
        body.append(_render_bullets(bullets))
    return "\\resumeCard{\n" + "\n".join(body) + "\n}"


def _render_item_section(section) -> str:
    blocks = [_render_card(item.heading, item.subheading, item.date_range, item.bullets) for item in section.items]
    return "\n\\vspace{0.45em}\n".join(blocks)


def render_resume_latex_from_draft(draft: ResumeDraft, template_name: str = "modern_blocks") -> str:
    template = get_template(template_name)
    if template.key != "modern_blocks":
        raise ValueError(f"Unsupported template: {template_name}")

    section_chunks: list[str] = []
    for section in draft.sections:
        chunk = [f"\\resumeSection{{{_escape_latex(section.title)}}}"]
        if section.layout in {"text", "chips"}:
            chunk.append(_render_text_section(section.content))
        else:
            chunk.append(_render_item_section(section))
        section_chunks.append("\n".join(chunk))

    page = Template(
        r"""\documentclass[10.5pt]{article}
\usepackage[a4paper,margin=0.52in]{geometry}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{iftex}
\usepackage{array}
\usepackage{graphicx}
\usepackage{xcolor}
\ifXeTeX
\usepackage[UTF8]{ctex}
\fi

\definecolor{resumeink}{HTML}{1E1E1E}
\definecolor{resumeaccent}{HTML}{1274C9}
\definecolor{resumelight}{HTML}{5B5B5B}
\definecolor{resumeline}{HTML}{A9CBF2}
\definecolor{resumebg}{HTML}{F7FBFF}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\setlist[itemize]{leftmargin=1.3em, itemsep=0.18em, topsep=0.18em, parsep=0em, partopsep=0em}

\newcommand{\resumeSection}[1]{%
  \vspace{1.0em}%
  {\fontsize{17}{19}\selectfont\bfseries\color{resumeaccent} #1}\par
  \vspace{0.02em}%
  {\color{resumeline}\rule{\linewidth}{0.85pt}}\par
  \vspace{0.52em}%
}

\newcommand{\resumeEntry}[2]{%
  \begin{tabular*}{\linewidth}{@{}p{0.75\linewidth}@{\extracolsep{\fill}}>{\raggedleft\arraybackslash}p{0.21\linewidth}@{}}
  {\bfseries\large\color{resumeink} #1} & {\normalsize\color{resumeink} #2} \\
  \end{tabular*}\par
}

\newcommand{\resumeMeta}[1]{%
  {\small\color{resumeink} #1}\par
}

\newcommand{\resumeCard}[1]{%
  \noindent\fcolorbox{resumeline}{resumebg}{%
    \begin{minipage}{0.972\linewidth}%
      \vspace{0.32em}%
      \hspace{0.34em}\begin{minipage}{0.952\linewidth}%
      #1
      \end{minipage}%
      \vspace{0.14em}%
    \end{minipage}%
  }\par
}

\begin{document}

\begin{tabular*}{\linewidth}{@{}p{0.76\linewidth}@{\extracolsep{\fill}}p{0.18\linewidth}@{}}
\begin{minipage}[t]{0.76\linewidth}
\vspace{0pt}
{\fontsize{25}{29}\selectfont\bfseries\color{resumeink} $name}\par
\vspace{0.18em}
{\small\color{resumeink} $contact}\par
\vspace{0.08em}
{\footnotesize\color{resumelight} $links}\par
\end{minipage}
&
\begin{minipage}[t]{0.18\linewidth}
\vspace{-0.28em}
\raggedleft
$photo
\end{minipage}
\end{tabular*}

$sections

\end{document}
"""
    )

    return page.substitute(
        name=_escape_latex(draft.name),
        contact="\\\\[0.16em]".join(_escape_latex(line) for line in draft.contact_lines),
        links=_render_links(draft.link_lines),
        photo=_photo_block(draft.photo_path, draft.language),
        sections="\n\n".join(section_chunks),
    )


def render_resume_latex(
    profile: CandidateProfile,
    ranked_resume: RankedResume,
    language: str = "en",
    template_name: str = "modern_blocks",
) -> str:
    draft = build_resume_draft(profile, ranked_resume, language=language)
    return render_resume_latex_from_draft(draft, template_name=template_name)
