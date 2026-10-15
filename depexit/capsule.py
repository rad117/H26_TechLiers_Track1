"""Write the Dependency Exit Capsule: summary.json, per-dependency capsule.json/.md, patch.diff,
report.html (Blast Radius) and replay.ps1.

Owner: Radhesh. Develop against team/sample_data/results.sample.json (DEV ONLY, never ship it as output):
    python -m depexit.capsule team/sample_data/results.sample.json capsule_dev

Rule for every file written here: facts observed by depexit (✅ verified) and Gemma's suggestions
(🤖 AI) are always kept in separate, labelled sections.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

REPORT_TEMPLATE = Path(__file__).parent / "templates" / "report.html"
# Team decision A (15 Oct): a migration "passes" if it installs and no test that passed before fails after.
# Tests that already failed on the original dependencies don't count against it.
SAFE = {"pass": "safe", "fail": "breaks something"}
SAFE_MEANING = '"Safe" means the change installs and no test that passed before fails after it.'
SAMPLE_BANNER ="> ⚠ **SAMPLE DATA, NOT A REAL RUN.** Every AI field and candidate test run in this file is invented.\n\n"


def write_all(out, meta, records, results, baseline, card):
    """Write every capsule file into out/. Return {"report": path_to_report_html, ...}."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    full = {r["name"]: r for r in records}  # results may carry a short "dep"; records hold everything

    for result in results:
        dep = full.get(result["dep"]["name"], result["dep"])
        folder = out / safe_name(dep["name"])
        folder.mkdir(exist_ok=True)
        write_json(folder / "capsule.json", {**result, "dep": dep})
        (folder / "capsule.md").write_text(capsule_md(meta, dep, result, baseline), encoding="utf-8")
        (folder / "patch.diff").write_text(result.get("patch") or "", encoding="utf-8")

    paths = {"replay": write_replay(out, meta, results, baseline)}
    summary = {"meta": meta, "scorecard": card, "baseline": baseline, "records": records,
               "results": results, "evidence": evidence_hashes(out, baseline, results)}
    paths["summary"] = write_json(out / "summary.json", summary)
    concern_map = {r["dep"]["name"]: concerns(full.get(r["dep"]["name"], r["dep"]), r.get("ai"), r.get("run"), r.get("comparison"))
                   for r in results}
    paths["report"] = write_report(out, {**summary, "concerns": concern_map})
    return {k: str(v) for k, v in paths.items()}


# ---------- small helpers ----------

def safe_name(name):
    """A package name as a safe folder name (no slashes or odd characters from untrusted input)."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def evidence_hashes(out, baseline, results):
    """sha256 of every evidence file, so anyone can check the capsule wasn't edited after the run."""
    files = sorted(p for p in out.glob("*/*") if p.name in ("capsule.json", "capsule.md", "patch.diff"))
    files.append(out / "replay.ps1")
    logs = [r.get("log_file") for r in [baseline, *[x.get("run") for x in results]] if r]
    files += [Path(log) for log in logs if log and Path(log).is_file()]
    return {p.relative_to(out).as_posix() if p.is_relative_to(out) else str(p): sha256(p) for p in files}


# ---------- capsule.md ----------

def run_line(label, run):
    if not run:
        return f"| {label} | not run | | | | |"
    return (f"| {label} | {run['stage']} | {'✅' if run['ok'] else '❌'} | {run.get('passed', '-')} "
            f"| {run.get('failed', '-')} | {run.get('errors', '-')} |")


