from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from .config import load_settings
from .models import ColleagueSkill, CompanySettings


class CompanyRepository:
    def __init__(self, settings: CompanySettings | None = None):
        self.settings = settings or load_settings()
        self.settings.company_data_dir.mkdir(parents=True, exist_ok=True)
        self.settings.run_output_dir.mkdir(parents=True, exist_ok=True)
        self.settings.colleagues_dir.mkdir(parents=True, exist_ok=True)

    def list_colleagues(self) -> list[ColleagueSkill]:
        colleagues: list[ColleagueSkill] = []
        assignments = self.load_assignments()
        for skill_dir in sorted(self.settings.colleagues_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            meta_path = skill_dir / "meta.json"
            work_path = skill_dir / "work.md"
            persona_path = skill_dir / "persona.md"
            if not (meta_path.exists() and work_path.exists() and persona_path.exists()):
                continue

            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            learning_path = skill_dir / "company_learning.md"
            learning_notes = learning_path.read_text(encoding="utf-8") if learning_path.exists() else ""
            assignment = assignments.get(skill_dir.name, {})
            colleague = ColleagueSkill(
                slug=skill_dir.name,
                name=meta.get("name", skill_dir.name),
                skill_dir=skill_dir,
                meta=meta,
                work=work_path.read_text(encoding="utf-8"),
                persona=persona_path.read_text(encoding="utf-8"),
                learning_notes=learning_notes,
                department=assignment.get("primary_department"),
                department_source="manual" if assignment.get("primary_department") else "unassigned",
                department_reason=assignment.get("reason", ""),
            )
            colleagues.append(colleague)
        return colleagues

    def load_assignments(self) -> dict[str, Any]:
        if not self.settings.assignments_path.exists():
            return {}
        with self.settings.assignments_path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        return payload.get("assignments", {})

    def load_provider_profile(self) -> dict[str, Any]:
        if not self.settings.provider_profile_path.exists():
            return {}
        with self.settings.provider_profile_path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def save_provider_profile(self, provider: str, api_key: str) -> Path:
        payload = {
            "provider": provider,
            "api_key": api_key,
            "updated_at": _now(),
        }
        self.settings.provider_profile_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings.provider_profile_path.write_text(
            yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return self.settings.provider_profile_path

    def replace_company_config(self, source_path: Path) -> Path:
        self.settings.company_config_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, self.settings.company_config_path)
        return self.settings.company_config_path

    def save_assignment(self, slug: str, department: str, reason: str = "") -> None:
        payload = {"assignments": self.load_assignments()}
        payload["assignments"][slug] = {
            "primary_department": department,
            "reason": reason,
            "updated_at": _now(),
        }
        self.settings.assignments_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings.assignments_path.write_text(
            yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    def append_learning_note(self, slug: str, title: str, body: str) -> Path:
        skill_dir = self.settings.colleagues_dir / slug
        skill_dir.mkdir(parents=True, exist_ok=True)
        learning_path = skill_dir / "company_learning.md"
        chunk = (
            f"\n\n## {title}\n"
            f"- 更新时间: {_now()}\n\n"
            f"{body.strip()}\n"
        )
        if learning_path.exists():
            current = learning_path.read_text(encoding="utf-8")
        else:
            current = "# Company Learning Notes\n"
        learning_path.write_text(current.rstrip() + chunk, encoding="utf-8")
        return learning_path

    def save_run_artifact(self, category: str, title: str, content: str) -> Path:
        category_dir = self.settings.run_output_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        slug = _slugify(title)
        artifact_path = category_dir / f"{timestamp}-{slug}.md"
        artifact_path.write_text(content, encoding="utf-8")
        return artifact_path

    def seed_demo_company(self, force: bool = False) -> list[Path]:
        source_root = self.settings.root_dir / "examples" / "demo_company"
        if not source_root.exists():
            raise FileNotFoundError(f"Missing demo company at {source_root}")

        created: list[Path] = []
        for source_skill_dir in sorted((source_root / "colleagues").iterdir()):
            target_dir = self.settings.colleagues_dir / source_skill_dir.name
            if target_dir.exists():
                if not force:
                    continue
                shutil.rmtree(target_dir)
            shutil.copytree(source_skill_dir, target_dir)
            created.append(target_dir)

        for source_file, target_file in (
            (source_root / "company.yaml", self.settings.company_config_path),
            (source_root / "assignments.yaml", self.settings.assignments_path),
        ):
            if source_file.exists():
                if target_file.exists() and not force:
                    continue
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, target_file)
                created.append(target_file)

        return created


def _slugify(value: str) -> str:
    output = []
    for char in value.lower():
        if char.isalnum():
            output.append(char)
        elif char in {" ", "_", "-"}:
            output.append("-")
    slug = "".join(output).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "artifact"


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
