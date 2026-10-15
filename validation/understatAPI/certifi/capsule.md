# Dependency Exit Capsule: certifi


Health score: 65/100 · Verdict: same · Gemma predicted: safe → actual: safe ✅

_"Safe" means the change installs and no test that passed before fails after it._

Target: https://github.com/collinb9/understatAPI @ `d1252d9734e94ba98c681d2e41d467f1edb7aaf5`

## ✅ Verified (observed by depexit)

### Dependency details

- Status: **unused**
- `requirements.txt`: `certifi==2025.11.12`
- Pinned: 2025.11.12 (released 2025-11-12) · Latest: 2026.7.22 (released 2026-07-22)
- Requires Python: >=3.7

### Risk indicators

| Signal | Detail | Points | Source |
|---|---|---|---|
| `major_behind` | pinned 2025.11.12, latest 2026.7.22 | -25 | pypi |
| `unused` | declared but never imported | -10 | code_scan |

### Usage locations

Not imported anywhere.

### Executed test results

| Run | Stage | OK | Passed | Failed | Errors |
|---|---|---|---|---|---|
| Baseline (original deps) | tests | ✅ | 2042 | 0 | 0 |
| After migration | tests | ✅ | 2042 | 0 | 0 |


Commands run (see replay.ps1):

    py -3.12 -m venv --clear .venv
    .venv\Scripts\python.exe -m pip install -r requirements.txt pytest
    .venv\Scripts\python.exe -m pytest -q -W default -p no:cacheprovider --junitxml=junit.xml

### Compatibility gaps

None observed.

## 🤖 AI-suggested (Gemma 4 · gemma-4-31b-it; not verified unless confirmed by the tests above)

### Risk explanation

The certifi package is pinned to an outdated version and is not directly imported or used by the project's source code. It exists in the requirements file only as a transitive dependency of the requests library.

### Proposed replacement

- `None` (remove)
- requirements.txt: remove `certifi`
- Predicted: **safe** (confidence 1.0)

### Migration steps

1. Remove the explicit version pin for certifi from requirements.txt. This allows the requests library to resolve the most appropriate version of its own dependency.

### Suggested tests

- Run pytest to ensure that network-dependent tests still pass with the updated version of certifi.

## ⚠ Open concerns and limitations

- A passing test suite only proves the code paths the tests actually exercise.
