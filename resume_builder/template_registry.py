from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResumeTemplate:
    key: str
    label: str
    description: str
    preview_image: str


TEMPLATES: list[ResumeTemplate] = [
    ResumeTemplate(
        key="modern_blocks",
        label="Modern Blocks",
        description="Chinese-friendly layout with clear section dividers and block-based experience cards.",
        preview_image="/static/template_previews/modern_blocks.svg",
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
        }
        for template in TEMPLATES
    ]
