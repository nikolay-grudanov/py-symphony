# Code Reviewer - Handoffs

## When to Hand Off

### To implementation-engineer
**Trigger**: Review completed with issues found

**Format**:
```
## Hand-off: Code Review Complete

**Reviewed**: [file/path]
**Issues Found**: N total (Critical: N, Important: N, Can Improve: N)

**Next**: Fix critical and important issues
```

### To test-engineer
**Trigger**: Bugs found that need tests

**Format**:
```
## Hand-off: Bugs Found

**File**: [path]
**Bugs**:
- [Bug 1]: description
- [Bug 2]: description

**Next**: Write tests to verify fixes
```

### To security-expert
**Trigger**: Critical security issues found

**Format**:
```
## Hand-off: Security Issues

**File**: [path]
**Critical Issues**:
- [Issue 1]: description
- [Issue 2]: description

**Next**: Deep security review
```

## Handoff Criteria

| Issue Type | Agent |
|-----------|-------|
| Code fixes | implementation-engineer |
| Bug tests | test-engineer |
| Security deep dive | security-expert |
| Verification | verification-agent |