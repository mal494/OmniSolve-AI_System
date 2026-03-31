"""
Brain backend factory.
Creates the appropriate BrainAPI implementation based on configuration.
"""
from typing import Optional

from ..config.constants import BRAIN_BACKEND
from ..exceptions.errors import ConfigurationError
from .base_brain import BrainAPI


def create_brain(backend: Optional[str] = None) -> BrainAPI:
    """
    Create and return the appropriate BrainAPI implementation.

    Args:
        backend: Backend name override. If None, uses OMNISOLVE_BRAIN_BACKEND
                 env var (defaults to "kobold").
                 Choices: kobold, openai, anthropic, mock

    Returns:
        BrainAPI instance ready for use

    Raises:
        ConfigurationError: If backend name is unknown or required packages
                            are not installed
    """
    chosen = (backend or BRAIN_BACKEND).lower().strip()

    if chosen == "kobold":
        from .kobold_brain import KoboldBrainAPI
        return KoboldBrainAPI()

    if chosen == "openai":
        from .openai_brain import OpenAIBrainAPI
        return OpenAIBrainAPI()

    if chosen == "anthropic":
        from .anthropic_brain import AnthropicBrainAPI
        return AnthropicBrainAPI()

    if chosen == "mock":
        from .mock_brain import MockBrainAPI
        return MockBrainAPI()

    raise ConfigurationError(
        f"Unknown brain backend: '{chosen}'. "
        "Valid choices: kobold, openai, anthropic, mock"
    )
