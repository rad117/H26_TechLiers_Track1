# Sheersh: Proof Engine (tests, before vs after, Gemma vs Reality)

> Read `team/CONTRACT.md` first (5 min). It has the exact dict shapes your code must return.

## Your job in one line
**Prove things.** Run the target repo's real test suite with the original dependencies, then again after applying Gemma's suggested change. Compare the two, and grade whether Gemma's prediction was right. Everything you produce is ✅ **verified evidence**, and that's what wins judging criterion 4.

## Your files
`depexit/runner.py` · `depexit/compare.py`

## Setup (10 min)
```powershell
git clone https://github.com/rad117/LinkWatch.git ; cd LinkWatch
uv python install 3.12                 # no uv? -> powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
uv venv --python 3.12 .venv ; .venv\Scripts\activate
uv pip install -r depexit/requirements.txt
git clone https://github.com/rishrek/LinkWatch ..\target     # a clean copy to test against
```

## What we already know (verified, 15 Oct, Python 3.12.13)
Running the original repo: **install OK (11 s with uv) → 10 tests: 9 passed, 1 failed.**
- Failed: `tests/test_report.py::test_report_renders_all_sites` with `ImportError: cannot import name 'soft_unicode' from 'markupsafe'` (old Jinja2 2.11.3).
- Warning: `linkwatch/resources.py:1: DeprecationWarning: pkg_resources is deprecated`.

Your baseline run must reproduce exactly this.

---

## Task 1 · `runner.run_tests(repo_dir, label, work)` (12:15 → 1:00)
Steps:
1. `uv venv --python 3.12 <repo_dir>/.venv`. If `uv` isn't on PATH, fall back to `py -3.12 -m venv`.
2. `uv pip install --python <venv python> -r requirements.txt pytest`. **Not** `requirements-dev.txt`, because it contains `nose`.
3. `<venv python> -m pytest -q -W default -p no:cacheprovider --junitxml=junit.xml`, with `cwd=repo_dir` and `timeout=300`.

Then:
- Parse `junit.xml` with `xml.etree.ElementTree`. Get tests/failures/errors/skipped from the `<testsuite>` attributes. For each `<testcase>` with a `<failure>` or `<error>` child, store `"<file>::<name>": <first line of its message>`.
- Get the warnings from pytest's stdout (the lines under `warnings summary`).
- **If install fails, that's a result, not a crash:** return `stage: "install", ok: false` with the last ~40 lines of the error.
- Save the full stdout+stderr of each step to `work/logs/<label>.log`. Record every command string in `commands` (Radhesh turns these into `replay.ps1`).
- Use `subprocess.run([...], capture_output=True, text=True)` with argument **lists**, never `shell=True`.

**Done when:** `run_tests(Path('..\\target'), 'baseline', Path('work'))` returns `passed: 9, failed: 1` with the soft_unicode message and the pkg_resources warning.

## 🍽 1:00 – 1:30 Lunch. At 1:25, show the team the baseline TestRun printing.

## Task 2 · `runner.apply_migration(repo, record, ai, work)` (1:30 → 2:15)
1. Copy `repo` to `work/candidates/<name>` (`shutil.copytree`, ignoring `.venv`, `__pycache__`, `junit.xml`).
2. Apply `ai["requirement_changes"]` to `requirements.txt`:
   - `set` replaces the line whose normalised package name matches;
   - `remove` deletes it;
   - `add` appends.
3. Apply `ai["file_edits"]`: overwrite each file with `new_content`. **Safety: reject any path that resolves outside the candidate folder** (`(cand / path).resolve()` must be inside `cand.resolve()`). It's AI output, so don't trust it blindly.
4. Build a unified diff of every changed file with `difflib.unified_diff` (`a/<path>` → `b/<path>`). Return `(candidate_path, diff_text)`.

**Done when:** a fake AI dict `{"requirement_changes":[{"action":"set","name":"Jinja2","line":"Jinja2>=3.1,<4"}],"file_edits":[]}` produces a candidate whose tests show **10 passed** and a 1-line diff. That's your first **"improved"** result.

## Task 3 · `compare.compare(baseline, run, ai)` (2:15 → 2:40)
- `newly_failing` = failing in run but not in baseline. `newly_passing` = the reverse. `still_failing` = both.
- `new_warnings` / `gone_warnings` = set difference of the warning lines.
- `verdict`:
  - `"blocked"` if the run never got past install;
  - `"regressed"` if anything is newly failing;
  - `"improved"` if something is newly passing (or a warning disappeared) and nothing regressed;
  - `"same"` otherwise.
- `actual_outcome` = `"pass"` if `run["ok"]` else `"fail"`. `prediction_correct` = `ai["predicted_outcome"] == actual_outcome` (`None` if the AI failed).
- `gaps`: one plain-English line per newly failing test, plus one for a blocked install. For example: `"tests/test_config.py::test_x now fails: TypeError …"`.

## Task 4 · `compare.scorecard(results)` (2:40 → 2:55)
Over the results that have a comparison: `total`, `correct`, `accuracy` (2 decimals), and `wrong` = a list of `{dep, predicted, actual, why}`, where `why` is the first gap.
This is our **"Gemma vs Reality"** headline: *"Gemma was right on 5/6 migrations."*

## Task 5 · Demo support (2:55 → 4:30)
- At **3:00**, run the full pipeline with Sohan. Watch for slow installs; `uv` keeps them around 10–20 s each.
- Find the **best demo story**: one dependency that's "improved" (Jinja2), and one where Gemma was **wrong** or something regressed. That honesty impresses judges.
- Write the README's **"How we verify"** section (5–8 lines) and send it to Radhesh.

## Your deliverables (tick them off)
- [ ] `run_tests` reproduces the baseline (9 passed / 1 failed) and never crashes on install errors
- [ ] `apply_migration` with path-safety check + unified diff
- [ ] `compare` + `scorecard` match the CONTRACT shapes
- [ ] Logs in `work/logs/`, commands recorded for `replay.ps1`
- [ ] At least 6 commits from you
- [ ] "How we verify" paragraph for the README

## Paste this into Claude Code to start
> Read team/CONTRACT.md and team/SHEERSH.md. Implement Task 1 (runner.run_tests) using uv with a py -3.12 fallback, parse junit.xml, and run it against ..\target to show it reproduces 9 passed / 1 failed. Keep the code short and readable. I must be able to explain every line to judges.

⚠ The rules say AI-generated code must be verified and "heavy use of AI must be avoided." Read and understand what Claude writes; the judges may ask you.
