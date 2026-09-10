# OmniSolve 3.0 - Installation & Setup Guide

## Quick Start (current repository layout)

> The sections below document the legacy Windows/Runtime deployment. The current
> repository layout (`Core/`, `Config/`, `tests/` at the project root) installs and
> runs on Linux, macOS, and Windows like any standard Python project:

### 1. Install dependencies (Python 3.8+)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Verify the installation

```bash
python -c "from Core.config import config_loader; print(config_loader.load_persona('Architect')['name'])"
python -c "from Core.utils import psi_generator; print(psi_generator.generate_psi('demo'))"
```

### 3. Run the orchestrator

```bash
python -m Core.orchestrator --help   # shows the required project/task arguments
# or, after `pip install -e .`:
omnisolve --help
```

Before the first real run, start your LLM backend (KoboldCPP by default; see
README → “Configuration (Environment Variables)” for `OMNISOLVE_API_URL`,
`OMNISOLVE_BRAIN_BACKEND`, `OPENAI_API_KEY`, and `ANTHROPIC_API_KEY`).

### 4. Run the tests

```bash
python -m pytest tests/unit         # unit tests (no live LLM backend required)
python -m pytest tests/integration  # integration tests (mock-based)
python -m pytest                    # full suite + coverage report
```

## Prerequisites

- Windows OS
- The existing OmniSolve directory with Runtime/ folder
- Internet connection (for installing Python packages)

## Installation Steps

### 1. Install Python Dependencies

```batch
REM Navigate to the AI_System directory
cd e:\AI_System

REM Install required packages using the embedded Python
Runtime\python.exe -m pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed requests-2.31.0 aiofiles-23.2.1
```

### 2. Verify Installation

```batch
REM Test import of the new modules
Runtime\python.exe -c "from AI_System.Core import OmniSolveOrchestrator; print('✓ Installation successful!')"
```

### 3. First Run

```batch
REM Simply run the launcher
LAUNCH_OMNISOLVE.bat
```

The launcher will:
1. Check for the model file
2. Start KoboldCPP (AI engine)
3. Wait for the API to be ready
4. Launch OmniSolve 3.0 orchestrator

### 4. Test with a Simple Project

When prompted:
```
Project Name: test_calculator
Development Request: Create a simple Python calculator with add, subtract, multiply, and divide functions
```

## Troubleshooting

### Issue: "No module named 'AI_System'"

**Solution:**
```batch
REM Make sure you're running from the correct directory
cd e:\
Runtime\python.exe -m AI_System.Core.orchestrator
```

### Issue: "No module named 'requests'" or "No module named 'aiofiles'"

**Solution:**
```batch
cd e:\AI_System
Runtime\python.exe -m pip install requests aiofiles
```

### Issue: "Cannot connect to API"

**Checklist:**
1. Is KoboldCPP running? Check Task Manager
2. Wait longer - model loading takes 3-5 minutes
3. Check port 5001 isn't blocked by firewall
4. Review `AI_System\Logs\orchestrator_*.log` for details

### Issue: "ConfigurationError: Persona configuration not found"

**Solution:**
Ensure these files exist in `AI_System\Config\`:
- Architect.json
- Steve.json (for Developer role)
- Planner.json
- QA.json

### Issue: "Module has no attribute 'run'"

**Solution:**
Old orchestrator may still be active. Ensure:
1. `OmniSolve_Orchestrator.py` was renamed to `.py.old`
2. New `orchestrator.py` exists in `AI_System\Core\`
3. `__init__.py` exists in `AI_System\Core\`

## Configuration (Optional)

### Customize Settings

Edit `AI_System\Core\config\constants.py`:

```python
# Increase retry attempts
MAX_RETRIES = 5

# Adjust temperature
DEFAULT_TEMPERATURE = 0.4

# Increase PSI cache time
PSI_CACHE_TIMEOUT = 600  # 10 minutes

# Change log level
LOG_LEVEL = "DEBUG"  # More verbose logging
```

### Environment Variables (Alternative)

Set environment variables before running:

```batch
REM Windows Command Prompt
set OMNISOLVE_LOG_LEVEL=DEBUG
set OMNISOLVE_API_TIMEOUT=180
LAUNCH_OMNISOLVE.bat

