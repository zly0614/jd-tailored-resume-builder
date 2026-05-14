from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .models import CandidateProfile, RankedResume


@dataclass
class DraftBlock:
    heading: str
    subheading: str
    date_range: str = ""
    bullets: list[str] = field(default_factory=list)


@dataclass
class DraftSection:
    key: str
    title: str
    layout: str
    content: str = ""
    items: list[DraftBlock] = field(default_factory=list)


@dataclass
class ResumeDraft:
    name: str
    title: str
    contact_lines: list[str]
    link_lines: list[str]
    photo_path: str
    language: str
    target_title: str
    sections: list[DraftSection]

    def to_dict(self) -> dict:
        return asdict(self)


def build_resume_draft(profile: CandidateProfile, ranked_resume: RankedResume, language: str = "zh") -> ResumeDraft:
    labels = _labels(language)
    basic = profile.basic_info

    contact_lines = [
        f"{labels['phone']}{basic.phone}    {labels['email']}{basic.email}",
        f"{labels['location']}{basic.location}",
    ]

    work_items = [
        DraftBlock(
            heading=item.company,
            subheading=_join_meta(
                [
                    f"{labels['job']}{item.title}" if item.title else "",
                    f"{labels['location']}{item.location}" if item.location else "",
                ]
            ),
            date_range=f"{item.start}--{item.end}",
            bullets=item.bullets,
        )
        for item in ranked_resume.work_experiences
    ]

    project_items = [
        DraftBlock(
            heading=item.name,
            subheading=f"{labels['role']}{item.role}" if item.role else "",
            date_range=f"{item.start}--{item.end}",
            bullets=item.bullets,
        )
        for item in ranked_resume.project_experiences
    ]

    education_items = [
        DraftBlock(
            heading=item.school,
            subheading=_join_meta([item.degree, item.major]),
            date_range=f"{item.start}--{item.end}",
        )
        for item in profile.education
    ]

    certificate_items = [
        DraftBlock(
            heading=item.name,
            subheading=_join_meta([item.issuer, item.year]),
        )
        for item in profile.certificates
    ]

    sections = [
        DraftSection(key="target", title=labels["target"], layout="text", content=ranked_resume.target_title),
        DraftSection(key="summary", title=labels["summary"], layout="text", content=ranked_resume.summary),
        DraftSection(
            key="skills",
            title=labels["skills"],
            layout="chips",
            content=" / ".join(ranked_resume.highlighted_skills),
        ),
        DraftSection(key="work", title=labels["work"], layout="timeline", items=work_items),
        DraftSection(key="project", title=labels["project"], layout="timeline", items=project_items),
        DraftSection(key="education", title=labels["education"], layout="stack", items=education_items),
        DraftSection(key="certificates", title=labels["certificates"], layout="stack", items=certificate_items),
    ]

    return ResumeDraft(
        name=basic.name,
        title=basic.title,
        contact_lines=contact_lines,
        link_lines=basic.links,
        photo_path=basic.photo_path,
        language=language,
        target_title=ranked_resume.target_title,
        sections=sections,
    )


def _join_meta(parts: list[str]) -> str:
    return "    ".join(part for part in parts if part)


def _labels(language: str) -> dict[str, str]:
    if language == "zh":
        return {
            "phone": "电话：",
            "email": "邮箱：",
            "location": "地点：",
            "job": "岗位：",
            "role": "角色：",
            "target": "目标岗位",
            "summary": "职业摘要",
            "skills": "专业技能",
            "work": "工作经历",
            "project": "项目经历",
            "education": "教育背景",
            "certificates": "其他资质",
        }
    return {
        "phone": "Phone: ",
        "email": "Email: ",
        "location": "Location: ",
        "job": "Title: ",
        "role": "Role: ",
        "target": "Target Role",
        "summary": "Professional Summary",
        "skills": "Selected Skills",
        "work": "Work Experience",
        "project": "Project Experience",
        "education": "Education",
        "certificates": "Certificates",
    }
