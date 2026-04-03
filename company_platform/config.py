from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from .models import CompanySettings, DepartmentDefinition, ProviderConfig


PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    "mock": {
        "model": "mock-sim",
        "base_url": "",
    },
    "openai": {
        "model": "gpt-4.1-mini",
        "base_url": "https://api.openai.com/v1",
    },
    "gemini": {
        "model": "gemini-3.1-pro-preview",
        "base_url": "https://generativelanguage.googleapis.com",
    },
    "qwen": {
        "model": "qwen-plus",
        "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    },
    "claude": {
        "model": "claude-sonnet-4-20250514",
        "base_url": "https://api.anthropic.com",
    },
}


DEFAULT_COMPANY_CONFIG: dict[str, Any] = {
    "company_name": "Skill Company",
    "llm": {
        "default_provider": "${COMPANY_LLM_PROVIDER:-mock}",
        "routing_mode": "${COMPANY_LLM_ROUTING_MODE:-hybrid}",
        "providers": {
            "mock": {"model": "mock-sim"},
            "openai": {
                "api_key": "${OPENAI_API_KEY:-}",
                "model": "${OPENAI_MODEL:-gpt-4.1-mini}",
                "base_url": "${OPENAI_BASE_URL:-https://api.openai.com/v1}",
            },
            "gemini": {
                "api_key": "${GEMINI_API_KEY:-}",
                "model": "${GEMINI_MODEL:-gemini-3.1-pro-preview}",
                "base_url": "${GEMINI_BASE_URL:-https://generativelanguage.googleapis.com}",
            },
            "qwen": {
                "api_key": "${QWEN_API_KEY:-}",
                "model": "${QWEN_MODEL:-qwen-plus}",
                "base_url": "${QWEN_BASE_URL:-https://dashscope-intl.aliyuncs.com/compatible-mode/v1}",
            },
            "claude": {
                "api_key": "${ANTHROPIC_API_KEY:-}",
                "model": "${CLAUDE_MODEL:-claude-sonnet-4-20250514}",
                "base_url": "${ANTHROPIC_BASE_URL:-https://api.anthropic.com}",
            },
        },
    },
    "departments": {
        "product": {
            "name": "产品部",
            "description": "负责需求定义、用户洞察和项目推进。",
            "keywords": ["产品", "prd", "roadmap", "需求", "用户研究", "增长"],
        },
        "backend": {
            "name": "后端部",
            "description": "负责服务端架构、接口、数据和稳定性。",
            "keywords": ["后端", "backend", "java", "python", "service", "api", "数据库"],
        },
        "frontend": {
            "name": "前端部",
            "description": "负责 Web、客户端交互与体验实现。",
            "keywords": ["前端", "frontend", "react", "vue", "ui", "交互", "页面"],
        },
        "qa": {
            "name": "测试部",
            "description": "负责测试策略、质量门禁和回归体系。",
            "keywords": ["测试", "qa", "质量", "回归", "用例", "自动化测试"],
        },
        "ops": {
            "name": "运维部",
            "description": "负责部署、监控、容量和应急响应。",
            "keywords": ["运维", "ops", "sre", "k8s", "监控", "部署", "告警"],
        },
        "data": {
            "name": "数据部",
            "description": "负责数据分析、算法、指标和建模。",
            "keywords": ["数据", "算法", "推荐", "分析", "模型", "etl", "指标"],
        },
        "security": {
            "name": "安全部",
            "description": "负责风控、权限、安全合规。",
            "keywords": ["安全", "风控", "权限", "合规", "审计", "加密"],
        },
        "general": {
            "name": "综合办公室",
            "description": "无法可靠归类时的默认部门。",
            "keywords": ["通用", "协调", "杂项"],
            "default": True,
        },
    },
}


def load_settings(root_dir: Path | None = None) -> CompanySettings:
    root = (root_dir or Path(__file__).resolve().parents[1]).resolve()
    company_data_dir = root / "company_data"
    company_config_path = company_data_dir / "company.yaml"
    provider_profile_path = company_data_dir / "provider.yaml"
    assignments_path = company_data_dir / "assignments.yaml"
    run_output_dir = company_data_dir / "runs"
    colleagues_dir = root / "colleagues"

    raw = DEFAULT_COMPANY_CONFIG
    if company_config_path.exists():
        with company_config_path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
        raw = _deep_merge(DEFAULT_COMPANY_CONFIG, loaded)

    expanded = _expand_env(raw)
    llm = expanded.get("llm", {})
    provider_profile = _load_yaml(provider_profile_path)
    selected_provider = str(provider_profile.get("provider", llm.get("default_provider", "mock"))).lower()
    providers: dict[str, ProviderConfig] = {}
    for provider_name, payload in llm.get("providers", {}).items():
        preset = PROVIDER_PRESETS.get(provider_name, {})
        model = payload.get("model") or preset.get("model") or None
        base_url = payload.get("base_url") or preset.get("base_url") or None
        api_key = payload.get("api_key") or None
        if provider_name == selected_provider and provider_profile.get("api_key"):
            api_key = provider_profile.get("api_key")
        providers[provider_name] = ProviderConfig(
            name=provider_name,
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout_seconds=int(payload.get("timeout_seconds", 60)),
        )

    departments: dict[str, DepartmentDefinition] = {}
    for key, payload in expanded.get("departments", {}).items():
        departments[key] = DepartmentDefinition(
            key=key,
            name=payload.get("name", key),
            description=payload.get("description", ""),
            keywords=list(payload.get("keywords", [])),
            is_default=bool(payload.get("default", False)),
        )

    return CompanySettings(
        root_dir=root,
        colleagues_dir=colleagues_dir,
        company_data_dir=company_data_dir,
        company_config_path=company_config_path,
        provider_profile_path=provider_profile_path,
        assignments_path=assignments_path,
        default_provider=selected_provider,
        routing_mode=llm.get("routing_mode", "hybrid"),
        departments=departments,
        providers=providers,
        run_output_dir=run_output_dir,
    )


def _expand_env(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _expand_env(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_expand_env(item) for item in value]
    if not isinstance(value, str):
        return value
    if not value.startswith("${") or not value.endswith("}"):
        return value

    body = value[2:-1]
    if ":-" in body:
        env_key, fallback = body.split(":-", 1)
        return os.getenv(env_key, fallback)
    return os.getenv(body, "")


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merged[key] = _deep_merge(base[key], value)
        else:
            merged[key] = value
    return merged


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}
