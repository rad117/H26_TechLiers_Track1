# Dependency Exit Capsule: urllib3


Health score: 45/100 · Verdict: same · Gemma predicted: safe → actual: safe ✅

_"Safe" means the change installs and no test that passed before fails after it._

Target: https://github.com/collinb9/understatAPI @ `d1252d9734e94ba98c681d2e41d467f1edb7aaf5`

## ✅ Verified (observed by depexit)

### Dependency details

- Status: **unused**
- `requirements.txt`: `urllib3==1.26.5`
- Pinned: 1.26.5 (released 2021-05-26) · Latest: 2.8.0 (released 2026-09-15)
- Requires Python: >=3.10

### Risk indicators

| Signal | Detail | Points | Source |
|---|---|---|---|
| `major_behind` | pinned 1.26.5, latest 2.8.0 | -25 | pypi |
| `old_pin` | 1.26.5 released 2021-05-26 (5 years ago) | -20 | pypi |
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

## 🤖 AI-suggested (Gemma 4 · gemma-4-26b-a4b-it; not verified unless confirmed by the tests above)

### Risk explanation

urllib3 is an outdated transitive dependency of requests that is not directly used by the application code. The current explicit pin to version 1.26.5 prevents the package manager from installing more recent, secure versions of urllib3 that are compatible with the installed version of requests.

### Proposed replacement

- `managed by requests` (remove)
- requirements.txt: remove `urllib3==1.26.5`
- Predicted: **safe** (confidence 1.0)

### Migration steps

1. Remove the explicit version pin for urllib3 from requirements.txt to allow the package manager to resolve the most recent compatible version via requests.

### Suggested tests

- Run the existing test suite to ensure that the requests library still functions correctly with the updated urllib3 version.
- [second opinion, residual risk medium] Run `pip show urllib3` in the target environment to confirm whether it resolved to a 2.x version
- [second opinion, residual risk medium] Execute integration tests using real HTTPS endpoints to verify SSL/TLS handshake success
- [second opinion, residual risk medium] Verify that the production platform's OpenSSL version meets the requirements for `urllib3` 2.x
- [second opinion, residual risk medium] Actual network I/O if the `requests` library is mocked within the existing test suite
- [second opinion, residual risk medium] Compatibility with `urllib3` 2.x breaking changes, specifically regarding stricter TLS/SSL and OpenSSL requirements
- [second opinion, residual risk medium] Low-level connection pooling and retry behavior changes resulting from the jump from `urllib3` 1.26.x to 2.x

## ⚠ Open concerns and limitations

- A passing test suite only proves the code paths the tests actually exercise.
