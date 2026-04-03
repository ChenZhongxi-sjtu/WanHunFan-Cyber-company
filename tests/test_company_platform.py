from __future__ import annotations

import shutil
from pathlib import Path

from company_platform.providers.base import ProviderNetworkError
from company_platform.services.company_service import CompanyPlatform
from company_platform.services.training_service import TrainingService


REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_ROOT = REPO_ROOT / "examples" / "demo_company"
EMBODIED_ROOT = REPO_ROOT / "company_embodied"


def prepare_root(tmp_path: Path) -> Path:
    (tmp_path / "examples").mkdir(parents=True, exist_ok=True)
    shutil.copytree(DEMO_ROOT, tmp_path / "examples" / "demo_company")
    shutil.copytree(EMBODIED_ROOT, tmp_path / "company_embodied")
    (tmp_path / "colleagues").mkdir()
    (tmp_path / "company_data").mkdir()
    return tmp_path


def test_seed_demo_and_department_assignment(tmp_path: Path):
    root = prepare_root(tmp_path)
    platform = CompanyPlatform(root_dir=root, provider_name="mock")
    created = platform.repository.seed_demo_company()

    assert created

    colleagues = platform.load_company()
    assert len(colleagues) == 6
    departments = {colleague.slug: colleague.department for colleague in colleagues}
    assert departments["li_ming_backend"] == "backend"
    assert departments["chen_xi_frontend"] == "frontend"
    assert departments["wang_yue_product"] == "product"


def test_all_hands_generates_artifact(tmp_path: Path):
    root = prepare_root(tmp_path)
    platform = CompanyPlatform(root_dir=root, provider_name="mock")
    platform.repository.seed_demo_company()

    result = platform.meeting_service.run("我们要做一个新的支付风控改造，谁应该参与？", platform.load_company())

    assert result.participants
    assert result.summary
    assert result.artifact_path is not None
    assert result.artifact_path.exists()


def test_department_exchange_updates_learning_notes(tmp_path: Path):
    root = prepare_root(tmp_path)
    platform = CompanyPlatform(root_dir=root, provider_name="mock")
    platform.repository.seed_demo_company()

    result = platform.exchange_service.run("backend", "frontend", platform.load_company(), topic="接口契约和异常态协作")

    assert result.updated_slugs
    learning_note = root / "colleagues" / "li_ming_backend" / "company_learning.md"
    assert learning_note.exists()
    assert "部门交流" in learning_note.read_text(encoding="utf-8")


def test_project_plan_selects_departments_and_owners(tmp_path: Path):
    root = prepare_root(tmp_path)
    platform = CompanyPlatform(root_dir=root, provider_name="mock")
    platform.repository.seed_demo_company()

    result = platform.project_service.run(
        "统一增长实验平台",
        "建设一个支持埋点治理、实验分流、前后端联调和结果分析的统一平台。",
        platform.load_company(),
    )

    assert "product" in result.departments
    assert "frontend" in result.departments
    assert "backend" in result.departments
    assert result.owners
    assert result.artifact_path is not None
    assert result.artifact_path.exists()


def test_configure_api_and_train_materials(tmp_path: Path):
    root = prepare_root(tmp_path)
    platform = CompanyPlatform(root_dir=root, provider_name="mock")
    profile_path = platform.repository.save_provider_profile("claude", "dummy-key")

    assert profile_path.exists()
    assert "provider: claude" in profile_path.read_text(encoding="utf-8")

    reloaded_for_provider = CompanyPlatform(root_dir=root)
    assert reloaded_for_provider.settings.default_provider == "claude"

    result = platform.training_service.train_directory(root / "company_embodied", force=True, reset_company=True)

    assert len(result["created"]) == 20
    assert (root / "colleagues" / "zhou_yao" / "meta.json").exists()

    reloaded = CompanyPlatform(root_dir=root)
    colleagues = reloaded.load_company()
    assert len(colleagues) == 20
    departments = {colleague.slug: colleague.department for colleague in colleagues}
    assert departments["zhou_yao"] == "perception"
    assert departments["gu_zhun"] == "planning"
    assert departments["pei_chuan"] == "hardware"
    assert departments["jiang_shuo"] == "platform"


def test_train_materials_falls_back_when_provider_network_fails(tmp_path: Path):
    class BrokenGeminiProvider:
        name = "gemini"

        def generate(self, *args, **kwargs):
            raise ProviderNetworkError("Gemini network is unreachable: simulated")

    root = prepare_root(tmp_path)
    platform = CompanyPlatform(root_dir=root, provider_name="mock")
    training_service = TrainingService(platform.repository, BrokenGeminiProvider())

    result = training_service.train_directory(root / "company_embodied", force=True, reset_company=True)

    assert len(result["created"]) == 20
    assert result["warnings"]
    assert "离线蒸馏" in result["warnings"][0]
    assert (root / "colleagues" / "zhou_yao" / "persona.md").exists()
