from __future__ import annotations

import json
import os
from dataclasses import replace
from urllib import error, request

from .models import CandidateProfile, Certificate, Education, JobDescription, LLMConfig, ProjectExperience, RankedResume, WorkExperience


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

    @classmethod
    def from_config(cls, config: LLMConfig) -> "LLMEnhancer":
        return cls(
            api_key=config.api_key or None,
            model=config.model or None,
            base_url=config.base_url or None,
        )

    def is_available(self) -> bool:
        return bool(self.api_key)

    def enhance(
        self,
        profile: CandidateProfile,
        jd: JobDescription,
        ranked_resume: RankedResume,
        memory_context: str = "",
        language: str = "en",
    ) -> RankedResume:
        if not self.is_available():
            return ranked_resume

        prompt = self._build_prompt(profile, jd, ranked_resume, memory_context, language)
        try:
            response_text = self._request_completion(prompt)
            payload = self._extract_json(response_text)
            return self._merge_response(ranked_resume, payload)
        except Exception:
            return ranked_resume

    def localize_resume(
        self,
        profile: CandidateProfile,
        ranked_resume: RankedResume,
        language: str,
    ) -> tuple[CandidateProfile, RankedResume]:
        if not self.is_available():
            return profile, ranked_resume

        payload = {
            "basic_info": {
                "title": profile.basic_info.title,
                "location": profile.basic_info.location,
            },
            "ranked_resume": {
                "target_title": ranked_resume.target_title,
                "summary": ranked_resume.summary,
                "highlighted_skills": ranked_resume.highlighted_skills,
                "work_experiences": [
                    {
                        "company": item.company,
                        "title": item.title,
                        "location": item.location,
                        "bullets": item.bullets,
                    }
                    for item in ranked_resume.work_experiences
                ],
                "project_experiences": [
                    {
                        "name": item.name,
                        "role": item.role,
                        "bullets": item.bullets,
                    }
                    for item in ranked_resume.project_experiences
                ],
            },
            "education": [
                {
                    "school": item.school,
                    "degree": item.degree,
                    "major": item.major,
                }
                for item in profile.education
            ],
            "certificates": [
                {
                    "name": item.name,
                    "issuer": item.issuer,
                }
                for item in profile.certificates
            ],
        }

        prompt = "\n".join(
            [
                "Translate and localize all user-visible resume content while preserving facts and structure.",
                f"Target language: {'Chinese' if language == 'zh' else 'English'}.",
                "Keep proper nouns as appropriate. Translate role names, summaries, bullets, skills, degree labels, and other display text.",
                "Return JSON only.",
                json.dumps(
                    {
                        "output_schema": {
                            "basic_info": {"title": "string", "location": "string"},
                            "ranked_resume": {
                                "target_title": "string",
                                "summary": "string",
                                "highlighted_skills": ["string"],
                                "work_experiences": [
                                    {
                                        "company": "string",
                                        "title": "string",
                                        "location": "string",
                                        "bullets": ["string"],
                                    }
                                ],
                                "project_experiences": [
                                    {
                                        "name": "string",
                                        "role": "string",
                                        "bullets": ["string"],
                                    }
                                ],
                            },
                            "education": [{"school": "string", "degree": "string", "major": "string"}],
                            "certificates": [{"name": "string", "issuer": "string"}],
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                json.dumps(payload, ensure_ascii=False, indent=2),
            ]
        )

        try:
            response_text = self._request_completion(prompt)
            localized = self._extract_json(response_text)
            return self._merge_localized(profile, ranked_resume, localized)
        except Exception:
            return profile, ranked_resume

    def _build_prompt(
        self,
        profile: CandidateProfile,
        jd: JobDescription,
        ranked_resume: RankedResume,
        memory_context: str,
        language: str,
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
            "target_language": "Chinese" if language == "zh" else "English",
            "rules": [
                "Preserve factual accuracy. Do not invent employers, achievements, technologies, or responsibilities.",
                "You may polish, reframe, and elevate wording so the resume reads stronger and more competitive for the JD.",
                "You may reorganize emphasis, highlight transferable strengths, and rewrite bullets to sound more professional, but keep the underlying facts consistent with the source profile and draft.",
                "If the source content implies impact but does not state it cleanly, make the impact more explicit through wording rather than fabrication.",
                "Prefer recruiter-friendly phrasing, stronger verbs, tighter structure, and clearer business value.",
                "Emphasize the experience, skills, and measurable outcomes most relevant to the JD.",
                "Keep the summary concise and role-targeted.",
                "Make bullets action-oriented and outcome-aware.",
                "When helpful, align terminology with the JD so long as the mapped terminology is reasonably supported by the candidate's real experience.",
                "Do not overclaim seniority, ownership, metrics, domain expertise, or technical depth beyond what the source materials can support.",
                "Respect historical feedback preferences when possible.",
                f"Write the resume in {'Chinese' if language == 'zh' else 'English'}.",
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
                "You are a senior resume strategist and resume copywriter. Rewrite the draft into strong, job-targeted resume content.",
                "Your job is not just to restate the draft, but to package the candidate's real experience in the strongest credible way for the target role.",
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
                    "content": (
                        "You rewrite and localize resume drafts into concise, job-targeted content. "
                        "You may polish and strategically package the candidate's真实经历 in a stronger professional tone, "
                        "but you must not fabricate facts. Always return valid JSON."
                    ),
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

    def _merge_localized(
        self,
        profile: CandidateProfile,
        ranked_resume: RankedResume,
        payload: dict,
    ) -> tuple[CandidateProfile, RankedResume]:
        localized_basic = payload.get("basic_info", {})
        localized_ranked = payload.get("ranked_resume", {})

        localized_profile = replace(
            profile,
            basic_info=replace(
                profile.basic_info,
                title=localized_basic.get("title", profile.basic_info.title),
                location=localized_basic.get("location", profile.basic_info.location),
            ),
            education=self._merge_education(profile.education, payload.get("education", [])),
            certificates=self._merge_certificates(profile.certificates, payload.get("certificates", [])),
        )

        localized_resume = RankedResume(
            target_title=localized_ranked.get("target_title", ranked_resume.target_title),
            summary=localized_ranked.get("summary", ranked_resume.summary),
            highlighted_skills=localized_ranked.get("highlighted_skills", ranked_resume.highlighted_skills),
            work_experiences=self._merge_localized_work(
                ranked_resume.work_experiences,
                localized_ranked.get("work_experiences", []),
            ),
            project_experiences=self._merge_localized_projects(
                ranked_resume.project_experiences,
                localized_ranked.get("project_experiences", []),
            ),
        )
        return localized_profile, localized_resume

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

    def _merge_localized_work(self, source: list[WorkExperience], updates: list[dict]) -> list[WorkExperience]:
        result: list[WorkExperience] = []
        for index, item in enumerate(source):
            update = updates[index] if index < len(updates) else {}
            result.append(
                replace(
                    item,
                    company=update.get("company", item.company),
                    title=update.get("title", item.title),
                    location=update.get("location", item.location),
                    bullets=update.get("bullets", item.bullets),
                )
            )
        return result

    def _merge_localized_projects(self, source: list[ProjectExperience], updates: list[dict]) -> list[ProjectExperience]:
        result: list[ProjectExperience] = []
        for index, item in enumerate(source):
            update = updates[index] if index < len(updates) else {}
            result.append(
                replace(
                    item,
                    name=update.get("name", item.name),
                    role=update.get("role", item.role),
                    bullets=update.get("bullets", item.bullets),
                )
            )
        return result

    def _merge_education(self, source: list[Education], updates: list[dict]) -> list[Education]:
        result: list[Education] = []
        for index, item in enumerate(source):
            update = updates[index] if index < len(updates) else {}
            result.append(
                replace(
                    item,
                    school=update.get("school", item.school),
                    degree=update.get("degree", item.degree),
                    major=update.get("major", item.major),
                )
            )
        return result

    def _merge_certificates(self, source: list[Certificate], updates: list[dict]) -> list[Certificate]:
        result: list[Certificate] = []
        for index, item in enumerate(source):
            update = updates[index] if index < len(updates) else {}
            result.append(
                replace(
                    item,
                    name=update.get("name", item.name),
                    issuer=update.get("issuer", item.issuer),
                )
            )
        return result
