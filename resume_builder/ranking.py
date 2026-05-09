from __future__ import annotations

from collections import Counter

from .models import CandidateProfile, JobDescription, ProjectExperience, RankedResume, WorkExperience


def _score_text_fragments(fragments: list[str], keywords: list[str], tags: list[str]) -> int:
    score = 0
    combined = " ".join(fragments + tags).lower()
    counts = Counter(combined.split())

    for keyword in keywords:
        if keyword in combined:
            score += 3
        score += counts.get(keyword, 0)

    return score


def _select_top_work_items(items: list[WorkExperience], keywords: list[str], limit: int) -> list[WorkExperience]:
    ranked = sorted(
        items,
        key=lambda item: _score_text_fragments(
            [item.company, item.title, *item.bullets],
            keywords,
            item.tags,
        ),
        reverse=True,
    )
    return ranked[:limit]


def _select_top_project_items(items: list[ProjectExperience], keywords: list[str], limit: int) -> list[ProjectExperience]:
    ranked = sorted(
        items,
        key=lambda item: _score_text_fragments(
            [item.name, item.role, *item.bullets],
            keywords,
            item.tags,
        ),
        reverse=True,
    )
    return ranked[:limit]


def _build_summary(profile: CandidateProfile, jd: JobDescription) -> str:
    if profile.summary_options:
        ranked = sorted(
            profile.summary_options,
            key=lambda item: _score_text_fragments([item], jd.keywords, []),
            reverse=True,
        )
        seed = ranked[0]
    else:
        seed = f"{profile.basic_info.title} with experience in cross-functional delivery, project execution, and business impact."

    top_keywords = ", ".join(jd.keywords[:6])
    if top_keywords:
        return f"{seed} This version emphasizes experience related to {top_keywords}."
    return seed


def _flatten_skills(skills: dict[str, list[str]]) -> list[str]:
    result: list[str] = []
    for category_items in skills.values():
        result.extend(category_items)
    return result


def build_ranked_resume(
    profile: CandidateProfile,
    jd: JobDescription,
    work_limit: int = 4,
    project_limit: int = 3,
    skill_limit: int = 12,
) -> RankedResume:
    all_skills = _flatten_skills(profile.skills)
    highlighted_skills = sorted(
        all_skills,
        key=lambda item: _score_text_fragments([item], jd.keywords, []),
        reverse=True,
    )[:skill_limit]

    ranked_work = _select_top_work_items(profile.work_experiences, jd.keywords, work_limit)
    ranked_projects = _select_top_project_items(profile.project_experiences, jd.keywords, project_limit)

    return RankedResume(
        target_title=_guess_target_title(jd),
        summary=_build_summary(profile, jd),
        highlighted_skills=highlighted_skills,
        work_experiences=ranked_work,
        project_experiences=ranked_projects,
    )


def _guess_target_title(jd: JobDescription) -> str:
    first_line = jd.raw_text.strip().splitlines()[0] if jd.raw_text.strip() else ""
    if 2 <= len(first_line) <= 40:
        return first_line
    return "Target Role"
