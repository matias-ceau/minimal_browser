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
        # For OpenRouter with pydantic-ai, use format "openrouter:model-name"
        # (colon separator, not slash)
        if self.provider == "openrouter":
            # If identifier already starts with "openrouter:", return as-is
            if identifier.startswith("openrouter:"):
                return identifier
            # If identifier starts with "openrouter/", convert to colon format
            if identifier.startswith("openrouter/"):
                return identifier.replace("openrouter/", "openrouter:", 1)
            # Otherwise, prepend "openrouter:" (e.g., "openai/gpt-5-codex-preview" -> "openrouter:openai/gpt-5-codex-preview")
            return f"openrouter:{identifier}"
        return identifier


# Available AI models
MODELS = {
    "gpt-5.2": AIModel(
        name="gpt-5.2",
        provider="openrouter",
        max_tokens=8000,
        supports_streaming=True,
        cost_per_token=0.000006,
        model_id="openai/gpt-5.2",
    ),
    "claude-opus-4.5": AIModel(
        name="claude-opus-4.5",
        provider="openrouter",
        max_tokens=8000,
        supports_streaming=True,
        cost_per_token=0.000005,
        model_id="anthropic/claude-opus-4.5",
    ),
    "gemini-3-pro": AIModel(
        name="gemini-3-pro",
        provider="openrouter",
        max_tokens=8000,
        supports_streaming=True,
        cost_per_token=0.000004,
        model_id="google/gemini-3-pro",
    ),
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
    "llama-3.1-70b": AIModel(
        name="openrouter/llama-3.1-70b-instruct",
        provider="openrouter",
        max_tokens=4000,
        supports_streaming=True,
        cost_per_token=0.000001,
        model_id="openrouter/llama-3.1-70b-instruct",
    ),
}

DEFAULT_MODEL = "gpt-5.2"
FALLBACK_MODEL = "claude-opus-4.5"


def get_model(name: str) -> Optional[AIModel]:
    """Get model configuration by name"""
    return MODELS.get(name)


def list_models() -> List[str]:
    """List available model names"""
    return list(MODELS.keys())
