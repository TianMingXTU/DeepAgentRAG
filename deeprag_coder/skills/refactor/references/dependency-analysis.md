# Dependency Analysis Guide

## Static Analysis Checks

### Find All Callers
- For Python: `grep -rn "target_function(" --include="*.py" src/`
- For imports: `grep -rn "from module import target\|from module import.*target" --include="*.py" src/`

### Trace Through Re-exports
- Check `__init__.py` files for `from .submodule import X`
- A symbol may be re-exported — the caller imports from the parent

### Detect Dynamic References
- Flag `getattr(obj, name_string)` where name_string could match the target
- Flag `globals()[name]` / `locals()[name]`
- These cannot be statically resolved — must be checked manually
