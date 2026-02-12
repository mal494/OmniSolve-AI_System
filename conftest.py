"""
Pytest configuration and fixtures.
Sets up the test environment and provides common fixtures.
"""
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Also ensure Core is importable
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest


@pytest.fixture(scope="session")
def project_root_dir():
    """Return the project root directory."""
    return project_root


@pytest.fixture(scope="session")
def core_dir():
    """Return the Core directory."""
    return project_root / "Core"


@pytest.fixture(scope="session")
def tests_dir():
    """Return the tests directory."""
    return project_root / "tests"
