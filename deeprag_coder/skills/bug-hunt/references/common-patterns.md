# Common Bug Patterns

## Python

### None / Null Reference
- Function returns `None` but caller doesn't check
- Fix: add `if result is not None:` guard or return a default

### Off-by-One
- Loop `for i in range(len(items)-1)` misses last element
- Fix: `range(len(items))` or `for item in items`

### Mutable Default Arguments
- `def foo(x=[])` — list is shared across calls
- Fix: `def foo(x=None): x = x or []`

### Exception Swallowing
- `try: ... except: pass` hides errors
- Fix: at minimum `logger.exception()`

### Race Condition
- Shared state modified from multiple threads without lock
- Fix: add threading.Lock or use thread-safe data structures

### Resource Leak
- File/db connection opened but not closed on error path
- Fix: use context managers (`with` statement)

## JavaScript / TypeScript

### Undefined Property Access
- Accessing `obj.prop` when `obj` may be undefined
- Fix: optional chaining `obj?.prop` or guard

### Async / Await Mismatch
- Calling async function without `await`
- Fix: add `await` or handle the returned Promise
