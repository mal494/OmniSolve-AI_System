"""
Setup script for OmniSolve AI System
"""
from setuptools import setup, find_packages
from pathlib import Path
import sys

# Add Core to path to import version
sys.path.insert(0, str(Path(__file__).parent))
from Core.version import __version__

# Read the README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, encoding="utf-8") as f:
        requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith("#")
        ]

setup(
    name="omnisolve-ai-system",
    version=__version__,
    author="OmniSolve Contributors",
    author_email="",
    description="A local, role-based AI software orchestration system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mal494/OmniSolve-AI_System",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "flake8>=6.0.0",
            "pylint>=2.17.0",
            "mypy>=1.4.0",
            "types-requests>=2.31.0",
            "black>=23.0.0",
            "isort>=5.12.0",
        ],
        "openai": [
            "openai>=1.0.0",
        ],
        "anthropic": [
            "anthropic>=0.20.0",
        ],
        "all": [
            "openai>=1.0.0",
            "anthropic>=0.20.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "omnisolve=Core.orchestrator:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="ai code-generation software-engineering multi-agent orchestration",
)
