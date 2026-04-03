from __future__ import annotations

from collections import defaultdict

from ..models import ColleagueSkill, CompanySettings, RoutingDecision
from ..utils.text import keyword_score
from .department_service import DepartmentService


class RoutingService:
    def __init__(self, settings: CompanySettings, department_service: DepartmentService):
        self.settings = settings
        self.department_service = department_service

    def select_colleagues(
        self,
        query: str,
        colleagues: list[ColleagueSkill],
        *,
        limit: int = 4,
        allowed_departments: set[str] | None = None,
    ) -> list[RoutingDecision]:
        scored: list[RoutingDecision] = []
        for colleague in colleagues:
            department = colleague.department or self.department_service._default_department()
            if allowed_departments and department not in allowed_departments:
                continue

            keywords = self.department_service.colleague_keywords(colleague)
            score, hits = keyword_score(query, keywords)
            score += self._department_signal(query, department)
            if score <= 0:
                score = 0.1 if department in self.default_departments_for(query) else 0.0
            if colleague.department_source == "manual":
                score += 0.05
            elif colleague.department_source == "auto":
                score += 0.01

            reason = (
                f"命中关键词: {', '.join(hits[:4])}"
                if hits
                else f"根据 {department} 部门默认职责补位"
            )
            scored.append(
                RoutingDecision(
                    slug=colleague.slug,
                    name=colleague.name,
                    department=department,
                    score=score,
                    reason=reason,
                )
            )

        scored.sort(key=lambda item: (-item.score, item.department, item.slug))
        preferred_departments = self.select_departments(query, limit=max(limit, 4))
        if allowed_departments:
            preferred_departments = [item for item in preferred_departments if item in allowed_departments]

        diverse = self._fallback_diverse_selection(scored, preferred_departments, limit)
        if diverse:
            return diverse

        return scored[:limit]

    def select_departments(self, query: str, limit: int = 4) -> list[str]:
        scored: list[tuple[str, float]] = []
        for key, department in self.settings.departments.items():
            if department.is_default:
                continue
            score, _ = keyword_score(query, department.keywords)
            scored.append((key, score))
        scored.sort(key=lambda item: (-item[1], item[0]))
        winning = [key for key, score in scored if score > 0][:limit]
        defaults = self.default_departments_for(query)
        merged = list(dict.fromkeys(winning + defaults))
        if merged:
            return merged[:limit]
        return defaults[:limit]

    def top_owner_per_department(
        self,
        query: str,
        colleagues: list[ColleagueSkill],
        departments: list[str],
    ) -> dict[str, RoutingDecision]:
        owners: dict[str, RoutingDecision] = {}
        scored = self.select_colleagues(query, colleagues, limit=max(len(colleagues), 1))
        for decision in scored:
            if decision.department in departments and decision.department not in owners:
                owners[decision.department] = decision

        if len(owners) < len(departments):
            by_department: dict[str, list[RoutingDecision]] = defaultdict(list)
            for decision in scored:
                by_department[decision.department].append(decision)
            for department in departments:
                if department in owners:
                    continue
                fallback = by_department.get(department)
                if fallback:
                    owners[department] = fallback[0]
        return owners

    def default_departments_for(self, query: str) -> list[str]:
        lowered = query.lower()
        embodied_defaults = ["perception", "planning", "hardware", "platform"]
        if all(department in self.settings.departments for department in embodied_defaults):
            return embodied_defaults

        defaults = ["product", "backend", "frontend", "qa"]
        if any(keyword in lowered for keyword in ("部署", "监控", "稳定性", "告警", "sre", "ops")):
            defaults.append("ops")
        if any(keyword in lowered for keyword in ("数据", "算法", "模型", "推荐", "指标")):
            defaults.append("data")
        if any(keyword in lowered for keyword in ("安全", "权限", "风控", "审计")):
            defaults.append("security")
        ordered = [department for department in defaults if department in self.settings.departments]
        return list(dict.fromkeys(ordered))

    def _department_signal(self, query: str, department: str) -> float:
        keywords = self.department_service.department_keywords(department)
        score, _ = keyword_score(query, keywords)
        return score * 1.5

    def _fallback_diverse_selection(
        self,
        scored: list[RoutingDecision],
        departments: list[str],
        limit: int,
    ) -> list[RoutingDecision]:
        by_department: dict[str, list[RoutingDecision]] = defaultdict(list)
        for item in scored:
            by_department[item.department].append(item)

        chosen: list[RoutingDecision] = []
        for department in departments:
            if department in by_department and by_department[department]:
                chosen.append(by_department[department][0])
            if len(chosen) >= limit:
                return chosen[:limit]

        for item in scored:
            if item not in chosen:
                chosen.append(item)
            if len(chosen) >= limit:
                break
        return chosen[:limit]
