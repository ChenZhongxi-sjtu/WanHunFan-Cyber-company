from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class DepartmentDefinition:
    key: str
    name: str
    description: str = ""
    keywords: list[str] = field(default_factory=list)
    is_default: bool = False


@dataclass(slots=True)
class ProviderConfig:
    name: str
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    timeout_seconds: int = 60


@dataclass(slots=True)
class CompanySettings:
    root_dir: Path
    colleagues_dir: Path
    company_data_dir: Path
    company_config_path: Path
    provider_profile_path: Path
    assignments_path: Path
    default_provider: str
    routing_mode: str
    departments: dict[str, DepartmentDefinition]
    providers: dict[str, ProviderConfig]
    run_output_dir: Path


@dataclass(slots=True)
class ColleagueSkill:
    slug: str
    name: str
    skill_dir: Path
    meta: dict[str, Any]
    work: str
    persona: str
    learning_notes: str = ""
    department: str | None = None
    department_source: str = "unassigned"
    department_reason: str = ""

    @property
    def profile(self) -> dict[str, Any]:
        return self.meta.get("profile", {})

    @property
    def role(self) -> str:
        return self.profile.get("role", "")

    @property
    def tags(self) -> dict[str, list[str]]:
        return self.meta.get("tags", {})

    @property
    def all_tags(self) -> list[str]:
        return list(self.tags.get("personality", [])) + list(self.tags.get("culture", []))

    def search_blob(self) -> str:
        parts = [
            self.name,
            self.slug,
            self.profile.get("company", ""),
            self.profile.get("level", ""),
            self.profile.get("role", ""),
            self.meta.get("impression", ""),
            " ".join(self.all_tags),
            self.work,
            self.persona,
            self.learning_notes,
        ]
        return "\n".join(part for part in parts if part)

    def short_summary(self, max_chars: int = 900) -> str:
        body = (
            f"姓名: {self.name}\n"
            f"角色: {self.profile.get('company', '')} {self.profile.get('level', '')} {self.role}\n"
            f"部门: {self.department or '未分配'}\n"
            f"印象: {self.meta.get('impression', '')}\n"
            f"标签: {', '.join(self.all_tags)}\n"
            f"Work 摘要:\n{self.work[: max_chars // 2]}\n\n"
            f"Persona 摘要:\n{self.persona[: max_chars // 2]}"
        )
        return body[:max_chars]

    def full_context(self, max_chars: int = 3000) -> str:
        text = (
            f"# {self.name}\n"
            f"部门: {self.department or '未分配'}\n"
            f"角色: {self.profile.get('company', '')} {self.profile.get('level', '')} {self.role}\n\n"
            f"## Work\n{self.work}\n\n"
            f"## Persona\n{self.persona}\n\n"
            f"## Learned Notes\n{self.learning_notes or '暂无'}\n"
        )
        return text[:max_chars]


@dataclass(slots=True)
class RoutingDecision:
    slug: str
    name: str
    department: str
    score: float
    reason: str


@dataclass(slots=True)
class MeetingTurn:
    speaker_slug: str
    speaker_name: str
    department: str
    content: str


@dataclass(slots=True)
class MeetingResult:
    question: str
    participants: list[RoutingDecision]
    turns: list[MeetingTurn]
    summary: str
    artifact_path: Path | None = None


@dataclass(slots=True)
class DepartmentExchangeResult:
    department_a: str
    department_b: str
    topic: str
    memo: str
    updated_slugs: list[str]
    artifact_path: Path | None = None


@dataclass(slots=True)
class ProjectPlanResult:
    project_name: str
    description: str
    departments: list[str]
    owners: dict[str, str]
    plan_markdown: str
    artifact_path: Path | None = None
