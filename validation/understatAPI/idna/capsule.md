# Dependency Exit Capsule: idna


Health score: 45/100 · Verdict: same · Gemma predicted: safe → actual: safe ✅

_"Safe" means the change installs and no test that passed before fails after it._

Target: https://github.com/collinb9/understatAPI @ `d1252d9734e94ba98c681d2e41d467f1edb7aaf5`

## ✅ Verified (observed by depexit)

### Dependency details

- Status: **unused**
- `requirements.txt`: `idna==2.10`
- Pinned: 2.10 (released 2020-06-27) · Latest: 3.20 (released 2026-09-17)
- Requires Python: >=3.9

### Risk indicators

| Signal | Detail | Points | Source |
|---|---|---|---|
| `major_behind` | pinned 2.10, latest 3.20 | -25 | pypi |
| `old_pin` | 2.10 released 2020-06-27 (6 years ago) | -20 | pypi |
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

The project is pinned to idna 2.10, which was released over six years ago and is significantly behind the latest version 3.20. The package is not directly imported in the project's source code and is only present as a transitive dependency of requests. Removing the pin allows the package manager to resolve a modern, secure version compatible with requests.

### Proposed replacement

- `None (transitive dependency of requests)` (remove)
- requirements.txt: remove `idna`
- Predicted: **safe** (confidence 1.0)

### Migration steps

1. Remove the idna==2.10 pin from requirements.txt to allow requests to use a current, compatible version of the library.

### Suggested tests

- Run pytest to ensure that requests continues to function correctly with the updated version of idna.
- [second opinion, residual risk medium] Verify the version of idna installed using `pip show idna` to ensure it's not a major version bump (e.g., 3.x) causing issues
- [second opinion, residual risk medium] Manually test `requests.get()` with an internationalized domain like 'http://exämple.com'
- [second opinion, residual risk medium] Check for `TypeError` or `UnicodeError` when passing Unicode hostnames to `requests`
- [second opinion, residual risk medium] Requests to URLs containing non-ASCII/Unicode domain names
- [second opinion, residual risk medium] Punycode encoding and decoding edge cases for specific scripts
- [second opinion, residual risk medium] Breaking changes in the idna 3.x API compared to the previous 2.10 version

## ⚠ Open concerns and limitations

- A passing test suite only proves the code paths the tests actually exercise.
