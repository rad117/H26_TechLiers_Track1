# Dependency Exit Capsule: idna


Health score: 45/100 · Verdict: same · Gemma predicted: safe → actual: safe ✅

_"Safe" means the change installs and no test that passed before fails after it._

Target: https://github.com/rishrek/LinkWatch @ `f52f3930c8e7c33d934ccf614955a38e26984bd5`

## ✅ Verified (observed by depexit)

### Dependency details

- Status: **unused**
- `requirements.txt`: `idna==2.7`
- `pyproject.toml`: `idna==2.7`
- Pinned: 2.7 (released 2018-06-11) · Latest: 3.20 (released 2026-09-17)
- Requires Python: >=3.9

### Risk indicators

| Signal | Detail | Points | Source |
|---|---|---|---|
| `major_behind` | pinned 2.7, latest 3.20 | -25 | pypi |
| `old_pin` | 2.7 released 2018-06-11 (8 years ago) | -20 | pypi |
| `unused` | declared but never imported | -10 | code_scan |

### Usage locations

Not imported anywhere.

### Executed test results

| Run | Stage | OK | Passed | Failed | Errors |
|---|---|---|---|---|---|
| Baseline (original deps) | tests | ❌ | 9 | 1 | 0 |
| After migration | tests | ❌ | 9 | 1 | 0 |

- Still failing: `tests/test_report.py::test_report_renders_all_sites`

Commands run (see replay.ps1):

    py -3.12 -m venv --clear .venv
    .venv\Scripts\python.exe -m pip install -r requirements.txt pytest
    .venv\Scripts\python.exe -m pytest -q -W default -p no:cacheprovider --junitxml=junit.xml

### Compatibility gaps

None observed.

## 🤖 AI-suggested (Gemma 4 · gemma-4-31b-it; not verified unless confirmed by the tests above)

### Risk explanation

The idna dependency is pinned to an extremely old version (2.7 from 2018) and is declared as unused in the project's source code.

### Proposed replacement

- `None` (remove)
- requirements.txt: remove `idna`
- Predicted: **safe** (confidence 1.0)

### Migration steps

1. Remove idna==2.7 from requirements.txt
2. Remove idna==2.7 from the dependencies list in pyproject.toml

### Suggested tests

- Run pytest to ensure no hidden dependencies on idna exist

## ⚠ Open concerns and limitations

- 1 test(s) still fail after this change (may be unrelated to it).
- Only requirements.txt was changed; pyproject.toml still has the old spec.
- A passing test suite only proves the code paths the tests actually exercise.
