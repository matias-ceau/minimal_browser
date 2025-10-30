"""Structured AI helpers using pydantic-ai."""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from pydantic import BaseModel, field_validator
from pydantic_ai import Agent

from .models import AIModel, DEFAULT_MODEL, get_model
from .schemas import AIAction


class StructuredAIError(RuntimeError):
    """Raised when the structured AI pipeline cannot complete."""


class StructuredActionEnvelope(BaseModel):
    """Envelope for AI-generated actions with validation."""

    action: AIAction

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: AIAction) -> AIAction:
        """Ensure the action is properly validated."""
        if v is None:
            raise ValueError("Action cannot be None")
        return v


class StructuredBrowserAgent:
    """Wrapper around pydantic-ai to enforce structured browser actions."""

    def __init__(
        self,
        *,
        model_name: str = DEFAULT_MODEL,
        system_prompt: str,
        history: Optional[Iterable[Dict[str, str]]] = None,
    ) -> None:
        if not system_prompt or not system_prompt.strip():
            raise StructuredAIError("System prompt cannot be empty")

        self._model_name = model_name
        self._model_config = get_model(self._model_name)
        if self._model_config is None:
            raise StructuredAIError(f"Unknown model '{model_name}'")

        self._system_prompt = system_prompt
        self._init_agent()

        self._history: List[Dict[str, str]] = list(history or [])
        self._validate_history()

    def _validate_history(self) -> None:
        """Validate that history entries have required fields."""
        for idx, item in enumerate(self._history):
            if not isinstance(item, dict):
                raise StructuredAIError(
                    f"History item at index {idx} must be a dictionary"
                )
            if "role" not in item or "content" not in item:
                raise StructuredAIError(
                    f"History item at index {idx} missing 'role' or 'content'"
                )

    def _init_agent(self) -> None:
        agent_identifier = self._model_config.resolved_model_id()
        self._agent = Agent(
            agent_identifier,
            output_type=StructuredActionEnvelope,
            system_prompt=self._system_prompt,
        )

    def run(self, user_query: str) -> AIAction:
        """Execute the agent and return a structured AIAction."""
        if not user_query or not user_query.strip():
            raise StructuredAIError("User query cannot be empty")

        history_lines = []
        for item in self._history:
            role = item.get("role", "user").capitalize()
            content = item.get("content", "")
            if content:
                history_lines.append(f"{role}: {content}")

        history_block = "\n".join(history_lines)
        if history_block:
            composed_prompt = (
                f"Conversation so far:\n{history_block}\n\nUser: {user_query}"
            )
        else:
            composed_prompt = user_query

        try:
            result = self._agent.run_sync(composed_prompt)
        except Exception as exc:  # pragma: no cover - defensive fallback
            message = str(exc)
            if (
                "not a valid model id" in message.lower()
                and self._model_config.provider == "openrouter"
            ):
                fallback = self._get_fallback_model()
                if fallback is not None:
                    print(
                        "Requested OpenRouter model unavailable; "
                        "falling back to 'claude-4-sonnet'."
                    )
                    self._model_name = "claude-4-sonnet"
                    self._model_config = fallback
                    self._init_agent()
                    return self.run(user_query)
            raise StructuredAIError(f"Structured agent failed: {message}") from exc
        if result.output is None:
            raise StructuredAIError("Structured agent returned no output.")
        
        # Validate the action before returning
        if not isinstance(result.output.action, (type(None).__class__,)):
            # The action is already validated by Pydantic, just return it
            return result.output.action
        raise StructuredAIError("Invalid action type returned from agent")

    def _get_fallback_model(self) -> Optional[AIModel]:
        """Return a fallback model configuration when available."""
        if self._model_name == "claude-4-sonnet":
            return None
        fallback = get_model("claude-4-sonnet")
        if fallback is None or fallback is self._model_config:
            return None
        return fallback