REM PowerShell
$env:OMNISOLVE_LOG_LEVEL="DEBUG"
$env:OMNISOLVE_API_TIMEOUT="180"
.\LAUNCH_OMNISOLVE.bat
```

## Verify Everything is Working

### Check Directory Structure

```batch
dir AI_System\Core
```

**Expected:**
```
agents/
config/
exceptions/
logging/
output/
utils/
orchestrator.py
__init__.py
OmniSolve_Orchestrator.py.old
```

### Check Logs

After running once, check:
```batch
dir AI_System\Logs
```

**Expected:**
```
audit_20260105_*.jsonl       (JSON audit trail)
orchestrator_20260105.log    (Main logs)
agents_20260105.log          (Agent activity)
```

### Test Individual Components

```batch
REM Test configuration loading
Runtime\python.exe -c "from AI_System.Core.config import config_loader; print(config_loader.load_persona('Architect'))"

REM Test PSI generation
Runtime\python.exe -c "from AI_System.Core.utils import psi_generator; print(psi_generator.generate_psi('test_project'))"

REM Test text parsers
Runtime\python.exe -c "from AI_System.Core.utils import validate_python_syntax; print(validate_python_syntax('print(123)'))"
```

## Performance Verification

### Caching Test

Run the orchestrator twice with the same project:
1. **First run**: PSI generated fresh, personas loaded from disk
2. **Second run** (within 5 min): PSI from cache, personas from LRU cache

Check logs for:
```
DEBUG - Using cached PSI for <project> (age: X.Xs)
```

### Parallel Execution (Future)

Currently sequential, but infrastructure ready:
- `ParallelAgentExecutor` class exists in `agents/base_agent.py`
- Can parallelize Architect + Planner stages
- Can parallelize multiple file generations

## Rollback (If Needed)

To revert to OmniSolve 2.4:

```batch
REM 1. Rename files back
cd e:\AI_System\Core
move orchestrator.py orchestrator.py.new
move OmniSolve_Orchestrator.py.old OmniSolve_Orchestrator.py

REM 2. Update launcher
notepad ..\LAUNCH_OMNISOLVE.bat
REM Change: python -m AI_System.Core.orchestrator
REM To: python AI_System\Core\OmniSolve_Orchestrator.py

REM 3. Remove new directories (optional)
rmdir /S agents config exceptions logging output utils
```

## Support & Documentation

- **Full Documentation**: `AI_System\README_v3.0.md`
- **File Reference**: `AI_System\FILE_LIST_v3.0.md`
- **Original Docs**: `docs\*.txt`
- **Logs**: `AI_System\Logs\`

## What to Expect

### First Successful Run

```
============================================================
OMNISOLVE v3.0 - REFACTORED ARCHITECTURE
============================================================
Project: test_calculator
Task: Create a simple Python calculator with add, subtract, multiply, and divide functions
============================================================

[STEP 1] Generating Project State Interface...
PSI generated (150 chars)

[STEP 2] ARCHITECT: Designing file structure...
Architecture complete: 2 files planned
  - calculator.py
  - main.py

[STEP 3] PLANNER: Creating logic blueprint...
Blueprint complete (450 chars)

[STEP 4] DEVELOPER (Steve): Generating code...

  [1/2] Working on: calculator.py
    Attempt 1/3...
    Submitting to QA for review...
    ✓ QA passed, writing file...
    ✓ File saved: e:\AI_System\Projects\test_calculator\calculator.py

  [2/2] Working on: main.py
    Attempt 1/3...
    Submitting to QA for review...
    ✓ QA passed, writing file...
    ✓ File saved: e:\AI_System\Projects\test_calculator\main.py

============================================================
PROJECT COMPLETE
============================================================
Files written: 2/2
Files failed: 0/2
Time elapsed: 45.3s
============================================================
```

### Generated Files

Check `AI_System\Projects\test_calculator\`:
- `calculator.py` - Calculator functions
- `main.py` - CLI interface

## Maintenance

### Clear Caches

```batch
REM Clear PSI cache
Runtime\python.exe -c "from AI_System.Core.utils import psi_generator; psi_generator.invalidate_cache()"

REM Clear persona cache
Runtime\python.exe -c "from AI_System.Core.config import config_loader; config_loader.load_persona.cache_clear()"
```

### Rotate Logs

Logs automatically rotate:
- Max 5MB per file
- 3-5 backup files kept
- Old files deleted automatically

Manual cleanup:
```batch
REM Delete logs older than 7 days
forfiles /P "AI_System\Logs" /M *.log /D -7 /C "cmd /c del @path"
```

### Monitor Performance

Check audit logs for timing:
```batch
REM View last audit log
Runtime\python.exe -c "import json; [print(json.loads(line)) for line in open('AI_System\\Logs\\audit_20260105_*.jsonl')]"
```

## Ready to Use!

You're all set! Run `LAUNCH_OMNISOLVE.bat` and start building.

For advanced usage, see `README_v3.0.md`.
