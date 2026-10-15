# Radhesh: Capsule + Blast Radius report + Submission owner (with Leena)

> Read `team/CONTRACT.md` first (5 min). Your input is the `meta / records / results / baseline / scorecard` data described there.

## Your job in one line
Turn everyone's data into the **Dependency Exit Capsule**: files a maintainer can reuse, plus a **Blast Radius** HTML page the judges understand in 5 seconds. You also own the **repo, README, slides and the final submission**.

## Your files
`depexit/capsule.py` (+ an HTML template string or `depexit/templates/report.html` if you prefer) · `README.md` · slides

## Setup (10 min)
```powershell
cd C:\Users\radhe\LinkWatch
uv venv --python 3.12 .venv ; .venv\Scripts\activate
uv pip install -r depexit/requirements.txt
python -m depexit.capsule team/sample_data/results.sample.json capsule_dev    # your dev loop
```
`team/sample_data/results.sample.json` is **fake sample data (DEV ONLY)** shaped exactly like the real thing, so you can build without waiting for Sohan and Sheersh. **Never show it as real output.** The demo must use a real run.

## First, right now (5 min)
- [ ] **Rename the repo** on GitHub: Settings → `H26_<TeamName>_<ProjectName>` (e.g. `H26_TeamX_DepExit`). GitHub redirects the old URL, so nobody has to re-clone.
- [ ] Licence: the fork already has LinkWatch's MIT `LICENSE`. Keep it unchanged. In the README, state that `depexit/` is also released under MIT by our team.

---

## Task 1 · Capsule files (12:20 → 1:00)
`capsule.write_all(out, meta, records, results, baseline, card)` writes:
```
out/
  summary.json            ← everything (meta, records, results, baseline, scorecard)
  <dep>/capsule.json      ← one DepResult
  <dep>/capsule.md        ← human-readable capsule (below)
  <dep>/patch.diff        ← result["patch"]
  replay.ps1              ← Task 3
  report.html             ← Task 2
```
Each `capsule.md` follows the brief's order, **with AI and verified content visibly separated**:
```markdown
# Dependency Exit Capsule: Jinja2
Health score: 45/100 · Verdict: improved · Gemma prediction: pass → actual: pass ✅

## ✅ Verified (observed by depexit)
### Dependency details        (name, specs per file, pinned vs latest, dates)
### Risk indicators           (each signal + its source)
### Usage locations           (file:line + code)
### Executed test results     (baseline vs after: passed/failed, failing tests, warnings, commands)
### Compatibility gaps        (comparison.gaps; "none observed" if empty)

## 🤖 AI-suggested (Gemma 4 · <model id>; not verified unless confirmed by the tests above)
### Proposed replacement
### Migration steps
### Suggested tests

## ⚠ Open concerns and limitations
(prediction wrong? install blocked? tests don't cover this code path? only requirements.txt changed, not pyproject.toml?)
```
Handle missing pieces gracefully (`ai` is None, `ok: false`, or `run` is None): write "not run" rather than crashing.

## 🍽 1:00 – 1:30 Lunch. At 1:25, show a generated capsule.md from the sample data.

## Task 2 · `report.html`: the Blast Radius page (1:30 → 2:45)
**One self-contained HTML file** (inline CSS/JS, data embedded as `const DATA = …json…`, no CDN, so it works offline at the venue):
- **Top bar:** repo + commit, run time, model id, and a big **"Gemma vs Reality: 5/6 correct"** scorecard tile.
- **Blast radius graph** (SVG or canvas, like your lunar_ice_watch map):
  - dependencies on the left, LinkWatch files on the right, a line for each usage;
  - circle size = number of usages; colour = health score (red < 50, amber < 70, green);
  - an undeclared dependency gets a dashed outline.
- **Click a dependency** to open a side panel:
  - a ✅ **Verified** box (signals, usages, baseline → after test numbers, failing tests);
  - a 🤖 **AI-suggested** box (replacement, steps);
  - the patch diff in a `<pre>`;
  - verdict badge.
- **Table** of all dependencies sorted by health score (including the ones not at risk).
Keep it simple. A clear table + side panel beats a fancy graph that isn't finished. **Build the table first, then the graph.**

