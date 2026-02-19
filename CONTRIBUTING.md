# Contributing to OmniSolve AI System

Thank you for your interest in contributing to OmniSolve! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Style Guidelines](#style-guidelines)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/OmniSolve-AI_System.git
   cd OmniSolve-AI_System
   ```

3. **Add the upstream repository**:
   ```bash
   git remote add upstream https://github.com/mal494/OmniSolve-AI_System.git
   ```

## Development Setup

1. **Install Python 3.8 or higher**

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"  # Install development dependencies
   ```

4. **Verify installation**:
   ```bash
   python -m pytest
   ```

## Making Changes

1. **Create a new branch** for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes** following the style guidelines below

3. **Add tests** for new functionality
   - Unit tests go in `tests/unit/`
   - Integration tests go in `tests/integration/`
   - Follow existing test patterns

4. **Update documentation** as needed
   - Update docstrings for all public APIs
   - Update README.md if adding major features
   - Add entries to CHANGELOG.md

## Testing

### Running Tests

Run all tests:
```bash
python -m pytest
```

Run specific test categories:
```bash
python -m pytest tests/unit/           # Unit tests only
python -m pytest tests/integration/    # Integration tests only
python -m pytest -m slow              # Slow tests
```

Run with coverage:
```bash
python -m pytest --cov=Core --cov-report=html
```

### Writing Tests

- Every new function should have at least one test
- Test edge cases and error conditions
- Use descriptive test names: `test_function_name_when_condition_then_expected_result`
- Use fixtures for common setup (see `conftest.py`)
- Mock external dependencies (API calls, file I/O)

Example test structure:
```python
def test_extract_json_with_valid_json_returns_parsed_dict():
    """Test that extract_json correctly parses valid JSON."""
    # Arrange
    text = 'Some text [{"key": "value"}] more text'
    
    # Act
    result = extract_json(text)
    
    # Assert
    assert result == [{"key": "value"}]
```

## Submitting Changes

1. **Ensure all tests pass**:
   ```bash
   python -m pytest
   ```

2. **Ensure code quality**:
   ```bash
   # Format code
   black Core/ tests/
   isort Core/ tests/
   
   # Lint code
   flake8 Core/ tests/
   pylint Core/
   
   # Type check
   mypy Core/
   ```

3. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Brief description of changes"
   ```
   
   Follow commit message conventions:
   - Use present tense: "Add feature" not "Added feature"
   - Use imperative mood: "Fix bug" not "Fixes bug"
   - Keep first line under 50 characters
   - Add detailed description in body if needed

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**:
   - Go to the original repository on GitHub
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill out the PR template with:
     - Description of changes
     - Related issue numbers
     - Testing performed
     - Screenshots (if UI changes)

## Style Guidelines

### Python Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Maximum line length: 100 characters (enforced by Black)

### Documentation Style

- Use [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- Document all public functions, classes, and modules
- Include type hints for all function signatures

Example docstring:
```python
def process_data(input_path: str, output_path: str) -> bool:
    """
    Process data from input file and write to output file.
    
    Args:
        input_path: Path to the input file
        output_path: Path to the output file
        
    Returns:
        True if processing succeeded, False otherwise
        
    Raises:
        FileNotFoundError: If input_path does not exist
        ValueError: If file format is invalid
    """
    pass
```

### Code Organization

- One class per file (with exceptions for closely related classes)
- Group imports: standard library, third-party, local
- Use relative imports within the Core package
- Keep functions small and focused (< 50 lines ideally)
- Use meaningful variable names (no single letters except loop counters)

### Testing Style

- One test file per module: `test_module_name.py`
- Group related tests in classes
- Use fixtures for common setup
- Keep tests isolated and independent
- Test one thing per test function

## Project Structure

```
OmniSolve-AI_System/
├── Core/                 # Main application code
│   ├── agents/          # Agent implementations
│   ├── config/          # Configuration management
│   ├── exceptions/      # Custom exceptions
│   ├── logging/         # Logging system
│   ├── output/          # File management
│   └── utils/           # Utility functions
├── tests/               # Test suite
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── fixtures/       # Test fixtures
├── examples/            # Example projects
└── docs/               # Documentation

```

## Adding New Features

### Adding a New Agent

1. Create agent file: `Core/agents/myagent.py`
2. Inherit from `BaseAgent`
3. Implement `process()` method
4. Add to `Core/agents/__init__.py`
5. Add tests: `tests/unit/test_myagent.py`
6. Update orchestrator if needed
7. Document in README.md

### Adding a New Utility

1. Create utility file: `Core/utils/myutil.py`
2. Add comprehensive docstrings
3. Export from `Core/utils/__init__.py`
4. Add tests: `tests/unit/test_myutil.py`
5. Document usage in docstring

## Questions?

- Open an issue with the "question" label
- Check existing issues and PRs
- Review documentation in the `docs/` directory

## Recognition

Contributors will be acknowledged in:
- README.md Contributors section
- Release notes
- CHANGELOG.md

Thank you for contributing to OmniSolve!
