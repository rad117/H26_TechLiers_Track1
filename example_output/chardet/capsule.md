# Dependency Exit Capsule: chardet


Health score: 55/100 · Verdict: same · Gemma predicted: safe → actual: safe ✅

_"Safe" means the change installs and no test that passed before fails after it._

Target: https://github.com/rishrek/LinkWatch @ `f52f3930c8e7c33d934ccf614955a38e26984bd5`

## ✅ Verified (observed by depexit)

### Dependency details

- Status: **declared**
- `requirements.txt`: `chardet==5.2.0`
- `pyproject.toml`: `chardet==5.2.0`
- Pinned: 5.2.0 (released 2023-08-01) · Latest: 7.6.0 (released 2026-08-14)
- Requires Python: >=3.10

### Risk indicators

| Signal | Detail | Points | Source |
|---|---|---|---|
| `major_behind` | pinned 5.2.0, latest 7.6.0 | -25 | pypi |
| `old_pin` | 5.2.0 released 2023-08-01 (3 years ago) | -20 | pypi |

### Usage locations

- `linkwatch/encoding.py:4`: `import chardet`

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

The chardet dependency is significantly outdated, with the project pinned to version 5.2.0 while 7.6.0 is available. Additionally, chardet is largely superseded in the modern Python ecosystem by charset-normalizer, which provides better performance and accuracy.

### Proposed replacement

- `charset-normalizer>=3.0.0` (swap)
- requirements.txt: remove `chardet==5.2.0`
- requirements.txt: add `charset-normalizer>=3.0.0`
- rewrites `linkwatch/encoding.py`
- Predicted: **safe** (confidence 0.95)

### Migration steps

1. Remove chardet from requirements.txt and add charset-normalizer>=3.0.0.
2. Update pyproject.toml dependencies to replace chardet with charset-normalizer.
3. Update linkwatch/encoding.py to use charset_normalizer for character encoding detection.

### Suggested tests

- Verify that detect_encoding correctly identifies non-UTF-8 encodings like ISO-8859-1 using a sample response.

## ⚠ Open concerns and limitations

- 1 test(s) still fail after this change (may be unrelated to it).
- Only requirements.txt was changed; pyproject.toml still has the old spec.
- A passing test suite only proves the code paths the tests actually exercise.
