# depexit: the final product, and what goes on each slide

**For Leena** (and anyone presenting). Written by Radhesh, 15 Oct. Plain language, no code needed.

> **Numbers rule:** every number below now comes from the **real run** in `example_output/` (15 Oct, 15:36).
> Never use the numbers from `team/sample_data`: that data is invented, and the judges may ask.
>
> **Real result:** Gemma was right about **7 of 7** migrations. Jinja2's fix repaired the broken test (9/10 → 10/10);
> setuptools' fix removed the deprecation warning; the other 5 broke nothing. The run took 4.6 minutes.

---

## Part 1: The final product

### In one sentence
**depexit finds the risky, outdated libraries in a Python project, asks Gemma 4 how to replace each one, then
actually tests that fix, and tells you honestly where Gemma was right and where it was wrong.**

### The problem (why this matters)
Every Python project depends on other people's libraries. Over time they go stale: old versions stop installing,
break with newer libraries, or get abandoned. Our target project, **LinkWatch**, is a real example:
- Its test suite **already fails** today (9 of 10 tests pass), because an old library (**Jinja2 2.11**) breaks with
  today's version of another library (MarkupSafe). Nobody changed LinkWatch; the world around it moved.
- Its two dependency files **disagree** with each other (pydantic version 1 in one file, version 2 in the other).
- It uses **abandoned** libraries (`appdirs`, `toml`) and a **deprecated** feature (`pkg_resources`).

Maintainers know this is risky but don't know **what** to change, **where**, or whether the fix will break something.
Asking an AI helps, but AI answers can be confidently wrong.

### What depexit does (5 steps, one command)
1. **Find** every dependency and score its health from 0 to 100 using public facts (PyPI release dates, version gaps,
   abandoned packages, test failures). ✅ *verified*
2. **Locate** exactly which files and lines use each risky dependency (the "blast radius"). ✅ *verified*
3. **Ask Gemma 4** for a replacement plan: what to change, the edited code, and a **prediction**: "will this break
   anything?" plus how confident it is. 🤖 *AI*
4. **Test the plan for real:** apply Gemma's fix to a copy of the project, install everything fresh, and run the
   project's own test suite. ✅ *verified*
5. **Write a Dependency Exit Capsule:** a folder a maintainer can keep, with the evidence, the patch, a report page,
   and a script that re-runs everything.

### What you get at the end (the deliverables)
| File | What it is |
|---|---|
| `report.html` | **The Blast Radius page.** Opens in any browser, works offline. The headline: **"Gemma was right about 7 of 7 migrations."** (real run) |
| `<dependency>/capsule.md` | A readable report per risky dependency: verified facts first, Gemma's suggestions second, honest concerns last |
| `<dependency>/patch.diff` | The exact code change that was tested |
| `replay.ps1` | Re-runs every test from scratch, so anyone can check our evidence |
| `summary.json` | All the data, with a fingerprint (sha256) of every evidence file, so nobody can quietly edit it later |

### What makes it different (our wow factor)
**Most AI tools trust the AI. We grade it.**
- Every claim Gemma makes is **tested**, and the report shows Gemma's prediction next to what really happened.
- In the report, **dashed outlines = what Gemma claimed**, **solid colours = what the tests proved**. You can tell
  AI from evidence at a glance, on every part of the page.
- When Gemma is wrong, we **show it** rather than hide it ("Gemma was 70% sure it was safe; it broke 1 test").
- We were careful to grade Gemma **fairly**: a fix counts as **safe** if it installs and **breaks no test that passed
  before**. Tests that were already broken don't count against it. (Sheersh spotted that our first scoring was unfair
  to Gemma, and we fixed it: a good story for judges.)

### Who it helps (impact)
Any maintainer of a Python project with old version pins, which is most projects older than a couple of years.
Instead of an afternoon of trial and error per library, they get a tested plan with evidence, and they know which
AI suggestions to trust.

---

## Part 2: The slides

Use the **Canva template** exactly as given: don't change its layout or theme. If the template already names its
slides, put our content under the matching title. The brief splits the work: **Leena does slides 1, 4, 5, 6;
Radhesh does slides 2 and 3** (Leena, you can paste the text below as a starting point, and Radhesh will check it).

Keep on-slide text short. The judges listen to you; the slide is a reminder, not a script.

### Slide 1: Team, track and problem (Leena)
**On the slide:**
- Title: **depexit: test the AI before you trust it**
- Team **TechLiers**: Sohan, Sheersh, Radhesh, Leena
- Track 1: **Best Use of Gemma 4**, Dependency Resilience
- Problem, in one line: *Old dependencies silently break projects. AI can suggest fixes, but can you trust them?*
- A real example: *LinkWatch's tests already fail today (9/10 pass) because of one outdated library.*

**Say:** "Python projects rot without anyone touching them. LinkWatch, our target, fails its own tests today
because Jinja2 2.11 broke when another library updated. You can ask an AI what to do, but how do you know the
answer is right?"

### Slide 2: How it works (Radhesh)
**On the slide:** a left-to-right diagram with 5 boxes, colour-coded (green = verified, purple = AI):

```
[1 Find & score] → [2 Locate usages] → [3 Ask Gemma 4] → [4 Test the fix] → [5 Exit Capsule]
   green              green               purple            green             report + replay
```
Under it: *One command:* `python -m depexit analyze <github-url>`

**Say:** "Steps 1, 2 and 4 are facts we measure. Step 3 is the only AI step, and step 4 exists to check it."

