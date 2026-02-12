"""
Version information for OmniSolve AI System
"""

__version__ = "3.0.0"
__version_info__ = tuple(int(i) for i in __version__.split(".") if i.isdigit())

# Version history
VERSION_HISTORY = {
    "3.0.0": "Complete refactoring with modular architecture, comprehensive testing, and improved documentation",
    "2.4.0": "Enhanced agent coordination and PSI generation",
    "2.0.0": "Multi-agent workflow implementation",
    "1.0.0": "Initial release",
}

def get_version():
    """Get the current version string."""
    return __version__

def get_version_info():
    """Get the current version as a tuple of integers."""
    return __version_info__
