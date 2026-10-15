"""Compare baseline vs candidate test runs, and grade Gemma's predictions ("Gemma vs Reality").

Owner: Sheersh. Output shapes: Comparison and Scorecard in team/CONTRACT.md.
"""


def last_line(text):
    lines = [l.strip() for l in (text or "").splitlines() if l.strip()]
    return lines[-1] if lines else "no output"


def compare(baseline, run, ai):
    """Return a Comparison dict for one dependency."""
    before, after = baseline.get("failing_tests", {}), run.get("failing_tests", {})
    blocked = run["stage"] != "tests"
    # tests from the original suite that no longer even ran (e.g. conftest.py fails to import)
    missing = 0 if blocked else baseline.get("tests", 0) - run.get("tests", 0)
    if blocked or run.get("tests", 0) == 0:  # nothing ran, so there is nothing to compare test by test
        newly_failing, newly_passing, still_failing, new_warnings, gone_warnings = [], [], [], [], []
    else:
        newly_failing = sorted(set(after) - set(before))
        newly_passing = sorted(set(before) - set(after))
        still_failing = sorted(set(before) & set(after))
        new_warnings = sorted(set(run["warnings"]) - set(baseline["warnings"]))
        gone_warnings = sorted(set(baseline["warnings"]) - set(run["warnings"]))

    if blocked:
        verdict = "blocked"
    elif newly_failing or missing > 0:
        verdict = "regressed"
    elif newly_passing or gone_warnings:
        verdict = "improved"
    else:
        verdict = "same"

    gaps = []
    if blocked:
        gaps.append(f"Blocked at the {run['stage']} stage, so no tests ran: {last_line(run.get('error'))}")
    if missing > 0:
        detail = f": {last_line(run['error'])}" if run.get("error") else ""
        gaps.append(f"{missing} of the original {baseline['tests']} tests no longer ran{detail}")
    gaps += [f"{test} now fails: {after[test]}" for test in newly_failing]
    # an AI can make a failing test "pass" by editing the test, so say so loudly
    edited_tests = [e.get("path") for e in (ai or {}).get("file_edits") or [] if str(e.get("path", "")).startswith("tests")]
    if edited_tests:
        gaps.append(f"The patch edits test files ({', '.join(edited_tests)}), so passing tests prove less")
    gaps += [f"New warning: {w}" for w in new_warnings]  # passing tests can still hide a coming break

    ai_ok = bool(ai and ai.get("ok"))
    # team decision (Option A): "pass" = installed and no test that passed before now fails.
    # Not run["ok"]: the baseline already has a failing test that most migrations don't touch.
    actual = "pass" if verdict in ("improved", "same") else "fail"
    predicted = ai.get("predicted_outcome") if ai_ok else None
    return {
        "verdict": verdict,
        "actual_outcome": actual,
        "predicted_outcome": predicted,
        "prediction_correct": (predicted == actual) if ai_ok else None,
        "newly_failing": newly_failing, "newly_passing": newly_passing, "still_failing": still_failing,
        "new_warnings": new_warnings, "gone_warnings": gone_warnings,
        "gaps": gaps,
    }


def why_wrong(cmp, run):
    """The observed reason the outcome was what it was (not a warning: warnings don't fail a run)."""
    if cmp["actual_outcome"] == "fail":  # verdict is "blocked" or "regressed", and gaps[0] says why
        return cmp["gaps"][0]
    return f"installed and nothing new broke ({run['passed']} of {run['tests']} tests pass)"


def scorecard(results):
    """Return a Scorecard dict over all DepResults that have both an AI prediction and a test run."""
    graded = [r for r in results if r.get("comparison") and r["comparison"]["prediction_correct"] is not None]
    wrong = [{"dep": r["dep"]["name"], "predicted": r["comparison"]["predicted_outcome"],
              "actual": r["comparison"]["actual_outcome"], "why": why_wrong(r["comparison"], r["run"])}
             for r in graded if not r["comparison"]["prediction_correct"]]
    total = len(graded)
    return {
        "total": total,
        "correct": total - len(wrong),
        "accuracy": round((total - len(wrong)) / total, 2) if total else None,
        "wrong": wrong,
    }
