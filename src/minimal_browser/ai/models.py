"""AI model configurations and providers"""

from typing import Annotated, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class AIModel(BaseModel):
    """AI model configuration with type validation."""

    name: Annotated[str, Field(min_length=1, description="Model name identifier")]
    provider: Annotated[
        str, Field(min_length=1, description="AI provider (e.g., openrouter, openai)")
    ]
    max_tokens: Annotated[int, Field(gt=0, description="Maximum token limit")]
    supports_streaming: bool = Field(
        description="Whether the model supports streaming responses"
    )
    cost_per_token: Annotated[float, Field(ge=0.0)] = 0.0
    model_id: Optional[str] = Field(
        default=None, description="Provider-specific model identifier"
    )

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Ensure provider name is lowercase for consistency."""
        return v.lower()

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
    """Get model configuration by name with validation."""
    return MODELS.get(name)


def list_models() -> List[str]:
    """List available model names"""
    return list(MODELS.keys())


def validate_model_config(name: str) -> bool:
    """Validate that a model configuration exists and is properly formed."""
    model = get_model(name)
    if model is None:
        return False
    # Pydantic validation happens automatically during model creation
    return True

