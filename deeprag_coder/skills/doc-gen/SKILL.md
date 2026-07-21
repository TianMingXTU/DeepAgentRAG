---
name: doc-gen
description: >
  Generate documentation — docstrings, README, API docs, changelog — following
  project conventions. Supports Python/TS/JS/Go/Java/Rust.
  Triggers on phrases like "generate docs", "write docstring", "document this",
  "create README", "API docs", "add comments".
allowed-tools: Read Write
---

# Documentation Generation Skill

## Workflow

### Step 1: Read the Code
- Understand what the symbol/file does
- Check existing doc patterns in the project for consistency

### Step 2: Choose Template — read `references/templates.md`
- Python: Google-style docstring (Args / Returns / Raises)
- README: project name + description + install + usage + API

### Step 3: Generate
- For each public function/class: write or update docstring
- Include type annotations in docstring if project convention requires
- For README: generate sections based on project structure

### Step 4: Review
- Verify coverage: all public symbols documented
- Check for outdated or misleading comments
- Confirm no sensitive info in docs

## Output Format
```
## Documentation: <target>
Type: docstring/README/API
Content:
<generated documentation>
```
