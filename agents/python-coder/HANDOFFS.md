# Python Coder - Handoffs

## When to Hand Off

### To test-engineer
**Trigger**: Implementation complete, tests needed

**Format**:
```
## Hand-off: Implementation Complete

**Module**: [module name]
**Functions**: [list]
**Tests**: [test file if any]
**Next**: Additional tests
```

### To verification-agent
**Trigger**: Code ready for verification

**Format**:
```
## Hand-off: Verification Request

**Module**: [module name]
**File**: [path]
**For**: [verification type]
```

### To jupyter-text
**Trigger**: Need Jupyter notebook

**Format**:
```
## Hand-off: Create Notebook

**Purpose**: [what notebook should do]
**Module**: [module to use]
**Context**: [additional context]
```

## Handoff Criteria

| Situation | Agent |
|-----------|-------|
| More tests needed | test-engineer |
| Verification | verification-agent |
| Jupyter notebook | jupyter-text |