# OpenCode Plugin Reviewer - Handoffs

## When to Hand Off

### To opencode-plugin-js
**Trigger**: Issues found, needs fix

**Format**:
```
## Hand-off: Review Complete - Fixes Needed

**Plugin**: [name]
**Verdict**: [REVISE / PASS WITH CHANGES]

**Critical Issues**:
- [Issue 1]: description → recommendation

**Important Issues**:
- [Issue 1]: description → recommendation

**Next**: Fix issues and resubmit
```

### To integration-architect
**Trigger**: API questions

**Format**:
```
## Hand-off: API Design Question

**Plugin**: [name]
**Question**: [description]
**Context**: [relevant code]
```

## Handoff Criteria

| Situation | Agent |
|-----------|-------|
| Needs fixes | opencode-plugin-js |
| API questions | integration-architect |