def capsule_md(meta, dep, result, baseline):
    ai, run, cmp = result.get("ai"), result.get("run"), result.get("comparison")
    ai_ok = bool(ai and ai.get("ok"))
    verdict = cmp["verdict"] if cmp else "not run"
    if cmp and cmp.get("prediction_correct") is not None:
        mark = "✅" if cmp["prediction_correct"] else "❌"
        prediction = f"Gemma predicted: {SAFE[cmp['predicted_outcome']]} → actual: {SAFE[cmp['actual_outcome']]} {mark}"
    else:
        prediction = "Gemma prediction: not graded"

    md = [f"# Dependency Exit Capsule: {dep['name']}\n",
          SAMPLE_BANNER if meta.get("sample") else "",
          f"Health score: {dep.get('health_score', '?')}/100 · Verdict: {verdict} · {prediction}\n",
          f"_{SAFE_MEANING}_\n",
          f"Target: {meta.get('target')} @ `{meta.get('target_commit') or 'unknown commit'}`\n",
          "## ✅ Verified (observed by depexit)\n",
          "### Dependency details\n"]

    pypi = dep.get("pypi") or {}
    md.append(f"- Status: **{dep.get('status', '?')}**")
    for file, spec in (dep.get("specs") or {}).items():
        md.append(f"- `{file}`: `{dep['name']}{spec}`" if spec else f"- `{file}`: unpinned")
    if dep.get("spec_mismatch"):
        md.append("- ⚠ requirements.txt and pyproject.toml **disagree**")
    md.append(f"- Pinned: {dep.get('pinned_version') or 'not pinned'} (released {pypi.get('pinned_date') or '?'})"
              f" · Latest: {pypi.get('latest', '?')} (released {pypi.get('latest_date') or '?'})")
    md.append(f"- Requires Python: {pypi.get('requires_python') or 'not stated'}\n")

    md.append("### Risk indicators\n")
    if dep.get("signals"):
        md.append("| Signal | Detail | Points | Source |\n|---|---|---|---|")
        md += [f"| `{s['id']}` | {s['detail']} | {s['points']} | {s['source']} |" for s in dep["signals"]]
    else:
        md.append("No risk signals.")
    md.append("")

    md.append("### Usage locations\n")
    for u in dep.get("usages") or []:
        flag = " ⚠ private API" if u.get("private") else ""
        md.append(f"- `{u['file']}:{u['line']}`: `{u['code']}`{flag}")
    if not dep.get("usages"):
        md.append("Not imported anywhere.")
    md.append("")

    md.append("### Executed test results\n")
    md.append("| Run | Stage | OK | Passed | Failed | Errors |\n|---|---|---|---|---|---|")
    md += [run_line("Baseline (original deps)", baseline), run_line("After migration", run), ""]
    if cmp:
        for key, label in [("newly_passing", "Newly passing"), ("newly_failing", "Newly failing"),
                           ("still_failing", "Still failing"), ("gone_warnings", "Warnings gone"),
                           ("new_warnings", "New warnings")]:
            md += [f"- {label}: `{item}`" for item in cmp.get(key) or []]
    if run:
        md.append("\nCommands run (see replay.ps1):\n")
        md += [f"    {c}" for c in run.get("commands") or []]
    md.append("")

    md.append("### Compatibility gaps\n")
    gaps = (cmp or {}).get("gaps")
    md += [f"- {g}" for g in gaps] if gaps else ["None observed." if cmp else "Not run, so unknown."]
    md.append("")

    model = (ai or {}).get("model") or meta.get("model") or "model unknown"
    md.append(f"## 🤖 AI-suggested (Gemma 4 · {model}; not verified unless confirmed by the tests above)\n")
    if not ai:
        md.append("Gemma was not run for this dependency.\n")
    elif not ai_ok:
        md.append(f"Gemma failed: {ai.get('error', 'unknown error')}\n")
    else:
        md += ["### Risk explanation\n", ai.get("risk_explanation", ""), "",
               "### Proposed replacement\n",
               f"- `{ai.get('replacement')}` ({ai.get('migration_type')})",
               *[f"- requirements.txt: {c['action']} `{c.get('line') or c['name']}`" for c in ai.get("requirement_changes") or []],
               *[f"- rewrites `{e['path']}`" for e in ai.get("file_edits") or []],
               f"- Predicted: **{SAFE.get(ai.get('predicted_outcome'), '?')}** (confidence {ai.get('confidence')})", "",
               "### Migration steps\n",
               *[f"{i}. {s}" for i, s in enumerate(ai.get("steps") or [], 1)], "",
               "### Suggested tests\n",
               *[f"- {t}" for t in ai.get("suggested_tests") or []], ""]

    md.append("## ⚠ Open concerns and limitations\n")
    md += [f"- {c}" for c in concerns(dep, ai, run, cmp)]
    return "\n".join(md) + "\n"


