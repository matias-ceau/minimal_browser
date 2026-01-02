"""AI model configurations and providers"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


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


def _get_models_json_path() -> Path:
    """Get the path to models.json file."""
    return Path(__file__).parent / "models.json"


def _load_models_from_json() -> tuple[Dict[str, AIModel], str, str]:
    """Load models from JSON file, with fallback to hardcoded models."""
    json_path = _get_models_json_path()
    
    if not json_path.exists():
        # Fallback to hardcoded models if JSON doesn't exist
        return _get_fallback_models()
    
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
        
        models_dict: Dict[str, AIModel] = {}
        for key, model_data in data.get("models", {}).items():
            models_dict[key] = AIModel(
                name=model_data.get("name", key),
                provider=model_data.get("provider", "openrouter"),
                max_tokens=model_data.get("max_tokens", 4000),
                supports_streaming=model_data.get("supports_streaming", True),
                cost_per_token=model_data.get("cost_per_token", 0.0),
                model_id=model_data.get("model_id"),
            )
        
        default_model = data.get("default_model", "gpt-5.2")
        fallback_model = data.get("fallback_model", "claude-opus-4.5")
        
        # Validate that default and fallback models exist
        if default_model not in models_dict:
            default_model = list(models_dict.keys())[0] if models_dict else "gpt-5.2"
        if fallback_model not in models_dict:
            fallback_model = list(models_dict.keys())[1] if len(models_dict) > 1 else list(models_dict.keys())[0] if models_dict else "claude-opus-4.5"
        
        return models_dict, default_model, fallback_model
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        # If JSON is invalid, fall back to hardcoded models
        print(f"Warning: Could not load models from {json_path}: {e}")
        print("Falling back to hardcoded models. Run scripts/generate_models.py to update.")
        return _get_fallback_models()


def _get_fallback_models() -> tuple[Dict[str, AIModel], str, str]:
    """Get fallback hardcoded models (used when JSON doesn't exist or is invalid)."""
    fallback_models = {
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
    return fallback_models, "gpt-5.2", "claude-opus-4.5"


# Load models from JSON file (with fallback to hardcoded)
_MODELS_DICT, _DEFAULT_MODEL, _FALLBACK_MODEL = _load_models_from_json()
MODELS: Dict[str, AIModel] = _MODELS_DICT
DEFAULT_MODEL: str = _DEFAULT_MODEL
FALLBACK_MODEL: str = _FALLBACK_MODEL


def get_model(name: str) -> Optional[AIModel]:
    """Get model configuration by name"""
    return MODELS.get(name)


def list_models() -> List[str]:
    """List available model names"""
    return list(MODELS.keys())
