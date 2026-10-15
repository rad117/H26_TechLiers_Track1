# Dependency Exit Capsule: Jinja2


Health score: 25/100 · Verdict: improved · Gemma predicted: safe → actual: safe ✅

_"Safe" means the change installs and no test that passed before fails after it._

Target: https://github.com/rishrek/LinkWatch @ `f52f3930c8e7c33d934ccf614955a38e26984bd5`

## ✅ Verified (observed by depexit)

### Dependency details

- Status: **declared**
- `requirements.txt`: `Jinja2==2.11.3`
- `pyproject.toml`: `Jinja2==2.11.3`
- Pinned: 2.11.3 (released 2021-01-31) · Latest: 3.1.6 (released 2025-03-05)
- Requires Python: >=3.7

### Risk indicators

| Signal | Detail | Points | Source |
|---|---|---|---|
| `fails_in_baseline` | ImportError: cannot import name 'soft_unicode' from 'markupsafe' (.venv\Lib\site-packages\markupsafe\__init__.py) | -30 | baseline_tests |
| `major_behind` | pinned 2.11.3, latest 3.1.6 | -25 | pypi |
| `old_pin` | 2.11.3 released 2021-01-31 (5 years ago) | -20 | pypi |

### Usage locations

- `linkwatch/report.py:3`: `from jinja2 import Environment, FileSystemLoader, select_autoescape`

### Executed test results

| Run | Stage | OK | Passed | Failed | Errors |
|---|---|---|---|---|---|
| Baseline (original deps) | tests | ❌ | 9 | 1 | 0 |
| After migration | tests | ✅ | 10 | 0 | 0 |

- Newly passing: `tests/test_report.py::test_report_renders_all_sites`

Commands run (see replay.ps1):

    py -3.12 -m venv --clear .venv
    .venv\Scripts\python.exe -m pip install -r requirements.txt pytest
    .venv\Scripts\python.exe -m pytest -q -W default -p no:cacheprovider --junitxml=junit.xml

### Compatibility gaps

None observed.

## 🤖 AI-suggested (Gemma 4 · gemma-4-26b-a4b-it; not verified unless confirmed by the tests above)

### Risk explanation

Jinja2 2.11.3 is incompatible with modern versions of MarkupSafe, leading to an ImportError when attempting to import 'soft_unicode'. Upgrading to Jinja2 3.x resolves this conflict and maintains compatibility with current dependencies.

### Proposed replacement

- `Jinja2>=3.1.0` (bump)
- requirements.txt: set `Jinja2==3.1.6`
- Predicted: **safe** (confidence 1.0)

### Migration steps

1. Update Jinja2 from 2.11.3 to 3.1.6 in requirements.txt to resolve MarkupSafe incompatibility.

### Suggested tests

- pytest

## ⚠ Open concerns and limitations

- Only requirements.txt was changed; pyproject.toml still has the old spec.
- A passing test suite only proves the code paths the tests actually exercise.
