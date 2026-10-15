# depexit: team status

**Last updated:** 15 Oct, 15:10, by Radhesh. Update your own row when something changes.

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

**The full product description, the slide-by-slide content, the demo script and likely judge questions are in
[PRODUCT_AND_SLIDES.md](PRODUCT_AND_SLIDES.md).** Leena: build the deck from that.

## Decisions

- **15 Oct, 13:40: what "pass" means (option A, raised by Sheersh, agreed).** A migration passes if it **installs and
  no test that passed before fails after it** (verdict `improved` or `same`). Tests that already fail on the original
  dependencies (like `test_report` because of Jinja2) don't count against other migrations. ✅ Done by everyone:
  `compare.py`, the `gemma.py` prompt, the report and the capsules all use this definition.
- **15 Oct, 15:05: no blast radius graph.** Feature freeze is 3:15. The ledger, test grid and table already tell the
  story, and the brief says a finished table beats an unfinished graph.

## Where each piece is

| Piece | Owner | Status |
|---|---|---|
| `deps.py`, `scan.py`, `pypi.py` | Sohan | ✅ done |
| `gemma.py` | Sohan | ✅ done, prompt matches decision A, offline tests |
| `runner.py` | Sheersh | ✅ works in the real run, but **3 of its tests fail on Windows** (fixes below) |
| `compare.py` | Sheersh | ✅ done, decision A, flags patches that edit tests |
| `capsule.py` + `report.html` | Radhesh | ✅ done, 10 tests. Fixed: `patch.diff` was corrupted on Windows (`\r\n` → `\r\r\n`), which would have broken `replay.ps1` |
| `README.md` (7 sections) | Radhesh | ✅ drafted. Has `TODO` comments for Sohan, Sheersh and Leena (search the file for `TODO(`) |
| **Full run with Gemma** | **Sohan** | ❌ **not done yet: the most important thing left** |
| `example_output/` + report screenshot | Radhesh | ❌ needs the full run first |
| `docs/model.md`, `docs/references.md`, slides | Leena | ❌ nothing pushed, **0 commits** |

## Verified: real end-to-end run without Gemma (15:02)

`python -m depexit analyze https://github.com/rishrek/LinkWatch --no-ai` ran **cleanly in 54 s** on Radhesh's
machine:
- Baseline reproduced exactly: **9 passed, 1 failed** (`soft_unicode`), plus the `pkg_resources` warning
- **7 at risk:** Jinja2, pydantic, idna, chardet, toml, appdirs, setuptools
- All capsule files written, 23 evidence files fingerprinted, `replay.ps1` pins commit `f52f393`

## What we need, from whom (in order)

1. **Sohan (now):** do the full run with Gemma and send Radhesh the `capsule_out` folder (zip it, or push it to
   `example_output/` yourself without `_work/` except `_work/logs/`). If it's slow, use `--max-deps 4`.
   Then fill `TODO(Sohan)` in the README: confirm the model ids, plus anything that went wrong (limitations).
2. **Sheersh:** fix the 3 Windows test failures (both are in the tests/helpers, the real run works):
   - `runner.relative()`: also strip the repo path followed by `/`:
     `text.replace(str(repo_dir) + os.sep, "").replace(str(repo_dir) + "/", "")`
     (your tests build paths like `f"{tmp_path}/.venv/x.py"`; on Windows `os.sep` is `\`)
   - `test_runner.py` line 64: write the patch as bytes:
     `(tmp_path / "patch.diff").write_bytes(diff.encode("utf-8"))`. `write_text` on Windows turns `\r\n` into
     `\r\r\n`, so `git apply` rejects it. (Radhesh hit the same bug in `capsule.py`.)
   - Then check the README's "How we verify" section (`TODO(Sheersh)`), and edit it if you want.
3. **Leena:** push `docs/model.md` (Gemma 4 licence name and link), fill `TODO(Leena)` in the README, and make the
   deck from `PRODUCT_AND_SLIDES.md`. **You need at least one commit**: the GitHub web editor is fine.
4. **Radhesh:** commit `example_output/`, add the report screenshot to the README, fill the result numbers in
   `PRODUCT_AND_SLIDES.md`, record the demo at 3:45, final checks at 4:15, submit by 4:30.

## Checkpoints

| Time | Checkpoint | State |
|---|---|---|
| 2:15 | First end-to-end run | ✅ 15:02 without Gemma; **the full run with Gemma is still pending** |
| 3:15 | Feature freeze: bug fixes only after this | |
| 3:45 | Screen-record the full run and the report | |
| 4:00 | README done, real run committed to `example_output/` | README drafted ✅ |
| 4:15 | Final checks: repo public ✅ and renamed ✅, no `AIza` in history, LICENSE present ✅, everyone has commits | |
| 4:30 | **Submit** (Radhesh) | |

**Commits so far:** Radhesh 10 · Sohan 7 · Sheersh 6 · Leena 0.

**Repo:** `rad117/H26_TechLiers_Track1`. If your clone still uses the old URL:
`git remote set-url origin https://github.com/rad117/H26_TechLiers_Track1.git`.
