# OpenCode Plugin Reviewer - Checklist

## Quality Gates

### Before submitting review:
- [ ] opencode-plugin-docs loaded
- [ ] All 10 categories reviewed
- [ ] Findings backed by code
- [ ] Verdict clearly stated
- [ ] Recommendations specific

### Review completeness:
- [ ] Task alignment verified
- [ ] Architecture verified
- [ ] Security verified
- [ ] DX verified

## Validation Checklist

### Categories
- [ ] Task Alignment
- [ ] Plugin Architecture
- [ ] Plugin vs Custom Tool
- [ ] Hooks/Events Wiring
- [ ] Security & Side Effects
- [ ] File Structure & Exports
- [ ] Readability
- [ ] DX
- [ ] Orchestration Risks
- [ ] Edge Cases

### Accuracy
- [ ] Findings with code references
- [ ] Recommendations specific
- [ ] Priority clear

## Common Pitfalls

1. **Editing code**: Never edit, only recommend
2. **No verdict**: Always state verdict
3. **Generic findings**: Be specific
4. **Missing categories**: All 10 must be reviewed