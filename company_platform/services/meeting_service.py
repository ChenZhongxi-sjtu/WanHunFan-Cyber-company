from __future__ import annotations

from ..models import ColleagueSkill, MeetingResult, MeetingTurn
from ..providers.base import BaseProvider
from ..repository import CompanyRepository
from ..utils.text import truncate
from .routing_service import RoutingService


class MeetingService:
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
        question: str,
        colleagues: list[ColleagueSkill],
        *,
        participant_limit: int = 4,
        department_filters: set[str] | None = None,
    ) -> MeetingResult:
        participants = self.routing_service.select_colleagues(
            question,
            colleagues,
            limit=participant_limit,
            allowed_departments=department_filters,
        )
        colleague_map = {colleague.slug: colleague for colleague in colleagues}
        turns: list[MeetingTurn] = []
        for participant in participants:
            colleague = colleague_map[participant.slug]
            system_prompt = (
                "你正在参加公司大会。你必须扮演指定同事，"
                "按照他的 work 规范和 persona 口吻回答老板。"
                "回答要求：结论先行，最多 180 字，必须给出一个建议或风险提醒。\n\n"
                f"{colleague.full_context(2600)}"
            )
            user_prompt = f"老板的问题：{question}"
            content = self.provider.generate(user_prompt, system_prompt=system_prompt)
            turns.append(
                MeetingTurn(
                    speaker_slug=participant.slug,
                    speaker_name=participant.name,
                    department=participant.department,
                    content=truncate(content.strip(), 280),
                )
            )

        summary_prompt = self._build_summary_prompt(question, turns)
        summary = self.provider.generate(
            summary_prompt,
            system_prompt="你是 CEO 助理，负责把公司大会发言整理成明确结论。",
        )

        artifact = self.repository.save_run_artifact(
            "all_hands",
            title=question[:32],
            content=self._render_markdown(question, participants, turns, summary),
        )
        return MeetingResult(
            question=question,
            participants=participants,
            turns=turns,
            summary=summary.strip(),
            artifact_path=artifact,
        )

    def _build_summary_prompt(self, question: str, turns: list[MeetingTurn]) -> str:
        transcript = "\n".join(
            f"- {turn.speaker_name}({turn.department}): {turn.content}"
            for turn in turns
        )
        return (
            f"老板的问题：{question}\n\n"
            f"发言记录：\n{transcript}\n\n"
            "请整理成三部分：1. 集体结论 2. 主要风险 3. 下一步 action items。"
        )

    def _render_markdown(self, question: str, participants, turns, summary: str) -> str:
        participant_lines = "\n".join(
            f"- {item.name} | {item.department} | {item.reason}" for item in participants
        )
        turn_lines = "\n".join(
            f"### {turn.speaker_name}（{turn.department}）\n{turn.content}" for turn in turns
        )
        return (
            f"# 全体公司大会\n\n"
            f"## 老板问题\n{question}\n\n"
            f"## 自动点名结果\n{participant_lines}\n\n"
            f"## 发言记录\n{turn_lines}\n\n"
            f"## 会议总结\n{summary.strip()}\n"
        )
