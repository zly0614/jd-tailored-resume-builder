from __future__ import annotations

import json
from pathlib import Path

from .models import BasicInfo, CandidateProfile, Certificate, Education, ProjectExperience, WorkExperience


def load_profile(path: str | Path) -> CandidateProfile:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return load_profile_from_dict(payload)


def load_profile_from_text(raw_text: str) -> CandidateProfile:
    payload = json.loads(raw_text)
    return load_profile_from_dict(payload)


def load_profile_from_dict(payload: dict) -> CandidateProfile:
    basic_info = BasicInfo(**payload["basic_info"])
    work_experiences = [WorkExperience(**item) for item in payload.get("work_experiences", [])]
    project_experiences = [ProjectExperience(**item) for item in payload.get("project_experiences", [])]
    education = [Education(**item) for item in payload.get("education", [])]
    certificates = [Certificate(**item) for item in payload.get("certificates", [])]

    return CandidateProfile(
        basic_info=basic_info,
        summary_options=payload.get("summary_options", []),
        skills=payload.get("skills", {}),
        work_experiences=work_experiences,
        project_experiences=project_experiences,
        education=education,
        certificates=certificates,
    )
