# Sohan: Facts Engine + Gemma + Integration lead

> Read `team/CONTRACT.md` first (5 min). It has the exact dict shapes your code must return.

## Your job in one line
Find **every dependency**, **where it's used** and **how risky it is** (all ✅ verified facts). Then ask **Gemma 4** what to do about each risky one (🤖 AI), and make sure `python -m depexit analyze …` runs from start to finish.

## Your files
`depexit/deps.py` · `depexit/scan.py` · `depexit/pypi.py` · `depexit/gemma.py` · `depexit/__main__.py` (already wired; you own it)

## Setup (10 min)
```powershell
git clone https://github.com/rad117/LinkWatch.git ; cd LinkWatch
uv python install 3.12                 # no uv? -> powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
uv venv --python 3.12 .venv ; .venv\Scripts\activate
uv pip install -r depexit/requirements.txt
$env:GEMINI_API_KEY = "<key>"          # never commit
python -c "from google import genai; [print(m.name) for m in genai.Client().models.list() if 'gemma' in m.name]"
$env:GEMMA_MODEL = "<the gemma-4 id printed above>"
```
Test your modules against a plain clone of the original repo: `git clone https://github.com/rishrek/LinkWatch ..\target`.

---

## Task 1 · `deps.collect(repo)`: read the declared dependencies (12:15 → 12:40)
- Parse `requirements.txt`: skip blanks and `#` comments (note `# PyYAML==5.1` is commented out, so ignore it). Split `name`, operator, version.
- Parse `pyproject.toml` `[project] dependencies` with **`tomllib`** (stdlib in 3.11+; open the file in `"rb"` mode).
- Merge both by **normalised name** (lowercase, `_`/`.` → `-`).
- Set `spec_mismatch: true` when the two files disagree. **pydantic** is `==1.10.13` vs `>=2`, which is a real finding.
- `pinned_version` is set only for `==` pins.

**Done when:** `collect()` returns 12 records, pydantic has `spec_mismatch: true`, and `click`/`six`/`rich`/`python-dateutil` have `pinned_version: null`.

## Task 2 · `scan.attach_usages(records, repo, venv_python)`: where is each one used? (12:40 → 1:00)
- Walk every `.py` file (skip `.venv`, `tests/` is fine to include but tag it) with `ast.parse`, collecting `Import` and `ImportFrom` (only `level == 0`, which skips relative imports like `from .dates import`).
- Ignore stdlib (`sys.stdlib_module_names`) and the project's own package (`linkwatch`).
- **Package → import name:** if `venv_python` is given, run
  `[venv_python, "-c", "import importlib.metadata as m, json; print(json.dumps(m.packages_distributions()))"]`
  and invert it. Fallback: lowercase name with `-` → `_`, plus `{"python-dateutil": "dateutil"}`.
- Each usage gets `file`, `line`, `code` (the source line), `names` (imported names), and `private` (any name starting with `_`).
- Mark records with no usages as `status: "unused"` (expect **six**). Add new records with `status: "undeclared"` for imported-but-not-declared packages (expect **certifi**, imported in `checker.py`).
- Bonus: also flag `pkg_resources` (it comes from **setuptools**) and attach it to the setuptools record.

**Done when:** jinja2 → `linkwatch/report.py:3` · dateutil → `linkwatch/dates.py` · certifi = undeclared · six = unused · `requests.utils._parse_content_type_header` has `private: true`.

## 🍽 1:00 – 1:30 Lunch. At 1:25, show the team Tasks 1–2 printing.

## Task 3 · `pypi.enrich_and_score(records, baseline)`: risk score (1:30 → 2:00)
- `GET https://pypi.org/pypi/<name>/json` (timeout 10 s; cache results in a dict). Fill `latest`, `latest_date`, `pinned_date` (from `releases[pinned][0]["upload_time"]`), `inactive` (any classifier containing "Inactive"), `requires_python`.
- Add signals. Every one must say where it came from (`source`):

| id | rule | points |
|---|---|---|
| `fails_in_baseline` | a baseline failure message mentions this package's import name (e.g. `markupsafe`/`jinja2`) | −30 |
| `major_behind` | major(pinned) < major(latest) | −25 |
| `old_pin` | pinned release older than 3 years | −20 |
| `inactive` | no release in 2+ years, or "Inactive" classifier | −20 |
| `deprecation_warning` | a baseline warning mentions it (`pkg_resources` → setuptools) | −15 |
| `spec_mismatch` | requirements vs pyproject disagree | −15 |
| `private_api` | any usage with `private: true` | −10 |
| `undeclared` / `unused` | from Task 2 | −10 |
| `unpinned` | no version constraint at all | −5 |

- `health_score = clamp(100 + sum(points), 0, 100)` and `at_risk = health_score < 70`.

**Done when:** Jinja2, pydantic, setuptools, appdirs, toml and idna are `at_risk`. The rules and points are explained in a comment at the top of the file, so the judges can read them.

## Task 4 · `gemma.analyze(record, repo, out)`: the AI part (2:00 → 2:45)
- Send Gemma the **verified facts** (the record as JSON) **plus the full text of each file in `usages`** (they're tiny). Ask for **only JSON** in the exact `AIResult` shape from CONTRACT.md. Tell it:
  - `migration_type`: `bump` (version change only), `swap` (different library, so give `file_edits` with the **complete** new file), or `remove`.
  - `requirement_changes` use `requirements.txt` syntax.
  - `predicted_outcome` = will LinkWatch's tests pass after this change? (`pass`/`fail`)
- Parse it robustly: strip ```` ```json ```` fences, `json.loads`, and retry once on failure. Never raise: return `{"ok": false, "error": …, "raw": …}`.
- Cache to `out/ai/<name>.json`. If the cache exists, reuse it (this saves rate limit and makes the demo fast).
- Put `model_name()` and `raw` in every result.

**Done when:** `gemma.analyze` on the Jinja2 record returns a `bump` to Jinja2 3.x, and on appdirs returns a `swap` to platformdirs with an edited `linkwatch/cache.py`.

## Task 5 · Integration (2:45 → 3:15, then on call until 4:30)
- At **2:15**, run `python -m depexit analyze https://github.com/rishrek/LinkWatch --no-ai --no-tests` (works once your 3 modules are done).
- At **2:45**, do a full run with `--max-deps 3`. Fix glue bugs in `__main__.py`, and tell Sheersh/Radhesh the exact error if it's in their module.
- **3:15 feature freeze.** After this, only bug fixes.

## Your deliverables (tick them off)
- [ ] `deps.py`, `scan.py`, `pypi.py`, `gemma.py` return the CONTRACT shapes
- [ ] Risk rules documented at the top of `pypi.py`
- [ ] Gemma answers cached in `capsule_out/ai/`
- [ ] End-to-end command works on the real URL
- [ ] At least 6 commits from you
- [ ] Give Radhesh 3 lines for the README: model id, how the prompt works, what Gemma is and isn't trusted for

## Paste this into Claude Code to start
> Read team/CONTRACT.md and team/SOHAN.md. Implement Task 1 in depexit/deps.py exactly to the DepRecord shape, then test it against a clone of https://github.com/rishrek/LinkWatch and show me the output. Keep the code short and readable. I must be able to explain every line to judges.

⚠ The rules say AI-generated code must be verified and "heavy use of AI must be avoided." Read and understand what Claude writes; the judges may ask you.
