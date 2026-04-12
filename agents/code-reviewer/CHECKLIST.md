# Code Reviewer - Checklist

## Quality Gates

### Before submitting review:
- [ ] All security issues found
- [ ] All logic issues found
- [ ] All performance issues found
- [ ] All style issues found
- [ ] Issues properly classified (Critical/Important/Can Improve)
- [ ] Recommendations provided for each issue

### Review completeness:
- [ ] No obvious issues missed
- [ ] Edge cases considered
- [ ] Error handling verified

## Validation Checklist

### Security
- [ ] Secrets checked
- [ ] SQL injection checked
- [ ] XSS checked
- [ ] Unsafe functions checked

### Logic
- [ ] Edge cases checked
- [ ] Null handling checked
- [ ] Error handling checked

### Performance
- [ ] N+1 queries checked
- [ ] Memory leaks checked
- [ ] Algorithm complexity checked

### Style
- [ ] PEP 8 compliance checked
- [ ] Naming checked
- [ ] Documentation checked

## Common Pitfalls

1. **Missing edge cases**: Всегда проверять null, empty, boundary values
2. **Incorrect priority**: Critical vs Important - разница в severity
3. **Generic recommendations**: Давать конкретные примеры
4. **No context**: Указывать строку и файл для каждого issue