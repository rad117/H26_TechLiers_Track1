# Dependency Exit Capsule: setuptools


Health score: 60/100 · Verdict: improved · Gemma predicted: safe → actual: safe ✅

_"Safe" means the change installs and no test that passed before fails after it._

Target: https://github.com/rishrek/LinkWatch @ `f52f3930c8e7c33d934ccf614955a38e26984bd5`

## ✅ Verified (observed by depexit)

### Dependency details

- Status: **declared**
- `requirements.txt`: `setuptools==75.8.0`
- `pyproject.toml`: `setuptools==75.8.0`
- Pinned: 75.8.0 (released 2025-01-08) · Latest: 84.0.0 (released 2026-08-08)
- Requires Python: >=3.10

### Risk indicators

| Signal | Detail | Points | Source |
|---|---|---|---|
| `deprecation_warning` | linkwatch\resources.py:1: DeprecationWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html | -15 | baseline_tests |
| `major_behind` | pinned 75.8.0, latest 84.0.0 | -25 | pypi |

### Usage locations

- `linkwatch/resources.py:1`: `import pkg_resources`

### Executed test results

| Run | Stage | OK | Passed | Failed | Errors |
|---|---|---|---|---|---|
| Baseline (original deps) | tests | ❌ | 9 | 1 | 0 |
| After migration | tests | ❌ | 9 | 1 | 0 |

- Still failing: `tests/test_report.py::test_report_renders_all_sites`
- Warnings gone: `linkwatch\resources.py:1: DeprecationWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html`

Commands run (see replay.ps1):

    py -3.12 -m venv --clear .venv
    .venv\Scripts\python.exe -m pip install -r requirements.txt pytest
    .venv\Scripts\python.exe -m pytest -q -W default -p no:cacheprovider --junitxml=junit.xml

### Compatibility gaps

None observed.

## 🤖 AI-suggested (Gemma 4 · gemma-4-31b-it; not verified unless confirmed by the tests above)

### Risk explanation

The 'pkg_resources' module from 'setuptools' is deprecated. The 'importlib.resources' module in the standard library is the modern, recommended alternative for accessing package resources in Python 3.9+.

### Proposed replacement

- `importlib.resources (stdlib)` (remove)
- requirements.txt: remove `setuptools`
- rewrites `linkwatch/resources.py`
- Predicted: **safe** (confidence 1.0)

### Migration steps

1. Remove setuptools from requirements.txt and pyproject.toml dependencies
2. Replace pkg_resources.resource_filename with importlib.resources.files in linkwatch/resources.py

### Suggested tests

- Verify that the application can still locate and load the status.html.j2 template

## ⚠ Open concerns and limitations

- 1 test(s) still fail after this change (may be unrelated to it).
- Only requirements.txt was changed; pyproject.toml still has the old spec.
- A passing test suite only proves the code paths the tests actually exercise.
