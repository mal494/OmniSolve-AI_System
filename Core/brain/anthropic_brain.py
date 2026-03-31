"""
Anthropic brain backend.
Uses the Anthropic Python SDK to call Claude models.

Required env vars:
  ANTHROPIC_API_KEY  — your Anthropic API key
  ANTHROPIC_MODEL    — model name (default: claude-sonnet-4-6)
"""
import os
from typing import List

from ..exceptions.errors import BrainConnectionError, BrainResponseError, ConfigurationError
from .base_brain import BrainAPI, GenerateResult

_DEFAULT_MODEL = "claude-sonnet-4-6"


class AnthropicBrainAPI(BrainAPI):
    """
    LLM backend using the Anthropic Python SDK.
    Install with: pip install anthropic
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        try:
            import anthropic  # type: ignore
        except ImportError as exc:
            raise ConfigurationError(
                "anthropic package is required for Anthropic backend. "
                "Install it with: pip install anthropic"
            ) from exc

        self._model = model or os.getenv("ANTHROPIC_MODEL", _DEFAULT_MODEL)
        resolved_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        if not resolved_key:
            raise ConfigurationError(
                "ANTHROPIC_API_KEY environment variable is not set"
            )

        self._client = anthropic.Anthropic(api_key=resolved_key)

    def generate(
        self,
        prompt: str,
        temperature: float,
        max_length: int,
        max_context: int,
        stop_tokens: List[str],
    ) -> GenerateResult:
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=max_length,
                temperature=temperature,
                stop_sequences=stop_tokens or [],
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:
            err_str = str(exc)
            if "connection" in err_str.lower():
                raise BrainConnectionError(
                    f"Anthropic connection error: {exc}", {"error": err_str}
                ) from exc
            raise BrainResponseError(
                f"Anthropic API error: {exc}", {"error": err_str}
            ) from exc

        if not response.content:
            raise BrainResponseError("Anthropic returned empty response")

        text = response.content[0].text.strip()
        if not text:
            raise BrainResponseError("Anthropic returned empty text block")

        tokens_used: int | None = None
        if response.usage:
            tokens_used = response.usage.output_tokens

        return GenerateResult(text=text, tokens_used=tokens_used, model=self._model)

    def is_available(self) -> bool:
        try:
            # Lightweight check — list available models
            self._client.models.list()
            return True
        except Exception:
            return False
