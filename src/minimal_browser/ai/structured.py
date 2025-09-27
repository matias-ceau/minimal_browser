"""Structured AI helpers using pydantic-ai."""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from pydantic_ai import Agent
from pydantic import BaseModel

from .models import AIModel, DEFAULT_MODEL, get_model
from .schemas import AIAction


class StructuredAIError(RuntimeError):
    """Raised when the structured AI pipeline cannot complete."""


class StructuredActionEnvelope(BaseModel):
    action: AIAction


class StructuredBrowserAgent:
    """Wrapper around pydantic-ai to enforce structured browser actions."""

    def __init__(
        self,
        *,
        model_name: str = DEFAULT_MODEL,
        system_prompt: str,
        history: Optional[Iterable[Dict[str, str]]] = None,
    ) -> None:
        self._model_name = model_name
        self._model_config = get_model(self._model_name)
        if self._model_config is None:
            raise StructuredAIError(f"Unknown model '{model_name}'")

        self._system_prompt = system_prompt
        self._init_agent()

        self._history: List[Dict[str, str]] = list(history or [])

    def _init_agent(self) -> None:
        agent_identifier = self._model_config.resolved_model_id()
        self._agent = Agent(
            agent_identifier,
            output_type=StructuredActionEnvelope,
            system_prompt=self._system_prompt,
        )

    def run(self, user_query: str) -> AIAction:
        """Execute the agent and return a structured AIAction."""
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
        return result.output.action

    def _get_fallback_model(self) -> Optional[AIModel]:
        """Return a fallback model configuration when available."""
        if self._model_name == "claude-4-sonnet":
            return None
        fallback = get_model("claude-4-sonnet")
        if fallback is None or fallback is self._model_config:
            return None
        return fallback
