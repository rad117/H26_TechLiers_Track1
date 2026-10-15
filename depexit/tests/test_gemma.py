"""Offline tests for gemma.py (no network, no API key). Run: python -m pytest depexit/tests -q"""
import json

import pytest

from depexit import gemma

RECORD = {"name": "Jinja2", "usages": [{"file": "linkwatch/report.py", "line": 3}]}
GOOD = {
    "migration_type": "bump",
    "requirement_changes": [{"action": "set", "name": "Jinja2", "line": "Jinja2>=3.1,<4"}],
    "file_edits": [], "predicted_outcome": "pass", "confidence": 0.9,
}


def fake_repo(tmp_path):
    (tmp_path / "linkwatch").mkdir(parents=True)
    (tmp_path / "linkwatch" / "report.py").write_text("import jinja2\n", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("Jinja2==2.11.3\n", encoding="utf-8")
    return tmp_path


def test_extract_json_handles_fences_and_chatter():
    reply = 'Sure!\n```json\n{"a": 1}\n```\nHope that helps'
    assert gemma.extract_json(reply) == {"a": 1}
    with pytest.raises(ValueError):
        gemma.extract_json("no json here")


def test_clean_accepts_a_real_change():
    out = gemma.clean(GOOD, {"linkwatch/report.py"}, {"Jinja2==2.11.3"})
    assert out["requirement_changes"][0]["line"] == "Jinja2>=3.1,<4"
    assert out["predicted_outcome"] == "pass"


def test_clean_rejects_a_change_that_changes_nothing():
    noop = {**GOOD, "requirement_changes": [{"action": "set", "name": "Jinja2", "line": "Jinja2==2.11.3"}]}
    with pytest.raises(ValueError, match="no effective change"):
        gemma.clean(noop, set(), {"Jinja2==2.11.3"})


def test_clean_drops_wrong_package_and_unseen_files():
    data = {**GOOD,
            "requirement_changes": [{"action": "set", "name": "Jinja2", "line": "markupsafe>=2"}],
            "file_edits": [{"path": "../evil.py", "new_content": "x"},
                           {"path": "linkwatch/report.py", "new_content": "import jinja2\n# new"}]}
    out = gemma.clean(data, {"linkwatch/report.py"}, set())
    assert out["requirement_changes"] == []  # the line names a different package
    assert [e["path"] for e in out["file_edits"]] == ["linkwatch/report.py"]  # "../evil.py" never shown to the model


def test_unknown_migration_type_is_rejected():
    with pytest.raises(ValueError):
        gemma.clean({**GOOD, "migration_type": "yolo"}, set())


def test_analyze_caches_and_invalidates_when_prompt_changes(tmp_path, monkeypatch):
    repo, calls = fake_repo(tmp_path / "repo"), []
    monkeypatch.setenv("GEMMA_MODEL", "test-model")
    monkeypatch.setattr(gemma, "load_env", lambda: None)

    def fake_ask(prompt):
        calls.append(prompt)
        return json.dumps(GOOD), "test-model"

    monkeypatch.setattr(gemma, "ask", fake_ask)
    out = tmp_path / "out"
    first = gemma.analyze(RECORD, repo, out)
    assert first["ok"] and first["model"] == "test-model" and len(calls) == 1

    gemma.analyze(RECORD, repo, out)
    assert len(calls) == 1  # second call came from out/ai/Jinja2.json

    (repo / "linkwatch" / "report.py").write_text("import jinja2\n# edited\n", encoding="utf-8")
    gemma.analyze(RECORD, repo, out)
    assert len(calls) == 2  # the file Gemma sees changed, so the cached answer is stale


def test_analyze_never_raises_when_the_model_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(gemma, "load_env", lambda: None)

    def boom(prompt):
        raise RuntimeError("quota exceeded")

    monkeypatch.setattr(gemma, "ask", boom)
    result = gemma.analyze(RECORD, fake_repo(tmp_path / "repo"), tmp_path / "out")
    assert result["ok"] is False and "quota exceeded" in result["error"]
