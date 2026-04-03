from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .services.company_service import CompanyPlatform


class AssignDepartmentRequest(BaseModel):
    slug: str
    department: str
    reason: str = ""


class AllHandsRequest(BaseModel):
    question: str = Field(..., min_length=1)
    participants: int = 4
    departments: list[str] = Field(default_factory=list)


class DepartmentExchangeRequest(BaseModel):
    department_a: str
    department_b: str
    topic: str | None = None


class ProjectPlanRequest(BaseModel):
    name: str
    description: str


def create_app(root_dir: Path | None = None, provider_name: str | None = None) -> FastAPI:
    platform = CompanyPlatform(root_dir=root_dir, provider_name=provider_name)
    app = FastAPI(title="Company Skill Platform", version="2.0.0")

    @app.get("/health")
    def health():
        return {"status": "ok", "provider": platform.provider.name}

    @app.get("/colleagues")
    def list_colleagues(mode: str = "mixed"):
        colleagues = platform.load_company(mode=mode)
        return [
            {
                "slug": item.slug,
                "name": item.name,
                "department": item.department,
                "department_source": item.department_source,
                "department_reason": item.department_reason,
                "role": item.role,
            }
            for item in colleagues
        ]

    @app.post("/departments/assign")
    def assign_department(request: AssignDepartmentRequest):
        platform.repository.save_assignment(request.slug, request.department, request.reason)
        return {"ok": True}

    @app.post("/meetings/all-hands")
    def all_hands(request: AllHandsRequest):
        colleagues = platform.load_company()
        result = platform.meeting_service.run(
            request.question,
            colleagues,
            participant_limit=request.participants,
            department_filters=set(request.departments) or None,
        )
        return {
            "question": result.question,
            "participants": [asdict(participant) for participant in result.participants],
            "turns": [asdict(turn) for turn in result.turns],
            "summary": result.summary,
            "artifact_path": str(result.artifact_path) if result.artifact_path else None,
        }

    @app.post("/departments/exchange")
    def department_exchange(request: DepartmentExchangeRequest):
        colleagues = platform.load_company()
        result = platform.exchange_service.run(
            request.department_a,
            request.department_b,
            colleagues,
            topic=request.topic,
        )
        return {
            "department_a": result.department_a,
            "department_b": result.department_b,
            "topic": result.topic,
            "updated_slugs": result.updated_slugs,
            "artifact_path": str(result.artifact_path) if result.artifact_path else None,
        }

    @app.post("/projects/plan")
    def project_plan(request: ProjectPlanRequest):
        colleagues = platform.load_company()
        result = platform.project_service.run(request.name, request.description, colleagues)
        return {
            "project_name": result.project_name,
            "description": result.description,
            "departments": result.departments,
            "owners": result.owners,
            "plan_markdown": result.plan_markdown,
            "artifact_path": str(result.artifact_path) if result.artifact_path else None,
        }

    return app