### Slide 3: Tech and the AI model (Radhesh)
**On the slide:**
- **AI model:** Gemma 4 (`gemma-4-31b-it`, with `gemma-4-26b-a4b-it` as fallback) by Google DeepMind, via the
  Gemini API. In the real run, the 31B model answered 2 dependencies and the fallback answered 5.
- **What Gemma does:** explains the risk, proposes the replacement and code edits, predicts "safe or breaks?" with
  a confidence.
- **What Gemma is NOT trusted for:** every suggestion is tested before we report it as working.
- **Built with:** Python 3.12, `uv` (fast isolated installs), pytest, the PyPI API, and a single offline HTML report
- A screenshot of `report.html` from the **real run**

**Say:** "We send Gemma only verified facts plus the affected source files, and ask for strict JSON. Then we
apply its change in a sandbox copy and run the real tests."

### Slide 4: Feasibility, limits and risks (Leena)
**On the slide:**
- ✅ **Works today** on a real repository, end to end: 7 migrations tested in 4.6 minutes
- ✅ **Fast and free:** `uv` installs in about 10–20 s per test run; no paid APIs
- ⚠ **Limits (honest):**
  - Tests only prove what they cover: a fix can pass the tests and still break untested code
  - Python projects with `requirements.txt` / `pyproject.toml` only, for now
  - We update `requirements.txt`; `pyproject.toml` may still need a manual edit
  - Gemma sometimes returns unusable answers; we record that rather than crash
- 🛡 **Safety:** AI-written file edits can only touch files inside the project copy, never the real project

**Say:** "We report our limitations automatically: every capsule ends with an 'open concerns' section generated
from the evidence."

### Slide 5: Impact (Leena)
**On the slide:**
- **Who benefits:** every Python maintainer with old version pins
- **Before:** hours of trial and error per library, AI answers taken on faith
- **After:** one command → a tested plan, the exact patch, and evidence anyone can re-run
- **Result on LinkWatch:** all 7 Gemma migrations held up. The Jinja2 upgrade fixed the broken report test
  (9/10 → 10/10), and the setuptools fix removed a deprecation warning. Gemma even caught that pydantic v2 renamed a
  setting (`anystr_strip_whitespace` → `str_strip_whitespace`)

**Say:** "The output isn't a chat answer; it's a capsule a maintainer can keep, check and replay."

### Slide 6: Research and references (Leena)
**On the slide:** the official sources we checked Gemma's suggestions against (Leena: confirm each link opens, and
note whether Gemma agreed):

| Dependency | What the official source says | Link |
|---|---|---|
| Jinja2 | 3.x is the maintained line | jinja.palletsprojects.com/en/stable/changes/ |
| pydantic | v1 → v2 migration guide | docs.pydantic.dev/latest/migration/ |
| setuptools | `pkg_resources` is deprecated | setuptools.pypa.io/en/latest/pkg_resources.html |
| appdirs | Superseded by `platformdirs` | github.com/tox-dev/platformdirs |
| toml | Python 3.11+ has `tomllib` built in | docs.python.org/3/library/tomllib.html |
| Gemma 4 | Model card and licence/terms | ai.google.dev/gemma *(put the exact terms link in `docs/model.md`)* |

**Say:** "Gemma's replacements matched the official migration path every time: Jinja2 3.x, pydantic v2,
`platformdirs`, `tomllib`, and `importlib.resources` instead of `pkg_resources`. The tests then confirmed none of
them broke anything." *(Leena: confirm each link before saying this.)*

### Optional last slide: demo / thank you
Repo link: **github.com/rad117/H26_TechLiers_Track1**, plus a QR code if the template has room.

---

## Part 3: Demo script (2 minutes)
1. **Problem (15 s):** "LinkWatch fails its own tests today because of stale dependencies."
2. **Run (20 s):** run the command, or show the recording if the venue Wi-Fi is bad.
3. **Open `example_output/report.html` (20 s):** read the headline aloud: "Gemma was right about 7 of 7."
4. **Click Jinja2 (20 s):** the solid green box says the tests went from 9/10 to 10/10, with the patch shown.
5. **Click pydantic (20 s):** "Gemma ported the config file to pydantic v2 and even caught a renamed setting, and the
   tests confirm nothing broke. But we don't stop at a perfect score: LinkWatch only has 10 tests, so every capsule
   says what the tests *don't* prove."
6. **Test grid (10 s):** "Each column is a real test run; bright cells are what each fix changed."
7. **Capsule and replay (15 s):** "Anyone can run `replay.ps1` and get the same evidence."

## Part 4: Questions judges will probably ask
| Question | Answer |
|---|---|
| Which parts are AI and which are verified? | Only step 3 is AI. On the report, dashed = AI claim, solid = tested. Every capsule has separate ✅ and 🤖 sections. |
| How do you know Gemma's fix works? | We apply it to a copy, install fresh with Python 3.12, and run the project's own tests, before and after. |
| What if Gemma is wrong? | We show it: the scorecard counts it, and the capsule explains which test broke and why. |
| 7 out of 7: isn't that suspicious? | It's what the tests showed, and replay.ps1 lets you check. But LinkWatch only has 10 tests, so a perfect score is only as strong as they are; every capsule's "open concerns" says so. On a project with deeper tests, the grading is harder. |
| Is "pass" fair to Gemma? | Yes: "safe" means it breaks nothing that worked before. Pre-existing failures don't count against it. |
| Could you have faked the results? | Every evidence file has a sha256 fingerprint in `summary.json`, and `replay.ps1` re-runs everything. |
| What are the limits? | Tests only cover what they test; Python only; pyproject.toml isn't auto-edited yet. (See slide 4.) |
| Did you use paid APIs? | No. Gemma 4 through the Gemini API [free tier: Leena, confirm the organisers' answer]. |
