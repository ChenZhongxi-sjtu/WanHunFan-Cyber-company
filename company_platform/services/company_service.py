from __future__ import annotations

from ..config import load_settings
from ..providers import build_provider
from ..repository import CompanyRepository
from .department_service import DepartmentService
from .exchange_service import DepartmentExchangeService
from .meeting_service import MeetingService
from .project_service import ProjectService
from .routing_service import RoutingService
from .training_service import TrainingService


class CompanyPlatform:
    def __init__(self, root_dir=None, provider_name: str | None = None):
        self.settings = load_settings(root_dir)
        self.repository = CompanyRepository(self.settings)
        self.department_service = DepartmentService(self.settings)
        self.routing_service = RoutingService(self.settings, self.department_service)
        self.provider = build_provider(self.settings, provider_name)
        self.meeting_service = MeetingService(self.repository, self.routing_service, self.provider)
        self.exchange_service = DepartmentExchangeService(self.repository, self.provider)
        self.project_service = ProjectService(self.repository, self.routing_service, self.provider)
        self.training_service = TrainingService(self.repository, self.provider)

    def load_company(self, mode: str | None = None):
        colleagues = self.repository.list_colleagues()
        return self.department_service.assign_departments(colleagues, mode=mode or "mixed")
