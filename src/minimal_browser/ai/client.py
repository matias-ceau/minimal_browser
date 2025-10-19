"""AI client for making API requests."""

import json
from typing import Generator, List, Dict

import requests  # type: ignore[import-untyped]

from .auth import auth_manager
from .models import AIModel, get_model, DEFAULT_MODEL


class AIClient:
    """Client for interacting with an AI API like OpenRouter."""

    def __init__(self, system_prompt: str, model_name: str = DEFAULT_MODEL):
        model = get_model(model_name)
        if not model:
            raise ValueError(f"Model '{model_name}' not found.")
        self.model_config: AIModel = model

        self.api_key = auth_manager.get_key(self.model_config.provider)
        if not self.api_key:
            raise ValueError(
                f"API key for provider '{self.model_config.provider}' not found. "
                "Please set the corresponding environment variable."
            )
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.system_prompt = system_prompt

    def get_streaming_response(
        self,
        messages: List[Dict[str, str]],
    ) -> Generator[str, None, None]:
        """Get a streaming AI response from the API."""

        data = {
            "model": self.model_config.resolved_model_id(),
            "messages": messages,
            "stream": True,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        buffer = ""
        with requests.post(
            self.api_url, headers=headers, json=data, stream=True
        ) as response:
            response.raise_for_status()
            response.encoding = "utf-8"

            for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                if not chunk:
                    continue
                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.startswith("data: "):
                        data_content = line[6:]
                        if data_content == "[DONE]":
                            return
                        try:
                            data_obj = json.loads(data_content)
                            content = (
                                data_obj.get("choices", [{}])[0]
                                .get("delta", {})
                                .get("content")
                            )
                            if content:
                                yield content
                        except (json.JSONDecodeError, IndexError):
                            continue
