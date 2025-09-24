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


# Available AI models
MODELS = {
    "gpt-5": AIModel(
        name="gpt-5",
        provider="openai",
        max_tokens=4000,
        supports_streaming=True,
        cost_per_token=0.000005,
    ),
    "claude-4-sonnet": AIModel(
        name="anthropic/claude-3.5-sonnet",
        provider="openrouter",
        max_tokens=4000,
        supports_streaming=True,
        cost_per_token=0.000003,
    ),
    "llama-3.1-70b": AIModel(
        name="meta-llama/llama-3.1-70b-instruct",
        provider="openrouter",
        max_tokens=4000,
        supports_streaming=True,
        cost_per_token=0.000001,
    ),
}

DEFAULT_MODEL = "gpt-5"


def get_model(name: str) -> Optional[AIModel]:
    """Get model configuration by name"""
    return MODELS.get(name)


def list_models() -> List[str]:
    """List available model names"""
    return list(MODELS.keys())
