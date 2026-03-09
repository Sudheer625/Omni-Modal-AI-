from typing import Optional

import requests

from config import OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_URL


class LLMClientError(Exception):
    """Raised when LLM calls fail."""


class OpenRouterClient:
    def __init__(self) -> None:
        self.api_url = OPENROUTER_URL
        self.api_key = OPENROUTER_API_KEY
        self.model = OPENROUTER_MODEL

    def _extract_text_content(self, content):
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(item.get("text", ""))
                elif isinstance(item, str):
                    parts.append(item)
            return "\n".join([part for part in parts if part]).strip()
        return ""

    def _post(self, payload: dict) -> str:
        if not self.api_key:
            raise LLMClientError(
                "API key is missing. Set OPENROUTER_API_KEY or OPENAI_API_KEY in .env."
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=120)
        except requests.RequestException as exc:
            raise LLMClientError(f"OpenRouter request failed: {exc}") from exc

        if response.status_code >= 400:
            raise LLMClientError(
                f"OpenRouter API error ({response.status_code}): {response.text}"
            )

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise LLMClientError("OpenRouter returned no choices.")

        message = choices[0].get("message", {})
        content = self._extract_text_content(message.get("content"))

        if not content:
            raise LLMClientError("OpenRouter returned an empty message.")
        return content

    def chat(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }
        return self._post(payload)

    def describe_image(self, image_b64: str, mime_type: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe this image precisely. Include entities, text in image, layout, and important details.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_b64}",
                            },
                        },
                    ],
                }
            ],
            "temperature": 0.1,
        }
        return self._post(payload)
