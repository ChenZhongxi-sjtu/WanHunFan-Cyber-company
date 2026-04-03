from __future__ import annotations

import json
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

from ..providers.base import ProviderNetworkError
from ..providers.base import BaseProvider
from ..repository import CompanyRepository
from ..utils.json_tools import extract_json


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)
SECTION_RE = re.compile(r"^##\s+(.+?)\n", re.MULTILINE)


@dataclass(slots=True)
class TrainingMaterial:
    path: Path
    meta: dict
    body: str
    sections: dict[str, str]


class TrainingService:
    def __init__(self, repository: CompanyRepository, provider: BaseProvider):
        self.repository = repository
        self.provider = provider

    def train_directory(
        self,
        materials_dir: Path,
        *,
        force: bool = False,
        apply_company_profile: bool = True,
        reset_company: bool = False,
    ) -> dict[str, object]:
        materials_dir = materials_dir.resolve()
        company_profile_path = materials_dir / "company_profile.yaml"
        if apply_company_profile and company_profile_path.exists():
            self.repository.replace_company_config(company_profile_path)

        if reset_company:
            for skill_dir in self.repository.settings.colleagues_dir.iterdir():
                if skill_dir.is_dir():
                    shutil.rmtree(skill_dir)
            self.repository.settings.assignments_path.write_text("assignments: {}\n", encoding="utf-8")

        material_paths = sorted(path for path in materials_dir.glob("*.md") if path.is_file())
        created: list[str] = []
        skipped: list[str] = []
        assignments: dict[str, str] = {}
        warnings: list[str] = []

        for material_path in material_paths:
            material = _parse_material(material_path)
            slug = material.meta["slug"]
            skill_dir = self.repository.settings.colleagues_dir / slug
            if skill_dir.exists() and not force:
                skipped.append(slug)
                continue
            if skill_dir.exists() and force:
                shutil.rmtree(skill_dir)

            try:
                distilled = self._distill_material(material)
            except ProviderNetworkError as exc:
                distilled = self._distill_material_offline(material)
                warning = f"{slug}: Gemini 当前不可达，已回退到离线蒸馏。原因: {exc}"
                warnings.append(warning)
                print(f"[train-materials] {warning}", file=sys.stderr)
            meta = distilled["meta"]
            work = distilled["work"]
            persona = distilled["persona"]
            _create_skill_files(
                self.repository.settings.colleagues_dir,
                slug,
                meta,
                work,
                persona,
            )
            department = material.meta.get("department", "general")
            self.repository.save_assignment(slug, department, reason="来自 company_embodied 训练材料")
            created.append(slug)
            assignments[slug] = department

        artifact = self.repository.save_run_artifact(
            "training",
            title=f"train-{materials_dir.name}",
            content=self._render_summary(materials_dir, created, skipped, assignments, warnings),
        )
        return {
            "materials_dir": str(materials_dir),
            "created": created,
            "skipped": skipped,
            "warnings": warnings,
            "artifact_path": str(artifact),
            "company_config_path": str(self.repository.settings.company_config_path),
        }

    def _distill_material(self, material: TrainingMaterial) -> dict[str, object]:
        base_meta = {
            "name": material.meta["name"],
            "slug": material.meta["slug"],
            "profile": {
                "company": material.meta.get("company", "灵枢具身智能"),
                "level": material.meta.get("level", ""),
                "role": material.meta.get("role", ""),
                "gender": material.meta.get("gender", ""),
                "mbti": material.meta.get("mbti", ""),
            },
            "tags": {
                "personality": list(material.meta.get("personality", [])),
                "culture": list(material.meta.get("culture", [])),
            },
            "impression": material.sections.get("一句话印象", "").strip() or material.meta.get("impression", ""),
            "knowledge_sources": [str(material.path)],
            "corrections_count": 0,
            "source_collection": "company_embodied",
            "source_material": material.path.name,
        }

        deterministic = {
            "meta": base_meta,
            "work": _build_work(material, base_meta["name"]),
            "persona": _build_persona(material, base_meta["name"], base_meta),
        }
        if self.provider.name == "mock":
            return deterministic

        try:
            llm_result = self._distill_with_llm(material, base_meta)
            return {
                "meta": _merge_meta(base_meta, llm_result.get("meta", {})),
                "work": str(llm_result.get("work") or deterministic["work"]),
                "persona": str(llm_result.get("persona") or deterministic["persona"]),
            }
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            return deterministic

    def _distill_material_offline(self, material: TrainingMaterial) -> dict[str, object]:
        base_meta = {
            "name": material.meta["name"],
            "slug": material.meta["slug"],
            "profile": {
                "company": material.meta.get("company", "灵枢具身智能"),
                "level": material.meta.get("level", ""),
                "role": material.meta.get("role", ""),
                "gender": material.meta.get("gender", ""),
                "mbti": material.meta.get("mbti", ""),
            },
            "tags": {
                "personality": list(material.meta.get("personality", [])),
                "culture": list(material.meta.get("culture", [])),
            },
            "impression": material.sections.get("一句话印象", "").strip() or material.meta.get("impression", ""),
            "knowledge_sources": [str(material.path)],
            "corrections_count": 0,
            "source_collection": "company_embodied",
            "source_material": material.path.name,
        }
        return {
            "meta": base_meta,
            "work": _build_work(material, base_meta["name"]),
            "persona": _build_persona(material, base_meta["name"], base_meta),
        }

    def _distill_with_llm(self, material: TrainingMaterial, base_meta: dict) -> dict:
        prompt = (
            "请把下面的同事原材料蒸馏为同事 skill。"
            "必须输出 JSON，结构为 "
            '{"meta": {...}, "work": "...markdown...", "persona": "...markdown..."}。'
            "不要输出 JSON 以外的内容。\n\n"
            f"基础元数据：\n{json.dumps(base_meta, ensure_ascii=False, indent=2)}\n\n"
            f"原始材料：\n{material.path.read_text(encoding='utf-8')}\n"
        )
        system_prompt = (
            "你是一个擅长蒸馏同事工作风格的组织知识工程师。"
            "work 要偏职责、方法、技术规范和项目经验。"
            "persona 要偏表达方式、决策偏好、协作边界和雷区。"
            "保持中文输出，保留 markdown 结构。"
        )
        output = self.provider.generate(prompt, system_prompt=system_prompt, temperature=0.1)
        data = extract_json(output)
        if not isinstance(data, dict):
            raise ValueError("Unexpected non-dict JSON from model")
        return data

    def _render_summary(
        self,
        materials_dir: Path,
        created: list[str],
        skipped: list[str],
        assignments: dict[str, str],
        warnings: list[str],
    ) -> str:
        assignment_lines = "\n".join(f"- {slug}: {department}" for slug, department in assignments.items())
        created_lines = "\n".join(f"- {slug}" for slug in created) or "- 无"
        skipped_lines = "\n".join(f"- {slug}" for slug in skipped) or "- 无"
        warning_lines = "\n".join(f"- {warning}" for warning in warnings) or "- 无"
        return (
            f"# 训练结果\n\n"
            f"## 材料目录\n{materials_dir}\n\n"
            f"## 新建 Skills\n{created_lines}\n\n"
            f"## 跳过\n{skipped_lines}\n\n"
            f"## 警告\n{warning_lines}\n\n"
            f"## 部门归属\n{assignment_lines or '- 无'}\n"
        )


