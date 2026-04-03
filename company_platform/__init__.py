"""Company-scale orchestration platform for colleague skills."""

from .config import load_settings
from .repository import CompanyRepository

__all__ = ["CompanyRepository", "load_settings"]
