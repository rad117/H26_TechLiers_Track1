# Dependency Exit Capsule: appdirs


Health score: 60/100 · Verdict: same · Gemma predicted: safe → actual: safe ✅

_"Safe" means the change installs and no test that passed before fails after it._

Target: https://github.com/rishrek/LinkWatch @ `f52f3930c8e7c33d934ccf614955a38e26984bd5`

## ✅ Verified (observed by depexit)

### Dependency details

- Status: **declared**
- `requirements.txt`: `appdirs==1.4.4`
- `pyproject.toml`: `appdirs==1.4.4`
- Pinned: 1.4.4 (released 2020-05-11) · Latest: 1.4.4 (released 2020-05-11)
- Requires Python: not stated

### Risk indicators

| Signal | Detail | Points | Source |
|---|---|---|---|
| `old_pin` | 1.4.4 released 2020-05-11 (6 years ago) | -20 | pypi |
| `inactive` | last release 2020-05-11, or marked Inactive | -20 | pypi |

### Usage locations

- `linkwatch/cache.py:4`: `from appdirs import user_cache_dir`

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

appdirs is an inactive dependency that has not been updated since 2020. Replacing it with platformdirs provides a modern, actively maintained alternative for retrieving platform-specific directory paths.

### Proposed replacement

- `platformdirs` (swap)
- requirements.txt: remove `appdirs==1.4.4`
- requirements.txt: add `platformdirs`
- rewrites `linkwatch/cache.py`
- Predicted: **safe** (confidence 1.0)

### Migration steps

1. Remove appdirs from requirements.txt and pyproject.toml
2. Add platformdirs to requirements.txt and pyproject.toml
3. Update the import in linkwatch/cache.py from appdirs to platformdirs

### Suggested tests

- Run the application and verify that the cache directory is created in the expected OS-specific location.

## ⚠ Open concerns and limitations

- 1 test(s) still fail after this change (may be unrelated to it).
- Only requirements.txt was changed; pyproject.toml still has the old spec.
- A passing test suite only proves the code paths the tests actually exercise.
