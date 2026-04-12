# OpenCode Plugin JS - Handoffs

## When to Hand Off

### To opencode-plugin-reviewer
**Trigger**: Plugin implementation complete

**Format**:
```
## Hand-off: Plugin Complete

**Plugin**: [name]
**Files**: [list]
**Type**: [new plugin / extension / custom tool]
**Next**: Review
```

### To integration-architect
**Trigger**: API contract needed

**Format**:
```
## Hand-off: API Contract Needed

**Plugin**: [name]
**API**: [description]
**For**: [approval / design]
```

## Handoff Criteria

| Situation | Agent |
|-----------|-------|
| Plugin ready | opencode-plugin-reviewer |
| API contract | integration-architect |