def _parse_material(path: Path) -> TrainingMaterial:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"Material missing frontmatter: {path}")
    frontmatter, body = match.groups()
    meta = yaml.safe_load(frontmatter) or {}
    if "name" not in meta or "slug" not in meta:
        raise ValueError(f"Material missing required fields name/slug: {path}")
    sections = _split_sections(body)
    return TrainingMaterial(path=path, meta=meta, body=body, sections=sections)


def _split_sections(body: str) -> dict[str, str]:
    matches = list(SECTION_RE.finditer(body))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[title] = body[start:end].strip()
    return sections


def _build_work(material: TrainingMaterial, name: str) -> str:
    return (
        f"# {name} — Work Skill\n\n"
        f"## 职责范围\n\n{material.sections.get('职责范围', '暂无')}\n\n"
        f"## 技术与方法\n\n{material.sections.get('技术与方法', '暂无')}\n\n"
        f"## 工作方式\n\n{material.sections.get('工作方式', '暂无')}\n\n"
        f"## 代表项目\n\n{material.sections.get('代表项目', '暂无')}\n\n"
        f"## 协作边界\n\n{material.sections.get('协作边界', '暂无')}\n\n"
        f"## 知识库\n\n{material.sections.get('知识库', '暂无')}\n"
    )


def _build_persona(material: TrainingMaterial, name: str, meta: dict) -> str:
    profile = meta["profile"]
    personality = "、".join(meta["tags"].get("personality", [])) or "暂无"
    culture = "、".join(meta["tags"].get("culture", [])) or "暂无"
    return (
        f"# {name} — Persona\n\n"
        f"## Layer 0：核心性格\n\n{material.sections.get('核心规则', '暂无')}\n\n"
        f"## Layer 1：身份\n\n"
        f"你是{name}，{profile.get('company', '')} {profile.get('level', '')} {profile.get('role', '')}。\n"
        f"你的 MBTI 是 {profile.get('mbti', '未知')}。\n"
        f"你的个性标签：{personality}。\n"
        f"你的团队文化标签：{culture}。\n\n"
        f"## Layer 2：表达风格\n\n{material.sections.get('表达风格', '暂无')}\n\n"
        f"## Layer 3：决策方式\n\n{material.sections.get('决策方式', '暂无')}\n\n"
        f"## Layer 4：协作行为\n\n{material.sections.get('协作行为', '暂无')}\n\n"
        f"## Layer 5：雷区\n\n{material.sections.get('雷区', '暂无')}\n\n"
        f"## 典型话术\n\n{material.sections.get('典型话术', '暂无')}\n"
    )


