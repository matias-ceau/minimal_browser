"""Configuration management for Minimal Browser."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import tomllib
from xdg import BaseDirectory  # type: ignore[import-untyped]
from pydantic import BaseModel, Field, ValidationError


CONFIG_DIR = Path(BaseDirectory.xdg_config_home) / "minimal_browser"
CONFIG_FILE = CONFIG_DIR / "config.toml"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)


class BrowserConfig(BaseModel):
    headless: bool = Field(default=False)
    window_size: tuple[int, int] = Field(default=(1280, 720))
    user_agent: str = Field(default="minimal_browser/1.0")


class AIConfig(BaseModel):
    model: str = Field(default="gpt-5-codex-preview")
    system_prompt: str = Field(default="You are a helpful assistant.")
    enable_gpt5_codex_preview: bool = Field(
        default=True,
        description="Set to true to force all AI clients to use the GPT-5 Codex preview model.",
    )


class StorageConfig(BaseModel):
    conversation_log: Path = Field(default=CONFIG_DIR / "conversations.json")
    vector_db_path: Path = Field(default=CONFIG_DIR / "vector_db")


class SecurityConfig(BaseModel):
    """Security and credential management configuration."""
    use_system_keychain: bool = Field(
        default=True,
        description="Enable system keychain integration (GNOME Keyring/macOS Keychain/Windows Credential Manager) for API keys",
    )
    prefer_env_over_keychain: bool = Field(
        default=True,
        description="If true, environment variables take precedence over keychain storage",
    )


class AppConfig(BaseModel):
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    def merge(self, overrides: Dict[str, Any]) -> "AppConfig":
        """Return a new config with overrides applied."""
        data = self.model_dump()
        for section, values in overrides.items():
            if section in data and isinstance(values, dict):
                data[section].update(values)
            else:
                data[section] = values
        return AppConfig(**data)


DEFAULT_CONFIG = AppConfig()


def _validate_raw_config(raw_config: Dict[str, Any]) -> AppConfig:
    try:
        return AppConfig(**raw_config)
    except ValidationError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"Invalid configuration file: {exc}") from exc


def load_config(path: Optional[Path] = None) -> AppConfig:
    """Load configuration from disk, falling back to defaults."""
    config_path = path or CONFIG_FILE
    if not config_path.exists():
        return DEFAULT_CONFIG

    with config_path.open("rb") as fh:
        data = tomllib.load(fh)

    return _validate_raw_config(data)


def save_config(config: AppConfig, path: Optional[Path] = None) -> None:
    """Persist the configuration to disk."""
    config_path = path or CONFIG_FILE
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Defer import to avoid hard dependency when only reading defaults
    try:
        import tomli_w  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - optional dependency guard
        raise ImportError(
            "Saving configuration requires the 'tomli-w' package. Install minimal-browser with the 'config' extra."
        ) from exc

    with config_path.open("wb") as fh:
        tomli_w.dump(config.model_dump(mode="python"), fh)


__all__ = [
    "AppConfig",
    "AIConfig",
    "BrowserConfig",
    "StorageConfig",
    "SecurityConfig",
    "DEFAULT_CONFIG",
    "CONFIG_DIR",
    "CONFIG_FILE",
    "load_config",
    "save_config",
]
