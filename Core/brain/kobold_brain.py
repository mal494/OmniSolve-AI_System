"""
KoboldCPP brain backend.
Implements BrainAPI using the KoboldCPP local API (default backend).
"""
from typing import List

import requests

from ..config.constants import API_URL, API_TIMEOUT
from ..exceptions.errors import BrainConnectionError, BrainResponseError
from .base_brain import BrainAPI, GenerateResult


class KoboldBrainAPI(BrainAPI):
    """
    Communicates with a locally-running KoboldCPP instance via HTTP.
    Default endpoint: http://localhost:5001/api/v1/generate
    """

    def __init__(
        self,
        api_url: str = API_URL,
        api_timeout: int = API_TIMEOUT,
    ):
        self._api_url = api_url
        self._api_timeout = api_timeout

    def generate(
        self,
        prompt: str,
        temperature: float,
        max_length: int,
        max_context: int,
        stop_tokens: List[str],
    ) -> GenerateResult:
        payload = {
            "prompt": prompt,
            "max_context_length": max_context,
            "max_length": max_length,
            "temperature": temperature,
            "stop_sequence": stop_tokens,
        }

        try:
            response = requests.post(
                self._api_url,
                json=payload,
                timeout=self._api_timeout,
            )
            response.raise_for_status()
        except requests.exceptions.Timeout as exc:
            raise BrainConnectionError(
                f"KoboldCPP request timed out after {self._api_timeout}s",
                {"url": self._api_url, "error": str(exc)},
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise BrainConnectionError(
                "Unable to connect to KoboldCPP API",
                {"url": self._api_url, "error": str(exc)},
            ) from exc
        except requests.exceptions.HTTPError as exc:
            raise BrainResponseError(
                f"KoboldCPP HTTP error: {exc.response.status_code}",
                {"url": self._api_url, "error": str(exc)},
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise BrainResponseError(
                "KoboldCPP returned non-JSON response",
                {"error": str(exc)},
            ) from exc

        if "results" not in data or not data["results"]:
            raise BrainResponseError(
                "KoboldCPP response missing 'results' field",
                {"response": data},
            )

        text = data["results"][0].get("text", "").strip()
        if not text:
            raise BrainResponseError("KoboldCPP returned empty text")

        # Extract token usage if reported
        tokens_used: int | None = None
        if "usage" in data and isinstance(data["usage"], dict):
            tokens_used = data["usage"].get("completion_tokens") or data["usage"].get("tokens")

        return GenerateResult(text=text, tokens_used=tokens_used, model="koboldcpp")

    def is_available(self) -> bool:
        """Check if the KoboldCPP API is reachable."""
        try:
            base = self._api_url.rsplit("/api/", 1)[0]
            resp = requests.get(f"{base}/api/v1/info", timeout=5)
            return resp.status_code < 500
        except Exception:
            return False
