# depexit: team status

**Last updated:** 15 Oct, 13:21, by Radhesh. Update your own row when something changes.

## End goal

One command:

```powershell
python -m depexit analyze https://github.com/rishrek/LinkWatch --out capsule_out
```

…finds LinkWatch's risky dependencies, asks Gemma 4 for a fix for each one, **applies that fix in a copy of the
repo and runs the real tests**, then writes a Dependency Exit Capsule. The judges open `capsule_out/report.html`
and see, in 5 seconds:

> **"Gemma was right about X of Y migrations."** For each dependency: what Gemma predicted, and what the tests
> actually showed.

That honesty (AI claims shown separately from tested evidence) is our pitch. Everything below serves it.

## Where each piece is

| Piece | Owner | Status | Notes |
|---|---|---|---|
| `deps.py`: read requirements.txt and pyproject.toml | Sohan | ✅ pushed | |
| `scan.py`: find imports | Sohan | ✅ pushed | |
| `pypi.py`: health score | Sohan | ✅ pushed | |
| `gemma.py`: Gemma 4 analysis | Sohan | ✅ pushed | Has a model fallback, so the report must show which model actually answered (Radhesh is on it) |
| `runner.py`: `run_tests` and `apply_migration` | Sheersh | ✅ pushed | Commands are recorded relative to the repo, so `replay.ps1` works on any machine 👍 |
| `compare.py`: `compare` and `scorecard` | Sheersh | ⛔ **not started (stub)** | **Blocks every end-to-end run**: `__main__.py` always calls `scorecard()` |
| `capsule.py`: capsule files and `replay.ps1` | Radhesh | ✅ pushed, 7 tests passing | |
| `report.html`: Blast Radius page | Radhesh | ✅ ledger, test grid, table, drawer | Next: blast radius graph, `badge.svg` |
| README (7 sections) | Radhesh + Leena | ⏳ starts 3:00 | Needs inputs, see below |
| `docs/model.md`, `docs/references.md`, slides | Leena | ❓ unknown | Leena, please update this row |

## Verified integration check (13:15)

Radhesh ran Sohan's real `deps` → `scan` → `pypi` on a fresh clone of rishrek/LinkWatch and passed the result into
`capsule.write_all`. **It worked with no errors.** This ran without the baseline tests and without Gemma, so the scores
below are missing the `fails_in_baseline` and `deprecation_warning` penalties.

| At risk (health < 70) | Health |
|---|---|
| pydantic | 40 |
| idna | 45 |
| Jinja2 | 55 (drops to 25 once the baseline failure counts) |
| chardet | 55 |
| toml | 60 |
| appdirs | 60 |
| setuptools | 75 now, should drop to 60 with the `pkg_resources` warning from the baseline |

That's **about 7 migrations**, roughly 20 s of tests each plus the Gemma calls. Use `--max-deps 3` for fast test runs.
`chardet` wasn't on our original list. Sohan, check whether that's intended.

## What we need, from whom

- **Sheersh:** `compare.py`, as soon as possible. It's the only thing between us and the 2:15 end-to-end run. Then
  send Radhesh the **"How we verify"** paragraph (5–8 lines) for the README.
- **Sohan:** send Radhesh **3 lines** for the README: the exact model id, how the prompt works, and what Gemma is
  and isn't trusted for. Run the first end-to-end at 2:15 once `compare.py` lands.
- **Leena:** `docs/model.md` (model id, version, licence link, release date) and `docs/references.md` (official
  migration sources). Did the organisers answer the "free Gemini API tier" question? Please post the answer here.
- **Radhesh:** blast radius graph, show the actual model per dependency in the report, `badge.svg`, then the README
  from 3:00.

## See the report right now (sample data, not a real run)

```powershell
.venv\Scripts\python.exe -m depexit.capsule team/sample_data/results.sample.json capsule_dev
start capsule_dev\report.html
```

A red banner marks it as sample data. **Never screenshot or demo this one.** The demo uses a real run.

## Checkpoints

| Time | Checkpoint | State |
|---|---|---|
| 1:00 | Lunch sync | ✅ |
| **2:15** | **First end-to-end run** (`--no-ai --no-tests`, then a full run with `--max-deps 3`) | waiting on `compare.py` |
| 3:15 | Feature freeze: bug fixes only after this | |
| 3:45 | Screen-record the full run and the report | |
| 4:00 | README done, real run committed to `example_output/` | |
| 4:15 | Final checks: repo public ✅ and renamed ✅, no `AIza` in history, LICENSE present, everyone has commits | |
| 4:30 | **Submit** (Radhesh) | |

**Commits so far:** Radhesh 6 · Sohan 4 · Sheersh 2 · Leena 0. Everyone needs at least 6, and Leena needs at least one
(the GitHub web editor is fine).

**Repo:** renamed to `rad117/H26_TechLiers_Track1`. The old URL still redirects, but to update your clone run
`git remote set-url origin https://github.com/rad117/H26_TechLiers_Track1.git`.