## Task 3 · `replay.ps1` (2:45 → 3:00)
Write out `baseline["commands"]` and each `result["run"]["commands"]` as a runnable script with comments. Anyone can re-run our evidence, which is what makes the capsule *reusable*.

## Task 4 · README + submission (3:00 → 4:30). **You submit.**
README.md (replace LinkWatch's README with ours; move the old one to `LINKWATCH_README.md`). It needs the **7 required sections**:
1. Problem & solution overview
2. Setup (uv + Python 3.12 + API key)
3. Usage (`python -m depexit analyze <url>` + flags)
4. Architecture (the 8-step flow from CONTRACT.md; a Mermaid diagram is fine)
5. Dependencies
6. **AI model details:** model name, model version, source (Google DeepMind), access method (Gemini API), licence/terms (Gemma licence / Apache 2.0, as stated on the model page Leena checks), role in the project (Sohan's 3 lines)
7. Known limitations (be honest: Sheersh's verify notes and Sohan's notes)

Plus: Sheersh's "How we verify" section, a screenshot of `report.html`, and **`example_output/`** with a real run's capsule committed (the evidence).
- **3:45:** screen-record the full run + report (OBS or Win+G), 2–3 min, as the fallback for the live demo.
- **4:15:** final checks:
  - the repo is **public** and correctly named;
  - `git log -p | Select-String "AIza"` finds nothing;
  - LICENSE is present;
  - everyone has commits.
- **Submit before 4:30.**

## Your deliverables (tick them off)
- [ ] Repo renamed `H26_<TeamName>_<ProjectName>`
- [ ] `capsule.py` writes every file above from both sample and real data
- [ ] `report.html` works offline: table + side panel + graph + scorecard
- [ ] `replay.ps1`
- [ ] README with all 7 sections + `example_output/`
- [ ] Screen recording
- [ ] At least 6 commits from you
- [ ] Submitted ✅

---

# Leena: Research & Presentation (no Claude Code needed)

Leena works with Radhesh. She has GitHub access (**Lee-2846**), so she should commit her docs through the GitHub website ("Add file → Create new file"). **Every member needs commits.**

### Do immediately (12:15 → 12:45)
1. **Ask the organisers** (write down the answers and tell the team):
   - "Is the free Gemini API tier OK for Gemma 4, given that 'paid APIs' are banned?"
   - "The repo must be 'forked from the official starter link': is that rishrek/LinkWatch?"
2. **Find the exact Gemma 4 model facts** for README section 6:
   - model id + version;
   - licence/terms link (ai.google.dev/gemma, the Gemma terms page);
   - release date.

   Put them in `docs/model.md`.
3. Copy the **Canva PPT template** (canva.link/m54gx2gop31ay5m). Make a copy and don't change its layout or theme.

### 12:45 → 1:00 and 1:30 → 3:00
4. **Fact-check Gemma.** For each risky dependency, find the official source that says what replaces it. These are the human-checked references for slide 6:
   - Jinja2 3.x changelog;
   - Pydantic v1→v2 migration guide;
   - setuptools `pkg_resources` deprecation note;
   - `platformdirs` as the successor of `appdirs`;
   - Python `tomllib` docs;
   - nose being unmaintained.

   Put the links in `docs/references.md`. If Gemma suggests something different from the official source, **tell Sohan**: that's a great "Gemma was wrong" demo point.
5. **Slides:**
   - 1 (team + track + problem);
   - 4 (feasibility, limits, risks);
   - 5 (impact: who benefits; every Python maintainer with old pins);
   - 6 (research & references).

   Radhesh adds 2–3 (workflow diagram, tech) at 3:00.

### 3:00 → 4:30
6. **Timekeeper:** call out 3:15 (feature freeze), 3:45 (record), 4:15 (final checks).
7. **Demo script** (2 minutes):
   - problem;
   - run the command;
   - open the report;
   - click Jinja2 (verified fix);
   - show the scorecard (where Gemma was wrong);
   - capsule files;
   - "anyone can run replay.ps1".
8. Be ready to answer judges: "which parts are AI vs verified?" and "what are the limitations?"
