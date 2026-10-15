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
    assert (tmp_path / "replay.ps1").exists()
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
