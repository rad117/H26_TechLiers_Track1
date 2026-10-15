# depexit: shared contract (read this first, everyone)

**Track 1 · Best Use of Gemma 4 · Dependency Resilience**

`depexit` is our tool. Point it at a repo and it:

1. finds risky dependencies;
2. shows where they're used;
3. asks Gemma 4 for a replacement plan;
4. **actually tests** that plan;
5. writes a **Dependency Exit Capsule**.

```powershell
python -m depexit analyze https://github.com/rishrek/LinkWatch --out capsule_out
```

## Who owns what

| Module | Owner | Job |
|---|---|---|
| `depexit/__main__.py` | **Sohan** (integration lead) | CLI + calls everything in order |
| `depexit/deps.py` | **Sohan** | Read `requirements.txt` + `pyproject.toml` |
| `depexit/scan.py` | **Sohan** | Find where each package is imported (AST) |
| `depexit/pypi.py` | **Sohan** | PyPI metadata, risk signals, health score |
| `depexit/gemma.py` | **Sohan** | Gemma 4 analysis (AI part) |
| `depexit/runner.py` | **Sheersh** | Make venvs, apply migrations, run pytest |
| `depexit/compare.py` | **Sheersh** | Before/after diff + "Gemma vs Reality" scorecard |
| `depexit/capsule.py` | **Radhesh** | Write capsule JSON / Markdown / HTML report / replay script |
| README, PPT, research | **Radhesh + Leena** | Docs, slides, fact-checking |

**Rule: only edit your own files.** If you need a change in someone else's module, ask them. Shared files (this file, `__main__.py`) are changed by Sohan only.

## The order things run in (`__main__.py`)

```
1. repo      = get_repo(target)                          # git clone into capsule_out/_work/target
2. baseline  = runner.run_tests(repo, "baseline", work)  # Sheersh: run the ORIGINAL repo's tests
3. records   = deps.collect(repo)                        # Sohan
4. records   = scan.attach_usages(records, repo, baseline["venv_python"])   # Sohan
5. records   = pypi.enrich_and_score(records, baseline)  # Sohan
6. for each record where at_risk == True:
     ai        = gemma.analyze(record, repo, out)        # Sohan   (🤖 AI)
     cand, diff = runner.apply_migration(repo, record, ai, work)   # Sheersh
     run       = runner.run_tests(cand, record["name"], work)      # Sheersh (✅ verified)
     cmp       = compare.compare(baseline, run, ai)      # Sheersh
7. card      = compare.scorecard(results)                # Sheersh
8. capsule.write_all(out, meta, records, results, baseline, card)  # Radhesh
```

## Data shapes (all plain dicts, JSON-serialisable)

### `DepRecord` (made by Sohan; everyone reads it)
```json
{
  "name": "Jinja2",
  "import_names": ["jinja2"],
  "status": "declared",                 // "declared" | "undeclared" (imported, not listed) | "unused" (listed, never imported)
  "specs": {"requirements.txt": "==2.11.3", "pyproject.toml": "==2.11.3"},
  "pinned_version": "2.11.3",           // null if not pinned with ==
  "spec_mismatch": false,               // true if requirements.txt and pyproject.toml disagree (e.g. pydantic)
  "usages": [
    {"file": "linkwatch/report.py", "line": 3, "code": "from jinja2 import Environment, FileSystemLoader, select_autoescape",
     "names": ["Environment", "FileSystemLoader", "select_autoescape"], "private": false}
  ],
  "pypi": {"latest": "3.1.6", "latest_date": "2025-03-05", "pinned_date": "2021-01-31", "inactive": false, "requires_python": ">=3.7"},
  "signals": [
    {"id": "major_behind", "detail": "pinned 2.x, latest 3.x", "points": -25, "source": "pypi"},
    {"id": "fails_in_baseline", "detail": "ImportError: cannot import name 'soft_unicode' from 'markupsafe'", "points": -30, "source": "baseline_tests"}
  ],
  "health_score": 45,                   // 100 + sum(points), clamped 0..100
  "at_risk": true                       // health_score < 70
}
```

