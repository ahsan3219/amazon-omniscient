"""Google Gemini client using the official Google Gen AI SDK."""

from google import genai

from app.core.exceptions import LLMError
from app.llm.base_client import BaseLLMClient


class GeminiClient(BaseLLMClient):
    """Async Gemini implementation of Omniscient's shared LLM interface."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        if not api_key:
            raise LLMError("GEMINI_API_KEY is required for Gemini provider")
        self.client = genai.Client(api_key=api_key).aio
        self.model = model

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        system_message: str | None = None,
        json_mode: bool = False,
        response_schema: dict | None = None,
    ) -> str:
        config: dict = {
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_message:
            config["system_instruction"] = system_message
        if json_mode:
            config["response_mime_type"] = "application/json"
            if response_schema:
                config["response_schema"] = response_schema

        try:
            response = await self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )
            content = response.text
            if not content:
                raise LLMError("Gemini returned an empty response")
            return content
        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(f"Gemini API call failed: {exc}") from exc