def _merge_meta(base_meta: dict, llm_meta: dict) -> dict:
    merged = json.loads(json.dumps(base_meta, ensure_ascii=False))
    if not isinstance(llm_meta, dict):
        return merged
    for key, value in llm_meta.items():
        if key in {"profile", "tags"} and isinstance(value, dict):
            merged.setdefault(key, {})
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def _create_skill_files(base_dir: Path, slug: str, meta: dict, work_content: str, persona_content: str) -> Path:
    skill_dir = base_dir / slug
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "versions").mkdir(exist_ok=True)
    (skill_dir / "knowledge" / "docs").mkdir(parents=True, exist_ok=True)
    (skill_dir / "knowledge" / "messages").mkdir(parents=True, exist_ok=True)
    (skill_dir / "knowledge" / "emails").mkdir(parents=True, exist_ok=True)

    identity_parts = [
        meta.get("profile", {}).get("company", ""),
        meta.get("profile", {}).get("level", ""),
        meta.get("profile", {}).get("role", ""),
    ]
    identity = " ".join(part for part in identity_parts if part) or "同事"
    if meta.get("profile", {}).get("mbti"):
        identity += f"，MBTI {meta['profile']['mbti']}"

    skill_md = (
        f"---\nname: colleague_{slug}\ndescription: {meta.get('name', slug)}，{identity}\nuser-invocable: true\n---\n\n"
        f"# {meta.get('name', slug)}\n\n{identity}\n\n---\n\n## PART A：工作能力\n\n{work_content}\n\n---\n\n"
        f"## PART B：人物性格\n\n{persona_content}\n\n---\n\n## 运行规则\n\n"
        f"接收到任何任务或问题时：\n\n1. **先由 PART B 判断**：你会不会接这个任务？用什么态度接？\n"
        f"2. **再由 PART A 执行**：用你的技术能力和工作方法完成任务\n"
        f"3. **输出时保持 PART B 的表达风格**：你说话的方式、用词习惯、句式\n\n"
        f"**PART B 的 Layer 0 规则永远优先，任何情况下不得违背。**\n"
    )

    (skill_dir / "work.md").write_text(work_content, encoding="utf-8")
    (skill_dir / "persona.md").write_text(persona_content, encoding="utf-8")
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    now = datetime.now(timezone.utc).isoformat()
    meta = dict(meta)
    meta["slug"] = slug
    meta.setdefault("created_at", now)
    meta["updated_at"] = now
    meta.setdefault("version", "v1")
    meta.setdefault("corrections_count", 0)
    (skill_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return skill_dir
