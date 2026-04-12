# Documentation Writer - Handoffs

## When to Hand Off

### To implementation-engineer
**Trigger**: Need clarification on code behavior

**Format**:
```
## Hand-off: Clarification Needed

**Doc Section**: [section name]
**Question**: [what needs clarification]
**Context**: [relevant code or spec]
```

### To platform-architect
**Trigger**: Architecture documentation needs approval

**Format**:
```
## Hand-off: Architecture Doc Review

**Doc**: [doc name]
**Purpose**: [brief description]
**For Review**: [what needs approval]
```

### To verification-agent
**Trigger**: Documentation complete

**Format**:
```
## Hand-off: Documentation Complete

**Doc**: [doc name]
**Sections**: [list of sections]
**Ready For**: [review/approval]
```

## Handoff Criteria

| Situation | Agent |
|-----------|-------|
| Code clarification | implementation-engineer |
| Architecture approval | platform-architect |
| Final review | verification-agent |