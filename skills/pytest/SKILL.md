---
name: pytest
description: >
  Run the project test suite and report results. Use before commits or
  after completing a feature to check for regressions.
context: fork
disable-model-invocation: true
allowed-tools: Bash(pytest*), Bash(uv run pytest*), Read
---

# Run Tests

Run the project test suite and report results back.

## Command

```bash
uv run pytest -v --durations=5 --timeout=180
```

## Reporting

After the test run, report back with:

1. **Summary** — total passed / failed / skipped / errors
2. **Slowest tests** — the 5 slowest tests from `--durations=5` output
3. **Failures** — for each failure, include:
   - Test name and file location
   - The assertion error or exception traceback
   - A brief explanation of what likely went wrong

If all tests pass, just report the summary and slowest tests.
