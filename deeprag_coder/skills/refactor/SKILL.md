---
name: refactor
description: >
  Guide safe cross-file refactoring with dependency analysis. Use when users
  ask to rename, move, extract, restructure code, or change APIs.
  Triggers on phrases like "refactor this", "rename function", "extract method",
  "move module", "restructure", "change signature", "clean up code".
allowed-tools: Read Write Bash(grep:*)
---

# Refactor Skill

## Workflow

### Step 1: Understand the Scope
- Read the files involved
- Identify the symbol/API to change

### Step 2: Trace Dependencies — run `graph_query`
- Find all callers and importers of the target symbol
- Trace indirect call chains (depth 2-3)
- Check for dynamic references (`getattr`, `__import__`, string imports)

### Step 3: Plan — write a todo list
- Break the refactor into atomic steps
- Order: leaf dependencies → dependents
- Mark breaking changes

### Step 4: Execute Changes
- One file at a time
- After each change, verify imports still resolve
- Use `rag_search` to find any missed references

### Step 5: Verify
- Run tests (if available): `uv run pytest` or language-specific test command
- Check for dead imports after rename/move
- Confirm public API surface is preserved or documented as breaking

## Output Format
```
## Refactor Plan: <target>
Files affected: <list>
Steps: <numbered>
Breaking changes: <yes/no>
```