def concerns(dep, ai, run, cmp):
    """Honest, automatically derived caveats for one dependency."""
    out = []
    if not ai:
        out.append("Gemma was not run, so no migration was proposed or tested.")
    elif not ai.get("ok"):
        out.append("Gemma failed, so no migration was tested (test run: not run).")
    elif not run:
        out.append("The migration was proposed but not run (tests skipped).")
    if run and run["stage"] != "tests":
        out.append(f"Install was blocked at stage `{run['stage']}`; the tests never ran.")
    if cmp and cmp.get("prediction_correct") is False:
        if cmp["predicted_outcome"] == "fail":
            out.append("Gemma predicted the change would break something, but no test that passed before failed.")
        elif run and run["stage"] != "tests":
            out.append("Gemma predicted the change was safe, but it could not even be installed.")
        else:
            out.append(f"Gemma predicted the change was safe, but it broke {len(cmp.get('newly_failing') or [])} "
                       "test(s) that passed before.")
    if cmp and cmp.get("still_failing"):
        out.append(f"{len(cmp['still_failing'])} test(s) still fail after this change (may be unrelated to it).")
    changed = {c["name"].lower() for c in (ai or {}).get("requirement_changes") or []}
    if "pyproject.toml" in (dep.get("specs") or {}) and dep["name"].lower() in changed:
        out.append("Only requirements.txt was changed; pyproject.toml still has the old spec.")
    out.append("A passing test suite only proves the code paths the tests actually exercise.")
    return out


# ---------- report.html ----------

def write_report(out, data):
    """Embed all data as JSON inside the self-contained template (no server or internet needed)."""
    # "<" is escaped as < so text from Gemma like "</script>" can't end our <script> block early
    blob = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    page = REPORT_TEMPLATE.read_text(encoding="utf-8").replace("__DEPEXIT_DATA__", blob)
    path = out / "report.html"
    path.write_text(page, encoding="utf-8")
    return path


# ---------- replay.ps1 ----------

def ps_command(cmd):
    """PowerShell needs `&` to run an executable given as a path (e.g. .venv/Scripts/python.exe)."""
    first = cmd.split(" ", 1)[0]
    return f"& {cmd}" if ("/" in first or "\\" in first) else cmd


def write_replay(out, meta, results, baseline):
    target, commit = meta.get("target"), meta.get("target_commit")
    checkout = f'git -C $dir checkout -q {commit}' if commit and commit != "SAMPLE" else "# (commit unknown: using latest)"
    lines = ["# depexit replay: re-runs the exact commands behind this capsule, so anyone can check our evidence.",
             f"# Target: {target} @ {commit or 'unknown'}   Generated: {meta.get('generated_at')}",
             "# Usage (PowerShell, needs git + uv):  .\\replay.ps1",
             "$capsule = $PSScriptRoot", "$root = Join-Path $capsule '_replay'", ""]

    def block(title, folder, commands, patch=None):
        lines.extend([f"# ----- {title} -----", f"$dir = Join-Path $root '{folder}'",
                      f"git clone -q {target} $dir", checkout])
        if patch:
            lines.append(f"git -C $dir apply (Join-Path $capsule '{patch}')")
        lines.append("Push-Location $dir")
        lines.extend(ps_command(c) for c in commands)
        lines.extend(["Pop-Location", ""])

    if baseline:
        block("Baseline: original dependencies", "baseline", baseline.get("commands") or [])
    for r in results:
        name = safe_name(r["dep"]["name"])
        if r.get("run"):
            block(f"{r['dep']['name']}: apply Gemma's patch, then test", name,
                  r["run"].get("commands") or [], patch=f"{name}/patch.diff")
        else:
            lines.extend([f"# ----- {r['dep']['name']}: no test run recorded (not run) -----", ""])
    path = out / "replay.ps1"
    path.write_text("\n".join(lines), encoding="utf-8-sig")  # BOM: Windows PowerShell 5.1 only reads UTF-8 correctly with one
    return path


if __name__ == "__main__":
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(write_all(Path(sys.argv[2] if len(sys.argv) > 2 else "capsule_dev"),
                    data["meta"], data["records"], data["results"], data["baseline"], data["scorecard"]))
