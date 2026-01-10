# Simple Calculator Example

This is a self-contained example project that demonstrates OmniSolve's incremental continuation capabilities.

## Project Description

A simple command-line calculator application with basic arithmetic operations.

## Initial Implementation

The first version includes:
- Basic arithmetic operations (add, subtract, multiply, divide)
- Simple command-line interface
- Input validation

## Incremental Enhancements (for testing continuation)

This example can be used to test incremental continuation by asking OmniSolve to add features:

1. **Add square root operation**
2. **Add memory functions (store/recall)**
3. **Add history tracking**
4. **Add unit tests**
5. **Add help menu**

## Usage

### Running Initial Version

```bash
python calculator.py
```

### Example Session

```
Simple Calculator
1. Add
2. Subtract
3. Multiply
4. Divide
5. Quit

Choose operation: 1
Enter first number: 5
Enter second number: 3
Result: 8.0

Choose operation: 5
Goodbye!
```

## Testing Incremental Continuation

### Step 1: Generate Initial Version

Ask OmniSolve:
```
Create a simple command-line calculator with add, subtract, multiply, and divide operations.
```

### Step 2: Add Feature (Square Root)

Ask OmniSolve:
```
Add a square root operation to the existing calculator. Keep all existing functionality.
```

### Step 3: Add Memory Functions

Ask OmniSolve:
```
Add memory store and recall functions to the calculator. Users should be able to store the last result and recall it later.
```

### Step 4: Verify Incremental Behavior

Check that:
- ✅ Original operations still work
- ✅ New features are added
- ✅ Code structure is preserved
- ✅ No functionality is lost
- ✅ Changes are surgical and minimal

## Expected Project State Interface (PSI)

### Initial State
```
PROJECT STATE: simple_calculator
Files:
  calculator.py - Main calculator implementation (120 lines)
```

### After Adding Square Root
```
PROJECT STATE: simple_calculator
Files:
  calculator.py - Main calculator implementation (145 lines)
    - Added sqrt operation
    - Updated menu
    - Added sqrt validation
```

### After Adding Memory
```
PROJECT STATE: simple_calculator
Files:
  calculator.py - Main calculator implementation (180 lines)
    - Calculator with memory functions
    - Memory store/recall operations
```

## Architecture Correctness Checks

When testing continuation, verify:

1. **PSI Accuracy** - Does the PSI correctly represent the current state?
2. **Architect Awareness** - Does Architect recognize existing files?
3. **Planner Respect** - Does Planner build on existing structure?
4. **Developer Precision** - Does Developer make surgical changes?
5. **QA Validation** - Does QA catch regressions?

## Success Criteria

✅ **Incremental** - Each change builds on previous version
✅ **Preservative** - Existing code is not unnecessarily modified
✅ **Correct** - All operations continue to work
✅ **Clean** - Code quality is maintained or improved
✅ **Auditable** - Changes are clearly logged

## Lessons Learned (to document)

After testing, document:
- What worked well
- What was regenerated unnecessarily
- Where PSI helped
- Where continuation failed
- Improvements needed
