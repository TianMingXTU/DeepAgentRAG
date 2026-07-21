# Security Review Checklist

## Injection
- SQL queries use parameterized statements, not f-strings
- Shell commands use `subprocess.run([...])` with list args, not `shell=True`
- `eval()` / `exec()` / `pickle.load()` only on trusted input — flag all occurrences

## Secrets
- No hardcoded API keys, passwords, tokens in source
- No secrets in git history
- Environment variables read via config/settings.py, not `os.getenv()` inline

## Authentication & Authorization
- All API endpoints check auth
- Tokens have expiry and are validated
- No self-assigned roles without verification