### `AIResult` (made by Sohan's `gemma.analyze`; 🤖 everything in here is AI-suggested)
```json
{
  "source": "gemma", "model": "<exact Gemma 4 model id>", "ok": true,
  "risk_explanation": "…",
  "replacement": "Jinja2>=3.1",
  "migration_type": "bump",             // "bump" | "swap" | "remove"
  "requirement_changes": [{"action": "set", "name": "Jinja2", "line": "Jinja2>=3.1,<4"}],
                                        // action: "set" (replace line) | "remove" | "add"
  "file_edits": [{"path": "linkwatch/resources.py", "new_content": "<full new file text>"}],
  "steps": ["…", "…"],
  "suggested_tests": ["…"],
  "predicted_outcome": "pass",          // "pass" | "fail"  ← used by the scorecard; same definition as actual_outcome
  "confidence": 0.8,
  "raw": "<raw model text, for the evidence trail>"
}
```
If Gemma fails: `{"source": "gemma", "ok": false, "error": "…", "raw": "…"}`. Nobody may crash on that.

### `TestRun` (made by Sheersh's `runner.run_tests`; ✅ verified)
```json
{
  "label": "baseline",
  "stage": "tests",                     // furthest stage reached: "venv" | "install" | "tests"
  "ok": false,                          // true only if install worked AND all tests passed
  "python_version": "3.12.13",
  "venv_python": "…/.venv/Scripts/python.exe",
  "tests": 10, "passed": 9, "failed": 1, "errors": 0, "skipped": 0,
  "failing_tests": {"tests/test_report.py::test_report_renders_all_sites": "ImportError: cannot import name 'soft_unicode' from 'markupsafe'"},
  "warnings": ["linkwatch/resources.py:1: DeprecationWarning: pkg_resources is deprecated as an API"],
  "duration_s": 21.4,
  "commands": ["uv venv --python 3.12 .venv", "uv pip install -r requirements.txt pytest", "python -m pytest -q -W default --junitxml=junit.xml"],
  "log_file": "capsule_out/_work/logs/baseline.log"
}
```

### `Comparison` (made by Sheersh's `compare.compare`; ✅ verified)
```json
{
  "verdict": "improved",                // "improved" | "same" | "regressed" | "blocked" (install failed)
  "actual_outcome": "pass",             // "pass" if verdict is improved/same (installs, breaks no previously passing test), else "fail"
  "predicted_outcome": "pass",
  "prediction_correct": true,           // null if AI failed
  "newly_failing": [], "newly_passing": ["tests/test_report.py::test_report_renders_all_sites"], "still_failing": [],
  "new_warnings": [], "gone_warnings": [],
  "gaps": ["…human-readable compatibility gap…"]
}
```

### `DepResult` (one per at-risk dependency, assembled in `__main__.py`)
```json
{"dep": DepRecord, "ai": AIResult, "patch": "<unified diff text>", "run": TestRun, "comparison": Comparison}
```

### `Scorecard` (Sheersh)
```json
{"total": 6, "correct": 5, "accuracy": 0.83,
 "wrong": [{"dep": "pydantic", "predicted": "pass", "actual": "fail", "why": "3 tests failed: …"}]}
```

## Verified facts so far (ran 15 Oct, Python 3.12.13, original requirements.txt)
- Install works (11 s with `uv`). **Tests: 9 passed, 1 failed.**
- Failing: `tests/test_report.py::test_report_renders_all_sites`. The cause is `ImportError: cannot import name 'soft_unicode' from 'markupsafe'`: Jinja2 2.11.3 is broken by today's MarkupSafe.
- Warning: `linkwatch/resources.py:1: DeprecationWarning: pkg_resources is deprecated`.

## Team rules
- **Python 3.12** for everything (`uv python install 3.12`). LinkWatch doesn't run on 3.14.
- **Never commit the API key.** Put it in `$env:GEMINI_API_KEY` or `.env` (gitignored).
- **Commit small and often, with clear messages.** The judges check commit history from *every* member.
- `git pull --rebase` before every push.
- Hard checkpoints: **1:00** (lunch sync) · **2:15** (first end-to-end run) · **3:15** (feature freeze) · **4:00** (README/record) · **4:30** (submit).
