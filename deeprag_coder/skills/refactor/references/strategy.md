# Refactoring Strategies

## Rename Symbol
- Search all references: `grep -rn "old_name" --include="*.py" src/`
- Rename definition first, then all usages
- If the name appears in strings/commments, flag for manual review

## Extract Method / Function
- Identify code block with single responsibility
- Check for shared local variables → pass as parameters
- Name the new function based on what the block does
- Replace original block with call

## Move Module / File
- Update all import statements referencing the old path
- For Python: relative imports may break — change to absolute
- Fallback: keep a re-export alias at old location with deprecation warning

## Change Signature
- Add new parameters with defaults first (backward compatible)
- Remove old parameters after updating all callers
- Use `*args, **kwargs` forwarding if the change spans many callers

## Extract Class
- Group related methods and state into a new class
- Update type annotations in callers
