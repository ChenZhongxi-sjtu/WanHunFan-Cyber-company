from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .services.company_service import CompanyPlatform


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Multi-skill company management platform")
    parser.add_argument("--root-dir", type=Path, default=None, help="Project root directory")
    parser.add_argument("--provider", default=None, help="mock/openai/gemini/qwen/claude")

    subparsers = parser.add_subparsers(dest="command", required=True)

    configure_api = subparsers.add_parser("configure-api", help="Save provider + api key into company_data/provider.yaml")
    configure_api.add_argument("--provider", required=True, choices=["mock", "openai", "gemini", "qwen", "claude"])
    configure_api.add_argument("--api-key", default="", help="API key for the selected provider")

    seed_demo = subparsers.add_parser("seed-demo", help="Copy demo company data into runtime directories")
    seed_demo.add_argument("--force", action="store_true", help="Overwrite existing demo data")

    train_materials = subparsers.add_parser("train-materials", help="Distill markdown materials into colleague skills")
    train_materials.add_argument("--materials-dir", type=Path, default=Path("company_embodied"))
    train_materials.add_argument("--force", action="store_true", help="Overwrite existing generated skills")
    train_materials.add_argument("--reset-company", action="store_true", help="Remove existing colleagues before training")

    list_colleagues = subparsers.add_parser("list-colleagues", help="List colleagues with departments")
    list_colleagues.add_argument("--mode", default="mixed", choices=["manual", "auto", "mixed"])

    assign_department = subparsers.add_parser("assign-department", help="Assign a colleague to a department")
    assign_department.add_argument("--slug", required=True)
    assign_department.add_argument("--department", required=True)
    assign_department.add_argument("--reason", default="")

    sync_departments = subparsers.add_parser("sync-departments", help="Preview department routing results")
    sync_departments.add_argument("--mode", default="mixed", choices=["manual", "auto", "mixed"])
    sync_departments.add_argument("--persist-auto", action="store_true", help="Write auto assignments to assignments.yaml")

    all_hands = subparsers.add_parser("all-hands", help="Run the company-wide meeting flow")
    all_hands.add_argument("--question", required=True)
    all_hands.add_argument("--participants", type=int, default=4)
    all_hands.add_argument("--departments", default="", help="Comma-separated department keys")

    exchange = subparsers.add_parser("department-exchange", help="Run a knowledge exchange between departments")
    exchange.add_argument("--department-a", required=True)
    exchange.add_argument("--department-b", required=True)
    exchange.add_argument("--topic", default=None)

    project = subparsers.add_parser("project-plan", help="Generate a project plan and ownership proposal")
    project.add_argument("--name", required=True)
    project.add_argument("--description", required=True)

    serve = subparsers.add_parser("serve-api", help="Serve the FastAPI app")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    platform = CompanyPlatform(root_dir=args.root_dir, provider_name=args.provider)

    if args.command == "configure-api":
        profile_path = platform.repository.save_provider_profile(args.provider, args.api_key)
        print(f"已写入 provider 配置: {profile_path}")
        return

    if args.command == "seed-demo":
        created = platform.repository.seed_demo_company(force=args.force)
        print("已写入以下 demo 文件：")
        for path in created:
            print(f"- {path}")
        return

    if args.command == "train-materials":
        result = platform.training_service.train_directory(
            args.materials_dir if args.materials_dir.is_absolute() else platform.settings.root_dir / args.materials_dir,
            force=args.force,
            reset_company=args.reset_company,
        )
        _print_json(result)
        return

    if args.command == "list-colleagues":
        colleagues = platform.load_company(mode=args.mode)
        for colleague in colleagues:
            print(
                f"{colleague.slug}\t{colleague.name}\t{colleague.department}\t"
                f"{colleague.department_source}\t{colleague.role}"
            )
        return

    if args.command == "assign-department":
        platform.repository.save_assignment(args.slug, args.department, args.reason)
        print(f"已将 {args.slug} 指派到 {args.department}")
        return

    if args.command == "sync-departments":
        colleagues = platform.load_company(mode=args.mode)
        if args.persist_auto:
            for colleague in colleagues:
                if colleague.department_source == "auto":
                    platform.repository.save_assignment(
                        colleague.slug,
                        colleague.department or "general",
                        reason=f"自动分配: {colleague.department_reason}",
                    )
        for colleague in colleagues:
            print(
                f"{colleague.slug}\t{colleague.department}\t"
                f"{colleague.department_source}\t{colleague.department_reason}"
            )
        return

    if args.command == "all-hands":
        colleagues = platform.load_company()
        departments = {
            item.strip() for item in args.departments.split(",") if item.strip()
        } or None
        result = platform.meeting_service.run(
            args.question,
            colleagues,
            participant_limit=args.participants,
            department_filters=departments,
        )
        _print_json(
            {
                "question": result.question,
                "participants": [asdict(participant) for participant in result.participants],
                "turns": [asdict(turn) for turn in result.turns],
                "summary": result.summary,
                "artifact_path": str(result.artifact_path) if result.artifact_path else None,
            }
        )
        return

    if args.command == "department-exchange":
        colleagues = platform.load_company()
        result = platform.exchange_service.run(
            args.department_a,
            args.department_b,
            colleagues,
            topic=args.topic,
        )
        _print_json(
            {
                "department_a": result.department_a,
                "department_b": result.department_b,
                "topic": result.topic,
                "updated_slugs": result.updated_slugs,
                "artifact_path": str(result.artifact_path) if result.artifact_path else None,
            }
        )
        return

    if args.command == "project-plan":
        colleagues = platform.load_company()
        result = platform.project_service.run(args.name, args.description, colleagues)
        _print_json(
            {
                "project_name": result.project_name,
                "departments": result.departments,
                "owners": result.owners,
                "artifact_path": str(result.artifact_path) if result.artifact_path else None,
                "plan_markdown": result.plan_markdown,
            }
        )
        return

    if args.command == "serve-api":
        import uvicorn
        from .api import create_app

        uvicorn.run(create_app(root_dir=args.root_dir, provider_name=args.provider), host=args.host, port=args.port)
        return


def _print_json(payload) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
