# OmniSolve Quick Reference

A quick reference guide for common development tasks in OmniSolve.

## Testing

### Run All Tests
```bash
python -m pytest
```

### Run Specific Test File
```bash
python -m pytest tests/unit/test_text_parsers.py
```

### Run With Coverage
```bash
python -m pytest --cov=Core --cov-report=html
```

### Run Only Unit Tests
```bash
python -m pytest tests/unit/
```

### Run Only Integration Tests
```bash
python -m pytest tests/integration/
```

## Code Quality

### Check Syntax
```bash
python -m py_compile Core/**/*.py
```

### Run Linter (if installed)
```bash
flake8 Core --max-line-length=127
```

### Check Type Hints (if mypy installed)
```bash
mypy Core
```

## Using Validation Utilities

### Validate Architect Output
```python
from Core.utils import validate_architect_output

file_list = [{"path": "main.py", "type": "python", "action": "create"}]
result = validate_architect_output(file_list)

if not result.valid:
    print("Validation failed:")
    for error in result.errors:
        print(f"  - {error}")
```

### Validate Task Description
```python
from Core.utils import validate_task_description

result = validate_task_description("Create a calculator")
if result.warnings:
    print("Warnings:")
    for warning in result.warnings:
        print(f"  - {warning}")
```

### Validate Project Name
```python
from Core.utils import validate_project_name

result = validate_project_name("my_project")
if result.valid:
    print("Project name is valid")
```

## Working with PSI

### Generate PSI
```python
from Core.utils import psi_generator

psi = psi_generator.generate_psi("my_project", use_cache=True)
print(psi)
```

### Invalidate PSI Cache
```python
psi_generator.invalidate_cache("my_project")
```

### Get Cache Stats
```python
stats = psi_generator.get_cache_stats()
print(f"Cached projects: {stats['cached_projects']}")
```

## Working with Configuration

### Load Persona
```python
from Core.config import config_loader

architect = config_loader.load_persona("Architect")
print(architect["system_prompt"])
```

### Reload Persona (after editing config)
```python
config_loader.reload_persona("Architect")
```

## Logging

### Get Logger
```python
from Core.logging import get_logger

logger = get_logger('my_module')
logger.info("Starting operation")
logger.error("Operation failed", exc_info=True)
```

### Audit Log
```python
from Core.logging import audit_log

audit_log('operation_start', project='my_project', user='admin')
```

## Error Handling

### Raise Custom Exception
```python
from Core.exceptions import CodeValidationError

raise CodeValidationError(
    "Code validation failed",
    details={"file": "main.py", "line": 42}
)
```

### Catch Specific Exception
```python
from Core.exceptions import BrainConnectionError

try:
    # API call
    pass
except BrainConnectionError as e:
    print(f"Connection failed: {e.message}")
    print(f"Details: {e.details}")
```

## Text Parsing

### Extract JSON
```python
from Core.utils import extract_json

text = 'Result: [{"name": "test", "value": 123}]'
data = extract_json(text)
```

### Extract Code
```python
from Core.utils import extract_code

text = '''
```python
def hello():
    print("Hello")
```
'''
code = extract_code(text)
```

### Validate Python Syntax
```python
from Core.utils import validate_python_syntax

code = "def test():\n    pass"
is_valid, error = validate_python_syntax(code)
if not is_valid:
    print(f"Syntax error: {error}")
```

## File Operations

### Write File
```python
from Core.output import file_manager

file_manager.write_file(
    "my_project",
    "main.py",
    "print('Hello')",
    validate=True
)
```

### Write Multiple Files
```python
files = [
    ("main.py", "print('Main')"),
    ("utils.py", "def helper(): pass")
]

file_manager.write_files_batch("my_project", files)
```

## Common Constants

### Access Configuration
```python
from Core.config.constants import (
    API_URL,
    MAX_RETRIES,
    DEFAULT_TEMPERATURE,
    PROJECTS_DIR,
    CONFIG_DIR
)

print(f"API URL: {API_URL}")
print(f"Projects dir: {PROJECTS_DIR}")
```

## Debugging Tips

### Enable Debug Logging
Set environment variable:
```bash
export OMNISOLVE_LOG_LEVEL=DEBUG
python -m AI_System.Core.orchestrator
```

### Check Logs
```bash
tail -f Logs/orchestrator_*.log
tail -f Logs/agents_*.log
```

### View Audit Trail
```bash
cat Logs/audit_*.jsonl | jq '.'
```

### Check Cache Stats
```python
from Core.utils import psi_generator

stats = psi_generator.get_cache_stats()
print(stats)
```

## Example Projects

### Simple Calculator
```bash
cd examples/simple_calculator
python calculator.py
```

### Running Examples Through OmniSolve
See example README files for step-by-step instructions on testing incremental continuation.

## Git Workflow

### Run Tests Before Commit
```bash
python -m pytest --tb=short
```

### Check Coverage Before Commit
```bash
python -m pytest --cov=Core --cov-report=term-missing
```

### View What Will Be Committed
```bash
git diff --staged
```

## Documentation

- **TESTING_GUIDE.md** - Comprehensive testing documentation
- **DEVELOPMENT_PROGRESS.md** - Current development status
- **README.md** - System overview
- **INSTALLATION_GUIDE.md** - Setup instructions
- **docs/ROADMAP.md** - Future plans

## Useful Commands Summary

```bash
# Testing
pytest                              # Run all tests
pytest -v                           # Verbose output
pytest -k "test_name"              # Run specific test
pytest --lf                        # Run last failed tests
pytest --cov=Core                  # Coverage report

# Code Quality
flake8 Core                        # Lint code
mypy Core                          # Type checking

# Git
git status                         # Check status
git diff                           # See changes
git log --oneline -10             # Recent commits

# Python
python -m Core.orchestrator        # Run orchestrator
python -c "import Core; print(Core.__version__)"  # Check version
```

## Getting Help

1. Check relevant documentation (see above)
2. Read test files for usage examples
3. Review existing code in Core/ directory
4. Check logs for error details

## Quick Troubleshooting

**Import Error:**
```bash
cd /path/to/OmniSolve-AI_System
export PYTHONPATH=.
python your_script.py
```

**Test Failed:**
```bash
pytest test_file.py -v --tb=long  # See full traceback
```

**Coverage Not Working:**
```bash
pip install pytest-cov
```

**Module Not Found:**
```bash
pip install -r requirements.txt
```
