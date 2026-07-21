# Code Style Checklist

## Imports (Python)
- Standard library first, blank line, third-party, blank line, local
- One import per line (not `import os, sys`)

## Naming
- Classes: PascalCase
- Functions/variables: snake_case
- Constants: UPPER_SNAKE_CASE
- Private: underscore prefix

## Error Handling
- Use custom exception classes, not bare `raise Exception`
- Log exceptions with logger.exception() in except blocks
- Don't swallow exceptions silently
