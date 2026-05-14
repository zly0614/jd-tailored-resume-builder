from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BasicInfo:
    name: str
    title: str
    email: str
    phone: str
    location: str
    links: list[str] = field(default_factory=list)
    photo_path: str = ""


@dataclass
class WorkExperience:
    company: str
    title: str
    start: str
    end: str
    location: str
    tags: list[str] = field(default_factory=list)
    bullets: list[str] = field(default_factory=list)


@dataclass
class ProjectExperience:
    name: str
    role: str
    start: str
    end: str
    tags: list[str] = field(default_factory=list)
    bullets: list[str] = field(default_factory=list)


@dataclass
class Education:
    school: str
    degree: str
    major: str
    start: str
    end: str


@dataclass
class Certificate:
    name: str
    issuer: str
    year: str


@dataclass
class CandidateProfile:
    basic_info: BasicInfo
    summary_options: list[str] = field(default_factory=list)
    skills: dict[str, list[str]] = field(default_factory=dict)
    work_experiences: list[WorkExperience] = field(default_factory=list)
    project_experiences: list[ProjectExperience] = field(default_factory=list)
    education: list[Education] = field(default_factory=list)
    certificates: list[Certificate] = field(default_factory=list)


@dataclass
class JobDescription:
    raw_text: str
    keywords: list[str]
    responsibilities: list[str]


@dataclass
class RankedResume:
    target_title: str
    summary: str
    highlighted_skills: list[str]
    work_experiences: list[WorkExperience]
    project_experiences: list[ProjectExperience]


@dataclass
class LLMConfig:
    model: str = ""
    base_url: str = ""
    api_key: str = ""
