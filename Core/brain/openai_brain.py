"""
OpenAI-compatible brain backend.
Supports OpenAI and any OpenAI-compatible API (e.g. LM Studio, Together AI).

Required env vars:
  OPENAI_API_KEY  — your API key
  OPENAI_MODEL    — model name (default: gpt-4o)
  OPENAI_BASE_URL — optional base URL override for compatible APIs
"""
import os
from typing import List

from ..exceptions.errors import BrainConnectionError, BrainResponseError, ConfigurationError
from .base_brain import BrainAPI, GenerateResult


class OpenAIBrainAPI(BrainAPI):
    """
    LLM backend using the OpenAI Python SDK.
    Install with: pip install openai
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ):
        try:
            import openai  # type: ignore
        except ImportError as exc:
            raise ConfigurationError(
                "openai package is required for OpenAI backend. "
                "Install it with: pip install openai"
            ) from exc

        self._model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        resolved_key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not resolved_key:
            raise ConfigurationError(
                "OPENAI_API_KEY environment variable is not set"
            )

        kwargs = {"api_key": resolved_key}
        resolved_base = base_url or os.getenv("OPENAI_BASE_URL")
        if resolved_base:
            kwargs["base_url"] = resolved_base

        self._client = openai.OpenAI(**kwargs)

    def generate(
        self,
        prompt: str,
        temperature: float,
        max_length: int,
        max_context: int,
        stop_tokens: List[str],
    ) -> GenerateResult:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_length,
                stop=stop_tokens or None,
            )
        except Exception as exc:
            # openai raises various subclasses; wrap generically
            err_str = str(exc)
            if "connection" in err_str.lower() or "network" in err_str.lower():
                raise BrainConnectionError(
                    f"OpenAI connection error: {exc}", {"error": err_str}
                ) from exc
            raise BrainResponseError(
                f"OpenAI API error: {exc}", {"error": err_str}
            ) from exc

        choice = response.choices[0]
        text = (choice.message.content or "").strip()
        if not text:
            raise BrainResponseError("OpenAI returned empty response")

        tokens_used: int | None = None
        if response.usage:
            tokens_used = response.usage.completion_tokens

        return GenerateResult(text=text, tokens_used=tokens_used, model=self._model)

    def is_available(self) -> bool:
        try:
            self._client.models.list()
            return True
        except Exception:
            return False
