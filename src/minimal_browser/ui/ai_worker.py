"""AI worker thread for non-blocking API calls"""

from typing import Optional

import requests  # type: ignore[import-untyped]
from PySide6.QtCore import QThread, Signal as pyqtSignal

from ..ai.prompts import get_browser_assistant_prompt
from ..ai.structured import StructuredBrowserAgent, StructuredAIError
from ..ai.tools import ResponseProcessor


class AIWorker(QThread):
    """Worker thread for AI API calls with streaming support"""

    response_ready = pyqtSignal(str, str)  # response_type, content
    progress_update = pyqtSignal(str)  # progress message
    streaming_chunk = pyqtSignal(str)  # streaming response chunk

    def __init__(
        self,
        query: str,
        current_url: str = "",
        history: Optional[list[dict[str, str]]] = None,
    ):
        super().__init__()
        self.query = query
        self.current_url = current_url
        self.history = list(history or [])

    def run(self):
        try:
            print(f"AI Worker starting for query: {self.query}")
            self.progress_update.emit("Analyzing request...")

            response = self.get_ai_response(self.query, self.current_url)
            print(f"AI Worker got response: {response[:100]}...")

            self.response_ready.emit("success", response)
        except Exception as e:
            print(f"AI Worker error: {e}")
            self.response_ready.emit("error", str(e))

    def get_ai_response(self, query: str, current_url: str) -> str:
        """Get a structured AI response using pydantic-ai."""
        system_prompt = get_browser_assistant_prompt(current_url)
        agent = StructuredBrowserAgent(
            system_prompt=system_prompt,
            history=self.history,
        )

        self.progress_update.emit("Requesting structured action…")
        try:
            action = agent.run(query)
        except StructuredAIError as exc:
            raise Exception(str(exc)) from exc
        except requests.exceptions.RequestException as exc:
            raise Exception(f"API request failed: {exc}") from exc
        except Exception as exc:  # pragma: no cover - defensive fallback
            raise Exception(f"AI processing failed: {exc}") from exc

        action_type, payload = ResponseProcessor.action_to_tuple(action)

        prefix_map = {
            "navigate": "NAVIGATE:",
            "search": "SEARCH:",
            "html": "HTML:",
        }
        prefix = prefix_map.get(action_type, "HTML:")

        summary = f"{action.type.upper()}: {payload[:160]}"
        self.streaming_chunk.emit(summary)

        return f"{prefix}{payload}"
