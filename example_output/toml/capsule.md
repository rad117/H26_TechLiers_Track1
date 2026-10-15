# Dependency Exit Capsule: toml


Health score: 60/100 · Verdict: same · Gemma predicted: safe → actual: safe ✅

_"Safe" means the change installs and no test that passed before fails after it._

Target: https://github.com/rishrek/LinkWatch @ `f52f3930c8e7c33d934ccf614955a38e26984bd5`

## ✅ Verified (observed by depexit)

### Dependency details

- Status: **declared**
- `requirements.txt`: `toml==0.10.2`
- `pyproject.toml`: `toml==0.10.2`
- Pinned: 0.10.2 (released 2020-11-01) · Latest: 0.10.2 (released 2020-11-01)
- Requires Python: >=2.6, !=3.0.*, !=3.1.*, !=3.2.*

### Risk indicators

| Signal | Detail | Points | Source |
|---|---|---|---|
| `old_pin` | 0.10.2 released 2020-11-01 (5 years ago) | -20 | pypi |
| `inactive` | last release 2020-11-01, or marked Inactive | -20 | pypi |

### Usage locations

- `linkwatch/config.py:3`: `import toml`

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

The `toml` library is unmaintained and has not seen a release since 2020. Since the project uses Python 3.12, the dependency can be replaced with the built-in `tomllib` module from the standard library.

### Proposed replacement

- `tomllib (stdlib alternative)` (remove)
- requirements.txt: remove `toml==0.10.2`
- rewrites `linkwatch/config.py`
- Predicted: **safe** (confidence 1.0)

### Migration steps

1. Remove toml from requirements.txt and pyproject.toml
2. Replace 'import toml' with 'import tomllib' in linkwatch/config.py
3. Update load_settings in linkwatch/config.py to open the file in binary mode and use tomllib.load()

### Suggested tests

- Create a dummy sites.toml and run load_settings to verify successful parsing.

## ⚠ Open concerns and limitations

- 1 test(s) still fail after this change (may be unrelated to it).
- Only requirements.txt was changed; pyproject.toml still has the old spec.
- A passing test suite only proves the code paths the tests actually exercise.
