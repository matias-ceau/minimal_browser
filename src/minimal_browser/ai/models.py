"""AI model configurations and providers"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AIModel:
    """AI model configuration"""

    name: str
    provider: str
    max_tokens: int
    supports_streaming: bool
    cost_per_token: float = 0.0
    model_id: Optional[str] = None

    def resolved_model_id(self) -> str:
        """Return the provider-aware model identifier for API usage."""
        identifier = self.model_id or self.name
        if self.provider == "openrouter" and not identifier.startswith("openrouter/"):
            return f"openrouter/{identifier}"
        return identifier


# Available AI models
MODELS = {
    "gpt-5-codex-preview": AIModel(
        name="gpt-5-codex-preview",
        provider="openrouter",
        max_tokens=8000,
        supports_streaming=True,
        cost_per_token=0.000006,
        model_id="openai/gpt-5-codex-preview",
    ),
    "gpt-5": AIModel(
        name="gpt-5",
        provider="openai",
        max_tokens=4000,
        supports_streaming=True,
        cost_per_token=0.000005,
    ),
    "claude-4-sonnet": AIModel(
        name="claude-4-sonnet",
        provider="anthropic",
        max_tokens=4000,
        supports_streaming=True,
        cost_per_token=0.000003,
        model_id="anthropic/claude-4-sonnet",
    ),
    "llama-3.1-70b": AIModel(
        name="openrouter/llama-3.1-70b-instruct",
        provider="openrouter",
        max_tokens=4000,
        supports_streaming=True,
        cost_per_token=0.000001,
        model_id="openrouter/llama-3.1-70b-instruct",
    ),
}

DEFAULT_MODEL = "gpt-5-codex-preview"


def get_model(name: str) -> Optional[AIModel]:
    """Get model configuration by name"""
    return MODELS.get(name)


def list_models() -> List[str]:
    """List available model names"""
    return list(MODELS.keys())
