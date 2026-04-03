from __future__ import annotations

from collections import defaultdict

from ..models import ColleagueSkill, CompanySettings
from ..utils.text import keyword_score, split_keywords


class DepartmentService:
    def __init__(self, settings: CompanySettings):
        self.settings = settings

    def assign_departments(self, colleagues: list[ColleagueSkill], mode: str = "mixed") -> list[ColleagueSkill]:
        fallback_department = self._default_department()
        for colleague in colleagues:
            if mode in {"manual", "mixed"} and colleague.department:
                colleague.department_source = "manual"
                colleague.department_reason = colleague.department_reason or "来自 assignments.yaml"
                continue

            if mode == "manual":
                colleague.department = fallback_department
                colleague.department_source = "fallback"
                colleague.department_reason = "无手动配置，使用默认部门"
                continue

            auto_department, reason = self.infer_department(colleague)
            colleague.department = auto_department or fallback_department
            colleague.department_source = "auto"
            colleague.department_reason = reason
        return colleagues

    def infer_department(self, colleague: ColleagueSkill) -> tuple[str, str]:
        blob = colleague.search_blob()
        best_department = self._default_department()
        best_score = 0.0
        best_hits: list[str] = []
        for key, department in self.settings.departments.items():
            score, hits = keyword_score(blob, department.keywords)
            if colleague.role:
                extra_score, extra_hits = keyword_score(colleague.role, department.keywords)
                score += extra_score * 2
                hits.extend(extra_hits)
            if score > best_score:
                best_score = score
                best_department = key
                best_hits = hits

        if best_score <= 0:
            return best_department, "未命中明确关键词，落到默认部门"
        unique_hits = list(dict.fromkeys(best_hits))
        hit_summary = ", ".join(unique_hits[:5]) if unique_hits else "角色和文档关键词"
        return best_department, f"命中关键词: {hit_summary}"

    def members_by_department(self, colleagues: list[ColleagueSkill]) -> dict[str, list[ColleagueSkill]]:
        mapping: dict[str, list[ColleagueSkill]] = defaultdict(list)
        for colleague in colleagues:
            mapping[colleague.department or self._default_department()].append(colleague)
        return dict(mapping)

    def department_keywords(self, department: str) -> list[str]:
        payload = self.settings.departments.get(department)
        if not payload:
            return []
        return payload.keywords

    def colleague_keywords(self, colleague: ColleagueSkill) -> list[str]:
        pieces = [
            colleague.name,
            colleague.slug,
            colleague.profile.get("company", ""),
            colleague.profile.get("role", ""),
            colleague.meta.get("impression", ""),
            " ".join(colleague.all_tags),
        ]
        keywords: list[str] = []
        for piece in pieces:
            keywords.extend(split_keywords(piece))
        keywords.extend(self.department_keywords(colleague.department or self._default_department()))
        return list(dict.fromkeys(keywords))

    def _default_department(self) -> str:
        for key, department in self.settings.departments.items():
            if department.is_default:
                return key
        return "general"
