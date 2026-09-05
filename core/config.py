# -*- coding: utf-8 -*-
"""
RoamAI Configuration & Settings Module.
Implements an encapsulated, thread-safe Singleton Settings class with 
read-only property accessors, defensive validation, and environment loading.
"""
from __future__ import annotations
import os
import threading
from pathlib import Path
from typing import Tuple, Optional


class Settings:
    """
    Singleton application configuration object.
    Provides encapsulated, validated, read-only properties for application-wide settings.
    """
    _instance: Optional[Settings] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> Settings:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Settings, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance

    @classmethod
    def get_instance(cls) -> Settings:
        """Accessor for the global Settings singleton."""
        if cls._instance is None:
            return cls()
        return cls._instance

    def _initialize(self) -> None:
        """Protected initializer for configuration properties."""
        self._base_dir: Path = Path(__file__).resolve().parent.parent
        self._static_dir: Path = self._base_dir / "static"
        self._templates_dir: Path = self._base_dir / "templates"

        # Application Metadata
        self._app_title: str = "RoamAI • AI Student Travel Planner"
        self._app_description: str = "Next-Gen 3D Modern Student Travel Planner powered by Groq AI"
        self._app_version: str = "2.4.0"

        # Security & Network Defaults
        self._rate_limit_requests: int = 20
        self._rate_limit_window_seconds: int = 60
        self._default_host: str = "0.0.0.0"
        self._default_port: int = 8000

        # AI Models (Immutable tuple to prevent runtime mutation)
        self._groq_models: Tuple[str, ...] = (
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "llama3-70b-8192",
            "gemma2-9b-it"
        )

        # Load environment variables from .env if present
        self._load_dotenv()

        # Sensitive credentials
        self._groq_api_key: str = os.environ.get("GROQ_API_KEY", "").strip()

    def _load_dotenv(self) -> None:
        """Lightweight, safe .env loader avoiding external dependencies."""
        env_path = self._base_dir / ".env"
        if not env_path.is_file():
            return

        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    # Do not overwrite variables already explicitly passed in OS environment
                    if key not in os.environ:
                        os.environ[key] = val
        except Exception:
            # Defensive suppression of file read errors
            pass

    # Read-only Properties for Encapsulation
    @property
    def base_dir(self) -> Path:
        return self._base_dir

    @property
    def static_dir(self) -> Path:
        return self._static_dir

    @property
    def templates_dir(self) -> Path:
        return self._templates_dir

    @property
    def app_title(self) -> str:
        return self._app_title

    @property
    def app_description(self) -> str:
        return self._app_description

    @property
    def app_version(self) -> str:
        return self._app_version

    @property
    def groq_api_key(self) -> str:
        """Returns the active Groq API Key."""
        # Always check environment to allow runtime injection during testing
        return os.environ.get("GROQ_API_KEY", self._groq_api_key).strip()

    @property
    def masked_groq_key(self) -> str:
        """Returns safe masked representation of API key for telemetry/logging."""
        key = self.groq_api_key
        if not key:
            return "NOT_CONFIGURED"
        if len(key) <= 8:
            return "***"
        return f"{key[:4]}...{key[-4:]}"

    @property
    def is_groq_configured(self) -> bool:
        """Returns True if a non-empty Groq API key is configured."""
        return bool(self.groq_api_key)

    @property
    def groq_models(self) -> Tuple[str, ...]:
        return self._groq_models

    @property
    def rate_limit_requests(self) -> int:
        return self._rate_limit_requests

    @property
    def rate_limit_window_seconds(self) -> int:
        return self._rate_limit_window_seconds

    @property
    def default_host(self) -> str:
        return self._default_host

    @property
    def default_port(self) -> int:
        return self._default_port


# Singleton Instance
settings = Settings.get_instance()

# Backward-compatible convenience exports
APP_TITLE = settings.app_title
APP_DESCRIPTION = settings.app_description
APP_VERSION = settings.app_version
GROQ_MODELS = list(settings.groq_models)
BASE_DIR = settings.base_dir
STATIC_DIR = settings.static_dir
TEMPLATES_DIR = settings.templates_dir
RATE_LIMIT_REQUESTS = settings.rate_limit_requests
RATE_LIMIT_WINDOW_SECONDS = settings.rate_limit_window_seconds
DEFAULT_HOST = settings.default_host
DEFAULT_PORT = settings.default_port
