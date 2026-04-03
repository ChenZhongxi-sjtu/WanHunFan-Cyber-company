from __future__ import annotations

from ..models import ColleagueSkill, DepartmentExchangeResult
from ..providers.base import BaseProvider
from ..repository import CompanyRepository


class DepartmentExchangeService:
    def __init__(self, repository: CompanyRepository, provider: BaseProvider):
        self.repository = repository
        self.provider = provider

    def run(
        self,
        department_a: str,
        department_b: str,
        colleagues: list[ColleagueSkill],
        *,
        topic: str | None = None,
    ) -> DepartmentExchangeResult:
        members_a = [item for item in colleagues if item.department == department_a]
        members_b = [item for item in colleagues if item.department == department_b]
        topic_value = topic or f"{department_a} 与 {department_b} 的协作优化"
        prompt = self._build_prompt(department_a, department_b, members_a, members_b, topic_value)
        memo = self.provider.generate(
            prompt,
            system_prompt=(
                "你是公司的组织发展负责人。请让两个部门相互学习，"
                "输出共识、可迁移的做法和下一步更新建议。"
            ),
        )

        updated_slugs: list[str] = []
        title = f"部门交流：{department_a} x {department_b}"
        for member in members_a + members_b:
            self.repository.append_learning_note(member.slug, title, memo)
            updated_slugs.append(member.slug)

        artifact = self.repository.save_run_artifact(
            "department_exchange",
            title=f"{department_a}-{department_b}",
            content=self._render_markdown(department_a, department_b, topic_value, memo, updated_slugs),
        )
        return DepartmentExchangeResult(
            department_a=department_a,
            department_b=department_b,
            topic=topic_value,
            memo=memo.strip(),
            updated_slugs=updated_slugs,
            artifact_path=artifact,
        )

    def _build_prompt(
        self,
        department_a: str,
        department_b: str,
        members_a: list[ColleagueSkill],
        members_b: list[ColleagueSkill],
        topic: str,
    ) -> str:
        context_a = "\n\n".join(member.short_summary(700) for member in members_a) or "暂无成员"
        context_b = "\n\n".join(member.short_summary(700) for member in members_b) or "暂无成员"
        return (
            f"交流主题：{topic}\n\n"
            f"部门 A：{department_a}\n{context_a}\n\n"
            f"部门 B：{department_b}\n{context_b}\n\n"
            "请输出：1. A 从 B 学到什么 2. B 从 A 学到什么 3. 双方统一规则 4. 需要写回 skill 的学习笔记。"
        )

    def _render_markdown(
        self,
        department_a: str,
        department_b: str,
        topic: str,
        memo: str,
        updated_slugs: list[str],
    ) -> str:
        updated = "\n".join(f"- {slug}" for slug in updated_slugs)
        return (
            f"# 部门交流\n\n"
            f"## 参与部门\n- {department_a}\n- {department_b}\n\n"
            f"## 交流主题\n{topic}\n\n"
            f"## 交流纪要\n{memo.strip()}\n\n"
            f"## 已更新同事\n{updated}\n"
        )
