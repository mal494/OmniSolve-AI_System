"""OmniSolve package initializer.

Expose core entry points for programmatic usage.
"""
try:
    from Core.orchestrator import OmniSolveOrchestrator  # noqa: F401
    __all__ = ["OmniSolveOrchestrator"]
except ImportError:
    # Allow tests to run without the full package being installed
    __all__ = []
