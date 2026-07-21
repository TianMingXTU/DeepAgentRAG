---
name: bug-hunt
description: >
  Systematic bug investigation using code search and common bug patterns.
  Use when users report errors, unexpected behavior, crashes, or incorrect
  results.
  Triggers on phrases like "find bug", "why is this broken", "debug this",
  "error", "crash", "unexpected behavior", "not working".
allowed-tools: Read Bash(grep:*)
---

# Bug Hunting Skill

## Workflow

### Step 1: Understand the Bug
- Ask what was expected vs what happened
- Get error message, stack trace, or reproduction steps

### Step 2: Locate — use `rag_search`
- Search for the error message or symptom in code
- Search for relevant function/file based on description

### Step 3: Inspect
- Read the suspicious code path
- Check inputs, state, error handling
- Look for common bug patterns — read `references/common-patterns.md`

### Step 4: Formulate Hypothesis
- "If X is wrong, then Y should happen"
- Write a minimal test to confirm

### Step 5: Fix & Verify
- Apply the minimal fix
- Confirm the reproduction case passes
- Check no regressions in related paths

## Output Format
```
## Bug Report: <symptom>
Root cause: <cause>
Location: <file:line>
Fix: <description>
```
