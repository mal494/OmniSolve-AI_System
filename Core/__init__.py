"""
OmniSolve Core Module
"""
from .orchestrator import OmniSolveOrchestrator, main
from .version import __version__, __version_info__

__all__ = ['OmniSolveOrchestrator', 'main', '__version__', '__version_info__']
