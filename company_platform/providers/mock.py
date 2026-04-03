from __future__ import annotations

from .base import BaseProvider


class MockProvider(BaseProvider):
    name = "mock"

    def generate(
        self,
        user_prompt: str,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        hints = []
        prompt = (system_prompt or "") + "\n" + user_prompt
        if "风险" in prompt or "risk" in prompt.lower():
            hints.append("主要风险是范围膨胀、接口边界不清和跨部门依赖延迟。")
        if "行动" in prompt or "action" in prompt.lower():
            hints.append("建议先锁定 owner、里程碑和验收口径，再开始并行推进。")
        if "学习" in prompt or "exchange" in prompt.lower():
            hints.append("双方同步最佳实践后，应沉淀统一模板、监控项和交接清单。")
        if "项目" in prompt or "project" in prompt.lower():
            hints.append("方案应先做 MVP，优先打通核心链路，再逐步扩展能力。")
        if not hints:
            hints.append("从现有 skill 看，先明确背景、目标和职责边界，会比直接开做更稳。")
        return " ".join(hints)
