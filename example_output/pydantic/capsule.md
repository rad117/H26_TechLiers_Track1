# Dependency Exit Capsule: pydantic


Health score: 40/100 · Verdict: same · Gemma predicted: safe → actual: safe ✅

_"Safe" means the change installs and no test that passed before fails after it._

Target: https://github.com/rishrek/LinkWatch @ `f52f3930c8e7c33d934ccf614955a38e26984bd5`

## ✅ Verified (observed by depexit)

### Dependency details

- Status: **declared**
- `requirements.txt`: `pydantic==1.10.13`
- `pyproject.toml`: `pydantic>=2`
- ⚠ requirements.txt and pyproject.toml **disagree**
- Pinned: 1.10.13 (released 2023-09-27) · Latest: 2.14.1 (released 2026-10-11)
- Requires Python: >=3.10

### Risk indicators

| Signal | Detail | Points | Source |
|---|---|---|---|
| `major_behind` | pinned 1.10.13, latest 2.14.1 | -25 | pypi |
| `old_pin` | 1.10.13 released 2023-09-27 (3 years ago) | -20 | pypi |
| `spec_mismatch` | requirements.txt: ==1.10.13, pyproject.toml: >=2 | -15 | repo_files |

### Usage locations

- `linkwatch/config.py:4`: `from pydantic import BaseModel, validator`

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

## 🤖 AI-suggested (Gemma 4 · gemma-4-26b-a4b-it; not verified unless confirmed by the tests above)

### Risk explanation

The project is using an outdated version of Pydantic (1.10.13) which conflicts with the requirement in pyproject.toml (>=2). Upgrading to Pydantic 2.x is necessary to resolve this mismatch and benefit from performance improvements, but it requires code changes due to breaking API changes in validators and configuration.

### Proposed replacement

- `pydantic>=2` (bump)
- requirements.txt: set `pydantic>=2`
- rewrites `linkwatch/config.py`
- Predicted: **safe** (confidence 0.95)

### Migration steps

1. Update pydantic version in requirements.txt to align with pyproject.toml
2. Refactor linkwatch/config.py to use Pydantic V2 field_validator and ConfigDict

### Suggested tests

- Run existing tests to ensure validation logic (empty names, invalid URLs) still works with the new Pydantic API.
- Verify that whitespace stripping on string fields is still active.

## ⚠ Open concerns and limitations

- 1 test(s) still fail after this change (may be unrelated to it).
- Only requirements.txt was changed; pyproject.toml still has the old spec.
- A passing test suite only proves the code paths the tests actually exercise.
