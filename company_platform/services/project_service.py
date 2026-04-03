from __future__ import annotations

from ..models import ColleagueSkill, ProjectPlanResult
from ..providers.base import BaseProvider
from ..repository import CompanyRepository
from .routing_service import RoutingService


class ProjectService:
    def __init__(
        self,
        repository: CompanyRepository,
        routing_service: RoutingService,
        provider: BaseProvider,
    ):
        self.repository = repository
        self.routing_service = routing_service
        self.provider = provider

    def run(
        self,
        project_name: str,
        description: str,
        colleagues: list[ColleagueSkill],
    ) -> ProjectPlanResult:
        query = f"{project_name}\n{description}"
        departments = self.routing_service.select_departments(query, limit=5)
        owners = self.routing_service.top_owner_per_department(query, colleagues, departments)
        department_context = self._build_department_context(colleagues, departments, owners)
        prompt = (
            f"项目名称：{project_name}\n"
            f"项目简介：{description}\n\n"
            f"候选部门与 owner：\n{department_context}\n\n"
            "请输出一个完整策划，至少包含：项目目标、范围、里程碑、架构/方案、部门责任划分、风险与应对。"
        )
        plan = self.provider.generate(
            prompt,
            system_prompt="你是 PMO 与技术委员会联合秘书，请输出一份可执行、可分工的项目方案。",
        )
        owner_map = {department: decision.slug for department, decision in owners.items()}
        artifact = self.repository.save_run_artifact(
            "project_plan",
            title=project_name,
            content=self._render_markdown(project_name, description, departments, owners, plan),
        )
        return ProjectPlanResult(
            project_name=project_name,
            description=description,
            departments=departments,
            owners=owner_map,
            plan_markdown=plan.strip(),
            artifact_path=artifact,
        )

    def _build_department_context(self, colleagues, departments, owners) -> str:
        lines: list[str] = []
        grouped = {department: [] for department in departments}
        for colleague in colleagues:
            if colleague.department in grouped:
                grouped[colleague.department].append(colleague)

        for department in departments:
            owner = owners.get(department)
            members = grouped.get(department, [])
            member_names = ", ".join(member.name for member in members[:4]) or "暂无"
            owner_line = f"{owner.name}({owner.slug})" if owner else "待定"
            lines.append(
                f"- {department}: owner={owner_line}; members={member_names}"
            )
        return "\n".join(lines)

    def _render_markdown(self, project_name, description, departments, owners, plan: str) -> str:
        owner_lines = []
        for department in departments:
            owner = owners.get(department)
            if owner:
                owner_lines.append(f"- {department}: {owner.name} ({owner.slug})")
            else:
                owner_lines.append(f"- {department}: 待定")
        return (
            f"# 项目策划\n\n"
            f"## 项目名称\n{project_name}\n\n"
            f"## 项目简介\n{description}\n\n"
            f"## 涉及部门\n" + "\n".join(f"- {item}" for item in departments) + "\n\n"
            f"## 责任 owner\n" + "\n".join(owner_lines) + "\n\n"
            f"## 方案正文\n{plan.strip()}\n"
        )
