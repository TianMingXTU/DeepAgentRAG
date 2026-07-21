---
name: code-review
description: >
  Conduct code reviews focusing on correctness, security, performance, and
  maintainability. Use when users ask to review, audit, check code quality,
  or examine changes. Covers Python/TS/JS/Go/Java/Rust code.
  Triggers on phrases like "review this", "code review", "check my code",
  "audit", "is this correct", "find bugs".
allowed-tools: Read Bash(grep:*)
---

# Code Review Skill

## Workflow

### Step 1: Architecture & Correctness
- Check function/method has single responsibility
- Verify error handling: every external call wrapped in try/except
- Confirm return types match usage

### Step 2: Security — read `references/security.md`
- Run: `grep -rn "eval\|exec\|pickle.load" src/ --include="*.py" | grep -v test`
- Check for hardcoded secrets, SQL injection, shell injection

### Step 3: Performance
- Look for N+1 queries, unnecessary loops, missing caching
- Check large objects copied unnecessarily

### Step 4: Code Style — read `references/code-style.md`
- Verify imports follow project convention (stdlib → third-party → local)
- Check logging uses logger, not print
- Confirm type annotations on public functions

### Step 5: Documentation
- Public API has docstring
- Complex logic has inline comments
- Breaking changes documented

## Output Format
```
## Review: <file path>
Severity: high/medium/low
Line: <line numbers>
Issue: <description>
Suggestion: <fix recommendation>
```
