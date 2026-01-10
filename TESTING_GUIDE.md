# OmniSolve Testing Guide

## Overview

This document describes the testing infrastructure for OmniSolve v3.0 and how to write and run tests.

## Test Structure

```
tests/
├── __init__.py
├── unit/                    # Unit tests for individual modules
│   ├── test_text_parsers.py
│   ├── test_psi_generator.py
│   └── test_config_loader.py
├── integration/             # Integration tests for workflows
│   └── test_agent_workflow.py
└── fixtures/                # Test data and fixtures
    └── __init__.py
```

## Running Tests

### Install Test Dependencies

```bash
python -m pip install -r requirements.txt
```

This installs:
- `pytest` - Testing framework
- `pytest-asyncio` - Support for async tests
- `pytest-cov` - Code coverage reporting

### Run All Tests

```bash
# From the project root
python -m pytest

# With verbose output
python -m pytest -v

# With coverage report
python -m pytest --cov=Core --cov-report=term-missing
```

### Run Specific Test Files

```bash
# Run text parser tests only
python -m pytest tests/unit/test_text_parsers.py

# Run integration tests only
python -m pytest tests/integration/

# Run a specific test class
python -m pytest tests/unit/test_text_parsers.py::TestExtractJson

# Run a single test
python -m pytest tests/unit/test_text_parsers.py::TestExtractJson::test_extract_simple_json_list
```

### Run Tests by Marker

Tests can be marked with categories:

```bash
# Run only unit tests
python -m pytest -m unit

# Run only integration tests
python -m pytest -m integration

# Skip slow tests
python -m pytest -m "not slow"
```

## Test Configuration

Test configuration is in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

# Markers
markers = [
    "unit: Unit tests for individual components",
    "integration: Integration tests for workflows",
    "slow: Tests that take significant time to run",
]
```

## Writing Tests

### Unit Test Example

```python
"""Unit tests for my_module."""
import pytest
from Core.my_module import my_function

class TestMyFunction:
    """Tests for my_function."""

    def test_basic_functionality(self):
        """Test basic behavior."""
        result = my_function("input")
        assert result == "expected"

    def test_edge_case(self):
        """Test edge case."""
        with pytest.raises(ValueError):
            my_function(None)
```

### Using Fixtures

```python
@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {"key": "value"}

def test_with_fixture(sample_data):
    """Test using fixture data."""
    assert "key" in sample_data
```

### Mocking API Calls

```python
from unittest.mock import patch, Mock

def test_with_mock_api():
    """Test with mocked API response."""
    with patch('Core.agents.base_agent.BaseAgent.query_brain') as mock_query:
        mock_query.return_value = "Mocked response"
        
        agent = MyAgent()
        result = agent.process("task")
        
        assert "Mocked" in result
        mock_query.assert_called_once()
```

### Testing Async Code

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async functionality."""
    result = await async_function()
    assert result is not None
```

## Test Coverage

### View Coverage Report

After running tests with coverage:

```bash
# Terminal report
python -m pytest --cov=Core --cov-report=term-missing

# HTML report (opens in browser)
python -m pytest --cov=Core --cov-report=html
open htmlcov/index.html
```

### Coverage Goals

- **Core utilities**: Aim for 80%+ coverage
- **Agents**: Aim for 70%+ coverage (harder due to API dependencies)
- **Configuration**: Aim for 80%+ coverage
- **Orchestrator**: Aim for 60%+ coverage (complex integration logic)

## Current Test Status

### Completed Tests

✅ **text_parsers.py** (30 tests)
- JSON extraction (7 tests)
- Code extraction (6 tests)
- Python syntax validation (8 tests)
- Response cleaning (5 tests)
- Edge cases (4 tests)
- **Status**: All passing

### In Progress Tests

🟡 **psi_generator.py** (16 tests)
- Basic generation (5 tests)
- Caching (3 tests)
- Filtering (3 tests)
- Edge cases (5 tests)
- **Status**: 6 passing, 10 need fixture improvements

🟡 **config_loader.py** (24 tests)
- Basic loading (6 tests)
- Caching (2 tests)
- Validation (3 tests)
- Edge cases (13 tests)
- **Status**: Created, needs testing

🟡 **agent_workflow.py** (8 integration tests)
- Agent output formats (4 tests)
- Data flow between agents (3 tests)
- End-to-end workflow (1 test)
- **Status**: Structure created, needs API mocking

### Planned Tests

📋 **Agents** (base_agent.py, architect.py, planner.py, developer.py, qa.py)
- Prompt building
- Response parsing
- Retry logic
- Error handling

📋 **File Manager** (file_manager.py)
- File writing
- Batch operations
- Validation
- Async operations

📋 **Logger** (logger.py)
- JSON formatting
- Log rotation
- Audit logging

📋 **Orchestrator** (orchestrator.py)
- Workflow execution
- Error recovery
- Progress tracking

## Best Practices

### Do's

✅ **Write focused tests** - One behavior per test
✅ **Use descriptive names** - `test_extract_json_with_nested_structure`
✅ **Test edge cases** - Empty input, None, invalid data
✅ **Use fixtures** - Reuse test setup code
✅ **Mock external dependencies** - API calls, file I/O
✅ **Check both success and failure** - Test error handling
✅ **Keep tests fast** - Use mocks, avoid real API calls

### Don'ts

❌ **Don't test implementation details** - Test behavior, not internals
❌ **Don't make tests dependent** - Each test should be independent
❌ **Don't use real API calls** - Slow and unreliable
❌ **Don't ignore failing tests** - Fix or mark as xfail
❌ **Don't test third-party code** - Trust requests, aiofiles work

## Continuous Integration

### GitHub Actions (Planned)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - run: pip install -r requirements.txt
      - run: pytest --cov=Core --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Troubleshooting

### Import Errors

If tests fail with import errors:

```bash
# Make sure you're in the project root
cd /path/to/OmniSolve-AI_System

# Check Python path
python -c "import sys; print(sys.path)"

# The conftest.py should add project root to path automatically
```

### Fixture Not Found

```python
# Make sure fixture is in same file or conftest.py
@pytest.fixture
def my_fixture():
    return "data"

# Use fixture as parameter
def test_something(my_fixture):
    assert my_fixture == "data"
```

### Async Test Fails

```python
# Add pytest-asyncio marker
@pytest.mark.asyncio
async def test_my_async_function():
    result = await my_async_function()
    assert result is not None
```

## Contributing Tests

When adding new functionality:

1. **Write tests first** (TDD approach)
2. **Ensure tests fail** without implementation
3. **Implement feature** to make tests pass
4. **Refactor** while keeping tests green
5. **Document** test purpose and edge cases

### Test Checklist

- [ ] Tests for happy path
- [ ] Tests for error cases
- [ ] Tests for edge cases (None, empty, invalid)
- [ ] Tests pass consistently
- [ ] Coverage increased
- [ ] Documentation updated

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Python Mock Objects](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py](https://coverage.readthedocs.io/)

## Support

For questions or issues with tests:
1. Check this guide
2. Review existing test examples
3. Check pytest documentation
4. Open an issue with test output and description
