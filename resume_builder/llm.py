from __future__ import annotations

import json
import os
from dataclasses import replace
from urllib import error, request

from .models import CandidateProfile, JobDescription, ProjectExperience, RankedResume, WorkExperience


class LLMEnhancer:
    """Use an OpenAI-compatible chat completion endpoint to refine the resume draft."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int = 60,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.timeout_seconds = timeout_seconds

    def is_available(self) -> bool:
        return bool(self.api_key)

    def enhance(
        self,
        profile: CandidateProfile,
        jd: JobDescription,
        ranked_resume: RankedResume,
        memory_context: str = "",
    ) -> RankedResume:
        if not self.is_available():
            return ranked_resume

        prompt = self._build_prompt(profile, jd, ranked_resume, memory_context)
        try:
            response_text = self._request_completion(prompt)
            payload = self._extract_json(response_text)
            return self._merge_response(ranked_resume, payload)
        except Exception:
            return ranked_resume

    def _build_prompt(
        self,
        profile: CandidateProfile,
        jd: JobDescription,
        ranked_resume: RankedResume,
        memory_context: str,
    ) -> str:
        profile_payload = {
            "basic_info": {
                "name": profile.basic_info.name,
                "title": profile.basic_info.title,
                "location": profile.basic_info.location,
            },
            "skills": profile.skills,
        }
        draft_payload = {
            "target_title": ranked_resume.target_title,
            "summary": ranked_resume.summary,
            "highlighted_skills": ranked_resume.highlighted_skills,
            "work_experiences": [
                {
                    "company": item.company,
                    "title": item.title,
                    "start": item.start,
                    "end": item.end,
                    "location": item.location,
                    "tags": item.tags,
                    "bullets": item.bullets,
                }
                for item in ranked_resume.work_experiences
            ],
            "project_experiences": [
                {
                    "name": item.name,
                    "role": item.role,
                    "start": item.start,
                    "end": item.end,
                    "tags": item.tags,
                    "bullets": item.bullets,
                }
                for item in ranked_resume.project_experiences
            ],
        }
        instructions = {
            "goal": "Refine the draft resume using the candidate profile, the target JD, and past feedback memory.",
            "rules": [
                "Preserve factual accuracy. Do not invent employers, achievements, technologies, or responsibilities.",
                "Emphasize the experience, skills, and measurable outcomes most relevant to the JD.",
                "Keep the summary concise and role-targeted.",
                "Make bullets action-oriented and outcome-aware.",
                "Respect historical feedback preferences when possible.",
                "Return JSON only with no Markdown wrapper.",
            ],
            "output_schema": {
                "summary": "string",
                "highlighted_skills": ["string"],
                "work_experiences": [{"bullets": ["string"]}],
                "project_experiences": [{"bullets": ["string"]}],
            },
        }
        return "\n".join(
            [
                "You are a senior resume strategist. Rewrite the draft into strong, job-targeted resume content.",
                json.dumps(instructions, ensure_ascii=False, indent=2),
                "[Candidate Basics]",
                json.dumps(profile_payload, ensure_ascii=False, indent=2),
                "[Target JD]",
                jd.raw_text,
                "[Draft Resume]",
                json.dumps(draft_payload, ensure_ascii=False, indent=2),
                "[Feedback Memory]",
                memory_context or "No feedback memory yet.",
            ]
        )

    def _request_completion(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "temperature": 0.3,
            "messages": [
                {
                    "role": "system",
                    "content": "You rewrite resume drafts into concise, job-targeted resume content and always return valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
        }

        endpoint = f"{self.base_url}/chat/completions"
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            endpoint,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as resp:
                response_payload = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM request failed: {exc.code} {details}") from exc

        return response_payload["choices"][0]["message"]["content"]

    def _extract_json(self, raw_content: str) -> dict:
        content = raw_content.strip()
        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:].strip()
        return json.loads(content)

    def _merge_response(self, ranked_resume: RankedResume, payload: dict) -> RankedResume:
        work_experiences = self._merge_work_items(ranked_resume.work_experiences, payload.get("work_experiences", []))
        project_experiences = self._merge_project_items(
            ranked_resume.project_experiences,
            payload.get("project_experiences", []),
        )
        highlighted_skills = payload.get("highlighted_skills") or ranked_resume.highlighted_skills
        summary = payload.get("summary") or ranked_resume.summary

        return RankedResume(
            target_title=ranked_resume.target_title,
            summary=summary,
            highlighted_skills=highlighted_skills,
            work_experiences=work_experiences,
            project_experiences=project_experiences,
        )

    def _merge_work_items(self, source: list[WorkExperience], updates: list[dict]) -> list[WorkExperience]:
        result: list[WorkExperience] = []
        for index, item in enumerate(source):
            update = updates[index] if index < len(updates) else {}
            result.append(replace(item, bullets=update.get("bullets", item.bullets)))
        return result

    def _merge_project_items(self, source: list[ProjectExperience], updates: list[dict]) -> list[ProjectExperience]:
        result: list[ProjectExperience] = []
        for index, item in enumerate(source):
            update = updates[index] if index < len(updates) else {}
            result.append(replace(item, bullets=update.get("bullets", item.bullets)))
        return result
