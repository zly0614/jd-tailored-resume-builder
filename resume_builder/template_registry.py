from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResumeTemplate:
    key: str
    label: str
    description: str
    preview_image: str
    source_file: str = ""


DEFAULT_TEMPLATE_KEY = "zhang_leyan_default"

TEMPLATES: list[ResumeTemplate] = [
    ResumeTemplate(
        key=DEFAULT_TEMPLATE_KEY,
        label="张乐言默认模板",
        description="Default resume template based on 张乐言秋招简历 - 副本.doc.",
        preview_image="/static/template_previews/zhang_leyan_default.svg",
        source_file="/static/template_files/zhang_leyan_default.doc",
    ),
]


def get_template(template_name: str) -> ResumeTemplate:
    for template in TEMPLATES:
        if template.key == template_name:
            return template
    return TEMPLATES[0]


def template_options() -> list[dict[str, str]]:
    return [
        {
            "key": template.key,
            "label": template.label,
            "description": template.description,
            "preview_image": template.preview_image,
            "source_file": template.source_file,
        }
        for template in TEMPLATES
    ]
