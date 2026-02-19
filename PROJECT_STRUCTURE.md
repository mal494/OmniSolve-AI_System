# OmniSolve Project Structure

This document provides a comprehensive overview of the OmniSolve AI System project structure.

## Repository Layout

```
OmniSolve-AI_System/
│
├── Core/                           # Core application modules
│   ├── __init__.py                # Package initialization with version
│   ├── version.py                 # Version management
│   ├── py.typed                   # Type checking marker
│   ├── orchestrator.py            # Main orchestration logic
│   │
│   ├── agents/                    # AI agent implementations
│   │   ├── __init__.py
│   │   ├── base_agent.py         # Base class for all agents
│   │   ├── architect.py          # File structure designer
│   │   ├── planner.py            # Logic blueprint creator
│   │   ├── developer.py          # Code generator
│   │   └── qa.py                 # Code reviewer
│   │
│   ├── config/                    # Configuration management
│   │   ├── __init__.py
│   │   ├── constants.py          # System constants
│   │   └── config_loader.py      # Configuration loader
│   │
│   ├── exceptions/                # Custom exception hierarchy
│   │   ├── __init__.py
│   │   └── errors.py             # Exception definitions
│   │
│   ├── logging/                   # Logging infrastructure
│   │   ├── __init__.py
│   │   └── logger.py             # Structured logging
│   │
│   ├── output/                    # File output management
│   │   ├── __init__.py
│   │   └── file_manager.py       # File operations
│   │
│   └── utils/                     # Utility modules
│       ├── __init__.py
│       ├── psi_generator.py      # Project State Interface
│       ├── text_parsers.py       # Text parsing utilities
│       └── validation.py         # Input/output validation
│
├── Config/                        # Agent persona configurations
│   ├── Architect.json
│   ├── Developer.json
│   ├── Planner.json
│   ├── QA.json
│   └── Steve.json
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── conftest.py               # Test configuration
│   │
│   ├── fixtures/                 # Test fixtures
│   │   └── __init__.py
│   │
│   ├── unit/                     # Unit tests
│   │   ├── __init__.py
│   │   ├── test_config_loader.py
│   │   ├── test_psi_generator.py
│   │   ├── test_text_parsers.py
│   │   └── test_validation.py
│   │
│   └── integration/              # Integration tests
│       ├── __init__.py
│       └── test_agent_workflow.py
│
├── examples/                      # Example projects
│   ├── simple_calculator/        # Calculator example
│   │   ├── README.md
│   │   └── calculator.py
│   │
│   └── todo_list/                # Todo app example
│       └── README.md
│
├── docs/                          # Documentation
│   ├── ROADMAP.md                # Project roadmap
│   │
│   └── api/                      # API documentation
│       └── README.md
│
├── .github/                       # GitHub configuration
│   ├── workflows/                # CI/CD workflows
│   │   └── tests.yml            # Automated testing
│   │
│   ├── ISSUE_TEMPLATE/           # Issue templates
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── documentation.md
│   │
│   └── PULL_REQUEST_TEMPLATE.md  # PR template
│
├── setup.py                       # Package installation
├── pyproject.toml                # Project configuration
├── requirements.txt              # Dependencies
├── MANIFEST.in                   # Package data files
├── Makefile                      # Development tasks
├── mypy.ini                      # Type checking config
├── .pre-commit-config.yaml       # Pre-commit hooks
├── .editorconfig                 # Editor configuration
├── .gitignore                    # Git ignore rules
│
├── LICENSE                        # MIT License
├── README.md                     # Project overview
├── CHANGELOG.md                  # Version history
├── CONTRIBUTING.md               # Contribution guidelines
├── CODE_OF_CONDUCT.md            # Code of conduct
├── INSTALLATION_GUIDE.md         # Setup instructions
├── TESTING_GUIDE.md              # Testing documentation
├── DEVELOPMENT_PROGRESS.md       # Development status
├── DIRECTORY_STRUCTURE.md        # Directory guide
├── FILE_LIST_v3.0.md             # File reference
├── POST_INSTALL_CHECKLIST.md     # Post-install steps
├── QUICK_REFERENCE.md            # Quick reference
└── REFACTORING_SUMMARY.md        # Refactoring notes
```

