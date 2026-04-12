# OpenCode Plugin JS - Checklist

## Quality Gates

### Before submitting plugin:
- [ ] Documentation loaded (opencode-plugin-docs)
- [ ] TypeScript used (or JS explicitly requested)
- [ ] Type safety ensured
- [ ] Error handling in place
- [ ] Exports properly defined
- [ ] Tests where appropriate

### Plugin structure:
- [ ] Plugin entry exists
- [ ] package.json correct
- [ ] Exports defined
- [ ] Hooks implemented if needed

## Validation Checklist

### Architecture
- [ ] Correct plugin structure
- [ ] Proper exports
- [ ] Hooks wired correctly

### Safety
- [ ] Input validation
- [ ] No secrets in code
- [ ] Error handling

### Code Quality
- [ ] TypeScript used
- [ ] Type hints present
- [ ] Clean code

## Common Pitfalls

1. **No docs loaded**: Always load opencode-plugin-docs first
2. **Wrong architecture**: Plugin vs custom tool decision
3. **Missing types**: Use TypeScript
4. **No error handling**: Always handle errors