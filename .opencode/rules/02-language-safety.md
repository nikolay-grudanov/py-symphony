# Language & Safety Rule

**Priority**: HIGH | **Applies to**: All agents

---

## Purpose

Define language usage and safety boundaries for all agents in the system.

---

## Language Strategy

### System Instructions (Internal)

**Language**: **English**

Reason: Modern LLMs (GPT-4, Claude, Grok, Llama 3) are trained primarily on English (90%+ training data). English system prompts provide:
- +10-20% accuracy for complex tasks (reasoning, tool calls, JSON structures)
- Better adherence to instructions (fewer hallucinations)
- Improved tool call reliability (+25% success rate)

**Examples**:
- System role definition: English
- Few-shot examples: English
- Tool call templates: English

### User-Facing Output

**Language**: **Russian**

Reason: User speaks Russian and expects Russian responses.

**Scope**:
- Response text: Russian
- Markdown cells in notebooks: Russian
- Code comments: Russian
- Error messages: Russian

**Exceptions** (must remain English):
- Variable names
- Function names
- Technical terms (in their original language)
- JSON/Tool calls

---

## Language Consistency Rule

**CRITICAL**: DO NOT mix languages in a single prompt

❌ **Wrong**:
```
Ты эксперт по ML. Load {"tool": "skill", "name": "whoami"}
```

✅ **Correct**:
```
You are an ML expert. Load {"tool": "skill", "name": "whoami"}.
Respond to user in Russian.
```

**Why**: Mixed language causes confusion in 20-30% of cases (HuggingFace research).

---

## Safety Boundaries

### Input Validation

**ALWAYS**:
1. Validate user input for malicious patterns
2. Check for SQL injection, code injection, XSS
3. Verify file paths are within project directory
4. Sanitize user-generated content

**NEVER**:
- Execute code that deletes files without confirmation
- Run commands with `sudo`, `rm -rf /`, or similar destructive patterns
- Access files outside project directory
- Execute arbitrary shell commands from user input

### Output Safety

**RED FLAGS** - If user asks to:
- Create malware, viruses, or harmful code → **REFUSE**
- Generate exploits or attack tools → **REFUSE**
- Access protected data without authorization → **REFUSE**
- Bypass security controls → **REFUSE**

**Response to malicious requests**:
```
I cannot help with that request as it may be harmful.
If you need help with legitimate security research or
testing, please provide more context about your goals.
```

### Code Safety

**Before writing/executing code**:
1. Review for security vulnerabilities
2. Check for exposed secrets (API keys, passwords)
3. Verify no hardcoded credentials
4. Ensure proper error handling

### File Safety

**NEVER**:
- Write secrets to files (`.env`, credentials.json, etc.)
- Commit sensitive data to version control
- Create files with executable permissions unnecessarily

---

## Error Handling

### When Errors Occur

1. **Analyze**: Understand what went wrong
2. **Explain**: Provide clear Russian error description
3. **Suggest**: Offer safe solution
4. **Validate**: Verify solution before recommending

**Example**:
```markdown
## Ошибка: ModuleNotFoundError

Пакет `scikit-learn` не установлен.

**Решение:**
```bash
pip install scikit-learn
```

Затем повторите импорт.
```

---

## Validation Checklist

Before responding to user, check:
- [ ] Language consistency maintained (no mixing)
- [ ] User-facing text in Russian
- [ ] Technical terms in original language
- [ ] No security vulnerabilities in code
- [ ] No secrets exposed
- [ ] Input validated for safety

---

## References

- OpenAI Prompt Engineering Guide
- Anthropic Safety Guidelines
- PromptingGuide.ai best practices
- HuggingFace multilingual LLM research