## Module Organization

### Core Package (`Core/`)

The main application package following a modular architecture:

- **agents/** - Multi-agent system with role-based separation
- **config/** - Centralized configuration management
- **exceptions/** - Hierarchical exception system
- **logging/** - Structured logging with audit trails
- **output/** - File management and validation
- **utils/** - Shared utility functions

### Configuration (`Config/`)

JSON-based persona configurations for each AI agent role.

### Tests (`tests/`)

Comprehensive test suite with:
- **unit/** - Component-level tests (95%+ coverage on utils)
- **integration/** - Workflow tests
- **fixtures/** - Reusable test data

### Documentation

Multiple documentation types:
- **User guides** - Installation, testing, quick reference
- **Developer docs** - API reference, contributing guide
- **Project docs** - Roadmap, file lists, structure guides

### GitHub Integration

- **Workflows** - Automated CI/CD with testing and linting
- **Templates** - Issue and PR templates for better collaboration

## Key Design Patterns

1. **Singleton Pattern**
   - ConfigLoader, FileManager, PSIGenerator, OmniSolveLogger
   - Ensures single instances with shared state

2. **Template Method Pattern**
   - BaseAgent with abstract `process()` method
   - Consistent agent interface and behavior

3. **Factory Pattern**
   - Agent instantiation in orchestrator
   - Centralized object creation

4. **Strategy Pattern**
   - Different retry strategies per agent
   - Flexible error handling

## File Naming Conventions

- **Python modules** - lowercase with underscores: `text_parsers.py`
- **Test files** - prefixed with `test_`: `test_validation.py`
- **Documentation** - UPPERCASE for root docs: `README.md`, `CONTRIBUTING.md`
- **Configuration** - PascalCase JSON: `Architect.json`

## Import Structure

```python
# Top-level imports
from Core import OmniSolveOrchestrator, main, __version__

# Module imports
from Core.agents import ArchitectAgent, PlannerAgent
from Core.config import API_URL, MAX_RETRIES
from Core.exceptions import OmniSolveError, CodeGenerationError
from Core.logging import get_logger, audit_log
from Core.utils import extract_json, validate_python_syntax
```

## Development Workflow

1. **Setup** - `make install-dev` or `pip install -e ".[dev]"`
2. **Testing** - `make test` or `pytest`
3. **Linting** - `make lint` or individual linters
4. **Formatting** - `make format` or `black` + `isort`
5. **Building** - `make build` or `python setup.py sdist bdist_wheel`

## Package Distribution

The project can be distributed as a Python package:

```bash
# Install from source
pip install .

# Install in development mode
pip install -e .

# Build distribution
python setup.py sdist bdist_wheel

# Install from PyPI (when published)
pip install omnisolve-ai-system
```

## Runtime Directories

The following directories are created at runtime (not in repository):

- **Logs/** - Application logs and audit trails
- **Projects/** - Generated project output
- **Runtime/** - Embedded Python/Node.js runtimes
- **Models/** - LLM model files (large, excluded from git)
- **Engine/** - Inference engine binaries

## Version Management

Version is centrally managed in `Core/version.py`:

```python
__version__ = "3.0.0"
__version_info__ = (3, 0, 0)
```

Updated in:
- `Core/__init__.py` - Imports version
- `setup.py` - Reads from package
- `CHANGELOG.md` - Version history

## Type Checking Support

The `Core/py.typed` marker file enables type checking for the package.

```bash
# Run type checking
mypy Core/
```

## Code Quality Tools

- **pytest** - Testing framework
- **pytest-cov** - Coverage reporting
- **black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting
- **pylint** - Additional linting
- **mypy** - Type checking
- **bandit** - Security scanning

## Contributing Workflow

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on:

1. Setting up development environment
2. Creating branches
3. Writing tests
4. Code style
5. Submitting pull requests

## Questions?

- Check [README.md](README.md) for project overview
- See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for setup
- Review [TESTING_GUIDE.md](TESTING_GUIDE.md) for testing
- Read [CONTRIBUTING.md](CONTRIBUTING.md) for development
- Open an issue for other questions
