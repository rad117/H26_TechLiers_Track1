"""Tests for capsule.write_all. Run: python -m pytest depexit/tests -q"""
import json
from pathlib import Path

from depexit import capsule

SAMPLE = Path(__file__).parents[2] / "team" / "sample_data" / "results.sample.json"


def write_sample(out):
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    return capsule.write_all(out, data["meta"], data["records"], data["results"],
                             data["baseline"], data["scorecard"])


def test_writes_every_capsule_file(tmp_path):
    write_sample(tmp_path)
    assert (tmp_path / "summary.json").exists()
    replay = (tmp_path / "replay.ps1").read_text(encoding="utf-8-sig")
    # patches carry \r\n context from a Windows clone; without this flag they fail on autocrlf=false machines
    assert "apply --ignore-whitespace" in replay
    for dep in ["Jinja2", "pydantic", "appdirs"]:
        for name in ["capsule.json", "capsule.md", "patch.diff"]:
            assert (tmp_path / dep / name).exists(), f"{dep}/{name} missing"


def test_markdown_separates_verified_from_ai(tmp_path):
    write_sample(tmp_path)
    md = (tmp_path / "Jinja2" / "capsule.md").read_text(encoding="utf-8")
    assert md.index("## ✅ Verified") < md.index("## 🤖 AI-suggested") < md.index("## ⚠ Open concerns")
    assert "linkwatch/report.py:3" in md          # usage location
    assert "fails_in_baseline" in md              # risk signal
    assert "SAMPLE DATA" in md                    # sample runs are always labelled


def test_wrong_prediction_is_explained_in_safe_broke_terms(tmp_path):
    # Team decision A: "pass" = installs and no test that passed before fails after
    write_sample(tmp_path)
    md = (tmp_path / "pydantic" / "capsule.md").read_text(encoding="utf-8")
    assert "Gemma predicted the change was safe, but it broke 1 test(s) that passed before." in md


def test_regression_without_newly_failing_test_quotes_the_gap():
    cmp = {"verdict": "regressed", "predicted_outcome": "pass", "actual_outcome": "fail", "prediction_correct": False,
           "newly_failing": [], "still_failing": [], "gaps": ["3 of the original 10 tests no longer ran"]}
    run = {"stage": "tests"}
    lines = capsule.concerns({"name": "x"}, {"ok": True}, run, cmp)
    assert "Gemma predicted the change was safe, but: 3 of the original 10 tests no longer ran" in lines


def test_patch_bytes_are_written_exactly(tmp_path):
    # Windows clones have \r\n line endings; text mode would turn them into \r\r\n and `git apply` (replay.ps1) fails
    patch = "--- a/requirements.txt\r\n+++ b/requirements.txt\r\n@@ -1 +1 @@\r\n-Jinja2==2.11.3\r\n+Jinja2>=3.1,<4\n"
    record = {"name": "Jinja2", "status": "declared", "specs": {}, "usages": [], "signals": [], "health_score": 25}
    result = {"dep": record, "ai": None, "patch": patch, "run": None, "comparison": None}
    capsule.write_all(tmp_path, {"target": "x"}, [record], [result], None, {"total": 0, "correct": 0, "wrong": []})
    assert (tmp_path / "Jinja2" / "patch.diff").read_bytes() == patch.encode("utf-8")


def test_failed_ai_is_reported_not_crashed(tmp_path):
    write_sample(tmp_path)
    md = (tmp_path / "appdirs" / "capsule.md").read_text(encoding="utf-8")
    assert "Gemma failed" in md
    assert "not run" in md


def test_summary_has_evidence_hashes(tmp_path):
    write_sample(tmp_path)
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert len(summary["evidence"]["Jinja2/patch.diff"]) == 64     # sha256 hex digest


def test_report_embeds_data_and_works_offline(tmp_path):
    paths = write_sample(tmp_path)
    page = Path(paths["report"]).read_text(encoding="utf-8")
    assert "__DEPEXIT_DATA__" not in page          # data was injected
    assert "Jinja2" in page
    assert "http://" not in page.replace("http://www.w3.org", "") and "src=\"http" not in page   # no CDN


def test_ai_text_cannot_break_out_of_report(tmp_path):
    # Gemma's output is untrusted: a "</script>" inside it must not end our <script> block
    evil = "</script><img src=x onerror=alert(1)>"
    record = {"name": "evil", "status": "declared", "specs": {}, "usages": [], "signals": [], "health_score": 10}
    result = {"dep": record, "ai": {"ok": True, "risk_explanation": evil}, "patch": evil, "run": None, "comparison": None}
    paths = capsule.write_all(tmp_path, {"target": "x"}, [record], [result], None, {"total": 0, "correct": 0, "wrong": []})
    page = Path(paths["report"]).read_text(encoding="utf-8")
    assert page.count("</script>") == capsule.REPORT_TEMPLATE.read_text(encoding="utf-8").count("</script>")


def test_handles_no_ai_and_no_tests(tmp_path):
    record = {"name": "six", "status": "unused", "specs": {"requirements.txt": ""},
              "usages": [], "signals": [], "health_score": 90, "at_risk": False}
    result = {"dep": record, "ai": None, "patch": "", "run": None, "comparison": None}
    meta = {"target": "x", "target_commit": None, "model": None}
    capsule.write_all(tmp_path, meta, [record], [result], None, {"total": 0, "correct": 0, "accuracy": None, "wrong": []})
    assert "not run" in (tmp_path / "six" / "capsule.md").read_text(encoding="utf-8")
