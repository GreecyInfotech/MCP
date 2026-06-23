"""Shared platform utilities."""

from eai_platform.config import PlatformSettings, get_settings
from eai_platform.logging import get_logger, setup_logging

__all__ = ["PlatformSettings", "get_settings", "get_logger", "setup_logging"]
